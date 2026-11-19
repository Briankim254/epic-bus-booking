import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { TripResults } from "@/components/Search/TripResults"
import { TripSearchForm } from "@/components/Search/TripSearchForm"
import type { TripSearch } from "@/lib/queries"

// Search state lives in the URL, so results are shareable and survive a refresh.
// Anything invalid falls back to "not set" instead of throwing.
const searchSchema = z.object({
  origin: z.coerce.number().int().positive().optional().catch(undefined),
  destination: z.coerce.number().int().positive().optional().catch(undefined),
  date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional()
    .catch(undefined),
  sort: z
    .enum(["departs_at", "-departs_at", "price", "-price"])
    .optional()
    .catch(undefined),
  page: z.coerce.number().int().min(1).optional().catch(undefined),
})

export type SearchParams = z.infer<typeof searchSchema>

export const Route = createFileRoute("/")({
  validateSearch: (search) => searchSchema.parse(search),
  component: SearchPage,
  head: () => ({ meta: [{ title: "Search trips · EPIC Booking" }] }),
})

function SearchPage() {
  const params = Route.useSearch()
  const search: TripSearch = {
    origin: params.origin,
    destination: params.destination,
    date: params.date,
    sort: params.sort ?? "departs_at",
    page: params.page ?? 1,
  }
  return (
    <section className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Book an intercity bus</h1>
        <p className="text-muted-foreground text-sm">
          Six towns, four fare zones. Fares are per seat and set by zone.
        </p>
      </div>
      {/* key: re-sync the form's fields when the URL changes (back/forward). */}
      <TripSearchForm key={JSON.stringify(params)} search={search} />
      <TripResults search={search} />
    </section>
  )
}
