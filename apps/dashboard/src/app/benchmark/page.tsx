'use client';

/**
 * Main Benchmark Leaderboard Page
 * Public-facing leaderboard displaying agent performance rankings
 */

import { useState } from 'react';
import Link from 'next/link';
import { format } from 'date-fns';
import { Trophy, Users, Calendar, BookOpen, ChevronLeft, ChevronRight } from 'lucide-react';
import { useLeaderboard, useBenchmarkCategories } from '@/hooks/useBenchmark';
import { LeaderboardTable } from '@/components/benchmark/LeaderboardTable';
import { LeaderboardFiltersComponent } from '@/components/benchmark/LeaderboardFilters';
import { LoadingState } from '@/components/benchmark/LoadingState';
import { ErrorState } from '@/components/benchmark/ErrorState';
import type { LeaderboardFilters, LeaderboardSort } from '@/types/benchmark';

export default function BenchmarkLeaderboardPage() {
  const [filters, setFilters] = useState<LeaderboardFilters>({
    timeRange: 'all-time',
  });
  const [sort, setSort] = useState<LeaderboardSort>({
    field: 'rank',
    direction: 'asc',
  });
  const [page, setPage] = useState(1);
  const pageSize = 50;

  // Fetch data
  const {
    data: leaderboardData,
    isLoading,
    error,
    refetch,
  } = useLeaderboard(filters, sort, page, pageSize);

  const { data: categories = [] } = useBenchmarkCategories();

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <ErrorState error={error as Error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Trophy className="text-primary-600" size={32} />
                AgentTrace Benchmark Leaderboard
              </h1>
              <p className="mt-2 text-gray-600">
                Compare AI agent performance across multiple categories and tasks
              </p>
            </div>
            <Link
              href="/benchmark/methodology"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              <BookOpen size={18} />
              View Methodology
            </Link>
          </div>

          {/* Stats Bar */}
          {leaderboardData && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4 flex items-center gap-3">
                <Users className="text-primary-600" size={24} />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {leaderboardData.metadata.totalSubmissions}
                  </div>
                  <div className="text-sm text-gray-600">Total Submissions</div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 flex items-center gap-3">
                <Calendar className="text-primary-600" size={24} />
                <div>
                  <div className="text-sm font-semibold text-gray-900">
                    {format(new Date(leaderboardData.metadata.lastUpdated), 'MMM d, yyyy')}
                  </div>
                  <div className="text-sm text-gray-600">Last Updated</div>
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 flex items-center gap-3">
                <Trophy className="text-primary-600" size={24} />
                <div>
                  <div className="text-sm font-semibold text-gray-900">
                    v{leaderboardData.metadata.benchmarkVersion}
                  </div>
                  <div className="text-sm text-gray-600">Benchmark Version</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Filters */}
          <aside className="lg:col-span-1">
            <LeaderboardFiltersComponent
              filters={filters}
              categories={categories}
              onFiltersChange={setFilters}
            />
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-3 space-y-6">
            {isLoading ? (
              <LoadingState rows={pageSize} />
            ) : leaderboardData ? (
              <>
                {/* Results Info */}
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Showing {(page - 1) * pageSize + 1} -{' '}
                    {Math.min(page * pageSize, leaderboardData.pagination.totalCount)} of{' '}
                    {leaderboardData.pagination.totalCount} results
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Time Range:</span>
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {filters.timeRange.replace('-', ' ')}
                    </span>
                  </div>
                </div>

                {/* Leaderboard Table */}
                <LeaderboardTable
                  entries={leaderboardData.entries}
                  sort={sort}
                  onSortChange={setSort}
                  categories={categories}
                />

                {/* Pagination */}
                {leaderboardData.pagination.totalPages > 1 && (
                  <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 rounded-lg">
                    <div className="flex flex-1 justify-between sm:hidden">
                      <button
                        onClick={() => setPage(page - 1)}
                        disabled={page === 1}
                        className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setPage(page + 1)}
                        disabled={page === leaderboardData.pagination.totalPages}
                        className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                    <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm text-gray-700">
                          Page <span className="font-medium">{page}</span> of{' '}
                          <span className="font-medium">{leaderboardData.pagination.totalPages}</span>
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => setPage(page - 1)}
                          disabled={page === 1}
                          className="relative inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronLeft size={16} />
                          Previous
                        </button>
                        <button
                          onClick={() => setPage(page + 1)}
                          disabled={page === leaderboardData.pagination.totalPages}
                          className="relative inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Next
                          <ChevronRight size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                No results found. Try adjusting your filters.
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
