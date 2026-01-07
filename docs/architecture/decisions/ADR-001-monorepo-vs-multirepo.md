# ADR-001: Monorepo vs Multi-repo Structure

## Status

**Status:** accepted

**Date:** 2025-01-06

**Deciders:** Oscar Nuñez, AgentTrace Core Team

---

## Context

### Background

AgentTrace consists of multiple interconnected components:
- Python SDK package (published to PyPI)
- FastAPI backend service
- Next.js dashboard frontend
- Go ingestion service
- Shared trace schema definitions
- Example integrations and documentation

We need to decide on the repository structure that will support development, deployment, and maintenance of these components.

### Problem Statement

How should we organize our codebase to maximize developer productivity, maintain code quality, and enable efficient CI/CD while supporting independent versioning and deployment of components?

### Goals and Constraints

**Goals:**
- Simplify dependency management across components
- Enable atomic changes across multiple packages
- Facilitate code sharing and reuse
- Support efficient CI/CD pipelines
- Maintain clear package boundaries
- Enable independent package versioning

**Constraints:**
- Team size: Small (1-5 developers initially)
- Must support publishing SDK to PyPI independently
- Must support deploying services independently
- Limited CI/CD resources (GitHub Actions free tier)
- Need to support local development with minimal setup

**Assumptions:**
- Components will frequently need coordinated changes
- Shared schema definitions will be used across all components
- Development team will work across multiple components
- Breaking changes will need to be coordinated across packages

---

## Decision

**We will use a monorepo structure using standard tooling rather than specialized monorepo tools.**

### Implementation Details

The repository will be structured as:

```
agenttrace/
├── packages/          # Publishable packages
│   ├── sdk-python/   # PyPI package
│   └── trace-schema/ # Shared schemas
├── apps/             # Deployable applications
│   ├── api/          # FastAPI service
│   ├── dashboard/    # Next.js frontend
│   └── ingestion/    # Go service
├── examples/         # Integration examples
├── docs/            # Documentation
└── scripts/         # Shared scripts
```

**Tooling approach:**
- Use native package managers (pip, npm, go modules) without monorepo overlays
- Use conventional CI/CD with job matrices for component testing
- Use workspace features when available (npm workspaces, Python editable installs)
- Implement selective CI runs based on changed files (future optimization)

### Key Components

- **Packages directory:** Contains publishable, versioned packages
- **Apps directory:** Contains deployable applications
- **Shared tooling:** Unified linting, formatting, and testing configurations
- **Coordinated CI/CD:** Single CI pipeline testing all components

---

## Consequences

### Positive Consequences

- ✅ **Simplified dependency management**: All dependencies visible in one place, easier to update
- ✅ **Atomic commits**: Can update SDK, API, and dashboard in a single commit
- ✅ **Code sharing**: Easy to share utilities, types, and schemas across packages
- ✅ **Unified tooling**: Single ESLint, Prettier, Ruff configuration
- ✅ **Better discoverability**: All code in one place, easier for new contributors
- ✅ **Simplified local development**: Clone once, see everything
- ✅ **Consistent versioning**: Easier to track which versions work together
- ✅ **Reduced context switching**: Developers work in one repository

### Negative Consequences

- ⚠️ **Larger repository size**: Single clone includes all components
- ⚠️ **Longer CI runs**: Testing all components on every change (mitigated by parallelization)
- ⚠️ **Potential for coupling**: Easier to create unintended dependencies between packages
- ⚠️ **Git history complexity**: More commits and changes in single repository
- ⚠️ **Build tool limitations**: Cannot use specialized monorepo tools (Bazel, Nx, Turborepo)

### Risks and Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| Accidental coupling between packages | Medium | Medium | Enforce package boundaries with linting rules, code review guidelines |
| CI becoming too slow | High | Medium | Implement selective CI based on changed files, use aggressive caching |
| Difficulty with independent versioning | Medium | Low | Use semantic versioning per package, maintain separate CHANGELOGs |
| Repository becoming too large | Low | Low | Use Git LFS for large files, exclude build artifacts from version control |

---

## Alternatives Considered

### Alternative 1: Multi-repo (Separate repositories per component)

**Description:** Each major component (SDK, API, Dashboard, Ingestion) in its own repository.

**Pros:**
- Independent versioning and release cycles
- Smaller repository size per component
- Clear package boundaries enforced by repository structure
- Faster CI for individual components
- Better access control per component

**Cons:**
- Complex dependency management across repositories
- Difficult to make atomic changes across components
- Duplication of tooling configuration
- More complex local development setup
- Harder to track compatibility between versions
- More overhead for coordinating releases
- Increased cognitive load (multiple repos to track)

**Reason for rejection:** The overhead of managing multiple repositories outweighs the benefits for our team size and coordination requirements. Atomic changes across the SDK and API are common enough that the multi-repo model would slow down development significantly.

### Alternative 2: Monorepo with Nx or Turborepo

**Description:** Use a specialized monorepo tool like Nx or Turborepo to manage dependencies and builds.

**Pros:**
- Sophisticated dependency graph management
- Optimized build caching and task execution
- Built-in selective CI/CD
- Better support for micro-frontends
- Advanced code generation capabilities

**Cons:**
- Additional tooling complexity and learning curve
- Lock-in to specific tool ecosystem
- Primarily JavaScript-focused (limited Python/Go support)
- Overkill for current project size
- Additional build step overhead
- Potential migration challenges as project grows

**Reason for rejection:** The project is not large enough to justify the complexity and learning curve of specialized monorepo tools. Our stack includes Python, JavaScript/TypeScript, and Go, and current monorepo tools are primarily JavaScript-focused. Standard tooling is sufficient for our needs and team size.

### Alternative 3: Monorepo with Bazel

**Description:** Use Google's Bazel build system for fine-grained build control.

**Pros:**
- Extremely fast incremental builds
- Hermetic builds ensure reproducibility
- Language-agnostic (supports Python, Go, TypeScript)
- Excellent for very large codebases
- Advanced caching and remote execution

**Cons:**
- Steep learning curve
- Complex configuration (BUILD files everywhere)
- Poor integration with standard package managers
- Difficult local development setup
- Overkill for project size
- Limited community support for our stack
- Significant maintenance burden

**Reason for rejection:** Bazel's complexity is not justified for a project of our size. The learning curve and maintenance burden would slow down development. Standard package managers and build tools are sufficient for our needs.

---

## References

### Related ADRs

- ADR-002: Trace Storage Backend (related to data schema sharing)
- ADR-003: SDK Instrumentation Approach (related to SDK development workflow)

### Supporting Documentation

- [Monorepo Tools Comparison](https://monorepo.tools/)
- [Google's Monorepo Paper](https://cacm.acm.org/magazines/2016/7/204032-why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)
- [Advantages of Monorepos](https://danluu.com/monorepo/)
- [GitHub: Monorepo vs Multi-repo](https://github.blog/2022-02-02-monorepo-vs-polyrepo/)

### Industry Examples

- **Monorepo users:** Google, Facebook (Meta), Twitter, Uber (for some projects)
- **Multi-repo users:** Netflix, Amazon (for most services)
- **Hybrid:** Microsoft (mix of both)

---

## Notes

### Timeline

- **2025-01-06:** Decision proposed and accepted
- **2025-01-06:** Implementation completed (initial structure)

### Review Schedule

This decision should be reviewed when:
- Team size exceeds 10 developers
- Repository size exceeds 10GB
- CI run time consistently exceeds 15 minutes
- Coordination between packages becomes infrequent

**Scheduled review date:** 2025-07-01 (6 months)

### Success Metrics

How will we measure if this decision was successful?

- **Developer satisfaction**: Survey results on ease of development
- **CI performance**: Average CI run time < 10 minutes
- **Deployment frequency**: Ability to deploy multiple components simultaneously
- **Code sharing**: Number of shared utilities/types across packages
- **Onboarding time**: New developer can contribute within 1 day
- **Cross-package changes**: Ability to make atomic changes without temporary compatibility layers

### Migration Path

If we need to split into multiple repositories in the future:
1. Each directory under `packages/` and `apps/` is already self-contained
2. Use `git filter-branch` or `git-filter-repo` to extract history
3. Set up package registry (private npm registry, PyPI) for dependencies
4. Update CI/CD to work with separate repositories
5. Coordinate versioning with lockstep releases initially

**Estimated migration effort:** 2-3 weeks for full transition

---

## Appendix: Decision Matrix

| Criteria | Weight | Monorepo (Standard) | Multi-repo | Monorepo (Nx) | Monorepo (Bazel) |
|----------|--------|-------------------|-----------|--------------|-----------------|
| Developer productivity | 10 | 9 | 6 | 8 | 4 |
| CI/CD simplicity | 8 | 8 | 5 | 9 | 6 |
| Build performance | 7 | 7 | 8 | 9 | 10 |
| Learning curve | 8 | 9 | 7 | 6 | 3 |
| Tooling maturity | 7 | 10 | 10 | 8 | 7 |
| Code sharing | 9 | 10 | 4 | 9 | 9 |
| Independent versioning | 6 | 7 | 10 | 7 | 7 |
| Team size fit (1-5) | 9 | 10 | 6 | 7 | 4 |
| **Total Score** | | **449** | **362** | **416** | **339** |

**Winner:** Monorepo with standard tooling (Score: 449/500)

---

**Last Updated:** 2025-01-06

**Authors:** Oscar Nuñez
