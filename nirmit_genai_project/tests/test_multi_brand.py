import json
import pytest
from socsci_agents.energy_market import generate_personas
from socsci_agents.multi_brand import load_brand_catalog, available_brands, simulate_brand, compare_brands, sweep_brand


def test_catalog_facts_and_missing_benchmarks():
    c=load_brand_catalog()
    assert c['Celsius']['benchmark']['prior']==381.0
    assert c['Alani Nu']['benchmark']['current']==410.1
    assert c['Red Bull']['benchmark'] is None
    assert c['Monster']['benchmark']['metric']=='company_case_volume_millions'


def test_simulation_control_and_direction():
    panel=generate_personas(600,seed=21)
    for b in ('Monster','Celsius','Red Bull','Alani Nu','Rockstar','Ghost','C4'):
        control=simulate_brand(panel,b,{})
        assert control['synthetic_brand_volume_change_pct']==0
        high=simulate_brand(panel,b,{'price_change_pct':25})
        assert high['synthetic_brand_volume_change_pct']<0
        assert high['brand_favorite_personas']>0


def test_missing_benchmark_and_brands():
    panel=generate_personas(600,seed=21)
    r=simulate_brand(panel,'Red Bull',{'price_change_pct':15})
    assert r['observed_growth_pct'] is None
    assert r['direction_matches_observed'] is None
    with pytest.raises(ValueError):
        simulate_brand(panel,'not-a-brand')


def test_sweep_and_comparison():
    panel=generate_personas(600,seed=21)
    rows=compare_brands(panel,{'flavor_appeal_pct':20})
    assert 'Alani Nu' in {x['brand'] for x in rows}
    assert len(rows)==len(available_brands(panel))
    assert len(sweep_brand(panel,'Celsius'))>=8
    assert all(x['comparability']=='NOT DIRECTLY COMPARABLE' for x in rows)
