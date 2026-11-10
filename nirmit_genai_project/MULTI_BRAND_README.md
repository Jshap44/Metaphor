# Multi-brand extension: Q3 2026 case studies

This extension keeps the existing Monster historical case study, teammates' Reaction Lab, interview personas, and synthetic consumer simulation. It adds a separate **Multi-Brand Scenario & Earnings Comparison** at the bottom of `energy_dashboard.py`.

## Brands

Monster, Celsius, Alani Nu, Rockstar, Red Bull, Ghost, C4, Gorilla Mind, and the synthetic `Other` category.

**Sourced Q3 2026 vs Q3 2025 comparisons:**
- Monster Beverage: 304.902 vs 258.387 **million 192-ounce case equivalents** across its company-wide energy-drink business (NOT Monster-brand-only), [SEC filing](https://www.sec.gov/Archives/edgar/data/865752/000110465926123503/mnst-20260930x10q.htm).
- CELSIUS brand: $356.8m vs $381.0m **brand revenue**, [company earnings](https://ir.celsiusholdingsinc.com/news/news-details/2026/Celsius-Holdings-Reports-Third-Quarter-2026-Financial-Results/default.aspx).
- Alani Nu: $410.1m vs $332.0m **brand revenue**, same earnings release.
- Rockstar: $80.3m Q3 2026 reported brand revenue, **no paired 2025 brand period in this project**. It is not assigned an invented growth rate.
- Red Bull, Ghost, C4, Gorilla Mind: **no documented comparable Q3 benchmark** in this project. Do not infer 0% growth.

The two distinct benchmark units must **never** be treated as equivalent or scored as an accuracy test against synthetic unit-purchase changes. The data/energy_brand_benchmarks.json file contains the sources, definitions and reporting caveats.

## Install and run (Windows PowerShell)

From `socsci_agents/`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ui,test]"
.\.venv\Scripts\python.exe -m socsci_agents.energy_cli generate --n 600 --seed 42
.\.venv\Scripts\python.exe -m streamlit run energy_dashboard.py
```

CLI examples:

```powershell
.\.venv\Scripts\python.exe -m socsci_agents.multi_brand_cli --brand Celsius --price-change 10
.\.venv\Scripts\python.exe -m socsci_agents.multi_brand_cli --brand "Alani Nu" --flavor-appeal 25
.\.venv\Scripts\python.exe -m socsci_agents.multi_brand_cli --brand all --price-change 10 --csv output/all_brands.csv
.\.venv\Scripts\python.exe -m socsci_agents.multi_brand_cli --brand Red Bull --sweep --csv output/red_bull_sweep.csv
.\.venv\Scripts\python.exe -m pytest -q
```

The original `reaction_lab/simulate.py` and interview profiles are preserved. They are not automatically used to calibrate the new brand model. The multi-brand engine reuses the transparent, **uncalibrated** scenario assumptions originally used for Monster; market shares, baseline personas, and modeled volume changes are illustrative.

## Important methodology

The same price increase applied to each brand is an **independent what-if experiment** for that brand. It is *not* a simultaneous multi-brand equilibrium. The sum of estimated brand changes should not be interpreted as total market change. Observed company revenues are affected by regions, distribution, shipments, channel mix, promotion and acquisitions, which are not measured here. The purpose is hypothesis generation and model engineering, not demonstrated historical prediction.
