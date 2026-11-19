import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import {
  createRootRoute,
  HeadContent,
  Link,
  Outlet,
} from "@tanstack/react-router"
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools"
import ErrorComponent from "@/components/Common/ErrorComponent"
import NotFound from "@/components/Common/NotFound"

const navLink =
  "text-sm text-muted-foreground hover:text-foreground [&.active]:text-foreground [&.active]:font-medium"

export const Route = createRootRoute({
  component: () => (
    <>
      <HeadContent />
      <header className="border-b">
        <nav className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
          <span className="font-semibold">EPIC Booking</span>
          <Link to="/" className={navLink} activeOptions={{ exact: true }}>
            Search
          </Link>
          <Link to="/admin/trips" className={navLink}>
            Admin
          </Link>
        </nav>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
      <footer className="text-muted-foreground mx-auto max-w-5xl px-4 pb-8 text-xs">
        All times are Lagos time (WAT, UTC+1). Prices in US dollars.
      </footer>
      {import.meta.env.DEV && (
        <>
          <TanStackRouterDevtools position="bottom-right" />
          <ReactQueryDevtools initialIsOpen={false} />
        </>
      )}
    </>
  ),
  notFoundComponent: () => <NotFound />,
  errorComponent: () => <ErrorComponent />,
})
