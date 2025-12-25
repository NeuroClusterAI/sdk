# SDK Versioning Policy (SemVer)

This document defines **what is considered public API** for the NeuroCluster Python SDK and how we apply **Semantic Versioning** (SemVer) to it.

This policy applies to the **SDK only** (not the backend API).

## Public API Surface

The following are **public** and covered by SemVer guarantees:

- `neurocluster.NeuroCluster`
  - `__init__(api_key: str, api_url: str = ...)`
  - `Agent` (manager)
  - `Thread` (manager)
  - `Versions` (client)
  - `close()`, async context manager (`async with NeuroCluster(...)`)
- `neurocluster.AgentPressTools`
- `neurocluster.MCPTools`
- `neurocluster.neurocluster` (legacy module-like alias; kept for compatibility)

Anything else is considered **internal** unless explicitly documented as public.

## Versioning Rules

We follow SemVer: `MAJOR.MINOR.PATCH`.

### MAJOR (breaking changes)
Increment MAJOR when we:
- Remove/rename any public class/function/module or change import paths.
- Change public method signatures (parameter rename/removal, type changes, default behavior changes).
- Change request/response shapes returned by public methods (e.g., dataclass fields users rely on).
- Change authentication header behavior (e.g., token header name).
- Change error types raised for the same failure mode in a way that breaks callers’ exception handling.
- Remove deprecated functionality.

### MINOR (backwards-compatible features)
Increment MINOR when we:
- Add new public methods/classes/options that do not break existing usage.
- Add new optional fields to returned dataclasses in a backwards-compatible way.

### PATCH (bugfixes)
Increment PATCH when we:
- Fix bugs without changing public API contracts.
- Improve performance or internal refactors with no outward behavior changes.

## Deprecation Policy

- Deprecated APIs MUST continue to work until the next **MAJOR** release.
- Deprecated APIs SHOULD emit a clear warning in docs (and optionally `DeprecationWarning`).
- Deprecated APIs MUST be documented in `sdk/CHANGELOG.md` when introduced.

## CI Rule (enforced)

If SDK code changes (anything under `sdk/neurocluster/**` or packaging metadata), we require a version bump in `sdk/pyproject.toml`.

Docs-only or tests-only changes are exempt.


