import * as path from 'path';
import * as fs from 'fs';
import {
  loadConfig,
  validateConfig,
  validateTestCase,
  validateEvaluatorConfig,
  interpolateEnvVars,
  interpolateEnvVarsInObject,
  applyDefaults,
  loadEnvFile,
  getConfigSummary,
  resolveConfigPath,
} from '../src/config';
import { AgentTraceConfig } from '../src/types';

// Mock @actions/core
jest.mock('@actions/core', () => ({
  info: jest.fn(),
  warning: jest.fn(),
  error: jest.fn(),
  setFailed: jest.fn(),
  getInput: jest.fn(),
  getBooleanInput: jest.fn(),
}));

const FIXTURES_DIR = path.join(__dirname, 'fixtures');

describe('Configuration Parser', () => {
  beforeEach(() => {
    // Clear environment variables
    delete process.env.PROJECT_NAME;
    delete process.env.PROJECT_ID;
    delete process.env.AGENT_MODULE;
    delete process.env.USER_NAME;
    delete process.env.BASE_BRANCH;
    delete process.env.API_KEY;
    delete process.env.DATABASE_URL;
    delete process.env.DEBUG;
    delete process.env.MAX_RETRIES;
    delete process.env.QUOTED_VALUE;
    delete process.env.SINGLE_QUOTED;
  });

  describe('loadConfig', () => {
    test('should load and validate a valid configuration file', () => {
      const configPath = path.join(FIXTURES_DIR, 'valid-config.yaml');
      const config = loadConfig(configPath);

      expect(config.version).toBe(1);
      expect(config.project.name).toBe('customer-support-agent');
      expect(config.agent.module).toBe('src.agents.support');
      expect(config.agent.function).toBe('SupportAgent');
      expect(config.test_suites).toHaveLength(2);
      expect(config.evaluators).toHaveLength(3);
      expect(config.baseline.branch).toBe('main');
      expect(config.reporting.comment_on_pr).toBe(true);
      expect(config.execution.timeout_seconds).toBe(300);
    });

    test('should throw error for non-existent file', () => {
      const configPath = path.join(FIXTURES_DIR, 'non-existent.yaml');

      expect(() => loadConfig(configPath)).toThrow('Configuration file not found');
    });

    test('should throw error for invalid file extension', () => {
      const configPath = path.join(FIXTURES_DIR, 'config.txt');

      // Create a dummy file
      fs.writeFileSync(configPath, 'test');

      expect(() => loadConfig(configPath)).toThrow(
        'Configuration file must be .yaml, .yml, or .json'
      );

      // Clean up
      fs.unlinkSync(configPath);
    });

    test('should apply default values', () => {
      const configPath = path.join(FIXTURES_DIR, 'valid-config.yaml');
      const config = loadConfig(configPath);

      // Check that defaults are applied
      expect(config.baseline.require_improvement).toBe(false);
      expect(config.baseline.regression_threshold).toBe(0.05);
      expect(config.reporting.badge_style).toBe('flat');
    });

    test('should preserve user-specified values over defaults', () => {
      const configPath = path.join(FIXTURES_DIR, 'valid-config.yaml');
      const config = loadConfig(configPath);

      // User specified these values
      expect(config.execution.timeout_seconds).toBe(300);
      expect(config.execution.max_retries).toBe(2);
      expect(config.execution.parallelism).toBe(4);
    });
  });

  describe('Environment Variable Interpolation', () => {
    test('should interpolate environment variables in strings', () => {
      process.env.TEST_VAR = 'test-value';

      const result = interpolateEnvVars('Hello ${TEST_VAR}!');
      expect(result).toBe('Hello test-value!');
    });

    test('should handle multiple environment variables', () => {
      process.env.VAR1 = 'value1';
      process.env.VAR2 = 'value2';

      const result = interpolateEnvVars('${VAR1} and ${VAR2}');
      expect(result).toBe('value1 and value2');
    });

    test('should keep placeholder if environment variable is not defined', () => {
      const result = interpolateEnvVars('Hello ${UNDEFINED_VAR}!');
      expect(result).toBe('Hello ${UNDEFINED_VAR}!');
    });

    test('should interpolate environment variables in objects', () => {
      process.env.PROJECT_NAME = 'my-project';
      process.env.AGENT_MODULE = 'my.module';

      const obj = {
        name: '${PROJECT_NAME}',
        module: '${AGENT_MODULE}',
        nested: {
          value: '${PROJECT_NAME}',
        },
        array: ['${PROJECT_NAME}', 'static'],
      };

      const result = interpolateEnvVarsInObject(obj);

      expect(result.name).toBe('my-project');
      expect(result.module).toBe('my.module');
      expect(result.nested.value).toBe('my-project');
      expect(result.array[0]).toBe('my-project');
      expect(result.array[1]).toBe('static');
    });

    test('should load config with environment variable interpolation', () => {
      process.env.PROJECT_NAME = 'test-project';
      process.env.PROJECT_ID = 'proj-123';
      process.env.AGENT_MODULE = 'test.agent';
      process.env.USER_NAME = 'Alice';
      process.env.BASE_BRANCH = 'develop';

      const configPath = path.join(FIXTURES_DIR, 'config-with-env-vars.yaml');
      const config = loadConfig(configPath);

      expect(config.project.name).toBe('test-project');
      expect(config.project.id).toBe('proj-123');
      expect(config.agent.module).toBe('test.agent');
      expect(config.baseline.branch).toBe('develop');
      expect(config.test_suites[0].test_cases[0].input.messages[0].content).toBe(
        'Hello Alice'
      );
    });
  });

  describe('File Inclusion', () => {
    test('should include external YAML files', () => {
      const configPath = path.join(FIXTURES_DIR, 'config-with-include.yaml');
      const config = loadConfig(configPath);

      expect(config.test_suites[0].test_cases).toHaveLength(2);
      expect(config.test_suites[0].test_cases[0].name).toBe('greeting_test');
      expect(config.test_suites[0].test_cases[1].name).toBe('farewell_test');
    });

    test('should throw error for non-existent included file', () => {
      const configPath = path.join(FIXTURES_DIR, 'temp-include-test.yaml');

      const configContent = `
version: 1
project:
  name: test
agent:
  module: test
  function: Test
test_suites:
  - name: test
    test_cases: !include non-existent.yaml
evaluators: []
baseline:
  branch: main
reporting:
  comment_on_pr: true
  detailed_traces: true
  upload_traces: true
`;

      fs.writeFileSync(configPath, configContent);

      expect(() => loadConfig(configPath)).toThrow('Included file not found');

      // Clean up
      fs.unlinkSync(configPath);
    });
  });

  describe('Validation', () => {
    test('should validate a valid configuration', () => {
      const validConfig: AgentTraceConfig = {
        version: 1,
        project: {
          name: 'test-project',
        },
        agent: {
          module: 'test.agent',
          function: 'TestAgent',
        },
        test_suites: [
          {
            name: 'test-suite',
            test_cases: [
              {
                name: 'test-case',
                input: {
                  messages: [{ role: 'user', content: 'test' }],
                },
                expected: {
                  success: true,
                },
              },
            ],
          },
        ],
        evaluators: [
          {
            name: 'accuracy',
            threshold: 0.8,
          },
        ],
        baseline: {
          branch: 'main',
        },
        reporting: {
          comment_on_pr: true,
          detailed_traces: true,
          upload_traces: true,
        },
        execution: {
          timeout_seconds: 300,
        },
      };

      expect(() => validateConfig(validConfig)).not.toThrow();
    });

    test('should reject config with missing required fields', () => {
      const configPath = path.join(FIXTURES_DIR, 'invalid-config-missing-required.yaml');

      expect(() => loadConfig(configPath)).toThrow('Configuration validation failed');
      expect(() => loadConfig(configPath)).toThrow('agent');
    });

    test('should reject config with invalid threshold', () => {
      const configPath = path.join(FIXTURES_DIR, 'invalid-config-bad-threshold.yaml');

      expect(() => loadConfig(configPath)).toThrow('Configuration validation failed');
      expect(() => loadConfig(configPath)).toThrow('threshold');
    });

    test('should reject config with empty test suite', () => {
      const invalidConfig = {
        version: 1,
        project: { name: 'test' },
        agent: { module: 'test', function: 'Test' },
        test_suites: [
          {
            name: 'empty-suite',
            test_cases: [], // Empty!
          },
        ],
        evaluators: [],
        baseline: { branch: 'main' },
        reporting: {
          comment_on_pr: true,
          detailed_traces: true,
          upload_traces: true,
        },
        execution: {},
      };

      expect(() => validateConfig(invalidConfig)).toThrow('At least one test case is required');
    });

    test('should reject test case with no messages', () => {
      const invalidTestCase = {
        name: 'test',
        input: {
          messages: [], // Empty!
        },
        expected: {
          success: true,
        },
      };

      expect(() => validateTestCase(invalidTestCase)).toThrow(
        'At least one message is required'
      );
    });

    test('should reject evaluator with invalid threshold', () => {
      const invalidEvaluator = {
        name: 'accuracy',
        threshold: 2.0, // Invalid: > 1
      };

      expect(() => validateEvaluatorConfig(invalidEvaluator)).toThrow(
        'Threshold must be between 0 and 1'
      );
    });
  });

  describe('validateTestCase', () => {
    test('should validate a valid test case', () => {
      const testCase = {
        name: 'test-case',
        input: {
          messages: [{ role: 'user', content: 'test' }],
        },
        expected: {
          success: true,
          contains: ['hello'],
        },
      };

      const validated = validateTestCase(testCase);
      expect(validated.name).toBe('test-case');
    });

    test('should reject test case without name', () => {
      const testCase = {
        input: {
          messages: [{ role: 'user', content: 'test' }],
        },
        expected: {
          success: true,
        },
      };

      expect(() => validateTestCase(testCase)).toThrow('Test case name is required');
    });

    test('should accept optional fields', () => {
      const testCase = {
        name: 'comprehensive-test',
        description: 'A comprehensive test',
        input: {
          messages: [{ role: 'user', content: 'test' }],
          context: { userId: '123' },
        },
        expected: {
          success: true,
          contains: ['hello'],
          not_contains: ['error'],
          tool_called: ['lookup'],
          max_latency_ms: 1000,
          max_tokens: 500,
        },
        timeout_seconds: 30,
        skip: false,
      };

      const validated = validateTestCase(testCase);
      expect(validated.description).toBe('A comprehensive test');
      expect(validated.timeout_seconds).toBe(30);
    });
  });

  describe('validateEvaluatorConfig', () => {
    test('should validate a valid evaluator config', () => {
      const evaluator = {
        name: 'accuracy',
        threshold: 0.8,
        required: true,
        config: {
          model: 'gpt-4',
        },
      };

      const validated = validateEvaluatorConfig(evaluator);
      expect(validated.name).toBe('accuracy');
      expect(validated.threshold).toBe(0.8);
    });

    test('should reject evaluator without name', () => {
      const evaluator = {
        threshold: 0.8,
      };

      expect(() => validateEvaluatorConfig(evaluator)).toThrow('Evaluator name is required');
    });

    test('should reject evaluator with negative threshold', () => {
      const evaluator = {
        name: 'accuracy',
        threshold: -0.5,
      };

      expect(() => validateEvaluatorConfig(evaluator)).toThrow();
    });
  });

  describe('applyDefaults', () => {
    test('should apply default values for missing fields', () => {
      const partialConfig = {
        version: 1,
        project: { name: 'test' },
        agent: { module: 'test', function: 'Test' },
        test_suites: [],
        evaluators: [],
        baseline: { branch: 'develop' },
        reporting: { comment_on_pr: false, detailed_traces: false, upload_traces: false },
        execution: {},
      };

      const result = applyDefaults(partialConfig);

      // Defaults should be applied
      expect(result.baseline.require_improvement).toBe(false);
      expect(result.baseline.regression_threshold).toBe(0.05);
      expect(result.execution.timeout_seconds).toBe(300);
      expect(result.execution.max_retries).toBe(0);
      expect(result.execution.parallelism).toBe(1);

      // User values should be preserved
      expect(result.baseline.branch).toBe('develop');
      expect(result.reporting.comment_on_pr).toBe(false);
    });
  });

  describe('loadEnvFile', () => {
    test('should load environment variables from .env file', () => {
      const envPath = path.join(FIXTURES_DIR, '.env.test');

      loadEnvFile(envPath);

      expect(process.env.API_KEY).toBe('test-api-key-12345');
      expect(process.env.DATABASE_URL).toBe('postgresql://localhost:5432/test');
      expect(process.env.DEBUG).toBe('true');
      expect(process.env.MAX_RETRIES).toBe('3');
      expect(process.env.QUOTED_VALUE).toBe('some value with spaces');
      expect(process.env.SINGLE_QUOTED).toBe('another value');
    });

    test('should not override existing environment variables', () => {
      process.env.API_KEY = 'existing-key';

      const envPath = path.join(FIXTURES_DIR, '.env.test');
      loadEnvFile(envPath);

      expect(process.env.API_KEY).toBe('existing-key');
    });

    test('should handle non-existent .env file gracefully', () => {
      expect(() => loadEnvFile('non-existent.env')).not.toThrow();
    });
  });

  describe('getConfigSummary', () => {
    test('should generate a config summary', () => {
      const configPath = path.join(FIXTURES_DIR, 'valid-config.yaml');
      const config = loadConfig(configPath);

      const summary = getConfigSummary(config);

      expect(summary).toContain('Configuration Summary');
      expect(summary).toContain('Project: customer-support-agent');
      expect(summary).toContain('Agent: src.agents.support.SupportAgent');
      expect(summary).toContain('Test Suites: 2');
      expect(summary).toContain('Total Test Cases: 3');
      expect(summary).toContain('Evaluators: 3');
      expect(summary).toContain('Baseline Branch: main');
    });

    test('should count skipped test cases', () => {
      const config: AgentTraceConfig = {
        version: 1,
        project: { name: 'test' },
        agent: { module: 'test', function: 'Test' },
        test_suites: [
          {
            name: 'suite1',
            test_cases: [
              {
                name: 'test1',
                input: { messages: [{ role: 'user', content: 'test' }] },
                expected: { success: true },
              },
              {
                name: 'test2',
                input: { messages: [{ role: 'user', content: 'test' }] },
                expected: { success: true },
                skip: true,
              },
            ],
          },
        ],
        evaluators: [],
        baseline: { branch: 'main', regression_threshold: 0.05 },
        reporting: {
          comment_on_pr: true,
          detailed_traces: true,
          upload_traces: true,
        },
        execution: { timeout_seconds: 300 },
      };

      const summary = getConfigSummary(config);

      expect(summary).toContain('Total Test Cases: 2');
      expect(summary).toContain('Skipped Test Cases: 1');
    });
  });

  describe('resolveConfigPath', () => {
    test('should resolve relative path from workspace', () => {
      process.env.GITHUB_WORKSPACE = '/workspace';

      const resolved = resolveConfigPath('config.yaml');

      expect(resolved).toBe(path.resolve('/workspace', 'config.yaml'));
    });

    test('should use cwd if GITHUB_WORKSPACE is not set', () => {
      delete process.env.GITHUB_WORKSPACE;

      const resolved = resolveConfigPath('config.yaml');

      expect(resolved).toBe(path.resolve(process.cwd(), 'config.yaml'));
    });
  });

  describe('Edge Cases', () => {
    test('should handle test case with all optional expected fields', () => {
      const testCase = {
        name: 'comprehensive-test',
        input: {
          messages: [{ role: 'user', content: 'test' }],
        },
        expected: {
          contains: ['hello', 'world'],
          not_contains: ['error', 'fail'],
          tool_called: ['search', 'lookup'],
          tool_not_called: ['delete', 'update'],
          max_latency_ms: 5000,
          max_tokens: 1000,
          success: true,
          graceful_error: false,
          custom: {
            sentiment: 'positive',
            language: 'en',
          },
        },
      };

      const validated = validateTestCase(testCase);
      expect(validated.expected.contains).toHaveLength(2);
      expect(validated.expected.custom?.sentiment).toBe('positive');
    });

    test('should handle minimal valid config', () => {
      const minimalConfig = {
        version: 1,
        project: { name: 'minimal' },
        agent: { module: 'test', function: 'Test' },
        test_suites: [
          {
            name: 'suite',
            test_cases: [
              {
                name: 'test',
                input: {
                  messages: [{ role: 'user', content: 'test' }],
                },
                expected: {},
              },
            ],
          },
        ],
        evaluators: [],
        baseline: { branch: 'main' },
        reporting: {
          comment_on_pr: true,
          detailed_traces: true,
          upload_traces: true,
        },
        execution: {},
      };

      const validated = validateConfig(minimalConfig);
      expect(validated.project.name).toBe('minimal');
    });

    test('should handle multiple test suites with different tags', () => {
      const config: AgentTraceConfig = {
        version: 1,
        project: { name: 'test' },
        agent: { module: 'test', function: 'Test' },
        test_suites: [
          {
            name: 'suite1',
            tags: ['smoke', 'critical'],
            test_cases: [
              {
                name: 'test1',
                input: { messages: [{ role: 'user', content: 'test' }] },
                expected: { success: true },
              },
            ],
          },
          {
            name: 'suite2',
            tags: ['integration', 'slow'],
            test_cases: [
              {
                name: 'test2',
                input: { messages: [{ role: 'user', content: 'test' }] },
                expected: { success: true },
              },
            ],
          },
        ],
        evaluators: [],
        baseline: { branch: 'main' },
        reporting: {
          comment_on_pr: true,
          detailed_traces: true,
          upload_traces: true,
        },
        execution: {},
      };

      const validated = validateConfig(config);
      expect(validated.test_suites[0].tags).toContain('smoke');
      expect(validated.test_suites[1].tags).toContain('integration');
    });
  });
});
