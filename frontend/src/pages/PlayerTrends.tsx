import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import { useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../api/client";
import { usePlayerBrowseItems, usePlayerCareerSummary, usePlayerSearchItems, usePlayerSeasons } from "../api/players";
import PlayerSeasonTable from "../components/PlayerSeasonTable";
import SearchBrowseList from "../components/SearchBrowseList";
import PlayerCareerSummaryCards from "./PlayerCareerSummaryCards";
import PlayerCountingStatChart from "./PlayerCountingStatChart";
import PlayerSGChart from "./PlayerSGChart";

function LoadingBlock() {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
      <CircularProgress />
    </Box>
  );
}

/**
 * Player Trends page: a persistent player search/browse bar (rendered
 * regardless of route state, so a user viewing one player can
 * immediately search for another) plus, once a player is selected via
 * the :playerId route param, their career summary, two configurable
 * charts, and a season-by-season table.
 */
export default function PlayerTrends() {
  const { playerId: playerIdParam } = useParams<{ playerId: string }>();
  const parsedId = playerIdParam ? Number(playerIdParam) : NaN;
  const playerId = Number.isInteger(parsedId) ? parsedId : null;
  const navigate = useNavigate();

  const career = usePlayerCareerSummary(playerId);
  const seasons = usePlayerSeasons(playerId);

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        Player Trends
      </Typography>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <SearchBrowseList
            placeholder="Search players by name…"
            onSelect={(id) => navigate(`/players/${id}`)}
            useBrowse={usePlayerBrowseItems}
            useSearch={usePlayerSearchItems}
            collapseOnSelect
          />
        </CardContent>
      </Card>

      {playerId === null ? (
        <Typography color="text.secondary">Search or select a player above to view their career trends.</Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {career.isLoading && <LoadingBlock />}

          {career.isError && (
            <Alert severity="error">
              {career.error instanceof ApiError && career.error.status === 404
                ? "This player couldn't be found."
                : `Failed to load this player's career summary: ${career.error.message}`}
            </Alert>
          )}

          {career.isSuccess && (
            <>
              <Typography variant="h5" component="h2">
                {career.data.player}
              </Typography>
              <PlayerCareerSummaryCards summary={career.data} />
            </>
          )}

          {seasons.isLoading && <LoadingBlock />}

          {seasons.isError && (
            <Alert severity="error">
              {seasons.error instanceof ApiError && seasons.error.status === 404
                ? "No season data found for this player."
                : `Failed to load this player's season data: ${seasons.error.message}`}
            </Alert>
          )}

          {seasons.isSuccess && (
            <>
              <Box
                sx={{
                  display: "grid",
                  gap: 3,
                  gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
                }}
              >
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" component="h3" sx={{ mb: 2 }}>
                      Strokes Gained by Season
                    </Typography>
                    <PlayerSGChart seasons={seasons.data} />
                  </CardContent>
                </Card>

                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" component="h3" sx={{ mb: 2 }}>
                      Season Results
                    </Typography>
                    <PlayerCountingStatChart seasons={seasons.data} />
                  </CardContent>
                </Card>
              </Box>

              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" component="h3" sx={{ mb: 2 }}>
                    Season by Season
                  </Typography>
                  <PlayerSeasonTable seasons={seasons.data} />
                </CardContent>
              </Card>
            </>
          )}
        </Box>
      )}
    </Box>
  );
}
