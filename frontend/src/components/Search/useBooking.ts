import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import {
  type BookingIn,
  type BookingOut,
  BookingsService,
  type TripOut,
} from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { toProblem } from "@/lib/problem"

type Session = {
  trip: TripOut
  idempotencyKey: string
  booking: BookingOut | null
}

/**
 * The one booking in progress on the page. Held above the results list so the form, its
 * error and the confirmation survive a refetch that drops a now-full trip from the list.
 *
 * The Idempotency-Key is made when the form opens and reused for every retry of that
 * submission, so a double click or a lost response can never book twice. Failed attempts
 * store nothing on the server, so reusing the key after a 409 or 422 is safe; "book
 * another" starts a new key.
 */
export function useBooking() {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [session, setSession] = useState<Session | null>(null)

  const mutation = useMutation({
    mutationFn: async ({ body, key }: { body: BookingIn; key: string }) =>
      (
        await BookingsService.createBooking({
          body,
          headers: { "Idempotency-Key": key },
        })
      ).data,
    onSuccess: (booking) => {
      setSession((s) => (s ? { ...s, booking } : s))
      showSuccessToast(`Booked. Your reference is ${booking.reference}.`)
      queryClient.invalidateQueries({ queryKey: ["trips"] })
    },
    onError: (error) => {
      // Availability changed under us, or the trip left: refresh what the list shows.
      const status = toProblem(error)?.status
      if (status === 409 || status === 404) {
        queryClient.invalidateQueries({ queryKey: ["trips"] })
      }
    },
  })

  return {
    session,
    mutation,
    open(trip: TripOut) {
      mutation.reset()
      setSession({ trip, idempotencyKey: crypto.randomUUID(), booking: null })
    },
    close() {
      mutation.reset()
      setSession(null)
    },
    submit(values: Omit<BookingIn, "trip_id">) {
      if (!session) return
      mutation.mutate({
        body: { trip_id: session.trip.id, ...values },
        key: session.idempotencyKey,
      })
    },
    bookAnother() {
      mutation.reset()
      setSession((s) =>
        s ? { ...s, idempotencyKey: crypto.randomUUID(), booking: null } : s,
      )
    },
  }
}

export type BookingController = ReturnType<typeof useBooking>
