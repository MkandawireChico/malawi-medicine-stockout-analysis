from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analytics.run_analysis import build_monthly_summary
from src.analytics.inventory import detect_stockout_status
from src.data.generate import generate_ledger

st.set_page_config(page_title="Medicine Stock-Out Decision Support", page_icon="💊", layout="wide")
st.title("Medicine Stock-Out Decision Support")
st.caption("Inventory visibility • replenishment review • facility-level monitoring")

base_path = REPO_ROOT / "data" / "generated"
base_path.mkdir(parents=True, exist_ok=True)
baseline_path = base_path / "baseline_inventory_ledger.csv"
if not list(base_path.glob("*_inventory_ledger.csv")):
    generate_ledger(seed=42).to_csv(baseline_path, index=False)

file_options = sorted(base_path.glob("*_inventory_ledger.csv"))
if not file_options:
    st.error("No inventory ledger is available.")
    st.stop()

with st.sidebar:
    st.header("Analysis controls")
    selected = st.selectbox("Scenario dataset", [p.name for p in file_options], index=0)
    st.caption("Choose a baseline or scenario ledger to compare inventory conditions.")
    st.divider()
    st.caption("Indicators are rule-based estimates from the selected ledger.")

ledger_path = base_path / selected
with st.spinner("Preparing inventory indicators…"):
    raw = pd.read_csv(ledger_path, parse_dates=["date"])
    summary = build_monthly_summary(ledger_path)

if summary.empty:
    st.warning("The selected ledger contains no records.")
    st.stop()

summary["date"] = pd.to_datetime(summary["date"], errors="coerce")
# The source rows are daily. Estimate consumption from a trailing 30-record
# window per facility/medicine instead of dividing one day's issues by 30.
summary = summary.sort_values(["facility_id", "medicine_id", "date"]).copy()
summary["avg_daily_consumption"] = (
    summary.groupby(["facility_id", "medicine_id"])["issued"]
    .transform(lambda values: values.rolling(30, min_periods=1).mean())
)
summary["days_of_stock"] = (
    summary["closing_stock"] / summary["avg_daily_consumption"].replace(0, pd.NA)
).fillna(0).clip(lower=0)
summary["reorder_point"] = (
    summary["avg_daily_consumption"] * summary["lead_time_days"] + summary["safety_stock"]
)
summary["reorder_quantity"] = (
    summary["target_stock"] - summary["closing_stock"] - summary["received"]
).clip(lower=0)
summary["stock_status"] = summary.apply(
    lambda row: detect_stockout_status(
        row["closing_stock"], row["days_of_stock"],
        row["lead_time_days"], row["safety_stock"]
    ), axis=1
)
latest_date = summary["date"].max()
snapshot = (summary.sort_values("date")
            .groupby(["facility_id", "medicine_id"], as_index=False)
            .tail(1).copy())
status_order = ["confirmed_stockout", "low_stock_warning", "adequate", "unknown"]
status_counts = snapshot["stock_status"].value_counts()
stockouts = int(status_counts.get("confirmed_stockout", 0))
low_stock = int(status_counts.get("low_stock_warning", 0))
adequate = int(status_counts.get("adequate", 0))
pairs = len(snapshot)
reporting_rate = float(raw["reported"].astype(bool).mean() * 100) if "reported" in raw else float("nan")

st.caption(f"Dataset: **{selected}** · Latest ledger date: **{latest_date:%d %b %Y}** · {len(raw):,} daily records")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Facilities", f"{snapshot['facility_id'].nunique():,}")
m2.metric("Medicine types", f"{snapshot['medicine_id'].nunique():,}")
m3.metric("Facility–medicine pairs", f"{pairs:,}")
m4.metric("Stock-out flags", f"{stockouts:,}", delta=f"{stockouts / max(pairs, 1):.1%} of pairs", delta_color="inverse")
m5.metric("Low-stock warnings", f"{low_stock:,}")

tab_overview, tab_risk, tab_facility, tab_trends, tab_quality = st.tabs([
    "Overview", "Risk register", "Facility review", "Inventory trends", "Data quality"
])

with tab_overview:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Current inventory status")
        status_frame = pd.DataFrame({
            "Status": ["Stock-out", "Low stock", "Adequate", "Unknown"],
            "Facility–medicine pairs": [
                stockouts, low_stock, adequate, int(status_counts.get("unknown", 0))
            ],
        }).set_index("Status")
        st.bar_chart(status_frame)
    with right:
        st.subheader("Facilities requiring attention")
        attention = snapshot[snapshot["stock_status"].isin(["confirmed_stockout", "low_stock_warning"])]
        facility_attention = (attention.groupby("facility_id")
                              .agg(Pairs_at_risk=("medicine_id", "count"),
                                   Stock_out_flags=("stock_status", lambda x: int((x == "confirmed_stockout").sum())))
                              .sort_values(["Stock_out_flags", "Pairs_at_risk"], ascending=False)
                              .head(10))
        if facility_attention.empty:
            st.success("No stock-out or low-stock flags in the latest snapshot.")
        else:
            st.dataframe(facility_attention, use_container_width=True)
    st.subheader("Highest-priority medicine items")
    priority = snapshot[snapshot["stock_status"].isin(["confirmed_stockout", "low_stock_warning"])].copy()
    priority["priority_rank"] = priority["stock_status"].map({"confirmed_stockout": 0, "low_stock_warning": 1})
    priority = priority.sort_values(["priority_rank", "days_of_stock", "reorder_quantity"])
    show_cols = ["facility_id", "medicine_id", "closing_stock", "days_of_stock", "lead_time_days", "reorder_point", "reorder_quantity", "stock_status"]
    if priority.empty:
        st.info("No priority items were identified in this snapshot.")
    else:
        st.dataframe(priority[show_cols].head(20).round(1), use_container_width=True, hide_index=True)

with tab_risk:
    st.subheader("Search and filter the latest risk register")
    c1, c2, c3 = st.columns(3)
    facility_options = ["All facilities"] + sorted(snapshot["facility_id"].dropna().unique().tolist())
    medicine_options = ["All medicines"] + sorted(snapshot["medicine_id"].dropna().unique().tolist())
    risk_facility = c1.selectbox("Facility filter", facility_options)
    risk_medicine = c2.selectbox("Medicine filter", medicine_options)
    risk_status = c3.multiselect("Status filter", status_order, default=["confirmed_stockout", "low_stock_warning"])
    filtered = snapshot.copy()
    if risk_facility != "All facilities":
        filtered = filtered[filtered["facility_id"] == risk_facility]
    if risk_medicine != "All medicines":
        filtered = filtered[filtered["medicine_id"] == risk_medicine]
    if risk_status:
        filtered = filtered[filtered["stock_status"].isin(risk_status)]
    st.caption(f"{len(filtered):,} matching facility–medicine pairs")
    st.dataframe(filtered[show_cols].sort_values(["days_of_stock", "facility_id"]).round(2),
                 use_container_width=True, hide_index=True)
    st.download_button("Download filtered risk register", filtered[show_cols].to_csv(index=False),
                       file_name="medicine_stockout_risk_register.csv", mime="text/csv")

with tab_facility:
    st.subheader("Facility and medicine drill-down")
    fc1, fc2 = st.columns(2)
    chosen_facility = fc1.selectbox("Select facility", sorted(snapshot["facility_id"].unique()), key="detail_facility")
    facility_medicines = sorted(summary.loc[summary["facility_id"] == chosen_facility, "medicine_id"].unique())
    chosen_medicine = fc2.selectbox("Select medicine", facility_medicines, key="detail_medicine")
    history = summary[(summary["facility_id"] == chosen_facility) & (summary["medicine_id"] == chosen_medicine)].sort_values("date")
    latest = history.iloc[-1]
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Closing stock", f"{latest['closing_stock']:,.1f}")
    d2.metric("Days of stock", f"{latest['days_of_stock']:,.1f}")
    d3.metric("Reorder point", f"{latest['reorder_point']:,.1f}")
    d4.metric("Suggested reorder qty", f"{latest['reorder_quantity']:,.1f}")
    st.write(f"**Current status:** {latest['stock_status'].replace('_', ' ').title()}  ·  **As of:** {latest['date']:%d %b %Y}")
    st.subheader("Recent stock movement")
    st.dataframe(history[["date", "opening_stock", "received", "issued", "losses", "closing_stock", "days_of_stock", "stock_status"]].tail(30).round(2),
                 use_container_width=True, hide_index=True)
    trend = history.set_index("date")[["closing_stock"]]
    st.line_chart(trend, y="closing_stock", height=250)

with tab_trends:
    st.subheader("Inventory movement over time")
    trend_facility = st.selectbox("Facility for trend", sorted(summary["facility_id"].unique()), key="trend_facility")
    trend_medicine = st.selectbox(
        "Medicine for trend",
        sorted(summary.loc[summary["facility_id"] == trend_facility, "medicine_id"].unique()),
        key="trend_medicine",
    )
    trend_data = summary[(summary["facility_id"] == trend_facility) & (summary["medicine_id"] == trend_medicine)].sort_values("date").set_index("date")
    st.line_chart(trend_data[["closing_stock", "issued", "received"]], height=320)
    monthly = trend_data[["issued", "received"]].resample("MS").sum()
    st.subheader("Monthly issues and receipts")
    st.bar_chart(monthly, height=260)

with tab_quality:
    st.subheader("Reporting coverage and ledger profile")
    q1, q2, q3 = st.columns(3)
    q1.metric("Daily ledger rows", f"{len(raw):,}")
    q2.metric("Reported records", f"{int(raw['reported'].astype(bool).sum()):,}" if "reported" in raw else "Not available")
    q3.metric("Reporting rate", f"{reporting_rate:.1f}%" if pd.notna(reporting_rate) else "Not available")
    if "reported" in raw:
        reporting = raw.assign(month=raw["date"].dt.to_period("M").astype(str)).groupby("month")["reported"].mean().mul(100)
        st.subheader("Monthly reporting rate")
        st.line_chart(reporting)
    st.subheader("Ledger fields")
    st.write(", ".join(raw.columns.astype(str)))
    st.info("This view describes reporting flags and the available ledger structure. It does not independently certify stock balances or repair missing records.")

st.divider()
st.caption("Decision-support demonstration only. Stock status and reorder quantities are rule-based estimates; verify source records and local supply protocols before acting.")
