"""Runs that complete the paper's evidence (forward baselines, tuning set, independent validation).

Uses bsl_sim3.py and run_lib.py. Output: out_extra/{forward,tuning,validation}/*.csv
Jobs whose CSV already exists are skipped, so the script can be stopped and restarted.
Runtime: about 15 min on one CPU core.

  forward/    evaluation set (parameter seed 42, N = 400, sensor-noise seed 7), forward descent:
              PI, RB, FFPI, PROP1 (A-FF+PI)                                  -> Table 3
  tuning/     independent tuning set (parameter seed 3, N = 120, noise seed 7), PROP3 with
              (Qg, hysteresis band) = (0.6, 0), (0.15, 0), (0.15, 1.0), (0.15, 2.0) -> Table 5
  validation/ independent validation set (parameter seed 2027, N = 400, noise seed 11)  -> Table 6
"""
import os
import numpy as np, pandas as pd
import bsl_sim3 as S
from bsl_sim3 import simulate, sample_params, friction_margin
from run_lib import metrics

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'out_extra')


def run(fn, kind, prm, direction, seed, Qg=0.15, db=1.0, kre=0.06):
    if os.path.exists(fn):
        return
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    S.SLIP['re'] = kre
    df = pd.DataFrame(metrics(simulate(kind, prm, direction=direction, seed=seed, Qg=Qg, db=db)))
    df['margin'] = friction_margin(prm); df['A'] = prm['A']; df['mu'] = prm['mu']
    df.to_csv(fn, index=False, float_format='%.5g')
    S.SLIP['re'] = 0.06
    print('wrote', os.path.relpath(fn, ROOT), flush=True)


EVAL = sample_params(400, np.random.default_rng(42))
for k in ['PI', 'RB', 'FFPI', 'PROP1']:
    run(f'{OUT}/forward/mc_{k}_fwd.csv', k, EVAL, +1, seed=7)

TUNE = sample_params(120, np.random.default_rng(3))
for qg, db in [(0.6, 0.0), (0.15, 0.0), (0.15, 1.0), (0.15, 2.0)]:
    run(f'{OUT}/tuning/mc_PROP3_qg{qg}_db{db}_fwd.csv', 'PROP3', TUNE, +1, seed=7, Qg=qg, db=db)

VAL = sample_params(400, np.random.default_rng(2027))
for d, k, kre in [(-1, 'PROP3', 0.04), (-1, 'PROP3', 0.05), (-1, 'PROP3', 0.06), (-1, 'FFPI', 0.06),
                  (-1, 'PI', 0.06), (-1, 'RB', 0.06), (-1, 'PROP1', 0.06),
                  (+1, 'PROP3', 0.06), (+1, 'PROP3', 0.04), (+1, 'FFPI', 0.06)]:
    tag = f'_re{kre}' if k == 'PROP3' else ''
    run(f'{OUT}/validation/mc_{k}{tag}_{"fwd" if d > 0 else "rev"}.csv', k, VAL, d, seed=11, kre=kre)
print('ALL DONE', flush=True)
