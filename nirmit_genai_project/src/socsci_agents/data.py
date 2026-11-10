"""Load, clean, split and sample SocSci210 without loading 2.9M rows into RAM."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HF_DATASET = "socratesft/SocSci210"
COLUMNS = ("sample_id", "participant", "demographic", "stimuli", "response",
           "condition_num", "task_num", "prompt", "reasoning", "study_id")


def normalize(row):
    result = {k: row.get(k) for k in COLUMNS}
    dem = result["demographic"]
    if isinstance(dem, str):
        try:
            dem = json.loads(dem)
        except ValueError:
            dem = {}
    result["demographic"] = dem if isinstance(dem, dict) else {}
    for k in ("study_id", "stimuli", "prompt", "reasoning"):
        result[k] = str(result[k] or "")
    result["response"] = str(result["response"])
    return result


def group_key(row):
    # Response scales are not comparable across different tasks or studies.
    return f'{row["study_id"]}::{row["task_num"]}'


def split_name(row, seed=42, val_fraction=0.2):
    # Same participant within study goes to same split; prevents participant leakage.
    key = f'{seed}|{row["study_id"]}|{row["participant"]}'
    fraction = int(hashlib.sha256(key.encode()).hexdigest()[:12], 16) / float(16**12)
    return "val" if fraction < val_fraction else "train"


def read_jsonl(path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield normalize(json.loads(line))


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(normalize(row), ensure_ascii=False) + "\n")
            n += 1
    return n


def download_sample(output, max_rows=10000, seed=42):
    """Streaming remote download. Requires internet only when invoked by user."""
    from datasets import load_dataset
    stream = load_dataset(HF_DATASET, split="train", streaming=True)
    def limited():
        count = 0
        for row in stream:
            # Shuffle isn't guaranteed on remote; use reproducible stream shuffle buffer.
            yield row
            count += 1
            if count >= max_rows:
                break
    return write_jsonl(output, limited())


def inspect(path):
    counts, label_counts = Counter(), Counter()
    n = 0
    for row in read_jsonl(path):
        n += 1
        counts[group_key(row)] += 1
        label_counts[row["response"]] += 1
    return {"rows": n, "study_task_groups": len(counts),
            "largest_groups": counts.most_common(10),
            "largest_labels_globally_NOT_comparable": label_counts.most_common(10)}
