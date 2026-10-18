from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    preds = model.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, preds),
        "precision": precision_score(y_test, preds, zero_division=0),
        "recall": recall_score(y_test, preds, zero_division=0),
        "f1": f1_score(y_test, preds, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
    }
    return metrics


def main() -> None:
    import argparse
    import joblib

    parser = argparse.ArgumentParser(description="Evaluate a stock-out baseline model.")
    parser.add_argument("--input", default="outputs/summary.csv", help="Summary CSV used for evaluation.")
    parser.add_argument("--model", default="models/baseline_logistic_regression.joblib", help="Path to trained model.")
    args = parser.parse_args()
    data = pd.read_csv(args.input)
    data["target"] = data["stock_status"].isin(["confirmed_stockout", "low_stock_warning"]).astype(int)
    X = data[["closing_stock", "lead_time_days", "safety_stock", "issued", "received"]].fillna(0)
    y = data["target"]
    model = joblib.load(args.model)
    metrics = evaluate_model(model, X, y)
    print(metrics)


if __name__ == "__main__":
    main()
