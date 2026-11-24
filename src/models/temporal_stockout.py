from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "closing_stock",
    "issued",
    "received",
    "lead_time_days",
    "safety_stock",
    "days_of_stock",
    "reorder_point",
]


@dataclass(frozen=True)
class TemporalSplit:
    train: pd.DataFrame
    test: pd.DataFrame
    cutoff: pd.Timestamp
    purge_days: int


def build_forward_stockout_target(
    frame: pd.DataFrame,
    horizon_days: int = 30,
    min_future_reports: int = 21,
) -> pd.DataFrame:
    """Label a row when a *later* reported row shows stock-out within the horizon.

    The current row's status is never used as its target. Rows without sufficient
    future reporting coverage are marked label_available=False and excluded from
    model fitting. This is a forecasting target proxy, not a causal outcome.
    """
    if isinstance(horizon_days, bool) or not isinstance(horizon_days, int) or horizon_days < 1:
        raise ValueError("horizon_days must be a positive integer")
    if isinstance(min_future_reports, bool) or not isinstance(min_future_reports, int) or min_future_reports < 1:
        raise ValueError("min_future_reports must be a positive integer")

    required = {"facility_id", "medicine_id", "date", "stock_status", "reported"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["reported"] = data["reported"].fillna(False).astype(bool)
    data["stock_status"] = data["stock_status"].astype("string")
    data["target"] = pd.Series(pd.NA, index=data.index, dtype="Int64")
    data["label_available"] = False

    valid = data.dropna(subset=["date", "facility_id", "medicine_id"])
    for _, group in valid.groupby(["facility_id", "medicine_id"], sort=False):
        ordered = group.sort_values("date")
        dates = ordered["date"].to_numpy(dtype="datetime64[ns]")
        observed = ordered["reported"].to_numpy(dtype=bool)
        future_event = (
            ordered["reported"].to_numpy(dtype=bool)
            & ordered["stock_status"].isin(["confirmed_stockout"]).to_numpy(dtype=bool)
        )
        observed_prefix = np.concatenate(([0], np.cumsum(observed, dtype=np.int64)))
        event_prefix = np.concatenate(([0], np.cumsum(future_event, dtype=np.int64)))

        for position, (index, current_date) in enumerate(zip(ordered.index, dates)):
            left = np.searchsorted(dates, current_date, side="right")
            right = np.searchsorted(
                dates,
                current_date + np.timedelta64(horizon_days, "D"),
                side="right",
            )
            report_count = int(observed_prefix[right] - observed_prefix[left])
            if report_count < min_future_reports:
                continue
            event_count = int(event_prefix[right] - event_prefix[left])
            data.at[index, "target"] = int(event_count > 0)
            data.at[index, "label_available"] = True

    return data


def chronological_split(
    labelled: pd.DataFrame,
    test_fraction: float = 0.2,
    purge_days: int = 30,
) -> TemporalSplit:
    """Split by time and purge training rows whose target horizon touches test."""
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    if isinstance(purge_days, bool) or not isinstance(purge_days, int) or purge_days < 0:
        raise ValueError("purge_days must be a non-negative integer")

    data = labelled.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.loc[data["label_available"].astype(bool)].dropna(subset=["date", "target"])
    unique_dates = np.sort(data["date"].dropna().unique())
    if len(unique_dates) < 3:
        raise ValueError("At least three distinct labelled dates are required")
    split_position = max(1, min(len(unique_dates) - 1, int(np.floor(len(unique_dates) * (1-test_fraction)))))
    cutoff = pd.Timestamp(unique_dates[split_position])
    train_end = cutoff - pd.Timedelta(days=purge_days)
    train = data.loc[data["date"] < train_end].copy()
    test = data.loc[data["date"] >= cutoff].copy()
    if train.empty or test.empty:
        raise ValueError("Chronological split produced an empty train or test set")
    return TemporalSplit(train=train, test=test, cutoff=cutoff, purge_days=purge_days)


def fit_temporal_baseline(
    labelled: pd.DataFrame,
    test_fraction: float = 0.2,
    purge_days: int = 30,
    horizon_days: int = 30,
) -> tuple[object, dict, TemporalSplit]:
    """Fit a leakage-conscious logistic baseline and evaluate only future rows."""
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        average_precision_score,
        brier_score_loss,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    split = chronological_split(labelled, test_fraction=test_fraction, purge_days=purge_days)
    features = [column for column in FEATURE_COLUMNS if column in split.train.columns]
    if not features:
        raise ValueError("No supported model features are present")
    if split.train["target"].nunique() < 2:
        raise ValueError("Training period must contain both target classes")

    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(split.train[features], split.train["target"].astype(int))
    probability = model.predict_proba(split.test[features])[:, 1]
    prediction = (probability >= 0.5).astype(int)
    truth = split.test["target"].astype(int)
    metrics = {
        "train_rows": int(len(split.train)),
        "test_rows": int(len(split.test)),
        "train_start": str(split.train["date"].min().date()),
        "train_end": str(split.train["date"].max().date()),
        "test_start": str(split.test["date"].min().date()),
        "test_end": str(split.test["date"].max().date()),
        "purge_days": int(split.purge_days),
        "positive_rate_test": float(truth.mean()),
        "precision_at_0_5": float(precision_score(truth, prediction, zero_division=0)),
        "recall_at_0_5": float(recall_score(truth, prediction, zero_division=0)),
        "brier_score": float(brier_score_loss(truth, probability)),
        "roc_auc": float(roc_auc_score(truth, probability)) if truth.nunique() > 1 else None,
        "average_precision": float(average_precision_score(truth, probability)),
        "features": features,
        "target_definition": "reported confirmed stock-out in the subsequent horizon",
        "horizon_days": int(horizon_days),
    }
    return model, metrics, split
