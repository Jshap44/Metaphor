"""Non-predictive integration of qualitative profiles and reaction-lab artifacts.

No interview-derived market weights or numeric price elasticities are inferred.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path


def load_profiles(directory):
    profiles = []
    for path in sorted(Path(directory).glob('*.json')):
        profile = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(profile, dict) or not profile.get('consumer_id'):
            raise ValueError(f'Invalid interview profile: {path}')
        profiles.append(profile)
    return profiles


def profile_overview(profiles):
    result = []
    for p in profiles:
        products = p.get('product_preferences', {})
        ids = products.get('primary_brands', products.get('favorites', []))
        if not isinstance(ids, list):
            ids = [str(ids)]
        econ = p.get('economic_behavior', p.get('economics', {}))
        freq = p.get('consumption', {})
        result.append(dict(consumer_id=p['consumer_id'], profile_type=p.get('profile_type', 'unknown'),
            brands=', '.join(map(str,ids)),
            consumption=freq.get('frequency', str(freq.get('drinks_per_week', 'unspecified'))),
            real_purchase_data=bool(p.get('metadata', {}).get('real_purchase_data_available', False)),
            calibrated_elasticity=bool(p.get('metadata', {}).get('numeric_price_elasticity_calibrated', False)),
            price_behavior=str(econ.get('price_increase_25pct',econ.get('price_sensitivity','unspecified')))))
    return result


def summarize_reaction_csv(path):
    """Inspect Reaction Lab summary CSV without treating it as observed data."""
    with open(path, newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
    return dict(rows=rows, source=str(path), disclaimer='LLM-stated or dry-run behavior. Placeholder calibration. NOT observed market demand.')
