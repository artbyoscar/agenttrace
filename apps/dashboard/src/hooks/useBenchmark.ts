/**
 * Custom React Query hooks for benchmark data
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { queryKeys } from '@/lib/query-client';
import type {
  LeaderboardResponse,
  LeaderboardFilters,
  LeaderboardSort,
  BenchmarkSubmission,
  PerformanceDataPoint,
  AgentComparison,
  BenchmarkMethodology,
} from '@/types/benchmark';

/**
 * Fetch leaderboard data with filters and sorting
 */
export function useLeaderboard(
  filters?: LeaderboardFilters,
  sort?: LeaderboardSort,
  page: number = 1,
  pageSize: number = 50,
  options?: UseQueryOptions<LeaderboardResponse>
) {
  return useQuery({
    queryKey: queryKeys.leaderboard({ filters, sort, page, pageSize }),
    queryFn: async () => {
      const response = await apiClient.post<LeaderboardResponse>('/benchmark/leaderboard', {
        filters,
        sort,
        page,
        pageSize,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * Fetch single benchmark submission by ID
 */
export function useBenchmarkSubmission(
  id: string,
  options?: UseQueryOptions<BenchmarkSubmission>
) {
  return useQuery({
    queryKey: queryKeys.benchmarkSubmission(id),
    queryFn: async () => {
      const response = await apiClient.get<BenchmarkSubmission>(`/benchmark/submissions/${id}`);
      return response.data;
    },
    enabled: !!id,
    ...options,
  });
}

/**
 * Fetch historical performance for an agent
 */
export function useBenchmarkHistory(
  agentName: string,
  options?: UseQueryOptions<PerformanceDataPoint[]>
) {
  return useQuery({
    queryKey: queryKeys.benchmarkHistory(agentName),
    queryFn: async () => {
      const response = await apiClient.get<PerformanceDataPoint[]>(
        `/benchmark/history/${encodeURIComponent(agentName)}`
      );
      return response.data;
    },
    enabled: !!agentName,
    ...options,
  });
}

/**
 * Fetch comparison data for multiple agents
 */
export function useBenchmarkComparison(
  agentIds: string[],
  options?: UseQueryOptions<AgentComparison>
) {
  return useQuery({
    queryKey: queryKeys.benchmarkComparison(agentIds),
    queryFn: async () => {
      const response = await apiClient.post<AgentComparison>('/benchmark/compare', {
        agentIds,
      });
      return response.data;
    },
    enabled: agentIds.length >= 2 && agentIds.length <= 4,
    ...options,
  });
}

/**
 * Fetch benchmark methodology documentation
 */
export function useBenchmarkMethodology(
  options?: UseQueryOptions<BenchmarkMethodology>
) {
  return useQuery({
    queryKey: queryKeys.benchmarkMethodology(),
    queryFn: async () => {
      const response = await apiClient.get<BenchmarkMethodology>('/benchmark/methodology');
      return response.data;
    },
    staleTime: 60 * 60 * 1000, // 1 hour - methodology changes infrequently
    ...options,
  });
}

/**
 * Fetch available benchmark categories
 */
export function useBenchmarkCategories(
  options?: UseQueryOptions<string[]>
) {
  return useQuery({
    queryKey: queryKeys.benchmarkCategories(),
    queryFn: async () => {
      const response = await apiClient.get<string[]>('/benchmark/categories');
      return response.data;
    },
    staleTime: 60 * 60 * 1000, // 1 hour
    ...options,
  });
}
