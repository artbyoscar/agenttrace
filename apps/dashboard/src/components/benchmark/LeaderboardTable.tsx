'use client';

/**
 * Leaderboard Table Component
 * Displays benchmark submissions in a sortable table
 */

import Link from 'next/link';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { format } from 'date-fns';
import { ScoreBadge } from './ScoreBadge';
import { VerificationBadge } from './VerificationBadge';
import { RankChange } from './RankChange';
import type { LeaderboardEntry, LeaderboardSort } from '@/types/benchmark';

interface LeaderboardTableProps {
  entries: LeaderboardEntry[];
  sort?: LeaderboardSort;
  onSortChange?: (sort: LeaderboardSort) => void;
  categories: string[];
  showCategories?: boolean;
}

export function LeaderboardTable({
  entries,
  sort,
  onSortChange,
  categories,
  showCategories = true,
}: LeaderboardTableProps) {
  const handleSort = (field: string) => {
    if (!onSortChange) return;

    const direction =
      sort?.field === field && sort.direction === 'desc' ? 'asc' : 'desc';
    onSortChange({ field: field as any, direction });
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sort?.field !== field) return <ArrowUpDown size={14} className="text-gray-400" />;
    return sort.direction === 'asc' ? (
      <ArrowUp size={14} className="text-primary-600" />
    ) : (
      <ArrowDown size={14} className="text-primary-600" />
    );
  };

  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left">
              <button
                onClick={() => handleSort('rank')}
                className="flex items-center gap-1 text-xs font-semibold text-gray-700 uppercase hover:text-primary-600"
              >
                Rank
                <SortIcon field="rank" />
              </button>
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
              Agent
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
              Organization
            </th>
            <th className="px-4 py-3 text-left">
              <button
                onClick={() => handleSort('compositeScore')}
                className="flex items-center gap-1 text-xs font-semibold text-gray-700 uppercase hover:text-primary-600"
              >
                Score
                <SortIcon field="compositeScore" />
              </button>
            </th>
            {showCategories && categories.map((category) => (
              <th key={category} className="px-4 py-3 text-left hidden lg:table-cell">
                <button
                  onClick={() => handleSort(category)}
                  className="flex items-center gap-1 text-xs font-semibold text-gray-700 uppercase hover:text-primary-600"
                >
                  {category}
                  <SortIcon field={category} />
                </button>
              </th>
            ))}
            <th className="px-4 py-3 text-left">
              <button
                onClick={() => handleSort('submissionDate')}
                className="flex items-center gap-1 text-xs font-semibold text-gray-700 uppercase hover:text-primary-600"
              >
                Submitted
                <SortIcon field="submissionDate" />
              </button>
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {entries.map((entry) => (
            <tr key={entry.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-gray-900">
                    {entry.rank}
                  </span>
                  <RankChange change={entry.rankChange} size="sm" />
                </div>
              </td>
              <td className="px-4 py-3">
                <Link
                  href={`/benchmark/${entry.id}`}
                  className="text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
                >
                  {entry.agentName}
                </Link>
              </td>
              <td className="px-4 py-3">
                <div className="text-sm text-gray-900">{entry.organization}</div>
                <div className="text-xs text-gray-500 capitalize">
                  {entry.organizationType}
                </div>
              </td>
              <td className="px-4 py-3">
                <ScoreBadge score={entry.compositeScore} size="md" />
              </td>
              {showCategories && categories.map((category) => (
                <td key={category} className="px-4 py-3 hidden lg:table-cell">
                  <span className="text-sm text-gray-700">
                    {entry.categoryScores[category]?.toFixed(1) || '-'}
                  </span>
                </td>
              ))}
              <td className="px-4 py-3">
                <span className="text-sm text-gray-600">
                  {format(new Date(entry.submissionDate), 'MMM d, yyyy')}
                </span>
              </td>
              <td className="px-4 py-3">
                <VerificationBadge status={entry.verified} size="sm" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
