# Energy drink consumer agents — investor-side scenario prototype

This implementation follows the uploaded **Investor Side Agent Based Market Prediction** proposal. Its selected first market is **energy-drink consumption among college students**. The proposal also discusses a Coors beer-company example; that is an illustrative method, not the project's chosen prototype market.

## Quick start

```bash
python -m pip install -e '.[ui,test]'
energy-market generate --n 600 --seed 42
energy-market simulate --price-change 25 --budget-change -15
energy-market sensitivity
streamlit run energy_dashboard.py
pytest -q
```

No API key is needed. `data/energy_personas_synthetic.csv` is already generated and `artifacts/energy_simulation.json` is included.

## Approach

1. **Demographic panel:** generate clearly synthetic college-student consumer personas; configure budget, frequency, favorite/alternative brand, price sensitivity, loyalty, stock availability, health concern, and convenience.
2. **Qualitative interview:** `data/interview_example.json` transcribes important preferences from one interview in the project document. No claim that this one respondent is representative. Its per-serving cost is marked as a hypothetical value because the interview reports container-level prices, not a precise per-serving cost.
3. **Scenario injection:** model 25% brand price increase, discretionary-spending squeeze, emerging health concern, stockouts, and competitor promotions. View example cases in `configs/energy_scenarios.json`.
4. **Repeated behavior:** simulate every synthetic consumer for 1–36 months under a documented heuristic switching/cutback model.
5. **Investor-side aggregates:** report unit volume, price-weighted revenue, hypothetical gross profit, brand switching, and brand allocation; run a grid of sensitivity cases.
6. **Dashboard:** `energy_dashboard.py` has sliders, comparative KPI outputs, charts and downloadable JSON.

## Project architecture and source mapping

- Uploaded `GenAI Final (1).docx`, page 1: college students + energy drinks; use own/public consumer data; combine dashboard; simulate events.
- Pages 2–3: persona panels → macroeconomic shock → behavior → investment signals. These become simulation stages.
- Pages 4–8: survey themes and one detailed energy-consumer interview, incorporated as an illustrative separate record and as candidate future features.
- Research article `https://arxiv.org/pdf/2304.03442`: generative-agent memory, reflection, and planning are separately prototyped in `src/socsci_agents/agent.py`, not falsely attributed to the heuristic market simulator.
- SocSci210 `https://huggingface.co/datasets/socratesft/SocSci210`: generic survey training examples are available in the original `socsci` data workflow. This dataset is **not automatically energy-drink purchasing labels** and does not establish any causal price effect.

## Data file/schema

- `data/energy_personas_synthetic.csv`: simulated participant-level configuration; explicitly fabricated.
- `data/interview_example.json`: project-document-derived ONE respondent with an illustrative added price-per-serving assumption, clearly stated.
- `data/survey_template.csv`: structured intake sheet for additional real, consented respondents. It contains headers only.
- `artifacts/energy_simulation.json`, `artifacts/sensitivity_grid.json`: deterministic hypothetical results.

To use real survey data, collect consent and use the CSV schema; however, **do not assume the current heuristic is trained**. Next phase: obtain multiple respondents' baseline purchases and event-response labels, stratify train/test by respondent, estimate model parameters from observed choices, calibrate predicted probabilities and evaluate against held-out data. Weight the panel to a known population if market sizing is intended.

## Limitations

- All market aggregates are for the synthetic panel, **not actual market or company sales**.
- Price response coefficients, panel budget shares and brand shares are assumptions, not fitted estimates.
- Scenarios are counterfactual demonstrations, not causal estimates or validated stock-price predictions.
- Unit costs are illustrative; gross profit is *not* company financial profit, and this project does not recommend investments.
- The single interview includes ambiguous language in the question about a 50% decrease in price; no definitive behavior was inferred from that ambiguous answer.
- Real-world use requires consent, representativeness checks, calibrated measurements, quantitative validation, and financial reporting reconciliation.

## Existing general SocSci work

The original survey-response predictor and simple memory/reflection/planning agent are retained as a separate experimental track: `socsci --help`, `streamlit run app.py`. They should not be confused with the project-specific energy market application.
