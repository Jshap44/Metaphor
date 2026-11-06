#!/usr/bin/env python3
"""
Reaction Lab: persona simulation prototype
------------------------------------------
Tests whether LLM "personas" give sensible, varied reactions to a consumer event
(here: a price increase on a fictional energy drink called "Voltage").

This is a TEST OF THE METHOD, not a forecasting tool:
  * Personas come from placeholder trait distributions, not real survey data.
  * STATED_TO_ACTUAL (below) is a placeholder, not fitted to real outcomes.
  * The ranges show variation across simulated personas and runs. They are NOT
    a measure of how wrong the model could be in the real world.

Usage (see SETUP.md for the full walkthrough):
  python simulate.py --dry-run          # no API key needed; fake answers, tests the pipeline
  python simulate.py --n 10 --runs 1    # small, cheap real test
  python simulate.py                    # default: 50 personas x 3 runs
"""

import argparse
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Settings you may want to change
# ----------------------------------------------------------------------------
MODEL = "claude-haiku-5-5"   # a small, inexpensive model. Change if your account needs another.
N_PERSONAS = 50              # personas in the panel
RUNS_PER_PERSONA = 3         # times each persona answers (gives a spread of answers)
MAX_CALLS = 400              # hard cap on API calls, so a typo can't run up a bill
MAX_WORKERS = 1              # temporarily sequential for debugging
BOOTSTRAP_DRAWS = 2000       # resamples used to build the ranges

# Placeholder: people say they'll cut back more than they actually do. This factor
# converts the stated change into an estimated real change. Replace it with a value
# fitted on past events once you have real outcome data.
STATED_TO_ACTUAL = 0.45

BRAND = "Voltage"            # fictional brand, so results aren't contaminated by what the
BASE_PRICE = 3.19            # model already "knows" about real companies

# Share of the target customer base each segment represents (placeholder values).
SEGMENT_SHARES = {
    "Loyal regulars": 0.34,
    "Value-seekers": 0.28,
    "Occasional buyers": 0.24,
    "Recent switchers": 0.14,
}

TRAIT_KEYS = [
    "age", "living", "budget", "cans_per_week", "price_sensitivity",
    "brand_loyalty", "health_concern", "channel", "coffee",
]


# ----------------------------------------------------------------------------
# Personas
# ----------------------------------------------------------------------------
def pick(rng, options, probs):
    return options[rng.choice(len(options), p=probs)]


def make_persona(segment, rng):
    """Draw one persona's traits from placeholder distributions for its segment."""
    age = int(pick(rng, [18, 19, 20, 21, 22, 23, 24], [.12, .17, .20, .20, .14, .10, .07]))
    living = pick(rng, ["a dorm", "an off-campus apartment with roommates",
                        "home with family, commuting to campus"], [.40, .45, .15])
    channel = pick(rng, ["a convenience store", "a campus store", "a grocery store",
                         "a gas station"], [.35, .25, .25, .15])
    coffee = bool(rng.random() < 0.55)
    health = pick(rng, ["low", "moderate", "high"], [.35, .40, .25])

    if segment == "Loyal regulars":
        cans = pick(rng, [3, 4, 5, 7], [.30, .30, .25, .15])
        loyalty = "high"
        price = pick(rng, ["low", "moderate", "high"], [.50, .40, .10])
        relation = f"{BRAND} is your usual energy drink, and you have bought it for over a year."
        budget = int(np.clip(rng.normal(28, 9), 10, 60))
    elif segment == "Value-seekers":
        cans = pick(rng, [1, 2, 3, 4], [.25, .35, .25, .15])
        loyalty = pick(rng, ["low", "moderate"], [.60, .40])
        price = pick(rng, ["moderate", "high"], [.20, .80])
        relation = (f"You rotate between several energy drink brands, including {BRAND}, "
                    "and usually buy whichever is on sale.")
        budget = int(np.clip(rng.normal(14, 5), 5, 30))
    elif segment == "Occasional buyers":
        cans = pick(rng, [0.5, 1, 2], [.35, .45, .20])
        loyalty = pick(rng, ["low", "moderate"], [.50, .50])
        price = pick(rng, ["low", "moderate", "high"], [.25, .45, .30])
        relation = (f"You buy {BRAND} now and then, mostly when you need to stay up "
                    "to study or are tired.")
        budget = int(np.clip(rng.normal(18, 7), 5, 40))
    else:  # Recent switchers
        cans = pick(rng, [1, 2, 3, 4], [.20, .35, .30, .15])
        loyalty = "low"
        price = pick(rng, ["moderate", "high"], [.45, .55])
        relation = (f"You started buying {BRAND} in the last three months, "
                    "after switching from another brand.")
        budget = int(np.clip(rng.normal(17, 6), 5, 35))

    return {
        "segment": segment, "age": age, "living": living, "budget": budget,
        "cans_per_week": cans, "price_sensitivity": price, "brand_loyalty": loyalty,
        "health_concern": health, "channel": channel, "coffee": coffee,
        "relation": relation,
    }


def build_panel(n, rng):
    """Stratified panel: each segment gets a number of personas matching its share."""
    counts = {seg: max(1, round(n * share)) for seg, share in SEGMENT_SHARES.items()}
    panel, pid = [], 0
    for seg, count in counts.items():
        for _ in range(count):
            p = make_persona(seg, rng)
            p["persona_id"] = pid
            pid += 1
            panel.append(p)
    return panel


def cans_sentence(c):
    if c < 1:
        return "You drink an energy drink about once every two weeks."
    n = int(c) if float(c).is_integer() else c
    return f"You drink about {n} energy drink{'s' if n != 1 else ''} per week in total."


def persona_card(p):
    coffee = "You also drink coffee regularly." if p["coffee"] else "You do not usually drink coffee."
    return (
        f"You are a {p['age']}-year-old college student living in {p['living']}. "
        f"You spend about ${p['budget']} a week on drinks of all kinds. "
        f"{cans_sentence(p['cans_per_week'])} {p['relation']} "
        f"You usually buy drinks at {p['channel']}. {coffee} "
        f"Price sensitivity: {p['price_sensitivity']}. Brand loyalty: {p['brand_loyalty']}. "
        f"Concern about health and caffeine: {p['health_concern']}."
    )


# ----------------------------------------------------------------------------
# The event and the prompt
# ----------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are role-playing one specific consumer in a market research simulation. "
    "Answer as that person honestly would, not as an ideal or perfectly rational shopper. "
    "Real people are often creatures of habit, sometimes do not notice or care about "
    "small changes, and sometimes react strongly. Do not be agreeable for its own sake. "
    "Reply with JSON only."
)


def event_text(pct):
    new_price = round(BASE_PRICE * (1 + pct / 100), 2)
    return (
        f"{BRAND} has announced a {pct:g}% price increase on its 16 oz cans, from "
        f"${BASE_PRICE:.2f} to ${new_price:.2f}, effective next week. Other brands have not "
        f"changed their prices, there is no coupon or promotion, and {BRAND} stays in the "
        f"same place on the shelf. You will see the new price on the shelf tag the next "
        f"time you shop."
    )


def build_prompt(p, pct):
    return (
        persona_card(p) + "\n\n"
        "News: " + event_text(pct) + "\n\n"
        "Think about what you personally would do over the next month, then reply with "
        "JSON only, in exactly this format:\n"
        "{\n"
        f'  "voltage_cans_per_week_before": <number: cans of {BRAND} you buy in a typical '
        "week at the current price, 0 if none>,\n"
        f'  "voltage_cans_per_week_after": <number: cans of {BRAND} you expect to buy per '
        "week once the new price is in effect>,\n"
        '  "chance_you_switch_to_another_brand_pct": <integer 0-100>,\n'
        '  "reason": "<one short sentence>"\n'
        "}"
    )


def parse_answer(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON found in reply")
    d = json.loads(m.group(0))
    before = float(d["voltage_cans_per_week_before"])
    after = float(d["voltage_cans_per_week_after"])
    switch = float(d["chance_you_switch_to_another_brand_pct"])
    if not (0 <= before <= 30 and 0 <= after <= 30 and 0 <= switch <= 100):
        raise ValueError("answer outside sensible range")
    return before, after, switch, str(d.get("reason", ""))[:300]


# ----------------------------------------------------------------------------
# Dry-run stand-in for the model (fake numbers, only tests the pipeline)
# ----------------------------------------------------------------------------
def fake_response(p, pct, seed, run, attempt):
    rng = np.random.default_rng([seed, p["persona_id"], run, attempt])
    voltage_share = {"Loyal regulars": 0.85, "Value-seekers": 0.40,
                     "Occasional buyers": 0.20, "Recent switchers": 0.50}[p["segment"]]
    before = p["cans_per_week"] * voltage_share * rng.uniform(0.8, 1.2)
    sens = ({"low": 0.5, "moderate": 1.0, "high": 1.6}[p["price_sensitivity"]]
            * {"high": 0.6, "moderate": 1.0, "low": 1.4}[p["brand_loyalty"]])
    drop = float(np.clip(sens * pct * 0.012 * rng.uniform(0.6, 1.4), 0, 0.9))
    switch = int(np.clip(drop * 150 + rng.normal(0, 6), 0, 100))
    return json.dumps({
        "voltage_cans_per_week_before": round(before, 2),
        "voltage_cans_per_week_after": round(before * (1 - drop), 2),
        "chance_you_switch_to_another_brand_pct": switch,
        "reason": "[dry run] synthetic answer, not from a model",
    })


# ----------------------------------------------------------------------------
# Running the simulation
# ----------------------------------------------------------------------------
class FatalAPIError(Exception):
    pass


class Runner:
    def __init__(self, args, client, anthropic_module):
        self.args = args
        self.client = client
        self.anthropic = anthropic_module
        self.lock = threading.Lock()
        self.calls = 0
        self.use_temperature = True

    def take_call(self):
        if self.args.dry_run:
            return True
        with self.lock:
            if self.calls >= MAX_CALLS:
                return False
            self.calls += 1
            return True

    def ask_model(self, p):
        kwargs = dict(
            model=self.args.model, max_tokens=300, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_prompt(p, self.args.price_increase)}],
        )
        if self.use_temperature:
            kwargs["temperature"] = 1.0   # keeps answers varied between runs
        try:
            resp = self.client.messages.create(**kwargs)
        except self.anthropic.BadRequestError as e:
            # Some models don't accept a temperature setting; retry without it.
            if self.use_temperature and "temperature" in str(e).lower():
                self.use_temperature = False
                kwargs.pop("temperature", None)
                resp = self.client.messages.create(**kwargs)
            else:
                raise
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def run_task(self, p, run):
        base = {"persona_id": p["persona_id"], "segment": p["segment"], "run": run,
                **{k: p[k] for k in TRAIT_KEYS}}
        last_err = ""
        for attempt in range(2):
            if not self.take_call():
                return {**base, "ok": False, "error": "call cap reached"}
            try:
                if self.args.dry_run:
                    text = fake_response(p, self.args.price_increase, self.args.seed, run, attempt)
                else:
                    text = self.ask_model(p)
                before, after, switch, reason = parse_answer(text)
                return {**base, "ok": True, "before": before, "after": after,
                        "switch_pct": switch, "reason": reason}
            except Exception as e:  # noqa: BLE001
                if self.anthropic and isinstance(e, (self.anthropic.AuthenticationError,
                                                     self.anthropic.PermissionDeniedError,
                                                     self.anthropic.NotFoundError)):
                    raise FatalAPIError(str(e)) from e
                last_err = f"{type(e).__name__}: {e}"[:200]
                print(f"Persona {p['persona_id']} attempt {attempt + 1} failed: {type(e).__name__}: {e}", flush=True)
        return {**base, "ok": False, "error": last_err}


# ----------------------------------------------------------------------------
# Aggregation
# ----------------------------------------------------------------------------
def summarize(df, rng):
    ok = df[df["ok"]]
    per_p = (ok.groupby(["persona_id", "segment"], as_index=False)
               .agg(before=("before", "mean"), after=("after", "mean"),
                    switch=("switch_pct", "mean")))

    stats = {}
    for seg, share in SEGMENT_SHARES.items():
        d = per_p[per_p["segment"] == seg]
        if d.empty:
            continue
        b, a = d["before"].to_numpy(), d["after"].to_numpy()
        idx = rng.integers(0, len(d), size=(BOOTSTRAP_DRAWS, len(d)))
        stats[seg] = {"share": share, "n": len(d), "b": b.mean(), "a": a.mean(),
                      "switch": d["switch"].mean(), "bb": b[idx].mean(1), "ab": a[idx].mean(1)}

    rows = []

    def add(label, share, n, point, boot, switch):
        lo, hi = np.percentile(boot, [10, 90]) * 100
        point *= 100
        rows.append({
            "segment": label, "share_of_base_pct": share, "personas": n,
            "stated_change_pct": point, "stated_low": lo, "stated_high": hi,
            "est_volume_change_pct": point * STATED_TO_ACTUAL,
            "est_low": lo * STATED_TO_ACTUAL, "est_high": hi * STATED_TO_ACTUAL,
            "avg_switch_chance_pct": switch,
        })

    for seg, s in stats.items():
        point = s["a"] / s["b"] - 1 if s["b"] > 0 else np.nan
        boot = s["ab"] / np.maximum(s["bb"], 1e-9) - 1
        add(seg, s["share"] * 100, s["n"], point, boot, s["switch"])

    if stats:
        A = sum(s["share"] * s["a"] for s in stats.values())
        B = sum(s["share"] * s["b"] for s in stats.values())
        boot_all = (sum(s["share"] * s["ab"] for s in stats.values())
                    / np.maximum(sum(s["share"] * s["bb"] for s in stats.values()), 1e-9) - 1)
        total_share = sum(s["share"] for s in stats.values())
        switch_all = sum(s["share"] * s["switch"] for s in stats.values()) / total_share
        add("All segments (weighted)", total_share * 100,
            sum(s["n"] for s in stats.values()), A / B - 1 if B > 0 else np.nan,
            boot_all, switch_all)
    return pd.DataFrame(rows)


def print_summary(summary, args):
    show = pd.DataFrame({
        "Segment": summary["segment"],
        "Share": summary["share_of_base_pct"].map("{:.0f}%".format),
        "Personas": summary["personas"],
        "Stated change": summary["stated_change_pct"].map("{:+.1f}%".format),
        "Range (10th-90th)": [f"{lo:+.1f}% to {hi:+.1f}%"
                              for lo, hi in zip(summary["stated_low"], summary["stated_high"])],
        "Est. real volume": summary["est_volume_change_pct"].map("{:+.1f}%".format),
        "Switch chance": summary["avg_switch_chance_pct"].map("{:.0f}%".format),
    })
    print()
    if args.dry_run:
        print("*** DRY RUN: these numbers are synthetic and say nothing about consumers. ***")
    print(f"Event: {event_text(args.price_increase)}\n")
    print(show.to_string(index=False))
    print(f"\nEst. real volume = stated change x {STATED_TO_ACTUAL} (a placeholder, not fitted).")
    print("Ranges reflect variation across simulated personas and runs, not real-world error.")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Persona simulation prototype")
    ap.add_argument("--n", type=int, default=N_PERSONAS, help="number of personas")
    ap.add_argument("--runs", type=int, default=RUNS_PER_PERSONA, help="runs per persona")
    ap.add_argument("--price-increase", type=float, default=8.0, help="price increase, in percent")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true", help="use fake answers, no API calls")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = ap.parse_args()

    if args.n < 4:
        sys.exit("Use at least 4 personas (one per segment).")

    rng = np.random.default_rng(args.seed)
    panel = build_panel(args.n, rng)
    tasks = [(p, r) for p in panel for r in range(args.runs)]
    planned = len(tasks)

    client, anthropic_module = None, None
    if not args.dry_run:
        if planned > MAX_CALLS:
            sys.exit(f"That would make {planned} calls, above the cap of {MAX_CALLS}. "
                     "Lower --n or --runs, or raise MAX_CALLS at the top of the script.")
        try:
            import anthropic as anthropic_module  # noqa: F811
        except ImportError:
            sys.exit("The anthropic package is missing. Run: pip install anthropic")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("No ANTHROPIC_API_KEY found. See SETUP.md step 4, or try --dry-run first.")
        client = anthropic_module.Anthropic(max_retries=5)
        if not args.yes:
            ans = input(f"About to make up to {planned} calls to {args.model}. Continue? [y/N] ")
            if ans.strip().lower() != "y":
                sys.exit("Cancelled.")

    print(f"Panel: {len(panel)} personas x {args.runs} runs = {planned} calls "
          f"({'dry run' if args.dry_run else args.model})")

    runner = Runner(args, client, anthropic_module)
    results, done = [], 0
    ex = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = [ex.submit(runner.run_task, p, r) for p, r in tasks]
    try:
        for f in as_completed(futures):
            results.append(f.result())
            done += 1
            if done % 10 == 0 or done == planned:
                print(f"  {done}/{planned} done", flush=True)
    except FatalAPIError as e:
        ex.shutdown(wait=False, cancel_futures=True)
        sys.exit(f"\nStopped: the API rejected the request ({e}).\n"
                 "Check your API key, and that the model name at the top of the script is "
                 "available to your account.")
    ex.shutdown(wait=True)

    df = pd.DataFrame(results).sort_values(["persona_id", "run"]).reset_index(drop=True)
    failed = int((~df["ok"]).sum())
    if failed:
        print(f"\n{failed} of {planned} calls failed and were left out. "
              "See the 'error' column in the results file.")
    if df["ok"].sum() == 0:
        os.makedirs("output", exist_ok=True)
        error_path = f"output/failed_results_{datetime.now():%Y%m%d_%H%M%S}.csv"
        df.to_csv(error_path, index=False)
        sys.exit(f"No usable answers came back. Errors saved to {error_path}")

    summary = summarize(df, rng)
    print_summary(summary, args)

    if not args.dry_run:
        print("\nSample reasons (read these for realism, not just the numbers):")
        for seg in SEGMENT_SHARES:
            sub = df[(df["segment"] == seg) & df["ok"]]
            if not sub.empty:
                print(f'  {seg}: "{sub.iloc[0]["reason"]}"')

    os.makedirs("output", exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = "dryrun_" if args.dry_run else ""
    suffix = f"n{args.n}_seed{args.seed}_{stamp}"
    results_path = f"output/{tag}results_{suffix}.csv"
    summary_path = f"output/{tag}summary_{suffix}.csv"
    df.to_csv(results_path, index=False)
    summary.round(2).to_csv(summary_path, index=False)
    print(f"\nSaved:\n  {results_path}\n  {summary_path}")


if __name__ == "__main__":
    main()
