'use client';

/**
 * Agent Detail Page
 * Comprehensive view of a single benchmark submission
 */

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Building2,
  Calendar,
  TrendingUp,
  Award,
  Clock,
  Coins,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { useBenchmarkSubmission, useBenchmarkHistory } from '@/hooks/useBenchmark';
import { PerformanceRadarChart } from '@/components/benchmark/PerformanceRadarChart';
import { PerformanceTrendChart } from '@/components/benchmark/PerformanceTrendChart';
import { ScoreBadge } from '@/components/benchmark/ScoreBadge';
import { VerificationBadge } from '@/components/benchmark/VerificationBadge';
import { RankChange } from '@/components/benchmark/RankChange';
import { LoadingState, ChartLoadingState } from '@/components/benchmark/LoadingState';
import { ErrorState } from '@/components/benchmark/ErrorState';

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.agentId as string;

  const {
    data: submission,
    isLoading,
    error,
    refetch,
  } = useBenchmarkSubmission(agentId);

  const { data: history = [] } = useBenchmarkHistory(
    submission?.agentName || '',
    { enabled: !!submission }
  );

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
        <LoadingState rows={8} />
      </div>
    );
  }

  if (!submission) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="text-center py-12">
          <p className="text-gray-500">Submission not found</p>
          <Link
            href="/benchmark"
            className="mt-4 inline-flex items-center gap-2 text-primary-600 hover:text-primary-700"
          >
            <ArrowLeft size={16} />
            Back to Leaderboard
          </Link>
        </div>
      </div>
    );
  }

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

          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {submission.agentName}
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Version {submission.agentVersion}
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Building2 size={16} />
                  <span className="font-medium">{submission.organization}</span>
                  <span className="text-gray-400">•</span>
                  <span className="capitalize">{submission.organizationType}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar size={16} />
                  {format(new Date(submission.submissionDate), 'MMMM d, yyyy')}
                </div>
                <VerificationBadge status={submission.verified} />
              </div>
            </div>

            <div className="flex gap-4">
              <Link
                href={`/benchmark/compare?ids=${agentId}`}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Compare
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Overview Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Score Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Award className="text-primary-600" size={20} />
              <h2 className="text-lg font-semibold text-gray-900">
                Composite Score
              </h2>
            </div>
            <div className="flex items-end gap-2">
              <ScoreBadge score={submission.compositeScore} size="lg" showLabel />
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
              <TrendingUp size={16} className="text-green-600" />
              <span>
                {submission.percentileRank}th percentile
              </span>
            </div>
          </div>

          {/* Success Rate */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Performance Metrics
            </h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-600">Success Rate</div>
                <div className="text-2xl font-bold text-gray-900">
                  {(submission.metadata.successRate * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Tasks Completed</div>
                <div className="text-2xl font-bold text-gray-900">
                  {submission.metadata.totalTasks}
                </div>
              </div>
            </div>
          </div>

          {/* Efficiency Metrics */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Efficiency
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-gray-400" />
                <div>
                  <div className="text-sm text-gray-600">Avg Execution Time</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {(submission.metadata.averageExecutionTimeMs / 1000).toFixed(2)}s
                  </div>
                </div>
              </div>
              {submission.metadata.averageTokensPerTask && (
                <div className="flex items-center gap-2">
                  <Coins size={16} className="text-gray-400" />
                  <div>
                    <div className="text-sm text-gray-600">Avg Tokens/Task</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {submission.metadata.averageTokensPerTask.toLocaleString()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Performance Radar Chart */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Category Performance
          </h2>
          <PerformanceRadarChart
            categoryScores={submission.categoryScores}
            agentName={submission.agentName}
          />
        </div>

        {/* Historical Performance */}
        {history.length > 1 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Historical Performance
            </h2>
            <PerformanceTrendChart data={history} />
          </div>
        )}

        {/* Category Breakdown */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Category Breakdown
          </h2>
          <div className="space-y-4">
            {submission.categoryScores.map((category) => (
              <div key={category.category} className="border-b border-gray-100 pb-4 last:border-0">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-900">
                    {category.category}
                  </h3>
                  <ScoreBadge score={category.score} size="sm" />
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full"
                    style={{ width: `${category.score}%` }}
                  />
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
                  <span>{category.taskCount} tasks</span>
                  <span>
                    CI: {category.confidenceInterval.lower.toFixed(1)} -{' '}
                    {category.confidenceInterval.upper.toFixed(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Task Performance (Public Tasks Only) */}
        {submission.publicTasks.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Public Task Performance
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                      Task
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                      Category
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                      Difficulty
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                      Score
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                      Time
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {submission.publicTasks.map((task) => (
                    <tr key={task.taskId} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {task.taskName}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {task.category}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            task.difficulty === 'easy'
                              ? 'bg-green-100 text-green-700'
                              : task.difficulty === 'medium'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {task.difficulty}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <ScoreBadge score={task.score} size="sm" />
                      </td>
                      <td className="px-4 py-3">
                        {task.passed ? (
                          <CheckCircle className="text-green-600" size={18} />
                        ) : (
                          <XCircle className="text-red-600" size={18} />
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {(task.executionTimeMs / 1000).toFixed(2)}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Methodology Notes */}
        {(submission.modelUsed || submission.architecturalApproach || submission.specialTechniques) && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Implementation Details
            </h2>
            <div className="space-y-4">
              {submission.modelUsed && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-1">
                    Model(s) Used
                  </h3>
                  <p className="text-sm text-gray-600">{submission.modelUsed}</p>
                </div>
              )}
              {submission.architecturalApproach && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-1">
                    Architectural Approach
                  </h3>
                  <p className="text-sm text-gray-600">
                    {submission.architecturalApproach}
                  </p>
                </div>
              )}
              {submission.specialTechniques && submission.specialTechniques.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-1">
                    Special Techniques
                  </h3>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {submission.specialTechniques.map((technique, idx) => (
                      <li key={idx}>{technique}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
