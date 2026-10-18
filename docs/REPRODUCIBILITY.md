# Reproducibility

All synthetic data generation uses fixed random seeds. This allows the same scenarios to be regenerated deterministically for comparisons, testing, and presentation.

## Example workflow
```bash
python -m src.data.generate --output-dir data/generated --seed 42
python -m src.data.validate data/generated/baseline_inventory_ledger.csv --output data/quality/validation_issues.csv
python -m src.analytics.run_analysis --input data/generated/baseline_inventory_ledger.csv --output outputs/summary.csv
python -m src.models.train --input outputs/summary.csv --output-dir models/
```

## Notes
- Keep the same seed to reproduce the same baseline ledger.
- Store report outputs in versioned folders for comparison.
- Keep scenario files separate so the baseline remains comparable to intervention runs.
