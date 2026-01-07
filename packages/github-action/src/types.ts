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

// Main configuration interface
export interface AgentTraceConfig {
  version: 1;

  project: {
    name: string;
    id?: string;
  };

  agent: {
    module: string;
    function: string;
    setup_command?: string;
    env_file?: string;
  };

  test_suites: TestSuite[];

  evaluators: EvaluatorConfig[];

  baseline: {
    branch: string;
    require_improvement?: boolean;
    regression_threshold?: number;
  };

  reporting: {
    comment_on_pr: boolean;
    detailed_traces: boolean;
    upload_traces: boolean;
    badge_style?: 'flat' | 'flat-square' | 'plastic';
  };

  execution: {
    timeout_seconds?: number;
    max_retries?: number;
    parallelism?: number;
  };
}

export interface TestSuite {
  name: string;
  description?: string;
  tags?: string[];
  test_cases: TestCase[];
}

export interface TestCase {
  name: string;
  description?: string;
  input: {
    messages: Array<{role: string; content: string}>;
    context?: Record<string, any>;
  };
  expected: {
    contains?: string[];
    not_contains?: string[];
    tool_called?: string[];
    tool_not_called?: string[];
    max_latency_ms?: number;
    max_tokens?: number;
    success?: boolean;
    graceful_error?: boolean;
    custom?: Record<string, any>;
  };
  timeout_seconds?: number;
  skip?: boolean;
  skip_reason?: string;
}

export interface EvaluatorConfig {
  name: string;
  threshold: number;
  required?: boolean;
  config?: Record<string, any>;
}

// Legacy support for old config format
export interface LegacyAgentTraceConfig {
  project: string;
  api_key?: string;
  api_url?: string;
  suites: LegacyTestSuite[];
  evaluators?: LegacyEvaluatorConfig[];
  thresholds?: ThresholdConfig;
}

export interface LegacyTestSuite {
  name: string;
  description?: string;
  test_cases: LegacyTestCase[];
  evaluators?: string[];
  parallel?: boolean;
  timeout?: number;
}

export interface LegacyTestCase {
  id: string;
  name: string;
  description?: string;
  input: Record<string, any>;
  expected_output?: Record<string, any>;
  metadata?: Record<string, any>;
  evaluators?: string[];
}

export interface LegacyEvaluatorConfig {
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
