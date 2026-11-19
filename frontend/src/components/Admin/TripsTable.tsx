import type { ColumnDef } from "@tanstack/react-table"
import type { TripOut, TripStatus } from "@/client"
import {
  DataTable,
  type DataTableFeatures,
} from "@/components/Common/DataTable"
import { Badge } from "@/components/ui/badge"
import { formatLagosTime } from "@/lib/format"

// Presentation only: the badge style per status. The rules about statuses live in the
// backend (domain/trip_status.py); nothing here decides what a status allows.
const STATUS_VARIANT: Record<TripStatus, "default" | "secondary" | "outline"> =
  {
    scheduled: "default",
    boarding: "default",
    departed: "secondary",
    in_transit: "secondary",
    arrived: "outline",
    completed: "outline",
  }

const label = (status: TripStatus) => status.replace("_", " ")

// The brief's five columns in the brief's order, plus the bus after the route.
const columns: ColumnDef<DataTableFeatures, TripOut>[] = [
  {
    id: "route",
    header: "Route",
    cell: ({ row }) => (
      <span className="font-medium">
        {row.original.origin.name} → {row.original.destination.name}
      </span>
    ),
  },
  {
    id: "bus",
    header: "Bus",
    cell: ({ row }) => (
      <span className="font-mono text-xs">{row.original.bus.plate_number}</span>
    ),
  },
  {
    id: "departure",
    header: "Departure",
    cell: ({ row }) => (
      <time dateTime={row.original.departs_at}>
        {formatLagosTime(row.original.departs_at)}
      </time>
    ),
  },
  {
    id: "capacity",
    header: "Capacity",
    cell: ({ row }) => (
      <span className="tabular-nums">{row.original.capacity}</span>
    ),
  },
  {
    id: "booked",
    header: "Bookings so far",
    cell: ({ row }) => {
      const t = row.original
      return (
        <span className="tabular-nums">
          {t.seats_booked}
          {t.seats_available === 0 && (
            <span className="text-muted-foreground ml-2 text-xs">full</span>
          )}
        </span>
      )
    },
  },
  {
    id: "status",
    header: "Status",
    cell: ({ row }) => (
      <Badge
        variant={STATUS_VARIANT[row.original.status]}
        className="capitalize"
      >
        {label(row.original.status)}
      </Badge>
    ),
  },
]

export function TripsTable({ trips }: { trips: TripOut[] }) {
  return <DataTable columns={columns} data={trips} />
}
