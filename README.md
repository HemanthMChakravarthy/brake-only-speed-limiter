# v0.4 — Reallocation-threshold check and lock-up root cause
Python only (NumPy, SciPy, Matplotlib, pandas). Generic parameters, with no OEM or supplier data.
`bsl_sim3.py` = v0.3 plant and controllers, plus logging of reallocation trigger events. `run_v4.py` → `out_v4/`.
v3 settings: Qg = 0.15, 1.0 bar hysteresis. Same Monte Carlo set as v0.3 (seed 42, N=400, 393 feasible).

## A. Reallocation slip threshold (v3), all 393 feasible runs
| Threshold | Dir | RMS err [km/h] | p95 max speed | Runs locked >0.5 s | Pressure activity [bar/s] | Trigger events [1/s] |
|---|---|---|---|---|---|---|
| 0.06 | fwd | 0.162 | 4.86 | 0 | 14.2 | 2.3 |
| 0.05 | fwd | 0.162 | 4.87 | 0 | 14.2 | 5.5 |
| 0.04 | fwd | 0.162 | 4.87 | 0 | 14.2 | 11.5 |
| 0.06 | rev | 0.244 | 4.86 | 8 | 15.4 | 4.7 |
| 0.05 | rev | 0.170 | 4.83 | 2 | 14.4 | 7.5 |
| **0.04** | rev | **0.161** | **4.82** | **0** | 14.3 | 12.5 |
Rough-terrain subset (roughness A > 0.05, 152 runs): same pattern. 0.04 gives no lock-up and no loss of accuracy or jerk.
Forward never locks at any threshold. A lower threshold only adds trigger events there.

## B. Lock-up root cause — the v0.3 hypothesis was wrong
v0.3 suggested the remaining reverse lock-ups were physically unholdable (friction margin close to 1.05). **This is not supported:**
v3 at threshold 0.04 holds **all 8** of those runs at ≤ 5.1 km/h, including margin 1.05 (μ = 0.45).
The cause was **late front-to-rear reallocation**, not physics. Widening the feasibility margin to 1.15 would have hidden a real controller weakness.
FF+PI (no reallocation) locks in **71 of 393** reverse runs, including 54 with margin > 1.3 (`lockup_cases.csv`, fig10).

## Recommendation
**Direction-scheduled threshold: 0.04 in reverse, 0.06 forward.**
This gives zero lock-ups in both directions without the extra trigger activity in forward driving.

## Caveat
Trigger events reach about 12/s in reverse at 0.04. They had no measurable effect on pressure activity or jerk in this model,
but the model has no valve hardware dynamics. Treat this as an open item for rig validation.
Remaining limitations: no pitch or suspension, generic ABS layer, simulation only.

## v0.5 — Manuscript figures (out_paper/)
- `figs_paper.py`, `fig4.py`, `fig_fix.py` regenerate Figures 1–4 of the manuscript.
- Reverse-descent PI, RB and A-FF+PI (PROP1) Monte Carlo runs: `out_paper/mc_*_rev_{0,1}.csv`. Same parameter samples (seed 42), run in two batches of 200 with sensor-noise seed 7 per batch.
- Final controller = PROP3 with Qg = 0.15, 1.0 bar hysteresis, and reallocation threshold 0.06 forward / 0.04 reverse.
- `paper/build.js` builds the manuscript .docx (docx-js).
