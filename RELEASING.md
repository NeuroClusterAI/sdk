# Releasing the NeuroCluster SDK (PyPI)

This repo is a monorepo; the SDK lives in `sdk/` and is published as the PyPI distribution **`neurocluster`**.

## Versioning

See `sdk/VERSIONING.md` for the SemVer rules and what counts as a breaking change.

1. Update `sdk/pyproject.toml`:
   - Bump `[project].version` (Semantic Versioning).
2. Add an entry to `sdk/CHANGELOG.md`.

## Create a release tag

Tag format: `sdk-vX.Y.Z` (example: `sdk-v0.1.1`).

## GitHub Actions publish

The publish workflow triggers on tags matching `sdk-v*` and:
- runs the SDK test suite
- builds sdist + wheel from `sdk/`
- publishes to PyPI using the `PYPI_API_TOKEN` secret

## Required secrets

- `PYPI_API_TOKEN`: a PyPI token with permission to publish the `neurocluster` project.

