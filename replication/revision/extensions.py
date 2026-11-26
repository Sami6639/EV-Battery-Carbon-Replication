from functools import lru_cache
from pathlib import Path
import numpy as np
import pandas as pd
from itertools import product
out=Path(__file__).resolve().parent
d=Path.cwd()/'inputs'
def rd(s):return pd.read_parquet(d/(s+'.parquet'))
p=pd.read_csv(out/'pairs.csv')
b=pd.read_csv(out/'fastsim.csv')
profile=rd('representative_bev_baseline')
sf=rd('p14_vehicle_survival')
grid=rd('p14_grid_pathways').query("geography_level=='US_LOAD_WEIGHTED' and pathway_role=='PRIMARY_AVERAGE_CI'").pivot(index='calendar_year',columns='scenario',values='grid_ci_gco2e_per_kwh')/1000
mp=rd('p14_battery_manufacturing_pathways').query("benchmark_type=='PROSPECTIVE'").set_index(['calendar_year','chemistry','pathway']).pack_ghg_kgco2e_per_kwh
eta=rd('p14_charging_conversion').query("scenario_id=='central_efficiency'").charging_efficiency_fraction.iloc[0]
pack=77.413145
km=10729.496448
loss=b.iloc[-1].fresh_storage_loss_kwh_per_km
# Fixed power at a nominal open-circuit voltage, positive for discharge.
rows=[]
for cycle,w in [('HWFET',.45),('UDDS',.55)]:
 t=profile.query('drive_cycle==@cycle').sort_values('time_s')
 dt=t.time_s.diff().fillna(0).values
 pw=t.hv_terminal_power_w.values
 base=b.query('drive_cycle==@cycle').iloc[0]
 V=394.2
 r=base.fresh_storage_loss_kwh*3.6e6/sum((pw/V)**2*dt)
 for temp,mult in [('reference',1.),('cold_sensitivity',2.)]:
  for rel in [1,1.1238,1.5,2.0823]:
   def current(res):
    disc=V**2-4*res*pw
    assert min(disc)>0
    return 2*pw/(V+np.sqrt(disc))
   a=current(r*rel*mult); f=current(r*mult)
   inc=sum(dt*(a*a*r*rel*mult-f*f*r*mult))/3600/base.distance_km
   rows.append([cycle,w,temp,rel,inc,(V-a*r*rel*mult).min(),max(abs(a))])
powr=pd.DataFrame(rows,columns=['cycle','weight','temperature_case','r','increment_Wh_km','min_terminal_V','peak_current_A'])
powr.to_csv(out/'power.csv',index=False)
# Test legacy R endpoint at the next measured check; never use a future state in screening current rows.
n=p.groupby('cell_key').r10_rel.shift(-1); nxt=p[n.notna()].copy();nxt['next_r']=n[n.notna()]
nxt['inside_original_upper']=nxt.next_r.le(1.1238)
nxt.groupby('band').inside_original_upper.agg(['count','sum','mean']).to_csv(out/'endpoint.csv')
# Common vehicle withdrawal horizon with matched stationary storage service using system expansion.
# Conditional capacity at removal is stipulated, not inferred from elapsed years.
@lru_cache(maxsize=None)
def credit(year,q,path,gridcase,displacement,processing,eff_sl):
 cap=pack*q*.8
 # lifespan-equivalent displaced capacity: 600 versus 1200 equivalent full discharges
 avoided=displacement*cap*.5*mp.loc[year,'LFP',path]
 # 100 discharged equivalent cycles/year for six years; reference and second use serve equal output.
 incremental=sum(cap*100*(1/eff_sl-1/.90)*grid.loc[year+k,gridcase] for k in range(6))
 return max(0.,avoided-processing-incremental) # choose conventional storage if diversion has no benefit
rows=[]
for y,age,delay,g,path,displ,proc,eff,qdel,qterm,qnew in product([2025,2035],[8],[1,3,5],grid.columns,['SPS','SDS'],[0,.5,1],[100,300],[.85,.90],[.70,.78],[.65,.75],[.80,.95]):
 s=sf.query("survival_scenario=='central' and current_vehicle_age_years==@age").set_index('years_after_conditioning').conditional_survival
 # Planned retirement after ten years, or earlier scrappage. Everyone active at t=9 exits by t=10.
 ex=np.array([s[t-1]-s[t] if t<10 else s[9] for t in range(1,11)])
 assert abs(sum(ex)-1)<1e-8
 # New packs at earlier vs later installation can have different residual state: both evaluated with same credit method.
 oldnow=credit(y,.80,path,g,displ,proc,eff)
 now=pack*mp.loc[y,'NMC811',path]-oldnow
 later=s[delay]*(pack*mp.loc[y+delay,'NMC811',path]-credit(y+delay,qdel,path,g,displ,proc,eff))
 keep=0.
 for t,prob in enumerate(ex,1):
  now-=prob*credit(y+t,.80,path,g,displ,proc,eff)
  later-=prob*credit(y+t,qterm if t<=delay else qnew,path,g,displ,proc,eff)
  keep-=prob*credit(y+t,qterm,path,g,displ,proc,eff)
 for t in range(10):
  old_extra=km*s[t]*grid.loc[y+t,g]*loss*.5/eta
  keep+=old_extra
  if t<delay:later+=old_extra
 rows.append((y,delay,g,path,displ,proc,eff,qdel,qterm,qnew,now-later,now-keep))
cols=['year','delay','grid','path','displacement','repurposing_kg','stationary_eff','q_delayed_removal','q_old_exit','q_delayed_new_exit','immediate_minus_delay','immediate_minus_keep']
pd.DataFrame(rows,columns=cols).to_csv(out/'circular.csv',index=False)
# Observed range threshold and repeat-measure diagnostics.
e_atb=.270072194/1.609344*eta
r_old=1.5; r_after=1.1
range_old=pack*.90*.8/(e_atb+loss*(r_old-1)); range_new=pack*.90/e_atb
service=[]
for q in [.84,.86,.9]:
 for fraction in [.1,.25]:
  for process in [50,200]:
   for path in ['SPS','SDS']:
    manuf=pack*mp.loc[2025,'NMC811',path]
    repair=fraction*manuf+process
    deficit=km*sum(sf.query("survival_scenario=='central' and current_vehicle_age_years==8").set_index('years_after_conditioning').conditional_survival[t]*grid.loc[2025+t,'MidCase'] for t in range(10))*loss*(r_after-1)/eta
    service.append([q,fraction,process,path,range_old,range_new,pack*.9*q/(e_atb+loss*(r_after-1)),manuf-repair-deficit])
pd.DataFrame(service,columns=['tested_q_after','module_fraction','process_kg','path','old_range','new_range','repair_range','full_minus_repair_kg_before_end_of_life']).to_csv(out/'repair.csv',index=False)
rows=[]
for capwindow,aux,range_km in product([.85,.90,.95],[0,20,40],[201.1744,400.,540.6216]):
 e=e_atb+aux/1000
 ran=pack*capwindow*p.q/(e+loss*(p.r10_rel-1).clip(lower=0))
 for leg in [1,2]:
  fails=ran.lt(range_km/leg)
  rows.append((capwindow,aux,range_km,leg,int(fails.sum()),p.loc[fails,'cell_key'].nunique(),pack*capwindow/e))
pd.DataFrame(rows,columns=['usable_window','extra_Wh_km','route_km','equal_legs','fail_checks','fail_cells','fresh_range_km']).to_csv(out/'routes.csv',index=False)
# Alternative allocation: only the vehicle share of new-pack embodied burden is assigned
# to mobility; no system-expansion or second-life credits in this accounting treatment.
rows=[]
for y,delay,g,path,cycles in product([2025,2035],[1,3,5],grid.columns,['SPS','SDS'],[0,300,600]):
 s=sf.query("survival_scenario=='central' and current_vehicle_age_years==8").set_index('years_after_conditioning').conditional_survival
 def vehicle_share(years):
  drive=years*km*e_atb
  future=pack*.8*.8*cycles
  return drive/(drive+future)
 delta=0.
 for t in range(1,11):
  prob=s[t-1]-s[t] if t<10 else s[9]
  delta+=prob*pack*mp.loc[y,'NMC811',path]*vehicle_share(t)
  if t>delay:delta-=prob*pack*mp.loc[y+delay,'NMC811',path]*vehicle_share(t-delay)
 delta-=sum(s[t]*km*grid.loc[y+t,g]*loss*.5/eta for t in range(delay))
 rows.append((y,delay,g,path,cycles,delta))
pd.DataFrame(rows,columns=['year','delay','grid','path','future_cycles','delta_kg']).to_csv(out/'allocation.csv',index=False)
