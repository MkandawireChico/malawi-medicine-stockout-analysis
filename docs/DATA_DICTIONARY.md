# Data Dictionary

## Ledger fields
- `facility_id`: facility identifier.
- `medicine_id`: medicine identifier.
- `date`: inventory reporting date.
- `opening_stock`: stock at the start of the day.
- `received`: stock received during the period.
- `issued`: stock issued or dispensed.
- `adjustment`: inventory corrections or adjustments.
- `losses`: known losses or wastage.
- `closing_stock`: inventory after movement.
- `lead_time_days`: expected procurement time.
- `safety_stock`: minimum policy reserve.
- `target_stock`: target maximum-stock level.
- `reported`: whether the facility reported this day.

## Derived fields
- `days_of_stock`: usable stock divided by average daily consumption.
- `reorder_point`: expected demand during lead time plus safety stock.
- `reorder_quantity`: target stock minus current stock minus incoming stock.
- `stockout_status`: classification based on operational rules.
