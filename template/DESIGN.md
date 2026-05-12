# System Design: <<PROJECT_TITLE>>
**Version:** v0.1 | **Last updated:** <<YEAR>> | **Status:** draft

## 1. Purpose & Scope
- Problem: e.g. "Researchers lose track of grant deadlines across 5 spreadsheets, missing 1-2 per cycle."
- Solution: e.g. "A local CLI that ingests grant URLs and surfaces a daily 'what to submit today' summary."
- Non-goals: e.g. "Not a CRM. Not multi-user. Not real-time alerts."

## 2. Architecture Overview
- Import contract (write ADR-0001 first): e.g. "`cli` → `service` → `db`; `db` must not import `service`."

## 3. Technology Stack
- Python <<PYTHON_FLOOR>>+
- e.g. "SQLite via `sqlite3` stdlib (small local data store; no server required)."
- e.g. "Redis for job queue if background processing is added (deferred; out of scope for v1)."

## 4. File Structure
- e.g. `src/<package>/{cli.py, service.py, db.py, models.py}`; `tests/test_<module>.py` mirrors src tree.

## 5+ ...
- TODO
