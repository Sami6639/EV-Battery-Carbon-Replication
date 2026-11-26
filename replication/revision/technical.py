"""Four reviewer checks. Run after extensions.py from the package root."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

out=Path(__file__).resolve().parent
src=out.parent/'inputs'
def rd(name):return pd.read_parquet(src/(name+'.parquet'))
def save(name,rows):pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False)
pack=77.413145
km=10729.496448
eta=rd('p14_charging_conversion').query("scenario_id=='central_efficiency'").charging_efficiency_fraction.iloc[0]
base=.270072194/1.609344*eta
loss=pd.read_csv(out/'fastsim.csv').iloc[-1].fresh_storage_loss_kwh_per_km
p=pd.read_csv(out/'pairs.csv').sort_values(['cell_key','timestamp_s'])
excess=loss*(p.r10_rel-1).clip(lower=0)
cap=pack*.9*p.q
rc=cap/base
rj=cap/(base+excess)
rows=[]
for dist in sorted(set(range(0,551))|{201.1744,540.6216,59.8985}):
 rows.append(dict(km=dist,capacity_only=int((rc<dist).sum()),joint=int((rj<dist).sum()),required_q_at_fresh_resistance=dist*base/(pack*.9)))
curve=pd.DataFrame(rows);save('duty_curve',rows)
wrows=[]
for name,col in [('nhts_trip_observations','trip_distance_km'),('nhts_long_distance_observations','long_distance_km')]:
 a=pd.read_csv(src/(name+'.csv'))
 for dist in [201.1744,400,540.6216]:
  wrows.append(dict(source=name,km=dist,weighted_share_at_or_below=a.loc[a[col]<=dist,'survey_weight'].sum()/a.survey_weight.sum()))
save('survey_position',wrows)
fig,(a,b)=plt.subplots(2,1,figsize=(6.2,4.2),sharex=True,gridspec_kw={'height_ratios':[2,1]})
a.plot(curve.km,curve.joint,label='Capacity and resistance',c='#006b75',lw=2.5);a.plot(curve.km,curve.capacity_only,'--',label='Capacity alone',c='#9c531e',lw=1.25);a.set_ylabel('Checks falling short');a.legend(frameon=False,fontsize=8)
b.plot(curve.km,curve.joint-curve.capacity_only,c='#006b75');b.set(ylabel='Additional checks',xlabel='Uninterrupted distance (km)')
for ax in [a,b]:
 ax.axvline(400,color='gray',lw=.8,ls=':');ax.spines[['top','right']].set_visible(False)
fig.tight_layout();fig.savefig(out/'figure2.png',dpi=230);plt.close(fig)
s=rd('p14_vehicle_survival').query("survival_scenario=='central' and current_vehicle_age_years==8").set_index('years_after_conditioning').conditional_survival
grid=rd('p14_grid_pathways').query("geography_level=='US_LOAD_WEIGHTED' and pathway_role=='PRIMARY_AVERAGE_CI'").pivot(index='calendar_year',columns='scenario',values='grid_ci_gco2e_per_kwh')/1000
mp=rd('p14_battery_manufacturing_pathways').query("benchmark_type=='PROSPECTIVE'").set_index(['calendar_year','chemistry','pathway']).pack_ghg_kgco2e_per_kwh
rows=[]
for old in pd.read_csv(out/'delay.csv').itertuples():
 d=old.delay
 M=lambda t:pack*mp.loc[2025+t,'NMC811',old.path]
 for h in [0,.05,.10,.25,.50,1]:
  # At the start of each year a still-operating old pack may require replacement.
  prob=np.array([h*(1-h)**t for t in range(d)]+[(1-h)**d])
  assert np.isclose(sum(prob),1)
  cleaner=sum(prob[t]*(M(0)-M(t)) for t in range(d+1))
  retire=sum(prob[t]*(1-s[t])*M(t) for t in range(d+1))
  extra=sum(km*s[t]*(1-h)**(t+1)*grid.loc[2025+t,old.grid]*loss*(old.r10-1)/eta for t in range(d))
  delta=cleaner+retire-extra
  if h==0:assert abs(delta-old.immediate_minus_delayed_kg)<1e-7
  if h==1:assert abs(delta)<1e-7
  rows.append(dict(delay=d,h=h,grid=old.grid,path=old.path,r=old.r10,cleaner_production=cleaner,retirement=retire,extra_operation=extra,net=delta))
save('early_replacement',rows)
# Exact piecewise-linear expanded-system contrast at continuous displacement f.
circ=pd.read_csv(out/'circular.csv')
keys=[c for c in circ if c not in ('displacement','immediate_minus_delay','immediate_minus_keep')]
rows=[]
for key,group in circ.groupby(keys):
 k=dict(zip(keys,key));y,d,g,path=[k[n] for n in ['year','delay','grid','path']]
 def term(t,q,weight):
  capacity=pack*q*.8
  slope=capacity*.5*mp.loc[y+t,'LFP',path]
  cost=k['repurposing_kg']+capacity*100*(1/k['stationary_eff']-1/.9)*grid[g].loc[y+t:y+t+5].sum()
  return [weight,slope,cost]
 terms=[term(0,.8,-1),term(d,k['q_delayed_removal'],s[d])]
 for t in range(1,11):
  w=s[t-1]-s[t] if t<10 else s[9]
  terms.extend([term(t,.80,-w),term(t,k['q_old_exit'] if t<=d else k['q_delayed_new_exit'],w)])
 w,m,c=np.array(terms).T
 intercept=group.loc[group.displacement.eq(0),'immediate_minus_delay'].iloc[0]
 def value(f):return intercept+w@np.maximum(0,m*f-c)
 for rec in group.itertuples():assert abs(value(rec.displacement)-rec.immediate_minus_delay)<1e-7
 knots=np.unique(np.r_[0,1,np.clip(c/m,0,1)])
 roots=[]
 for left,right in zip(knots[:-1],knots[1:]):
  l,r=value(left),value(right)
  if l*r<0:roots.append(left+(right-left)*l/(l-r))
  if l==0:roots.append(left)
 if value(1)==0:roots.append(1)
 rows.append(dict(**k,first_root=min(roots,default=np.nan),roots=len(set(roots)),delta_at_099=value(.99),delta_at_100=value(1),minimum=min(map(value,knots))))
save('storage_thresholds',rows)
# Match delivered pack energy (stored-energy basis) using a clearly labelled loss proxy.
rows=[]
for adj in [0,.5,1,2]:
 energy=.13352505+adj*loss
 fail=cap/(energy+excess)<400
 rows.append(dict(loss_multiplier=adj,stored_Wh_km=energy*1000,fresh_range=pack*.9/energy,checks_failing=int(fail.sum()),cells=p.loc[fail,'cell_key'].nunique()))
save('id3_boundary',rows)
p['next']=p.groupby('cell_key').r10_rel.shift(-1)
p=p.dropna(subset=['next'])
p['current_above']=p.r10_rel>1.1238;p['next_above']=p['next']>1.1238
z=p.groupby(['band','current_above','next_above']).size().unstack(['current_above','next_above'],fill_value=0)
z.columns=['above_%d_to_%d'%(a,b) for a,b in z.columns];z.to_csv(out/'ceiling_transitions.csv')
