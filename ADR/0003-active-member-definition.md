# ADR 0003: Active Member Definition

## Context

Threshold checks require a precise, testable definition of "active member".

## Decision

A member is active if they have at least one commit timestamp inside the
selected evaluation window.

- Window is inclusive: `[since, until]`.
- If one boundary is omitted, the range is open on that side.

## Consequences

- Activity checks are deterministic and simple to validate.
- The definition aligns with contribution presence, not review/comment activity.

## Alternatives Considered

- Count review or comment activity as active: rejected to keep policy strict and
  commit-centric.
- Require N commits (N > 1): rejected for being overly restrictive.
