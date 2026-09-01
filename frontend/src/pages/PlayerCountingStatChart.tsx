import Box from "@mui/material/Box";
import MenuItem from "@mui/material/MenuItem";
import Select, { type SelectChangeEvent } from "@mui/material/Select";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PlayerSeason } from "../api/players";
import { COUNTING_METRICS, type CountingMetricKey } from "./playerChartMetrics";

const DEFAULT_SELECTION: CountingMetricKey[] = ["wins", "top10Finishes"];

interface PlayerCountingStatChartProps {
  seasons: PlayerSeason[];
}

/**
 * Configurable counting-stat bar chart: a multi-select covering all 4
 * available stats (no cap needed -- there are only 4 total). Bars are
 * grouped per season, not stacked -- these are 4 independent counts, not
 * parts of one whole, so stacking them would misleadingly imply a
 * meaningful combined total.
 */
export default function PlayerCountingStatChart({ seasons }: PlayerCountingStatChartProps) {
  const [selectedKeys, setSelectedKeys] = useState<CountingMetricKey[]>(DEFAULT_SELECTION);

  function handleChange(event: SelectChangeEvent<CountingMetricKey[]>) {
    const value = event.target.value;
    setSelectedKeys(typeof value === "string" ? (value.split(",") as CountingMetricKey[]) : value);
  }

  const sorted = [...seasons].sort((a, b) => a.season - b.season);
  const chartData = sorted.map((season) => {
    const row: Record<string, number> & { season: number } = { season: season.season };
    for (const metric of COUNTING_METRICS) {
      if (selectedKeys.includes(metric.key)) {
        row[metric.key] = season[metric.field] as number;
      }
    }
    return row;
  });

  return (
    <Box>
      <Select<CountingMetricKey[]>
        size="small"
        multiple
        value={selectedKeys}
        onChange={handleChange}
        renderValue={(selected) => selected.map((key) => COUNTING_METRICS.find((m) => m.key === key)?.label).join(", ")}
        sx={{ minWidth: 260, mb: 2 }}
        aria-label="Counting stats"
      >
        {COUNTING_METRICS.map((metric) => (
          <MenuItem key={metric.key} value={metric.key}>
            {metric.label}
          </MenuItem>
        ))}
      </Select>

      {selectedKeys.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          Select one or more stats above to plot them.
        </Typography>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" />
            <XAxis dataKey="season" stroke="#898781" />
            <YAxis stroke="#898781" allowDecimals={false} />
            <Tooltip />
            <Legend />
            {selectedKeys.map((key) => {
              const metric = COUNTING_METRICS.find((m) => m.key === key)!;
              return <Bar key={key} dataKey={key} name={metric.label} fill={metric.color} radius={[4, 4, 0, 0]} maxBarSize={24} />;
            })}
          </BarChart>
        </ResponsiveContainer>
      )}
    </Box>
  );
}
