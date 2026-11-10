import csv
import json
from pathlib import Path
from socsci_agents.integration import load_profiles, profile_overview, summarize_reaction_csv

ROOT = Path(__file__).resolve().parents[1]

def test_profiles():
    p = load_profiles(ROOT / 'personas')
    assert {x['consumer_id'] for x in p} == {'consumer_001','consumer_002'}
    overview = profile_overview(p)
    assert len(overview) == 2
    assert all(x['real_purchase_data'] is False for x in overview)

def test_reaction_summary_csv(tmp_path):
    file = tmp_path/'summary.csv'
    file.write_text('format,segment,stated_change_pct\nchoice,Loyal regulars,-10\n',encoding='utf8')
    summary=summarize_reaction_csv(file)
    assert summary['rows'][0]['stated_change_pct']=='-10'

def test_reaction_source_and_defaults():
    # Source file is preserved separately, with its original defaults.
    source=(ROOT/'reaction_lab'/'simulate.py').read_text(encoding='utf-8')
    assert 'STATED_TO_ACTUAL = 0.45' in source
    assert 'def persona_mode(argv)' in source
