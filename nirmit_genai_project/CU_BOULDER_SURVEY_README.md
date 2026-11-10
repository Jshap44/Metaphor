# CU Boulder survey integration (pilot data)

## What changed

The team's 30 survey responses are now the **default data source** in **Generative AI Consumer Research Lab** within `energy_dashboard.py`. The collected responses are stored as `data/cu_boulder_survey_responses.csv` with the timestamp and empty third-party completion-link field removed. Answers to the 15 survey questions are preserved. The original CSV remains with the team; this packaged copy does not contain timestamps.

Select **CU Boulder survey (30 responses)** to inspect a brand snapshot, conservative classifications of 25% price-increase intentions, and anonymized profiles. Agent experiments can now use these responses rather than the synthetic demo. Existing synthetic market simulator and corporate history modules remain unchanged; their synthetic behavior coefficients have **not** been calibrated to these survey responses. Live LLM mode still requires an Anthropic API key.

## Data quality and scientific cautions

- CU Boulder collection context is **team reported**. The form has no verified student-status field, so the software does not claim all respondents are enrolled or that the sample represents CU Boulder students.
- Frequency responses with no explicit units, ranges, and non-numeric answers remain missing, rather than having units guessed. Daily and weekly statements with clear units are normalized.
- Some responses mention multiple price-reaction outcomes. These remain unclassified; classifications based on free text are exploratory, not independent ground-truth labels.
- Free-text heuristic labels are **not** used in the statistical holdout calculation, avoiding spurious accuracy claims. Collect structured choice labels and numeric after-quantity answers for rigorous validation.
- Brand bars use the first matched brand in a text response, **not** market share, weighted brand volume, or audited sales.
- Do not publish identifiable raw responses without respondent consent. The package omits timestamps and unused tracking fields; original survey answers are still included for the team's research use.

## Run in PowerShell

From the `socsci_agents` folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ui,test]"
.\.venv\Scripts\python.exe -m streamlit run energy_dashboard.py
```

To validate importer and run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

To replace the current data with new survey responses, use the **Upload Google Forms CSV** option. The bundled pilot survey is unchanged until you deliberately replace its file in `data/`.
