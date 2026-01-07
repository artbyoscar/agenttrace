export interface ActionInputs {
  apiKey: string;
  configFile: string;
  failOnRegression: boolean;
  failOnThreshold: boolean;
  commentOnPr: boolean;
  uploadTraces: boolean;
  baselineBranch: string;
}

export interface ActionOutputs {
  passCount: number;
  failCount: number;
  regressionCount: number;
  overallScore: number;
  resultsUrl?: string;
}

export interface AgentTraceConfig {
  project: string;
  api_key?: string;
  api_url?: string;
  suites: TestSuite[];
  evaluators?: EvaluatorConfig[];
  thresholds?: ThresholdConfig;
}

export interface TestSuite {
  name: string;
  description?: string;
  test_cases: TestCase[];
  evaluators?: string[];
  parallel?: boolean;
  timeout?: number;
}

export interface TestCase {
  id: string;
  name: string;
  description?: string;
  input: Record<string, any>;
  expected_output?: Record<string, any>;
  metadata?: Record<string, any>;
  evaluators?: string[];
}

export interface EvaluatorConfig {
  name: string;
  type: string;
  config?: Record<string, any>;
  threshold?: number;
}

export interface ThresholdConfig {
  min_score?: number;
  max_failures?: number;
  max_regressions?: number;
  evaluators?: Record<string, number>;
}

export interface EvaluationResult {
  testCase: TestCase;
  suite: string;
  passed: boolean;
  score?: number;
  evaluatorResults: EvaluatorResult[];
  output?: any;
  error?: string;
  duration: number;
  traceId?: string;
}

export interface EvaluatorResult {
  name: string;
  passed: boolean;
  score?: number;
  reason?: string;
  metadata?: Record<string, any>;
}

export interface TestRunResults {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  overallScore: number;
  evaluations: EvaluationResult[];
  duration: number;
  timestamp: string;
}

export interface BaselineComparison {
  current: TestRunResults;
  baseline?: TestRunResults;
  regressions: Regression[];
  improvements: Improvement[];
  hasRegressions: boolean;
}

export interface Regression {
  testCaseId: string;
  testCaseName: string;
  suite: string;
  currentScore: number;
  baselineScore: number;
  delta: number;
  evaluator?: string;
}

export interface Improvement {
  testCaseId: string;
  testCaseName: string;
  suite: string;
  currentScore: number;
  baselineScore: number;
  delta: number;
  evaluator?: string;
}

export interface PRComment {
  body: string;
  isUpdate?: boolean;
}

export interface GitHubContext {
  owner: string;
  repo: string;
  prNumber?: number;
  sha: string;
  ref: string;
  actor: string;
}
