# Generative AI Consumer Research — integrated extension

This extends (does not replace) the energy-drink market simulator, teammates' Reaction Lab, historical Monster/Celsius/Alani tests, and multi-brand dashboard.

## How to install and start (Windows PowerShell)

Run from the extracted `socsci_agents` folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[ui,test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run energy_dashboard.py
```

Scroll to **Generative AI Consumer Research Lab**. Choose synthetic demo, the two interview profiles, or upload your group's Google Forms export CSV. The dashboard includes `Agent purchasing experiments`, `Held-out evaluation`, and `Research interpretation` tabs.

## Command-line examples

```powershell
# Works without any API key; offline outputs are assumptions, not AI output
.\.venv\Scripts\python.exe -m socsci_agents.genai_cli --demo --experiment episodes --memory
.\.venv\Scripts\python.exe -m socsci_agents.genai_cli --interviews --experiment episodes --price-change 25
.\.venv\Scripts\python.exe -m socsci_agents.genai_cli --demo --experiment evaluate
.\.venv\Scripts\python.exe -m socsci_agents.genai_cli --demo --experiment compare

# Once Google Forms responses are exported, import into structured JSONL and simulate
.\.venv\Scripts\python.exe -m socsci_agents.genai_cli --survey-csv responses.csv --experiment episodes

# Live LLM; costs money, uses Anthropic API (keys should NEVER be committed)
.\.venv\Scripts\python.exe -m pip install -e ".[ui,test,llm]"
$env:ANTHROPIC_API_KEY = "your-api-key"
$env:ANTHROPIC_MODEL = "your-supported-model-id"
.\.venv\Scripts\python.exe -m socsci_agents.genai_cli --interviews --mode llm --max-consumers 2 --episodes 2 --memory --max-calls 4
```

Use the provider's current model ID, and do not disclose keys or save them in source files.

## What is actually implemented

- Google Forms CSV importer maps the 15 supplied survey questions into a structured JSONL format, preserving raw data and nulls for unknown values. Optional new multiple-choice price reaction question becomes a stronger evaluation label.
- Converts your teammates' `consumer_001.json` / `consumer_002.json` into rich, qualitative LLM contexts. They are not assumed to represent a demographic.
- Structured (same/less/switch/quit) purchasing decisions and numeric quantities, with response validation.
- Direct optional LLM decisions using the Anthropic API or a clearly **non-LLM offline** heuristic to debug the workflow.
- Per-consumer memory of previous simulated shopping episodes; toggle on/off to compare with memory-free decisions.
- Consumer-level evaluation split with a fitted scikit-learn logistic regression baseline and an offline rule-based comparator. The `compare` CLI can also evaluate the live LLM on the exact same held-out consumers, subject to call caps.
- Streamlit agent choices, consumer profiles, scenario sliders, metric tables and CSV exports.
- Built-in synthetic fixture to verify the workflow without real response data.

## Research caveats

- The supplied survey *questions* are not survey *responses*. No observed purchases or trained survey-calibrated model are claimed until you import responses. The bundled demo rows are deliberately fabricated.
- The 15 questions are largely free text. Parsing free-text 25%-price reactions is approximate. Free-text inferred labels are excluded from statistical training by default. For stronger evaluation, add a **structured multiple-choice** question with same/less/switch/quit options and collect the actual post-price quantities. The importer recognizes these columns.
- Your two existing interviews are qualitative case studies with no blind held-out test labels. They cannot yield a legitimate accuracy score by themselves.
- `llm` mode **really calls** Anthropic; `offline` mode NEVER does. No fallback from LLM errors to pretend responses. `max_calls` caps the number of live agent calls.
- Prior simulated memory is not real-life memory and cannot establish predictive benefits without controlled evaluation.
- Statistical baseline on held-out hypothetical choices is not observed-purchase validation; synthetic-demo metrics do not support research claims. With real data, assess sample size, respondent leakage, class imbalance, and representative sampling.
- Historical corporate brand revenue and the college-student model are not directly comparable. Causal claims require controlled data and careful validation.

## Next genuine empirical milestones

1. Collect consented survey responses (including a *held-out* scenario question and numeric after-price quantity), strip identifying information before model calls.
2. Reserve test consumers **before** tuning prompts and hyperparameters, compare statistical baseline / heuristic / zero-memory LLM / memory LLM using the same test cases.
3. Report choice accuracy, balanced accuracy, quantity MAE where available, repeated-run reliability, costs, and errors. Don't force results to match earnings reports.
4. If permitted, collect actual subsequent purchase data for stronger out-of-sample validation.

## Student-facing dashboard presentation (updated)

The Streamlit apps show readable consumer summaries, experiment metrics, behavior charts,
confusion matrices, and tables. They no longer render raw JSON or Python snippets
as visible results. Full structured profiles and experiment files are retained for
export and reproducibility. This is a presentation-only change; no behavioral
coefficients, agent prompts, earnings benchmarks, or simulation logic were altered.

Launch from the `socsci_agents` project folder:

```powershell
..\.venv\Scripts\python.exe -m streamlit run energy_dashboard.py
```

If your virtual environment is located inside this folder instead, replace
`..\.venv` with `.\.venv`.
