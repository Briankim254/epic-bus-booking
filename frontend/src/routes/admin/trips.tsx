import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { RefreshCw } from "lucide-react"
import { TripsTable } from "@/components/Admin/TripsTable"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { problemMessage } from "@/lib/problem"
import { adminTripsQuery } from "@/lib/queries"

export const Route = createFileRoute("/admin/trips")({
  component: AdminTripsPage,
  head: () => ({ meta: [{ title: "Trips · Admin · EPIC Booking" }] }),
})

function AdminTripsPage() {
  const trips = useQuery(adminTripsQuery)
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Trips</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => trips.refetch()}
          disabled={trips.isFetching}
        >
          <RefreshCw
            className={trips.isFetching ? "animate-spin" : undefined}
          />
          Refresh
        </Button>
      </div>
      <Alert>
        <AlertDescription>
          Trusted-only: no authentication, per the brief. Read-only; status
          changes go through the admin API.
        </AlertDescription>
      </Alert>
      {trips.isPending ? (
        <div className="space-y-2" aria-busy="true">
          <p className="sr-only" role="status">
            Loading trips
          </p>
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : trips.isError ? (
        <Alert variant="destructive">
          <AlertTitle>Could not load trips</AlertTitle>
          <AlertDescription>{problemMessage(trips.error)}</AlertDescription>
        </Alert>
      ) : (
        <TripsTable trips={trips.data.items} />
      )}
    </section>
  )
}
