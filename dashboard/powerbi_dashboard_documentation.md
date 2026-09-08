# Power BI Dashboard — Implementation Documentation

**Status: not yet built.** This is a structured implementation plan, written from the actual fields and findings in `data/processed/monthly_stock_summary_clean.csv` (produced by `notebooks/medicine_stockout_analysis.ipynb`), for building the dashboard in Power BI Desktop.

All data behind this dashboard is synthetic. Facility names are real, verified Salima District facilities; every stock/consumption/delivery figure is generated. See the project [README](../README.md).

---

## 1. Data source

Primary: `data/processed/monthly_stock_summary_clean.csv` — the monthly Facility x Medicine reporting table (1,560 rows), with all engineered fields (`Months_of_Stock`, `Reorder_Point`, `Stock_Status`, `Inventory_Value`, `Expiry_Value`) already computed.

Secondary (optional, for a drill-through/detail page): `data/raw/daily_stock_ledger_synthetic.csv` — the 47,000+ row daily ledger, useful if a "day-level" investigation view is wanted for a specific facility-medicine.

## 2. Data model

A single flat monthly table plus a Calendar date table is sufficient here:

```
Calendar (date dimension, keyed on month) ---1:*--- monthly_stock_summary (fact/flat table)
```

Mark Calendar as a Date Table in Power BI so month-over-month trend visuals use real time intelligence.

## 3. Measures (DAX)

```dax
Total Facilities = DISTINCTCOUNT(stock[Facility])
Medicines Monitored = DISTINCTCOUNT(stock[Medicine])

Stock-Out Rate = 
    DIVIDE(
        CALCULATE(COUNTROWS(stock), stock[Stockout_Flag_Month] = TRUE),
        COUNTROWS(stock)
    )

Total Stock-Out Days = SUM(stock[Days_Out_Of_Stock])

Inventory Value = SUM(stock[Inventory_Value])
Expiry Value = SUM(stock[Expiry_Value])

Medicines At High Risk = 
    CALCULATE(
        COUNTROWS(stock),
        stock[Stock_Status] IN {"Stock-Out", "At Risk (<1 month)"}
    )

Order Fulfilment Rate = 
    DIVIDE(
        SUM(stock[Orders_Placed]) - SUM(stock[Orders_Delayed]),
        SUM(stock[Orders_Placed])
    )

Avg Reporting Completeness = AVERAGE(stock[Reporting_Completeness])
```

**Why `DIVIDE()` instead of `/`:** returns `BLANK()` instead of erroring when a slicer selection produces a zero-order or zero-row context — this happens often once Medicine/Facility slicers are added.

## 4. Pages

### Page 1 — Executive Overview

KPI cards: `[Total Facilities]`, `[Medicines Monitored]`, `[Stock-Out Rate]`, `[Total Stock-Out Days]`, `[Inventory Value]`, `[Expiry Value]`, `[Medicines At High Risk]`.

Visuals:
- Stock-out trend by month (line)
- Stock-out rate by facility (bar)
- Stock-out rate by medicine (bar) — this is the single most important chart on the page, since the notebook found stock-outs are heavily concentrated in a few medicines rather than spread evenly (Section 6)
- Facility list/table with `Avg_Reporting_Completeness` as a conditional-formatted column

### Page 2 — Inventory Monitoring

- Current stock, `Months_of_Stock`, and `Stock_Status` for every facility-medicine combination (matrix or table), filterable by month
- Conditional formatting (red/amber/green) on `Stock_Status`
- Reorder status: `Closing_Stock` vs. `Reorder_Point`, flagged where stock has fallen below the reorder point

### Page 3 — Stock-Out Analysis

- Stock-outs by facility (bar)
- Stock-outs by medicine (bar)
- Monthly stock-out trend
- Top medicines by total stock-out days (table)
- **Delayed-delivery callout** (see Section 6 below) — this belongs on this page, not buried in a footnote

### Page 4 — Forecast & Risk

- `Average_Monthly_Consumption` vs. `Closing_Stock` scatter, colored by `Stock_Status`
- The logistic regression risk classifier's predictions (recomputed in Power Query or pre-scored and joined in) shown as a "predicted at-risk next month" flag
- Recommended reorder quantity: `Maximum_Stock_Level - Closing_Stock` for anything below `Reorder_Point`

## 5. An honest caveat worth building into Page 2 and Page 4 directly

**The notebook found zero overstocked facility-medicine combinations across the entire year (0 of 1,560 facility-months).** This is a real result, not an oversight — worth stating plainly on the dashboard rather than omitting the "Overstocked" category and hoping nobody asks. The reason is structural: the simulation's order-up-to policy caps maximum stock at roughly 30–50 days of consumption above safety stock, which rarely produces more than 3 months of stock on hand even right after a delivery. **In other words: this dataset, as designed, cannot demonstrate the overstocking scenario the original project brief asked about** — a real facility could still overstock (e.g. after a large emergency donation, a demand forecast error, or a programme handover of leftover stock), but nothing in this particular simulation creates that scenario.

Rather than quietly dropping "overstocking" from the dashboard, Page 2 should keep the `Stock_Status` category and simply show it at zero, with a note: *"No facility-medicine combination exceeded 3 months of stock in this dataset — see project README for why."* That's a more honest and more interview-defensible dashboard than one that implies overstocking was checked and found not to matter, when actually the simulation design prevented it from ever occurring.

## 6. Delayed-delivery finding to surface on Page 3

The notebook directly compared stock levels the day a delivery arrived, split by whether that delivery was on-time or delayed (Section 12). Pull the two summary numbers (average closing stock at arrival, and share of arrivals that occurred at/after a stock-out) into a text box or two extra KPI cards on Page 3 — this is one of the more concrete, decision-relevant findings in the whole project and shouldn't be Python-notebook-only.

## 7. Build order

1. Import the monthly table, build the Calendar table
2. Write the core measures (Section 3)
3. Build Page 1's KPIs and stock-out-rate-by-medicine chart first — sense-check every number against the notebook's printed output
4. Build Pages 2–4
5. Add the Section 5 and Section 6 callouts — don't skip these; they're what make the dashboard trustworthy rather than just complete-looking
6. Add slicers (Month, Facility, Medicine, Medicine_Category) last
7. Screenshot into `visuals/` and link from the main README
