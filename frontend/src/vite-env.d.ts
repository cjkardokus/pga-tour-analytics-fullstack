/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * Base URL of the FastAPI backend (see api/config.py's API_V1_PREFIX for
   * the path prefix appended on top of this). Defaults to
   * http://localhost:8000 when unset -- see src/api/client.ts -- so local
   * dev works with zero config as long as the backend is running on its
   * own documented default port (see root README.md's "Running the API
   * locally"). Set VITE_API_BASE_URL in frontend/.env.local to override,
   * e.g. for a deployed backend origin.
   */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
