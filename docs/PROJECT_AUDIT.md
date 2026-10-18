# Project Audit

## Scope
This repository was audited against the requirements in the upgrade brief and the code already checked into the workspace. The project is a synthetic inventory-analysis portfolio project focused on essential medicines in Salima District, Malawi. It contains a raw daily ledger, a processed monthly summary table, and Power BI assets, but it did not yet include a reusable Python package, reliable validation layer, or production-grade model and analytics pipeline.

## Confirmed strengths
- Synthetic data is intentionally generated with a fixed seed and a realistic supply-chain narrative.
- The raw ledger exposes operational fields such as opening stock, receipts, issue quantities, and closing stock.
- The monthly summary table contains a useful operational view by facility, medicine, and month.
- The notebook demonstrates a practical stock-out analysis and basic forecasting logic.
- There is a Power BI dashboard concept and documentation, which indicates a clear decision-support objective.

## Confirmed bugs and defects
1. The repository is mostly notebook-centric rather than a modular project. There is no actual `src/` package, no automated tests, and no reproducible CLI for generation or validation.
2. Missing reports are not handled explicitly as a separate class of data-quality problem; the project currently risks conflating missing reporting with low or zero stock without a robust rule.
3. The current data model is not yet formalized as reusable validation and metrics logic; business rules are embedded in exploratory code, which makes them harder to audit and reuse.
4. There is no explicit data-quality export workflow or sanctioned validation schema.
5. The stock-out status and inventory accounting rules were not yet implemented as a reusable, tested module; this makes operational decisions hard to trust.

## Methodological weaknesses
- The project describes a stock-out analysis and a risk classifier, but the prediction logic is not yet built as a reproducible pipeline with proper train/validation/test separation.
- There is no clear separation between operational KPIs, forecasting, and model evaluation.
- No data-quality or business-rule validation is enforced at write time.
- Separating genuine stock-outs from missing reporting or stale data remains under-specified without explicit rules.
- Dataset assumptions are feasible for a synthetic portfolio demo, but they are not yet packaged for scenario analysis and sensitivity testing in a reusable way.

## Missing functionality relative to the brief
- Reproducible data-generation CLI with scenario presets.
- Data validation using schema rules or lightweight checks.
- SQL analytical queries and database-loading scripts.
- KPI functions for reorder point, reorder quantity, days of stock, and stock-out status.
- Baseline and advanced model comparison with proper chronological validation.
- Scenario and redistribution modules.
- Streamlit decision-support application.
- Dashboard export schema documentation.
- Clean documentation set for methodology, architecture, assumptions, and reproducibility.

## Stock-out definition used in this project
A stock-out is defined operationally as a facility-medicine combination with non-positive usable stock or zero reliable days of stock remaining for the reporting window. Missing reports are not automatically converted to stock-out; they are treated as missing or stale data and flagged separately. This definition is intentionally strict and is included in the reusable analytical modules.

## Proposed implementation sequence
1. Create a stable Python package for data, analytics, and models.
2. Implement data generation, validation, and ledger accounting tests.
3. Add reusable KPI calculations and scenario presets.
4. Train baseline and comparison models using chronological splits.
5. Add SQL and export logic for BI integration.
6. Build a minimal Streamlit application.
7. Add documentation, reproducibility notes, and final verification.

## Status
The repository is now being upgraded from a notebook prototype into a modular analytics platform with documented assumptions, tested inventory rules, and a reproducible scaffolding for future model and dashboard work.
