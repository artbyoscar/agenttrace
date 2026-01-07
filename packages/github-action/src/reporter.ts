import * as core from '@actions/core';
import {
  TestRunResults,
  BaselineComparison,
  EvaluationResult,
  Regression,
  Improvement,
} from './types';

export function generatePRComment(
  results: TestRunResults,
  comparison?: BaselineComparison,
  dashboardUrl?: string
): string {
  const sections: string[] = [];

  sections.push('# AgentTrace Evaluation Results\n');

  sections.push(generateSummarySection(results, comparison));

  if (comparison?.regressions && comparison.regressions.length > 0) {
    sections.push(generateRegressionsSection(comparison.regressions));
  }

  if (comparison?.improvements && comparison.improvements.length > 0) {
    sections.push(generateImprovementsSection(comparison.improvements));
  }

  sections.push(generateDetailedResultsSection(results));

  if (dashboardUrl) {
    sections.push(`\n[View full results in AgentTrace Dashboard](${dashboardUrl})`);
  }

  sections.push('\n---\n*Automated evaluation by AgentTrace*');

  return sections.join('\n\n');
}

function generateSummarySection(
  results: TestRunResults,
  comparison?: BaselineComparison
): string {
  const passRate = ((results.passedTests / results.totalTests) * 100).toFixed(1);
  const statusIcon = results.passedTests === results.totalTests ? ':white_check_mark:' : ':x:';

  let summary = `## ${statusIcon} Summary\n\n`;
  summary += `| Metric | Value |\n`;
  summary += `|--------|-------|\n`;
  summary += `| **Tests Passed** | ${results.passedTests}/${results.totalTests} (${passRate}%) |\n`;
  summary += `| **Overall Score** | ${results.overallScore.toFixed(2)} |\n`;
  summary += `| **Duration** | ${(results.duration / 1000).toFixed(2)}s |\n`;

  if (comparison) {
    summary += `| **Regressions** | ${comparison.regressions.length} |\n`;
    summary += `| **Improvements** | ${comparison.improvements.length} |\n`;
  }

  return summary;
}

function generateRegressionsSection(regressions: Regression[]): string {
  let section = `## :warning: Regressions Detected\n\n`;
  section += `| Test Case | Suite | Current | Baseline | Delta |\n`;
  section += `|-----------|-------|---------|----------|-------|\n`;

  for (const regression of regressions) {
    const delta = regression.delta.toFixed(2);
    section += `| ${regression.testCaseName} | ${regression.suite} | ${regression.currentScore.toFixed(2)} | ${regression.baselineScore.toFixed(2)} | ${delta} |\n`;
  }

  return section;
}

function generateImprovementsSection(improvements: Improvement[]): string {
  let section = `## :chart_with_upwards_trend: Improvements\n\n`;
  section += `| Test Case | Suite | Current | Baseline | Delta |\n`;
  section += `|-----------|-------|---------|----------|-------|\n`;

  for (const improvement of improvements) {
    const delta = `+${improvement.delta.toFixed(2)}`;
    section += `| ${improvement.testCaseName} | ${improvement.suite} | ${improvement.currentScore.toFixed(2)} | ${improvement.baselineScore.toFixed(2)} | ${delta} |\n`;
  }

  return section;
}

function generateDetailedResultsSection(results: TestRunResults): string {
  let section = `## Detailed Results\n\n`;

  const suiteGroups = groupBySuite(results.evaluations);

  for (const [suiteName, evaluations] of Object.entries(suiteGroups)) {
    section += `### ${suiteName}\n\n`;

    for (const evaluation of evaluations) {
      const statusIcon = evaluation.passed ? ':white_check_mark:' : ':x:';
      section += `${statusIcon} **${evaluation.testCase.name}**`;

      if (evaluation.score !== undefined) {
        section += ` (Score: ${evaluation.score.toFixed(2)})`;
      }

      section += `\n`;

      if (evaluation.evaluatorResults && evaluation.evaluatorResults.length > 0) {
        for (const evalResult of evaluation.evaluatorResults) {
          const evalIcon = evalResult.passed ? ':white_check_mark:' : ':x:';
          section += `  ${evalIcon} ${evalResult.name}`;

          if (evalResult.score !== undefined) {
            section += ` (${evalResult.score.toFixed(2)})`;
          }

          if (evalResult.reason) {
            section += `: ${evalResult.reason}`;
          }

          section += `\n`;
        }
      }

      if (evaluation.error) {
        section += `  :warning: Error: ${evaluation.error}\n`;
      }

      section += `\n`;
    }
  }

  return section;
}

function groupBySuite(
  evaluations: EvaluationResult[]
): Record<string, EvaluationResult[]> {
  const groups: Record<string, EvaluationResult[]> = {};

  for (const evaluation of evaluations) {
    if (!groups[evaluation.suite]) {
      groups[evaluation.suite] = [];
    }
    groups[evaluation.suite].push(evaluation);
  }

  return groups;
}

export function logResultsSummary(
  results: TestRunResults,
  comparison?: BaselineComparison
): void {
  core.startGroup('Evaluation Summary');

  core.info(`Total Tests: ${results.totalTests}`);
  core.info(`Passed: ${results.passedTests}`);
  core.info(`Failed: ${results.failedTests}`);
  core.info(`Overall Score: ${results.overallScore.toFixed(2)}`);
  core.info(`Duration: ${(results.duration / 1000).toFixed(2)}s`);

  if (comparison) {
    core.info(`Regressions: ${comparison.regressions.length}`);
    core.info(`Improvements: ${comparison.improvements.length}`);

    if (comparison.regressions.length > 0) {
      core.warning('Regressions detected:');
      for (const regression of comparison.regressions) {
        core.warning(
          `  - ${regression.testCaseName}: ${regression.currentScore.toFixed(2)} (was ${regression.baselineScore.toFixed(2)})`
        );
      }
    }
  }

  core.endGroup();
}

export function logFailedTests(results: TestRunResults): void {
  const failedTests = results.evaluations.filter((e) => !e.passed);

  if (failedTests.length > 0) {
    core.startGroup('Failed Tests');

    for (const test of failedTests) {
      core.error(`${test.suite} - ${test.testCase.name}`);

      if (test.error) {
        core.error(`  Error: ${test.error}`);
      }

      if (test.evaluatorResults) {
        for (const evalResult of test.evaluatorResults) {
          if (!evalResult.passed) {
            core.error(`  ${evalResult.name}: ${evalResult.reason || 'Failed'}`);
          }
        }
      }
    }

    core.endGroup();
  }
}
