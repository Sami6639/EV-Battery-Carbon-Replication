"""Run from workspace root. Inputs are the GitHub repository, the archived processed inputs and official Luh archives."""
from pathlib import Path
import sys
import hashlib
import numpy as np
import pandas as pd
root=Path.cwd()
out=root/'revision'
d=root/'inputs'
sys.path.insert(0,str(root/'ev'))
from src.degradation import p12_pipeline as p12
from src.vehicle_energy import p13_pipeline as p13
import yaml
p12.PROCESSED=d
p12.LUH_RAW=root/'raw'
for fn,digest in [('cell_eocv2.zip','81c10714570da82f99359d88b394d039f4d116f3bfb337e79d8bfdc370f7afb3'),('cell_plsv2.zip','fa2b4565de657db37102d9068a5b897862484b290da581602c9420e39ffe9301')]:
 assert hashlib.sha256((p12.LUH_RAW/fn).read_bytes()).hexdigest()==digest
def rd(s):return pd.read_parquet(d/(s+'.parquet'))
cond=p12._condition_map()
cap=p12.build_capacity_states(cond)
r=p12.build_resistance_states(cond,yaml.safe_load(open(root/'ev/src/degradation/p12_config.yaml')))
r=r[r.soc_nom.eq(50)]
pairs=[]
for cell, pulses in r.groupby('cell_key'):
 c=cap[cap.cell_key.eq(cell)][['timestamp_s','reconstructed_capacity_retention','num_cycles_checkup']].rename(columns={'timestamp_s':'cap_time','reconstructed_capacity_retention':'q'})
 x=pd.merge_asof(pulses.sort_values('timestamp_s'),c.sort_values('cap_time'),left_on='timestamp_s',right_on='cap_time',direction='nearest',tolerance=86400.)
 x['lag_hours']=(x.timestamp_s-x.cap_time)/3600
 pairs.append(x.dropna(subset=['q']).sort_values('lag_hours',key=lambda s:s.abs()).drop_duplicates('cap_time'))
p=pd.concat(pairs,ignore_index=True)
p=p[['cell_key','condition_id','timestamp_s','q','r10_rel','r1s_rel','lag_hours']].sort_values(['cell_key','timestamp_s'])
p['band']=pd.cut(p.q,[0,.7,.75,.8,.85,2],right=False)
def save(df,n):df.to_csv(out/(n+'.csv'),index=False)
save(p,'pairs')
save(p.groupby('band',observed=True).agg(checks=('q','size'),cells=('cell_key','nunique'),conditions=('condition_id','nunique'),min_q=('q','min'),median_r10=('r10_rel','median'),lag95h=('lag_hours',lambda s:s.abs().quantile(.95))).reset_index(),'bands')
profile,b=p13.run_fresh_fastsim(p13.load_config());save(b,'fastsim')
en=rd('p13_incremental_energy_penalty')
en['increment']=en.incremental_battery_side_kwh_per_km*en.drive_cycle.map({'UDDS':.55,'HWFET':.45})
energy=en.groupby(['conditional_extreme','resistance_specification','degradation_state_id','source_id','topology_id','cell_resistance_share','fresh_usable_window_fraction'],as_index=False).increment.sum()
sv=rd('p14_vehicle_survival').query("survival_scenario=='central' and current_vehicle_age_years==0").set_index('years_after_conditioning').conditional_survival
grid=rd('p14_grid_pathways').query("geography_level=='US_LOAD_WEIGHTED' and pathway_role=='PRIMARY_AVERAGE_CI'").pivot(index='calendar_year',columns='scenario',values='grid_ci_gco2e_per_kwh')/1000
mfg=rd('p14_battery_manufacturing_pathways').query("chemistry=='NMC811' and benchmark_type=='PROSPECTIVE'").pivot(index='calendar_year',columns='pathway',values='pack_ghg_kgco2e_per_kwh')*77.413145
eta=rd('p14_charging_conversion').query("scenario_id=='central_efficiency'").charging_efficiency_fraction.iloc[0]
km=10729.496448
trace=[]
for stress in [False,True]:
 e=energy.query('conditional_extreme==True') if stress else energy.query("conditional_extreme==False and resistance_specification=='10-ms'")
 row=e.loc[e.increment.idxmax()]
 for g in grid:
  s=sv.loc[:25].values
  trace.append(dict(stress=stress,grid=g,state=row.degradation_state_id,delta_Wh_km=1000*row.increment,km=km*s.sum(),eff=eta,weighted_grid_kg_kwh=np.average(grid[g],weights=s),total_extra_grid_kwh=km*s.sum()*row.increment/eta,kg=km*(s*grid[g]).sum()*row.increment/eta))
save(pd.DataFrame(trace),'original_savings')
base=b.iloc[-1].fresh_battery_side_kwh_per_km
loss=b.iloc[-1].fresh_storage_loss_kwh_per_km
atb=.270072194/1.609344*eta
# Constant service-demand sensitivity, same incremental resistive loss as the cycle.
feas=[]
for model,e in [('lab',base),('ATB',atb),('ID3',.13352505)]:
 for dist in [59.8985,201.1744,400,540.6216]:
  x=p.assign(feasible=77.413145*.9*p.q/(e+loss*(p.r10_rel-1).clip(lower=0))>=dist)
  feas.append(dict(model=model,km=dist,fresh_range=77.413145*.9/e,observations=len(x),pass_checks=x.feasible.sum(),fail_checks=(~x.feasible).sum(),cells_with_failure=x.loc[~x.feasible,'cell_key'].nunique()))
save(pd.DataFrame(feas),'service')
# Compare on common 10-year horizon for an age-eight vehicle at the decision.
sur=rd('p14_vehicle_survival').query("survival_scenario=='central' and current_vehicle_age_years==8").set_index('years_after_conditioning').conditional_survival
rows=[]
for delay in [1,3,5]:
 for g in grid:
  for path in mfg:
   avoided=mfg.at[2025,path]-sur[delay]*mfg.at[2025+delay,path]
   factor=sum(km*sur[t]*grid.at[2025+t,g]/eta for t in range(delay))
   # Same post-switch efficiency; persistence horizon is conditional.
   for r10 in [1.1238,1.5,2]:
    rows.append(dict(delay=delay,grid=g,path=path,r10=r10,avoided_production_kg=avoided,extra_operation_kg=loss*(r10-1)*factor,immediate_minus_delayed_kg=avoided-loss*(r10-1)*factor,break_even_extra_Wh_km=1000*avoided/factor))
save(pd.DataFrame(rows),'delay')
print('CAP',len(cap),'R',len(r),'paired',len(p),p.cell_key.nunique())
for n in ['bands','original_savings','service','delay']:print(n,pd.read_csv(out/(n+'.csv')).head(12).to_string(index=False))
