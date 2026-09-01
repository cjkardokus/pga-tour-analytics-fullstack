import CloseIcon from "@mui/icons-material/Close";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import ListSubheader from "@mui/material/ListSubheader";
import MenuItem from "@mui/material/MenuItem";
import Select, { type SelectChangeEvent } from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Tooltip from "@mui/material/Tooltip";
import { useState } from "react";

import { CATEGORY_GROUPS, CATEGORY_LABELS, formatCategoryValue } from "../api/categories";
import type { CategoryEnum, LeaderboardMode } from "../api/leaderboards";
import { useAvailableSeasons, useLeaderboard } from "../api/leaderboards";
import LeaderboardTable from "../components/LeaderboardTable";

interface LeaderboardPanelProps {
  defaultMode: LeaderboardMode;
  defaultCategory: CategoryEnum;
  canRemove: boolean;
  onRemove: () => void;
}

/**
 * One independently-configurable leaderboard panel: mode toggle, year
 * selector (season mode only), category selector, and the resulting
 * table. Lives alongside its page (frontend/src/pages/Leaderboards.tsx),
 * not in components/ -- unlike LeaderboardTable, nothing else reuses
 * this whole panel, just its shared table piece.
 */
export default function LeaderboardPanel({ defaultMode, defaultCategory, canRemove, onRemove }: LeaderboardPanelProps) {
  const [mode, setMode] = useState<LeaderboardMode>(defaultMode);
  // Only set once the user actually picks a year -- null means "no
  // explicit choice yet", not "no year". See `effectiveYear` below for
  // the actual default-to-most-recent-year behavior.
  const [year, setYear] = useState<number | null>(null);
  const [category, setCategory] = useState<CategoryEnum>(defaultCategory);

  const seasons = useAvailableSeasons();

  // Defaults to the most recent available year whenever this panel is in
  // Season mode and the user hasn't explicitly picked one yet -- derived
  // at render time (not an effect + setState) so it resolves correctly
  // however the seasons list/mode-switch ordering happens, with no extra
  // render pass.
  const mostRecentSeason = seasons.data && seasons.data.length > 0 ? seasons.data[seasons.data.length - 1] : null;
  const effectiveYear = mode === "season" ? (year ?? mostRecentSeason) : null;

  const leaderboard = useLeaderboard({ mode, year: effectiveYear, category, limit: 25 });

  function handleModeChange(_event: unknown, newMode: LeaderboardMode | null) {
    // MUI's exclusive ToggleButtonGroup emits null if the already-selected
    // button is clicked again -- ignore that rather than clearing mode.
    if (newMode !== null) setMode(newMode);
  }

  function handleYearChange(event: SelectChangeEvent<number | "">) {
    const value = event.target.value;
    setYear(value === "" ? null : value);
  }

  function handleCategoryChange(event: SelectChangeEvent<CategoryEnum>) {
    setCategory(event.target.value as CategoryEnum);
  }

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" sx={{ alignItems: "flex-start", justifyContent: "space-between", mb: 2 }}>
          <Stack direction="row" spacing={2} useFlexGap sx={{ flexWrap: "wrap", rowGap: 2 }}>
            <ToggleButtonGroup value={mode} exclusive size="small" onChange={handleModeChange} aria-label="Leaderboard mode">
              <ToggleButton value="season" aria-label="Season">
                Season
              </ToggleButton>
              <ToggleButton value="all-time" aria-label="All-Time">
                All-Time
              </ToggleButton>
            </ToggleButtonGroup>

            <Select<number | "">
              size="small"
              value={effectiveYear ?? ""}
              onChange={handleYearChange}
              disabled={mode !== "season" || seasons.isLoading || seasons.isError}
              displayEmpty
              sx={{ minWidth: 100 }}
              aria-label="Season year"
            >
              {effectiveYear === null && <MenuItem value="">{seasons.isLoading ? "Loading…" : "Select year"}</MenuItem>}
              {seasons.data?.map((availableYear) => (
                <MenuItem key={availableYear} value={availableYear}>
                  {availableYear}
                </MenuItem>
              ))}
            </Select>

            <Select<CategoryEnum>
              size="small"
              value={category}
              onChange={handleCategoryChange}
              sx={{ minWidth: 260 }}
              aria-label="Leaderboard category"
            >
              {CATEGORY_GROUPS.flatMap((group) => [
                <ListSubheader key={group.label}>{group.label}</ListSubheader>,
                ...group.categories.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {CATEGORY_LABELS[cat]}
                  </MenuItem>
                )),
              ])}
            </Select>
          </Stack>

          <Tooltip title={canRemove ? "Remove leaderboard" : "At least one leaderboard must remain"}>
            {/* span wrapper: a disabled IconButton wouldn't otherwise fire
                the Tooltip's hover events */}
            <span>
              <IconButton onClick={onRemove} disabled={!canRemove} size="small" aria-label="Remove leaderboard">
                <CloseIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>

        {seasons.isError && mode === "season" && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load available seasons.
          </Alert>
        )}

        {leaderboard.isLoading && (
          <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", height: 200 }}>
            <CircularProgress />
          </Box>
        )}

        {leaderboard.isError && (
          <Alert severity="error">
            Failed to load leaderboard data
            {leaderboard.error instanceof Error ? `: ${leaderboard.error.message}` : "."}
          </Alert>
        )}

        {leaderboard.isSuccess && (
          <LeaderboardTable
            rows={leaderboard.data.results}
            valueLabel={CATEGORY_LABELS[category]}
            formatValue={(value) => formatCategoryValue(category, value)}
            showSeason={mode === "all-time"}
          />
        )}
      </CardContent>
    </Card>
  );
}
