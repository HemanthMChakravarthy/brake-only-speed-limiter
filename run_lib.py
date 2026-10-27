import numpy as np
from scipy.signal import butter, filtfilt
from bsl_sim3 import V_REF, DTC
bb, ab = butter(2, 5.0/(0.5/DTC))
def jerk(a): return np.gradient(filtfilt(bb, ab, a, axis=0), DTC, axis=0)
def metrics(r):
    v = r['v']; e = v[100:] - V_REF; j = jerk(r['a'].astype(float))[100:]
    return dict(rms_err_kph=np.sqrt((e**2).mean(0))*3.6, max_speed_kph=v[100:].max(0)*3.6,
        min_speed_kph=v[300:].min(0)*3.6, peak_jerk=np.abs(j).max(0), rms_jerk=np.sqrt((j**2).mean(0)),
        p_activity=np.abs(np.diff(r['pc'], axis=0)).sum(0)/r['t'][-1],
        p_reversals=(np.diff(np.sign(np.diff(r['pc'], axis=0)), axis=0) != 0).sum(0)/r['t'][-1],
        lock_time_s=r['lock'], realloc_switch_per_s=r['n_switch'])
