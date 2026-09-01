import AddIcon from "@mui/icons-material/Add";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useRef, useState } from "react";

import type { CategoryEnum, LeaderboardMode } from "../api/leaderboards";
import LeaderboardPanel from "./LeaderboardPanel";

const MAX_PANELS = 2;

interface PanelConfig {
  id: number;
  defaultMode: LeaderboardMode;
  defaultCategory: CategoryEnum;
}

/** Default config for a newly-added panel (the "Add leaderboard" button) --
 * same defaults as the page's own first panel, a reasonable starting
 * point the user can immediately reconfigure. */
const NEW_PANEL_DEFAULTS: Pick<PanelConfig, "defaultMode" | "defaultCategory"> = {
  defaultMode: "all-time",
  defaultCategory: "strokes_gained",
};

/**
 * Leaderboards page: 1-2 independently-configurable leaderboard panels
 * (see ./LeaderboardPanel.tsx). Starts with 2 -- all-time Strokes Gained
 * (Total) and all-time Wins -- capped at 2, with a floor of 1 (the page
 * must always show at least one leaderboard, so the last panel's remove
 * control is disabled).
 */
export default function Leaderboards() {
  const [panels, setPanels] = useState<PanelConfig[]>([
    { id: 0, defaultMode: "all-time", defaultCategory: "strokes_gained" },
    { id: 1, defaultMode: "all-time", defaultCategory: "wins" },
  ]);
  // Monotonically increasing, independent of `panels.length` -- so a
  // panel added after one has been removed still gets a fresh id rather
  // than colliding with a still-mounted panel's React key.
  const nextId = useRef(2);

  function addPanel() {
    setPanels((current) => {
      if (current.length >= MAX_PANELS) return current;
      return [...current, { id: nextId.current++, ...NEW_PANEL_DEFAULTS }];
    });
  }

  function removePanel(id: number) {
    setPanels((current) => (current.length <= 1 ? current : current.filter((panel) => panel.id !== id)));
  }

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Typography variant="h4" component="h1">
          Leaderboards
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={addPanel}
          disabled={panels.length >= MAX_PANELS}
        >
          Add Leaderboard
        </Button>
      </Stack>

      <Box
        sx={{
          display: "grid",
          gap: 3,
          gridTemplateColumns: panels.length > 1 ? { xs: "1fr", md: "1fr 1fr" } : "1fr",
        }}
      >
        {panels.map((panel) => (
          <LeaderboardPanel
            key={panel.id}
            defaultMode={panel.defaultMode}
            defaultCategory={panel.defaultCategory}
            canRemove={panels.length > 1}
            onRemove={() => removePanel(panel.id)}
          />
        ))}
      </Box>
    </Box>
  );
}
