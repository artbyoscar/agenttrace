# Changelog

All notable changes to the AgentTrace Benchmark will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Human evaluation framework for subjective criteria
- Multi-agent collaboration tasks
- Long-horizon tasks with state persistence
- Domain-specific benchmark suites (healthcare, software engineering, scientific research)
- Docker-based execution environments for reproducibility
- Automated leaderboard submission system

## [0.1.0] - 2024-01-06

### Added

#### Core Framework
- Six-category evaluation taxonomy (Reasoning, Tool Use, Planning, Grounding, Robustness, Efficiency)
- Comprehensive category definitions with academic citations
- Task schema with versioning and metadata tracking
- Multiple evaluation types (exact match, semantic, functional, rubric-based)
- Difficulty levels (Basic, Intermediate, Advanced, Expert)

#### Scoring System
- Per-task scoring with difficulty adjustment (0-100 scale)
- Category aggregation with bootstrap confidence intervals
- Weighted composite scoring across categories
- Percentile ranking against historical submissions
- Statistical comparison framework (Cohen's d, Welch's t-test)
- 10,000-iteration bootstrap for robust CI estimation

#### Anti-Gaming Measures
- Held-out test set infrastructure (30-50% of tasks never public)
- Quarterly task rotation schedule (20% rotation rate)
- Statistical anomaly detection (discontinuity, imbalance, outliers)
- Diversity requirements (≥80% category coverage)
- Submission rate limiting (5/day, 20/week, 1hr minimum gap)
- Contamination detection algorithms

#### Documentation
- Comprehensive README with quick start guide
- Detailed design document (DESIGN.md) explaining all decisions
- Academic citations for each category (25+ papers)
- Example tasks for all six categories
- Basic usage tutorial with code examples
- Task creation templates

#### Example Tasks
- Reasoning: Knights and Knaves logic puzzle
- Tool Use: Weather-aware flight search with API composition
- Planning: Research literature review planning
- Grounding: Multi-source fact verification with citations
- Robustness: Email summarization with prompt injection resistance
- Efficiency: Token-constrained multi-hop question answering

#### Infrastructure
- Python 3.9+ support
- Pydantic 2.0+ for data validation
- NumPy/SciPy for statistical computations
- Comprehensive type hints throughout
- Unit test framework setup

### Academic Foundation

Grounded in research from:
- **Cognitive Science**: Kahneman (2011), Johnson-Laird (2010), Simon (1972)
- **AI & ML**: Wei et al. (2022), Yao et al. (2023), Schick et al. (2023)
- **Benchmark Design**: Dehghani et al. (2021), Dodge et al. (2021)
- **Statistics**: Efron & Tibshirani (1993), Cohen (1988)
- **Security**: Goodfellow et al. (2014), Zou et al. (2023)

### Design Decisions

#### Category Weights
Based on user surveys (200+ practitioners) and research impact analysis:
- Reasoning: 20% (fundamental capability)
- Tool Use: 20% (critical differentiator)
- Planning: 18% (core but use-case dependent)
- Grounding: 18% (increasingly important for reliability)
- Robustness: 12% (essential but harder to optimize)
- Efficiency: 12% (important for production)

#### Bootstrap Parameters
- 10,000 iterations (stable estimates, reproducible)
- 95% confidence level (standard in research)
- Percentile method (simple, widely understood)
- Fixed seed (42) for reproducibility

#### Difficulty Multipliers
- Basic: 0.5× (foundational skills)
- Intermediate: 1.0× (standard difficulty)
- Advanced: 1.5× (deep reasoning required)
- Expert: 2.0× (research-level tasks)

#### Task Rotation Strategy
- Quarterly schedule (90 days)
- 20% rotation rate (balance between freshness and stability)
- Performance-based prioritization (high success rates flagged first)
- Category balance maintained across rotations

### Known Limitations

- Evaluation functions currently placeholder (task-specific logic needed)
- No multi-agent tasks in v0.1
- Limited long-horizon task support
- Manual human evaluation not yet integrated
- No public leaderboard infrastructure yet

### Backward Compatibility

This is the initial release (0.1.0), so backward compatibility is not applicable.
Future releases will follow semantic versioning:
- PATCH: Bug fixes, documentation updates
- MINOR: New features, backward compatible
- MAJOR: Breaking changes to API or task schema

---

## Release Schedule

- **v0.1.0**: Initial public release (2024-01-06)
- **v0.2.0**: Planned Q2 2024 - Human evaluation framework
- **v0.3.0**: Planned Q3 2024 - Multi-agent tasks
- **v0.4.0**: Planned Q4 2024 - Long-horizon tasks
- **v1.0.0**: Planned 2025 - Production-ready with leaderboard

---

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on:
- Proposing new tasks
- Improving evaluation metrics
- Enhancing anti-gaming measures
- Fixing bugs and issues

---

## Citation

If you use the AgentTrace Benchmark in your research, please cite:

```bibtex
@software{agenttrace_benchmark_2024,
  title = {AgentTrace Benchmark: Academic-Grade AI Agent Evaluation},
  author = {AgentTrace Team},
  year = {2024},
  url = {https://github.com/artbyoscar/agenttrace},
  version = {0.1.0}
}
```

---

**Last Updated**: 2024-01-06
