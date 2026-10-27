# Direction-Aware, Slip-Aware Brake-Only Speed Limiting

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)

Open simulation code for the paper:

> H. C. Mudduluru, *Direction-Aware, Slip-Aware Brake-Only Speed Limiting for Low-Speed Descent of Steep Grades with Adaptive Grade and Mass Estimation*. Submitted to the International Journal of Automotive Technology (IJAT).

The code simulates a vehicle that holds a walking-pace set speed (4 km/h) on steep grades using the friction brakes alone. It compares a proposed controller with four baselines in **forward** descent (nose downhill) and **reverse** descent (nose uphill), and reproduces every table and figure in the paper.

**Main finding.** In reverse descent, load shifts to the rear axle while a fixed front-biased brake distribution still asks the front axle for most of the braking force. The front wheels lock and the speed runs away, even with an anti-lock-style slip cap. A slip-aware, direction-scheduled front/rear pressure reallocation removes these lock-ups.

![Reverse descent at 30 % grade, mu = 0.42](figures/fig2_reverse_lowmu_timeseries.png)

## Repository layout

```
bsl/                    simulation package
  model.py              vehicle plant, controllers, slip layer, Monte Carlo sampling
  metrics.py            performance metrics
scripts/
  run_montecarlo.py     run one Monte Carlo job -> per-sample CSV
  reproduce_all.py      run all evaluation and tuning jobs, then build tables and figures
  run_validation.py     independent validation set (Table 6)
  make_tables.py        Tables 2-5 + friction-margin checks
  make_figures.py       Figures 1-4
results/
  montecarlo/           evaluation set (parameter seed 42, N = 400)
  tuning/               tuning set (parameter seed 3, N = 120)
  validation/           independent validation set (parameter seed 2027, N = 400)
  tables/               generated tables (CSV) and checks.txt
figures/                generated figures (PNG, 300 dpi)
tests/                  smoke tests
```

## Installation

Python 3.9 or later.

```bash
git clone https://github.com/HemanthMChakravarthy/brake-only-speed-limiter.git
cd brake-only-speed-limiter
pip install -r requirements.txt
pytest -q          # optional smoke tests, about 1 min
```

## Reproducing the paper

All result CSVs are included, so the tables and figures can be rebuilt immediately:

```bash
python scripts/make_tables.py
python scripts/make_figures.py
```

To rerun the simulations from scratch, delete `results/montecarlo/`, `results/tuning/` and `results/validation/`, then run:

```bash
python scripts/reproduce_all.py    # evaluation + tuning sets, about 15-20 min on one CPU core
python scripts/run_validation.py   # independent validation set, about 10 min
```

Both scripts skip jobs whose output CSV already exists, so they can be stopped and restarted.

Run a single Monte Carlo job:

```bash
python scripts/run_montecarlo.py --controller PROPOSED --direction rev --out my_run.csv
python scripts/run_montecarlo.py --controller PROPOSED --direction rev --kre 0.06 --out my_run_kre006.csv
```

Use the simulator directly:

```python
import numpy as np
from bsl import simulate, sample_params, metrics

prm = sample_params(10, np.random.default_rng(0))   # 10 random vehicles / grades / friction levels
rec = simulate('PROPOSED', prm, direction=-1)        # reverse descent, 40 s
print(metrics(rec)['max_speed_kph'])
```

## Model summary

| Part | Description |
|---|---|
| Vehicle | Two-axle longitudinal model, quasi-static load transfer, grade profile with optional roughness |
| Wheels and tires | Per-axle rotational dynamics, Pacejka-type longitudinal tire (B = 10, C = 1.65), brake lock possible |
| Powertrain | Low-range idle creep / engine-braking force, saturated |
| Brake actuator | Per axle: dead time + first-order lag + 400 bar/s rate limit; fixed hydraulic front share 0.65 |
| Sensors | Wheel speeds (σ = 0.02 m/s), accelerometer (σ = 0.05 m/s², bias up to ±0.1 m/s²) |
| Rates | Plant 1 ms, controllers 10 ms |

All parameters are generic and textbook-representative. They do not describe any production vehicle or brake system.

## Controllers

| Name | Description |
|---|---|
| `PI` | Feedback-only PI, nominal mass |
| `RB` | Generic rule-based pressure ramp with dead band (not a reproduction of any production system) |
| `FFPI` | PI + grade feedforward (fixed 0.15 s low-pass), nominal mass |
| `AFFPI` | FFPI + RLS effective-mass adaptation + jerk limiter, no reallocation (first design iteration) |
| `PROPOSED` | Noise-adaptive Kalman grade estimator, confidence-blended RLS effective mass, feedforward-PI with 1 bar pressure hysteresis, slip-aware front/rear reallocation with threshold κre = 0.06 forward / 0.04 reverse |

All controllers share the same PI gains and the same anti-lock-style per-axle slip cap.

## Data sets

| Set | Parameter seed | Sensor-noise seed | N (feasible) | Used for |
|---|---|---|---|---|
| Tuning | 3 | 7 | 120 | Estimator bandwidth Qg and hysteresis band |
| Evaluation | 42 | 7 | 400 (393) | Main results (Tables 2–5); reallocation-threshold selection |
| Validation | 2027 | 11 | 400 (393) | Independent confirmation (Table 6); not used for any design choice |

Samples with static friction margin μ cos θ / sin θ ≤ 1.05 are excluded as physically unholdable.

## Key results

Reverse descent, evaluation set, mean (95th percentile):

| Controller | RMS speed error [km/h] | Max speed [km/h] | Runs with wheel lock > 0.5 s |
|---|---|---|---|
| PI | 0.97 (2.33) | 6.76 (10.29) | 63 |
| Rule-based | 1.19 (3.32) | 6.18 (9.06) | 95 |
| FF+PI | 0.49 (1.51) | 5.41 (8.05) | 71 |
| A-FF+PI | 0.42 (0.82) | 5.32 (6.65) | 71 |
| **Proposed** | **0.16 (0.25)** | **4.47 (4.82)** | **0** |

Independent validation set, reverse descent:

| Controller | RMS speed error [km/h] | Max speed p95 [km/h] | Runs with wheel lock > 0.5 s |
|---|---|---|---|
| Baselines (PI, RB, FF+PI, A-FF+PI) | 0.43–1.21 | 7.04–13.98 | 66–111 |
| Proposed, κre = 0.06 | 0.24 | 4.92 | 8 |
| Proposed, κre = 0.05 | 0.18 | 4.92 | 2 |
| **Proposed, κre = 0.04 (final)** | **0.16** | **4.91** | **0** |

Forward descent: the proposed controller's mean RMS speed error was about 35 % lower than FF+PI (0.16 vs. 0.25 km/h) at a similar pressure activity, with no lock-ups.

## Mapping to the paper

| Paper | Generated by | Output |
|---|---|---|
| Table 2 | `make_tables.py` | `results/tables/table2_reverse.csv` |
| Table 3 | `make_tables.py` | `results/tables/table3_forward.csv` |
| Table 4 | `make_tables.py` | `results/tables/table4_threshold.csv` |
| Table 5 | `make_tables.py` | `results/tables/table5_tuning.csv` |
| Table 6 | `run_validation.py` | `results/validation/summary.csv` |
| Section 5.4 checks | `make_tables.py` | `results/tables/checks.txt` |
| Figures 1–4 | `make_figures.py` | `figures/fig1_*.png` … `figures/fig4_*.png` |

**Note:** reverse-descent PI, RB and A-FF+PI on the evaluation set were run in two batches of 200 samples. The parameter samples are the same as for the other controllers.

## Limitations

- Simulation only. No hardware-in-the-loop or vehicle data.
- Quasi-static load transfer. No pitch, suspension, lateral dynamics, split-μ or steering.
- The slip cap is a generic anti-lock-style limiter, not a production ABS. The speed reference is the largest wheel speed.
- Pressure activity is measured on the command signal. Valve hardware dynamics, noise and wear are not modelled.
- One target speed (4 km/h). Brake thermal fade is not coupled to the brake gain.

## Use of generative AI

Microsoft Copilot was used to help write this code. The author reviewed and verified the code and results.

## Citation

If you use this code, please cite it using [CITATION.cff](CITATION.cff) (GitHub's "Cite this repository" button). Once the paper is published, please cite the paper.

## License

MIT. See [LICENSE](LICENSE).
