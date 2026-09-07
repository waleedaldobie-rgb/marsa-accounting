# Sprint 8 — الوزن الخام/المنظف وإصدار البيع

## Implemented
- SaleItem raw_weight/cleaned_weight validation.
- Cleaned weight is customer-billed; raw weight is stock-out quantity.
- `sale_amount = cleaned_weight × unit_price`.
- `COGS = raw_weight × cost_at_sale`.
- `ProcessingRecord` stores raw, cleaned, difference.
- Atomic `issue_sale()` locks sale/shift/balances and creates one payment per sale.
- Repeated issue of an already issued sale is idempotent at the sale level.
- Payment reference uniqueness prevents duplicate sale payment records.
- SALE_OUT movement is created through the inventory service.
- Draft sales do not affect stock.

## Example
Raw 1.300 kg, cleaned 1.000 kg, price 40 => sale 40.00; stock out 1.300 kg; processing difference 0.300 kg.

## Not yet verified
Runtime Django migrations/tests require Django + PostgreSQL in an execution environment.
