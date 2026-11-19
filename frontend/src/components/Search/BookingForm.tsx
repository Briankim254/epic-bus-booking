import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type { TripOut } from "@/client"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { formatUsd } from "@/lib/format"
import { fieldErrors, problemMessage, toProblem } from "@/lib/problem"

const MAX_SEATS_PER_BOOKING = 10 // assumption A5; the server enforces it too

type Values = { passenger_name: string; seats: number }

export function BookingForm({
  trip,
  pending,
  error,
  onSubmit,
}: {
  trip: TripOut
  pending: boolean
  error: Error | null
  onSubmit: (values: Values) => void
}) {
  const problem = toProblem(error)
  // After a 409 the server tells us what is really left; trust it over the list.
  const remaining =
    problem?.code === "insufficient-seats" &&
    typeof problem.remaining === "number"
      ? problem.remaining
      : trip.seats_available
  const maxSeats = Math.min(MAX_SEATS_PER_BOOKING, remaining)

  const schema = z.object({
    passenger_name: z
      .string()
      .trim()
      .min(1, "Enter the passenger's name")
      .max(100, "At most 100 characters"),
    seats: z.coerce
      .number<number>()
      .int("Whole seats only")
      .min(1, "At least 1 seat")
      .max(
        Math.max(maxSeats, 1),
        `At most ${maxSeats} seat${maxSeats === 1 ? "" : "s"}`,
      ),
  })

  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { passenger_name: "", seats: 1 },
  })

  // Map the server's field errors (422) onto the fields.
  useEffect(() => {
    for (const [field, message] of Object.entries(fieldErrors(problem))) {
      if (field === "passenger_name" || field === "seats") {
        form.setError(field, { type: "server", message })
      }
    }
  }, [problem, form])

  const seats = Number(form.watch("seats")) || 0
  const soldOut = maxSeats < 1
  const showAlert = problem
    ? problem.status !== 422 || !problem.errors?.length
    : !!error

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((v) =>
          onSubmit({ ...v, passenger_name: v.passenger_name.trim() }),
        )}
        className="space-y-4"
        noValidate
      >
        {showAlert && (
          <Alert variant="destructive" role="alert">
            <AlertDescription>
              {problem?.code === "insufficient-seats"
                ? remaining === 0
                  ? "Sorry, the last seat was just taken."
                  : `Only ${remaining} seat${remaining === 1 ? "" : "s"} left now.`
                : problemMessage(error)}
            </AlertDescription>
          </Alert>
        )}
        <div className="grid gap-4 sm:grid-cols-[1fr_8rem]">
          <FormField
            control={form.control}
            name="passenger_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Passenger name</FormLabel>
                <FormControl>
                  <Input
                    autoComplete="name"
                    maxLength={100}
                    autoFocus
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="seats"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Seats</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    inputMode="numeric"
                    min={1}
                    max={Math.max(maxSeats, 1)}
                    {...field}
                  />
                </FormControl>
                <FormDescription>Up to {Math.max(maxSeats, 0)}</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm">
            Total{" "}
            <span className="font-semibold tabular-nums">
              {formatUsd(trip.fare_cents * Math.max(seats, 0))}
            </span>{" "}
            <span className="text-muted-foreground">
              ({Math.max(seats, 0)} × {formatUsd(trip.fare_cents)})
            </span>
          </p>
          <LoadingButton type="submit" loading={pending} disabled={soldOut}>
            {pending ? "Booking…" : "Confirm booking"}
          </LoadingButton>
        </div>
      </form>
    </Form>
  )
}
