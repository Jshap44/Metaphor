"""Unified reproducible research CLI."""
import argparse
import json
from pathlib import Path
from .genai_research import (import_survey_csv,save_survey_jsonl,load_survey_jsonl,build_demo_survey,
    run_episodes,aggregate_episodes,statistical_holdout,compare_methods_holdout,interview_to_consumer)
from .integration import load_profiles

def main():
    ap=argparse.ArgumentParser(description='Consumer GenAI experiments (simulated ≠ real purchases)')
    ap.add_argument('--survey-csv',help='Google Forms CSV with real survey responses')
    ap.add_argument('--survey-jsonl',help='Previously imported survey')
    ap.add_argument('--interviews',action='store_true',help='Use teammates interview profiles instead')
    ap.add_argument('--demo',action='store_true',help='Use clearly synthetic demonstration data')
    ap.add_argument('--mode',choices=('offline','llm'),default='offline')
    ap.add_argument('--experiment',choices=('episodes','evaluate','compare'),default='episodes')
    ap.add_argument('--price-change',type=float,default=25)
    ap.add_argument('--budget-change',type=float,default=0)
    ap.add_argument('--flavor-appeal',type=float,default=0)
    ap.add_argument('--stockout',type=float,default=0)
    ap.add_argument('--episodes',type=int,default=3)
    ap.add_argument('--memory',action='store_true')
    ap.add_argument('--model',default=None)
    ap.add_argument('--max-calls',type=int,default=20)
    ap.add_argument('--max-consumers',type=int,default=20)
    ap.add_argument('--output',default='output/genai_experiment.json')
    args=ap.parse_args()
    if sum(bool(x) for x in (args.survey_csv,args.survey_jsonl,args.interviews,args.demo))!=1:
        ap.error('Choose one input: --survey-csv, --survey-jsonl, --interviews, or --demo')
    if args.survey_csv:
        consumers=import_survey_csv(args.survey_csv)
        save_survey_jsonl(consumers,'data/survey_imported.jsonl')
    elif args.survey_jsonl: consumers=load_survey_jsonl(args.survey_jsonl)
    elif args.interviews: consumers=[interview_to_consumer(p) for p in load_profiles('personas')]
    else: consumers=build_demo_survey()
    if args.experiment=='evaluate': result=statistical_holdout(consumers)
    elif args.experiment=='compare':result=compare_methods_holdout(consumers,mode=args.mode,memory=args.memory,max_calls=args.max_calls,model=args.model)
    else:
        scenario={'price_change_pct':args.price_change,'budget_change_pct':args.budget_change,
                  'flavor_appeal_pct':args.flavor_appeal,'stockout_pct':args.stockout}
        records=run_episodes(consumers[:args.max_consumers],scenario,mode=args.mode,episodes=args.episodes,
                             memory_enabled=args.memory,max_calls=args.max_calls,model=args.model)
        result={'scenario':scenario,'summary':aggregate_episodes(records),'records':records}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','test_results')},indent=2)[:4000]);print('Saved:',path)
if __name__=='__main__':main()
