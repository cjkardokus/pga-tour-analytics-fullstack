import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import { createBrowserRouter, Link, NavLink, Outlet, RouterProvider } from "react-router-dom";

import Courses from "./pages/Courses";
import Home from "./pages/Home";
import Leaderboards from "./pages/Leaderboards";
import PlayerTrends from "./pages/PlayerTrends";

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
        <Outlet />
      </Container>
    </Box>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: "leaderboards", element: <Leaderboards /> },
      { path: "player-trends", element: <PlayerTrends /> },
      { path: "courses", element: <Courses /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
