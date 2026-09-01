import Link from "@mui/material/Link";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";

/** One row this table can render. Deliberately generic (no CategoryEnum,
 * no API response types) so it's reusable beyond the Leaderboards page --
 * e.g. the Player Trends page's own season list, which isn't a ranked
 * leaderboard at all (hence `rank` being optional). */
export interface LeaderboardRow {
  playerId: number;
  player: string;
  season: number;
  value: number;
  rank?: number;
}

interface LeaderboardTableProps {
  rows: LeaderboardRow[];
  /** Column header for the stat column, e.g. "Wins" or "Average Strokes
   * Gained (Putting)" -- the caller's concern, not this component's,
   * since it depends on category/context this table doesn't know about. */
  valueLabel: string;
  /** Formats each row's raw `value` for display (e.g. "2.43" vs "3").
   * Defaults to a plain String() conversion. */
  formatValue?: (value: number) => string;
  /** Whether to render the Season column -- irrelevant when every row is
   * already known to be the same season (e.g. a season-mode leaderboard).
   * Defaults to true. */
  showSeason?: boolean;
  /** Max height in px before the table scrolls internally, rather than
   * growing the page. Defaults to unconstrained -- LeaderboardPanel now
   * paginates at 25 rows per page (see ../pages/LeaderboardPanel.tsx),
   * which fits on one page without needing an internal scroll region. */
  maxHeight?: number;
}

/**
 * Reusable leaderboard/season table: rank, player (linking to
 * /players/{playerId} via React Router, not a plain <a>), value, and
 * (optionally) season. When `maxHeight` is given, renders inside a
 * height-capped TableContainer so a long result set scrolls internally
 * instead of growing the page.
 */
export default function LeaderboardTable({
  rows,
  valueLabel,
  formatValue = String,
  showSeason = true,
  maxHeight,
}: LeaderboardTableProps) {
  const showRank = rows.some((row) => row.rank !== undefined);

  return (
    <TableContainer sx={{ maxHeight }}>
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            {showRank && <TableCell>Rank</TableCell>}
            <TableCell>Player</TableCell>
            <TableCell align="right">{valueLabel}</TableCell>
            {showSeason && <TableCell align="right">Season</TableCell>}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={(showRank ? 1 : 0) + (showSeason ? 1 : 0) + 2}>
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: "center" }}>
                  No results.
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row) => (
              <TableRow key={`${row.playerId}-${row.season}`} hover>
                {showRank && <TableCell>{row.rank}</TableCell>}
                <TableCell>
                  <Link component={RouterLink} to={`/players/${row.playerId}`} underline="hover">
                    {row.player}
                  </Link>
                </TableCell>
                <TableCell align="right">{formatValue(row.value)}</TableCell>
                {showSeason && <TableCell align="right">{row.season}</TableCell>}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
