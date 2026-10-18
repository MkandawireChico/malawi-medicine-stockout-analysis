from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analytics.inventory import validate_ledger


def validate_dataset(csv_path: str | Path) -> list[dict]:
    """Load a ledger file and validate the contents."""
    df = pd.read_csv(csv_path)
    return validate_ledger(df)


def export_validation_report(csv_path: str | Path, output_path: str | Path) -> str:
    issues = validate_dataset(csv_path)
    report = pd.DataFrame(issues)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output, index=False)
    return str(output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate generated or processed leadger data.")
    parser.add_argument("csv_path", help="Path to ledger CSV.")
    parser.add_argument("--output", default="data/quality/validation_issues.csv", help="Where to store the issue report.")
    args = parser.parse_args()
    issues = validate_dataset(args.csv_path)
    print(f"Validation issues found: {len(issues)}")
    for issue in issues[:10]:
        print(issue)
    export_validation_report(args.csv_path, args.output)
