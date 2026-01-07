'use client';

/**
 * Benchmark Comparison Page
 * Side-by-side comparison of up to 4 agents
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Plus, X, TrendingUp, TrendingDown } from 'lucide-react';
import { useBenchmarkComparison, useLeaderboard } from '@/hooks/useBenchmark';
import { PerformanceRadarChart } from '@/components/benchmark/PerformanceRadarChart';
import { ScoreBadge } from '@/components/benchmark/ScoreBadge';
import { VerificationBadge } from '@/components/benchmark/VerificationBadge';
import { ChartLoadingState, LoadingState } from '@/components/benchmark/LoadingState';
import { ErrorState } from '@/components/benchmark/ErrorState';

export default function BenchmarkComparePage() {
  const searchParams = useSearchParams();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [showAgentSelector, setShowAgentSelector] = useState(false);

  // Initialize from URL params
  useEffect(() => {
    const ids = searchParams.get('ids');
    if (ids) {
      setSelectedIds(ids.split(',').filter(Boolean).slice(0, 4));
    }
  }, [searchParams]);

  const {
    data: comparison,
    isLoading,
    error,
    refetch,
  } = useBenchmarkComparison(selectedIds, {
    enabled: selectedIds.length >= 2,
  });

  const { data: leaderboardData } = useLeaderboard(
    { timeRange: 'all-time' },
    { field: 'rank', direction: 'asc' },
    1,
    100
  );

  const addAgent = (id: string) => {
    if (selectedIds.length < 4 && !selectedIds.includes(id)) {
      setSelectedIds([...selectedIds, id]);
      setShowAgentSelector(false);
    }
  };

  const removeAgent = (id: string) => {
    setSelectedIds(selectedIds.filter((i) => i !== id));
  };

  if (selectedIds.length < 2) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <Link
              href="/benchmark"
              className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-primary-600 mb-4"
            >
              <ArrowLeft size={16} />
              Back to Leaderboard
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Compare Agents</h1>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Select Agents to Compare
            </h2>
            <p className="text-gray-600 mb-6">
              Choose 2-4 agents from the leaderboard to compare their performance
            </p>

            {leaderboardData && (
              <div className="max-w-2xl mx-auto">
                <div className="space-y-2">
                  {leaderboardData.entries.slice(0, 10).map((entry) => (
                    <button
                      key={entry.id}
                      onClick={() => addAgent(entry.id)}
                      disabled={selectedIds.includes(entry.id)}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-gray-500">
                          #{entry.rank}
                        </span>
                        <div className="text-left">
                          <div className="font-medium text-gray-900">
                            {entry.agentName}
                          </div>
                          <div className="text-xs text-gray-500">
                            {entry.organization}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <ScoreBadge score={entry.compositeScore} size="sm" />
                        {selectedIds.includes(entry.id) ? (
                          <span className="text-xs text-primary-600 font-medium">
                            Selected
                          </span>
                        ) : (
                          <Plus size={16} className="text-gray-400" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <ErrorState error={error as Error} onRetry={() => refetch()} />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <LoadingState rows={6} />
      </div>
    );
  }

  if (!comparison) {
    return null;
  }

  const agents = comparison.agents;
  const colors = ['#0ea5e9', '#8b5cf6', '#f59e0b', '#10b981'];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link
            href="/benchmark"
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-primary-600 mb-4"
          >
            <ArrowLeft size={16} />
            Back to Leaderboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            Agent Comparison
          </h1>
          <p className="mt-2 text-gray-600">
            Comparing {agents.length} agents across categories and tasks
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Agent Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {agents.map((agent, idx) => (
            <div
              key={agent.id}
              className="bg-white border-2 rounded-lg p-4"
              style={{ borderColor: colors[idx] }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <Link
                    href={`/benchmark/${agent.id}`}
                    className="text-lg font-semibold text-gray-900 hover:text-primary-600"
                  >
                    {agent.agentName}
                  </Link>
                  <p className="text-xs text-gray-500 mt-1">
                    {agent.organization}
                  </p>
                </div>
                <button
                  onClick={() => removeAgent(agent.id)}
                  className="text-gray-400 hover:text-red-600"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Score</span>
                  <ScoreBadge score={agent.compositeScore} size="sm" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Percentile</span>
                  <span className="text-sm font-medium text-gray-900">
                    {agent.percentileRank}th
                  </span>
                </div>
                <VerificationBadge status={agent.verified} size="sm" />
              </div>
            </div>
          ))}

          {/* Add Agent Card */}
          {agents.length < 4 && (
            <button
              onClick={() => setShowAgentSelector(true)}
              className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-4 flex flex-col items-center justify-center hover:border-primary-400 hover:bg-gray-50 transition-colors min-h-[180px]"
            >
              <Plus size={32} className="text-gray-400 mb-2" />
              <span className="text-sm font-medium text-gray-600">
                Add Agent
              </span>
            </button>
          )}
        </div>

        {/* Radar Charts Comparison */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Category Performance Comparison
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {agents.map((agent, idx) => (
              <div key={agent.id}>
                <h3
                  className="text-sm font-medium mb-2"
                  style={{ color: colors[idx] }}
                >
                  {agent.agentName}
                </h3>
                <PerformanceRadarChart
                  categoryScores={agent.categoryScores}
                  agentName={agent.agentName}
                  height={300}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Category-by-Category Comparison */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Category Breakdown
          </h2>
          <div className="space-y-6">
            {comparison.categoryComparison.map((cat) => (
              <div key={cat.category}>
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  {cat.category}
                </h3>
                <div className="space-y-2">
                  {agents.map((agent, idx) => {
                    const score = cat.scores[agent.id] || 0;
                    const delta = score - cat.median;
                    return (
                      <div key={agent.id} className="flex items-center gap-3">
                        <div
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: colors[idx] }}
                        />
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-gray-700">
                              {agent.agentName}
                            </span>
                            <div className="flex items-center gap-2">
                              <ScoreBadge score={score} size="sm" />
                              {delta !== 0 && (
                                <span
                                  className={`text-xs font-medium ${
                                    delta > 0 ? 'text-green-600' : 'text-red-600'
                                  }`}
                                >
                                  {delta > 0 ? <TrendingUp size={14} className="inline" /> : <TrendingDown size={14} className="inline" />}
                                  {Math.abs(delta).toFixed(1)}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="h-2 rounded-full"
                              style={{
                                width: `${score}%`,
                                backgroundColor: colors[idx],
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  <div className="flex items-center gap-3 mt-2 pt-2 border-t border-gray-100">
                    <div className="w-3 h-3 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Median</span>
                        <span className="text-xs font-medium text-gray-600">
                          {cat.median.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Task-Level Comparison (Public Tasks) */}
        {comparison.taskComparison.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Task Performance Comparison
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                      Task
                    </th>
                    {agents.map((agent, idx) => (
                      <th
                        key={agent.id}
                        className="px-4 py-3 text-left text-xs font-semibold uppercase"
                        style={{ color: colors[idx] }}
                      >
                        {agent.agentName}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {comparison.taskComparison.map((task) => (
                    <tr key={task.taskId} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {task.taskName}
                      </td>
                      {agents.map((agent) => {
                        const score = task.scores[agent.id];
                        const time = task.executionTimes[agent.id];
                        return (
                          <td key={agent.id} className="px-4 py-3">
                            {score !== undefined ? (
                              <div>
                                <ScoreBadge score={score} size="sm" />
                                {time && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    {(time / 1000).toFixed(2)}s
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-sm text-gray-400">-</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Efficiency Comparison */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Efficiency Metrics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Execution Time */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Average Execution Time
              </h3>
              <div className="space-y-2">
                {agents.map((agent, idx) => (
                  <div key={agent.id} className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: colors[idx] }}
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-700">
                          {agent.agentName}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          {(agent.metadata.averageExecutionTimeMs / 1000).toFixed(2)}s
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Token Usage */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Average Tokens per Task
              </h3>
              <div className="space-y-2">
                {agents.map((agent, idx) => (
                  <div key={agent.id} className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: colors[idx] }}
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-700">
                          {agent.agentName}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          {agent.metadata.averageTokensPerTask?.toLocaleString() || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Selector Modal */}
      {showAgentSelector && leaderboardData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Select Agent
              </h2>
              <button
                onClick={() => setShowAgentSelector(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="space-y-2">
                {leaderboardData.entries
                  .filter((e) => !selectedIds.includes(e.id))
                  .map((entry) => (
                    <button
                      key={entry.id}
                      onClick={() => addAgent(entry.id)}
                      className="w-full flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-gray-500">
                          #{entry.rank}
                        </span>
                        <div className="text-left">
                          <div className="font-medium text-gray-900">
                            {entry.agentName}
                          </div>
                          <div className="text-xs text-gray-500">
                            {entry.organization}
                          </div>
                        </div>
                      </div>
                      <ScoreBadge score={entry.compositeScore} size="sm" />
                    </button>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
