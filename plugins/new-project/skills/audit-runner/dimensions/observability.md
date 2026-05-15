# Dimension: observability

**Tier:** CONTEXT-AWARE (evaluate if surface triggers fire; otherwise emit explicit
N/A, never silent skip)

## Purpose

Logs, metrics, traces, and exception handling — the surface that lets operators
understand what the system did after the fact. A diff that adds a failure path with no
log, or silently swallows an exception, is degrading observability.

## Surface triggers

Spawn this sub-agent **only if** the diff contains:

- New failure path (`raise`, new exception class, new `assert` in production code).
- Exception swallowed (`except ...: pass`, bare `except:`).
- Log level change (`debug` ↔ `info`, `warning` ↔ `error`).
- Structured-log key changed or removed (parsing pipelines may depend on names).
- Metric call added or removed (`statsd.*`, `prometheus_client.*`, project's metrics
  module).

If **none** fire, the coordinator emits:
> `observability: N/A because no surface in diff (triggers considered: <list>)`

## Checklist

(Only reached when at least one trigger fired.)

1. **Silent exception swallow.** `except Exception: pass` or `except: pass` is a
   bug magnet. Per global rules §5: *Never swallow exceptions silently. At minimum log
   the message; in non-UI paths let unexpected errors propagate.*

2. **User-facing save/delete paths.** Per global rules §5: catch broadly, show a
   friendly error, **do not re-raise**. If the diff re-raises in a save/delete path,
   flag it (primary-dim may be `correctness` or `docs` depending on the fix).

3. **Log level appropriateness.**
   - `debug` for traces a developer needs.
   - `info` for normal lifecycle events.
   - `warning` for unexpected-but-handled.
   - `error` for failures that need attention.
   - `critical` for "wake someone up."
   Flag anything mismatched (e.g. `info("payment failed: ...")`).

4. **Structured-log key drift.** If logs go to a parser (Loki, Splunk, Datadog), key
   names are an interface. Renaming `user_id` to `userId` breaks dashboards.

5. **Missing context in error logs.** Logging `"failed"` without the relevant
   identifiers is barely better than not logging. The log line should be
   actionable from the log alone.

6. **PII / secret leakage in logs.** New log line includes a password, token, full
   request body, or credit card number. Blocker.

7. **Metric drift.** A counter renamed without a deprecation; a histogram bucket
   layout changed (dashboards will silently misread). Treat metrics as a public API.

8. **New failure path with no log.** A new `raise` in code that runs in production
   should be observable — at minimum at the catching layer. Flag if there's no log
   between raise and the user-facing boundary.

9. **`assert` in production code.** Asserts are stripped under `python -O`. Use
   explicit raise for invariants that must hold in production.

## Drift sweep

What in observability's scope drifted from another source?

- Dashboards reference a metric name the diff renamed.
- Runbook references a log message string the diff changed.
- ADR declares a logging policy the diff violates.

## Severity guide

| Severity | When |
|----------|------|
| blocker  | PII / secret in a log. `except Exception: pass` on a path that matters. `assert` for an invariant that must hold in production. Structured-log key rename that breaks a known parser. |
| major    | New failure path with no log between raise and the user. Log level clearly mismatched (e.g. `info` on what is a `warning`). Metric renamed without deprecation. |
| minor    | Log line missing one useful identifier; log level borderline (`info` vs `debug`). |
| nit      | Log message could be slightly more informative. |

## Common patterns

**Good.** Exceptions are caught at the layer that can do something about them; logs at
that layer include the relevant IDs and the exception message. Save/delete user-facing
paths catch broadly, show a friendly error, and **do not re-raise**. Metrics treated as
a versioned interface.

**Bad.** `except Exception: pass`. `log.info("error: %s", e)` (wrong level). A
`raise X` in code with no log line in the catching layer. `assert user.is_admin`
guarding a privileged operation. A renamed counter that's already on a dashboard.
