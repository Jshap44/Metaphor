import pytest
from socsci_agents.energy_market import generate_personas
from socsci_agents.historical_validation import (
    load_report, reported_changes, simulate_monster_panel,
    compare_to_report, hypothesis_sweep, percent_change,
)


def test_filing_values_and_growth():
    report = load_report()
    changes = reported_changes(report)
    assert report['sales_2026_thousand_usd'] == 2563053
    assert 16.6 < changes['consolidated_sales_growth_pct'] < 16.8
    assert 17.9 < changes['company_case_volume_growth_pct'] < 18.1
    assert changes['average_net_sales_per_case_change_pct'] < 0


def test_zero_shock_is_control():
    personas = generate_personas(600, seed=42)
    out = simulate_monster_panel(personas)
    assert out['synthetic_brand_volume_change_pct'] == 0
    assert out['synthetic_retail_spend_change_pct'] == 0


def test_price_increase_reduces_volume_not_necessarily_spend():
    personas = generate_personas(600, seed=42)
    out = simulate_monster_panel(personas, {'price_change_pct': 10})
    assert out['synthetic_brand_volume_change_pct'] < 0
    assert out['synthetic_retail_spend_change_pct'] > out['synthetic_brand_volume_change_pct']


def test_flavor_appeal_and_marketing_directions():
    personas = generate_personas(600, seed=42)
    bad = simulate_monster_panel(personas, {'flavor_appeal_pct': -30})
    good = simulate_monster_panel(personas, {'flavor_appeal_pct': 30})
    marketing = simulate_monster_panel(personas, {'marketing_lift_pct': 20})
    assert bad['synthetic_brand_volume_change_pct'] < 0
    assert good['synthetic_brand_volume_change_pct'] > 0
    assert marketing['synthetic_brand_volume_change_pct'] > 0


def test_reports_annotated_non_comparable():
    personas = generate_personas(600, seed=42)
    result = simulate_monster_panel(personas, {'price_change_pct': 10})
    check = compare_to_report(result, load_report())
    assert check['direction_matches'] is False
    assert 'NOT prediction error' in check['warning']
    assert len(hypothesis_sweep(personas, load_report())) >= 7


def test_rejects_invalid_and_excludes_interviews():
    personas = generate_personas(100, seed=43)
    baseline = simulate_monster_panel(personas)
    personas.append({'source': 'interview_calibrated_consumer', 'favorite_brand': 'Monster'})
    assert simulate_monster_panel(personas)['synthetic_brand_volume_change_pct'] == baseline['synthetic_brand_volume_change_pct']
    with pytest.raises(ValueError):
        simulate_monster_panel(personas, {'stockout_pct': 101})
    with pytest.raises(ValueError):
        simulate_monster_panel(personas, {'unexpected_variable': 1})
    with pytest.raises(ValueError):
        percent_change(0, 3)
