from __future__ import annotations

from typing import Iterable

import pandas as pd


def safe_float(value, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def calculate_days_of_stock(usable_stock: float | int | None, avg_daily_consumption: float | int | None) -> float:
    """Return the number of days of usable stock remaining.

    Missing or zero consumption is treated explicitly as no reliable forecast.
    """
    stock = safe_float(usable_stock, 0.0)
    demand = safe_float(avg_daily_consumption, 0.0)
    if stock <= 0 or demand <= 0:
        return 0.0
    return round(stock / demand, 4)


def reorder_point(expected_demand_during_lead_time: float | int, safety_stock: float | int) -> float:
    """Return the minimum reorder trigger level."""
    return safe_float(expected_demand_during_lead_time, 0.0) + safe_float(safety_stock, 0.0)


def reorder_quantity(target_stock: float | int, stock_on_hand: float | int, incoming_stock: float | int = 0) -> float:
    """Return the recommended replenishment quantity under a max-stock policy."""
    target = safe_float(target_stock, 0.0)
    stock = safe_float(stock_on_hand, 0.0)
    inbound = safe_float(incoming_stock, 0.0)
    qty = target - stock - inbound
    return max(0.0, qty)


def detect_stockout_status(
    stock_on_hand: float | int | None,
    days_of_stock: float | int | None,
    lead_time_days: float | int | None,
    safety_stock: float | int | None,
    low_stock_threshold_days: float = 30.0,
    low_stock_offset_days: float = 7.0,
) -> str:
    """Classify inventory status using a simple rule-based framework.

    Values: confirmed_stockout, low_stock_warning, adequate, unknown.
    """
    stock = safe_float(stock_on_hand, 0.0)
    days = safe_float(days_of_stock, 0.0)
    lead_time = safe_float(lead_time_days, 0.0)
    safety = safe_float(safety_stock, 0.0)

    if stock <= 0 or days <= 0:
        return "confirmed_stockout"
    threshold = max(safety, lead_time * 0.5)
    if stock <= threshold or days <= 1.0:
        return "low_stock_warning"
    if 1.0 < days <= 7.0 and stock <= threshold * 2.0:
        return "low_stock_warning"
    return "adequate"


def validate_ledger(ledger: pd.DataFrame) -> list[dict]:
    """Validate an inventory ledger and return a list of issues.

    Hard validation errors are returned as dictionaries with facility_id, medicine_id,
    date, rule, severity, and explanation.
    """
    if ledger is None or ledger.empty:
        return []

    issues: list[dict] = []
    required = {"facility_id", "medicine_id", "date", "opening_stock", "received", "issued", "adjustment", "closing_stock"}
    missing = required - set(ledger.columns)
    if missing:
        for column in sorted(missing):
            issues.append(
                {
                    "facility_id": None,
                    "medicine_id": None,
                    "date": None,
                    "rule": "missing_required_column",
                    "severity": "error",
                    "explanation": f"Required ledger column '{column}' is missing.",
                }
            )
        return issues

    ledger = ledger.copy()
    ledger["date"] = pd.to_datetime(ledger["date"], errors="coerce")

    duplicates = ledger.duplicated(subset=["facility_id", "medicine_id", "date"], keep=False)
    duplicate_index = ledger.index[duplicates]
    for idx in duplicate_index:
        row = ledger.loc[idx]
        issues.append(
            {
                "facility_id": row.get("facility_id"),
                "medicine_id": row.get("medicine_id"),
                "date": row.get("date"),
                "rule": "duplicate_transaction",
                "severity": "error",
                "explanation": "The same facility-medicine-date transaction appears more than once.",
            }
        )
        issues.append(
            {
                "facility_id": row.get("facility_id"),
                "medicine_id": row.get("medicine_id"),
                "date": row.get("date"),
                "rule": "inconsistent_inventory_balance",
                "severity": "warning",
                "explanation": "Duplicate ledger rows indicate the balance could be overstated or understated after transaction consolidation.",
            }
        )

    for idx, row in ledger.iterrows():
        if pd.isna(row.get("facility_id")) or pd.isna(row.get("medicine_id")):
            issues.append(
                {
                    "facility_id": row.get("facility_id"),
                    "medicine_id": row.get("medicine_id"),
                    "date": row.get("date"),
                    "rule": "missing_identifier",
                    "severity": "error",
                    "explanation": "Facility or medicine identifier is missing.",
                }
            )

        if pd.isna(row.get("date")):
            issues.append(
                {
                    "facility_id": row.get("facility_id"),
                    "medicine_id": row.get("medicine_id"),
                    "date": row.get("date"),
                    "rule": "invalid_date",
                    "severity": "error",
                    "explanation": "Date value is not valid.",
                }
            )

        opening = safe_float(row.get("opening_stock"), 0.0)
        received = safe_float(row.get("received"), 0.0)
        issued = safe_float(row.get("issued"), 0.0)
        adjustment = safe_float(row.get("adjustment"), 0.0)
        closing = safe_float(row.get("closing_stock"), 0.0)
        losses = safe_float(row.get("losses"), 0.0)

        if closing < 0:
            issues.append(
                {
                    "facility_id": row.get("facility_id"),
                    "medicine_id": row.get("medicine_id"),
                    "date": row.get("date"),
                    "rule": "negative_closing_stock",
                    "severity": "error",
                    "explanation": "Closing stock is below zero, which is physically impossible for standard stock balances.",
                }
            )

        expected_closing = opening + received + adjustment - issued - losses
        if abs(expected_closing - closing) > 0.05:
            issues.append(
                {
                    "facility_id": row.get("facility_id"),
                    "medicine_id": row.get("medicine_id"),
                    "date": row.get("date"),
                    "rule": "inconsistent_inventory_balance",
                    "severity": "warning",
                    "explanation": (
                        "Closing stock differs from the accounting identity. "
                        f"Expected {expected_closing:.2f}, observed {closing:.2f}."
                    ),
                }
            )

    return issues


def inventory_status_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["facility_id", "medicine_id", "stock_on_hand", "days_of_stock", "status"])

    summary = df.copy()
    summary["stock_on_hand"] = summary.get("stock_on_hand", 0.0).apply(lambda x: safe_float(x, 0.0))
    summary["days_of_stock"] = summary.apply(
        lambda row: calculate_days_of_stock(row.get("stock_on_hand"), row.get("avg_daily_consumption")), axis=1
    )
    summary["status"] = summary.apply(
        lambda row: detect_stockout_status(
            row.get("stock_on_hand"),
            row.get("days_of_stock"),
            row.get("lead_time_days"),
            row.get("safety_stock"),
        ),
        axis=1,
    )
    return summary[["facility_id", "medicine_id", "stock_on_hand", "days_of_stock", "status"]]
