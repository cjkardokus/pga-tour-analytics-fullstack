# frontend/

The React front-end for PGA Tour Analytics -- consumes the `api/`
FastAPI layer at the project root. Scaffolded with Vite (not Create
React App, which is deprecated) + React + TypeScript. See the root
`README.md` for the full stack (pipeline -> Postgres -> API) and its
"Tech Stack" section for why each dependency here was chosen.

## Pages

- **Home** -- landing page, links to the three sections below.
- **Leaderboards** -- 1-2 independently-configurable panels (season or
  all-time), across all 16 rankable categories (12 strokes-gained
  variants plus wins/top-5s/top-10s/cuts made).
- **Player Trends** -- search or browse any player for their career
  summary, two configurable charts (strokes gained by season, counting
  stats by season), and a season-by-season table.
- **Courses** -- a strokes-gained-based difficulty ranking of all 81
  courses in the dataset, with a search/browse bar that scrolls to and
  highlights a selected course's row.

## Prerequisites

- **Node.js 20+** (this project was set up against Node 24; anything
  reasonably current should work, since nothing here depends on
  bleeding-edge runtime features).
- The root project's `api/` running locally, at least once, to generate
  types (see "Type generation" below) -- see the root `README.md`'s
  "Running the App" section for how to start it.

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
requires the backend to already be running** -- the script fetches
`http://localhost:8000/openapi.json` over HTTP, it doesn't read any
Python source directly. See the root `README.md` for how to start it
(in short: Postgres up via Docker Compose, then `uvicorn api.main:app
--reload` from the project root with its virtualenv active).

```bash
npm run generate-types
```

Re-run this any time a backend response model changes (a new field, a
new endpoint, a renamed alias) -- `src/types/api.ts` is generated output,
not something to hand-edit. It's committed to the repo (so a fresh
clone has working types without needing the backend running first) but
should be treated as derived from the backend, the same way a lockfile
is derived from `package.json`.

Note that several response envelopes (e.g. the paginated browse shape
for courses/players/leaderboards) are hand-written in `src/api/*.ts`
rather than pulled from the generated types: the backend's shared
`PaginatedResponse.results` field is typed `list[Any]` in Python (see
`api/models/pagination.py`), so `openapi-typescript` can only generate
`unknown[]` for it. The generated types are still the source of truth
for everything else (`CategoryEnum`, `PlayerCareerSummary`,
`CourseResponse`, etc.).

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

## Quality checks

```bash
npm run lint     # oxlint
npx tsc -b       # typecheck
npm run build    # tsc -b && vite build
```

There's no frontend test suite yet -- these three are this project's
quality gate for the frontend: static analysis, type soundness, and "it
actually compiles and bundles."

## CI

The three commands above all run on every push to `main` and every PR
targeting it, via the `frontend` job in
`.github/workflows/tests.yml` -- the same workflow that runs the
backend's pytest suite (`test`), as a separate parallel job. A push or
PR only shows green once both jobs pass.
