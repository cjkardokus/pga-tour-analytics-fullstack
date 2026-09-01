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

const DEFAULT_BROWSE_PAGE_SIZE = 20;
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
  /** Caps the height of the results list, scrolling internally past that
   * point instead of growing the page. Defaults to unconstrained (the
   * component's original behavior, still correct for Player Trends,
   * where this list is the primary content before a player is selected).
   * Courses passes an explicit smaller value so the list reads as a
   * compact lookup tool sitting above the real content -- the difficulty
   * table -- rather than dominating the page. */
  maxHeight?: number | string;
  /** Called with an item's id when it's clicked. What happens next is
   * entirely the caller's call -- navigate to a detail route (Player
   * Trends: `(id) => navigate(\`/players/${id}\`)`), scroll to and
   * highlight a row in some other list on the same page (Courses: no
   * detail route exists, so selecting a course instead jumps to its row
   * in the difficulty table below), or anything else a future reuse
   * needs. This component only ever reports *which id* was picked --
   * see the module docstring below for why that's the right boundary. */
  onSelect: (id: number) => void;
  /** Fetches one page of the full, unfiltered list (empty search input). */
  useBrowse: (limit: number, offset: number) => QueryLike<{ items: SearchBrowseItem[]; total: number }>;
  /** Fetches search matches for a non-empty, already-debounced query. */
  useSearch: (query: string) => QueryLike<SearchBrowseItem[]>;
  /** Browse-mode page size. Defaults to 20 (Player Trends' original,
   * unchanged behavior); Courses passes 25 to match its difficulty
   * table's page size below. */
  pageSize?: number;
  /** When true, selecting an item collapses the list/pagination down to
   * just the search input -- clicking or focusing the input reopens it
   * (in browse or search mode, whichever the current input content
   * implies), matching typeahead/autocomplete conventions. Defaults to
   * false, preserving the original always-open behavior Courses relies
   * on (selection there just highlights a row in the table below, so
   * there's no "now-visible content" to reveal by collapsing). Player
   * Trends opts in: once a player's selected, their career content is
   * real page content below this card, and leaving the list expanded
   * would force scrolling past it to reach that content. */
  collapseOnSelect?: boolean;
}

/**
 * Reusable, persistent search/browse list -- used standalone (not tied to
 * whether some detail route is currently selected), reused across
 * resources (players, courses) by passing in resource-specific query
 * hooks and an `onSelect` callback rather than hardcoding either here.
 *
 * `onSelect` over a `getDetailPath`-plus-internal-`navigate()` (this
 * component's first shape, on the Player Trends branch): that version
 * baked in the assumption that selecting an item always means routing
 * somewhere, which held for players but broke the moment Courses needed
 * "select an item" to mean "scroll to and highlight a table row on this
 * same page" instead -- there's no course detail route to navigate to.
 * Reporting only the selected id and letting the caller decide what
 * "selected" *means* is what actually makes this component reusable
 * across both cases (and whatever a future reuse needs) without a
 * one-off variant or a union of "maybe navigate, maybe something else"
 * props.
 *
 * Two modes, switched purely by whether the (debounced) search input is
 * empty: empty -> paginated browse via `useBrowse`; non-empty -> a
 * capped, non-paginated match list via `useSearch`. Debounced ~300ms so
 * fast typing doesn't fire a request per keystroke.
 */
export default function SearchBrowseList({
  placeholder,
  maxHeight,
  onSelect,
  useBrowse,
  useSearch,
  pageSize = DEFAULT_BROWSE_PAGE_SIZE,
  collapseOnSelect = false,
}: SearchBrowseListProps) {
  const [inputValue, setInputValue] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [offset, setOffset] = useState(0);
  // Only meaningful when collapseOnSelect is true -- ignored (list always
  // rendered) otherwise. Starts open: nothing's selected yet, so there's
  // nothing collapsing to reveal.
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    const timeout = setTimeout(() => setDebouncedQuery(inputValue.trim()), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timeout);
  }, [inputValue]);

  const isSearchMode = debouncedQuery.length > 0;
  const browse = useBrowse(pageSize, offset);
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

  function handleSelect(id: number) {
    onSelect(id);
    if (collapseOnSelect) setIsOpen(false);
  }

  const showList = !collapseOnSelect || isOpen;

  return (
    <Box>
      <TextField
        fullWidth
        size="small"
        placeholder={placeholder}
        value={inputValue}
        onChange={(event) => handleInputChange(event.target.value)}
        onFocus={() => {
          if (collapseOnSelect) setIsOpen(true);
        }}
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

      {showList && (
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
                <List dense disablePadding sx={{ maxHeight, overflowY: maxHeight ? "auto" : undefined }}>
                  {(isSearchMode ? search.data! : browse.data!.items).map((item) => (
                    <ListItemButton key={item.id} onClick={() => handleSelect(item.id)}>
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
                    onClick={() => setOffset((current) => Math.max(0, current - pageSize))}
                  >
                    <ChevronLeftIcon />
                  </IconButton>
                  <Typography variant="caption" color="text.secondary">
                    {offset + 1}-{Math.min(offset + pageSize, browse.data.total)} of {browse.data.total}
                  </Typography>
                  <IconButton
                    size="small"
                    aria-label="Next page"
                    disabled={offset + pageSize >= browse.data.total}
                    onClick={() => setOffset((current) => current + pageSize)}
                  >
                    <ChevronRightIcon />
                  </IconButton>
                </Stack>
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  );
}
