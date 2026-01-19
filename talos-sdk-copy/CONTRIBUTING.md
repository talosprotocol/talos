# Contributing to Talos Protocol

Thank you for your interest in contributing to the Talos Protocol ecosystem! We are committed to maintaining the highest standards of security, code quality, and documentation.

## Development Standards

### Security First
- **Dependencies**: Pin all dependencies with hashes.
- **Secrets**: Never commit secrets. Use `git-secrets` or similar to scan your commits.
- **Cryptography**: Do not implement your own crypto. Use the primitives provided in `talos-core` or approved libraries (`cryptography`, `libsodium`).

### Code Quality
- **Linting**: We enforce zero-tolerance for lint errors. Run `make lint` before committing.
- **Testing**: All new features must include unit tests. Fixes must include regression tests.
- **Coverage**: Maintain or improve code coverage. 

### Documentation
- **Comments**: Public APIs must be documented (docstrings/JavaDoc/TSDoc).
- **README**: Update the README if you change behavior.
- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/):
    - `feat: ...`
    - `fix: ...`
    - `docs: ...`
    - `chore: ...`

## Workflow

1.  **Fork & Clone**: Fork the repository and clone it locally.
2.  **Branch**: Create a feature branch: `git checkout -b feature/my-feature`.
3.  **Develop**: Write code, strictly following the style guide.
4.  **Test**: Run `make test` locally.
5.  **Commit**: Sign your commits (`git commit -s ...`) to certify usage rights (DCO).
6.  **Push**: Push to your fork and submit a Pull Request.

## Language Specifics

### Python (talos-sdk-py)
- **Style**: PEP 8, enforced by `ruff`.
- **Types**: 100% type hinting required (`mypy` strict).
- **Format**: `ruff format`.

### TypeScript (talos-sdk-ts)
- **Style**: Standard, enforced by `eslint` + `prettier`.
- **Types**: Strict mode enabled. No `any`.

### Go (talos-sdk-go)
- **Style**: `gofmt` and `golangci-lint`.
- **Idioms**: Effective Go.

### Java (talos-sdk-java)
- **Style**: Google Java Style.
- **Build**: Maven.

## Pull Request Process

1.  **Description**: Clearly explain the "Why" and "What".
2.  **Checklist**: Verify you have updated docs and tests.
3.  **Review**: A core maintainer must review and approve.
4.  **Merge**: We squash-merge PRs.

## License

By contributing, you agree that your contributions will be licensed under the project's [LICENSE](./LICENSE).
