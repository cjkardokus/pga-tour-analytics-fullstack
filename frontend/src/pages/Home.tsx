import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import GolfCourseIcon from "@mui/icons-material/GolfCourse";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import type { SvgIconComponent } from "@mui/icons-material";
import { Link } from "react-router-dom";

/** The three destinations this landing page exists to point at -- one
 * source of truth for the cards below, rather than three near-identical
 * copy-pasted <Card> blocks. */
const NAV_CARDS: { to: string; label: string; description: string; Icon: SvgIconComponent }[] = [
  {
    to: "/leaderboards",
    label: "Leaderboards",
    description: "Season and all-time rankings across every stat category.",
    Icon: EmojiEventsIcon,
  },
  {
    to: "/player-trends",
    label: "Player Trends",
    description: "See how a player's performance has moved season to season.",
    Icon: TrendingUpIcon,
  },
  {
    to: "/courses",
    label: "Courses",
    description: "Course difficulty rankings across every tour stop.",
    Icon: GolfCourseIcon,
  },
];

/**
 * Landing/nav page -- just a title, a one-line description, and three
 * cards linking to the app's real pages. No data of its own to fetch or
 * display, so deliberately simple. Each card's `CardActionArea` uses
 * React Router's `Link` (via MUI's `component` prop) rather than a plain
 * `<a>`, so clicking through is client-side routing, not a full page
 * reload.
 */
export default function Home() {
  return (
    <Box sx={{ textAlign: "center" }}>
      <Typography variant="h3" component="h1" gutterBottom>
        PGA Tour Analytics
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Explore PGA Tour player and course performance data from the 2017–2022 seasons.
      </Typography>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "repeat(3, 1fr)" },
          gap: 3,
        }}
      >
        {NAV_CARDS.map(({ to, label, description, Icon }) => (
          <Card key={to}>
            <CardActionArea component={Link} to={to} sx={{ height: "100%" }}>
              <CardContent sx={{ py: 4 }}>
                <Icon color="primary" sx={{ fontSize: 48, mb: 1 }} />
                <Typography variant="h6" component="h2" gutterBottom>
                  {label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {description}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Box>
    </Box>
  );
}
