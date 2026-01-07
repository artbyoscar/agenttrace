/**
 * Benchmark Types and Interfaces
 * Data structures for the public benchmark leaderboard
 */

export type OrganizationType = 'academic' | 'enterprise' | 'individual' | 'research';
export type TimeRange = 'all-time' | '30-days' | '7-days';
export type VerificationStatus = 'verified' | 'pending' | 'unverified';

/**
 * Category score with confidence interval
 */
export interface CategoryScore {
  category: string;
  score: number;
  confidenceInterval: {
    lower: number;
    upper: number;
  };
  taskCount: number;
}

/**
 * Task-level performance data (for public tasks only)
 */
export interface TaskPerformance {
  taskId: string;
  taskName: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  score: number;
  passed: boolean;
  executionTimeMs: number;
  tokenCount?: number;
  errorMessage?: string;
}

/**
 * Benchmark submission entry
 */
export interface BenchmarkSubmission {
  id: string;
  agentName: string;
  agentVersion: string;
  organization: string;
  organizationType: OrganizationType;
  compositeScore: number;
  percentileRank: number;
  categoryScores: CategoryScore[];
  submissionDate: string;
  verified: VerificationStatus;
  rankChange?: number; // +/- from previous submission
  modelUsed?: string;
  architecturalApproach?: string;
  specialTechniques?: string[];
  publicTasks: TaskPerformance[];
  metadata: {
    totalTasks: number;
    successRate: number;
    averageExecutionTimeMs: number;
    totalTokensUsed?: number;
    averageTokensPerTask?: number;
  };
}

/**
 * Leaderboard entry (lightweight version for list view)
 */
export interface LeaderboardEntry {
  rank: number;
  id: string;
  agentName: string;
  organization: string;
  organizationType: OrganizationType;
  compositeScore: number;
  categoryScores: Record<string, number>; // category -> score
  submissionDate: string;
  verified: VerificationStatus;
  rankChange?: number;
}

/**
 * Leaderboard response with metadata
 */
export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  metadata: {
    totalSubmissions: number;
    lastUpdated: string;
    benchmarkVersion: string;
    categories: string[];
  };
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
    totalCount: number;
  };
}

/**
 * Historical performance data point
 */
export interface PerformanceDataPoint {
  date: string;
  compositeScore: number;
  version: string;
}

/**
 * Comparison data for multiple agents
 */
export interface AgentComparison {
  agents: BenchmarkSubmission[];
  categoryComparison: {
    category: string;
    scores: Record<string, number>; // agentId -> score
    median: number;
  }[];
  taskComparison: {
    taskId: string;
    taskName: string;
    scores: Record<string, number>; // agentId -> score
    executionTimes: Record<string, number>; // agentId -> time
  }[];
}

/**
 * Filter options for leaderboard
 */
export interface LeaderboardFilters {
  timeRange: TimeRange;
  organizationType?: OrganizationType;
  minScore?: number;
  maxScore?: number;
  category?: string;
  verified?: boolean;
  searchQuery?: string;
}

/**
 * Sort options for leaderboard
 */
export interface LeaderboardSort {
  field: 'rank' | 'compositeScore' | 'submissionDate' | string; // string for category names
  direction: 'asc' | 'desc';
}

/**
 * Benchmark methodology version
 */
export interface BenchmarkMethodology {
  version: string;
  releaseDate: string;
  description: string;
  scoringFormula: string;
  categories: {
    name: string;
    description: string;
    weight: number;
    taskCount: number;
  }[];
  antiGamingMeasures: string[];
  changelog: {
    version: string;
    date: string;
    changes: string[];
  }[];
  academicCitations: {
    title: string;
    authors: string[];
    year: number;
    url?: string;
  }[];
}
