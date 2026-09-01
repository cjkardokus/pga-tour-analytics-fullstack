import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import { lazy, Suspense } from "react";
import { createBrowserRouter, Link, NavLink, Outlet, RouterProvider } from "react-router-dom";

import { RouteErrorFallback } from "./components/ErrorBoundary";

/** Each page gets its own build chunk, fetched only when a user actually
 * navigates to it, rather than shipped upfront in the main bundle -- see
 * <Suspense> around <Outlet /> below for the loading state while a
 * chunk's still in flight. Player Trends is the one that matters most
 * here: it's the only page that pulls in Recharts, so lazy-loading it
 * keeps Recharts out of every other page's download entirely.
 *
 * One lazy() call per page (not one per *route* -- players/:playerId
 * below reuses this same PlayerTrends reference rather than its own
 * lazy() call) -- reusing the same dynamic import() means both routes
 * share one chunk and one load/cache, not two separate fetches of the
 * same code. */
const Home = lazy(() => import("./pages/Home"));
const Leaderboards = lazy(() => import("./pages/Leaderboards"));
const PlayerTrends = lazy(() => import("./pages/PlayerTrends"));
const Courses = lazy(() => import("./pages/Courses"));

/** Suspense fallback for a page chunk still in flight -- deliberately
 * plain (a centered spinner), the same footprint as the error fallback
 * it sits alongside (components/ErrorBoundary.tsx's ErrorFallback) so a
 * loading route and a failed route occupy the page similarly rather than
 * jumping around. */
function RouteLoadingFallback() {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
      <CircularProgress />
    </Box>
  );
}

/** Nav bar links, in display order -- kept separate from the router's own
 * route list below (which needs an `index: true` route for "/" rather
 * than a `path`) so neither has to contort itself to stay derived from
 * the other. */
const NAV_LINKS = [
  { to: "/", label: "Home" },
  { to: "/leaderboards", label: "Leaderboards" },
  { to: "/player-trends", label: "Player Trends" },
  { to: "/courses", label: "Courses" },
];

/**
 * Top-level layout: an MUI AppBar/Toolbar nav bar, plus <Outlet /> for
 * whichever page route below is currently active. NavLink (rather than
 * plain Link) so each nav button can reflect the active route, e.g. for a
 * future "you are here" style -- not styled differently yet, but the hook
 * is already in place via the `isActive` render prop.
 */
function Layout() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100%" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{ flexGrow: 1, color: "inherit", textDecoration: "none" }}
          >
            PGA Tour Analytics
          </Typography>
          {NAV_LINKS.map((link) => (
            <Button key={link.to} component={NavLink} to={link.to} color="inherit">
              {link.label}
            </Button>
          ))}
        </Toolbar>
      </AppBar>
      <Container component="main" sx={{ py: 4, flexGrow: 1 }}>
        {/* One Suspense boundary for every routed page below, rather than
            one per route -- they'd all need the identical fallback
            anyway, and a single boundary here is what keeps a route
            transition's loading state from ever visibly touching the
            AppBar/nav above it. */}
        <Suspense fallback={<RouteLoadingFallback />}>
          <Outlet />
        </Suspense>
      </Container>
    </Box>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    // Catches render errors from Layout or any routed page below it --
    // see components/ErrorBoundary.tsx's RouteErrorFallback docstring for
    // why this, not main.tsx's ErrorBoundary wrapping <RouterProvider>,
    // is the catch point that actually engages for these.
    errorElement: <RouteErrorFallback />,
    children: [
      { index: true, element: <Home /> },
      { path: "leaderboards", element: <Leaderboards /> },
      { path: "player-trends", element: <PlayerTrends /> },
      // Player detail route, linked from LeaderboardTable's player names
      // (see components/LeaderboardTable.tsx). Still the same placeholder
      // component as the nav's "Player Trends" page -- a real per-player
      // detail view lands on that page's own branch; this route only
      // needs to exist and read :playerId correctly for now.
      { path: "players/:playerId", element: <PlayerTrends /> },
      { path: "courses", element: <Courses /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
