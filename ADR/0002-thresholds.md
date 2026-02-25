# ADR 0002: Minimum Group and Active-Member Thresholds

## Context

Even with group-level reporting, small cohorts can expose individual behavior.
Enforcement thresholds are required before output generation.

## Decision

Two mandatory thresholds are enforced:

- Configured group size must be at least 5 members.
- Active members must be at least 5:
  - per configured group,
  - in repository scope for the current run.

## Consequences

- Invalid group definitions fail fast during config loading.
- Runs with insufficient activity are blocked by default.
- Output quality improves for privacy, but some low-activity runs are blocked.

## Alternatives Considered

- Threshold of 3: rejected as too weak for privacy.
- Threshold configurable in config: rejected to avoid policy bypass.
