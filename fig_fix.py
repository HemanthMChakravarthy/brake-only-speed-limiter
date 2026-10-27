import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.size':9,'font.family':'serif','savefig.dpi':300})
O='out_paper/'
f0=pd.read_csv('out_v4/mc_FFPI_rena_rev.csv');feas=f0.margin>1.05
T=pd.read_csv('out_v4/summary_realloc_threshold.csv');A=T[T.subset.str.startswith('all')];xx=np.arange(3);th=[.06,.05,.04]
f,ax=plt.subplots(1,3,figsize=(12,3.8))
for a in ax: a.grid(alpha=.3)
for fn,c,mk,l in [('mc_FFPI_rena_rev.csv','tab:green','o','FF+PI'),('mc_PROP3_re0.06_rev.csv','tab:gray','s','Proposed, $\\kappa_{re}$ = 0.06'),('mc_PROP3_re0.04_rev.csv','tab:red','^','Proposed, $\\kappa_{re}$ = 0.04')]:
    x=pd.read_csv('out_v4/'+fn)[feas];ax[0].scatter(x.margin,x.max_speed_kph,s=9,c=c,marker=mk,label=l,alpha=.75)
ax[0].set_xscale('log');ax[0].set_xlabel('Friction margin $\\mu\\cos\\theta/\\sin\\theta$ [-]');ax[0].set_ylabel('Max speed [km/h]');ax[0].set_title('(a) Reverse runaway vs. friction margin',fontsize=9);ax[0].legend(fontsize=7)
for i,(d,c,l) in enumerate([('fwd','tab:blue','forward'),('rev','tab:red','reverse')]):
    s=A[A.dir==d].set_index('re').loc[th];ax[1].bar(xx+i*.38-.19,s.n_lock,.36,color=c,label=l);ax[2].bar(xx+i*.38-.19,s.sw,.36,color=c,label=l)
for a,t in [(ax[1],'(b) Runs with wheel lock > 0.5 s (of 393)'),(ax[2],'(c) Reallocation trigger events [1/s]')]:
    a.set_xticks(xx);a.set_xticklabels([str(v) for v in th]);a.set_xlabel('Reallocation threshold $\\kappa_{re}$ [-]');a.set_title(t,fontsize=9);a.legend(fontsize=7)
f.tight_layout();f.savefig(O+'fig5_threshold_margin.png');plt.close(f)
# architecture diagram
f,ax=plt.subplots(figsize=(10,3.6));ax.axis('off');ax.set_xlim(0,10);ax.set_ylim(0,3.6)
def box(x,y,w,h,t,fc):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.03',fc=fc,ec='k',lw=1));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=8)
def arr(x1,y1,x2,y2,t=''):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='->',lw=1));
    if t: ax.text((x1+x2)/2,(y1+y2)/2+.08,t,ha='center',fontsize=7)
box(0.1,2.5,1.6,0.8,'Wheel speeds\nLong. accel.','#eeeeee')
box(2.2,2.5,1.9,0.8,'Adaptive Kalman\ngrade estimator','#d6e6f5')
box(2.2,1.3,1.9,0.8,'RLS effective mass\n(confidence-blended)','#d6e6f5')
box(4.6,1.9,1.9,0.8,'Feedforward + PI\n+ pressure hysteresis','#fde2c8')
box(7.0,1.9,1.4,0.8,'Total pressure\ncommand $p^*$','#eeeeee')
box(7.0,0.3,2.0,0.9,'Slip layer: ABS-like cap\n+ direction-scheduled\nfront/rear reallocation $\\phi$','#f8d0d0')
box(8.7,1.9,1.2,0.8,'Front / rear\naxle pressures','#eeeeee')
arr(1.7,2.9,2.2,2.9);arr(1.7,2.7,2.2,1.8);arr(4.1,2.9,4.6,2.45,'$\\hat g_s$');arr(4.1,1.7,4.6,2.15,'$\\hat m$')
arr(6.5,2.3,7.0,2.3);arr(7.7,1.9,7.9,1.2);arr(9.0,0.75,9.3,1.9)
ax.plot([0.9,0.9],[2.5,0.5],'k',lw=1);arr(0.9,0.5,7.0,0.5);ax.text(4.0,0.56,'per-axle wheel slip',fontsize=7,ha='center')
box(2.2,0.8,1.9,0.35,'Direction flag (fwd / rev)','#eeeeee');arr(4.1,0.97,7.0,0.97,'$\\kappa_{re}$ = 0.06 / 0.04')
f.tight_layout();f.savefig(O+'fig1_architecture.png');plt.close(f)
fw=pd.read_csv('out_v4/mc_PROP3_re0.06_fwd.csv');x=fw[fw.margin>1.05]
print('fwd prop',x.rms_err_kph.mean().round(3),x.rms_err_kph.quantile(.95).round(3),x.max_speed_kph.mean().round(3),x.max_speed_kph.quantile(.95).round(3),(x.lock_time_s>.5).sum(),x.peak_jerk.mean().round(3),x.p_activity.mean().round(2))
