# ADR 0004: Override Governance

## Context

Some operational situations require output despite threshold violations, but
override must be explicit and auditable by operator intent.

## Decision

Override is allowed only when all conditions are true:

1. CLI flag `--overwrite-data-protection` is set.
2. A visible disclaimer is printed.
3. User confirms explicitly by typing `y`.

If any condition is missing, execution aborts.

## Consequences

- Unsafe output cannot be produced accidentally.
- Interactive confirmation introduces friction for automation workflows.
- Report metadata can annotate override usage.

## Alternatives Considered

- Flag-only override with no confirmation: rejected as too easy to misuse.
- Environment variable override: rejected because it is less explicit at run
  time.
