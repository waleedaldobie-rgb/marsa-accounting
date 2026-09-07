# Development Protocol

كل Sprint يمر عبر:
1. Read state/architecture/decisions.
2. Inspect existing implementation.
3. Implement only the stated scope.
4. Add migrations.
5. Add unit + integration tests relevant to the Sprint.
6. Test permissions and rollback for sensitive flows.
7. Run formatting/checks/tests.
8. Update PROJECT_STATE.md.
9. Write a short change log.
10. Commit only after tests pass.
