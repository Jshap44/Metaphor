# Energy Drink Investor-Side Agent Market Prediction — merged team project

## Integrated sources

1. **Original project**: `src/socsci_agents/energy_market.py` (600-person synthetic panel), `energy_dashboard.py`, and the SocSci210 prototype.
2. **Teammates’ Reaction Lab**: `reaction_lab/simulate.py`, preserved from `reaction_lab_updated.py`. Both supplied copies were identical. It implements LLM-driven price-reaction experiments for fictional Voltage, with **cans** and **choice** formats, repeated runs, and within-panel bootstrap ranges.
3. **Teammates’ interview personas**: `personas/consumer_001.json` and `personas/consumer_002.json` retained as qualitative evidence. No fabricated numerical utility weights or market representativeness are imposed.
4. **Integration**: `src/socsci_agents/integration.py` exposes profiles and interprets Reaction Lab summary CSVs; the Streamlit dashboard includes both in separate tabs.

## Important methodological distinctions

- The **market engine** is an assumption-based synthetic simulation, not a trained forecast. Its dollars are illustrative panel amounts.
- **Voltage Reaction Lab** uses a different panel, a fictional brand and a different experimental endpoint; **do not numerically average its percentages with the market engine**. A dry run produces fake responses, not actual LLM outputs.
- **Interview mode** uses exactly two self-reported profiles (no real purchase records, no representative sampling). A dry run previews input only; live runs call the Anthropic API and require a configured API key and accessible model name.
- Ranges from repeated synthetic runs are **not real-world prediction intervals**. `STATED_TO_ACTUAL = 0.45` is the teammate's uncalibrated placeholder.
- SocSci210 is a separate social-science dataset experiment, **not energy-drink training data**.

## Windows PowerShell setup

From inside the extracted `socsci_agents` folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ui,test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\energy-market.exe generate --n 600 --seed 42
.\.venv\Scripts\energy-market.exe simulate --price-change 25 --budget-change -15
.\.venv\Scripts\python.exe reaction_lab/simulate.py --dry-run --n 12 --runs 1
.\.venv\Scripts\python.exe reaction_lab/simulate.py --persona-mode --persona-dir personas --dry-run
.\.venv\Scripts\python.exe -m streamlit run energy_dashboard.py
```

Using `python -m pytest` avoids accidentally invoking an old Anaconda `pytest.exe`. The virtual environment avoids the Windows PATH issue. The dashboard can display the output of the Reaction Lab after a dry-run CSV has been generated.

## Optional real LLM experiments (paid API)

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ui,test,llm]"
$env:ANTHROPIC_API_KEY = 'YOUR_KEY_HERE'
.\.venv\Scripts\python.exe reaction_lab/simulate.py --n 8 --runs 1 --model YOUR_ACCESSIBLE_MODEL_ID
.\.venv\Scripts\python.exe reaction_lab/simulate.py --persona-mode --persona-dir personas --model YOUR_ACCESSIBLE_MODEL_ID
```

Don't commit your key or claim these are validated forecasts. The model ID in the teammates' source code is a default setting, not verified as accessible. You can pass `--model`. Live mode requires explicit confirmation before calls; cost limits are in source.

## Project layout

- `src/socsci_agents/`: original market simulator, CLI, SocSci210 model, integration helpers
- `reaction_lab/`: preserved teammate LLM code + instructions
- `personas/`: two structured interviews
- `energy_dashboard.py`: main UI, enhanced with interview/reaction panels
- `data/`: 600 sample synthetic personas; separately the single-interview illustrative profile
- `tests/`: integration and original tests
- `artifacts/`: illustrative outputs from original simulations
- `output/`: generated when Reaction Lab runs

## Suggested next research steps

1. Collect a larger, consented survey panel and observed hold-out purchase outcomes.
2. Define shared units: cans vs pre-workout servings, purchases vs consumption, and product-specific prices.
3. Validate hypothetical responses and estimate price response coefficients against held-out observations.
4. Only then consider calibrated population weights and investment-sensitive revenue forecasts.
