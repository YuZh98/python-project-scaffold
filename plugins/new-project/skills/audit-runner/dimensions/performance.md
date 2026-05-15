# Dimension: performance

**Tier:** CONTEXT-AWARE (evaluate if surface triggers fire; otherwise emit explicit
N/A, never silent skip)

## Purpose

Catch performance regressions that are visible in the diff: new DB queries in loops,
sync-in-async, removed indexes, new external calls without timeout/retry, changes on a
known hot path.

Performance findings are notoriously easy to over-flag (premature optimization is
real). Calibrate severity to *demonstrable* concern: order-of-magnitude regression
or contractually-bound latency.

## Surface triggers

Spawn this sub-agent **only if** the diff contains:

- Change on a file marked as a hot path by DESIGN.md / module docstring.
- New DB query inside a loop (regex catches `.execute(` / `.query(` / `session.`
  near a `for` header; sub-agent confirms by reading context).
- Sync I/O inside async code (`time.sleep`, `requests.*`, blocking `open` reads
  inside `async def`).
- Schema migration that drops or fails to add an expected index.
- New external service call (HTTP, RPC, queue) outside of an existing well-bounded
  call site.
- Removed cache, removed batch, removed lazy loading.

If **none** fire, the coordinator emits:
> `performance: N/A because no surface in diff (triggers considered: <list>)`

## Checklist

(Only reached when at least one trigger fired.)

1. **N+1 query.** New code iterates a collection and issues a DB query per element.
   Use eager loading / `IN` / `JOIN` / batch fetch.

2. **Sync in async.** `time.sleep`, `requests.get`, `open(...).read()` inside an
   `async def`. Use `asyncio.sleep`, `httpx.AsyncClient`, `aiofiles`.

3. **Removed index.** Migration drops an index that supports a known query. Often
   intentional, sometimes accidental. Look for the matching query in source — if it
   still exists, the index removal is a regression.

4. **External call without timeout.** Any new `requests.*` / `httpx.*` / RPC call
   without an explicit timeout. Production default is "block forever," which is
   never what you want.

5. **External call without retry boundary.** A new dependency on a flaky external
   service with no retry / circuit breaker / fallback. Severity depends on whether
   the call is on a user-facing path.

6. **Hot-path allocation.** New allocation inside a known hot loop (per DESIGN.md or
   prior profiling). Common offender: `dict()` / `list()` constructed per iteration
   where one could be hoisted.

7. **Regex compilation in loops.** `re.compile` or even `re.search` with a literal
   pattern inside a tight loop. Hoist or use `re.compile` at module load.

8. **Quadratic algorithms.** `if x in some_list` where `some_list` grows; nested loops
   over the same collection; repeated `sorted()` on the same data.

9. **Async fanout without bound.** `await asyncio.gather(*[fetch(u) for u in urls])`
   where `urls` is user-controlled = unbounded concurrency. Use a semaphore or
   `as_completed` with a worker count.

## Drift sweep

What in performance's scope drifted from another source?

- DESIGN.md declares a latency budget the diff plausibly violates.
- Existing benchmark expects N queries; new code issues N+1.
- Module docstring claims O(n) complexity; new code makes it O(n²).

## Severity guide

| Severity | When |
|----------|------|
| blocker  | Order-of-magnitude regression on a known hot path; SLA-bound latency clearly violated; unbounded external fanout. |
| major    | N+1 query on a path that runs at request scale; missing timeout on an external call from a user-facing route. |
| minor    | Suboptimal but functional algorithm; missing batch where the batch size is small. |
| nit      | Allocation in a non-hot loop; regex that *could* be precompiled. |

## Common patterns

**Good.** New external call has `timeout=` and a retry policy (or an explicit comment
that retries are handled upstream). New DB query uses `joinedload` / `selectinload` /
`IN` for fan-out. Async code stays async end-to-end.

**Bad.** `for user in users: db.query(Profile).filter_by(user_id=user.id).first()`.
`requests.get(url)` with no timeout. `await asyncio.gather(*tasks)` with unbounded
`tasks`. A migration with `DROP INDEX` and no compensating change to the query plan.
