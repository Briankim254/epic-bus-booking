import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { ArrowLeftRight, X } from "lucide-react"
import { type FormEvent, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { lagosToday } from "@/lib/format"
import { type TripSearch, type TripSort, townsQuery } from "@/lib/queries"

const ANY = "any"

const SORTS: { value: TripSort; label: string }[] = [
  { value: "departs_at", label: "Earliest first" },
  { value: "-departs_at", label: "Latest first" },
  { value: "price", label: "Cheapest first" },
  { value: "-price", label: "Most expensive first" },
]

export function TripSearchForm({ search }: { search: TripSearch }) {
  const navigate = useNavigate({ from: "/" })
  const towns = useQuery(townsQuery)
  const [origin, setOrigin] = useState(search.origin?.toString() ?? ANY)
  const [destination, setDestination] = useState(
    search.destination?.toString() ?? ANY,
  )
  const [date, setDate] = useState(search.date ?? "")
  const [sort, setSort] = useState<TripSort>(search.sort)

  const sameTown = origin !== ANY && origin === destination
  const hasFilters =
    origin !== ANY ||
    destination !== ANY ||
    date !== "" ||
    sort !== "departs_at" ||
    search.page > 1

  function submit(event: FormEvent) {
    event.preventDefault()
    if (sameTown) return
    navigate({
      search: {
        origin: origin === ANY ? undefined : Number(origin),
        destination: destination === ANY ? undefined : Number(destination),
        date: date || undefined,
        sort: sort === "departs_at" ? undefined : sort,
        page: undefined, // a new search starts on page 1
      },
    })
  }

  function clear() {
    setOrigin(ANY)
    setDestination(ANY)
    setDate("")
    setSort("departs_at")
    navigate({ search: {} })
  }

  function swap() {
    setOrigin(destination)
    setDestination(origin)
  }

  const townOptions = (
    <>
      <SelectItem value={ANY}>Any town</SelectItem>
      {towns.data?.map((t) => (
        <SelectItem key={t.id} value={t.id.toString()}>
          {t.name}
        </SelectItem>
      ))}
    </>
  )

  return (
    <form
      onSubmit={submit}
      className="bg-card grid gap-4 rounded-lg border p-4 sm:grid-cols-[1fr_auto_1fr] lg:grid-cols-[1fr_auto_1fr_10rem_11rem_auto] lg:items-end"
      aria-label="Search trips"
    >
      <div className="flex flex-col gap-2">
        <Label htmlFor="origin">From</Label>
        <Select value={origin} onValueChange={setOrigin}>
          <SelectTrigger id="origin" className="w-full">
            <SelectValue placeholder="Any town" />
          </SelectTrigger>
          <SelectContent>{townOptions}</SelectContent>
        </Select>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={swap}
        aria-label="Swap origin and destination"
        className="self-end justify-self-center"
      >
        <ArrowLeftRight />
      </Button>
      <div className="flex flex-col gap-2">
        <Label htmlFor="destination">To</Label>
        <Select value={destination} onValueChange={setDestination}>
          <SelectTrigger
            id="destination"
            className="w-full"
            aria-invalid={sameTown || undefined}
            aria-describedby={sameTown ? "same-town-error" : undefined}
          >
            <SelectValue placeholder="Any town" />
          </SelectTrigger>
          <SelectContent>{townOptions}</SelectContent>
        </Select>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="date">Date</Label>
        <Input
          id="date"
          type="date"
          min={lagosToday()}
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="sort">Sort</Label>
        <Select value={sort} onValueChange={(v) => setSort(v as TripSort)}>
          <SelectTrigger id="sort" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SORTS.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex gap-2 sm:col-span-full lg:col-span-1">
        <Button
          type="submit"
          disabled={sameTown}
          className="flex-1 lg:flex-none"
        >
          Search
        </Button>
        {hasFilters && (
          <Button type="button" variant="ghost" onClick={clear}>
            <X /> Clear
          </Button>
        )}
      </div>
      {sameTown && (
        <p
          id="same-town-error"
          role="alert"
          className="text-destructive text-sm sm:col-span-full"
        >
          Origin and destination must be different towns.
        </p>
      )}
    </form>
  )
}
