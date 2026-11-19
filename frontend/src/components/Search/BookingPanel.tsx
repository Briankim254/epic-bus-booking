import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { formatLagosTime } from "@/lib/format"
import { cn } from "@/lib/utils"
import { BookingConfirmation } from "./BookingConfirmation"
import { BookingForm } from "./BookingForm"
import type { BookingController } from "./useBooking"

/** Inline booking form, then the confirmation in its place. State lives in useBooking. */
export function BookingPanel({
  controller,
  standalone = false,
}: {
  controller: BookingController
  standalone?: boolean
}) {
  const { session, mutation } = controller
  if (!session) return null
  const { trip, booking } = session

  return (
    <section
      aria-label={booking ? "Booking confirmed" : "Book seats"}
      className={cn(
        "space-y-4 p-4",
        standalone
          ? "bg-card rounded-lg border ring-2 ring-ring/40"
          : "border-t",
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="font-medium">
          {booking ? "Booking confirmed" : "Book seats"}
          {standalone && (
            <span className="text-muted-foreground block text-sm font-normal">
              {trip.origin.name} → {trip.destination.name},{" "}
              {formatLagosTime(trip.departs_at)}
            </span>
          )}
        </h3>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={controller.close}
          aria-label="Close"
        >
          <X />
        </Button>
      </div>
      {booking ? (
        <BookingConfirmation
          booking={booking}
          onBookAnother={controller.bookAnother}
        />
      ) : (
        <BookingForm
          trip={trip}
          pending={mutation.isPending}
          error={mutation.error}
          onSubmit={controller.submit}
        />
      )}
    </section>
  )
}
