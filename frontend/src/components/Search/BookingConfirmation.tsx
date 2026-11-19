import { Check, Copy } from "lucide-react"
import { useState } from "react"
import type { BookingOut } from "@/client"
import { Button } from "@/components/ui/button"
import { formatLagosTime, formatUsd } from "@/lib/format"

export function BookingConfirmation({
  booking,
  onBookAnother,
}: {
  booking: BookingOut
  onBookAnother: () => void
}) {
  const [copied, setCopied] = useState(false)
  const { trip } = booking

  async function copy() {
    try {
      await navigator.clipboard.writeText(booking.reference)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard can be blocked; the reference is on screen to copy by hand.
    }
  }

  return (
    <div className="space-y-4" aria-live="polite">
      <div className="bg-muted/50 flex flex-wrap items-center justify-between gap-3 rounded-md p-4">
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Booking reference
          </p>
          <p className="font-mono text-2xl font-semibold tracking-wider">
            {booking.reference}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={copy}>
          {copied ? <Check /> : <Copy />} {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
        <dt className="text-muted-foreground">Passenger</dt>
        <dd>{booking.passenger_name}</dd>
        <dt className="text-muted-foreground">Trip</dt>
        <dd>
          {trip.origin.name} → {trip.destination.name},{" "}
          {formatLagosTime(trip.departs_at)}
        </dd>
        <dt className="text-muted-foreground">Bus</dt>
        <dd>{trip.bus.plate_number}</dd>
        <dt className="text-muted-foreground">Seats</dt>
        <dd className="tabular-nums">
          {booking.seats} × {formatUsd(booking.fare_cents_per_seat)}
        </dd>
        <dt className="text-muted-foreground">Total</dt>
        <dd className="font-semibold tabular-nums">
          {formatUsd(booking.total_cents)}
        </dd>
      </dl>
      <p className="text-muted-foreground text-sm">
        Show this reference at the motor park. Times are Lagos time (WAT).
      </p>
      <Button variant="link" className="px-0" onClick={onBookAnother}>
        Book another seat on this trip
      </Button>
    </div>
  )
}
