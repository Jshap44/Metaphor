# Monster Q3 2026 Historical Validation Lab

## What this adds

This adds an **exploratory hypothesis test**, not a validated financial forecasting system:

* Reported Q3 2026 versus Q3 2025 net sales, Monster Energy segment sales, energy-drink 192-ounce case-equivalent volume, and average net sales per case.
* Six independently adjustable hypothetical consumer drivers: Monster retail price, student budget, new flavor/product appeal, marketing, competing promotions, and stockouts.
* An uncalibrated Monster-preferring student-demand proxy from the project's existing synthetic-persona CSV. Interview personas remain separate and **do not count as representative market observations**.
* A chart and table that compare *direction*, not commensurate forecast errors, versus observed company case-volume growth.
* A fixed list of hypothesis scenarios and CSV/JSON exports, plus 6 unit tests.

## Quick start (Windows PowerShell)

From `socsci_agents/`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ui,test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m socsci_agents.historical_cli
.\.venv\Scripts\python.exe -m streamlit run energy_dashboard.py
```

Open the **Historical Validation Lab — Monster Q3 2026** section at the bottom of the existing dashboard. Select a preset scenario or adjust the six independent sliders, then inspect volume and retail-spend indices. Export a scenario JSON or the multi-hypothesis CSV. You may also run:

```powershell
.\.venv\Scripts\monster-backtest.exe --preset "Disliked flavor / weaker appeal"
.\.venv\Scripts\monster-backtest.exe --price-change 10 --budget-change -15 --flavor-appeal -20
```

If you do not have the generated panel, first run ` .\.venv\Scripts\energy-market.exe generate --n 600 --seed 42`.

## Financial dataset and citations

`data/monster_q3_2026_reported.json` records published figures; its URLs link to the contemporaneous primary sources.

* Monster Beverage, [Q3 2026 earnings release, November 5, 2026](https://www.globenewswire.com/news-release/2026/11/05/3397113/10193/en/monster-beverage-reports-2026-third-quarter-financial-results.html)
* Monster Beverage, [Q3 2026 SEC Form 10-Q](https://www.sec.gov/Archives/edgar/data/865752/000110465926123503/mnst-20260930x10q.htm)

Gross company metrics do not uniquely identify a causal effect. **Do not claim** a price increase, disliked flavor, or marketing caused quarterly growth without external evidence.

## Research limitations

1. The company reported **+16.7% consolidated net sales** and **about +18.0% energy case-equivalent volume** from Q3 2025 to Q3 2026, but the panel represents fictional US college students with invented population weights.
2. The company's average **net sales per case fell from $8.35 to $8.30**. This manufacturer metric is **not** the consumer-facing price used in a scenario.
3. The simulator's "+/-" volume response is a rule-based **behavioral assumption** rather than a measured elasticity; its retail spend index is not Monster's reported sales.
4. A directional match is **not** predictive validation. The difference in percentages is displayed only as a non-comparable diagnostic and is not an RMSE or error estimate.
5. No data from Monster's Q3 2026 financial results were used to fit coefficients. For credible validation, obtain consumer price histories, actual sales-volume observations by channel and region, isolate mix/FX/distribution effects, and evaluate holdout periods without post hoc tuning.
6. Reaction Lab remains an **optional, separate LLM experiment**; the historical scenario engine does not make API calls and does not pretend the LLM outputs have been calibrated or fed into the business-wide revenue series.

## Files

* `src/socsci_agents/historical_validation.py`: sourced benchmark calculations and scenario sweeps
* `src/socsci_agents/historical_cli.py`: terminal runner
* `data/monster_q3_2026_reported.json`: sourced benchmark
* `energy_dashboard.py`: new historical section appended after existing simulation and Reaction Lab
* `tests/test_historical_validation.py`: tests
