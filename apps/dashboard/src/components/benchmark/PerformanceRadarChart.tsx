'use client';

/**
 * Radar Chart Component
 * Displays category performance scores in a radar/spider chart
 */

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import type { CategoryScore } from '@/types/benchmark';

interface PerformanceRadarChartProps {
  categoryScores: CategoryScore[];
  agentName?: string;
  comparison?: {
    name: string;
    scores: CategoryScore[];
  };
  height?: number;
}

export function PerformanceRadarChart({
  categoryScores,
  agentName = 'Agent',
  comparison,
  height = 400,
}: PerformanceRadarChartProps) {
  // Transform data for recharts
  const data = categoryScores.map((cat) => {
    const dataPoint: any = {
      category: cat.category,
      score: cat.score,
    };

    if (comparison) {
      const comparisonScore = comparison.scores.find(
        (s) => s.category === cat.category
      );
      if (comparisonScore) {
        dataPoint.comparisonScore = comparisonScore.score;
      }
    }

    return dataPoint;
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="category"
          tick={{ fill: '#6b7280', fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: '#6b7280', fontSize: 10 }}
        />
        <Radar
          name={agentName}
          dataKey="score"
          stroke="#0ea5e9"
          fill="#0ea5e9"
          fillOpacity={0.6}
        />
        {comparison && (
          <Radar
            name={comparison.name}
            dataKey="comparisonScore"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            fillOpacity={0.6}
          />
        )}
        <Legend />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e5e7eb',
            borderRadius: '0.5rem',
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
