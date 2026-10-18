from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analytics.inventory import calculate_days_of_stock, detect_stockout_status, reorder_point, reorder_quantity
from src.data.validate import validate_dataset


def build_monthly_summary(input_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    if "closing_stock" not in df.columns:
        raise ValueError("Input ledger must include closing_stock.")
    summary = df.copy()
    summary["avg_daily_consumption"] = summary["issued"].clip(lower=0).replace(0, pd.NA) / 30.0
    summary["days_of_stock"] = summary.apply(
        lambda row: calculate_days_of_stock(row.get("closing_stock"), row.get("avg_daily_consumption")), axis=1
    )
    summary["reorder_point"] = summary.apply(
        lambda row: reorder_point(row.get("lead_time_days", 0), row.get("safety_stock", 0)), axis=1
    )
    summary["reorder_quantity"] = summary.apply(
        lambda row: reorder_quantity(
            row.get("target_stock", 0),
            row.get("closing_stock", 0),
            row.get("received", 0),
        ),
        axis=1,
    )
    summary["stock_status"] = summary.apply(
        lambda row: detect_stockout_status(
            row.get("closing_stock"),
            row.get("days_of_stock"),
            row.get("lead_time_days"),
            row.get("safety_stock"),
        ),
        axis=1,
    )
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build a stock status summary from a generated ledger.")
    parser.add_argument("--input", default="data/generated/baseline_inventory_ledger.csv", help="CSV path to the ledger file.")
    parser.add_argument("--output", default="outputs/summary.csv", help="Destination CSV for the summary.")
    args = parser.parse_args()

    validation_issues = validate_dataset(args.input)
    summary = build_monthly_summary(args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out, index=False)
    print(f"Rows written: {len(summary)}")
    print(f"Validation issues: {len(validation_issues)}")


if __name__ == "__main__":
    main()
