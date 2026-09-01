/**
 * Typed fetch functions + TanStack Query hooks for the courses endpoints
 * (see ../../../api/routers/courses.py).
 */

import { useQuery } from "@tanstack/react-query";

import type { QueryLike, SearchBrowseItem } from "../components/SearchBrowseList";
import type { components } from "../types/api";
import { apiFetch } from "./client";

export type CourseResponse = components["schemas"]["CourseResponse"];

/** Shape of GET /api/v1/courses in browse mode. Hand-written, like
 * ./players.ts's PlayerBrowseResponse and ./leaderboards.ts's
 * LeaderboardResponse: the backend's PaginatedResponse.results is
 * `list[Any]` in Python (see api/models/pagination.py), so
 * openapi-typescript can only generate `unknown[]` for it. */
interface CourseBrowseResponse {
  total: number;
  limit: number;
  offset: number;
  results: CourseResponse[];
}

async function fetchCoursesBrowse(limit: number, offset: number): Promise<CourseBrowseResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return apiFetch<CourseBrowseResponse>(`/api/v1/courses/?${params}`);
}

async function fetchCoursesSearch(query: string): Promise<CourseResponse[]> {
  const params = new URLSearchParams({ search: query });
  return apiFetch<CourseResponse[]>(`/api/v1/courses/?${params}`);
}

/** Normalizes a page of browse results into SearchBrowseList's generic
 * {id, label} shape, for the persistent search/browse bar. This is a
 * SEPARATE query (own queryKey, own cache entry) from useCourses below,
 * which feeds the page's main difficulty table -- the two aren't the
 * same list instance, and paging one must never affect the other. */
export function useCourseBrowseItems(limit: number, offset: number): QueryLike<{ items: SearchBrowseItem[]; total: number }> {
  const query = useQuery({
    queryKey: ["courses", "search-bar-browse", limit, offset],
    queryFn: () => fetchCoursesBrowse(limit, offset),
  });
  return {
    data: query.data
      ? {
          items: query.data.results.map((course): SearchBrowseItem => ({ id: course.courseId, label: course.course })),
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
export function useCourseSearchItems(query: string): QueryLike<SearchBrowseItem[]> {
  const search = useQuery({
    queryKey: ["courses", "search-bar-search", query],
    queryFn: () => fetchCoursesSearch(query),
    enabled: query.length > 0,
  });
  return {
    data: search.data?.map((course): SearchBrowseItem => ({ id: course.courseId, label: course.course })),
    isLoading: search.isLoading,
    isError: search.isError,
    isSuccess: search.isSuccess,
    error: search.error,
  };
}

// GET /api/v1/courses' own documented cap (Query(le=100)) -- comfortably
// covers every row in this small, already-aggregated table (81 rows as
// of this writing, see api/routers/courses.py's module docstring) in one
// request, with headroom for modest growth.
const ALL_COURSES_LIMIT = 100;

/** Feeds the page's main difficulty table -- independent of, and not
 * paged together with, the search/browse bar's own browse mode above
 * (see that hook's docstring): a separate queryKey/cache entry, so
 * paging one never touches the other.
 *
 * Fetches the WHOLE table in one request rather than one page at a
 * time, and paginates it client-side (see ./pages/Courses.tsx) -- given
 * how small and rarely-changing this table is, that's simpler than
 * server-paging it, and it's what makes "jump to and highlight the row
 * for a course selected via search" reliable: the target row's exact
 * position is already in hand (an index in the fetched array), rather
 * than something to derive from `difficultyRank` (unreliable: `rank()`
 * leaves gaps across ties, so rank isn't the same thing as row
 * position -- see src/transform.py) or a second network round-trip.
 * Sorted difficultyRank ascending (nulls last), matching the API's own
 * default ordering for this endpoint -- not re-sorted here.
 */
export function useCourses() {
  return useQuery({
    queryKey: ["courses", "table"],
    queryFn: () => fetchCoursesBrowse(ALL_COURSES_LIMIT, 0),
  });
}
