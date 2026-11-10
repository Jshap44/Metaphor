"""Optional Streamlit demonstration. Run: streamlit run app.py"""
import json
from pathlib import Path
import streamlit as st
from socsci_agents.agent import SurveyAgent
from socsci_agents.model import predict
from socsci_agents.data import normalize
from ui_presenters import readable, friendly

st.set_page_config(page_title="SocSci210 Research Prototype", layout="wide")
st.title("SocSci210 • Generative Survey Agents")
st.caption("Experimental survey-response prediction. Simulated responses are not observed human behavior.")
example = json.loads(Path("data/example_input.json").read_text(encoding="utf-8"))
model = st.text_input("Model artifact", "artifacts/models.joblib")
stimulus = st.text_area("Stimulus", example["stimuli"], height=140)
question = st.text_area("Survey question / prompt", example["prompt"], height=140)
persona = st.text_area("Demographic JSON", json.dumps(example["demographic"], indent=2), height=170)
study = st.text_input("Study ID", example["study_id"])
task = st.number_input("Task number", value=int(example["task_num"]), step=1)
condition = st.number_input("Condition number", value=int(example["condition_num"]), step=1)
if st.button("Simulate response", type="primary"):
    try:
        row = normalize({**example, "stimuli": stimulus, "prompt": question,
                         "demographic": json.loads(persona), "study_id": study,
                         "task_num": task, "condition_num": condition})
        agent = SurveyAgent(persona=row["demographic"])
        result = agent.react(stimulus, question, lambda r: predict(r, model), row)
        st.subheader('Predicted response')
        for key, value in result.items():
            st.markdown(f'**{friendly(key)}:** {readable(value)}')
    except Exception as exc:
        st.error(str(exc))
