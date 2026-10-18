from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analytics.run_analysis import build_monthly_summary


st.set_page_config(page_title="Medicine Stock-Out Dashboard", layout="wide")
st.title("Medicine Stock-Out Decision Support")

base_path = Path("data/generated")
file_options = [p for p in base_path.glob("*_inventory_ledger.csv")] if base_path.exists() else []
selected = st.selectbox("Dataset", [p.name for p in file_options] or ["No generated data found"], index=0)

if selected == "No generated data found":
    st.warning("No synthetic dataset is present yet. Run the data generator first.")
    st.stop()

ledger = pd.read_csv(base_path / selected)
summary = build_monthly_summary(base_path / selected)

st.metric("Facilities", summary["facility_id"].nunique())
st.metric("Stock-out risk rows", int((summary["stock_status"] == "confirmed_stockout").sum()))

facility = st.selectbox("Facility", sorted(summary["facility_id"].unique()))
medicine = st.selectbox("Medicine", sorted(summary.loc[summary["facility_id"] == facility, "medicine_id"].unique()))

subset = summary[(summary["facility_id"] == facility) & (summary["medicine_id"] == medicine)]
if subset.empty:
    st.info("No records exist for this facility-medicine pair.")
else:
    row = subset.iloc[-1]
    st.subheader(f"{facility} / {medicine}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Closing stock", round(float(row["closing_stock"]), 2))
    col2.metric("Days of stock", round(float(row["days_of_stock"]), 2))
    col3.metric("Status", row["stock_status"])

    st.dataframe(subset[["closing_stock", "issued", "received", "days_of_stock", "reorder_point", "reorder_quantity", "stock_status"]].tail(12))
