from socsci_agents.survey_insights import load_campus_survey,summarize_survey
from socsci_agents.genai_research import frequency_per_week,normalize_choice,statistical_holdout,run_episodes

def test_team_survey_loaded_and_counts():
    people=load_campus_survey()
    assert len(people)==30
    assert all(p['source']=='self_reported_survey' for p in people)
    assert len({p['consumer_id'] for p in people})==30
    snap=summarize_survey(people)
    assert snap['responses']==30
    assert sum(snap['reaction_counts'].values())==30

def test_conservative_parse():
    assert frequency_per_week('8 a month')==8*12/52
    assert frequency_per_week('daily')==7
    assert frequency_per_week('twice per week')==2
    assert frequency_per_week('3') is None
    assert frequency_per_week('3-4 each week') is None
    assert frequency_per_week('Five hour energy') is None
    assert normalize_choice('probably switch or stop drinking') is None
    assert normalize_choice('I would switch')=='switch'

def test_no_false_accuracy_and_offline_runs():
    people=load_campus_survey()
    assert 'error' in statistical_holdout(people)
    results=run_episodes(people[:3],{'price_change_pct':25},episodes=2)
    assert len(results)==6
    assert all(r['model']=='offline' for r in results)
