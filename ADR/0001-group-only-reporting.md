# ADR 0001: Group-Only Reporting

## Context

The project previously emitted per-user statistics in Markdown output. This can
create re-identification risks and conflicts with privacy expectations.

## Decision

The report output is group-only:

- No single-user statistics are rendered.
- Metrics are computed and reported for configured `user_groups` only.

## Consequences

- Existing users must configure groups in the YAML config.
- Report sections are now organized by group instead of username.
- Some prior per-user workflows require migration to group-level analysis.

## Alternatives Considered

- Keep per-user output behind a flag: rejected, because accidental misuse is
  too easy.
- Pseudonymize usernames in output: rejected, because small cohorts can still
  be re-identified.
