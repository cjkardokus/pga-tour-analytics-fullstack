/**
 * Configured fetch wrapper for the FastAPI backend (see ../../../api/).
 *
 * Base URL is read from VITE_API_BASE_URL (see ../vite-env.d.ts), NOT
 * hardcoded -- this lets the same build point at a different backend
 * origin (e.g. a deployed API) without a code change, just a different
 * .env.local. Defaults to http://localhost:8000, matching the port
 * `uvicorn api.main:app --reload` binds to by default (see root
 * README.md's "Running the API locally") -- so local dev works with zero
 * env config as long as the backend is running.
 *
 * `path` should include the /api/v1 prefix where the backend expects it
 * (e.g. apiFetch<Courses>("/api/v1/courses")) -- this wrapper only owns
 * the origin, not route structure, since that's the caller's concern.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    // Mirrors api/main.py's global exception handler: every non-2xx
    // response body is a plain {"detail": "..."} shape (FastAPI's own
    // 404/422 responses, and the fixed 500 message for unhandled
    // exceptions) -- so reading `detail` here covers all of them.
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : response.statusText;
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}
