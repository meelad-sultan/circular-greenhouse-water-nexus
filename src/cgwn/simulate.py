"""Hourly coupled simulation: greenhouse loop <-> storage tank <-> treatment train <-> sensors.

Per hour: crop transpiration sets make-up demand; a bleed leaves the loop and re-enters treatment with the
source intake; a sediment pre-filter acts on the source stream; each adsorption bed (cation / arsenic / PFAS)
filters its contaminants; treated water goes to the tank. Policies decide when beds are replaced and
whether the intake is blocked. Contaminant mass is tracked in ug and closes exactly (see mass_balance_rel_err).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np

from cgwn.adsorption import Bed
from cgwn.climate import et_m3_per_h, synth_climate
from cgwn.events import make_source
from cgwn.system import System, build_system


@dataclass
class Policy:
    replacement: str = "sensor"  # none | fixed | sensor
    guard: bool = True
    interval_days: float | None = None

    @property
    def label(self) -> str:
        return f"{self.replacement}{'+guard' if self.guard else ''}"


@dataclass
class SimResult:
    kpis: dict
    series: dict = field(default_factory=dict)


def simulate(sys_: System, clim, source, policy: Policy, rng, record: bool = False) -> SimResult:
    cfg, tk, lp, sn, cs, tr = sys_.cfg, sys_.tank, sys_.loop, sys_.sens, sys_.costs, sys_.treat
    csrc, tss = source
    H, n = clim.hours, sys_.n
    et = et_m3_per_h(clim, sys_.crop)
    limits, kup, phi, is_metal = sys_.limits, sys_.kup, sys_.phi, sys_.is_metal
    inv_lim = 1.0 / limits
    beds = [Bed(s) for s in sys_.beds]
    nb = len(beds)
    pfas_beds = [i for i, b in enumerate(beds) if (~is_metal[b.spec.idx]).any()]
    pfas_idx = np.flatnonzero(~is_metal)
    Vmax, VL, ratio, qcap, qsrc_max = tk["max_m3"], lp["volume_m3"], lp["bleed_ratio"], tk["q_cap"], tk["q_src_max"]
    on_frac = tk["intake_on_frac"]
    sd = sn["sd_frac"] * limits
    noise_eff = rng.standard_normal((H, n)) * sd
    noise_src = rng.standard_normal((H, n)) * sd
    lab_noise = rng.lognormal(0.0, sn["pfas_lab_sigma"], H)
    cus_k, cus_h = sn["cusum_k"], sn["cusum_h"]
    interval_h = int((policy.interval_days or cfg["policy_defaults"]["replace_interval_days"]) * 24)
    pf_cap, eta = tr["prefilter"]["capacity_kg"] * 1e6, tr["prefilter"]["tss_removal"]

    V_T, M_T, M_L = tk["start_frac"] * Vmax, np.zeros(n), np.zeros(n)
    S_cus, hold, pending = np.zeros(n), [0] * nb, deque()
    block_until, guard_run, base_hi = -1, 0, None
    in_src, out_pf, ads_tot, ov_mass, up_mass = (np.zeros(n) for _ in range(5))
    exc_h, n_repl = np.zeros(n), [0] * nb
    expo = bt_h = n_bw = premature = n_block = 0
    sum_fw = sum_mu = sum_in = sum_tank = ov_vol = pf_load = max_hi = sum_hi = 0.0
    if record:
        rec = {k: [] for k in ("hi", "cl", "smax", "vt", "fw", "et", "guard")}

    def replace(bi: int) -> None:
        nonlocal premature
        b = beds[bi]
        premature += int(b.smax() < 0.5)
        b.reset()
        n_repl[bi] += 1
        hold[bi] = int(sn["hold_h"])
        S_cus[b.spec.idx] = 0.0

    for t in range(H):
        ETt = et[t]
        Qb = min(ratio * ETt, qcap)
        Qmu = ETt + Qb
        C_T = M_T / (V_T * 1000.0) if V_T > 1e-9 else np.zeros(n)
        C_L = M_L / (VL * 1000.0)
        hi = float((C_L * inv_lim).sum())
        expo += hi > 1.0
        exc_h += C_L > limits
        sum_hi += hi
        max_hi = max(max_hi, hi)
        from_tank = min(Qmu, V_T)
        fw = Qmu - from_tank
        M_L = M_L + from_tank * 1000.0 * C_T - (Qb * 1000.0 + ETt * 1000.0 * kup) * C_L
        up_mass += ETt * 1000.0 * kup * C_L
        blocked = policy.guard and t < block_until
        n_block += blocked
        Qs = max(0.0, min(qsrc_max, qcap - Qb)) if (V_T < on_frac * Vmax and not blocked) else 0.0
        mass_src = Qs * 1000.0 * csrc[t]
        in_src += mass_src
        if Qs > 0.0:
            pf_load += eta * Qs * 1000.0 * tss[t]
            removed = eta * phi * mass_src
            out_pf += removed
            mass_src = mass_src - removed
            if pf_load >= pf_cap:
                pf_load, n_bw = 0.0, n_bw + 1
        mass_in = mass_src + Qb * 1000.0 * C_L
        Qin = Qs + Qb
        mass_out = mass_in.copy()
        for b in beds:
            mass_out[b.spec.idx] = b.apply(mass_in[b.spec.idx])
        ads_tot += mass_in - mass_out
        conc_out = mass_out / (Qin * 1000.0) if Qin > 1e-12 else np.zeros(n)
        bt_h += bool((conc_out > limits).any())
        V_new = V_T + Qin - from_tank
        M_new = M_T + mass_out - from_tank * 1000.0 * C_T
        if V_new > Vmax:
            ov = V_new - Vmax
            M_new = M_new - ov * 1000.0 * C_T
            ov_mass += ov * 1000.0 * C_T
            ov_vol += ov
            V_new = Vmax
        V_T, M_T = V_new, M_new
        sum_fw += fw
        sum_mu += Qmu
        sum_in += Qin
        sum_tank += from_tank
        # ---- sensing and policy ------------------------------------------------------------------
        for i in range(nb):
            hold[i] -= 1
        if policy.replacement == "fixed":
            if (t + 1) % interval_h == 0:
                for i in range(nb):
                    replace(i)
        elif policy.replacement == "sensor":
            y = conc_out + noise_eff[t]  # signed (blank-corrected) reading: iid normal when in control
            S_cus = np.where(is_metal, np.maximum(0.0, S_cus + y * inv_lim / sn["sd_frac"] - cus_k), 0.0)
            for i, b in enumerate(beds):
                if i not in pfas_beds and hold[i] <= 0 and (S_cus[b.spec.idx] > cus_h).any():
                    replace(i)
            if t % sn["pfas_lab_interval_h"] == 0 and len(pfas_idx):
                pending.append((t + sn["pfas_lab_delay_h"], conc_out[pfas_idx] * lab_noise[t]))
            while pending and pending[0][0] <= t:
                vals = pending.popleft()[1]
                if (vals * inv_lim[pfas_idx]).max() > sn["pfas_trigger_frac"]:
                    for i in pfas_beds:
                        if hold[i] <= 0:
                            replace(i)
        if policy.guard:
            y_src = csrc[t] + noise_src[t]
            hi_src = float((y_src[is_metal] * inv_lim[is_metal]).sum())
            base_hi = hi_src if base_hi is None else base_hi
            alarm = hi_src > max(sn["guard_min_hi"], sn["guard_ratio"] * base_hi)
            guard_run = guard_run + 1 if alarm else 0
            if not alarm:
                base_hi = (1 - sn["guard_ewma"]) * base_hi + sn["guard_ewma"] * hi_src
            if guard_run >= 2:
                block_until = t + 1 + int(sn["guard_hold_h"])
        if record:
            rec["hi"].append(hi)
            rec["cl"].append(C_L.copy())
            rec["smax"].append([b.smax() for b in beds])
            rec["vt"].append(V_T)
            rec["fw"].append(fw)
            rec["et"].append(ETt)
            rec["guard"].append(int(blocked))

    storage = M_T + M_L
    resid = in_src - (out_pf + ads_tot + ov_mass + up_mass + storage)
    energy = tr["e_pump_kwh_m3"] * sum_mu + tr["e_treat_kwh_m3"] * sum_in + tr["prefilter"]["backwash_kwh"] * n_bw
    media = sum(n_repl[i] * (b.spec.labour_eur + b.spec.mass_kg * (b.spec.media_eur_kg + b.spec.disposal_eur_kg))
                for i, b in enumerate(beds))
    k = {
        "exposure_h": float(expo), "exposure_frac": expo / H, "max_hi": max_hi, "mean_hi": sum_hi / H,
        "bed_breakthrough_h": float(bt_h), "freshwater_m3": sum_fw, "reuse_frac": 1.0 - sum_fw / max(sum_mu, 1e-12),
        "replacements": float(sum(n_repl)), "premature_replacements": float(premature),
        "backwashes": float(n_bw), "guard_block_h": float(n_block), "overflow_m3": ov_vol,
        "energy_kwh": energy, "energy_kwh_per_m3_reused": energy / max(sum_tank, 1e-12),
        "co2_kg": energy * cs["grid_kg_co2_kwh"],
        "cost_eur": energy * cs["elec_eur_kwh"] + sum_fw * cs["freshwater_eur_m3"] + media, "media_cost_eur": media,
        "n_offset_note": 0.0, "mass_balance_rel_err": float(np.abs(resid).sum() / max(in_src.sum(), 1e-12)),
        "et_m3": float(et.sum()),
    }
    for nm, e in zip(sys_.names, exc_h, strict=True):
        k[f"exceed_h_{nm}"] = float(e)
    for i, b in enumerate(beds):
        k[f"replacements_{b.spec.name}"] = float(n_repl[i])
    series = {}
    if record:
        series = {"hi": np.array(rec["hi"]), "cl": np.array(rec["cl"]), "smax": np.array(rec["smax"]),
                  "vt": np.array(rec["vt"]), "fw": np.array(rec["fw"]), "et": np.array(rec["et"]),
                  "guard": np.array(rec["guard"]), "bed_names": [b.spec.name for b in beds]}
    return SimResult(k, series)


def run_scenario(cfg: dict, scenario: str, policy: Policy, seed: int, days: int | None = None,
                 record: bool = False) -> SimResult:
    """Run one simulated year (or ``days``) of ``scenario``. Same seed => same weather, events and noise."""
    days = days or cfg["horizon_days"]
    ss = np.random.SeedSequence(int(seed))
    r_clim, r_src, r_sim = (np.random.default_rng(s) for s in ss.spawn(3))
    sys_ = build_system(cfg)
    clim = synth_climate(sys_.site, days, r_clim)
    source = make_source(cfg, scenario, clim.hours, r_src)
    return simulate(sys_, clim, source, policy, r_sim, record)
