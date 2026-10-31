"""Reverse-descent baselines on the evaluation set -> out_paper/mc_{PI,RB,PROP1}_rev_{0,1}.csv (Table 2).

Parameter seed 42, N = 400, run in two batches of 200 samples (indices 0-199 and 200-399),
each with sensor-noise seed 7. Jobs whose CSV already exists are skipped. About 5 min on one CPU core.
"""
import os
import numpy as np, pandas as pd
from bsl_sim3 import simulate, sample_params, friction_margin
from run_lib import metrics

ROOT = os.path.dirname(os.path.abspath(__file__))
P = sample_params(400, np.random.default_rng(42)); fm = friction_margin(P)
os.makedirs(os.path.join(ROOT, 'out_paper'), exist_ok=True)
for kind in ['PI', 'RB', 'PROP1']:
    for part in (0, 1):
        fn = os.path.join(ROOT, 'out_paper', f'mc_{kind}_rev_{part}.csv')
        if os.path.exists(fn):
            continue
        idx = np.arange(400)[part*200:(part+1)*200]
        sub = {k: v[idx] for k, v in P.items()}
        df = pd.DataFrame(metrics(simulate(kind, sub, direction=-1, seed=7, Qg=0.15, db=1.0)))
        df['idx'] = idx; df['margin'] = fm[idx]
        df.to_csv(fn, index=False); print('wrote', fn, flush=True)
