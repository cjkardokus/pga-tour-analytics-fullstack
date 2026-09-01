/**
 * Typed fetch functions + TanStack Query hooks for the leaderboard
 * endpoints (see ../../../api/routers/leaderboards.py).
 */

import { useQuery } from "@tanstack/react-query";

import type { components } from "../types/api";
import { apiFetch } from "./client";

export type CategoryEnum = components["schemas"]["CategoryEnum"];
export type LeaderboardMode = "season" | "all-time";

/**
 * One row of a leaderboard response. Hand-written rather than pulled from
 * ../types/api.ts: the backend's PaginatedResponse.results field is typed
 * `list[Any]` in Python (see api/models/pagination.py) -- it's the same
 * generic envelope every list endpoint uses, so it carries no per-
 * resource schema for openapi-typescript to generate from, and
 * `unknown[]` isn't useful here. This mirrors
 * api/models/leaderboard.py's LeaderboardEntry Pydantic model's actual
 * JSON shape (its camelCase aliases) exactly -- keep the two in sync if
 * that model's fields change.
 */
export interface LeaderboardEntry {
  playerId: number;
  player: string;
  season: number;
  tournamentsPlayed: number;
  value: number;
  rank: number;
}

interface LeaderboardResponse {
  total: number;
  limit: number;
  offset: number;
  results: LeaderboardEntry[];
}

async function fetchAvailableSeasons(): Promise<number[]> {
  const data = await apiFetch<components["schemas"]["AvailableSeasonsResponse"]>("/api/v1/leaderboards/seasons");
  return data.seasons;
}

async function fetchSeasonLeaderboard(
  year: number,
  category: CategoryEnum,
  limit: number,
): Promise<LeaderboardResponse> {
  const params = new URLSearchParams({ category, limit: String(limit) });
  return apiFetch<LeaderboardResponse>(`/api/v1/leaderboards/season/${year}?${params}`);
}

async function fetchAllTimeLeaderboard(category: CategoryEnum, limit: number): Promise<LeaderboardResponse> {
  const params = new URLSearchParams({ category, limit: String(limit) });
  return apiFetch<LeaderboardResponse>(`/api/v1/leaderboards/all-time?${params}`);
}

/**
 * The distinct list of seasons with data, for the year selector. Every
 * panel calls this hook independently, but TanStack Query dedupes by
 * queryKey -- with several panels mounted, this is still only ever
 * fetched once and shared from cache, not once per panel. A 5-minute
 * staleTime is a modest optimization on top of that dedup: which seasons
 * exist doesn't change within a browsing session, so there's no reason to
 * silently refetch it on every window refocus.
 */
export function useAvailableSeasons() {
  return useQuery({
    queryKey: ["leaderboard-seasons"],
    queryFn: fetchAvailableSeasons,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Fetches one leaderboard -- season or all-time, whichever `mode` says --
 * keyed on every input that changes the result (mode, year, category,
 * limit), so switching any control re-fetches correctly and revisiting a
 * previously-seen combination is served from cache instead of a fresh
 * loading spinner.
 *
 * Always calls both useQuery hooks (Rules of Hooks: hook calls can't be
 * conditional), but `enabled` means only the query matching `mode` ever
 * actually fetches -- the other stays idle.
 */
export function useLeaderboard({
  mode,
  year,
  category,
  limit = 25,
}: {
  mode: LeaderboardMode;
  year: number | null;
  category: CategoryEnum;
  limit?: number;
}) {
  const seasonQuery = useQuery({
    queryKey: ["leaderboard", "season", year, category, limit],
    queryFn: () => fetchSeasonLeaderboard(year as number, category, limit),
    enabled: mode === "season" && year !== null,
  });

  const allTimeQuery = useQuery({
    queryKey: ["leaderboard", "all-time", category, limit],
    queryFn: () => fetchAllTimeLeaderboard(category, limit),
    enabled: mode === "all-time",
  });

  return mode === "season" ? seasonQuery : allTimeQuery;
}
