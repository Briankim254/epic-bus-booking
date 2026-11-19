// Server state lives only in TanStack Query. Keys follow PLAN §3 "Frontend state".
import { queryOptions } from "@tanstack/react-query"
import { AdminService, TownsService, TripsService } from "@/client"

export type TripSort = "departs_at" | "-departs_at" | "price" | "-price"

export type TripSearch = {
  origin?: number
  destination?: number
  date?: string
  sort: TripSort
  page: number
}

export const PAGE_SIZE = 10

export const townsQuery = queryOptions({
  queryKey: ["towns"],
  queryFn: async () => (await TownsService.listTowns()).data,
  staleTime: Number.POSITIVE_INFINITY, // reference data
})

export const tripsQuery = (search: TripSearch) =>
  queryOptions({
    queryKey: ["trips", search],
    queryFn: async () =>
      (
        await TripsService.searchTrips({
          query: {
            origin_town_id: search.origin,
            destination_town_id: search.destination,
            date: search.date,
            sort: search.sort,
            limit: PAGE_SIZE,
            offset: (search.page - 1) * PAGE_SIZE,
          },
        })
      ).data,
  })

export const adminTripsQuery = queryOptions({
  queryKey: ["admin", "trips"],
  // About 10 trips: one page, paged client-side by the table.
  queryFn: async () =>
    (
      await AdminService.adminSearchTrips({
        query: { limit: 100, sort: "departs_at" },
      })
    ).data,
})
