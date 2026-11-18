import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/")({
  component: SearchPage,
  head: () => ({ meta: [{ title: "Search trips · EPIC Booking" }] }),
})

function SearchPage() {
  return (
    <section className="space-y-2">
      <h1 className="text-2xl font-semibold">Search trips</h1>
      <p className="text-muted-foreground">
        Origin, destination and date search, results and inline booking go here.
      </p>
    </section>
  )
}
