# Sprint 15 — Runtime Bootstrap, Sequencing, Audit & Concurrency

## Implemented
- Added `InvoiceSequence`, scoped one-to-one per branch.
- Added locked invoice allocation service with deterministic format `BRANCH-YYYYMMDD-000001`.
- Replaced UUID-based draft invoice numbers with the sequence allocator.
- Added automatic audit capture for successful POST/PUT/PATCH/DELETE requests, while preserving domain-level audit events.
- Added `scripts/bootstrap_runtime.py` to run check → makemigrations → migrate → test in a real local environment.
- Added a PostgreSQL concurrency test plan.

## Verification in build environment
- Python syntax/compile checks only.
- Django/PostgreSQL runtime, migration generation/application, and concurrency tests remain NOT RUN because Django/PostgreSQL runtime is unavailable here.

## Production rule
Do not treat automatic HTTP audit entries as a substitute for domain audit events. Sensitive business actions must continue calling `log_event()` with meaningful entity/action/reason data.
