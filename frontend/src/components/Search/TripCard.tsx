import type { ReactNode } from "react"
import type { TripOut } from "@/client"
import { Button } from "@/components/ui/button"
import { formatLagosTime, formatUsd } from "@/lib/format"
import { cn } from "@/lib/utils"

export function TripCard({
  trip,
  selected,
  onBook,
  children,
}: {
  trip: TripOut
  selected: boolean
  onBook: () => void
  children?: ReactNode
}) {
  const seats = trip.seats_available
  return (
    <article
      className={cn(
        "bg-card rounded-lg border",
        selected && "ring-ring/40 ring-2",
      )}
      aria-label={`${trip.origin.name} to ${trip.destination.name}`}
    >
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 p-4">
        <div className="min-w-48 flex-1 space-y-1">
          <p className="font-medium">
            {trip.origin.name} <span aria-hidden="true">→</span>
            <span className="sr-only">to</span> {trip.destination.name}
          </p>
          <p className="text-muted-foreground text-sm">
            <time dateTime={trip.departs_at}>
              {formatLagosTime(trip.departs_at)}
            </time>
            {" · "}Bus {trip.bus.plate_number}
          </p>
        </div>
        <div className="text-right">
          <p className="font-semibold tabular-nums">
            {formatUsd(trip.fare_cents)}
          </p>
          <p className="text-muted-foreground text-xs">per seat</p>
        </div>
        <p
          className={cn(
            "w-28 text-sm tabular-nums",
            seats <= 3
              ? "font-medium text-amber-700 dark:text-amber-400"
              : "text-muted-foreground",
          )}
        >
          {seats} {seats === 1 ? "seat" : "seats"} left
        </p>
        <Button
          onClick={onBook}
          variant={selected ? "secondary" : "default"}
          aria-expanded={selected}
          disabled={selected}
        >
          Book
        </Button>
      </div>
      {children}
    </article>
  )
}
