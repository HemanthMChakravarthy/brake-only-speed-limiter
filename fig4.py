import pandas as pd, glob, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
plt.rcParams.update({'font.size':9,'font.family':'serif','axes.grid':True,'grid.alpha':.3,'savefig.dpi':300})
O='out_paper/'
def load(k):
    if k=='FFPI': return pd.read_csv('out_v4/mc_FFPI_rena_rev.csv')
    if k=='PROP3': return pd.read_csv('out_v4/mc_PROP3_re0.04_rev.csv')
    return pd.concat([pd.read_csv(f) for f in sorted(glob.glob(O+f'mc_{k}_rev_*.csv'))]).reset_index(drop=True)
K=['PI','RB','FFPI','PROP1','PROP3'];D={k:load(k) for k in K};feas=(D['FFPI'].margin>1.05).values
f,ax=plt.subplots(1,4,figsize=(12,3.6))
for a,(m,l) in zip(ax,[('rms_err_kph','(a) RMS speed error [km/h]'),('max_speed_kph','(b) Max speed [km/h]'),('lock_time_s','(c) Wheel-lock time [s]'),('p_activity','(d) Pressure activity [bar/s]')]):
    a.boxplot([D[k][m][feas] for k in K],labels=['PI','RB','FF+PI','A-FF+PI','Prop.'],flierprops=dict(markersize=2))
    a.set_title(l,fontsize=9);a.tick_params(axis='x',labelsize=7.5)
    if m=='max_speed_kph':
        a.set_yscale('log');a.set_yticks([4,6,10,20]);a.yaxis.set_major_formatter(ScalarFormatter());a.yaxis.set_minor_formatter(plt.NullFormatter())
f.tight_layout();f.savefig(O+'fig4_mc_reverse.png');plt.close(f);print('ok')
