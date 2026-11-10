from socsci_agents.energy_market import generate_personas,save_personas,load_personas,simulate,summarize,sensitivity_grid,example_interview

def test_generate_reproducible():
    a=generate_personas(30,seed=7)
    assert a==generate_personas(30,seed=7)
    assert all(x['source']=='synthetic' for x in a)

def test_csv_roundtrip(tmp_path):
    rows=generate_personas(7)
    assert len(load_personas(save_personas(rows,tmp_path/'test.csv')))==7

def test_no_shock_has_low_switch_probability():
    out=summarize(simulate(generate_personas(100),dict(months=3),seed=15))
    assert out['personas']==100
    assert out['persona_months']==300
    assert 0<=out['switched_share']<=1

def test_price_shock_increases_switching():
    rows=generate_personas(300)
    a=summarize(simulate(rows,dict(price_change_pct=0),seed=1))
    b=summarize(simulate(rows,dict(price_change_pct=40),seed=1))
    assert b['switched_share']>a['switched_share']

def test_interview_is_not_population():
    row=example_interview()
    assert row['source']=='single_interview'
    try: simulate([row])
    except ValueError: pass
    else: raise AssertionError('Interview-only input should not make a market prediction')

def test_sensitivity():
    assert len(sensitivity_grid(generate_personas(8)))==12
