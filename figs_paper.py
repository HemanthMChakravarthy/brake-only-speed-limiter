import numpy as np, pandas as pd, matplotlib, glob
matplotlib.use('Agg'); import matplotlib.pyplot as plt
import bsl_sim3 as S
from bsl_sim3 import simulate, V_REF
plt.rcParams.update({'font.size':9,'font.family':'serif','axes.grid':True,'grid.alpha':.3,'savefig.dpi':300})
O='out_paper/'
COL={'PI':'tab:blue','RB':'tab:orange','FFPI':'tab:green','PROP1':'tab:purple','PROP3':'tab:red'}
LAB={'PI':'PI','RB':'Rule-based','FFPI':'FF+PI','PROP1':'Adaptive FF+PI (no realloc.)','PROP3':'Proposed'}
# --- Fig A: reverse low-mu time series
o=np.ones(1);prm=dict(mf=o.copy(),Gmax=np.array([.30]),A=0*o,ph=np.zeros((1,3)),mu=np.array([.42]),kbf=o.copy(),tau=.1*o,td=.04*o,kptf=o.copy(),abias=0*o)
R={}
for k in ['PI','RB','FFPI','PROP1','PROP3']:
    S.SLIP['re']=0.04; R[k]=simulate(k,prm,direction=-1,seed=1,Qg=.15,db=1.0)
f,ax=plt.subplots(4,1,figsize=(7,8.2),sharex=True);t=R['PI']['t']
ax[0].plot(t,100*R['PI']['grade'][:,0],'k');ax[0].set_ylabel('Grade [%]')
for k,r in R.items():
    lw=1.6 if k=='PROP3' else .9
    ax[1].plot(t,r['v'][:,0]*3.6,c=COL[k],lw=lw,label=LAB[k])
    ax[2].plot(t,np.maximum(np.abs(r['kf'][:,0]),np.abs(r['kr'][:,0])),c=COL[k],lw=lw)
ax[3].plot(t,R['PROP3']['phi'][:,0],c=COL['PROP3'],lw=1.6,label='Proposed: front share $\\phi$');ax[3].axhline(.65,ls='--',c='k',lw=.8,label='Fixed hydraulic bias 0.65')
ax[1].axhline(V_REF*3.6,ls='--',c='k',lw=.7);ax[1].set_ylabel('Speed [km/h]');ax[1].legend(fontsize=7,ncol=2)
ax[2].set_ylabel('Max |wheel slip| [-]');ax[3].set_ylabel('Front brake share [-]');ax[3].set_xlabel('Time [s]');ax[3].legend(fontsize=7)
f.tight_layout();f.savefig(O+'fig3_reverse_lowmu_timeseries.png');plt.close(f)
# --- Fig B: MC reverse boxplots
def load(k):
    if k=='FFPI': return pd.read_csv('out_v4/mc_FFPI_rena_rev.csv')
    if k=='PROP3': return pd.read_csv('out_v4/mc_PROP3_re0.04_rev.csv')
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(O+f'mc_{k}_rev_*.csv'))]).reset_index(drop=True)
D={k:load(k) for k in ['PI','RB','FFPI','PROP1','PROP3']}
feas=D['FFPI'].margin>1.05
f,ax=plt.subplots(1,4,figsize=(12,3.4))
for a,(m,l) in zip(ax,[('rms_err_kph','RMS speed error [km/h]'),('max_speed_kph','Max speed [km/h]'),('lock_time_s','Wheel-lock time [s]'),('p_activity','Pressure activity [bar/s]')]):
    a.boxplot([D[k][m][feas.values] for k in D],labels=['PI','RB','FF+PI','Adapt.','Prop.'],showfliers=True,flierprops=dict(markersize=2))
    a.set_title(l,fontsize=9)
    if m=='max_speed_kph': a.set_yscale('log')
f.suptitle(f'Reverse descent, Monte Carlo N={feas.sum()}');f.tight_layout();f.savefig(O+'fig4_mc_reverse.png');plt.close(f)
rows=[]
for k,d in D.items():
    x=d[feas.values];rows.append(dict(controller=LAB[k],rms_mean=x.rms_err_kph.mean(),rms_p95=x.rms_err_kph.quantile(.95),vmax_mean=x.max_speed_kph.mean(),
      vmax_p95=x.max_speed_kph.quantile(.95),vmax_max=x.max_speed_kph.max(),n_lock=(x.lock_time_s>.5).sum(),jerk_p95=x.peak_jerk.quantile(.95),act=x.p_activity.mean()))
pd.DataFrame(rows).round(3).to_csv(O+'table_mc_reverse.csv',index=False);print(pd.DataFrame(rows).round(3).to_string())
# --- Fig C: threshold + margin (fixed layout)
f,ax=plt.subplots(1,3,figsize=(12,3.8))
for k,mk in [('FFPI','o'),('PROP3','^')]:
    x=D[k][feas.values];ax[0].scatter(x.margin,x.max_speed_kph,s=8,c=COL[k],marker=mk,label=LAB[k],alpha=.7)
x=pd.read_csv('out_v4/mc_PROP3_re0.06_rev.csv')[feas.values];ax[0].scatter(x.margin,x.max_speed_kph,s=8,c='tab:gray',marker='s',label='Proposed, threshold 0.06',alpha=.6)
ax[0].set_xscale('log');ax[0].set_xlabel('Friction margin $\\mu\\cos\\theta/\\sin\\theta$ [-]');ax[0].set_ylabel('Max speed [km/h]');ax[0].set_title('(a) Reverse runaway vs. margin',fontsize=9);ax[0].legend(fontsize=7)
T=pd.read_csv('out_v4/summary_realloc_threshold.csv');A=T[T.subset.str.startswith('all')];xx=np.arange(3);th=[.06,.05,.04]
for i,(d,c,l) in enumerate([('fwd','tab:blue','forward'),('rev','tab:red','reverse')]):
    s=A[A.dir==d].set_index('re').loc[th];ax[1].bar(xx+i*.38-.19,s.n_lock,.36,color=c,label=l);ax[2].bar(xx+i*.38-.19,s.sw,.36,color=c,label=l)
for a,t in [(ax[1],'(b) Runs locked > 0.5 s'),(ax[2],'(c) Reallocation triggers [1/s]')]:
    a.set_xticks(xx);a.set_xticklabels([str(v) for v in th]);a.set_xlabel('Reallocation threshold $\\kappa_{re}$ [-]');a.set_title(t,fontsize=9);a.legend(fontsize=7)
f.tight_layout();f.savefig(O+'fig5_threshold_margin.png');plt.close(f)
print('figs ok')
