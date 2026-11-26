from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
out=Path(__file__).resolve().parent
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
p=pd.read_csv(out/'pairs.csv')
def done(fig,i):
 fig.tight_layout()
 fig.savefig(out/f'figure{i}.png',dpi=230,bbox_inches='tight')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(6.2,3.0));ax.axvspan(70,80,color='#f3e3c4');ax.scatter(p.q*100,p.r10_rel,s=5,alpha=.26,linewidth=0,c='#006b75');ax.set(xlabel='Capacity retained (% of same-cell baseline)',ylabel='10 ms resistance / baseline');done(fig,1)
fig,ax=plt.subplots(figsize=(6.2,2.7));labels=['Unadjusted cycle','ID.3 benchmark','ATB road reference'];x=pd.read_csv(out/'service.csv').query('km==400').set_index('model').loc[['lab','ID3','ATB'],'fail_checks'];bar=ax.barh(labels,x,color=['#a6c4c6','#518b91','#006b75']);ax.bar_label(bar,padding=4);ax.set(xlim=(0,1280),xlabel='Checks below 400 km (3,142 paired checks)');done(fig,2)
fig,ax=plt.subplots(figsize=(6.2,3.1));x=pd.read_csv(out/'circular.csv')
for y,offset,col,marker in [(2025,-.08,'#006b75','o'),(2035,.08,'#aa5928','s')]:
 a=x[x.year==y].groupby('delay').immediate_minus_delay.agg(['min','max']);idx=a.index+offset
 ax.vlines(idx,a['min'],a['max'],color=col,lw=3);ax.scatter(idx,a['min'],c=col,marker=marker,s=19,label=str(y));ax.scatter(idx,a['max'],c=col,marker=marker,s=19)
ax.axhline(0,color='black',lw=.75);ax.set(xticks=[1,3,5],xlim=(.5,5.5),xlabel='Replacement delay (years)',ylabel='Immediate − delayed (kg CO₂e)');ax.legend(frameon=False);done(fig,3)
fig,ax=plt.subplots(figsize=(6.2,2.9));a=pd.read_csv(out/'repair.csv');ranges=[a.old_range[0],*a.groupby('tested_q_after').repair_range.min(),a.new_range[0]];n=['Installed, 80%','Repair to 84%','Repair to 86%','Repair to 90%','Fresh pack'];ax.scatter(ranges,n,s=55,color='#006b75',zorder=3);ax.axvline(400,color='#aa5928',ls='--',label='Required duty');ax.set(xlim=(360,490),xlabel='Technical range (km)');ax.legend(frameon=False,loc='lower right');done(fig,4)
