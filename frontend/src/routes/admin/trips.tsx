import { createFileRoute } from "@tanstack/react-router"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export const Route = createFileRoute("/admin/trips")({
  component: AdminTripsPage,
  head: () => ({ meta: [{ title: "Trips · Admin · EPIC Booking" }] }),
})

// The brief's five columns, in the brief's order.
const COLUMNS = [
  "Route",
  "Departure",
  "Capacity",
  "Bookings so far",
  "Status",
] as const

function AdminTripsPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Trips</h1>
      <Alert>
        <AlertDescription>
          Trusted-only: no authentication, per the brief.
        </AlertDescription>
      </Alert>
      <Table>
        <TableHeader>
          <TableRow>
            {COLUMNS.map((c) => (
              <TableHead key={c}>{c}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell
              colSpan={COLUMNS.length}
              className="text-center text-muted-foreground"
            >
              No trips yet.
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </section>
  )
}
