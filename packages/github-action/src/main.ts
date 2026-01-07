import * as core from '@actions/core';
import * as fs from 'fs';
import * as path from 'path';
import { getActionInputs, loadConfig, resolveConfigPath } from './config';
import { TestExecutor, compareWithBaseline } from './executor';
import {
  generatePRComment,
  logResultsSummary,
  logFailedTests,
} from './reporter';
import {
  getGitHubContext,
  postPRComment,
  setCommitStatus,
  fetchBaselineResults,
} from './github';
import { ActionOutputs, TestRunResults } from './types';

async function run(): Promise<void> {
  try {
    core.info('Starting AgentTrace evaluation');

    const inputs = getActionInputs();
    const configPath = resolveConfigPath(inputs.configFile);
    const config = loadConfig(configPath);

    const executor = new TestExecutor(config, inputs.apiKey);
    const githubContext = getGitHubContext();

    const githubToken = process.env.GITHUB_TOKEN;
    if (!githubToken) {
      core.warning('GITHUB_TOKEN not found, some features may be limited');
    }

    if (githubToken) {
      await setCommitStatus(
        githubToken,
        githubContext,
        'pending',
        'Running AgentTrace evaluation...'
      );
    }

    const results = await executor.executeAllTests();

    const resultsPath = path.join(
      process.env.GITHUB_WORKSPACE || process.cwd(),
      '.agenttrace',
      'results.json'
    );

    const resultsDir = path.dirname(resultsPath);
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }

    fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
    core.info(`Results saved to ${resultsPath}`);

    let baseline: TestRunResults | null = null;
    if (githubToken) {
      baseline = await fetchBaselineResults(
        githubToken,
        githubContext,
        inputs.baselineBranch,
        '.agenttrace/results.json'
      );
    }

    const comparison = compareWithBaseline(results, baseline);

    logResultsSummary(results, comparison);
    logFailedTests(results);

    const dashboardUrl = inputs.uploadTraces
      ? `https://app.agenttrace.com/projects/${config.project}/runs/latest`
      : undefined;

    if (inputs.commentOnPr && githubToken) {
      const comment = generatePRComment(results, comparison, dashboardUrl);
      await postPRComment(githubToken, githubContext, {
        body: comment,
        isUpdate: true,
      });
    }

    const outputs: ActionOutputs = {
      passCount: results.passedTests,
      failCount: results.failedTests,
      regressionCount: comparison.regressions.length,
      overallScore: results.overallScore,
      resultsUrl: dashboardUrl,
    };

    core.setOutput('pass_count', outputs.passCount);
    core.setOutput('fail_count', outputs.failCount);
    core.setOutput('regression_count', outputs.regressionCount);
    core.setOutput('overall_score', outputs.overallScore.toFixed(2));

    if (outputs.resultsUrl) {
      core.setOutput('results_url', outputs.resultsUrl);
    }

    let shouldFail = false;
    let failureReason = '';

    if (inputs.failOnRegression && comparison.hasRegressions) {
      shouldFail = true;
      failureReason = `${comparison.regressions.length} regression(s) detected`;
    }

    if (inputs.failOnThreshold && config.thresholds) {
      if (
        config.thresholds.min_score !== undefined &&
        results.overallScore < config.thresholds.min_score
      ) {
        shouldFail = true;
        failureReason = `Overall score ${results.overallScore.toFixed(2)} below threshold ${config.thresholds.min_score}`;
      }

      if (
        config.thresholds.max_failures !== undefined &&
        results.failedTests > config.thresholds.max_failures
      ) {
        shouldFail = true;
        failureReason = `${results.failedTests} failures exceed threshold of ${config.thresholds.max_failures}`;
      }

      if (
        config.thresholds.max_regressions !== undefined &&
        comparison.regressions.length > config.thresholds.max_regressions
      ) {
        shouldFail = true;
        failureReason = `${comparison.regressions.length} regressions exceed threshold of ${config.thresholds.max_regressions}`;
      }
    }

    if (githubToken) {
      const status = shouldFail ? 'failure' : 'success';
      const description = shouldFail
        ? failureReason
        : `All tests passed (${results.passedTests}/${results.totalTests})`;

      await setCommitStatus(githubToken, githubContext, status, description, dashboardUrl);
    }

    if (shouldFail) {
      core.setFailed(failureReason);
    } else {
      core.info('Evaluation completed successfully');
    }
  } catch (error: any) {
    const errorMessage = error.message || 'Unknown error occurred';
    core.setFailed(errorMessage);

    const githubToken = process.env.GITHUB_TOKEN;
    if (githubToken) {
      const githubContext = getGitHubContext();
      await setCommitStatus(
        githubToken,
        githubContext,
        'failure',
        `Evaluation failed: ${errorMessage}`
      );
    }
  }
}

run();
