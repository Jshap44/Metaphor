"""Command line workflow."""
import argparse
import json
from pathlib import Path
from .data import download_sample, inspect, normalize
from .model import train, predict
from .agent import SurveyAgent


def main():
    parser = argparse.ArgumentParser(description="SocSci210 experimental agent workflow")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("download", help="Stream a sample of actual Hugging Face data")
    p.add_argument("--output", default="data/real_sample.jsonl")
    p.add_argument("--max-rows", type=int, default=10000)
    p = sub.add_parser("inspect")
    p.add_argument("--data", default="data/demo_synthetic.jsonl")
    p = sub.add_parser("train")
    p.add_argument("--data", default="data/demo_synthetic.jsonl")
    p.add_argument("--model", default="artifacts/models.joblib")
    p.add_argument("--report", default="artifacts/metrics.json")
    p.add_argument("--min-rows", type=int, default=20)
    p = sub.add_parser("predict")
    p.add_argument("--row", required=True, help="Path to a single-row JSON object")
    p.add_argument("--model", default="artifacts/models.joblib")
    p = sub.add_parser("agent")
    p.add_argument("--row", default="data/example_input.json")
    p.add_argument("--model", default="artifacts/models.joblib")
    args = parser.parse_args()
    if args.cmd == "download":
        print(f"Downloaded {download_sample(args.output, args.max_rows)} rows to {args.output}")
    elif args.cmd == "inspect":
        print(json.dumps(inspect(args.data), indent=2))
    elif args.cmd == "train":
        print(json.dumps(train(args.data, args.model, args.report, args.min_rows), indent=2))
    else:
        row = normalize(json.loads(Path(args.row).read_text(encoding="utf-8")))
        if args.cmd == "predict":
            print(json.dumps(predict(row, args.model), indent=2))
        else:
            agent = SurveyAgent(persona=row["demographic"])
            print(json.dumps(agent.react(row["stimuli"], row["prompt"],
                                         predictor=lambda r: predict(r, args.model), row=row), indent=2))

if __name__ == "__main__":
    main()
