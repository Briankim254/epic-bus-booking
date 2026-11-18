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

| Path                         | Holds                                        |
| ---------------------------- | -------------------------------------------- |
| `src/routes/index.tsx`       | Customer search, results and inline booking  |
| `src/routes/admin/trips.tsx` | Read-only trips table (brief's five columns) |
| `src/client/`                | Generated from OpenAPI. Do not edit          |
| `src/components/ui/`         | shadcn components, unstyled beyond defaults  |
| `src/lib/format.ts`          | Lagos time and USD formatting                |
