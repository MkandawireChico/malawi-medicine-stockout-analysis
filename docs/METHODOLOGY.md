# Methodology

This project combines synthetic inventory simulation, ledger validation, operational KPI calculation, and simple predictive modeling. The goal is to demonstrate how a supply-chain analytics workflow can convert raw order and stock movement data into decision-ready output for district-level review.

## Data lifecycle
1. Generate a deterministic daily inventory ledger.
2. Validate ledger identity and accounting integrity.
3. Aggregate inventory to a monthly summary for risk analysis.
4. Compute days of stock, reorder points, and stock-out status.
5. Train a baseline model against chronological splits.
6. Export outputs for BI and decision support.

## Synthetic assumptions
- Facility and medicine combinations are generated to reflect a small district-level portfolio.
- Demand varies with seasonal and random effects.
- Delivery delay and reporting disruption are included as scenario modifiers.
- Avoided data fabrication: all outcomes are clearly labeled synthetic and cannot be interpreted as real health-system performance.

## Operational definition
Stock-out logic is intentionally conservative. A current or historical stock-out is only reported after considering confirmed stock levels and missing-report handling. Missing reports are flagged as uncertain rather than silently converted into zero.
