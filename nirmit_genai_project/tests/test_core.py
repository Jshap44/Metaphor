from socsci_agents.agent import SurveyAgent
from socsci_agents.data import split_name, group_key, normalize
from socsci_agents.model import train, predict
import json

def test_group_split_participant():
    a = normalize({"study_id":"A", "task_num": 1, "participant": 9})
    b = normalize({"study_id":"A", "task_num": 2, "participant": 9})
    assert split_name(a) == split_name(b)
    assert group_key(a) != group_key(b)

def test_agent_reflection():
    agent = SurveyAgent(persona={"age": 25}, reflection_every=2)
    agent.observe("Watched a town hall")
    agent.observe("Read an article")
    assert any(m.kind == "reflection" for m in agent.memories)
    assert agent.retrieve("article")

def test_train_prediction(tmp_path):
    import random
    rows=[]
    for i in range(120):
        rows.append({"study_id":"demo", "task_num":0, "participant":i,
                     "demographic":{"age": 20 + i%40, "preference": "A" if i%2 else "B"},
                     "stimuli":"Example survey stimulus", "prompt":"Which option?",
                     "response": 1 if i%2 else 0, "condition_num":i%2})
    p = tmp_path / "data.jsonl"
    p.write_text("".join(json.dumps(x)+"\n" for x in rows))
    model, report = tmp_path / "m.joblib", tmp_path / "report.json"
    out = train(p, model, report)
    assert out["evaluated_groups"] == 1
    assert predict(normalize(rows[0]), model)["response"] in ("0", "1")
