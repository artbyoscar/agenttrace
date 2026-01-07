# AgentTrace GitHub Action

Evaluate AI agent quality on every pull request with AgentTrace.

## Features

- **Automated Evaluation**: Run comprehensive agent evaluations on every PR
- **Regression Detection**: Automatically compare against baseline to catch performance regressions
- **PR Comments**: Post detailed results as PR comments with pass/fail status
- **Threshold Enforcement**: Fail CI checks when evaluation scores drop below configured thresholds
- **Dashboard Integration**: Upload traces and view detailed analysis in AgentTrace dashboard
- **Flexible Configuration**: Use YAML configuration files to define test suites and evaluators

## Usage

### Basic Example

```yaml
name: Agent Evaluation

on:
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install agenttrace

      - name: Run AgentTrace Evaluation
        uses: agenttrace/github-action@v1
        with:
          api_key: ${{ secrets.AGENTTRACE_API_KEY }}
          config_file: 'agenttrace.yaml'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Advanced Example with Custom Configuration

```yaml
name: Comprehensive Agent Testing

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  evaluate-agent:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      statuses: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install agenttrace

      - name: Run AgentTrace Evaluation
        id: agenttrace
        uses: agenttrace/github-action@v1
        with:
          api_key: ${{ secrets.AGENTTRACE_API_KEY }}
          config_file: 'config/agenttrace.yaml'
          fail_on_regression: 'true'
          fail_on_threshold: 'true'
          comment_on_pr: 'true'
          upload_traces: 'true'
          baseline_branch: 'main'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload results artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: agenttrace-results
          path: .agenttrace/results.json

      - name: Check outputs
        run: |
          echo "Tests passed: ${{ steps.agenttrace.outputs.pass_count }}"
          echo "Tests failed: ${{ steps.agenttrace.outputs.fail_count }}"
          echo "Regressions: ${{ steps.agenttrace.outputs.regression_count }}"
          echo "Overall score: ${{ steps.agenttrace.outputs.overall_score }}"
          echo "Results URL: ${{ steps.agenttrace.outputs.results_url }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `api_key` | AgentTrace API key for authentication | Yes | - |
| `config_file` | Path to agenttrace.yaml configuration file | No | `agenttrace.yaml` |
| `fail_on_regression` | Fail the check if regressions are detected | No | `true` |
| `fail_on_threshold` | Fail if any evaluator score is below threshold | No | `true` |
| `comment_on_pr` | Post evaluation results as PR comment | No | `true` |
| `upload_traces` | Upload traces to AgentTrace dashboard | No | `true` |
| `baseline_branch` | Branch to compare against for regression detection | No | `main` |

## Outputs

| Output | Description |
|--------|-------------|
| `pass_count` | Number of tests that passed |
| `fail_count` | Number of tests that failed |
| `regression_count` | Number of regressions detected compared to baseline |
| `overall_score` | Overall evaluation score (0-100) |
| `results_url` | URL to view full results in AgentTrace dashboard |

## Configuration File

Create an `agenttrace.yaml` file in your repository root:

```yaml
project: my-agent-project

suites:
  - name: core-functionality
    description: Core agent capabilities
    parallel: true
    timeout: 60000
    evaluators:
      - accuracy
      - relevance
    test_cases:
      - id: test-001
        name: Simple query handling
        input:
          query: "What is the capital of France?"
        expected_output:
          answer: "Paris"

      - id: test-002
        name: Multi-step reasoning
        input:
          query: "Calculate the total cost of 3 items at $15 each"
        expected_output:
          answer: "45"

  - name: edge-cases
    description: Edge case handling
    evaluators:
      - robustness
      - error-handling
    test_cases:
      - id: edge-001
        name: Empty input handling
        input:
          query: ""
        evaluators:
          - error-handling

evaluators:
  - name: accuracy
    type: exact-match
    threshold: 0.9

  - name: relevance
    type: semantic-similarity
    config:
      model: sentence-transformers/all-MiniLM-L6-v2
    threshold: 0.8

  - name: robustness
    type: llm-judge
    config:
      model: gpt-4
      criteria: "Does the response handle the edge case appropriately?"
    threshold: 0.7

thresholds:
  min_score: 75
  max_failures: 2
  max_regressions: 1
```

## Setting up API Key

1. Get your API key from [AgentTrace Dashboard](https://app.agenttrace.com)
2. Add it as a repository secret:
   - Go to your repository **Settings** > **Secrets and variables** > **Actions**
   - Click **New repository secret**
   - Name: `AGENTTRACE_API_KEY`
   - Value: Your API key from AgentTrace

## Permissions

The action requires the following GitHub permissions:

```yaml
permissions:
  contents: read        # To read the repository code
  pull-requests: write  # To post comments on PRs
  statuses: write       # To set commit status checks
```

## Example PR Comment

The action will post a comment on your PR that looks like this:

```markdown
# AgentTrace Evaluation Results

## ✅ Summary

| Metric | Value |
|--------|-------|
| **Tests Passed** | 18/20 (90.0%) |
| **Overall Score** | 85.42 |
| **Duration** | 12.34s |
| **Regressions** | 0 |
| **Improvements** | 3 |

## 📈 Improvements

| Test Case | Suite | Current | Baseline | Delta |
|-----------|-------|---------|----------|-------|
| Simple query handling | core-functionality | 95.20 | 88.50 | +6.70 |
| Multi-step reasoning | core-functionality | 92.30 | 85.10 | +7.20 |

## Detailed Results

### core-functionality

✅ **Simple query handling** (Score: 95.20)
  ✅ accuracy (95.00): Exact match
  ✅ relevance (95.40): High semantic similarity

❌ **Complex reasoning** (Score: 65.30)
  ✅ accuracy (70.00): Partial match
  ❌ relevance (60.60): Low semantic similarity

[View full results in AgentTrace Dashboard](https://app.agenttrace.com/projects/my-project/runs/123)

---
*Automated evaluation by AgentTrace*
```

## Development

### Building the Action

```bash
cd packages/github-action
npm install
npm run build
```

This compiles TypeScript to JavaScript and bundles everything into `dist/main.js` using `@vercel/ncc`.

### Testing Locally

```bash
# Set required environment variables
export INPUT_API_KEY="your-api-key"
export INPUT_CONFIG_FILE="agenttrace.yaml"
export GITHUB_WORKSPACE="$(pwd)"

# Run the action
node dist/main.js
```

## License

MIT

## Support

- Documentation: [docs.agenttrace.com](https://docs.agenttrace.com)
- Issues: [GitHub Issues](https://github.com/agenttrace/github-action/issues)
- Email: support@agenttrace.com
