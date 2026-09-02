# frontend/

The React front-end for PGA Tour Analytics -- consumes the `api/`
FastAPI layer. Scaffolded with Vite (not Create React App, which is
deprecated) + React + TypeScript.

## Status

All four pages are built: Home, Leaderboards, Player Trends, and Courses
(`src/pages/`), plus the shared components they're built from
(`src/components/` -- SearchBrowseList, LeaderboardTable,
PlayerSeasonTable, ErrorBoundary). Every page fetches real data from the
`api/` backend via TanStack Query.

## Stack

- **Vite** -- dev server / build tool
- **TypeScript**
- **React Router** (`react-router-dom`) -- real URL-based routing, not
  state-based view switching (see `src/App.tsx`)
- **TanStack Query** (`@tanstack/react-query`) -- data fetching/caching,
  wired up in `src/main.tsx` and used by every page's `src/api/*.ts` hooks
- **MUI** (Material UI) -- components/styling, with MUI's default theme
  (see `src/main.tsx`) -- this app hasn't needed a custom palette/
  typography beyond it
- Response types in `src/types/api.ts` are **generated** from the
  backend's OpenAPI schema via `openapi-typescript`, not hand-written --
  see "Type generation" below

## Prerequisites

- **Node.js 20+** (this project was set up against Node 24; anything
  reasonably current should work, since nothing here depends on
  bleeding-edge runtime features).
- The root project's `api/` running locally, at least once, to generate
  types (see "Type generation" below) -- see the root `README.md`'s
  "Running the API locally" for how to start it.

## Install

```bash
cd frontend
npm install
```

**Note on `package.json`'s `overrides` field:** `openapi-typescript`
(current latest, 7.13.0) still declares a `typescript@^5.x` peer
dependency, while this project's Vite-scaffolded `typescript` is 6.x.
It works fine against 6.x in practice (verified via
`npm run generate-types` below) -- the `overrides` entry just tells npm
to satisfy that peer with this project's own installed `typescript`
instead of erroring on a plain `npm install`. Safe to remove once
`openapi-typescript` bumps its peer range.

## Run the dev server

```bash
npm run dev
```

Serves the app at `http://localhost:5173` (Vite's default port).

## Type generation

`npm run generate-types` runs `openapi-typescript` against the live
API's OpenAPI schema and writes the result to `src/types/api.ts`. **This
requires the backend to already be running** (see the root `README.md`;
in short: `cd docker && docker compose up -d postgres`, then, from the
project root with the Python virtualenv active,
`uvicorn api.main:app --reload`) -- the script fetches
`http://localhost:8000/openapi.json` over HTTP, it doesn't read any
Python source directly.

```bash
npm run generate-types
```

Re-run this any time a backend response model changes (a new field, a
new endpoint, a renamed alias) -- `src/types/api.ts` is generated output,
not something to hand-edit. It's committed to the repo (so a fresh
clone has working types without needing the backend running first) but
should be treated as derived from the backend, the same way a lockfile
is derived from `package.json`.

## Environment variables

- `VITE_API_BASE_URL` -- base URL of the FastAPI backend (see
  `src/api/client.ts`). Defaults to `http://localhost:8000` when unset,
  matching `uvicorn`'s default port, so local dev works with zero
  config. Copy `.env.example` to `.env.local` (gitignored) to override,
  e.g. for a deployed backend origin.

The backend's `CORS_ORIGINS` (`api/config.py`, set via the project
root's `.env` -- see `.env.example` there) is configured for
`http://localhost:5173`, Vite's dev server port, so this app's real API
calls work against a locally-run backend with zero extra config.

## Folder structure

```
src/
  api/          # fetch wrapper + per-resource TanStack Query hooks, pointed at VITE_API_BASE_URL
  components/   # shared/reusable components (SearchBrowseList, LeaderboardTable, PlayerSeasonTable, ErrorBoundary)
  pages/        # one file per page (Home, Leaderboards, PlayerTrends, Courses) plus their page-specific subcomponents
  types/        # generated api.ts (see "Type generation" above)
  App.tsx       # React Router setup: layout + nav + routes
  main.tsx      # entry point: QueryClientProvider + MUI ThemeProvider
```

## CI

`npm run lint` (oxlint), `tsc -b` (typecheck), and `npm run build` all
run on every push to `main` and every PR targeting it, via the
`frontend` job in `.github/workflows/tests.yml` -- the same workflow
that runs the backend's pytest suite, as a separate parallel job. There's
no frontend test suite yet (see "Status" above), so this is CI-level
build/lint/typecheck parity with the backend rather than test coverage.
