"""Descriptive analysis of the current team-provided survey sample.

No demographic representativeness or enrollment verification is implied.
"""
from collections import Counter
from pathlib import Path
from .genai_research import import_survey_csv

DEFAULT_CSV = Path(__file__).resolve().parents[2] / 'data' / 'cu_boulder_survey_responses.csv'

def load_campus_survey(path=None):
    return import_survey_csv(path or DEFAULT_CSV)

def summarize_survey(consumers):
    counts=Counter(c.get('favorite_brand') or 'Unclassified' for c in consumers)
    reactions=Counter(c.get('label') or 'Ambiguous / unclassified' for c in consumers)
    quantities=[float(c['weekly_drinks']) for c in consumers if c.get('weekly_drinks') is not None]
    budgets=Counter(c.get('fields',{}).get('budget') or 'Not supplied' for c in consumers)
    labeled=sum(c.get('label_source')=='free_text_heuristic' for c in consumers)
    return dict(responses=len(consumers),known_weekly=len(quantities),mean_weekly=sum(quantities)/len(quantities) if quantities else None,
                brand_counts=dict(counts),reaction_counts=dict(reactions),budget_counts=dict(budgets),
                interpreted_price_reactions=labeled,
                disclaimer='Team-reported CU Boulder collection context; enrollment not independently verified. Nonrepresentative, self-reported and hypothetical choices. Brand counts show first recognized brand, not market shares.')
