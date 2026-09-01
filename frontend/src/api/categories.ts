/**
 * Human-readable metadata for CategoryEnum (see ../../../api/models/leaderboard.py),
 * for the Leaderboards page's category selector.
 */

import type { CategoryEnum } from "./leaderboards";

/** Full label for each category, e.g. "Average Strokes Gained (Putting)"
 * -- deliberately the full descriptive name rather than just "Putting",
 * so the closed Select still reads clearly on its own without relying on
 * the group header for context. Wording follows the enum's own naming
 * (api/models/leaderboard.py) 1:1, just with human casing/spacing. */
export const CATEGORY_LABELS: Record<CategoryEnum, string> = {
  average_strokes_gained: "Average Strokes Gained",
  average_strokes_gained_putting: "Average Strokes Gained (Putting)",
  average_strokes_gained_around_green: "Average Strokes Gained (Around the Green)",
  average_strokes_gained_approach: "Average Strokes Gained (Approach)",
  average_strokes_gained_off_tee: "Average Strokes Gained (Off the Tee)",
  average_strokes_gained_tee_to_green: "Average Strokes Gained (Tee to Green)",
  strokes_gained: "Strokes Gained",
  strokes_gained_putting: "Strokes Gained (Putting)",
  strokes_gained_around_green: "Strokes Gained (Around the Green)",
  strokes_gained_approach: "Strokes Gained (Approach)",
  strokes_gained_off_tee: "Strokes Gained (Off the Tee)",
  strokes_gained_tee_to_green: "Strokes Gained (Tee to Green)",
  wins: "Wins",
  top_5_finishes: "Top 5 Finishes",
  top_10_finishes: "Top 10 Finishes",
  cuts_made: "Cuts Made",
};

/** Category selector groups, matching CategoryEnum's own three-part
 * structure (see api/models/leaderboard.py's docstring). */
export const CATEGORY_GROUPS: { label: string; categories: CategoryEnum[] }[] = [
  {
    label: "Strokes Gained (Average)",
    categories: [
      "average_strokes_gained",
      "average_strokes_gained_putting",
      "average_strokes_gained_around_green",
      "average_strokes_gained_approach",
      "average_strokes_gained_off_tee",
      "average_strokes_gained_tee_to_green",
    ],
  },
  {
    label: "Strokes Gained (Total)",
    categories: [
      "strokes_gained",
      "strokes_gained_putting",
      "strokes_gained_around_green",
      "strokes_gained_approach",
      "strokes_gained_off_tee",
      "strokes_gained_tee_to_green",
    ],
  },
  {
    label: "Results",
    categories: ["wins", "top_5_finishes", "top_10_finishes", "cuts_made"],
  },
];

/** The four counting-stat categories -- whole numbers, formatted as
 * plain integers. Every other category is a strokes-gained figure,
 * formatted as a decimal. See formatCategoryValue below. */
const INTEGER_CATEGORIES: ReadonlySet<CategoryEnum> = new Set(["wins", "top_5_finishes", "top_10_finishes", "cuts_made"]);

/** Formats a leaderboard row's `value` for display: counting stats
 * (wins, top 5/10 finishes, cuts made) as plain integers (e.g. "3"),
 * everything else -- strokes-gained figures -- as a 2-decimal number
 * (e.g. "2.43"), matching how these stats are conventionally reported. */
export function formatCategoryValue(category: CategoryEnum, value: number): string {
  return INTEGER_CATEGORIES.has(category) ? String(Math.round(value)) : value.toFixed(2);
}
