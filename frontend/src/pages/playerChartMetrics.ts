/**
 * Fixed metric -> color/dash-pattern assignments for the two Player
 * Trends charts (see PlayerSGChart.tsx / PlayerCountingStatChart.tsx).
 *
 * Colors are assigned PER ENTITY, once, and never change based on which
 * subset is currently selected -- selecting/deselecting a category must
 * never repaint the survivors (see dataviz skill's categorical-color
 * rule). Hexes are the dataviz skill's validated default categorical
 * palette (references/palette.md); light-mode only for now, since this
 * app's MUI theme (see main.tsx) doesn't have a dark mode yet.
 *
 * SG_METRICS' 6 colors are the specific 6-of-8 slots confirmed (via the
 * skill's validate_palette.js, `--pairs all`) to clear the hard
 * normal-vision floor for every possible pair -- required here because
 * the category picker allows an arbitrary subset of up to
 * MAX_SG_SELECTIONS entities to be visible together, not just adjacent
 * ones in a fixed stack/sequence. Two pairs in that 6-set still land in
 * the CVD 6-8 "warn" band (legal only with secondary encoding, never
 * excusable for the normal-vision floor) -- each metric also gets a
 * distinct `dash` pattern so identity never rests on hue alone.
 * COUNTING_METRICS' 4 colors are a separate, smaller set (all 4 always
 * shown at once, no picker cap) that clears every check cleanly with no
 * warnings at all.
 */

import type { PlayerSeason } from "../api/players";

export const MAX_SG_SELECTIONS = 4;

export type SGMetricKey = "total" | "putting" | "aroundGreen" | "approach" | "offTee" | "teeToGreen";

interface SGMetric {
  key: SGMetricKey;
  label: string;
  averageField: keyof PlayerSeason;
  totalField: keyof PlayerSeason;
  color: string;
  dash: string | undefined; // undefined = solid
}

export const SG_METRICS: SGMetric[] = [
  {
    key: "total",
    label: "Total",
    averageField: "averageStrokesGained",
    totalField: "strokesGained",
    color: "#2a78d6", // blue
    dash: undefined, // solid
  },
  {
    key: "putting",
    label: "Putting",
    averageField: "averageStrokesGainedPutting",
    totalField: "strokesGainedPutting",
    color: "#eda100", // yellow
    dash: "6 3",
  },
  {
    key: "aroundGreen",
    label: "Around the Green",
    averageField: "averageStrokesGainedAroundGreen",
    totalField: "strokesGainedAroundGreen",
    color: "#e87ba4", // magenta
    dash: "2 2",
  },
  {
    key: "approach",
    label: "Approach",
    averageField: "averageStrokesGainedApproach",
    totalField: "strokesGainedApproach",
    color: "#008300", // green
    dash: "8 3 2 3",
  },
  {
    key: "offTee",
    label: "Off the Tee",
    averageField: "averageStrokesGainedOffTee",
    totalField: "strokesGainedOffTee",
    color: "#4a3aa7", // violet
    dash: "1 3",
  },
  {
    key: "teeToGreen",
    label: "Tee to Green",
    averageField: "averageStrokesGainedTeeToGreen",
    totalField: "strokesGainedTeeToGreen",
    color: "#1baf7a", // aqua
    dash: "10 3",
  },
];

export type CountingMetricKey = "wins" | "top5Finishes" | "top10Finishes" | "cutsMade";

interface CountingMetric {
  key: CountingMetricKey;
  label: string;
  field: keyof PlayerSeason;
  color: string;
}

export const COUNTING_METRICS: CountingMetric[] = [
  { key: "wins", label: "Wins", field: "wins", color: "#2a78d6" }, // blue
  { key: "top5Finishes", label: "Top 5 Finishes", field: "top5Finishes", color: "#eb6834" }, // orange
  { key: "top10Finishes", label: "Top 10 Finishes", field: "top10Finishes", color: "#1baf7a" }, // aqua
  { key: "cutsMade", label: "Cuts Made", field: "cutsMade", color: "#4a3aa7" }, // violet
];
