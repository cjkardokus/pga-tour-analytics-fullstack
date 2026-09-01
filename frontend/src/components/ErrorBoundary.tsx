import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { Component, type ErrorInfo, type ReactNode } from "react";
import { useRouteError } from "react-router-dom";

/**
 * Top-level catch-all fallback UI for unexpected render-time errors --
 * this app's closest analog to api/main.py's global exception handler.
 * Handled API-error states (a failed query, a 404) are NOT what this is
 * for -- those already render their own inline Alert per page (see e.g.
 * pages/PlayerTrends.tsx). This is only for what would otherwise unmount
 * the whole tree to a blank white screen: a bug in a component's render,
 * an unexpected data shape slipping past the generated types, etc.
 *
 * Shared between two catch points below (ErrorBoundary and App.tsx's
 * router `errorElement`) so both render identically -- see ErrorBoundary's
 * own docstring for why both exist.
 */
export function ErrorFallback() {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        gap: 2,
        minHeight: "60vh",
        px: 2,
      }}
    >
      <Typography variant="h5" component="h1">
        Something went wrong.
      </Typography>
      <Typography variant="body2" color="text.secondary">
        An unexpected error occurred. Reloading the page usually fixes this.
      </Typography>
      <Button variant="contained" onClick={() => window.location.reload()}>
        Reload page
      </Button>
    </Box>
  );
}

/**
 * Router-level catch point: React Router's data router (createBrowserRouter,
 * see ../App.tsx) wraps every route's element in its OWN internal error
 * boundary, which intercepts a route component's render error before it
 * would ever reach an ErrorBoundary wrapped around <RouterProvider> --
 * confirmed directly (a component made to throw during this work was
 * caught by React Router's generic "Unexpected Application Error!" page,
 * never by ErrorBoundary below). Passed as the root route's `errorElement`
 * in App.tsx, which is the catch point that actually engages for a route
 * render error. `useRouteError()` is how a component rendered as an
 * errorElement retrieves the error React Router caught -- logged here for
 * the same reason ErrorBoundary.componentDidCatch below logs: don't let
 * it vanish silently along with the unmounted route tree.
 */
export function RouteErrorFallback() {
  const error = useRouteError();
  console.error("Unhandled route render error caught by React Router's errorElement:", error);
  return <ErrorFallback />;
}

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Wraps <App /> in main.tsx, outside <RouterProvider> entirely -- kept as
 * defense-in-depth for anything that could throw outside the router's own
 * render cycle (which RouteErrorFallback above cannot catch, precisely
 * because it lives inside that cycle), even though nothing in this app
 * currently renders there. RouteErrorFallback is the catch point that
 * actually engages for the render errors this app can produce today (any
 * route component, since the entire app lives under the router's root
 * route) -- see its own docstring for how that was confirmed.
 *
 * Must be a class component -- React has no hook-based equivalent of
 * getDerivedStateFromError/componentDidCatch as of this writing.
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Unhandled render error caught by ErrorBoundary:", error, errorInfo);
  }

  render() {
    return this.state.hasError ? <ErrorFallback /> : this.props.children;
  }
}
