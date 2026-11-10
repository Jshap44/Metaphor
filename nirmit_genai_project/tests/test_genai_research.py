import csv
import json
from pathlib import Path
import pytest
from socsci_agents.genai_research import (build_demo_survey,import_survey_csv,frequency_per_week,normalize_choice,
    prompt_for_choice,run_episodes,aggregate_episodes,statistical_holdout,compare_methods_holdout,interview_to_consumer,
    validate_prediction)

def test_frequency_strict():
    assert frequency_per_week('2 per day')==14
    assert frequency_per_week('8 per month')==pytest.approx(8*12/52)
    assert frequency_per_week('sometimes') is None

def test_import_google_forms_csv(tmp_path):
    p=tmp_path/'form.csv'
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['How often do you consume energy drinks? Give your best estimate in drinks per week or month.',
            'Which energy drink brands do you currently purchase, and approximately what proportion of your purchases does each represent?',
            'If your favorite drink increased in price by 25%, while competitors prices stayed the same?',
            'If your favorite energy drink increased in price by 25%, what would you most likely do?'])
        w.writerow(['5 per week','Monster: 80%, Red Bull: 20%','Probably would change','Switch to a different brand'])
    rows=import_survey_csv(p)
    assert len(rows)==1 and rows[0]['favorite_brand']=='Monster' and rows[0]['weekly_drinks']==5
    assert rows[0]['label']=='switch' and rows[0]['label_source']=='structured_choice'
    assert len(rows[0]['raw_answers'])==4

def test_no_test_label_leakage():
    c=build_demo_survey(1)[0]
    c['fields']['price_response']='UNIQUE_HOLDOUT_ANSWER_MARKER'
    prompt=prompt_for_choice(c,{'price_change_pct':25})
    assert 'UNIQUE_HOLDOUT_ANSWER_MARKER' not in prompt
    assert 'synthetic_demo' in prompt

def test_episodes_memory_and_no_memory():
    people=build_demo_survey(3)
    a=run_episodes(people,{'price_change_pct':25},episodes=3,memory_enabled=True)
    b=run_episodes(people,{'price_change_pct':25},episodes=3,memory_enabled=False)
    assert len(a)==len(b)==9
    assert aggregate_episodes(a)['total']==9
    assert all(r['model']=='offline' for r in a)

def test_statistical_split():
    score=statistical_holdout(build_demo_survey(90))
    assert score['test_n']>0 and 0<=score['accuracy']<=1
    assert score['train_n']+score['test_n']==score['n']
    report=compare_methods_holdout(build_demo_survey(90))
    assert report['offline']['n']==score['test_n']

def test_no_evaluation_when_unlabeled():
    rows=build_demo_survey(12)
    for r in rows:r['label']=None
    assert 'error' in statistical_holdout(rows)

def test_prediction_validation():
    with pytest.raises(ValueError):validate_prediction({'choice':'same','quantity_after':-1})

def test_interview_profile_preserves_unknown():
    profile={'consumer_id':'c1','consumption':{},'product_preferences':{'favorites':['Ghost']},'economics':{}}
    out=interview_to_consumer(profile)
    assert out['source']=='interview' and out['weekly_drinks'] is None and out['label'] is None
