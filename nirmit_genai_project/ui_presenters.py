"""Human-readable Streamlit presentation of experiment results.

Keep structured data in downloads, not as raw JSON/code blocks in the UI.
"""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st


def friendly(text):
    return str(text).replace('_', ' ').replace('-', ' ').strip().capitalize()


def readable(value):
    if value is None:
        return 'Not available'
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, dict):
        return '; '.join(f'{friendly(k)}: {readable(v)}' for k,v in value.items()) or 'Not provided'
    if isinstance(value, (list, tuple)):
        return ', '.join(readable(v) for v in value) or 'Not provided'
    if isinstance(value, float):
        return f'{value:,.3f}'
    return str(value)


def interview_profile(profile):
    st.subheader('Consumer preferences')
    preferences = profile.get('product_preferences', {})
    consumption = profile.get('consumption', {})
    economics = profile.get('economic_behavior', profile.get('economics', {}))
    columns = st.columns(3)
    brands = preferences.get('primary_brands', preferences.get('favorites', []))
    columns[0].metric('Favorite brands', ', '.join(map(str, brands)) if brands else 'Not specified')
    freq = consumption.get('frequency', consumption.get('drinks_per_week', 'Not specified'))
    columns[1].metric('Consumption frequency', readable(freq))
    columns[2].metric('Purchase data verified', 'Yes' if profile.get('metadata', {}).get('real_purchase_data_available') else 'No')
    for name, data in [('Consumption habits', consumption), ('Product preferences', preferences),
                       ('Price and purchasing behavior', economics),
                       ('Behavioral factors', profile.get('behavioral_factors', {}))]:
        with st.expander(name):
            if not isinstance(data, dict) or not data:
                st.caption('No details provided')
            else:
                rows = [{'Attribute': friendly(k), 'Response': readable(v)} for k,v in data.items()]
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption('An individual qualitative interview, not representative of the college-student market.')
    st.download_button('Download full interview profile', json.dumps(profile, indent=2),
                       f"{profile['consumer_id']}_profile.json", mime='application/json',
                       key=f"profile_download_{profile['consumer_id']}")


def episode_summary(summary):
    if not summary.get('total'):
        st.info('No agent decisions recorded.'); return
    a,b = st.columns(2)
    a.metric('Simulated purchase decisions', f"{summary['total']:,}")
    b.metric('Average units after event', f"{summary.get('mean_units_after', 0):.2f}")
    c,d = st.columns(2)
    with c:
        st.markdown('**Purchase behavior**')
        st.bar_chart(pd.Series(summary.get('choices', {}), name='Decisions'))
    with d:
        st.markdown('**Chosen brands**')
        st.bar_chart(pd.Series(summary.get('by_brand', {}), name='Decisions'))
    if summary.get('caveat'): st.caption(summary['caveat'])


def evaluation_summary(result):
    """Show scores, warnings, confusion matrices and nested model comparisons."""
    if not isinstance(result, dict):
        st.write(readable(result)); return
    if result.get('error'):
        st.warning(result['error']); return
    metrics = [(friendly(k),v) for k,v in result.items()
               if k in ('n','train_n','test_n','accuracy','balanced_accuracy')]
    if metrics:
        columns = st.columns(len(metrics))
        for column,(name,val) in zip(columns,metrics):
            shown = f'{val:.1%}' if name in ('Accuracy', 'Balanced accuracy') and isinstance(val,(int,float)) else readable(val)
            column.metric(name,shown)
    if result.get('confusion_matrix'):
        labels = [friendly(v) for v in result.get('confusion_labels', [])]
        st.markdown('**Confusion matrix (actual rows, predicted columns)**')
        st.dataframe(pd.DataFrame(result['confusion_matrix'],index=labels,columns=labels),use_container_width=True)
    if result.get('test_results'):
        st.markdown('**Held-out predictions**')
        st.dataframe(pd.DataFrame(result['test_results']),hide_index=True,use_container_width=True)
    for key in ('statistical','offline','llm'):
        if key in result:
            st.subheader({'statistical':'Statistical model','offline':'Rule-based baseline','llm':'LLM agent'}[key])
            evaluation_summary(result[key])
    if result.get('warning'): st.warning(result['warning'])
