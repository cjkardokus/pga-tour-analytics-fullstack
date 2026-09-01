import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import SearchIcon from "@mui/icons-material/Search";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const BROWSE_PAGE_SIZE = 20;
const SEARCH_DEBOUNCE_MS = 300;

export interface SearchBrowseItem {
  id: number;
  label: string;
}

/** The subset of TanStack Query's UseQueryResult this component actually
 * needs. Deliberately not `UseQueryResult` itself: that's a discriminated
 * union keyed on `status` (data's very type depends on which branch),
 * which doesn't survive being reconstructed with a transformed `data`
 * field (see ../api/players.ts's usePlayerBrowseItems/usePlayerSearchItems) --
 * this flatter shape is what every caller can actually produce and this
 * component actually consumes. */
export interface QueryLike<T> {
  data: T | undefined;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  error: Error | null;
}

interface SearchBrowseListProps {
  /** Text field placeholder, e.g. "Search players by name…". */
  placeholder: string;
  /** Builds the route to navigate to when an item is clicked, e.g.
   * `(id) => \`/players/${id}\`` -- keeps this component ignorant of
   * which resource (players, courses, ...) it's browsing. */
  getDetailPath: (id: number) => string;
  /** Fetches one page of the full, unfiltered list (empty search input). */
  useBrowse: (limit: number, offset: number) => QueryLike<{ items: SearchBrowseItem[]; total: number }>;
  /** Fetches search matches for a non-empty, already-debounced query. */
  useSearch: (query: string) => QueryLike<SearchBrowseItem[]>;
}

/**
 * Reusable, persistent search/browse list -- used standalone (not tied to
 * whether some detail route is currently selected), reused across
 * resources (players now, courses on an upcoming branch) by passing in
 * resource-specific query hooks and a detail-route builder rather than
 * hardcoding either here.
 *
 * Two modes, switched purely by whether the (debounced) search input is
 * empty: empty -> paginated browse via `useBrowse`; non-empty -> a
 * capped, non-paginated match list via `useSearch`. Debounced ~300ms so
 * fast typing doesn't fire a request per keystroke.
 */
export default function SearchBrowseList({ placeholder, getDetailPath, useBrowse, useSearch }: SearchBrowseListProps) {
  const [inputValue, setInputValue] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const timeout = setTimeout(() => setDebouncedQuery(inputValue.trim()), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timeout);
  }, [inputValue]);

  const isSearchMode = debouncedQuery.length > 0;
  const browse = useBrowse(BROWSE_PAGE_SIZE, offset);
  const search = useSearch(debouncedQuery);
  const active = isSearchMode ? search : browse;

  function handleInputChange(value: string) {
    setInputValue(value);
    // A fresh search (or clearing back to browse mode) always restarts
    // browse pagination from the top -- an offset left over from a
    // previous browse session would otherwise silently apply once the
    // user clears the search box again.
    setOffset(0);
  }

  return (
    <Box>
      <TextField
        fullWidth
        size="small"
        placeholder={placeholder}
        value={inputValue}
        onChange={(event) => handleInputChange(event.target.value)}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          },
        }}
      />

      <Box sx={{ mt: 1 }}>
        {active.isLoading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {active.isError && <Alert severity="error">Failed to load players: {active.error?.message}</Alert>}

        {active.isSuccess && (
          <>
            {(isSearchMode ? search.data! : browse.data!.items).length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                No players found.
              </Typography>
            ) : (
              <List dense disablePadding>
                {(isSearchMode ? search.data! : browse.data!.items).map((item) => (
                  <ListItemButton key={item.id} onClick={() => navigate(getDetailPath(item.id))}>
                    <ListItemText primary={item.label} />
                  </ListItemButton>
                ))}
              </List>
            )}

            {!isSearchMode && browse.data && (
              <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between", mt: 1 }}>
                <IconButton
                  size="small"
                  aria-label="Previous page"
                  disabled={offset === 0}
                  onClick={() => setOffset((current) => Math.max(0, current - BROWSE_PAGE_SIZE))}
                >
                  <ChevronLeftIcon />
                </IconButton>
                <Typography variant="caption" color="text.secondary">
                  {offset + 1}-{Math.min(offset + BROWSE_PAGE_SIZE, browse.data.total)} of {browse.data.total}
                </Typography>
                <IconButton
                  size="small"
                  aria-label="Next page"
                  disabled={offset + BROWSE_PAGE_SIZE >= browse.data.total}
                  onClick={() => setOffset((current) => current + BROWSE_PAGE_SIZE)}
                >
                  <ChevronRightIcon />
                </IconButton>
              </Stack>
            )}
          </>
        )}
      </Box>
    </Box>
  );
}
