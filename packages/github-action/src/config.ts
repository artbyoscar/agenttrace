import * as core from '@actions/core';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { ActionInputs, AgentTraceConfig } from './types';

export function getActionInputs(): ActionInputs {
  return {
    apiKey: core.getInput('api_key', { required: true }),
    configFile: core.getInput('config_file') || 'agenttrace.yaml',
    failOnRegression: core.getBooleanInput('fail_on_regression'),
    failOnThreshold: core.getBooleanInput('fail_on_threshold'),
    commentOnPr: core.getBooleanInput('comment_on_pr'),
    uploadTraces: core.getBooleanInput('upload_traces'),
    baselineBranch: core.getInput('baseline_branch') || 'main',
  };
}

export function loadConfig(configPath: string): AgentTraceConfig {
  core.info(`Loading configuration from ${configPath}`);

  if (!fs.existsSync(configPath)) {
    throw new Error(`Configuration file not found: ${configPath}`);
  }

  const fileContents = fs.readFileSync(configPath, 'utf8');
  let config: AgentTraceConfig;

  try {
    if (configPath.endsWith('.yaml') || configPath.endsWith('.yml')) {
      config = yaml.load(fileContents) as AgentTraceConfig;
    } else if (configPath.endsWith('.json')) {
      config = JSON.parse(fileContents);
    } else {
      throw new Error('Configuration file must be .yaml, .yml, or .json');
    }
  } catch (error) {
    throw new Error(`Failed to parse configuration file: ${error}`);
  }

  validateConfig(config);
  return config;
}

export function validateConfig(config: AgentTraceConfig): void {
  if (!config.project) {
    throw new Error('Configuration must include a "project" field');
  }

  if (!config.suites || config.suites.length === 0) {
    throw new Error('Configuration must include at least one test suite');
  }

  for (const suite of config.suites) {
    if (!suite.name) {
      throw new Error('Each test suite must have a "name" field');
    }

    if (!suite.test_cases || suite.test_cases.length === 0) {
      throw new Error(`Test suite "${suite.name}" must have at least one test case`);
    }

    for (const testCase of suite.test_cases) {
      if (!testCase.id) {
        throw new Error(`Test case in suite "${suite.name}" must have an "id" field`);
      }

      if (!testCase.name) {
        throw new Error(`Test case "${testCase.id}" must have a "name" field`);
      }

      if (!testCase.input) {
        throw new Error(`Test case "${testCase.id}" must have an "input" field`);
      }
    }
  }

  core.info(`Configuration validated successfully`);
  core.info(`Project: ${config.project}`);
  core.info(`Test suites: ${config.suites.length}`);
  core.info(
    `Total test cases: ${config.suites.reduce((sum, suite) => sum + suite.test_cases.length, 0)}`
  );
}

export function resolveConfigPath(relativePath: string): string {
  const workspacePath = process.env.GITHUB_WORKSPACE || process.cwd();
  return path.resolve(workspacePath, relativePath);
}
