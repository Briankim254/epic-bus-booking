# Frontend

React 19 + Vite + TanStack Router/Query + shadcn/ui (Tailwind 4). Yarn workspace `frontend`.

## Run on the host

```bash
yarn install                     # from the repo root
cp frontend/.env.example frontend/.env
yarn dev                         # http://localhost:5173 (expects the API on :8000)
```

## Regenerate the API client

Run after any backend schema change, in the same commit:

```bash
bash scripts/generate-client.sh  # from the repo root
```

## Layout

| Path                                                                | Holds                                                                                                            |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `src/routes/index.tsx`                                              | Customer page. Search state (origin, destination, date, sort, page) lives in the URL, validated with zod         |
| `src/components/Search/`                                            | Search form, results, trip cards, and the inline booking form and confirmation                                   |
| `src/components/Search/useBooking.ts`                               | The booking in progress: Idempotency-Key, mutation, confirmation. Held above the list so a refetch can't lose it |
| `src/routes/admin/trips.tsx`, `src/components/Admin/TripsTable.tsx` | Read-only trips table: the brief's five columns plus the bus                                                     |
| `src/lib/queries.ts`                                                | TanStack Query keys and fetchers (`['towns']`, `['trips', search]`, `['admin', 'trips']`)                        |
| `src/lib/problem.ts`                                                | Reads problem+json errors: `toProblem`, `fieldErrors`, `problemMessage`                                          |
| `src/lib/format.ts`                                                 | Lagos time and USD formatting                                                                                    |
| `src/client/`                                                       | Generated from OpenAPI. Do not edit                                                                              |
| `src/components/ui/`                                                | shadcn components, unstyled beyond defaults                                                                      |

## Behaviour worth knowing

- **Availability is a hint.** The list says "N seats left"; the server decides at booking time. A 409 `insufficient-seats` shows the real `remaining` count, clamps the seats field, and refreshes the list.
- **No double bookings.** One `Idempotency-Key` (`crypto.randomUUID()`) is made when the booking form opens and reused for every retry of that submission.
- **The reference appears inline** in place of the form, and stays even when the trip drops out of the refreshed results.
- **Times** are always Lagos time, whatever the browser's time zone.
