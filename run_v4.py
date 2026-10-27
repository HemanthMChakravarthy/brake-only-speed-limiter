"""v0.4 checks: (A) reallocation threshold 0.04/0.05/0.06 forward+reverse incl. rough terrain,
(B) lock-up root cause vs. friction margin. Same MC set as v0.3 (seed 42, N=400). Incremental CSV output."""
import numpy as np, pandas as pd, time, os, sys
import bsl_sim3 as S
from bsl_sim3 import simulate, sample_params, friction_margin
from run_lib import metrics
os.makedirs('out_v4', exist_ok=True)
QG, DB = 0.15, 1.0
P_ = sample_params(400, np.random.default_rng(42)); marg = friction_margin(P_)
feas = marg > 1.05
pd.DataFrame({**{k: v for k, v in P_.items() if k != 'ph'}, 'margin': marg}).to_csv('out_v4/mc_samples.csv', index=False)
# deterministic rough + low-mu cases
o = np.ones(2)
DET = dict(mf=np.array([1., 1.]), Gmax=np.array([.25, .30]), A=np.array([.15, 0.]), ph=np.array([[0, 1, 2]]*2, float),
           mu=np.array([.8, .42]), kbf=o.copy(), tau=.1*o, td=.04*o, kptf=o.copy(), abias=0*o)
jobs = [(re_, dr) for re_ in [0.06, 0.05, 0.04] for dr in [1, -1]] + [('FFPI', -1)]
for tag, dr in jobs:
    t0 = time.time()
    fn = f'out_v4/mc_{"FFPI" if tag=="FFPI" else "PROP3"}_re{"na" if tag=="FFPI" else tag}_{"fwd" if dr>0 else "rev"}.csv'
    if os.path.exists(fn): continue
    if tag == 'FFPI':
        kind = 'FFPI'
    else:
        kind = 'PROP3'; S.SLIP['re'] = tag
    M = metrics(simulate(kind, P_, direction=dr, seed=7, Qg=QG, db=DB))
    df = pd.DataFrame(M); df['margin'] = marg; df['A'] = P_['A']; df['mu'] = P_['mu']
    df.to_csv(f'out_v4/mc_{kind}_re{tag if kind=="PROP3" else "na"}_{"fwd" if dr>0 else "rev"}.csv', index=False)
    D = metrics(simulate(kind, DET, direction=dr, seed=1, Qg=QG, db=DB))
    pd.DataFrame(D, index=['F2_rough' if dr > 0 else 'R2_rough', 'X_lowmu']).to_csv(
        f'out_v4/det_{kind}_re{tag if kind=="PROP3" else "na"}_{"fwd" if dr>0 else "rev"}.csv')
    print('done', kind, tag, dr, round(time.time()-t0), flush=True)
S.SLIP['re'] = 0.06
print('ALL DONE', flush=True)
