from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_FACILITIES = [
    "Salima District Hospital",
    "Chagunda Health Centre",
    "Makanjira Health Centre",
    "Kaphatenga Health Centre",
    "M'bango Health Centre",
    "Mponela Health Centre",
    "Ngodzi Health Centre",
    "Senga Bay Health Centre",
    "Makanjira Rural Clinic",
    "Maganga Health Centre",
]

DEFAULT_MEDICINES = [
    "Amoxicillin",
    "Artemether/Lumefantrine",
    "ARVs (TDF/3TC/DTG)",
    "Cotrimoxazole",
    "Disposable Syringes",
    "Examination Gloves",
    "Malaria RDTs",
    "Oral Rehydration Salts",
    "Paracetamol",
    "TB Combination Therapy",
    "Zinc",
    "Insulin",
    "Amlodipine",
]


def _date_range(start: str, days: int):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    for offset in range(days):
        yield start_dt + timedelta(days=offset)


def generate_ledger(seed: int = 42, facilities: list[str] | None = None, medicines: list[str] | None = None, start_date: str = "2025-01-01", days: int = 365) -> pd.DataFrame:
    """Generate a deterministic synthetic inventory ledger.

    The ledger keeps the same accounting equation used in the health supply-chain
    logic: closing_stock = opening_stock + received + adjustments - issued - losses.
    """
    rng = np.random.default_rng(seed)
    facility_names = facilities or DEFAULT_FACILITIES
    medicine_names = medicines or DEFAULT_MEDICINES

    records: list[dict] = []
    for facility in facility_names:
        for medicine in medicine_names:
            base_demand = 18.0 + rng.uniform(2.0, 18.0)
            stock = 220.0 + rng.uniform(40.0, 180.0)
            lead_time = int(7 + rng.integers(0, 18))
            safety_stock = max(15.0, base_demand * 10.0)
            order_target = base_demand * 45.0
            for date in _date_range(start_date, days):
                seasonal_multiplier = 1.0 + 0.45 * np.sin((date.timetuple().tm_yday / 365.0) * 2 * np.pi)
                demand = max(0.0, base_demand * seasonal_multiplier * (1.0 + rng.normal(0.0, 0.18)))
                if date.weekday() >= 5:
                    demand *= 0.75

                reported = rng.random() > 0.07
                if not reported:
                    demand = 0.0

                received = 0.0
                if rng.random() < 0.04:
                    received = max(10.0, base_demand * (10 + rng.integers(0, 14)))
                    if rng.random() < 0.12:
                        received *= 0.5

                adjustment = 0.0
                if rng.random() < 0.02:
                    adjustment = rng.uniform(-10.0, 15.0)

                losses = 0.0
                if rng.random() < 0.01:
                    losses = rng.uniform(1.0, 8.0)

                opening_stock = stock
                issued = min(max(demand, 0.0), max(opening_stock, 0.0))
                stock = opening_stock + received + adjustment - issued - losses
                if stock < 0:
                    stock = 0.0

                if rng.random() < 0.02:
                    stock = max(0.0, stock - rng.uniform(12.0, 50.0))

                records.append(
                    {
                        "facility_id": facility,
                        "facility_type": "Health Facility",
                        "medicine_id": medicine,
                        "medicine_category": "General",
                        "date": date.strftime("%Y-%m-%d"),
                        "opening_stock": round(opening_stock, 2),
                        "received": round(received, 2),
                        "issued": round(issued, 2),
                        "adjustment": round(adjustment, 2),
                        "losses": round(losses, 2),
                        "closing_stock": round(stock, 2),
                        "lead_time_days": lead_time,
                        "safety_stock": round(safety_stock, 2),
                        "target_stock": round(order_target, 2),
                        "reported": bool(reported),
                    }
                )

    return pd.DataFrame(records)


def generate_scenario_data(seed: int = 42, scenario: str = "baseline") -> pd.DataFrame:
    df = generate_ledger(seed=seed)
    if scenario == "delayed_deliveries":
        df["received"] = df["received"] * 0.7
    elif scenario == "high_demand":
        df["issued"] = df["issued"] * 1.35
    elif scenario == "improved_policy":
        df["safety_stock"] = df["safety_stock"] * 1.25
    return df


def write_generated_data(output_dir: str | Path, seed: int = 42) -> dict[str, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    baseline = generate_ledger(seed=seed)
    delayed = generate_scenario_data(seed=seed, scenario="delayed_deliveries")
    high_demand = generate_scenario_data(seed=seed, scenario="high_demand")
    improved = generate_scenario_data(seed=seed, scenario="improved_policy")

    paths = {
        "baseline": root / "baseline_inventory_ledger.csv",
        "delayed_deliveries": root / "delayed_deliveries_inventory_ledger.csv",
        "high_demand": root / "high_demand_inventory_ledger.csv",
        "improved_policy": root / "improved_policy_inventory_ledger.csv",
    }
    baseline.to_csv(paths["baseline"], index=False)
    delayed.to_csv(paths["delayed_deliveries"], index=False)
    high_demand.to_csv(paths["high_demand"], index=False)
    improved.to_csv(paths["improved_policy"], index=False)
    return paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate deterministic synthetic inventory scenario datasets.")
    parser.add_argument("--output-dir", default="data/generated", help="Directory for generated CSV outputs.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = parser.parse_args()
    paths = write_generated_data(args.output_dir, seed=args.seed)
    for name, path in paths.items():
        print(f"{name}: {path}")
