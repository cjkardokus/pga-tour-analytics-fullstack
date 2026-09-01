/**
 * Typed fetch functions + TanStack Query hooks for the player endpoints
 * (see ../../../api/routers/players.py).
 */

import { useQuery } from "@tanstack/react-query";

import type { components } from "../types/api";
import { apiFetch } from "./client";
import type { QueryLike, SearchBrowseItem } from "../components/SearchBrowseList";

export type PlayerSummary = components["schemas"]["PlayerSummary"];
export type PlayerCareerSummary = components["schemas"]["PlayerCareerSummary"];
export type PlayerSeason = components["schemas"]["PlayerSeason"];

/** Shape of GET /api/v1/players in browse mode. Hand-written, like
 * ./leaderboards.ts's LeaderboardResponse: the backend's
 * PaginatedResponse.results is `list[Any]` in Python (see
 * api/models/pagination.py), so openapi-typescript can only generate
 * `unknown[]` for it. */
interface PlayerBrowseResponse {
  total: number;
  limit: number;
  offset: number;
  results: PlayerSummary[];
}

async function fetchPlayersBrowse(limit: number, offset: number): Promise<PlayerBrowseResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiFetch<PlayerBrowseResponse>(`/api/v1/players/?${params}`);
}

async function fetchPlayersSearch(query: string): Promise<PlayerSummary[]> {
  const params = new URLSearchParams({ search: query });
  return apiFetch<PlayerSummary[]>(`/api/v1/players/?${params}`);
}

/** Normalizes a page of browse results into SearchBrowseList's generic
 * {id, label} shape. Returns a plain QueryLike, not TanStack Query's own
 * (much richer, but discriminated-union-typed) UseQueryResult -- see
 * QueryLike's own docstring for why. */
export function usePlayerBrowseItems(limit: number, offset: number): QueryLike<{ items: SearchBrowseItem[]; total: number }> {
  const query = useQuery({
    queryKey: ["players", "browse", limit, offset],
    queryFn: () => fetchPlayersBrowse(limit, offset),
  });
  return {
    data: query.data
      ? {
          items: query.data.results.map(
            (player): SearchBrowseItem => ({ id: player.playerId, label: player.player }),
          ),
          total: query.data.total,
        }
      : undefined,
    isLoading: query.isLoading,
    isError: query.isError,
    isSuccess: query.isSuccess,
    error: query.error,
  };
}

/** Normalizes search results into SearchBrowseList's generic {id, label}
 * shape. `enabled: query.length > 0` -- an empty query is browse mode's
 * job, not this hook's (see SearchBrowseList.tsx). */
export function usePlayerSearchItems(query: string): QueryLike<SearchBrowseItem[]> {
  const search = useQuery({
    queryKey: ["players", "search", query],
    queryFn: () => fetchPlayersSearch(query),
    enabled: query.length > 0,
  });
  return {
    data: search.data?.map((player): SearchBrowseItem => ({ id: player.playerId, label: player.player })),
    isLoading: search.isLoading,
    isError: search.isError,
    isSuccess: search.isSuccess,
    error: search.error,
  };
}

export function usePlayerCareerSummary(playerId: number | null) {
  return useQuery({
    queryKey: ["player-career", playerId],
    queryFn: () => apiFetch<PlayerCareerSummary>(`/api/v1/players/${playerId}`),
    enabled: playerId !== null,
    retry: false, // a 404 (bad/missing id) won't resolve by retrying
  });
}

/** Feeds both charts and PlayerSeasonTable on the Player Trends page --
 * fetched once here and shared via TanStack Query's cache, not
 * re-fetched per consumer. */
export function usePlayerSeasons(playerId: number | null) {
  return useQuery({
    queryKey: ["player-seasons", playerId],
    queryFn: () => apiFetch<PlayerSeason[]>(`/api/v1/players/${playerId}/seasons`),
    enabled: playerId !== null,
    retry: false,
  });
}
