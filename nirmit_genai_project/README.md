# SocSci210 Generative Survey Agents

An **independent research prototype** that combines a task-aware SocSci210 survey-response classifier with an inspectable agent inspired by Park et al.'s memory / retrieval / reflection / planning architecture.

**Not a reproduction of the paper's 25-agent town, not a validated simulation of real humans, and not a reproduction of requirements in the inaccessible Google Doc.** The bundled sample is **synthetic** and is not from SocSci210. The actual dataset is downloaded by the explicit command below.

## Research sources

- Dataset: https://huggingface.co/datasets/socratesft/SocSci210
- Paper: https://arxiv.org/abs/2304.03442
- Additional project requirements supplied by user (not accessible during authoring): https://docs.google.com/document/d/1pYyGSLVKmk4Iu3yC7SnNvuIV9c52kfaBOya396I2EhA/edit

## Setup

Python 3.10+ recommended. Run these commands **from the project directory**:

```bash
python -m venv .venv
source .venv/bin/activate                # Windows: .venv\Scripts\activate
python -m pip install -e '.[ui,test]'
```

## Start immediately with bundled synthetic demonstration data

```bash
socsci inspect --data data/demo_synthetic.jsonl
socsci train --data data/demo_synthetic.jsonl
socsci predict --row data/example_input.json
socsci agent --row data/example_input.json
streamlit run app.py
pytest -q
```

The demo dataset has 360 **synthetically created** survey observations across two tasks. Its scores are only useful as a software smoke test.

## Fetch and train on the actual SocSci210 dataset

An internet connection is required on **your machine** for this step. The real source contains millions of records and is deliberately **not bundled into the ZIP**. For a smaller initial experiment:

```bash
socsci download --max-rows 10000 --output data/real_sample.jsonl
socsci inspect --data data/real_sample.jsonl
socsci train --data data/real_sample.jsonl --model artifacts/real_models.joblib --report artifacts/real_metrics.json --min-rows 20
```

To download the full dataset change `--max-rows` to an appropriately high number (e.g. `3000000`); have sufficient local disk, RAM, and time. `download` streams rows rather than loading them all simultaneously, but `train` currently loads grouped rows into RAM. For full-scale training use a higher-memory machine or extend the code to train partitions incrementally.

**Sampling caveat:** `--max-rows` takes the first N rows in the dataset stream (not a statistically random sample). Real results may be skewed by dataset order. This prototype should not be used to make demographic or policy claims without proper study design, representative sampling, and bias audits.

## Architecture and behavior

- `src/socsci_agents/data.py`: streaming Hugging Face download, schema normalization, JSONL handling, deterministic participant-within-study train/validation assignment, inspection.
- `src/socsci_agents/model.py`: per-study-and-task multinomial response classifier based on demographic attributes, condition, and TF-IDF stimulus/prompt text; majority-class benchmark; holdout accuracy and macro-F1; prediction from a saved model.
- `src/socsci_agents/agent.py`: observation memory, retrieval by relevance/recency/importance, evidence-only periodic reflections, transparent plan generation and predicted-action recording.
- `src/socsci_agents/cli.py`: `download`, `inspect`, `train`, `predict`, `agent` commands.
- `app.py`: optional interactive Streamlit demo.
- `data/demo_synthetic.jsonl`: generated toy dataset (no actual survey respondents).
- `data/example_input.json`: example prediction payload.
- `tests/test_core.py`: smoke tests for split consistency, agent reflection and model training.
- `configs/default.json`: documented reference settings (not yet wired to override CLI defaults).

## Design details and limitations

Each study/task can have a different response scale. The implementation therefore fits **separate models per `study_id` + `task_num`** and excludes groups with too few rows or too many distinct response labels. Validation uses a stable participant-level split **within each study**. This reduces leakage of the same participant across conditions/tasks; it does not avoid all stimulus- or study-level leakage. The response field is modeled as a categorical label, not automatically interpreted as numeric or ordinal. All reported scores are from held-out rows within the eligible group. Group-average scores are unweighted; check individual groups and their baseline before concluding performance.

The lightweight agent **does not generate human-like natural language with an LLM**. Reflection is a compact evidence-preserving summary; planning is a fixed sequence; the agent calls the trained classifier to produce a survey response. This keeps the demo free to run and inspect but falls short of the paper's LLM-powered reflection, recursive planning, interactive world, and emergent multiagent social behaviors. Replacing these with an LLM/embedding implementation and adding longitudinal evaluations would be necessary for a fuller reproduction.

Some demographic fields can be sensitive. Run bias/privacy reviews and comply with dataset licensing, consent, local rules, and any relevant institutional research requirements. Avoid portraying generated survey responses as real human opinions, and do not treat them as individual psychological predictions.

## Troubleshooting

- `ModuleNotFoundError`: run `pip install -e '.[ui,test]'` from the project root.
- `No trained model for ...`: your input `study_id` and `task_num` must match a group trained in the model. Try `data/example_input.json` with the demo model.
- `evaluated_groups: 0`: the data subset has insufficient observations or unlearnable response types. Increase the number of rows or reduce `--min-rows`.
- Remote download fails: verify the Hugging Face dataset is reachable on your machine; authentication/network restrictions can apply.
- Do not load untrusted `.joblib` files; pickle-based deserialization may execute code.

## Example input schema

```json
{
  "sample_id": 0,
  "participant": 0,
  "study_id": "DEMO_SYNTHETIC",
  "task_num": 0,
  "condition_num": 0,
  "demographic": {"age": 20, "gender": "Female", "ideology": "moderate"},
  "stimuli": "A city proposes adding a new public park.",
  "prompt": "How strongly do you support the park? Select 0, 1 or 2.",
  "response": 0,
  "reasoning": ""
}
```

## New GenAI research integration

See [GENAI_RESEARCH_README.md](GENAI_RESEARCH_README.md) for survey-to-agent conversion, optional Anthropic LLM simulations, temporal decision memory, an offline baseline, held-out statistical evaluation and the **Generative AI Consumer Research Lab** dashboard section. This adds research functionality without replacing the original multi-brand, historical, or teammates' Reaction Lab modules. Offline demo results are synthetic and cannot establish real predictive performance.
