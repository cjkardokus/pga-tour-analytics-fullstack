import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";

import type { CourseResponse } from "../api/courses";

function formatNullable(value: number | null, digits = 0): string {
  return value === null ? "–" : value.toFixed(digits);
}

interface CourseDifficultyTableProps {
  courses: CourseResponse[];
  /** The currently-highlighted course (selected via the search/browse bar
   * above), or null if none. See ./Courses.tsx for how a row becomes
   * highlighted and how it's dismissed. */
  highlightedId: number | null;
  onRowClick: (courseId: number) => void;
}

/**
 * The page's main course difficulty table -- one row per course, sorted
 * however the fetched page already arrived (difficultyRank ascending,
 * nulls last -- the API's own default order, not re-sorted here). Each
 * row carries a DOM id (`course-row-{courseId}`) so the search/browse
 * bar's onSelect callback can scroll it into view directly.
 */
export default function CourseDifficultyTable({ courses, highlightedId, onRowClick }: CourseDifficultyTableProps) {
  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Course</TableCell>
            <TableCell align="right">Avg. Strokes Gained</TableCell>
            <TableCell align="right">Difficulty Rank</TableCell>
            <TableCell align="right">Avg. Strokes vs. Par Rank</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {courses.map((course) => (
            <TableRow
              key={course.courseId}
              id={`course-row-${course.courseId}`}
              hover
              onClick={() => onRowClick(course.courseId)}
              selected={course.courseId === highlightedId}
              sx={{ cursor: "pointer", transition: "background-color 0.3s" }}
            >
              <TableCell>{course.course}</TableCell>
              <TableCell align="right">{formatNullable(course.averageStrokesGained, 2)}</TableCell>
              <TableCell align="right">{formatNullable(course.difficultyRank)}</TableCell>
              <TableCell align="right">{course.averageStrokesVsParRank}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
