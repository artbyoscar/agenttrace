'use client';

/**
 * Leaderboard Filters Component
 * Filter controls for the leaderboard page
 */

import { Search } from 'lucide-react';
import type { LeaderboardFilters, TimeRange, OrganizationType } from '@/types/benchmark';

interface LeaderboardFiltersProps {
  filters: LeaderboardFilters;
  categories: string[];
  onFiltersChange: (filters: LeaderboardFilters) => void;
}

export function LeaderboardFiltersComponent({
  filters,
  categories,
  onFiltersChange,
}: LeaderboardFiltersProps) {
  const updateFilter = <K extends keyof LeaderboardFilters>(
    key: K,
    value: LeaderboardFilters[K]
  ) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900">Filters</h3>

      {/* Search */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Search Agent
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            placeholder="Search by name..."
            value={filters.searchQuery || ''}
            onChange={(e) => updateFilter('searchQuery', e.target.value || undefined)}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Time Range */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Time Range
        </label>
        <select
          value={filters.timeRange}
          onChange={(e) => updateFilter('timeRange', e.target.value as TimeRange)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="all-time">All Time</option>
          <option value="30-days">Last 30 Days</option>
          <option value="7-days">Last 7 Days</option>
        </select>
      </div>

      {/* Organization Type */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Organization Type
        </label>
        <select
          value={filters.organizationType || ''}
          onChange={(e) => updateFilter('organizationType', e.target.value as OrganizationType || undefined)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">All Types</option>
          <option value="academic">Academic</option>
          <option value="enterprise">Enterprise</option>
          <option value="individual">Individual</option>
          <option value="research">Research</option>
        </select>
      </div>

      {/* Category Filter */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Category
        </label>
        <select
          value={filters.category || ''}
          onChange={(e) => updateFilter('category', e.target.value || undefined)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>

      {/* Score Range */}
      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">
          Min Score
        </label>
        <input
          type="number"
          min="0"
          max="100"
          step="5"
          placeholder="0"
          value={filters.minScore || ''}
          onChange={(e) => updateFilter('minScore', e.target.value ? Number(e.target.value) : undefined)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Verification Status */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="verified-only"
          checked={filters.verified || false}
          onChange={(e) => updateFilter('verified', e.target.checked || undefined)}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <label htmlFor="verified-only" className="ml-2 text-sm text-gray-700">
          Verified only
        </label>
      </div>

      {/* Reset Filters */}
      <button
        onClick={() => onFiltersChange({ timeRange: 'all-time' })}
        className="w-full px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
      >
        Reset Filters
      </button>
    </div>
  );
}
