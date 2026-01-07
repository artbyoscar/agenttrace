# Contributing to AgentTrace GitHub Action

Thank you for your interest in contributing to the AgentTrace GitHub Action!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/agenttrace/agenttrace.git
cd agenttrace/packages/github-action
```

2. Install dependencies:
```bash
npm install
```

3. Build the action:
```bash
npm run build
```

## Development Workflow

### Making Changes

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes to the TypeScript files in the `src/` directory

3. Run linting:
```bash
npm run lint
```

4. Format code:
```bash
npm run format
```

5. Build the action:
```bash
npm run build
```

6. Test locally (set environment variables first):
```bash
export INPUT_API_KEY="test-key"
export INPUT_CONFIG_FILE="agenttrace.example.yaml"
export GITHUB_WORKSPACE="$(pwd)"
node dist/main.js
```

### Testing

We use Jest for testing. To run tests:

```bash
npm test
```

To run tests with coverage:

```bash
npm test -- --coverage
```

### Code Style

- Follow TypeScript best practices
- Use meaningful variable and function names
- Add JSDoc comments for public APIs
- Keep functions small and focused
- Use async/await for asynchronous code

### Commit Messages

Follow conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build process or auxiliary tool changes

Example:
```
feat: add support for custom evaluator thresholds
```

## Building for Production

The action uses `@vercel/ncc` to compile the TypeScript code and all dependencies into a single `dist/main.js` file:

```bash
npm run build
```

Important: Always commit the compiled `dist/main.js` file along with your changes, as GitHub Actions runs the compiled code.

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the version number following [SemVer](https://semver.org/)
3. Ensure all tests pass and linting is clean
4. Build and commit the `dist/main.js` file
5. Create a Pull Request with a clear description of the changes

## Release Process

Releases are managed by maintainers:

1. Update version in `package.json`
2. Update CHANGELOG.md
3. Build the action: `npm run build`
4. Commit changes
5. Create a git tag: `git tag -a v1.x.x -m "Release v1.x.x"`
6. Push tag: `git push origin v1.x.x`
7. Create GitHub release from tag

## Questions?

Feel free to open an issue for any questions or concerns.

## Code of Conduct

Be respectful and inclusive. We aim to foster a welcoming community.
