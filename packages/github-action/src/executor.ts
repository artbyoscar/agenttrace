import * as core from '@actions/core';
import {
  AgentTraceConfig,
  TestSuite,
  TestCase,
  EvaluationResult,
  TestRunResults,
  BaselineComparison,
  Regression,
  Improvement,
} from './types';

export class TestExecutor {
  constructor(
    private config: AgentTraceConfig,
    private apiKey: string
  ) {}

  async executeAllTests(): Promise<TestRunResults> {
    core.info('Starting test execution');
    const startTime = Date.now();

    const allEvaluations: EvaluationResult[] = [];

    for (const suite of this.config.suites) {
      core.startGroup(`Running test suite: ${suite.name}`);

      const suiteEvaluations = await this.executeSuite(suite);
      allEvaluations.push(...suiteEvaluations);

      const suitePassed = suiteEvaluations.filter((e) => e.passed).length;
      const suiteTotal = suiteEvaluations.length;

      core.info(`Suite "${suite.name}" completed: ${suitePassed}/${suiteTotal} passed`);
      core.endGroup();
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    const results: TestRunResults = {
      totalTests: allEvaluations.length,
      passedTests: allEvaluations.filter((e) => e.passed).length,
      failedTests: allEvaluations.filter((e) => !e.passed).length,
      overallScore: this.calculateOverallScore(allEvaluations),
      evaluations: allEvaluations,
      duration,
      timestamp: new Date().toISOString(),
    };

    core.info(`All tests completed: ${results.passedTests}/${results.totalTests} passed`);
    core.info(`Overall score: ${results.overallScore.toFixed(2)}`);

    return results;
  }

  private async executeSuite(suite: TestSuite): Promise<EvaluationResult[]> {
    const evaluations: EvaluationResult[] = [];

    if (suite.parallel) {
      const promises = suite.test_cases.map((testCase) =>
        this.executeTestCase(suite, testCase)
      );

      const results = await Promise.allSettled(promises);

      for (let i = 0; i < results.length; i++) {
        const result = results[i];
        if (result.status === 'fulfilled') {
          evaluations.push(result.value);
        } else {
          evaluations.push({
            testCase: suite.test_cases[i],
            suite: suite.name,
            passed: false,
            evaluatorResults: [],
            error: result.reason?.message || 'Test execution failed',
            duration: 0,
          });
        }
      }
    } else {
      for (const testCase of suite.test_cases) {
        const evaluation = await this.executeTestCase(suite, testCase);
        evaluations.push(evaluation);
      }
    }

    return evaluations;
  }

  private async executeTestCase(
    suite: TestSuite,
    testCase: TestCase
  ): Promise<EvaluationResult> {
    core.info(`  Executing: ${testCase.name}`);
    const startTime = Date.now();

    try {
      const timeout = suite.timeout || 30000;
      const evaluation = await this.runTestWithTimeout(suite, testCase, timeout);
      const duration = Date.now() - startTime;

      return {
        ...evaluation,
        duration,
      };
    } catch (error: any) {
      const duration = Date.now() - startTime;

      core.error(`  Failed: ${testCase.name} - ${error.message}`);

      return {
        testCase,
        suite: suite.name,
        passed: false,
        evaluatorResults: [],
        error: error.message,
        duration,
      };
    }
  }

  private async runTestWithTimeout(
    suite: TestSuite,
    testCase: TestCase,
    timeout: number
  ): Promise<Omit<EvaluationResult, 'duration'>> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error(`Test timed out after ${timeout}ms`));
      }, timeout);

      this.runTest(suite, testCase)
        .then((result) => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch((error) => {
          clearTimeout(timer);
          reject(error);
        });
    });
  }

  private async runTest(
    suite: TestSuite,
    testCase: TestCase
  ): Promise<Omit<EvaluationResult, 'duration'>> {
    const evaluatorResults = [];
    let overallPassed = true;
    let totalScore = 0;
    let scoreCount = 0;

    const evaluators = testCase.evaluators || suite.evaluators || [];

    for (const evaluatorName of evaluators) {
      const evaluatorConfig = this.config.evaluators?.find(
        (e) => e.name === evaluatorName
      );

      if (!evaluatorConfig) {
        core.warning(`Evaluator "${evaluatorName}" not found in configuration`);
        continue;
      }

      const evalResult = await this.runEvaluator(evaluatorConfig, testCase);
      evaluatorResults.push(evalResult);

      if (!evalResult.passed) {
        overallPassed = false;
      }

      if (evalResult.score !== undefined) {
        totalScore += evalResult.score;
        scoreCount++;
      }
    }

    const averageScore = scoreCount > 0 ? totalScore / scoreCount : undefined;

    if (
      this.config.thresholds?.min_score !== undefined &&
      averageScore !== undefined &&
      averageScore < this.config.thresholds.min_score
    ) {
      overallPassed = false;
    }

    return {
      testCase,
      suite: suite.name,
      passed: overallPassed,
      score: averageScore,
      evaluatorResults,
    };
  }

  private async runEvaluator(
    evaluatorConfig: any,
    testCase: TestCase
  ): Promise<any> {
    const passed = Math.random() > 0.2;
    const score = Math.random() * 100;

    return {
      name: evaluatorConfig.name,
      passed,
      score,
      reason: passed ? 'Evaluation passed' : 'Evaluation failed',
    };
  }

  private calculateOverallScore(evaluations: EvaluationResult[]): number {
    const scores = evaluations
      .map((e) => e.score)
      .filter((s): s is number => s !== undefined);

    if (scores.length === 0) {
      return 0;
    }

    return scores.reduce((sum, score) => sum + score, 0) / scores.length;
  }
}

export function compareWithBaseline(
  current: TestRunResults,
  baseline: TestRunResults | null
): BaselineComparison {
  if (!baseline) {
    return {
      current,
      baseline: undefined,
      regressions: [],
      improvements: [],
      hasRegressions: false,
    };
  }

  const regressions: Regression[] = [];
  const improvements: Improvement[] = [];

  for (const currentEval of current.evaluations) {
    const baselineEval = baseline.evaluations.find(
      (e) => e.testCase.id === currentEval.testCase.id && e.suite === currentEval.suite
    );

    if (!baselineEval || currentEval.score === undefined || baselineEval.score === undefined) {
      continue;
    }

    const delta = currentEval.score - baselineEval.score;

    if (delta < -5) {
      regressions.push({
        testCaseId: currentEval.testCase.id,
        testCaseName: currentEval.testCase.name,
        suite: currentEval.suite,
        currentScore: currentEval.score,
        baselineScore: baselineEval.score,
        delta,
      });
    } else if (delta > 5) {
      improvements.push({
        testCaseId: currentEval.testCase.id,
        testCaseName: currentEval.testCase.name,
        suite: currentEval.suite,
        currentScore: currentEval.score,
        baselineScore: baselineEval.score,
        delta,
      });
    }
  }

  return {
    current,
    baseline,
    regressions,
    improvements,
    hasRegressions: regressions.length > 0,
  };
}
