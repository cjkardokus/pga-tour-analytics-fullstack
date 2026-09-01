import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";

import type { PlayerCareerSummary } from "../api/players";

function formatNullable(value: number | null, digits = 2): string {
  return value === null ? "N/A" : value.toFixed(digits);
}

interface StatTile {
  label: string;
  value: string;
}

function buildStats(summary: PlayerCareerSummary): StatTile[] {
  return [
    { label: "Seasons Played", value: String(summary.seasonsPlayed) },
    { label: "Tournaments Played", value: String(summary.tournamentsPlayed) },
    { label: "Wins", value: String(summary.wins) },
    { label: "Top 5 Finishes", value: String(summary.top5Finishes) },
    { label: "Top 10 Finishes", value: String(summary.top10Finishes) },
    { label: "Cuts Made", value: String(summary.cutsMade) },
    { label: "Career Strokes Gained", value: formatNullable(summary.careerStrokesGained) },
    { label: "Career Avg. Strokes Gained", value: formatNullable(summary.careerAverageStrokesGained) },
    { label: "First Season", value: String(summary.firstSeason) },
    { label: "Last Season", value: String(summary.lastSeason) },
  ];
}

interface PlayerCareerSummaryCardsProps {
  summary: PlayerCareerSummary;
}

/** Row of stat tiles for a player's career summary. `careerStrokesGained`/
 * `careerAverageStrokesGained` can legitimately be null (a player whose
 * every season falls in the ShotLink data gap -- see
 * api/models/player.py) -- rendered as "N/A" rather than crashing on
 * `.toFixed()` or showing a blank tile. */
export default function PlayerCareerSummaryCards({ summary }: PlayerCareerSummaryCardsProps) {
  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: { xs: "repeat(2, 1fr)", sm: "repeat(3, 1fr)", md: "repeat(5, 1fr)" },
        gap: 2,
      }}
    >
      {buildStats(summary).map((stat) => (
        <Card key={stat.label} variant="outlined">
          <CardContent sx={{ textAlign: "center", py: 2 }}>
            <Typography variant="h5" component="div">
              {stat.value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {stat.label}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
}
