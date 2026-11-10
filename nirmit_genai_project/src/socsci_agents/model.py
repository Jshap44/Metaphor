"""Group-aware supervised response prediction with honest holdout metrics."""
import json
from collections import Counter, defaultdict
from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score
from .data import read_jsonl, group_key, split_name


def features(row):
    result = {"text:stimuli": (row.get("stimuli") or "")[:2000],
              "text:prompt": (row.get("prompt") or "")[:2000],
              "condition": str(row.get("condition_num"))}
    dem = row.get("demographic") or {}
    for k, v in dem.items():
        if v is None or isinstance(v, (list, dict)):
            continue
        result[f"dem:{k}"] = str(v)
    return result


def vectorize_fields(rows):
    # DictVectorizer handles arbitrary demographics; TF-IDF of stimuli adds text signal.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.sparse import hstack
    dict_rows = []
    for row in rows:
        item = features(row)
        item.pop("text:stimuli")
        item.pop("text:prompt")
        dict_rows.append(item)
    dv = DictVectorizer()
    xd = dv.fit_transform(dict_rows)
    docs = [((r.get("stimuli") or "") + " " + (r.get("prompt") or ""))[:4000] for r in rows]
    tv = TfidfVectorizer(max_features=3000, min_df=1, ngram_range=(1,2), stop_words="english")
    xt = tv.fit_transform(docs)
    return dv, tv, hstack([xd, xt], format="csr")


def transform(rows, dv, tv):
    from scipy.sparse import hstack
    dictionaries = []
    for row in rows:
        item = features(row)
        item.pop("text:stimuli")
        item.pop("text:prompt")
        dictionaries.append(item)
    docs = [((r.get("stimuli") or "") + " " + (r.get("prompt") or ""))[:4000] for r in rows]
    return hstack([dv.transform(dictionaries), tv.transform(docs)], format="csr")


def train(data_path, model_path, report_path, min_rows=20, max_classes=30, seed=42):
    """Train one classification model per study/task; exclude unlearnable scales."""
    groups = defaultdict(list)
    for row in read_jsonl(data_path):
        groups[group_key(row)].append(row)
    models, reports = {}, []
    for key, rows in sorted(groups.items()):
        if len(rows) < min_rows:
            continue
        classes = Counter(r["response"] for r in rows)
        if len(classes) > max_classes:
            continue
        train_rows = [r for r in rows if split_name(r, seed) == "train"]
        val_rows = [r for r in rows if split_name(r, seed) == "val"]
        if len(train_rows) < 8 or len(val_rows) < 3:
            continue
        dv, tv, _ = vectorize_fields(train_rows)
        xtr = transform(train_rows, dv, tv)
        ytr = [r["response"] for r in train_rows]
        if len(set(ytr)) < 2:
            # Majority predictor when only one class is in training data.
            clf = DummyClassifier(strategy="most_frequent")
        else:
            clf = LogisticRegression(max_iter=500, random_state=seed, class_weight="balanced")
        clf.fit(xtr, ytr)
        yval = [r["response"] for r in val_rows]
        pred = clf.predict(transform(val_rows, dv, tv))
        majority = Counter(ytr).most_common(1)[0][0]
        reports.append({"group": key, "n_train": len(train_rows), "n_val": len(val_rows),
                        "n_classes_train": len(set(ytr)), "accuracy": float(accuracy_score(yval, pred)),
                        "macro_f1": float(f1_score(yval, pred, average="macro", zero_division=0)),
                        "majority_baseline_accuracy": float(np.mean(np.array(yval) == majority))})
        models[key] = {"classifier": clf, "dict_vectorizer": dv, "text_vectorizer": tv,
                       "n_train": len(train_rows)}
    model_path, report_path = Path(model_path), Path(report_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"models": models, "seed": seed}, model_path)
    summary = {"evaluated_groups": len(reports), "sampled_rows": sum(map(len, groups.values())),
               "mean_group_accuracy": float(np.mean([r["accuracy"] for r in reports])) if reports else None,
               "mean_group_macro_f1": float(np.mean([r["macro_f1"] for r in reports])) if reports else None,
               "note": "Unweighted means over eligible study/task groups; synthetic-data results are not scientific evidence.",
               "groups": reports}
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def predict(row, model_path):
    bundle = joblib.load(model_path)  # Only load trusted model files.
    key = group_key(row)
    if key not in bundle["models"]:
        raise ValueError(f"No trained model for {key}. Available: {list(bundle['models'])[:10]}")
    m = bundle["models"][key]
    X = transform([row], m["dict_vectorizer"], m["text_vectorizer"])
    label = str(m["classifier"].predict(X)[0])
    probabilities = (m["classifier"].predict_proba(X)[0] if hasattr(m["classifier"], "predict_proba") else None)
    return {"response": label, "group": key, "probability": float(max(probabilities)) if probabilities is not None else None,
            "warning": "Predicted response, not an observed human survey result."}
