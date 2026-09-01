import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CssBaseline from "@mui/material/CssBaseline";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App.tsx";
import ErrorBoundary from "./components/ErrorBoundary.tsx";
import "./index.css";

// Default theme for now -- real palette/typography decisions wait for a
// later branch. Created once at module scope, not per-render.
const theme = createTheme();

// One QueryClient for the whole app's lifetime, likewise created once at
// module scope so it isn't torn down and rebuilt (losing its cache) on
// every re-render of a component that might otherwise construct it.
const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {/* Normalizes browser default styles and applies the theme's
            background/color to <body> -- see index.css for the one thing
            it doesn't cover (full-viewport height). */}
        <CssBaseline />
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);
