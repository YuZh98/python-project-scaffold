# Dimension: security

**Tier:** CONTEXT-AWARE (evaluate if surface triggers fire; otherwise emit explicit
N/A, never silent skip)

## Purpose

Catch security-affecting changes: command injection, code injection, environment
leakage, network surface, deserialization, path traversal, SQL injection, auth path
changes. The bar for security findings is **conservative** — false positives cost a
review cycle; false negatives can ship a vulnerability.

## Surface triggers

Spawn this sub-agent **only if** the diff contains one of:

- `subprocess.` (any module member — `run`, `Popen`, `check_output`, etc.)
- `eval(` or `exec(`
- `os.environ[...] =` or `os.environ.setdefault(...)` (writing process env)
- New network call (`requests.`, `httpx.`, `urllib.request.urlopen`, `aiohttp.`)
- Deserialization of untrusted input (`pickle.loads`, `yaml.load` without
  `SafeLoader`, `marshal.loads`)
- Path construction from user input (`Path(input(...))`, `Path(sys.argv[...])`,
  `Path(request.…)`)
- SQL `execute` / `executemany` with string formatting (f-string, `%`, `.format()`)
- Auth-related symbol touched (`authenticate`, `authorize`, `verify_token`,
  `check_password`, `hash_password`, JWT/cookie/session handling)

If **none** fire, the coordinator emits:
> `security: N/A because no surface in diff (triggers considered: <list>)`

## Checklist

(Only reached when at least one trigger fired.)

1. **Command injection.** `subprocess.run(..., shell=True)` with any non-literal
   argument → almost always a blocker. `shell=False` + argv-list with validated
   input is the safe pattern.

2. **Code injection.** `eval` / `exec` over any input that crosses a trust boundary
   (user, env, file, network) → blocker. Even over constants, ask whether a different
   construct would do.

3. **Env variable writes.** Writing to `os.environ` from library code mutates global
   state and can leak. Flag any non-test, non-CLI-entry-point write.

4. **Network surface.** New external call to a URL that's user-controlled, or to a
   service over plaintext, or without timeout. SSRF risk on user-supplied URLs.

5. **Deserialization.** `pickle.loads` over untrusted bytes = remote code execution.
   `yaml.load` without `SafeLoader` = same. `marshal` = same. Any deserialization of
   network/file/user input is a blocker until proven safe.

6. **Path traversal.** Any `Path(...)` or `open(...)` whose argument can include user
   input must validate that the resolved path is inside an expected root. Look for
   missing `Path.resolve().is_relative_to(root)` checks.

7. **SQL injection.** Any `execute("..." + var)`, `execute(f"...")`, or
   `execute("..." % var)` over a value that crosses a trust boundary. Parameterised
   queries (`execute("... WHERE id = ?", (id,))`) are the only safe form.

8. **Auth path changes.** Anything in the auth surface gets extra scrutiny: missing
   constant-time comparison for tokens (`hmac.compare_digest`), missing salt on
   password hash, JWT verification with `verify=False`, cookie without `Secure` /
   `HttpOnly` / `SameSite`, session fixation.

9. **Secrets in code.** API keys, tokens, passwords as literals. Even a `.env` file
   committed by accident.

10. **CSRF / origin checks** if web context. **Insecure crypto primitives** (MD5,
    SHA-1, DES) for security purposes.

## Drift sweep

What in security's scope drifted from another source?

- SECURITY.md describes a security policy the diff violates.
- A previously parameterised query path now uses string formatting.
- Auth path had timing-safe comparison; new code uses `==`.

## Severity guide

| Severity | When |
|----------|------|
| blocker  | RCE surface (pickle/yaml.load over untrusted input, eval/exec over input, shell=True over input). SQL injection. Hardcoded secret. Missing auth on a protected route. |
| major    | Missing input validation on a path that's currently constrained by upstream callers (defence-in-depth). Network call without timeout. Insecure default that the user-facing API doesn't override. |
| minor    | Tight pattern that *could* be tighter (e.g. `shell=False` with argv list but no input regex check on items that are unlikely to be hostile). |
| nit      | Defensive comment missing on a clearly-safe pattern. |

## Common patterns

**Good.** `subprocess.run([...], shell=False, check=True, timeout=10)` with each argv
element validated. Parameterised SQL. `secrets.compare_digest` for token comparison.
Path inputs resolved against a root with `is_relative_to`. Network calls with explicit
timeouts and SSL verification.

**Bad.** `subprocess.run(cmd, shell=True)` where `cmd` is constructed from input.
`yaml.load(open(path))` (no `SafeLoader`). `cursor.execute(f"SELECT * FROM t WHERE
id = {user_id}")`. Token comparison with `==`. API key as a default kwarg value.
