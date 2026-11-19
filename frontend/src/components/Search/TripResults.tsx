import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { formatLagosDate } from "@/lib/format"
import { problemMessage } from "@/lib/problem"
import { PAGE_SIZE, type TripSearch, tripsQuery } from "@/lib/queries"
import { BookingPanel } from "./BookingPanel"
import { TripCard } from "./TripCard"
import { useBooking } from "./useBooking"

export function TripResults({ search }: { search: TripSearch }) {
  const navigate = useNavigate({ from: "/" })
  const trips = useQuery({
    ...tripsQuery(search),
    placeholderData: keepPreviousData,
  })
  // The booking in progress lives here, not in a card, so its form, error and
  // confirmation survive a refetch that drops a now-full trip from the list.
  const booking = useBooking()
  const active = booking.session?.trip ?? null

  const heading = search.date
    ? `Trips on ${formatLagosDate(search.date)}`
    : "Upcoming trips"

  if (trips.isPending) {
    return (
      <div className="space-y-3" aria-busy="true">
        <p className="sr-only" role="status">
          Loading trips
        </p>
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (trips.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Could not load trips</AlertTitle>
        <AlertDescription>{problemMessage(trips.error)}</AlertDescription>
      </Alert>
    )
  }

  const { items, total } = trips.data
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const activeOffPage = active && !items.some((t) => t.id === active.id)
  const goTo = (page: number) =>
    navigate({
      search: (prev) => ({ ...prev, page: page === 1 ? undefined : page }),
    })

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-lg font-medium">{heading}</h2>
        <p className="text-muted-foreground text-sm" aria-live="polite">
          {total} {total === 1 ? "trip" : "trips"}
        </p>
      </div>

      {activeOffPage && <BookingPanel controller={booking} standalone />}

      {items.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="font-medium">No trips with seats left</p>
          <p className="text-muted-foreground text-sm">
            Try another date, or set either town to “Any town”.
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((trip) => (
            <li key={trip.id}>
              <TripCard
                trip={trip}
                selected={active?.id === trip.id}
                onBook={() => booking.open(trip)}
              >
                {active?.id === trip.id && (
                  <BookingPanel controller={booking} />
                )}
              </TripCard>
            </li>
          ))}
        </ul>
      )}

      {pages > 1 && (
        <nav
          className="flex items-center justify-center gap-3"
          aria-label="Pages"
        >
          <Button
            variant="outline"
            size="sm"
            disabled={search.page <= 1}
            onClick={() => goTo(search.page - 1)}
          >
            <ChevronLeft /> Previous
          </Button>
          <span className="text-muted-foreground text-sm">
            Page {search.page} of {pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={search.page >= pages}
            onClick={() => goTo(search.page + 1)}
          >
            Next <ChevronRight />
          </Button>
        </nav>
      )}
    </div>
  )
}
