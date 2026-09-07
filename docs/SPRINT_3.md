# Sprint 3 — Catalog, Suppliers & Pricing

## Goal
Establish the master catalog used by purchases, inventory and sales.

## Implemented
- Product master with unique SKU and fixed KG base unit.
- Supplier master.
- Time-bounded ProductPrice records.
- Validation against overlapping price periods.
- Non-negative selling prices.
- Current-price helper based on server time.
- Arabic RTL product and supplier list/detail/create screens.
- CSV product import with UTF-8 BOM support.
- CSV template download.
- Catalog permission map: view_catalog and manage_catalog.

## CSV contract
Required columns:
- sku
- name

Optional columns:
- description
- is_active
- price
- starts_at
- ends_at

Datetime format: `YYYY-MM-DDTHH:MM`.

## Rules
- SKU is normalized to uppercase.
- Product base unit is always KG.
- Products are not hard-deleted.
- Price intervals for the same product must not overlap.
- A price is valid when starts_at <= now and (ends_at is null or ends_at > now).
- Historical prices remain immutable records; future changes create a new period.

## Verification
- Python syntax compilation passed for apps/config/manage.py.
- Django runtime migrations/tests remain pending until a working Django/PostgreSQL environment is available.
