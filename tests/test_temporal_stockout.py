import pandas as pd
import pytest

from src.models.temporal_stockout import build_forward_stockout_target, chronological_split


def sample_ledger(days=90):
    dates = pd.date_range("2025-01-01", periods=days, freq="D")
    rows = []
    for day, date in enumerate(dates):
        rows.append(
            {
                "facility_id": "F1",
                "medicine_id": "M1",
                "date": date,
                "stock_status": "confirmed_stockout" if day == 40 else "adequate",
                "reported": True,
                "closing_stock": max(0, 100 - day * 2),
                "issued": 2.0,
                "received": 0.0,
                "lead_time_days": 10,
                "safety_stock": 20.0,
                "days_of_stock": max(0, 50 - day),
                "reorder_point": 40.0,
            }
        )
    return pd.DataFrame(rows)


def test_target_uses_future_stockout_not_current_status():
    labelled = build_forward_stockout_target(
        sample_ledger(), horizon_days=10, min_future_reports=8
    )
    # The day-30 row sees the stockout on day 40 in its future window.
    day_30 = labelled.loc[labelled["date"] == pd.Timestamp("2025-01-31")].iloc[0]
    assert day_30["target"] == 1
    # The stockout row itself has no later event in its next ten days.
    day_40 = labelled.loc[labelled["date"] == pd.Timestamp("2025-02-10")].iloc[0]
    assert day_40["target"] == 0


def test_unreported_future_window_is_not_labelled_negative():
    frame = sample_ledger()
    frame.loc[31:89, "reported"] = False
    labelled = build_forward_stockout_target(
        frame, horizon_days=10, min_future_reports=8
    )
    row = labelled.loc[labelled["date"] == pd.Timestamp("2025-02-01")].iloc[0]
    assert not row["label_available"]
    assert pd.isna(row["target"])


def test_temporal_split_has_no_overlap_or_horizon_leakage():
    labelled = build_forward_stockout_target(
        sample_ledger(), horizon_days=10, min_future_reports=8
    )
    split = chronological_split(labelled, test_fraction=0.2, purge_days=10)
    assert split.train["date"].max() < split.cutoff - pd.Timedelta(days=10)
    assert split.test["date"].min() >= split.cutoff
    assert split.train["date"].max() < split.test["date"].min()


@pytest.mark.parametrize("value", [True, 0, -1, 1.5])
def test_invalid_horizon_rejected(value):
    with pytest.raises(ValueError, match="horizon_days"):
        build_forward_stockout_target(sample_ledger(), horizon_days=value)
