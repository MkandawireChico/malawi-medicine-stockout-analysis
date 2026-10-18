from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


def build_target(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["target"] = (data["stock_status"].isin(["confirmed_stockout", "low_stock_warning"]).astype(int))
    return data


def train_baseline_model(input_csv: str | Path, output_dir: str | Path) -> dict:
    data = pd.read_csv(input_csv)
    frame = build_target(data)
    features = ["closing_stock", "lead_time_days", "safety_stock", "issued", "received"]
    X = frame[features].fillna(0)
    y = frame["target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "baseline_logistic_regression.joblib"
    import joblib
    joblib.dump(model, model_path)
    return {"model_path": str(model_path), "train_size": len(X_train), "test_size": len(X_test), "classes": list(model.classes_)}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Train a baseline stock-out classifier.")
    parser.add_argument("--input", default="outputs/summary.csv", help="Summary CSV to train on.")
    parser.add_argument("--output-dir", default="models", help="Where to save the trained model.")
    args = parser.parse_args()
    result = train_baseline_model(args.input, args.output_dir)
    print(result)


if __name__ == "__main__":
    main()
