# Teammates’ Reaction Lab (preserved original code)

This is the **unchanged** `reaction_lab_updated.py` (both submitted copies were byte-identical), renamed to `simulate.py`. It has two separate modes:

- **Voltage panel**: synthetic personas respond to an energy-drink price increase using cans/choice response formats; optionally Anthropic API.
- **Interview mode**: prompts an LLM with a specific structured interview profile and a held-out scenario.

Without API credentials, the first mode offers fake response generation (`--dry-run`), and the second only previews inputs (`--dry-run`). Neither is a validated market forecast. The team's placeholder `STATED_TO_ACTUAL=0.45`, `CHOICE_VOLUME`, and segment shares remain unchanged.

Run from the project root:

```powershell
python reaction_lab/simulate.py --dry-run --n 12 --runs 1
python reaction_lab/simulate.py --persona-mode --persona-dir personas --dry-run
```

For actual LLM runs, `pip install -e ".[ui,test,llm]"` then set `ANTHROPIC_API_KEY` and select a model your account can access:

```powershell
python reaction_lab/simulate.py --n 8 --runs 1 --model YOUR_MODEL_ID
python reaction_lab/simulate.py --persona-mode --persona-dir personas --scenario "Your preferred drink rises in price by 15%; what do you buy?" --model YOUR_MODEL_ID
```

API calls can incur costs. Do not place API keys in source control. See main `INTEGRATION_README.md`.
