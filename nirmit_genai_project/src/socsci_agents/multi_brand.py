"""Multi-brand exploratory demand scenarios and carefully labeled reported benchmarks.

Benchmark revenue and synthetic purchase-volume are NOT numerically comparable.
The scenario engine uses the historical_validation assumptions, not fitted data.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Mapping
from .historical_validation import SCENARIOS, simulate_monster_panel, reported_changes, load_report, percent_change

DATA_PATH = Path(__file__).resolve().parents[2] / 'data' / 'energy_brand_benchmarks.json'


def load_brand_catalog(path: str | Path | None = None) -> dict:
    with (Path(path) if path else DATA_PATH).open(encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        raise ValueError('Brand catalog is empty or invalid')
    for name, meta in data.items():
        if meta.get('brand') != name:
            raise ValueError(f'Brand key mismatch for {name}')
        if meta.get('benchmark') is not None:
            b = meta['benchmark']
            if b['metric'] not in ('brand_net_revenue_musd', 'company_case_volume_millions'):
                raise ValueError(f'Unsupported benchmark metric for {name}')
            if b['prior'] <= 0 or b['current'] < 0 or not b.get('source_url'):
                raise ValueError(f'Bad benchmark values for {name}')
    return data


def available_brands(personas: list[dict], catalog: Mapping | None = None) -> list[str]:
    data = catalog if catalog is not None else load_brand_catalog()
    represented = {p.get('favorite_brand') for p in personas if p.get('source') == 'synthetic'}
    return [b for b in data if b in represented]


def simulate_brand(personas: list[dict], brand: str, scenario: Mapping | None = None) -> dict:
    catalog = load_brand_catalog()
    if brand not in catalog:
        raise ValueError(f'Unknown brand: {brand}. Available: {", ".join(catalog)}')
    result = simulate_monster_panel(personas, scenario, target_brand=brand)
    result['brand'] = brand
    result['benchmark'] = catalog[brand]['benchmark']
    result['benchmark_note'] = catalog[brand]['benchmark_note']
    if result['benchmark'] is not None:
        b = result['benchmark']
        result['observed_growth_pct'] = round(percent_change(b['prior'], b['current']), 3)
        result['observed_metric'] = b['metric']
        result['direction_matches_observed'] = ((result['synthetic_brand_volume_change_pct'] > 0) ==
                                                (result['observed_growth_pct'] > 0)) if result['synthetic_brand_volume_change_pct'] != 0 and result['observed_growth_pct'] != 0 else (result['synthetic_brand_volume_change_pct'] == 0 and result['observed_growth_pct'] == 0)
    else:
        result['observed_growth_pct'] = None
        result['observed_metric'] = None
        result['direction_matches_observed'] = None
    result['comparison_warning'] = ('Reported figures can cover different geographies, channels, periods and accounting measures. '
                                    'A synthetic college-student purchase-volume change is not directly comparable '
                                    'with reported revenue; directional agreement does not validate causation or forecasting.')
    return result


def compare_brands(personas: list[dict], scenario: Mapping | None = None, brands: list[str] | None = None) -> list[dict]:
    catalog = load_brand_catalog()
    chosen = brands if brands is not None else available_brands(personas, catalog)
    rows=[]
    for brand in chosen:
        if brand not in catalog:
            raise ValueError(f'Unknown brand: {brand}')
        r = simulate_brand(personas, brand, scenario)
        rows.append(dict(brand=brand, favorites=r['brand_favorite_personas'],
                         baseline_quarterly_units=r['baseline_quarterly_units'],
                         simulated_volume_change_pct=r['synthetic_brand_volume_change_pct'],
                         simulated_retail_spend_change_pct=r['synthetic_retail_spend_change_pct'],
                         observed_growth_pct=r['observed_growth_pct'], observed_metric=r['observed_metric'],
                         source_url=r['benchmark']['source_url'] if r['benchmark'] else '',
                         comparability='NOT DIRECTLY COMPARABLE'))
    return rows


def sweep_brand(personas: list[dict], brand: str) -> list[dict]:
    rows=[]
    for label, shock in SCENARIOS.items():
        r=simulate_brand(personas, brand, shock)
        rows.append(dict(brand=brand, hypothesis=label,
                         simulated_volume_change_pct=r['synthetic_brand_volume_change_pct'],
                         simulated_retail_spend_change_pct=r['synthetic_retail_spend_change_pct'],
                         observed_growth_pct=r['observed_growth_pct'],
                         observed_metric=r['observed_metric']))
    return rows


def export_rows_csv(rows: list[dict], path: str | Path) -> Path:
    if not rows:
        raise ValueError('No results to export')
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path
