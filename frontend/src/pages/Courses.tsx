import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { useEffect, useState } from "react";

import { useCourseBrowseItems, useCourseSearchItems, useCourses } from "../api/courses";
import SearchBrowseList from "../components/SearchBrowseList";
import CourseDifficultyTable from "./CourseDifficultyTable";

const TABLE_PAGE_SIZE = 25;

// Caps the search/browse list to roughly 10 rows tall so it reads as a
// compact lookup tool above the difficulty table rather than the page's
// primary content (contrast Player Trends, which leaves this unset).
const SEARCH_LIST_MAX_HEIGHT = 400;

/**
 * Courses page: a persistent search/browse bar (reused from Player
 * Trends) plus the main course difficulty table. Unlike Player Trends,
 * there's no course detail route to navigate to -- selecting a course
 * above instead scrolls to and highlights that course's row in the
 * table below (see SearchBrowseList's docstring for why `onSelect` is
 * the right boundary for that difference).
 */
export default function Courses() {
  const courses = useCourses();
  const [offset, setOffset] = useState(0);
  const [highlightedId, setHighlightedId] = useState<number | null>(null);

  // Scrolls to the highlighted row once it's actually on the displayed
  // page. Table pagination here is client-side over an already-fetched
  // array (see useCourses' docstring), so by the time this effect runs
  // after `offset`/`highlightedId` change, the target row is already in
  // the DOM -- no async page fetch to wait on.
  useEffect(() => {
    if (highlightedId === null) return;
    document.getElementById(`course-row-${highlightedId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlightedId, offset]);

  function handleSelectFromSearch(courseId: number) {
    const allCourses = courses.data?.results ?? [];
    const index = allCourses.findIndex((course) => course.courseId === courseId);
    if (index !== -1) {
      setOffset(Math.floor(index / TABLE_PAGE_SIZE) * TABLE_PAGE_SIZE);
    }
    setHighlightedId(courseId);
  }

  function handleRowClick(courseId: number) {
    // Clicking the already-highlighted row dismisses the highlight;
    // clicking a different one moves it there instead.
    setHighlightedId((current) => (current === courseId ? null : courseId));
  }

  const total = courses.data?.total ?? 0;
  const pageCourses = courses.data?.results.slice(offset, offset + TABLE_PAGE_SIZE) ?? [];

  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
        Courses
      </Typography>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <SearchBrowseList
            placeholder="Search courses by name…"
            maxHeight={SEARCH_LIST_MAX_HEIGHT}
            onSelect={handleSelectFromSearch}
            useBrowse={useCourseBrowseItems}
            useSearch={useCourseSearchItems}
            pageSize={TABLE_PAGE_SIZE}
          />
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" component="h2" sx={{ mb: 1 }}>
            Course Difficulty
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            Strokes-gained data comes from ShotLink, the Tour's shot-tracking system --
            it isn't deployed at major championships or international/limited-field
            events, so 17 of the 81 courses here have no strokes-gained data and show a
            dash for Avg. Strokes Gained and Difficulty Rank. Avg. Strokes vs. Par Rank
            is a fallback difficulty signal built from scores relative to par, which
            every course has regardless of ShotLink coverage.
          </Alert>

          {courses.isLoading && (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress />
            </Box>
          )}

          {courses.isError && <Alert severity="error">Failed to load courses: {courses.error.message}</Alert>}

          {courses.isSuccess && (
            <>
              <CourseDifficultyTable courses={pageCourses} highlightedId={highlightedId} onRowClick={handleRowClick} />
              <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between", mt: 1 }}>
                <IconButton
                  size="small"
                  aria-label="Previous page"
                  disabled={offset === 0}
                  onClick={() => setOffset((current) => Math.max(0, current - TABLE_PAGE_SIZE))}
                >
                  <ChevronLeftIcon />
                </IconButton>
                <Typography variant="caption" color="text.secondary">
                  {offset + 1}-{Math.min(offset + TABLE_PAGE_SIZE, total)} of {total}
                </Typography>
                <IconButton
                  size="small"
                  aria-label="Next page"
                  disabled={offset + TABLE_PAGE_SIZE >= total}
                  onClick={() => setOffset((current) => current + TABLE_PAGE_SIZE)}
                >
                  <ChevronRightIcon />
                </IconButton>
              </Stack>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
