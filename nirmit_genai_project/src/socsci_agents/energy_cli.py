import argparse
import json
from pathlib import Path
from .energy_market import generate_personas,save_personas,load_personas,simulate,summarize,sensitivity_grid,example_interview

def main():
    p=argparse.ArgumentParser(description='Energy drink market simulation (synthetic assumptions)')
    s=p.add_subparsers(dest='command',required=True)
    g=s.add_parser('generate');g.add_argument('--n',type=int,default=600);g.add_argument('--seed',type=int,default=42);g.add_argument('--output',default='data/energy_personas_synthetic.csv')
    x=s.add_parser('simulate');x.add_argument('--input',default='data/energy_personas_synthetic.csv');x.add_argument('--output',default='artifacts/energy_simulation.json');x.add_argument('--price-change',type=float,default=25);x.add_argument('--budget-change',type=float,default=-15);x.add_argument('--health-risk',type=float,default=0);x.add_argument('--stockout',type=float,default=0);x.add_argument('--competitor-discount',type=float,default=0);x.add_argument('--months',type=int,default=6)
    e=s.add_parser('interview');e.add_argument('--output',default='data/interview_example.json')
    t=s.add_parser('sensitivity');t.add_argument('--input',default='data/energy_personas_synthetic.csv');t.add_argument('--output',default='artifacts/sensitivity_grid.json')
    a=p.parse_args()
    if a.command=='generate':
        save_personas(generate_personas(a.n,a.seed),a.output);print('Saved synthetic sample:',a.output);return
    if a.command=='interview':
        result=example_interview()
    elif a.command=='simulate':
        result=summarize(simulate(load_personas(a.input),dict(price_change_pct=a.price_change,budget_change_pct=a.budget_change,health_risk=a.health_risk,stockout_pct=a.stockout,competitor_discount_pct=a.competitor_discount,months=a.months)))
    else: result=sensitivity_grid(load_personas(a.input))
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2),encoding='utf-8');print('Saved:',out)
if __name__=='__main__':main()
