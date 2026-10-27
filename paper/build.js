const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Footer,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, TabStopType,
  LevelFormat } = require('docx');

const FONT = 'Times New Roman';
const W = 9360;
const FIG = '../out_paper/';

function runs(text, opts = {}) {
  // supports _{sub}, ^{sup}, *italic*
  const out = []; const re = /(_\{[^}]*\}|\^\{[^}]*\}|\*[^*]+\*)/g; let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...opts }));
    const t = m[0];
    if (t.startsWith('_{')) out.push(new TextRun({ text: t.slice(2, -1), subScript: true, font: FONT, ...opts }));
    else if (t.startsWith('^{')) out.push(new TextRun({ text: t.slice(2, -1), superScript: true, font: FONT, ...opts }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, ...opts }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...opts }));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), alignment: AlignmentType.JUSTIFIED, spacing: { after: 120, line: 300 }, ...o });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })] });
const EQ = (t, n) => new Paragraph({
  tabStops: [{ type: TabStopType.CENTER, position: W / 2 }, { type: TabStopType.RIGHT, position: W }],
  spacing: { before: 60, after: 120 },
  children: [new TextRun({ text: '\t', font: FONT }), ...runs(t), new TextRun({ text: `\t(${n})`, font: FONT })]
});
const BUL = t => new Paragraph({ numbering: { reference: 'bul', level: 0 }, children: runs(t), spacing: { after: 80, line: 300 }, alignment: AlignmentType.JUSTIFIED });
const NUM = (t, ref = 'contrib') => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 80, line: 300 }, alignment: AlignmentType.JUSTIFIED });
const NOTE = t => new Paragraph({ children: runs(t, { color: 'C00000', bold: true }), spacing: { after: 120 } });

function fig(file, wpx, hpx, caption) {
  const w = 600, h = Math.round(w * hpx / wpx);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, keepNext: true, children: [new ImageRun({ type: 'png', data: fs.readFileSync(FIG + file), transformation: { width: w, height: h }, altText: { title: caption.slice(0, 40), description: caption, name: file } })] }),
    new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 200 }, children: runs(caption, { size: 20 }) })
  ];
}
const bd = { style: BorderStyle.SINGLE, size: 4, color: '999999' };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function table(caption, head, rows, widths) {
  const tot = widths.reduce((a, b) => a + b, 0);
  const mk = (cells, isHead) => new TableRow({
    tableHeader: isHead, children: cells.map((c, i) => new TableCell({
      borders, width: { size: widths[i], type: WidthType.DXA }, margins: { top: 50, bottom: 50, left: 80, right: 80 },
      shading: isHead ? { fill: 'E7E6E6', type: ShadingType.CLEAR } : undefined,
      children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, children: runs(String(c), { size: 18, bold: isHead }) })]
    }))
  });
  return [
    new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 }, children: runs(caption, { size: 20 }) }),
    new Table({ width: { size: tot, type: WidthType.DXA }, columnWidths: widths, rows: [mk(head, true), ...rows.map(r => mk(r, false))] }),
    new Paragraph({ spacing: { after: 160 }, children: [] })
  ];
}

const C = [];
// ---------- Title block
C.push(NOTE('DRAFT v0.1 for author review. Red bracketed items need your input before submission.'));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: 'Direction-Aware, Slip-Aware Brake-Only Speed Limiting for Low-Speed Descent of Steep Grades with Adaptive Grade and Mass Estimation', bold: true, size: 32, font: FONT })] }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, children: runs('Hemanth Chakravarthy Mudduluru^{1,*}', { size: 24 }) }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, children: runs('^{1} [Affiliation, city, country — confirm whether an employer affiliation can be listed]', { size: 20, color: 'C00000' }) }));
C.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: runs('^{*} Corresponding author: [e-mail]', { size: 20, color: 'C00000' }) }));

C.push(new Paragraph({ children: [new TextRun({ text: 'Abstract', bold: true, font: FONT })], spacing: { after: 80 } }));
C.push(P('Brake-only speed limiting at walking pace on steep off-road grades must hold a set speed with the friction brakes alone while vehicle mass, brake gain, road grade and tire–road friction are uncertain. Published work on such functions generally assumes forward descent. This paper shows, in simulation, that reverse descent introduces a distinct failure mode: with the vehicle nose uphill, load shifts toward the rear axle while a conventional fixed hydraulic brake bias still directs most of the pressure to the front axle, so the front wheels lock and the vehicle speed runs away even when an anti-lock-style slip cap is active. A brake-only controller is proposed that combines (i) a noise-adaptive Kalman grade estimator using wheel-speed and accelerometer signals, (ii) a confidence-blended recursive-least-squares estimate of effective mass that also absorbs brake-gain error, (iii) a feedforward–PI law with pressure-command hysteresis, and (iv) a slip-aware, direction-scheduled front/rear pressure reallocation. An open-source simulation with per-axle wheel dynamics, a Pacejka-type tire model and hydraulic actuator dynamics was used to compare the controller with four baselines over 393 physically feasible Monte Carlo samples per direction. In reverse descent, wheel lock longer than 0.5 s occurred in 63 to 95 samples for the baselines and in none for the proposed controller, and the 95th-percentile maximum speed fell from 8.05 km/h (feedforward–PI) to 4.82 km/h at a 4 km/h target. In forward descent, the RMS speed error was 35 % lower than with feedforward–PI at a similar pressure activity. The study is simulation-only; the validation steps needed before vehicle use are identified.'));
C.push(new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: 'Key Words: ', bold: true, font: FONT }), ...runs('Hill descent control, Brake-only speed control, Road grade estimation, Mass estimation, Wheel slip, Brake force distribution, Reverse driving, Off-road vehicles')] }));

// ---------- 1 Introduction
C.push(H1('1. Introduction'));
C.push(P('Hill descent control and low-range speed-limiting functions hold a low set speed on steep grades without driver pedal input, using the service brakes as the main actuator. At walking pace the powertrain contributes only a small, speed-dependent creep or engine-braking force, so nearly all of the gravitational load must be reacted by friction brakes. The controller therefore has to apply a pressure that is, to a first approximation, proportional to vehicle mass times the sine of the grade angle, and it must do so while mass, brake gain, grade and tire–road friction are only partly known. Sustained braking on long descents also raises brake-disc and brake-fluid temperatures, which is a durability and safety concern in its own right [1].'));
C.push(P('Estimating road grade and vehicle mass online is a mature topic. Vahidi et al. used recursive least squares (RLS) with multiple forgetting factors to estimate a piecewise-constant mass and a time-varying grade, and they reported that persistent excitation is required for convergence [2]. Kidambi et al. compared RLS, extended Kalman filtering, a dynamic grade observer and an accelerometer-based parallel mass-and-grade method on vehicle data [3]. These methods were developed mainly for propulsion and powertrain control, where the tractive force is known and well excited. In a brake-only descent at a constant low speed the excitation is weak, and the brake force is known only through an uncertain pressure-to-force gain. The present work therefore estimates an *effective* mass that lumps the brake-gain error with the true mass, and it blends this estimate in only as its confidence grows.'));
C.push(P('Wheel-slip control for active braking is also well established [4]. A slip cap of the anti-lock type limits pressure on an axle that starts to slip, but by itself it does not move the lost braking force to an axle that still has spare adhesion. In forward descent this is rarely a limitation, because a front-biased hydraulic distribution matches the forward load transfer. In reverse descent the situation is inverted: the vehicle travels rear-first with its nose uphill, gravity and deceleration shift load toward the rear axle, and the fixed front bias asks the lightly loaded front axle for most of the braking force. Reverse descent has received comparatively little explicit treatment in the open literature reviewed for this work.'));
C.push(P('This paper makes four contributions:'));
C.push(NUM('It identifies and quantifies, by Monte Carlo simulation, a reverse-descent failure mode in brake-only speed limiting: front-axle lock and speed runaway caused by a fixed front brake bias, which a generic slip cap does not prevent.'));
C.push(NUM('It proposes a brake-only controller that combines a noise-adaptive Kalman grade estimator, a confidence-blended RLS effective-mass estimator, a feedforward–PI law with pressure-command hysteresis, and a slip-aware, direction-scheduled front/rear pressure reallocation.'));
C.push(NUM('It evaluates the controller against four baselines over 393 feasible samples per direction, including a friction-margin analysis showing that the residual lock-ups of a less sensitive reallocation threshold were caused by late reallocation rather than by physical infeasibility.'));
C.push(NUM('It reports the design iterations transparently, including a negative result (a jerk limiter that gave no measurable benefit) and the trade-off between estimator bandwidth and brake-pressure activity. The simulation code is released for reproduction.'));
C.push(P('Section 2 describes the vehicle model, Section 3 the controller, Section 4 the simulation study, and Section 5 the results. Section 6 discusses limitations and Section 7 concludes.'));

// ---------- 2 Model
C.push(H1('2. Vehicle Model'));
C.push(H2('2.1 Longitudinal and Wheel Dynamics'));
C.push(P('The vehicle is modelled as a two-axle longitudinal system travelling on a grade profile θ(s) that depends on the distance travelled s. A direction flag d = +1 denotes forward descent (nose downhill) and d = −1 reverse descent (nose uphill). In the body frame, with x pointing to the vehicle nose and signed velocity v, the longitudinal dynamics are'));
C.push(EQ('m v̇ = F_{x,f} + F_{x,r} − F_{res} + d m g sin θ', 1));
C.push(P('where F_{x,f} and F_{x,r} are the axle tire forces and F_{res} combines rolling resistance and aerodynamic drag, acting against the motion. The normal loads follow a quasi-static load-transfer model with wheelbase L, rear-axle distance l_{r} and centre-of-gravity height h:'));
C.push(EQ('F_{z,f} = [ m g cos θ · l_{r} + h m ( d g sin θ − v̇ ) ] / L,   F_{z,r} = m g cos θ − F_{z,f}', 2));
C.push(P('For d = −1, the gravity term reduces the front load, and a braking deceleration (v̇ > 0 when the velocity is negative) reduces it further. Each axle has a lumped rotational inertia I_{w} and effective rolling radius r:'));
C.push(EQ('I_{w} ω̇_{i} = − r F_{x,i} + T_{pt,i} − sgn(ω_{i}) K_{b} p_{i} r,   i ∈ {f, r}', 3));
C.push(P('where p_{i} is the axle brake pressure, K_{b} the pressure-to-force gain and T_{pt,i} the powertrain torque. The powertrain is modelled as a low-range creep and engine-braking force that is proportional to the deviation from an idle speed and saturates at fixed limits, split equally between the axles. The tire force uses a Pacejka-type longitudinal characteristic [5]:'));
C.push(EQ('F_{x,i} = μ F_{z,i} sin( C arctan( B κ_{i} ) ),   κ_{i} = ( ω_{i} r − v ) / max( |v|, v_{ε} )', 4));
C.push(P('with B = 10, C = 1.65 and v_{ε} = 0.5 m/s. The wheel equation is integrated semi-implicitly at 1 ms with a Coulomb treatment of brake lock, so a wheel can stop rotating when the brake torque exceeds the remaining wheel torque. Each axle pressure follows its command through a pure dead time τ_{d}, a first-order lag τ and a rate limit of 400 bar/s. A lumped thermal model per axle is included, but it is used only as a consistency check.'));
C.push(H2('2.2 Sensors'));
C.push(P('The controller receives wheel speeds with Gaussian noise (σ = 0.02 m/s), with the largest wheel speed used as the vehicle-speed reference, and a longitudinal accelerometer that measures specific force with Gaussian noise (σ = 0.05 m/s²) and a constant bias of up to ±0.1 m/s². All controllers run at 10 ms. Table 1 lists the nominal parameters, which are generic and textbook-representative and do not describe a specific production vehicle.'));
C.push(...table('Table 1. Nominal parameters and Monte Carlo ranges.', ['Quantity', 'Nominal', 'Monte Carlo range'], [
  ['Mass m', '2500 kg', '0.75–1.30 × nominal'],
  ['Wheelbase L / rear distance l_{r} / CG height h', '3.0 / 1.5 / 0.75 m', '—'],
  ['Brake gain K_{b} (total)', '250 N/bar', '0.85–1.15 × nominal'],
  ['Hydraulic front share (fixed bias)', '0.65', '—'],
  ['Actuator lag τ / dead time τ_{d}', '0.10 s / 0.04 s', '0.07–0.15 s / 0.02–0.06 s'],
  ['Peak grade', '—', '5–45 %'],
  ['Grade roughness amplitude A', '—', '0–8 % (grade)'],
  ['Tire–road friction μ', '—', '0.45–0.90'],
  ['Powertrain creep / engine-brake gain', '3000 N/(m/s)', '0.7–1.3 × nominal'],
  ['Accelerometer bias', '0', '±0.1 m/s²'],
  ['Target speed', '4 km/h', '—'],
], [4200, 2400, 2760]));

// ---------- 3 Controller
C.push(H1('3. Controller Design'));
C.push(P('Figure 1 shows the controller structure. The speed loop computes a total pressure command from estimated grade and effective mass. A slip layer then divides it between the axles and limits it, and that layer is the part that handles reverse descent.'));
C.push(...fig('fig1_architecture.png', 2919, 998, 'Figure 1. Structure of the proposed brake-only speed limiter. The grade and effective-mass estimates feed a feedforward–PI law. The slip layer distributes the total pressure command between the axles using per-axle wheel slip and the direction of travel.'));
C.push(H2('3.1 Noise-Adaptive Grade Estimator'));
C.push(P('Because an accelerometer measures specific force, the difference between the derivative of the wheel-speed signal and the accelerometer reading is a direct measurement of the gravitational component along the direction of travel. Both signals pass through matched second-order state-variable filters (3 Hz, ζ = 0.8), so the measurement'));
C.push(EQ('z_{k} = v̇_{ws,k} − a_{x,k} ≈ g sin θ_{k} + b_{a} + n_{k}', 5));
C.push(P('has no relative phase lag between the two paths. The grade term g_{s} = g sin θ is modelled as a random walk with intensity Q_{g} and estimated with a scalar Kalman filter. Its measurement-noise variance R_{k} is adapted online from the innovation sequence, following the innovation-based approach of Mehra [6]:'));
C.push(EQ('R_{k+1} = R_{k} + (Δt / T_{R}) [ clip( ν_{k}^{2} − P_{k|k−1}, 0, 4 ) − R_{k} ]', 6));
C.push(P('where ν_{k} is the innovation and T_{R} = 1.5 s. The filter therefore lowers its gain automatically on rough terrain or with noisy wheel-speed signals. Q_{g} = 0.15 (m/s²)²/s was chosen by the tuning study in Section 5.5.'));
C.push(H2('3.2 Effective-Mass Estimation'));
C.push(P('During braking, the longitudinal balance can be written in the linear-regression form y = m_{eff} φ, with'));
C.push(EQ('y = K_{b,nom} p̂ − F_{pt,nom}(v) + F_{aero}(v),   φ = −( a_{x} + c_{r} g )', 7));
C.push(P('where p̂ is the delayed and filtered nominal response of the actuator to the command. Because the nominal brake gain K_{b,nom} is used, the estimated parameter is an *effective* mass m_{eff} ≈ m K_{b,nom}/K_{b}, which also corrects the pressure command for brake-gain error. The parameter is updated by RLS with a forgetting factor of 0.995 [7]. Updates are made only when φ > 0.4 m/s² and the estimated pressure exceeds 3 bar, so that the regressor is sufficiently excited. To avoid an abrupt change in the command when the estimator first converges, the mass used by the controller is blended from the nominal value:'));
C.push(EQ('m̂ = m_{nom} + w ( m_{RLS} − m_{nom} ),   w → ( 1 − P_{RLS}/P_{0} )^{1/2}', 8));
C.push(P('where the weight w is rate-limited to 0.5 s⁻¹, the blended mass is rate-limited to 400 kg/s, P_{RLS} is the RLS covariance and P_{0} its initial value.'));
C.push(H2('3.3 Feedforward–PI Law with Pressure Hysteresis'));
C.push(P('With speed error e = |v̂| − v_{ref}, the requested deceleration and the total pressure command are'));
C.push(EQ('a_{req} = ĝ_{s} − c_{r} g + ( F_{pt,nom} − F_{aero} ) / m̂ + K_{P} e + K_{I} ∫ e dt,   p^{*} = m̂ a_{req} / K_{b,nom}', 9));
C.push(P('with K_{P} = 2 s⁻¹ and K_{I} = 1 s⁻². The command is limited to [0, p_{max}], and the integrator uses conditional integration as anti-windup [8]. To reduce valve activity, the command sent to the hydraulic unit is held until it differs from the held value by more than a band of 1.0 bar. The hold is bypassed when the command falls below 0.5 bar (release) or when |e| > 0.25 m/s, so the hysteresis cannot delay the response to a large speed error.'));
C.push(H2('3.4 Slip Layer and Direction-Scheduled Reallocation'));
C.push(P('Per-axle slip is computed from wheel speeds alone as κ_{i} = (ω_{i} r − v_{ref}) / max(v_{ref}, 0.5), using the largest wheel speed as the reference. All controllers in this study, including the baselines, use the same generic anti-lock-style cap. A per-axle scaling factor c_{i} ∈ [0, 1] decreases at 4 s⁻¹ while κ_{i} < −0.15 and recovers at 1 s⁻¹ otherwise. The proposed controller adds a reallocation of the front share φ (φ = 0.65 by default):'));
C.push(EQ('φ̇ = −0.6 s⁻¹ if κ_{f} < −κ_{re} and κ_{r} ≥ −κ_{re};   +0.6 s⁻¹ if the opposite holds;   0.1 s⁻¹ · sgn(0.65 − φ) otherwise', 10));
C.push(P('with φ limited to [0.30, 0.80] and axle commands p_{f} = c_{f} φ p^{*} and p_{r} = c_{r} (1 − φ) p^{*}. The threshold κ_{re} is scheduled with the direction of travel: κ_{re} = 0.06 in forward and κ_{re} = 0.04 in reverse. The choice of these values is analysed in Section 5.4.'));

// ---------- 4 Simulation study
C.push(H1('4. Simulation Study'));
C.push(H2('4.1 Baselines'));
C.push(P('Four baselines were compared with the proposed controller. All PI-based controllers use the same gains, and all controllers use the same slip cap:'));
C.push(BUL('PI: feedback-only PI; the pressure is computed with the nominal mass.'));
C.push(BUL('RB: a generic rule-based pressure-ramp controller with a ±0.1 m/s dead band, representing a simple hill-descent-style strategy. It is not a reproduction of any production system.'));
C.push(BUL('FF+PI: PI plus a grade feedforward from a fixed 0.15 s low-pass filter, with the nominal mass.'));
C.push(BUL('A-FF+PI: FF+PI plus RLS mass adaptation without blending and a 2.5 m/s³ jerk limiter on the requested deceleration. This was the first design iteration and has no reallocation.'));
C.push(H2('4.2 Scenarios, Sampling and Metrics'));
C.push(P('Each run lasts 40 s on a grade profile that ramps up over 4 m, holds for about 24 m and ramps down, with optional multi-sinusoidal roughness (wavelengths of 8, 3 and 1.2 m). A Monte Carlo set of 400 samples was drawn uniformly from the ranges in Table 1 (random seed 42) and run in both directions. Samples whose static friction margin μ cos θ / sin θ at the steepest point was below 1.05 were excluded as physically unholdable, which left 393 samples per direction. The metrics are: RMS speed error after the first second; maximum speed; wheel-lock time, defined as the time with |κ| > 0.5 on any axle while |v| > 0.2 m/s; peak jerk, from the acceleration filtered at 5 Hz; and pressure activity, the total variation of the pressure command per second. The number of command-direction reversals per second and the number of reallocation trigger events per second were also recorded.'));
C.push(P('The estimator bandwidth Q_{g} and the hysteresis band were tuned on an independent Monte Carlo set (seed 3, N = 120). The reallocation threshold κ_{re} was selected using the evaluation set itself (Section 5.4), so its results are in-sample and need independent confirmation.'));

// ---------- 5 Results
C.push(H1('5. Results'));
C.push(H2('5.1 Reverse Descent on Low Friction'));
C.push(P('Figure 2 shows a reverse descent of a 30 % grade at μ = 0.42 with nominal parameters. Every baseline enters a cycle in which a front wheel locks, the slip cap releases it and the wheel locks again. Speed rises to 6–10 km/h, and A-FF+PI and RB each drop to a standstill at least once after an overshoot. The proposed controller reduces the front share from 0.65 to about 0.47 as the grade builds up (between about 4 and 5 s). It keeps both axles below the reallocation threshold and holds the speed close to 4 km/h throughout. The front share returns to 0.65 after the grade ends.'));
C.push(...fig('fig3_reverse_lowmu_timeseries.png', 2050, 2385, 'Figure 2. Reverse descent of a 30 % grade at μ = 0.42 (nominal mass and brake gain). From top: grade, speed, maximum absolute wheel slip, and the front brake share of the proposed controller.'));
C.push(H2('5.2 Monte Carlo: Reverse Descent'));
C.push(P('Table 2 and Figure 3 summarise the reverse-descent Monte Carlo results. Lock events longer than 0.5 s occurred in 63 to 95 of the 393 samples for every baseline and in none for the proposed controller. The worst maximum speed was above 25 km/h for every baseline and 5.3 km/h for the proposed controller. Adding adaptive mass estimation (A-FF+PI) improved tracking compared with FF+PI but did not change the number of lock-ups. This indicates that the reverse-descent problem lies in the brake distribution, not in the speed loop. Pressure activity was similar to FF+PI; RB had the lowest activity but the largest speed error.'));
C.push(...table('Table 2. Reverse-descent Monte Carlo results (N = 393 feasible samples; mean, with 95th percentile in parentheses).', ['Controller', 'RMS error [km/h]', 'Max speed [km/h]', 'Worst max speed [km/h]', 'Runs locked > 0.5 s', 'Peak jerk p95 [m/s³]', 'Pressure activity [bar/s]'], [
  ['PI', '0.97 (2.33)', '6.76 (10.29)', '27.1', '63', '15.2', '24.7'],
  ['RB', '1.19 (3.32)', '6.18 (9.06)', '25.5', '95', '22.6', '6.2'],
  ['FF+PI', '0.49 (1.51)', '5.41 (8.05)', '26.2', '71', '12.4', '15.3'],
  ['A-FF+PI', '0.42 (0.82)', '5.32 (6.65)', '26.3', '71', '12.7', '15.3'],
  ['Proposed', '0.16 (0.25)', '4.47 (4.82)', '5.3', '0', '2.3', '14.3'],
], [1500, 1350, 1350, 1250, 1250, 1300, 1360]));
C.push(...fig('fig4_mc_reverse.png', 3519, 1001, 'Figure 3. Reverse-descent Monte Carlo distributions (N = 393). A-FF+PI denotes adaptive FF+PI with a jerk limiter and no reallocation. The maximum-speed axis is logarithmic.'));
C.push(P('Note: the PI, RB and A-FF+PI results in Table 2 were computed in two batches of 200 samples with a different sensor-noise seed from the FF+PI and proposed runs. The parameter samples are identical.', { children: runs('Note: the PI, RB and A-FF+PI results in Table 2 were computed in two batches of 200 samples with a different sensor-noise seed from the FF+PI and proposed runs. The parameter samples are identical.', { size: 20, italics: true }) }));
C.push(H2('5.3 Monte Carlo: Forward Descent'));
C.push(P('In forward descent no controller produced lock-ups (the 95th-percentile lock time was 0 s for all). The proposed controller had the lowest mean and 95th-percentile RMS error: 35 % below FF+PI and 79 % below PI on average (Table 3). Its mean peak jerk was slightly higher than FF+PI (1.76 vs. 1.34 m/s³), because the higher-bandwidth grade feedforward passes more terrain content to the command. Its pressure activity was within 5 % of FF+PI.'));
C.push(...table('Table 3. Forward-descent Monte Carlo results (N = 393; mean, with 95th percentile in parentheses).', ['Controller', 'RMS error [km/h]', 'Max speed [km/h]', 'Mean peak jerk [m/s³]', 'Pressure activity [bar/s]'], [
  ['PI', '0.77 (1.33)', '6.21 (8.17)', '1.47', '24.2'],
  ['RB', '0.81 (1.38)', '5.56 (6.25)', '2.63', '5.2'],
  ['FF+PI', '0.25 (0.42)', '4.70 (5.37)', '1.34', '13.6'],
  ['A-FF+PI', '0.21 (0.29)', '4.61 (4.89)', '1.51', '12.8'],
  ['Proposed', '0.16 (0.24)', '4.48 (4.86)', '1.76', '14.2'],
], [2160, 1800, 1800, 1800, 1800]));
C.push(H2('5.4 Reallocation Threshold and Friction Margin'));
C.push(P('Table 4 and Figure 4 show the effect of the reallocation threshold. In forward descent, lowering κ_{re} from 0.06 to 0.04 changed neither tracking nor lock-ups; it only raised the trigger rate from 2.3 to 11.5 events per second. In reverse descent, κ_{re} = 0.06 left 8 samples with lock-ups and κ_{re} = 0.05 left 2, while κ_{re} = 0.04 removed all of them. The same pattern held in the rough-terrain subset (A > 5 %, 152 samples). This is why the threshold is scheduled with direction.'));
C.push(...table('Table 4. Effect of the reallocation threshold on the proposed controller (N = 393 per direction).', ['κ_{re}', 'Direction', 'RMS error [km/h]', 'Max speed p95 [km/h]', 'Runs locked > 0.5 s', 'Triggers [1/s]', 'Pressure activity [bar/s]'], [
  ['0.06', 'Forward', '0.162', '4.86', '0', '2.3', '14.2'],
  ['0.04', 'Forward', '0.162', '4.87', '0', '11.5', '14.2'],
  ['0.06', 'Reverse', '0.244', '4.86', '8', '4.7', '15.4'],
  ['0.05', 'Reverse', '0.170', '4.83', '2', '7.5', '14.4'],
  ['0.04', 'Reverse', '0.161', '4.82', '0', '12.5', '14.3'],
], [900, 1200, 1400, 1500, 1460, 1300, 1600]));
C.push(...fig('fig5_threshold_margin.png', 3522, 1042, 'Figure 4. (a) Reverse maximum speed against the static friction margin; (b) number of samples with lock-ups by reallocation threshold; (c) reallocation trigger rate by threshold.'));
C.push(P('An earlier hypothesis was that the residual lock-ups at κ_{re} = 0.06 occurred in samples that were close to physically unholdable. Figure 4(a) contradicts this. With κ_{re} = 0.04, the controller held every one of those samples at or below 5.1 km/h, including one with a friction margin of 1.05 (μ = 0.45). The cause was therefore late reallocation, not physics. Excluding samples with a margin below 1.15 would have hidden a real controller weakness. By contrast, FF+PI locked in 71 reverse samples, 54 of them with a margin above 1.3.'));
C.push(H2('5.5 Design Iterations'));
C.push(P('The controller was developed iteratively, and the intermediate results are reported because two of them shape the final design (Table 5). First, a jerk limiter on the requested deceleration (A-FF+PI) gave no measurable reduction in jerk, because jerk in this setting is dominated by the terrain and by sensor noise passed through the feedforward. When the mass estimate first switched on, the limiter even produced a transient. It was therefore replaced by confidence blending of the mass estimate. Second, the first adaptive Kalman estimator (Q_{g} = 0.6) improved tracking but roughly tripled pressure activity compared with FF+PI. On the independent tuning set, lowering Q_{g} to 0.15 and adding the 1 bar hysteresis band restored the activity to the FF+PI level and halved the number of command reversals, at a small cost in RMS error.'));
C.push(...table('Table 5. Effect of estimator bandwidth and hysteresis on the proposed controller in forward descent.', ['Configuration', 'Data set', 'RMS error [km/h]', 'Pressure activity [bar/s]', 'Command reversals [1/s]'], [
  ['Q_{g} = 0.6, no hysteresis', 'Tuning (N = 120)', '0.149', '42.7', '—'],
  ['Q_{g} = 0.15, no hysteresis', 'Tuning (N = 120)', '0.154', '29.6', '—'],
  ['Q_{g} = 0.15, 1.0 bar band (final)', 'Tuning (N = 120)', '0.163', '14.3', '—'],
  ['Q_{g} = 0.15, 2.0 bar band', 'Tuning (N = 120)', '0.236', '8.2', '—'],
  ['FF+PI (reference)', 'Evaluation (N = 393)', '0.249', '13.6', '51.5'],
  ['Q_{g} = 0.15, 1.0 bar band (final)', 'Evaluation (N = 393)', '0.162', '14.2', '23.1'],
], [3000, 1800, 1400, 1580, 1580]));

// ---------- 6 Discussion
C.push(H1('6. Discussion and Limitations'));
C.push(P('The main finding is structural. A fixed front-biased brake distribution suits forward braking, where the load shifts forward, but it works against the load distribution in reverse descent. Speed-loop improvements alone, such as better grade feedforward or mass adaptation, did not reduce lock-ups. Reallocating pressure between the axles, driven only by wheel slip, did. The reallocation needs no friction or load estimate, so the extra computation is small. However, it requires the hydraulic unit to set the axle pressures independently, which is assumed here.'));
C.push(P('The results should be read in light of the following limitations:'));
C.push(BUL('All results are from simulation with generic parameters. No hardware-in-the-loop or vehicle data were used.'));
C.push(BUL('Load transfer is quasi-static, with no pitch, suspension or lateral dynamics. Split-μ and steering effects are not modelled.'));
C.push(BUL('The slip cap is a generic anti-lock-style limiter, not a production ABS, and the vehicle-speed reference is the largest wheel speed. A production system would use a more robust reference estimate.'));
C.push(BUL('Pressure activity is measured on the command signal. Valve hardware dynamics, noise and wear are not modelled, and the reverse trigger rate of about 12 events per second at κ_{re} = 0.04 needs to be assessed on a rig.'));
C.push(BUL('The threshold κ_{re} was selected on the evaluation set. The estimator and hysteresis settings were tuned on an independent set.'));
C.push(BUL('Only one target speed (4 km/h) was studied, and brake thermal fade was not coupled to the brake gain.'));
C.push(P('The planned next steps are a cross-check with an open multibody vehicle simulator, independent validation of κ_{re} on a new random set, and hardware-in-the-loop tests with a real hydraulic unit.'));

// ---------- 7 Conclusions
C.push(H1('7. Conclusions'));
C.push(P('A brake-only speed limiter for low-speed descent of steep grades was developed and evaluated in simulation in both directions of travel. Reverse descent with a fixed front brake bias caused front-axle lock and speed runaway in 16 % to 24 % of feasible Monte Carlo samples for all baselines, including a baseline with adaptive mass estimation. A slip-aware, direction-scheduled front/rear pressure reallocation removed these lock-ups (0 of 393 samples) and held the 95th-percentile maximum speed at 4.82 km/h for a 4 km/h target. Combined with a noise-adaptive grade estimator, confidence-blended effective-mass estimation and pressure-command hysteresis, the controller also reduced the forward RMS speed error by 35 % compared with feedforward–PI, at a similar pressure activity. Hardware validation of the reallocation logic is the essential next step.'));

// ---------- Declarations
C.push(H1('Declarations'));
C.push(P('Funding: [State funding, or "No funding was received for this work."]'));
C.push(P('Competing interests: [Declare any competing interests, including employer relationships, or state "The author has no competing interests to declare."]'));
C.push(P('Data and code availability: The simulation code, parameter samples and result tables are available at [repository URL / DOI].'));
C.push(P('Use of generative AI: Microsoft Copilot, a generative AI tool, was used to help write the simulation code, generate figures and draft this manuscript. The author reviewed and verified the code, results and text and takes full responsibility for the content. [Adjust this statement to match the actual use and the journal policy.]'));

// ---------- References
C.push(H1('References'));
const refs = [
  'Poojari, U., Westphalen, J. and Venugopal, N. (2026). Machine learning for predicting rotor and brake-fluid temperatures in hill-descent events. SAE Technical Paper 2026-01-0159. https://doi.org/10.4271/2026-01-0159',
  'Vahidi, A., Stefanopoulou, A. and Peng, H. (2005). Recursive least squares with forgetting for online estimation of vehicle mass and road grade: Theory and experiments. Vehicle System Dynamics 43, 1, 31–55. https://doi.org/10.1080/00423110412331290446',
  'Kidambi, N., Harne, R. L., Fujii, Y., Pietron, G. M. and Wang, K. W. (2014). Methods in vehicle mass and road grade estimation. SAE Int. J. Passenger Cars – Mechanical Systems 7, 3, 981–991. https://doi.org/10.4271/2014-01-0111',
  'Savaresi, S. M. and Tanelli, M. (2010). Active Braking Control Systems Design for Vehicles. Springer. London, UK.',
  'Pacejka, H. B. (2012). Tire and Vehicle Dynamics. 3rd edn. Butterworth-Heinemann. Oxford, UK.',
  'Mehra, R. K. (1970). On the identification of variances and adaptive Kalman filtering. IEEE Trans. Automatic Control 15, 2, 175–184.',
  'Ljung, L. (1999). System Identification: Theory for the User. 2nd edn. Prentice Hall. Upper Saddle River, NJ, USA.',
  'Åström, K. J. and Hägglund, T. (2006). Advanced PID Control. ISA. Research Triangle Park, NC, USA.',
  'Rajamani, R. (2012). Vehicle Dynamics and Control. 2nd edn. Springer. New York, NY, USA.',
];
refs.forEach(r => C.push(new Paragraph({ numbering: { reference: 'refs', level: 0 }, spacing: { after: 80 }, children: runs(r, { size: 20 }) })));
C.push(NOTE('[Before submission: expand the literature review with recent hill-descent, brake-distribution and slip-control papers, including IJAT papers, and verify every reference against the original source. Reference 9 is not yet cited in the text.]'));

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 24, bold: true, font: FONT }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 22, bold: true, italics: true, font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1, keepNext: true } },
    ]
  },
  numbering: {
    config: [
      { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'contrib', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '(%1)', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 420 } } } }] },
      { reference: 'refs', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '[%1]', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 540 } } } }] },
    ]
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 })] })] }) },
    children: C
  }]
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync('../../IJAT_Manuscript_BrakeOnly_SpeedLimiter_DRAFT.docx', b); console.log('written'); });
