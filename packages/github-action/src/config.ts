import * as core from '@actions/core';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { z } from 'zod';
import { ActionInputs, AgentTraceConfig, TestCase, EvaluatorConfig } from './types';

// Zod schemas for validation
const MessageSchema = z.object({
  role: z.string(),
  content: z.string(),
});

const TestCaseExpectedSchema = z.object({
  contains: z.array(z.string()).optional(),
  not_contains: z.array(z.string()).optional(),
  tool_called: z.array(z.string()).optional(),
  tool_not_called: z.array(z.string()).optional(),
  max_latency_ms: z.number().positive().optional(),
  max_tokens: z.number().positive().optional(),
  success: z.boolean().optional(),
  graceful_error: z.boolean().optional(),
  custom: z.record(z.any()).optional(),
});

const TestCaseSchema = z.object({
  name: z.string().min(1, 'Test case name is required'),
  description: z.string().optional(),
  input: z.object({
    messages: z.array(MessageSchema).min(1, 'At least one message is required'),
    context: z.record(z.any()).optional(),
  }),
  expected: TestCaseExpectedSchema,
  timeout_seconds: z.number().positive().optional(),
  skip: z.boolean().optional(),
  skip_reason: z.string().optional(),
});

const TestSuiteSchema = z.object({
  name: z.string().min(1, 'Test suite name is required'),
  description: z.string().optional(),
  tags: z.array(z.string()).optional(),
  test_cases: z.array(TestCaseSchema).min(1, 'At least one test case is required'),
});

const EvaluatorConfigSchema = z.object({
  name: z.string().min(1, 'Evaluator name is required'),
  threshold: z.number().min(0).max(1, 'Threshold must be between 0 and 1'),
  required: z.boolean().optional(),
  config: z.record(z.any()).optional(),
});

const AgentTraceConfigSchema = z.object({
  version: z.literal(1),
  project: z.object({
    name: z.string().min(1, 'Project name is required'),
    id: z.string().optional(),
  }),
  agent: z.object({
    module: z.string().min(1, 'Agent module is required'),
    function: z.string().min(1, 'Agent function is required'),
    setup_command: z.string().optional(),
    env_file: z.string().optional(),
  }),
  test_suites: z.array(TestSuiteSchema).min(1, 'At least one test suite is required'),
  evaluators: z.array(EvaluatorConfigSchema),
  baseline: z.object({
    branch: z.string().min(1, 'Baseline branch is required'),
    require_improvement: z.boolean().optional(),
    regression_threshold: z.number().min(0).max(1).optional(),
  }),
  reporting: z.object({
    comment_on_pr: z.boolean(),
    detailed_traces: z.boolean(),
    upload_traces: z.boolean(),
    badge_style: z.enum(['flat', 'flat-square', 'plastic']).optional(),
  }),
  execution: z.object({
    timeout_seconds: z.number().positive().optional(),
    max_retries: z.number().int().min(0).optional(),
    parallelism: z.number().int().positive().optional(),
  }),
});

// Default configuration values
const DEFAULT_CONFIG: Partial<AgentTraceConfig> = {
  baseline: {
    branch: 'main',
    require_improvement: false,
    regression_threshold: 0.05,
  },
  reporting: {
    comment_on_pr: true,
    detailed_traces: true,
    upload_traces: true,
    badge_style: 'flat',
  },
  execution: {
    timeout_seconds: 300,
    max_retries: 0,
    parallelism: 1,
  },
};

/**
 * Get action inputs from GitHub Action environment
 */
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

/**
 * Interpolate environment variables in a string
 * Supports ${VAR_NAME} syntax
 */
export function interpolateEnvVars(str: string): string {
  return str.replace(/\$\{([^}]+)\}/g, (match, varName) => {
    const value = process.env[varName];
    if (value === undefined) {
      core.warning(`Environment variable ${varName} is not defined, keeping placeholder`);
      return match;
    }
    return value;
  });
}

/**
 * Recursively interpolate environment variables in an object
 */
export function interpolateEnvVarsInObject(obj: any): any {
  if (typeof obj === 'string') {
    return interpolateEnvVars(obj);
  }

  if (Array.isArray(obj)) {
    return obj.map(item => interpolateEnvVarsInObject(item));
  }

  if (obj !== null && typeof obj === 'object') {
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = interpolateEnvVarsInObject(value);
    }
    return result;
  }

  return obj;
}

/**
 * Custom YAML type for file inclusion (!include path/to/file.yaml)
 */
const IncludeYamlType = new yaml.Type('!include', {
  kind: 'scalar',
  resolve(data: any): boolean {
    return typeof data === 'string';
  },
  construct(data: string): any {
    const includePath = data;
    const baseDir = process.env.GITHUB_WORKSPACE || process.cwd();
    const fullPath = path.resolve(baseDir, includePath);

    if (!fs.existsSync(fullPath)) {
      throw new Error(`Included file not found: ${fullPath}`);
    }

    const fileContents = fs.readFileSync(fullPath, 'utf8');

    if (fullPath.endsWith('.yaml') || fullPath.endsWith('.yml')) {
      return yaml.load(fileContents, { schema: CUSTOM_SCHEMA });
    } else if (fullPath.endsWith('.json')) {
      return JSON.parse(fileContents);
    } else {
      throw new Error(`Unsupported file type for inclusion: ${fullPath}`);
    }
  },
});

// Custom YAML schema with include support
const CUSTOM_SCHEMA = yaml.DEFAULT_SCHEMA.extend([IncludeYamlType]);

/**
 * Load and parse YAML file with custom schema
 */
export function loadYamlFile(filePath: string): any {
  const fileContents = fs.readFileSync(filePath, 'utf8');

  try {
    return yaml.load(fileContents, { schema: CUSTOM_SCHEMA });
  } catch (error) {
    if (error instanceof yaml.YAMLException) {
      throw new Error(
        `Failed to parse YAML file ${filePath}:\n` +
        `  Line ${error.mark?.line}: ${error.message}`
      );
    }
    throw error;
  }
}

/**
 * Apply default values to configuration
 */
export function applyDefaults(config: Partial<AgentTraceConfig>): AgentTraceConfig {
  return {
    ...config,
    baseline: {
      ...DEFAULT_CONFIG.baseline,
      ...config.baseline,
    },
    reporting: {
      ...DEFAULT_CONFIG.reporting,
      ...config.reporting,
    },
    execution: {
      ...DEFAULT_CONFIG.execution,
      ...config.execution,
    },
  } as AgentTraceConfig;
}

/**
 * Load configuration from file
 */
export function loadConfig(configPath: string): AgentTraceConfig {
  core.info(`Loading configuration from ${configPath}`);

  if (!fs.existsSync(configPath)) {
    throw new Error(`Configuration file not found: ${configPath}`);
  }

  let rawConfig: any;

  try {
    if (configPath.endsWith('.yaml') || configPath.endsWith('.yml')) {
      rawConfig = loadYamlFile(configPath);
    } else if (configPath.endsWith('.json')) {
      const fileContents = fs.readFileSync(configPath, 'utf8');
      rawConfig = JSON.parse(fileContents);
    } else {
      throw new Error('Configuration file must be .yaml, .yml, or .json');
    }
  } catch (error) {
    throw new Error(`Failed to parse configuration file: ${error}`);
  }

  // Interpolate environment variables
  rawConfig = interpolateEnvVarsInObject(rawConfig);

  // Apply defaults
  const configWithDefaults = applyDefaults(rawConfig);

  // Validate against schema
  const validatedConfig = validateConfig(configWithDefaults);

  return validatedConfig;
}

/**
 * Validate configuration against schema
 */
export function validateConfig(config: any): AgentTraceConfig {
  try {
    return AgentTraceConfigSchema.parse(config);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.errors.map(err => {
        const path = err.path.join('.');
        return `  - ${path}: ${err.message}`;
      });

      throw new Error(
        'Configuration validation failed:\n' + errorMessages.join('\n')
      );
    }
    throw error;
  }
}

/**
 * Validate a single test case
 */
export function validateTestCase(testCase: any): TestCase {
  try {
    return TestCaseSchema.parse(testCase);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.errors.map(err => {
        const path = err.path.join('.');
        return `  - ${path}: ${err.message}`;
      });

      throw new Error(
        `Test case "${testCase.name || 'unnamed'}" validation failed:\n` +
        errorMessages.join('\n')
      );
    }
    throw error;
  }
}

/**
 * Validate evaluator configuration
 */
export function validateEvaluatorConfig(evaluator: any): EvaluatorConfig {
  try {
    return EvaluatorConfigSchema.parse(evaluator);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.errors.map(err => {
        const path = err.path.join('.');
        return `  - ${path}: ${err.message}`;
      });

      throw new Error(
        `Evaluator "${evaluator.name || 'unnamed'}" validation failed:\n` +
        errorMessages.join('\n')
      );
    }
    throw error;
  }
}

/**
 * Resolve configuration file path relative to workspace
 */
export function resolveConfigPath(relativePath: string): string {
  const workspacePath = process.env.GITHUB_WORKSPACE || process.cwd();
  return path.resolve(workspacePath, relativePath);
}

/**
 * Load environment variables from .env file
 */
export function loadEnvFile(envFilePath: string): void {
  const fullPath = resolveConfigPath(envFilePath);

  if (!fs.existsSync(fullPath)) {
    core.warning(`Environment file not found: ${fullPath}`);
    return;
  }

  const envContent = fs.readFileSync(fullPath, 'utf8');
  const lines = envContent.split('\n');

  for (const line of lines) {
    const trimmed = line.trim();

    // Skip empty lines and comments
    if (!trimmed || trimmed.startsWith('#')) {
      continue;
    }

    // Parse KEY=VALUE format
    const match = trimmed.match(/^([^=]+)=(.*)$/);
    if (match) {
      const [, key, value] = match;
      const trimmedKey = key.trim();
      const trimmedValue = value.trim();

      // Remove quotes if present
      const unquotedValue = trimmedValue.replace(/^["'](.*)["']$/, '$1');

      // Only set if not already defined
      if (!process.env[trimmedKey]) {
        process.env[trimmedKey] = unquotedValue;
      }
    }
  }

  core.info(`Loaded environment variables from ${envFilePath}`);
}

/**
 * Get configuration summary for logging
 */
export function getConfigSummary(config: AgentTraceConfig): string {
  const totalTestCases = config.test_suites.reduce(
    (sum, suite) => sum + suite.test_cases.length,
    0
  );

  const skippedTestCases = config.test_suites.reduce(
    (sum, suite) => sum + suite.test_cases.filter(tc => tc.skip).length,
    0
  );

  return [
    `Configuration Summary:`,
    `  Project: ${config.project.name}`,
    `  Agent: ${config.agent.module}.${config.agent.function}`,
    `  Test Suites: ${config.test_suites.length}`,
    `  Total Test Cases: ${totalTestCases}`,
    `  Skipped Test Cases: ${skippedTestCases}`,
    `  Evaluators: ${config.evaluators.length}`,
    `  Baseline Branch: ${config.baseline.branch}`,
    `  Regression Threshold: ${config.baseline.regression_threshold}`,
  ].join('\n');
}
