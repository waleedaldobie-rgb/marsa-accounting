# Concurrency test plan

The production runtime test suite must cover these cases against PostgreSQL:

1. Two concurrent `allocate_invoice_number()` calls for the same branch return different numbers.
2. Two concurrent `issue_sale()` calls against the same draft sale produce one issued sale, one stock-out set, and one payment transaction.
3. Two concurrent outbound movements cannot drive `StockBalance.quantity` below zero.
4. Two concurrent transfer receives cannot receive the same transfer twice.

The services use `transaction.atomic()` and `select_for_update()` for the critical rows. These tests are intentionally executed only in a real Django/PostgreSQL runtime, not faked by syntax checks.
