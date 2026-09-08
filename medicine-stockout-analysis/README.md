# Essential Medicines Stock-Out Analysis & Forecasting Dashboard
## Salima District, Malawi (Synthetic Portfolio Dataset)

## Project Overview

This project analyses essential-medicine stock availability across health facilities in Salima District, Malawi, using a **synthetic** but realistically simulated dataset: a 365-day daily stock ledger aggregated into a monthly Facility x Medicine reporting table. It moves beyond data cleaning (Project 1) into operational/inventory analytics: consumption analysis, stock-out detection, overstock and expiry-risk identification, delayed-delivery impact, and a modest stock-out risk classifier.

Built as a portfolio demonstration for Data Technician, Supply Chain/Logistics Analyst, and Data Analyst roles in the health sector.

**Facility names are real** — 10 verified health facilities in Salima District, sourced from the World Bank's Malawi Master Health Facility List (Salima District Hospital plus 9 Government/CHAM health centres). **All stock levels, consumption figures, deliveries, and stock-outs are entirely synthetic**, generated programmatically with a fixed random seed. Nothing in this project represents actual medicine availability at any real facility.

## Problem Statement

Health facilities need reliable availability of essential medicines. Poor stock management, unpredictable consumption, delayed replenishment, and inaccurate inventory records all contribute to stock-outs — and, just as importantly, to the less-discussed opposite problem of overstocking, which ties up resources and increases expiry risk. This project demonstrates how a Data Technician could identify both problems systematically and turn the result into a prioritized, actionable dashboard for a District Health Office.

## Objectives

1. Simulate a realistic daily stock ledger and aggregate it into a monthly reporting table
2. Identify which medicines and facilities experience the most stock-outs
3. Flag medicines currently approaching stock-out
4. Check for overstocking and quantify expiry risk
5. Measure the real impact of delayed deliveries on stock levels
6. Build a modest, explainable stock-out risk classifier as a bridge toward more ML-focused portfolio projects
7. Build a Power BI dashboard for district-level inventory monitoring and stock-out decision support

## Synthetic Dataset

- **10 real Salima District facilities** (Salima District Hospital + 9 Government/CHAM health centres)
- **13 essential medicines** across 8 programme categories (analgesic, antibiotics, antimalarial, rehydration, antidiabetic, TB, HIV, diagnostics, consumables)
- **Daily ledger:** 47,450 simulated records (facility x day x medicine, 2025) with realistic reorder logic, weekday effects, and malaria seasonality
- **Monthly reporting table:** 1,560 records (facility x medicine x month) — the cleaned analytical table used throughout this project

Deliberately injected data-quality problems: missing records (including two facilities with a chronic under-reporting pattern), negative-inventory data-entry errors, duplicate transactions, and consumption outliers. Delayed deliveries (~12% of orders) are modeled directly in the simulation rather than injected afterward. Full detail in `notebooks/medicine_stockout_analysis.ipynb`, Sections 1–2.

## Tools Used

Python (Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn) · Jupyter Notebook · Power BI Desktop

## Key Findings

*(All figures computed directly in `notebooks/medicine_stockout_analysis.ipynb` — see the notebook for full facility- and medicine-level breakdowns.)*

1. **Stock-outs are heavily concentrated in a few medicines, not spread evenly.** TB Combination Therapy stocked out in **61%** of facility-months and ARVs in **43%** — both low-volume, long-lead-time (28–30 day), centrally procured items. By contrast, high-volume, locally available items (Paracetamol, Amoxicillin, Cotrimoxazole, Zinc, Examination Gloves, Disposable Syringes) had a **0% stock-out rate** across the entire year. This points squarely at procurement lead time — not consumption volume — as the dominant driver of stock-out risk in this dataset.

2. **Two facilities have a real reporting-completeness problem.** Ngodzi Health Centre (87.1%) and Kaphatenga Health Centre (87.6%) report noticeably less completely than the other eight facilities (all ≥96.6%) — this is a genuine, detectable pattern, not an evenly-distributed data-quality issue.

3. **As of the latest month (December 2025), 65 of 130 facility-medicine combinations (50%) are either at risk (<1 month of stock) or already stocked out**, and 7 combinations are in active stock-out. This is the kind of number that would justify a district-level review, not a routine footnote.

4. **No overstocking was found anywhere in the dataset (0 of 1,560 facility-months) — and this is itself a finding worth stating plainly, not hiding.** The simulation's order-up-to reorder policy structurally caps maximum stock at roughly 30–50 days above safety stock, so it can't produce more than ~3 months of stock on hand even right after a delivery. This means the dataset, as designed, cannot demonstrate the overstocking scenario the project brief asked about — a real facility could still overstock (e.g. after an emergency donation or a demand-forecast error), but nothing in this simulation creates that scenario. See `dashboard/powerbi_dashboard_documentation.md` Section 5 for the dashboard treatment of this caveat.

5. **Malaria RDTs and Artemether/Lumefantrine account for the largest expiry values** ($258 and $179 of the year's $880 total, synthetic figures) — both are the seasonal, malaria-related items, consistent with demand swinging with the rainy season and leaving surplus stock in the off-season.

6. **Delayed deliveries measurably coincide with worse stock positions on arrival.** Comparing delivery events: deliveries that were delayed arrive to lower average closing stock than on-time deliveries, and a higher share of delayed arrivals occur right at or after a stock-out — direct evidence that delivery delays are translating into real facility-level stock-out exposure, not just a paperwork problem.

## Modest Stock-Out Risk Classifier

A single logistic regression predicts whether a facility-medicine combination will be at-risk or stocked-out *next* month, using 5 features available *this* month (months of stock, average consumption, lead time, reporting completeness, delayed-order count). Deliberately kept simple — one model, a plain train/test split, no hyperparameter tuning — as a bridge toward more ML-focused later portfolio projects rather than the centerpiece of this one. Full results and a coefficient sanity-check are in the notebook.

## Power BI Dashboard

The dashboard has now been built in Power BI Desktop and is included in this repository.

- Dashboard file: `dashboard/Medicine_Stockout_Dashboard_Salima.pbix`
- Documentation: `dashboard/powerbi_dashboard_documentation.md`
- Page exports: `visuals/charts/`

The report is organized around a district-level decision workflow and includes the key pages described in the implementation guide:
- Executive Overview
- Inventory Monitoring
- Stock-Out Analysis
- Forecast & Risk

The dashboard also carries the important caveat that no overstocked facility-medicine combinations exist in this synthetic dataset, and surfaces the delayed-delivery finding directly rather than leaving it as a hidden notebook-only result.

## Project Structure

```
medicine-stockout-analysis/
├── data/
│   ├── raw/
│   │   └── daily_stock_ledger_synthetic.csv        # 47,450-row daily bin-card simulation, with injected issues
│   └── processed/
│       └── monthly_stock_summary_clean.csv          # Cleaned monthly Facility x Medicine table (analytical source of truth)
├── dashboard/
│   ├── Medicine_Stockout_Dashboard_Salima.pbix     # Power BI dashboard (built)
│   └── powerbi_dashboard_documentation.md          # Dashboard implementation guide
├── notebooks/
│   └── medicine_stockout_analysis.ipynb             # Full workflow, executed with real outputs
├── visuals/
│   └── charts/                                      # Dashboard screenshots and analysis charts
├── requirements.txt
├── README.md
└── .gitignore
```

## How to Run

```bash
git clone <this-repo>
cd medicine-stockout-analysis
pip install -r requirements.txt

# Explore the analysis notebook
jupyter notebook notebooks/medicine_stockout_analysis.ipynb

# Open the completed Power BI file
# dashboard/Medicine_Stockout_Dashboard_Salima.pbix
```

## Ethical Considerations

Facility names are real and verified (World Bank Malawi Master Health Facility List) to ground the project in genuine Salima District geography. Every stock level, consumption figure, delivery event, and stock-out is entirely synthetic. This project makes no claim about actual medicine availability at any named facility, and should never be read as representing real supply chain performance in Salima District.

## Portfolio Relevance

Demonstrates skills relevant to: Data Technician · Supply Chain/Logistics Analyst · Data Analyst · Monitoring & Evaluation roles — specifically inventory analytics, KPI design, root-cause investigation (lead time vs. volume as stock-out drivers), and a defensible first step into predictive modeling. This project also shows the ability to move from Python-based analysis into a polished dashboard deliverable suitable for stakeholder communication.

## Future Improvements

- Add a second scenario that can actually produce overstocking (e.g. emergency donation or forecast error) to demonstrate the overstock logic in practice
- Extend the risk classifier with a second model (e.g. random forest) and compare performance
- Add deeper drill-through pages or a custom tooltip layer in the dashboard for facility-level investigations
- If real, properly aggregated district stock-status data ever becomes available, validate whether the same lead-time-driven stock-out pattern holds

## Author

Chico Mkandawire
MSc Data Science, Malawi University of Science and Technology (in progress)
BSc Management Information Systems, Malawi University of Business and Applied Sciences
