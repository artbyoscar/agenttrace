'use client';

/**
 * Performance Trend Chart
 * Line chart showing historical performance over time
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format } from 'date-fns';
import type { PerformanceDataPoint } from '@/types/benchmark';

interface PerformanceTrendChartProps {
  data: PerformanceDataPoint[];
  height?: number;
}

export function PerformanceTrendChart({
  data,
  height = 300,
}: PerformanceTrendChartProps) {
  // Transform data for display
  const chartData = data.map((point) => ({
    ...point,
    formattedDate: format(new Date(point.date), 'MMM d, yyyy'),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="formattedDate"
          tick={{ fill: '#6b7280', fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#6b7280', fontSize: 12 }}
          label={{
            value: 'Composite Score',
            angle: -90,
            position: 'insideLeft',
            style: { fill: '#6b7280' },
          }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e5e7eb',
            borderRadius: '0.5rem',
          }}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="compositeScore"
          name="Composite Score"
          stroke="#0ea5e9"
          strokeWidth={2}
          dot={{ fill: '#0ea5e9', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
