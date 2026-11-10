"""Usage: python -m socsci_agents.multi_brand_cli --brand Celsius --price-change 10"""
import argparse
import json
from .energy_market import load_personas
from .multi_brand import load_brand_catalog, compare_brands, simulate_brand, sweep_brand, export_rows_csv


def main():
    p=argparse.ArgumentParser(description='Synthetic multi-brand energy-drink scenario experiments')
    p.add_argument('--personas',default='data/energy_personas_synthetic.csv')
    p.add_argument('--brand',default='all',help='Brand name or all')
    p.add_argument('--price-change',type=float,default=0)
    p.add_argument('--budget-change',type=float,default=0)
    p.add_argument('--flavor-appeal',type=float,default=0)
    p.add_argument('--marketing-lift',type=float,default=0)
    p.add_argument('--competitor-discount',type=float,default=0)
    p.add_argument('--stockout',type=float,default=0)
    p.add_argument('--sweep',action='store_true')
    p.add_argument('--csv',default=None)
    a=p.parse_args()
    personas=load_personas(a.personas)
    scenario=dict(price_change_pct=a.price_change,budget_change_pct=a.budget_change,
                  flavor_appeal_pct=a.flavor_appeal,marketing_lift_pct=a.marketing_lift,
                  competitor_discount_pct=a.competitor_discount,stockout_pct=a.stockout)
    if a.brand == 'all':
        if a.sweep: p.error('--sweep requires --brand')
        result=compare_brands(personas,scenario)
    elif a.sweep:
        result=sweep_brand(personas,a.brand)
    else:
        result=simulate_brand(personas,a.brand,scenario)
    if a.csv:
        if not isinstance(result,list): p.error('--csv requires --brand all or --sweep')
        print(f'Wrote {export_rows_csv(result,a.csv)}')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
