"""CLI for the Monster Q3 historical hypothesis exercise; no API key required."""
import argparse
import json
from .energy_market import load_personas
from .historical_validation import (
    load_report, reported_changes, simulate_monster_panel, compare_to_report,
    hypothesis_sweep, write_sweep_csv, SCENARIOS,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--personas', default='data/energy_personas_synthetic.csv')
    parser.add_argument('--report', default='data/monster_q3_2026_reported.json')
    parser.add_argument('--preset', choices=SCENARIOS, default='Monster price +10%')
    parser.add_argument('--price-change', type=float, default=None)
    parser.add_argument('--budget-change', type=float, default=None)
    parser.add_argument('--flavor-appeal', type=float, default=None)
    parser.add_argument('--marketing-lift', type=float, default=None)
    parser.add_argument('--competitor-discount', type=float, default=None)
    parser.add_argument('--stockout', type=float, default=None)
    parser.add_argument('--sweep-output', default='output/monster_q3_hypotheses.csv')
    args = parser.parse_args(argv)
    personas = load_personas(args.personas)
    report = load_report(args.report)
    scenario = dict(SCENARIOS[args.preset])
    for key, val in [('price_change_pct', args.price_change),
                     ('budget_change_pct', args.budget_change),
                     ('flavor_appeal_pct', args.flavor_appeal),
                     ('marketing_lift_pct', args.marketing_lift),
                     ('competitor_discount_pct', args.competitor_discount),
                     ('stockout_pct', args.stockout)]:
        if val is not None:
            scenario[key] = val
    simulated = simulate_monster_panel(personas, scenario)
    print(json.dumps({'reported_growth': reported_changes(report), 'simulated': simulated,
                      'comparison': compare_to_report(simulated, report)}, indent=2))
    path = write_sweep_csv(hypothesis_sweep(personas, report), args.sweep_output)
    print(f'\nHypothesis comparison saved: {path}')


if __name__ == '__main__':
    main()
