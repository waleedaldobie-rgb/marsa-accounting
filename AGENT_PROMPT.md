# Prompt for a New Coding Agent

You are continuing the **مَرسى** Django ERP/POS project. Do not hallucinate project state.

First read:
- PROJECT_STATE.md
- ARCHITECTURE.md
- DECISIONS.md
- HANDOFF.md
- README.md

Then inspect the repository.

Your default task is **Sprint 2 only** from `docs/SPRINT_PLAN.md` unless the user explicitly names another Sprint.

Requirements:
- Preserve PostgreSQL as the primary database.
- Preserve StockMovement as the inventory source of truth.
- Preserve weighted-average costing decisions.
- Preserve raw-vs-cleaned weight semantics.
- Use domain services for sensitive state changes.
- Enforce permissions server-side, including branch scoping.
- Use atomic transactions and row locks where needed.
- Add tests for every important rule introduced.
- Do not implement future Sprints early.
- Do not delete approved financial/inventory records.
- Do not claim completion without running available checks.

At the end:
1. report changed files;
2. report tests/checks and results;
3. list anything not verified;
4. update PROJECT_STATE.md;
5. update CHANGELOG.md.


## Sprint 8 rule
Do not treat cleaning difference as waste automatically. Use ProcessingRecord first; only approved WasteAdjustment creates WASTE_OUT. Do not move sale stock logic into templates or JavaScript.
