import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";

import type { PlayerSeason } from "../api/players";

/** Dash for any null/unqualified figure -- e.g. a ShotLink-gap season's
 * average strokes gained, or a season below the ranking's qualifying
 * tournament threshold -- rather than a blank cell that reads as a
 * loading glitch, or a crash from formatting `null`. */
function formatNullable(value: number | null, digits = 0): string {
  return value === null ? "–" : value.toFixed(digits);
}

interface PlayerSeasonTableProps {
  seasons: PlayerSeason[];
}

/**
 * One row per season for a single, already-selected player -- distinct
 * from LeaderboardTable (many players, one stat, one season/all-time
 * scope): this is one player, every stat, every season. Not built as a
 * LeaderboardTable variant since the shapes don't actually overlap.
 */
export default function PlayerSeasonTable({ seasons }: PlayerSeasonTableProps) {
  const sorted = [...seasons].sort((a, b) => a.season - b.season);

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Season</TableCell>
            <TableCell align="right">Tournaments</TableCell>
            <TableCell align="right">Wins</TableCell>
            <TableCell align="right">Top 5s</TableCell>
            <TableCell align="right">Top 10s</TableCell>
            <TableCell align="right">Cuts Made</TableCell>
            <TableCell align="right">Avg. Strokes Gained</TableCell>
            <TableCell align="right">Avg. SG Rank</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sorted.map((season) => (
            <TableRow key={season.season} hover>
              <TableCell>{season.season}</TableCell>
              <TableCell align="right">{season.tournamentsPlayed}</TableCell>
              <TableCell align="right">{season.wins}</TableCell>
              <TableCell align="right">{season.top5Finishes}</TableCell>
              <TableCell align="right">{season.top10Finishes}</TableCell>
              <TableCell align="right">{season.cutsMade}</TableCell>
              <TableCell align="right">{formatNullable(season.averageStrokesGained, 2)}</TableCell>
              <TableCell align="right">{formatNullable(season.averageStrokesGainedRank)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
