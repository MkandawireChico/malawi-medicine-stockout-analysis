# Architecture

## High-level components
- Data generation: deterministic synthetic ledgers and scenario presets.
- Data validation: ledger quality checks and anomaly reporting.
- Analytics: inventory KPIs, stock-out status, and reorder logic.
- Forecasting: baseline risk model and evaluation.
- Application: dashboard and decision-support UI.
- BI: export-ready CSV and schema guidance for Power BI.

## Dependency flow
Data generation -> validation -> KPI aggregation -> forecasting -> reporting -> BI export.

## Design principles
- Keep calculations in reusable functions and modules.
- Separate model training from inference.
- Label every result as synthetic.
- Preserve a clear audit trail through the data lifecycle.
