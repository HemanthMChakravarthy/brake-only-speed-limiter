"""Build Tables 2-6 of the paper from the CSVs in out_paper/, out_v4/ and out_extra/.
Output: tables/*.csv and tables/checks.txt. Runs in a few seconds; no simulation needed."""
import os, glob
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'tables'); os.makedirs(OUT, exist_ok=True)
FEAS = 1.05   # samples with friction margin <= 1.05 are excluded as physically unholdable


def rd(path):
    if '*' in path:
        d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(ROOT, path)))], ignore_index=True)
    else:
        d = pd.read_csv(os.path.join(ROOT, path))
    return d[d.margin > FEAS]


def mp(x, nd=2):
    return f'{x.mean():.{nd}f} ({x.quantile(.95):.{nd}f})'


def locked(d):
    return int((d.lock_time_s > 0.5).sum())


# Table 2: reverse descent, evaluation set
REV = {'PI': 'out_paper/mc_PI_rev_*.csv', 'RB': 'out_paper/mc_RB_rev_*.csv', 'FF+PI': 'out_v4/mc_FFPI_rena_rev.csv',
       'A-FF+PI': 'out_paper/mc_PROP1_rev_*.csv', 'Proposed': 'out_v4/mc_PROP3_re0.04_rev.csv'}
t2 = pd.DataFrame([{'Controller': c, 'N': len(d), 'RMS error [km/h]': mp(d.rms_err_kph), 'Max speed [km/h]': mp(d.max_speed_kph),
                    'Worst max speed [km/h]': f'{d.max_speed_kph.max():.1f}', 'Runs locked > 0.5 s': locked(d),
                    'Peak jerk p95 [m/s3]': f'{d.peak_jerk.quantile(.95):.1f}', 'Pressure activity [bar/s]': f'{d.p_activity.mean():.1f}'}
                   for c, d in ((c, rd(p)) for c, p in REV.items())])

# Table 3: forward descent, evaluation set
FWD = {'PI': 'out_extra/forward/mc_PI_fwd.csv', 'RB': 'out_extra/forward/mc_RB_fwd.csv', 'FF+PI': 'out_extra/forward/mc_FFPI_fwd.csv',
       'A-FF+PI': 'out_extra/forward/mc_PROP1_fwd.csv', 'Proposed': 'out_v4/mc_PROP3_re0.06_fwd.csv'}
t3 = pd.DataFrame([{'Controller': c, 'N': len(d), 'RMS error [km/h]': mp(d.rms_err_kph), 'Max speed [km/h]': mp(d.max_speed_kph),
                    'Mean peak jerk [m/s3]': f'{d.peak_jerk.mean():.2f}', 'Pressure activity [bar/s]': f'{d.p_activity.mean():.1f}',
                    'Runs locked > 0.5 s': locked(d)}
                   for c, d in ((c, rd(p)) for c, p in FWD.items())])

# Table 4: reallocation threshold, evaluation set (+ rough-terrain subset A > 0.05)
rows = []
for kre in ['0.06', '0.05', '0.04']:
    for dr, lab in [('fwd', 'Forward'), ('rev', 'Reverse')]:
        d = rd(f'out_v4/mc_PROP3_re{kre}_{dr}.csv'); r = d[d.A > 0.05]
        rows.append({'kre': kre, 'Direction': lab, 'RMS error [km/h]': f'{d.rms_err_kph.mean():.3f}',
                     'Max speed p95 [km/h]': f'{d.max_speed_kph.quantile(.95):.2f}', 'Runs locked > 0.5 s': locked(d),
                     'Triggers [1/s]': f'{d.realloc_switch_per_s.mean():.1f}', 'Pressure activity [bar/s]': f'{d.p_activity.mean():.1f}',
                     'Rough subset: N / runs locked': f'{len(r)} / {locked(r)}'})
t4 = pd.DataFrame(rows)

# Table 5: estimator bandwidth and hysteresis
rows = []
for qg, db, lab in [('0.6', '0.0', 'Qg = 0.6, no hysteresis'), ('0.15', '0.0', 'Qg = 0.15, no hysteresis'),
                    ('0.15', '1.0', 'Qg = 0.15, 1.0 bar band (final)'), ('0.15', '2.0', 'Qg = 0.15, 2.0 bar band')]:
    d = rd(f'out_extra/tuning/mc_PROP3_qg{qg}_db{db}_fwd.csv')
    rows.append({'Configuration': lab, 'Data set': f'Tuning (N = {len(d)})', 'RMS error [km/h]': f'{d.rms_err_kph.mean():.3f}',
                 'Pressure activity [bar/s]': f'{d.p_activity.mean():.1f}', 'Command reversals [1/s]': f'{d.p_reversals.mean():.1f}'})
for p, lab in [('out_extra/forward/mc_FFPI_fwd.csv', 'FF+PI (reference)'), ('out_v4/mc_PROP3_re0.06_fwd.csv', 'Qg = 0.15, 1.0 bar band (final)')]:
    d = rd(p)
    rows.append({'Configuration': lab, 'Data set': f'Evaluation (N = {len(d)})', 'RMS error [km/h]': f'{d.rms_err_kph.mean():.3f}',
                 'Pressure activity [bar/s]': f'{d.p_activity.mean():.1f}', 'Command reversals [1/s]': f'{d.p_reversals.mean():.1f}'})
t5 = pd.DataFrame(rows)

# Table 6: independent validation set
V = [('PI', 'Reverse', 'mc_PI_rev'), ('RB', 'Reverse', 'mc_RB_rev'), ('FF+PI', 'Reverse', 'mc_FFPI_rev'),
     ('A-FF+PI', 'Reverse', 'mc_PROP1_rev'), ('Proposed, kre = 0.06', 'Reverse', 'mc_PROP3_re0.06_rev'),
     ('Proposed, kre = 0.05', 'Reverse', 'mc_PROP3_re0.05_rev'), ('Proposed, kre = 0.04 (final)', 'Reverse', 'mc_PROP3_re0.04_rev'),
     ('FF+PI', 'Forward', 'mc_FFPI_fwd'), ('Proposed, kre = 0.06 (final)', 'Forward', 'mc_PROP3_re0.06_fwd')]
t6 = pd.DataFrame([{'Controller': c, 'Direction': dr, 'N': len(d), 'RMS error [km/h]': mp(d.rms_err_kph),
                    'Max speed [km/h]': mp(d.max_speed_kph), 'Worst max speed [km/h]': f'{d.max_speed_kph.max():.1f}',
                    'Runs locked > 0.5 s': locked(d)}
                   for c, dr, d in ((c, dr, rd(f'out_extra/validation/{f}.csv')) for c, dr, f in V)])

# Friction-margin checks (Sections 5.4 and 5.6)
ff = rd('out_v4/mc_FFPI_rena_rev.csv'); p6 = rd('out_v4/mc_PROP3_re0.06_rev.csv'); p4 = rd('out_v4/mc_PROP3_re0.04_rev.csv')
late = p6.index[p6.lock_time_s > 0.5]
vff = rd('out_extra/validation/mc_FFPI_rev.csv')
checks = [f'Evaluation set: reverse samples locked with kre = 0.06: {len(late)}',
          f'  max speed of those samples with kre = 0.04: {p4.loc[late].max_speed_kph.max():.2f} km/h '
          f'(lowest friction margin {p4.loc[late].margin.min():.2f})',
          f'Evaluation set: FF+PI reverse samples locked: {locked(ff)}, with margin > 1.3: {locked(ff[ff.margin > 1.3])}',
          f'Validation set: FF+PI reverse samples locked: {locked(vff)}, with margin > 1.3: {locked(vff[vff.margin > 1.3])}']

for t, f, n in [(t2, 'table2_reverse', 'Table 2'), (t3, 'table3_forward', 'Table 3'), (t4, 'table4_threshold', 'Table 4'),
                (t5, 'table5_tuning', 'Table 5'), (t6, 'table6_validation', 'Table 6')]:
    t.to_csv(f'{OUT}/{f}.csv', index=False); print(f'\n{n}\n' + t.to_string(index=False))
open(f'{OUT}/checks.txt', 'w').write('\n'.join(checks) + '\n'); print('\n' + '\n'.join(checks))
