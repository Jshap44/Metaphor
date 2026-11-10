"""Exploratory, explicitly UNCALIBRATED consumer-demand backtests.

Observed corporate metrics and hypothetical college-student purchasing responses are
kept separate throughout; no regression or post-hoc fitted parameters are implied.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Mapping

REPORT_PATH = Path(__file__).resolve().parents[2] / 'data' / 'monster_q3_2026_reported.json'

# Pure assumptions. They are NOT estimated from interviews, the filing or SocSci210.
ASSUMPTIONS = {
    'price_elasticity_coefficient': 1.10,
    'budget_stress_coefficient': 0.75,
    'flavor_response_coefficient': 0.40,
    'marketing_response_coefficient': 0.22,
    'competitor_promotion_coefficient': 0.60,
    'stockout_response_coefficient': 0.65,
    'competitor_switch_in_base_probability': 0.025,
    'competitor_switch_in_marketing_coefficient': 0.14,
    'competitor_switch_in_flavor_coefficient': 0.15,
}

SCENARIOS = {
    'No change (control)': {},
    'Monster price +10%': {'price_change_pct': 10},
    'Disliked flavor / weaker appeal': {'flavor_appeal_pct': -30},
    'Well-received flavor': {'flavor_appeal_pct': 30},
    'Marketing / awareness +25%': {'marketing_lift_pct': 25},
    'Student spending budgets -15%': {'budget_change_pct': -15},
    'Competitor discount 15%': {'competitor_discount_pct': 15},
    'Monster product stockout 15%': {'stockout_pct': 15},
    'Price +10%, flavor +20%, marketing +25%': {
        'price_change_pct': 10, 'flavor_appeal_pct': 20, 'marketing_lift_pct': 25,
    },
}


def load_report(path: str | Path | None = None) -> dict:
    """Load sourced observed numbers; never fetch data automatically."""
    filepath = Path(path) if path else REPORT_PATH
    with filepath.open(encoding='utf-8') as f:
        report = json.load(f)
    required = ('sales_2026_thousand_usd', 'sales_2025_thousand_usd',
                'energy_drinks_segment_2026_thousand_usd',
                'energy_drinks_segment_2025_thousand_usd',
                'energy_case_equivalents_2026_thousand',
                'energy_case_equivalents_2025_thousand',
                'average_net_sales_per_case_2026_usd',
                'average_net_sales_per_case_2025_usd')
    if any(k not in report for k in required):
        raise ValueError('Missing one or more required reported financial metrics')
    return report


def percent_change(before: float, after: float) -> float:
    if before <= 0:
        raise ValueError('Before value must be positive')
    return 100.0 * (after / before - 1.0)


def reported_changes(report: Mapping) -> dict:
    return {
        'consolidated_sales_growth_pct': percent_change(report['sales_2025_thousand_usd'], report['sales_2026_thousand_usd']),
        'energy_segment_sales_growth_pct': percent_change(report['energy_drinks_segment_2025_thousand_usd'], report['energy_drinks_segment_2026_thousand_usd']),
        'company_case_volume_growth_pct': percent_change(report['energy_case_equivalents_2025_thousand'], report['energy_case_equivalents_2026_thousand']),
        'average_net_sales_per_case_change_pct': percent_change(report['average_net_sales_per_case_2025_usd'], report['average_net_sales_per_case_2026_usd']),
    }


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _validate_scenario(scenario: Mapping | None) -> dict:
    defaults = dict(price_change_pct=0., budget_change_pct=0., flavor_appeal_pct=0.,
                    marketing_lift_pct=0., competitor_discount_pct=0., stockout_pct=0.)
    if scenario:
        unknown = set(scenario) - set(defaults)
        if unknown:
            raise ValueError(f'Unknown historical scenario fields: {sorted(unknown)}')
        defaults.update(scenario)
    for key in defaults:
        value = float(defaults[key])
        if not math.isfinite(value):
            raise ValueError(f'{key} must be finite')
        defaults[key] = value
    for key in ('stockout_pct', 'competitor_discount_pct'):
        if not 0 <= defaults[key] <= 100:
            raise ValueError(f'{key} must be between 0 and 100')
    if defaults['price_change_pct'] <= -100 or defaults['budget_change_pct'] <= -100:
        raise ValueError('Price/budget cannot be reduced by 100% or more')
    if not -100 <= defaults['flavor_appeal_pct'] <= 100:
        raise ValueError('flavor_appeal_pct must be in [-100,100]')
    if not -100 <= defaults['marketing_lift_pct'] <= 100:
        raise ValueError('marketing_lift_pct must be in [-100,100]')
    return defaults


def simulate_monster_panel(personas: list[dict], scenario: Mapping | None = None,
                           target_brand: str = 'Monster') -> dict:
    """Estimate expected brand-purchase change in a synthetic student panel.

    Scenario-specific *hypothetical* propensities use a reference (unshocked)
    panel; the results are expectation weights, not individual purchase events.
    Revenue is a consumer-price *index*, NOT company revenue and NOT shelf-to-
    manufacturer price pass-through. Company-wide growth is never forced to match.
    """
    if not personas:
        raise ValueError('No personas provided')
    s = _validate_scenario(scenario)
    price = s['price_change_pct'] / 100
    budget_stress = max(0, -s['budget_change_pct'] / 100)
    budget_gain = max(0, s['budget_change_pct'] / 100)
    flavor = s['flavor_appeal_pct'] / 100
    marketing = s['marketing_lift_pct'] / 100
    competitor_discount = s['competitor_discount_pct'] / 100
    stockout = s['stockout_pct'] / 100
    base_units = 0.0
    final_units = 0.0
    switch_away_units = 0.0
    switch_in_units = 0.0
    qualifying = 0
    for p in personas:
        if p.get('source') != 'synthetic':
            # Interviews are evidence, not a random sample: never add them as market people.
            continue
        weekly = max(0., float(p['weekly_drinks']))
        if weekly == 0:
            continue
        loyalty = _clamp(float(p['loyalty']), 0, 1)
        sensitivity = _clamp(float(p['price_sensitivity']), 0, 1)
        units = weekly * 13   # 13-week quarter, per persona
        growth = max(0., 1.0 - ASSUMPTIONS['budget_stress_coefficient'] * budget_stress * (0.4 + sensitivity)
                     + 0.35 * budget_gain)
        is_monster = p['favorite_brand'] == target_brand
        if is_monster:
            qualifying += 1
            base_units += units
            # Independent directional drivers; coefficients deliberately not fitted.
            multiplier = (1 - ASSUMPTIONS['price_elasticity_coefficient'] * price * sensitivity * (1 - 0.6 * loyalty)
                          + ASSUMPTIONS['flavor_response_coefficient'] * flavor * (0.45 + 0.55 * (1 - loyalty))
                          + ASSUMPTIONS['marketing_response_coefficient'] * marketing
                          - ASSUMPTIONS['competitor_promotion_coefficient'] * competitor_discount * sensitivity)
            expected = units * growth * _clamp(multiplier, 0, 3) * (1 - ASSUMPTIONS['stockout_response_coefficient'] * stockout)
            final_units += max(0., expected)
            switch_away_units += max(0., units * growth - expected)
        elif p['alternative_brand'] == target_brand:
            # Only a subset of competitor buyers have Monster as their declared alternative.
            # No inflow under an unchanged scenario. Marketing/flavor effects are assumptions.
            attractiveness = (ASSUMPTIONS['competitor_switch_in_marketing_coefficient'] * max(0., marketing)
                              + ASSUMPTIONS['competitor_switch_in_flavor_coefficient'] * max(0., flavor)
                              + ASSUMPTIONS['competitor_switch_in_base_probability'] * max(0., -price))
            attractiveness *= (1 - stockout)
            inflow = units * growth * _clamp(attractiveness, 0, 0.8)
            switch_in_units += inflow
            final_units += inflow
    if base_units <= 0:
        raise ValueError(f'No synthetic panel members with favorite_brand={target_brand!r}')
    change = percent_change(base_units, final_units)
    # Retail price index for a fixed synthetic basket ONLY.
    revenue_index = 100 * (final_units / base_units) * (1 + price)
    return {
        'brand': target_brand, 'scenario': s, 'synthetic_personas_total': sum(p.get('source') == 'synthetic' for p in personas),
        'brand_favorite_personas': qualifying, 'baseline_quarterly_units': round(base_units, 3),
        'scenario_quarterly_units': round(final_units, 3), 'synthetic_brand_volume_change_pct': round(change, 3),
        'synthetic_retail_spend_change_pct': round(revenue_index - 100, 3),
        'switch_away_unit_proxy': round(switch_away_units, 3), 'switch_in_unit_proxy': round(switch_in_units, 3),
        'interpretation': 'Exploratory, uncalibrated directional response; not a manufacturer-revenue forecast.',
    }


def compare_to_report(model: Mapping, report: Mapping) -> dict:
    actual = reported_changes(report)
    simulated = model['synthetic_brand_volume_change_pct']
    observed = actual['company_case_volume_growth_pct']
    return {
        'observed_case_volume_growth_pct': round(observed, 3),
        'simulated_student_monster_volume_change_pct': simulated,
        'direction_matches': (observed > 0 and simulated > 0) or (observed < 0 and simulated < 0) or (observed == 0 and simulated == 0),
        'non_comparable_difference_percentage_points': round(simulated - observed, 3),
        'warning': ('The difference is descriptive, NOT prediction error: company-wide case equivalents '
                    'and simulated US college-student Monster preferences are different populations and measures.'),
    }


def hypothesis_sweep(personas: list[dict], report: Mapping, scenarios: Mapping | None = None) -> list[dict]:
    data = scenarios if scenarios is not None else SCENARIOS
    rows = []
    for label, shock in data.items():
        model = simulate_monster_panel(personas, shock)
        check = compare_to_report(model, report)
        rows.append({'hypothesis': label,
                     'simulated_volume_change_pct': model['synthetic_brand_volume_change_pct'],
                     'simulated_retail_spend_change_pct': model['synthetic_retail_spend_change_pct'],
                     'observed_company_case_volume_growth_pct': check['observed_case_volume_growth_pct'],
                     'direction_matches': check['direction_matches'],
                     'descriptive_gap_pp_not_model_error': check['non_comparable_difference_percentage_points']})
    return rows


def write_sweep_csv(rows: list[dict], path: str | Path) -> Path:
    if not rows:
        raise ValueError('Nothing to export')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
