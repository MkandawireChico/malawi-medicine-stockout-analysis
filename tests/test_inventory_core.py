import pandas as pd

from src.analytics.inventory import (
    calculate_days_of_stock,
    detect_stockout_status,
    reorder_point,
    reorder_quantity,
    validate_ledger,
)


def test_days_of_stock_handles_zero_and_missing_consumption():
    assert calculate_days_of_stock(120.0, 10.0) == 12.0
    assert calculate_days_of_stock(0.0, 10.0) == 0.0
    assert calculate_days_of_stock(80.0, 0.0) == 0.0
    assert calculate_days_of_stock(80.0, None) == 0.0


def test_reorder_point_and_quantity_logic():
    assert reorder_point(25.0, 10.0) == 35.0
    assert reorder_quantity(target_stock=200.0, stock_on_hand=150.0, incoming_stock=20.0) == 30.0
    assert reorder_quantity(target_stock=200.0, stock_on_hand=300.0, incoming_stock=0.0) == 0.0


def test_detect_stockout_status_distinguishes_states():
    assert detect_stockout_status(0.0, 0.0, 7.0, 0.0) == "confirmed_stockout"
    assert detect_stockout_status(50.0, 0.5, 9.0, 5.0) == "low_stock_warning"
    assert detect_stockout_status(40.0, 2.5, 14.0, 15.0) == "adequate"


def test_validate_ledger_flags_duplicates_and_impossible_events():
    ledger = pd.DataFrame(
        {
            "facility_id": ["F1", "F1", "F1", "F2"],
            "medicine_id": ["M1", "M1", "M1", "M1"],
            "date": ["2025-01-01", "2025-01-01", "2025-01-02", "2025-01-02"],
            "opening_stock": [100.0, 100.0, 200.0, 50.0],
            "received": [0.0, 10.0, 0.0, 0.0],
            "issued": [10.0, 5.0, 200.0, 60.0],
            "adjustment": [0.0, 0.0, 0.0, 0.0],
            "closing_stock": [90.0, 105.0, 0.0, -10.0],
        }
    )

    issues = validate_ledger(ledger)
    assert any(issue["rule"] == "duplicate_transaction" for issue in issues)
    assert any(issue["rule"] == "negative_closing_stock" for issue in issues)
    assert any(issue["rule"] == "inconsistent_inventory_balance" for issue in issues)
