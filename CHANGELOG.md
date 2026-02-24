# CHANGELOG


## v0.0.0 (2026-02-24)

### Continuous Integration

- Add automatic semver with python-semantic-release
  ([`ead9616`](https://github.com/wispnook/wispnook-server/commit/ead9616ac44c44146c5bf6366112674c60218929))

Adds python-semantic-release to dev dependencies and configures it in pyproject.toml to bump
  versions from conventional commit messages. Adds a release.yml workflow that runs on every push to
  main, bumping the version in pyproject.toml, creating a git tag, and publishing a GitHub Release
  automatically.

### Documentation

- Add conventional commit conventions to CLAUDE.md
  ([`e7bee04`](https://github.com/wispnook/wispnook-server/commit/e7bee0400f10debce3b8dde249c67247cf13c3f2))

- Add FastAPI built-in documentation to all endpoints
  ([`acafb45`](https://github.com/wispnook/wispnook-server/commit/acafb45bd39e2fd7fab857eb21e2400da00963c7))

Adds summary, description, and response_description to every route decorator across all routers.
  Adds Query descriptions to all paginated and filter parameters. Enriches the FastAPI app-level
  description with auth, rate limiting, and pagination guidance shown in Swagger UI and ReDoc.
  Updates README and CLAUDE.md with docs URLs and the requirement to document new endpoints.
