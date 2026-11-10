"""Run: streamlit run energy_dashboard.py"""
import pandas as pd
import streamlit as st
from socsci_agents.energy_market import load_personas,simulate,summarize,sensitivity_grid
from ui_presenters import interview_profile, episode_summary, evaluation_summary

st.set_page_config(page_title='Energy Drink Market Simulator',layout='wide')
st.title('College Student Energy Drink — Market Simulator')
st.caption('Integrated project: heuristic market simulator + teammates’ Reaction Lab + qualitative interview profiles')
st.warning('Research prototype. All market forecasts here are synthetic, heuristic, and unvalidated. Not investment advice.')
path=st.sidebar.text_input('Persona CSV','data/energy_personas_synthetic.csv')
price=st.sidebar.slider('Favorite-brand price change (%)',-50,100,25)
budget=st.sidebar.slider('Discretionary-budget change (%)',-60,30,-15)
health=st.sidebar.slider('Health concern shock (0 to 1)',0.0,1.0,0.0,0.05)
stockout=st.sidebar.slider('Stockout probability (%)',0,100,0)
discount=st.sidebar.slider('Competitor discount (%)',0,60,0)
months=st.sidebar.slider('Simulated months',1,24,6)
unit_cost=st.sidebar.number_input('Illustrative per-serving cost ($)',0.0,15.0,1.35,0.05)
try:
    personas=load_personas(path)
except Exception as exc:
    st.error(f'Cannot read personas: {exc}. Run `energy-market generate` first.');st.stop()
scenario=dict(price_change_pct=price,budget_change_pct=budget,health_risk=health,
              stockout_pct=stockout,competitor_discount_pct=discount,months=months,unit_cost=unit_cost)
records=simulate(personas,scenario)
metrics=summarize(records)
a,b,c,d=st.columns(4)
a.metric('Projected servings',f"{metrics['projected_units']:,.0f}",f"{metrics['volume_change_pct']:.1f}%")
b.metric('Illustrative revenue',f"${metrics['projected_revenue']:,.0f}",f"{metrics['revenue_change_pct']:.1f}%")
c.metric('Illustrative gross profit',f"${metrics['projected_gross_profit']:,.0f}",f"{metrics['gross_profit_change_pct']:.1f}%")
d.metric('Brand switching',f"{metrics['switched_share']:.1%}")
st.caption(f"{metrics['personas']:,} synthetic personas × {months} months. Amounts apply to the simulated panel, not the actual market.")
left,right=st.columns(2)
with left:
    st.subheader('Servings by month')
    st.line_chart(pd.DataFrame(metrics['by_month']).set_index('month')[['baseline_units','projected_units']])
with right:
    st.subheader('Projected brand volumes')
    st.bar_chart(pd.Series(metrics['projected_brand_units']).sort_values(ascending=False))
st.subheader('Illustrative sensitivity analysis')
st.dataframe(pd.DataFrame(sensitivity_grid(personas)),use_container_width=True)
st.subheader('Sample simulated decisions')
st.dataframe(pd.DataFrame(records).head(40),use_container_width=True)
st.download_button('Export aggregated scenario JSON',__import__('json').dumps(metrics,indent=2),'scenario_summary.json','application/json')
st.info('This system does not connect to trading accounts, infer real market size, or estimate a stock price target. Obtain representative surveys and observed purchasing data before interpreting changes as forecasts.')


# Read-only integration panels: intentionally not merged into the synthetic market panel.
st.divider()
st.header('Teammates’ Reaction Lab and consumer interviews')
st.info('The profile evidence and LLM runs are separate research tracks. They are not calibrated market forecasts and do not modify the synthetic panel above.')
from pathlib import Path
from socsci_agents.integration import load_profiles,profile_overview,summarize_reaction_csv
profile_tab, reaction_tab = st.tabs(['Interview personas', 'Reaction Lab results'])
with profile_tab:
    profiles = load_profiles('personas')
    if profiles:
        st.dataframe(pd.DataFrame(profile_overview(profiles)),use_container_width=True)
        selected=st.selectbox('Inspect interview profile', [p['consumer_id'] for p in profiles])
        interview_profile(next(p for p in profiles if p['consumer_id']==selected))
    else:
        st.warning('No interview profiles found in personas/')
with reaction_tab:
    st.info('This section displays saved Reaction Lab results. Run experiments from the terminal, then return here to compare the results.')
    results = sorted(Path('output').glob('*summary*.csv'),reverse=True) if Path('output').exists() else []
    if results:
        file=st.selectbox('Reaction summary CSV',results,format_func=lambda p:p.name)
        reaction=summarize_reaction_csv(file)
        st.dataframe(pd.DataFrame(reaction['rows']),use_container_width=True)
        st.caption(reaction['disclaimer'])
    else:
        st.caption('No Reaction Lab summary files yet. Run the dry-run experiment first; results will appear here.')

# ------------------------------------------------------------------------------
# Historical case study: strictly separate published financials from panel proxy.
# ------------------------------------------------------------------------------
st.divider()
st.header('Historical Validation Lab — Monster Q3 2026')
st.caption('Observed corporate metrics vs. hypothetical college-student demand responses. ' 
           'The two populations are not equivalent; matching a sign does not validate a forecast.')
from socsci_agents.historical_validation import (
    load_report, reported_changes, simulate_monster_panel, compare_to_report,
    hypothesis_sweep, SCENARIOS,
)
try:
    filing = load_report()
    observed = reported_changes(filing)
except (OSError, ValueError) as exc:
    st.error(f'Cannot load the sourced earnings benchmark: {exc}')
else:
    st.markdown(f"**Observed:** [{filing['period']}]({filing['press_release_url']}) · "
                f"[SEC 10-Q]({filing['sec_10q_url']})")
    o1,o2,o3,o4 = st.columns(4)
    o1.metric('Consolidated sales YoY', f"{observed['consolidated_sales_growth_pct']:+.1f}%")
    o2.metric('Energy segment sales YoY', f"{observed['energy_segment_sales_growth_pct']:+.1f}%")
    o3.metric('Company case volume YoY', f"{observed['company_case_volume_growth_pct']:+.1f}%")
    o4.metric('Manufacturer net sales/case YoY', f"{observed['average_net_sales_per_case_change_pct']:+.1f}%")
    st.caption('Financial data is company-wide. Case volume uses 192-ounce equivalents; '
               'net sales/case is a wholesale-level measure, not retail price.')
    st.subheader('Test a specific consumer-demand hypothesis')
    def _apply_historical_preset():
        shock = SCENARIOS[st.session_state['historical_preset']]
        for widget_key, scenario_key in [
            ('hist_price', 'price_change_pct'), ('hist_budget', 'budget_change_pct'),
            ('hist_flavor', 'flavor_appeal_pct'), ('hist_marketing', 'marketing_lift_pct'),
            ('hist_competitor', 'competitor_discount_pct'), ('hist_stockout', 'stockout_pct'),
        ]:
            st.session_state[widget_key] = int(shock.get(scenario_key, 0))

    preset = st.selectbox('Start with a hypothesis', list(SCENARIOS), index=1,
                          key='historical_preset', on_change=_apply_historical_preset)
    default_shock = SCENARIOS[preset]
    h1,h2,h3 = st.columns(3)
    with h1:
        hp = st.slider('Monster price change (%)', -40, 60,
                       int(default_shock.get('price_change_pct', 0)), 1, key='hist_price')
        hb = st.slider('Student budget change (%)', -50, 30,
                       int(default_shock.get('budget_change_pct', 0)), 1, key='hist_budget')
    with h2:
        hf = st.slider('Flavor/product appeal shock (%)', -100, 100,
                       int(default_shock.get('flavor_appeal_pct', 0)), 5, key='hist_flavor')
        hm = st.slider('Marketing/awareness shock (%)', -100, 100,
                       int(default_shock.get('marketing_lift_pct', 0)), 5, key='hist_marketing')
    with h3:
        hc = st.slider('Competitor discount (%)', 0, 60,
                       int(default_shock.get('competitor_discount_pct', 0)), 5, key='hist_competitor')
        hs = st.slider('Monster stockout rate (%)', 0, 100,
                       int(default_shock.get('stockout_pct', 0)), 5, key='hist_stockout')
    shock = dict(price_change_pct=hp, budget_change_pct=hb, flavor_appeal_pct=hf,
                 marketing_lift_pct=hm, competitor_discount_pct=hc, stockout_pct=hs)
    try:
        result = simulate_monster_panel(personas, shock)
        comparison = compare_to_report(result, filing)
    except ValueError as exc:
        st.error(f'Cannot simulate scenario: {exc}')
    else:
        m1,m2,m3 = st.columns(3)
        m1.metric('Synthetic Monster volume change', f"{result['synthetic_brand_volume_change_pct']:+.1f}%")
        m2.metric('Synthetic retail spend index change', f"{result['synthetic_retail_spend_change_pct']:+.1f}%")
        m3.metric('Observed corporate case-volume growth',
                  f"{comparison['observed_case_volume_growth_pct']:+.1f}%")
        st.bar_chart(pd.DataFrame({
            'Growth (%)': [result['synthetic_brand_volume_change_pct'],
                           comparison['observed_case_volume_growth_pct']],
        }, index=['Simulated US student Monster purchasing', 'Observed company case volume']))
        direction = 'same' if comparison['direction_matches'] else 'different'
        st.write(f'**Directional check:** The signs are **{direction}**. '
                 'This is not a causal finding or out-of-sample validation.')
        st.warning(comparison['warning'])
        st.download_button('Export this historical scenario (JSON)',
                           __import__('json').dumps({'hypothesis': preset, 'model': result,
                                                     'reported': observed, 'comparison': comparison}, indent=2),
                           'monster_q3_hypothesis.json', 'application/json')
    st.subheader('Compare predeclared hypotheses')
    candidates = pd.DataFrame(hypothesis_sweep(personas, filing))
    st.dataframe(candidates, use_container_width=True)
    st.download_button('Download hypotheses (CSV)', candidates.to_csv(index=False),
                       'monster_q3_hypothesis_sweep.csv', 'text/csv')
    with st.expander('Methodology / limitations — please read'):
        st.markdown('''
- **Actual financials:** Q3 2026 and Q3 2025 Monster disclosures, with explicit source links.
- **Hypotheses:** Price, flavor and marketing shocks are *proposed interventions*, not identified causes of Monster's results.
- **Simulation:** Transparent rule-based assumptions and a **synthetic** college-student panel; no learned elasticities or real sales calibration.
- **Unit mismatch:** The simulated measure is expected Monster purchases among synthetic US students; reported case volumes cover the company, geographies and channels. Their numerical gap **is not forecast error**.
- **Price mismatch:** The retail price/shopping index is not the manufacturer average net sales per case.
- **No fitting to Q3:** The simulator is not tuned to reproduce this quarter. Directional alignment alone is weak evidence; use independent holdout periods and observed behavior to assess prediction performance.
- **Next:** Acquire documented region/channel-level price and unit observations, estimate response parameters from surveys or experiments, then run preregistered out-of-sample backtests.
''')

# ------------------------------------------------------------------------------
# Multi-brand extension: same hypothetical scenario across several brands.
# Published brand revenue is never treated as measured college-student volume.
# ------------------------------------------------------------------------------
st.divider()
st.header('Multi-Brand Scenario & Earnings Comparison')
st.caption('Choose a brand or compare the same hypothetical shock across several. '
           'A brand-level revenue increase is not the same thing as a consumer-volume increase.')
from socsci_agents.multi_brand import (
    load_brand_catalog, available_brands, simulate_brand, compare_brands, sweep_brand
)
brand_catalog = load_brand_catalog()
represented = available_brands(personas, brand_catalog)
if not represented:
    st.warning('The synthetic persona CSV contains no recognized brands.')
else:
    mode = st.radio('Analysis mode', ['Compare all represented brands', 'Inspect one brand'], horizontal=True)
    selected_brand = None
    if mode == 'Inspect one brand':
        selected_brand = st.selectbox('Target energy drink brand', represented, index=represented.index('Celsius') if 'Celsius' in represented else 0)
    mb1, mb2, mb3 = st.columns(3)
    with mb1:
        mb_price = st.slider('Target brand shelf-price change (%)', -40, 60, 10, key='mb_price')
        mb_budget = st.slider('Student budget change (%)', -50, 30, 0, key='mb_budget')
    with mb2:
        mb_flavor = st.slider('Flavor appeal change (%)', -100, 100, 0, 5, key='mb_flavor')
        mb_marketing = st.slider('Marketing / awareness change (%)', -100, 100, 0, 5, key='mb_marketing')
    with mb3:
        mb_discount = st.slider('Competitor price discount (%)', 0, 60, 0, 5, key='mb_discount')
        mb_stockout = st.slider('Stockout rate (%)', 0, 100, 0, 5, key='mb_stockout')
    mb_scenario = dict(price_change_pct=mb_price, budget_change_pct=mb_budget,
                       flavor_appeal_pct=mb_flavor, marketing_lift_pct=mb_marketing,
                       competitor_discount_pct=mb_discount, stockout_pct=mb_stockout)
    if mode == 'Compare all represented brands':
        frame = pd.DataFrame(compare_brands(personas, mb_scenario))
        st.subheader('Simulated volume changes by brand')
        st.bar_chart(frame.set_index('brand')[['simulated_volume_change_pct']])
        st.dataframe(frame, use_container_width=True)
        st.download_button('Download multi-brand comparison (CSV)', frame.to_csv(index=False),
                           'multibrand_comparison.csv', 'text/csv')
        st.info('This applies the same shock to each brand **separately**, holding the rest of the panel constant. '
                'Do not sum these counterfactual changes across brands or treat them as a market-share forecast.')
    else:
        r = simulate_brand(personas, selected_brand, mb_scenario)
        a,b,c = st.columns(3)
        a.metric('Simulated purchase-volume change', f"{r['synthetic_brand_volume_change_pct']:+.2f}%")
        b.metric('Simulated retail-spend index change', f"{r['synthetic_retail_spend_change_pct']:+.2f}%")
        c.metric('Synthetic favorite-brand students', f"{r['brand_favorite_personas']:,}")
        benchmark = r['benchmark']
        if benchmark:
            st.markdown(f"**Published Q3 2026 vs Q3 2025 benchmark:** "
                        f"{r['observed_growth_pct']:+.2f}% in {benchmark['metric'].replace('_', ' ')}. "
                        f"[Official source]({benchmark['source_url']}).")
        else:
            st.caption('No verified comparable quarterly metric is included for this brand.')
        st.caption(r['benchmark_note'])
        st.warning(r['comparison_warning'])
        st.subheader(f'{selected_brand}: hypothesis sensitivity')
        swept = pd.DataFrame(sweep_brand(personas, selected_brand))
        st.dataframe(swept, use_container_width=True)
        st.download_button('Download brand hypotheses (CSV)', swept.to_csv(index=False),
                           f'{selected_brand.lower().replace(" ", "_")}_hypotheses.csv', 'text/csv')
        st.download_button('Download brand experiment (JSON)', __import__('json').dumps(r, indent=2),
                           'brand_experiment.json', 'application/json')
    with st.expander('Which numbers are real, and what is assumed?'):
        st.markdown('''
- **Observed:** Monster company-wide energy-drink case equivalents; Celsius and Alani Nu *brand revenue* as reported by Celsius Holdings. These are different measures.
- **Not available:** Verified directly comparable Q3 figures for Red Bull, Ghost, C4, Gorilla Mind, and Rockstar within this research dataset. Rockstar has a Q3 2026 standalone figure but not a verified comparative period.
- **Synthetic:** All simulated student volumes, retail spending, price sensitivity, flavor appeal, switch-in, and advertising effects. They have NOT been calibrated to the companies' financial reports or to observed student purchases.
- **Interpretation:** Brand-by-brand shocks are independent counterfactual experiments; they do not sum to a coherent market-level set of simultaneous changes. Neither agreement of sign nor similarity of magnitude proves causation or forecast accuracy.
''')

# ------------------------------------------------------------------------------
# Generative AI research: deliberately separate model evaluations from revenue.
# ------------------------------------------------------------------------------
st.divider()
st.header('Generative AI Consumer Research Lab')
st.caption('Survey-grounded agents, optional live LLM decisions, memory ablation and held-out evaluation. '
           'Offline mode is a heuristic stand-in, not an LLM. Do not interpret this sample as market share.')
from socsci_agents.genai_research import (import_survey_csv,build_demo_survey,interview_to_consumer,
    run_episodes,aggregate_episodes,compare_methods_holdout,statistical_holdout,save_survey_jsonl)
from socsci_agents.integration import load_profiles as _load_real_profiles
research_source=st.radio('Consumer inputs',['CU Boulder survey (30 responses)','Synthetic demonstration','Interview profiles','Upload Google Forms CSV'],horizontal=True)
from socsci_agents.survey_insights import load_campus_survey, summarize_survey, DEFAULT_CSV
research_consumers=[]
if research_source=='CU Boulder survey (30 responses)':
    research_consumers=load_campus_survey()
    st.success(f'Loaded {len(research_consumers)} survey responses collected in the CU Boulder study context (as reported by the team).')
    st.warning('The form does not verify student enrollment; these respondents must not be claimed to represent all CU Boulder students. The price responses are hypothetical and not observed purchases.')
    insights=summarize_survey(research_consumers)
    st.subheader('Survey snapshot')
    si1,si2,si3=st.columns(3)
    si1.metric('Survey respondents',insights['responses'])
    si2.metric('Unambiguous weekly frequencies',insights['known_weekly'])
    si3.metric('Interpretable price reactions',insights['interpreted_price_reactions'])
    sa,sb=st.columns(2)
    with sa:
        st.markdown('**Brands mentioned first**')
        st.bar_chart(pd.Series(insights['brand_counts']).sort_values(ascending=False))
        st.caption('First recognized brand only, not purchases or market share.')
    with sb:
        st.markdown('**Stated 25% price-increase reactions**')
        st.bar_chart(pd.Series(insights['reaction_counts']).sort_values(ascending=False))
        st.caption('Conservative keyword-based coding. Ambiguous responses stay unclassified.')
    with st.expander('Review anonymized survey profiles'):
        overview=pd.DataFrame([dict(consumer_id=c['consumer_id'],first_brand=c.get('favorite_brand') or 'Unknown',
            drinks_per_week=c.get('weekly_drinks'),budget=c['fields'].get('budget') or 'Unknown',
            stated_reaction=c.get('label') or 'Unclassified',label_quality=c.get('label_source')) for c in research_consumers])
        st.dataframe(overview,use_container_width=True,hide_index=True)
    st.caption(insights['disclaimer'])
elif research_source=='Synthetic demonstration':
    research_consumers=build_demo_survey(90)
    st.warning('DEMO: 90 fabricated survey rows; this mode demonstrates code only. It is not empirical validation.')
elif research_source=='Interview profiles':
    research_consumers=[interview_to_consumer(p) for p in _load_real_profiles('personas')]
    st.info('Two qualitative interview cases, not representative survey samples. No held-out labels yet.')
else:
    uploaded=st.file_uploader('Google Forms CSV export',type=['csv'],key='genai_survey_upload')
    if uploaded:
        import tempfile,os
        with tempfile.NamedTemporaryFile(mode='wb',suffix='.csv',delete=False) as tmp:
            tmp.write(uploaded.getvalue()); temp_path=tmp.name
        try:
            research_consumers=import_survey_csv(temp_path)
        finally:
            os.unlink(temp_path)
        st.success(f'Imported {len(research_consumers)} survey rows. Original free-text answers are preserved; no fabricated observations.')
        source_counts=pd.Series([r['label_source'] for r in research_consumers]).value_counts()
        st.dataframe(source_counts.rename('count'))
        st.download_button('Download structured survey JSONL',
            ''.join(__import__('json').dumps(r,ensure_ascii=False)+'\n' for r in research_consumers),
            'survey_imported.jsonl','application/x-ndjson')
if research_consumers:
    study_tab,eval_tab,design_tab=st.tabs(['Agent purchasing experiments','Held-out evaluation','Research interpretation'])
    with study_tab:
        a,b,c=st.columns(3)
        with a:
            study_price=st.slider('Agent scenario: price change (%)',-30,80,25,5,key='study_price')
            study_budget=st.slider('Agent scenario: budget change (%)',-50,30,0,5,key='study_budget')
        with b:
            study_flavor=st.slider('Agent scenario: flavor appeal change (%)',-100,100,0,5,key='study_flavor')
            study_stock=st.slider('Agent scenario: stockout (%)',0,100,0,5,key='study_stock')
        with c:
            study_mode=st.selectbox('Response engine',['offline','llm'],help='LLM mode requires an Anthropic API key supplied as an environment variable.')
            study_memory=st.checkbox('Include previous simulated purchase episodes in agent context',value=True)
            study_episodes=st.slider('Episodes per consumer',1,5,3)
            study_count=st.slider('Consumers to simulate',1,min(30,len(research_consumers)),min(5,len(research_consumers)))
        st.caption('Memory ablation: turn memory off and run the SAME scenario for comparison. '
                   'Memory is a context log of prior agent answers, not learned facts or observed purchasing history.')
        if st.button('Run consumer agents',key='run_genai_agents'):
            scenario=dict(price_change_pct=study_price,budget_change_pct=study_budget,
                          flavor_appeal_pct=study_flavor,stockout_pct=study_stock)
            try:
                with st.spinner('Running selected consumer agents'):
                    runs=run_episodes(research_consumers[:study_count],scenario,mode=study_mode,
                        episodes=study_episodes,memory_enabled=study_memory,max_calls=20)
                st.subheader('Consumer decision distribution')
                episode_summary(aggregate_episodes(runs))
                st.dataframe(pd.DataFrame(runs),use_container_width=True)
                st.download_button('Export agent predictions',pd.DataFrame(runs).to_csv(index=False),
                                   'agent_predictions.csv','text/csv')
            except Exception as exc:
                st.error(f'Agent experiment could not run: {exc}')
    with eval_tab:
        st.markdown('**No answer leakage:** a consumer’s price-increase answer is excluded from prompts. '
                    'Statistical tests split by consumer ID before training.')
        st.warning('If the input is the synthetic demo, scores are synthetic smoke-test results, not scientific evidence. '
                   'For survey rows, these labels measure stated intent, not actual future purchases. Free-text labels are excluded from statistical training until manually adjudicated.')
        st.subheader('Statistical baseline: held-out 25% price scenario')
        if st.button('Train and evaluate statistical baseline'):
            try:
                score=statistical_holdout(research_consumers)
                evaluation_summary(score)
            except Exception as exc:st.error(f'Could not evaluate baseline: {exc}')
        if st.button('Compare statistical baseline versus offline agent'):
            try:
                report=compare_methods_holdout(research_consumers)
                evaluation_summary(report)
            except Exception as exc:st.error(f'Could not compare: {exc}')
        st.caption('Live LLM evaluation is available through the optional research command-line workflow and requires API credentials. API usage may incur charges.')
    with design_tab:
        st.markdown('''**Experimental design:** Compare rule-based, survey-trained statistical, and LLM methods on the same *held-out* respondents and scenario. Record accuracy and balanced accuracy, plus quantity error when a numeric ground truth is available. Repeat live LLM calls to measure consistency; compare agents with and without prior-episode memory.

**Current limits:** Two interview profiles have no blind held-out test outcomes; Google Forms questions are not the responses; generic survey intentions at +25% are not observed purchases or Q3 corporate earnings. The offline mode is explicitly heuristic. An LLM with memory can still hallucinate or drift. The college-student sample is not automatically representative of the market.''')
