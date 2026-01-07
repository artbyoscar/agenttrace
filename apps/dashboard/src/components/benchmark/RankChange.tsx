/**
 * Rank Change Indicator
 * Shows rank movement with up/down arrows
 */

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface RankChangeProps {
  change?: number;
  size?: 'sm' | 'md';
}

export function RankChange({ change, size = 'md' }: RankChangeProps) {
  if (!change || change === 0) {
    return (
      <span className="inline-flex items-center gap-1 text-gray-500">
        <Minus size={size === 'sm' ? 14 : 16} />
      </span>
    );
  }

  const iconSize = size === 'sm' ? 14 : 16;
  const isPositive = change > 0;

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium ${
        isPositive ? 'text-green-600' : 'text-red-600'
      }`}
    >
      {isPositive ? (
        <TrendingUp size={iconSize} />
      ) : (
        <TrendingDown size={iconSize} />
      )}
      <span className={size === 'sm' ? 'text-xs' : 'text-sm'}>
        {Math.abs(change)}
      </span>
    </span>
  );
}
