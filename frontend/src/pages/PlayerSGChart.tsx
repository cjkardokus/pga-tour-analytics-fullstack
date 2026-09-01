import Box from "@mui/material/Box";
import MenuItem from "@mui/material/MenuItem";
import Select, { type SelectChangeEvent } from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PlayerSeason } from "../api/players";
import { MAX_SG_SELECTIONS, SG_METRICS, type SGMetricKey } from "./playerChartMetrics";

type SGType = "average" | "total";

interface PlayerSGChartProps {
  seasons: PlayerSeason[];
}

/**
 * Configurable strokes-gained line chart: a type toggle (Average vs
 * Total -- different scales, so switching always clears the category
 * selection rather than ever plotting both on one axis) and a
 * multi-select category picker capped at MAX_SG_SELECTIONS. Defaults to
 * Total type with only "Total" selected, mirroring the Leaderboards
 * page's own default emphasis on total strokes gained.
 *
 * Straight (linear, not "monotone"-curved) segments: each season is one
 * discrete measured value, not a continuously sampled signal, so a
 * linear connection between points is the honest representation.
 */
export default function PlayerSGChart({ seasons }: PlayerSGChartProps) {
  const [type, setType] = useState<SGType>("total");
  const [selectedKeys, setSelectedKeys] = useState<SGMetricKey[]>(["total"]);

  function handleTypeChange(_event: unknown, newType: SGType | null) {
    if (newType === null) return;
    setType(newType);
    // Average and total strokes-gained live on different scales -- never
    // carry a selection across the toggle, or the chart would end up
    // plotting both on one axis (see the dataviz "one axis" rule).
    setSelectedKeys([]);
  }

  function handleCategoryChange(event: SelectChangeEvent<SGMetricKey[]>) {
    const value = event.target.value;
    const next = typeof value === "string" ? (value.split(",") as SGMetricKey[]) : value;
    if (next.length > MAX_SG_SELECTIONS) return; // cap: ignore a 5th selection
    setSelectedKeys(next);
  }

  const sorted = [...seasons].sort((a, b) => a.season - b.season);
  const chartData = sorted.map((season) => {
    const row: Record<string, number | null> & { season: number } = { season: season.season };
    for (const metric of SG_METRICS) {
      if (selectedKeys.includes(metric.key)) {
        const field = type === "average" ? metric.averageField : metric.totalField;
        row[metric.key] = season[field] as number | null;
      }
    }
    return row;
  });

  return (
    <Box>
      <Stack direction="row" spacing={2} sx={{ mb: 2, flexWrap: "wrap", rowGap: 2 }}>
        <ToggleButtonGroup value={type} exclusive size="small" onChange={handleTypeChange} aria-label="Strokes gained type">
          <ToggleButton value="average" aria-label="Average">
            Average
          </ToggleButton>
          <ToggleButton value="total" aria-label="Total">
            Total
          </ToggleButton>
        </ToggleButtonGroup>

        <Select<SGMetricKey[]>
          size="small"
          multiple
          value={selectedKeys}
          onChange={handleCategoryChange}
          renderValue={(selected) => selected.map((key) => SG_METRICS.find((m) => m.key === key)?.label).join(", ")}
          sx={{ minWidth: 260 }}
          aria-label="Strokes gained categories"
        >
          {SG_METRICS.map((metric) => (
            <MenuItem
              key={metric.key}
              value={metric.key}
              disabled={selectedKeys.length >= MAX_SG_SELECTIONS && !selectedKeys.includes(metric.key)}
            >
              {metric.label}
            </MenuItem>
          ))}
        </Select>
      </Stack>

      {selectedKeys.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          Select one or more categories above to plot them.
        </Typography>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" />
            <XAxis dataKey="season" stroke="#898781" />
            <YAxis stroke="#898781" tickFormatter={(value: number) => value.toFixed(1)} />
            <Tooltip formatter={(value) => (typeof value === "number" ? value.toFixed(2) : value)} />
            <Legend />
            {selectedKeys.map((key) => {
              const metric = SG_METRICS.find((m) => m.key === key)!;
              return (
                <Line
                  key={key}
                  type="linear"
                  dataKey={key}
                  name={metric.label}
                  stroke={metric.color}
                  strokeDasharray={metric.dash}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  connectNulls={false}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      )}
    </Box>
  );
}
