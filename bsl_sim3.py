"""
v0.3/v0.4 - Brake-Only Low-Speed Limiting on Steep Grades (open, reproducible; NumPy only)

Plant  : longitudinal vehicle on position-dependent grade, quasi-static load transfer,
         per-axle wheel rotational dynamics + Pacejka-type longitudinal tire (slip / lock),
         4LOW creep / engine-brake force, hydraulic actuator per axle (dead time + lag + rate limit),
         lumped brake thermal model, noisy wheel-speed and accelerometer sensors.
         Forward (nose downhill) and reverse (nose uphill) descent.
Layer  : generic ABS-like per-axle slip cap for ALL controllers; slip-aware front/rear
         reallocation for PROP2/PROP3 only.
Ctrls  : PI, RB (rule-based), FFPI (ablation), PROP1 (v1: LPF grade + RLS + jerk limiter),
         PROP2 (v2: adaptive-KF grade + blended RLS + reallocation),
         PROP3 (v3: PROP2 + tunable KF bandwidth Qg + pressure-command hysteresis band db).
All parameters generic / textbook-representative (no OEM / supplier data).
"""
import numpy as np

G = 9.81
VEH = dict(
    m_nom=2500.0, L=3.0, lr=1.5, h=0.75, cr=0.015, CdA=1.0,
    Kb_nom=250.0, front_share=0.65, p_max=180.0, p_rate=400.0,
    tau_nom=0.10, td_nom=0.04, C_axle=7000.0, h_cool=20.0, T_amb=25.0,
    v_idle=1.4, Kpt_nom=3000.0, F_eb_max=1470.0, F_cr_max=1200.0,
    r_w=0.38, I_axle=2.4, B=10.0, Cp=1.65, v_eps=0.5,
)
V_REF = 4.0 / 3.6
DT, DTC = 1e-3, 1e-2
SLIP = dict(cap=0.15, re=0.06)


def grade_profile(s, Gmax, A, ph):
    env = np.clip((s - 2.0) / 4.0, 0, 1) * np.clip((34.0 - s) / 4.0, 0, 1)
    rough = A * (np.sin(2*np.pi*s/8.0 + ph[:, 0]) + 0.6*np.sin(2*np.pi*s/3.0 + ph[:, 1])
                 + 0.3*np.sin(2*np.pi*s/1.2 + ph[:, 2])) / 1.9
    return env * (Gmax + rough)


def f_pt(v, Kpt, P=VEH):
    return np.clip(Kpt * (P['v_idle'] - v), -P['F_eb_max'], P['F_cr_max'])


def tire(kappa, mu, Fz, P=VEH):
    B, C = P['B'], P['Cp']
    u = B*kappa; at = np.arctan(u)
    return mu*Fz*np.sin(C*at), mu*Fz*np.cos(C*at)*C*B/(1+u**2)


class SVF:
    def __init__(self, N, f=3.0, z=0.8, x0=0.0):
        self.wn, self.z = 2*np.pi*f, z
        self.x1 = np.full(N, x0, float); self.x2 = np.zeros(N)

    def step(self, u, dt):
        self.x2 += dt*(self.wn**2*(u - self.x1) - 2*self.z*self.wn*self.x2)
        self.x1 += dt*self.x2
        return self.x1, self.x2


class Controller:
    KP, KI, JERK = 2.0, 1.0, 2.5

    def __init__(self, kind, N, v0, P=VEH, Qg=0.6, db=0.0):
        self.v3 = kind == 'PROP3'
        self.k = 'PROP2' if self.v3 else kind
        self.P, self.N, self.Qg, self.db = P, N, Qg, (db if self.v3 else 0.0)
        self.vf = np.full(N, v0); self.I = np.zeros(N); self.areq = np.zeros(N)
        self.p_rb = np.zeros(N); self.p_hold = np.zeros(N)
        self.svf_v, self.svf_a, self.svf_y = SVF(N, x0=v0), SVF(N), SVF(N)
        self.gs = np.zeros(N); self.Pg = np.full(N, 1.0); self.Rg = np.full(N, 0.05)
        self.m = np.full(N, P['m_nom'])
        self.Pr0 = 1e4 if self.k == 'PROP1' else 2e3
        self.Pr = np.full(N, self.Pr0)
        self.w = np.zeros(N); self.m_use = np.full(N, P['m_nom']); self.mrec = self.m_use
        self.pm_buf = np.zeros((int(round(P['td_nom']/DTC)) + 1, N)); self.pm = np.zeros(N)
        self.p_cmd = np.zeros(N)

    def step(self, v_meas, a_meas):
        P, dt = self.P, DTC
        self.vf += dt/0.016*(v_meas - self.vf)
        e = self.vf - V_REF
        if self.k == 'RB':
            up = (8.0 + 25.0*e)*(e > 0.10); dn = 10.0*(e < -0.10)
            self.p_rb = np.clip(self.p_rb + (up - dn)*dt, 0, P['p_max'])
            self.p_cmd = self.p_rb
            return self.p_cmd
        _, vdot = self.svf_v.step(v_meas, dt)
        a_f, _ = self.svf_a.step(a_meas, dt)
        z = vdot - a_f
        if self.k == 'PROP2':
            Pp = self.Pg + self.Qg*dt
            r = z - self.gs
            K = Pp/(Pp + self.Rg)
            self.gs += K*r
            self.Pg = (1 - K)*Pp
            self.Rg = np.clip(self.Rg + dt/1.5*(np.clip(r**2 - Pp, 0.0, 4.0) - self.Rg), 0.01, 4.0)
        else:
            self.gs += dt/0.15*(z - self.gs)
        self.pm_buf = np.roll(self.pm_buf, 1, axis=0); self.pm_buf[0] = self.p_cmd
        self.pm += dt/P['tau_nom']*(self.pm_buf[-1] - self.pm)
        aero = 0.5*1.2*P['CdA']*self.vf**2
        y, _ = self.svf_y.step(P['Kb_nom']*self.pm - f_pt(self.vf, P['Kpt_nom']) + aero, dt)
        if self.k in ('PROP1', 'PROP2'):
            phi = -(a_f + P['cr']*G)
            upd = (phi > 0.4) & (self.pm > 3.0)
            lam = 0.995
            K = self.Pr*phi/(lam + phi**2*self.Pr)
            self.m = np.where(upd, np.clip(self.m + K*(y - phi*self.m), 0.5*P['m_nom'], 2.0*P['m_nom']), self.m)
            self.Pr = np.where(upd, np.minimum((self.Pr - K*phi*self.Pr)/lam, self.Pr0), self.Pr)
            if self.k == 'PROP1':
                m_use = self.m
            else:
                conf = np.clip(1.0 - self.Pr/self.Pr0, 0, 1)**0.5
                self.w += np.clip(conf - self.w, -0.5*dt, 0.5*dt)
                tgt = P['m_nom'] + self.w*(self.m - P['m_nom'])
                self.m_use += np.clip(tgt - self.m_use, -400*dt, 400*dt)
                m_use = self.m_use
        else:
            m_use = np.full(self.N, P['m_nom'])
        a_ff = 0.0 if self.k == 'PI' else self.gs - P['cr']*G + (f_pt(self.vf, P['Kpt_nom']) - aero)/m_use
        raw = a_ff + self.KP*e + self.KI*self.I
        a_max = P['p_max']*P['Kb_nom']/m_use
        freeze = ((raw <= 0) & (e < 0)) | ((raw >= a_max) & (e > 0))
        self.I = np.clip(self.I + np.where(freeze, 0.0, e*dt), -3.0, 6.0)
        tgt = np.clip(raw, 0, a_max)
        if self.k == 'PROP1':
            self.areq += np.clip(tgt - self.areq, -self.JERK*dt, self.JERK*dt)
        else:
            self.areq = tgt
        p_new = np.clip(m_use*self.areq/P['Kb_nom'], 0, P['p_max'])
        if self.db > 0:
            mv = (np.abs(p_new - self.p_hold) > self.db) | (p_new < 0.5) | (np.abs(e) > 0.25)
            self.p_hold = np.where(mv, p_new, self.p_hold)
            p_new = self.p_hold
        self.p_cmd = p_new
        self.mrec = m_use
        return self.p_cmd


class SlipLayer:
    def __init__(self, N, realloc, P=VEH):
        self.c = np.ones((2, N)); self.phi = np.full(N, P['front_share'])
        self.realloc, self.P = realloc, P
        self.n_switch = np.zeros(N); self._last = np.zeros(N)

    def step(self, wabs, p_cmd, dt=DTC):
        r = self.P['r_w']; vref = np.max(wabs, 0)*r
        kap = (wabs*r - vref)/np.maximum(vref, 0.5)
        self.c = np.clip(self.c + np.where(kap < -SLIP['cap'], -4.0*dt, 1.0*dt), 0.0, 1.0)
        if self.realloc:
            ff, rr = kap[0] < -SLIP['re'], kap[1] < -SLIP['re']
            mode = np.where(ff & ~rr, -1.0, np.where(rr & ~ff, 1.0, 0.0))
            self.n_switch += (mode != self._last) & (mode != 0)
            self._last = mode
            dphi = np.where(mode < 0, -0.6*dt, np.where(mode > 0, 0.6*dt,
                            0.1*dt*np.sign(self.P['front_share'] - self.phi)))
            self.phi = np.clip(self.phi + dphi, 0.30, 0.80)
        return self.c*np.vstack([self.phi, 1 - self.phi])*p_cmd


def sample_params(N, rng):
    return dict(
        mf=rng.uniform(0.75, 1.30, N), Gmax=rng.uniform(0.05, 0.45, N),
        A=rng.uniform(0.0, 0.08, N), ph=rng.uniform(0, 2*np.pi, (N, 3)),
        mu=rng.uniform(0.45, 0.90, N), kbf=rng.uniform(0.85, 1.15, N),
        tau=rng.uniform(0.07, 0.15, N), td=rng.uniform(0.02, 0.06, N),
        kptf=rng.uniform(0.7, 1.3, N), abias=rng.uniform(-0.1, 0.1, N))


def friction_margin(prm):
    """Static holdability margin mu*cos(theta)/sin(theta) at the steepest point (all-wheel braking)."""
    gm = np.arctan(prm['Gmax'] + prm['A'])
    return prm['mu']*np.cos(gm)/np.sin(gm)


def simulate(kind, prm, direction=+1, T=40.0, seed=1, P=VEH, Qg=0.6, db=0.0):
    rng = np.random.default_rng(seed)
    N = len(prm['mf']); ar = np.arange(N); dr = float(direction)
    m = P['m_nom']*prm['mf']; Kb = P['Kb_nom']*prm['kbf']; Kpt = P['Kpt_nom']*prm['kptf']
    r, Iw, ve = P['r_w'], P['I_axle'], P['v_eps']
    d = np.round(prm['td']/DT).astype(int); Lb = d.max() + 2
    buf = np.zeros((Lb, 2, N)); sl = SlipLayer(N, kind in ('PROP2', 'PROP3'), P); u_cmd = np.zeros((2, N))
    v = np.full(N, dr*V_REF); s = np.zeros(N); p = np.zeros((2, N))
    w = np.vstack([v/r, v/r]); Tw = np.full((2, N), P['T_amb'])
    ctrl = Controller(kind, N, V_REF, P, Qg, db)
    nc = int(round(DTC/DT)); steps = int(T/DT); nrec = steps//nc
    rec = {k: np.zeros((nrec, N), np.float32) for k in ['v', 'a', 'p', 'pc', 'grade', 'Tf', 'mhat', 'gs', 'kf', 'kr', 'phi']}
    a_acc = np.zeros(N); a_last = np.zeros(N); gx = np.zeros(N); th = np.zeros(N)
    p_cmd = np.zeros(N); lock_acc = np.zeros(N)
    for k in range(steps):
        if k % nc == 0:
            j = k//nc
            v_ws = np.max(np.abs(w), axis=0)*r + rng.normal(0, 0.02, N)
            a_spec = a_last - gx + prm['abias'] + rng.normal(0, 0.05, N)
            p_cmd = ctrl.step(v_ws, dr*a_spec)
            u_cmd = sl.step(np.abs(w) + rng.normal(0, 0.02/r, (2, N)), p_cmd)
            if j > 0:
                rec['a'][j-1] = a_acc/nc
            a_acc[:] = 0
            kap = (w*r - v)/np.maximum(np.abs(v), ve)
            rec['v'][j] = np.abs(v); rec['p'][j] = p.sum(0); rec['pc'][j] = p_cmd
            rec['grade'][j] = np.tan(th); rec['Tf'][j] = Tw[0]; rec['mhat'][j] = ctrl.mrec
            rec['gs'][j] = ctrl.gs; rec['kf'][j] = kap[0]; rec['kr'][j] = kap[1]; rec['phi'][j] = sl.phi
        buf[k % Lb] = u_cmd
        p += DT*np.clip((buf[(k - d) % Lb, :, ar].T - p)/prm['tau'], -P['p_rate'], P['p_rate'])
        th = np.arctan(grade_profile(s, prm['Gmax'], prm['A'], prm['ph']))
        sn, cs = np.sin(th), np.cos(th)
        gx = dr*G*sn
        Fzf = np.clip((m*G*cs*P['lr'] + P['h']*m*(gx - a_last))/P['L'], 0.05*m*G, 0.95*m*G)
        Fz = np.vstack([Fzf, m*G*cs - Fzf])
        den = np.maximum(np.abs(v), ve)
        Fx, dF = tire((w*r - v)/den, prm['mu'], Fz, P)
        kw = np.maximum(dF, 0.0)*r/den
        Tpt = dr*f_pt(np.abs(v), Kpt, P)*r/2.0
        Tb = Kb*p*r
        g = DT/Iw
        rhs = (w + g*(-r*Fx + r*kw*w + Tpt))/(1 + g*r*kw)
        Db = g*Tb/(1 + g*r*kw)
        w = np.where(np.abs(rhs) <= Db, 0.0, rhs - np.sign(rhs)*Db)
        kap = (w*r - v)/den
        Fx, _ = tire(kap, prm['mu'], Fz, P)
        res = (P['cr']*m*G*cs + 0.5*1.2*P['CdA']*v**2)*np.tanh(v/0.05)
        v_new = v + ((Fx.sum(0) - res)/m + gx)*DT
        a_last = (v_new - v)/DT
        Tw += DT*(Tb*np.abs(w) - P['h_cool']*(Tw - P['T_amb']))/P['C_axle']
        s += np.abs(v)*DT; v = v_new
        a_acc += dr*a_last
        lock_acc += ((np.abs(kap) > 0.5).any(0) & (np.abs(v) > 0.2))*DT
    rec['a'][-1] = a_acc/nc
    rec['t'] = np.arange(nrec)*DTC
    rec['lock'] = lock_acc
    rec['n_switch'] = sl.n_switch / T
    return rec
