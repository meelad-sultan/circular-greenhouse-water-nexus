"""Figures from the CSV/JSON files written by ``cgwn run``."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PAL = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02"]


def _save(fig, out: Path, name: str) -> Path:
    fig.tight_layout()
    fig.savefig(out / name, dpi=160)
    plt.close(fig)
    return out / name


def fig_baseline(res: Path, out: Path) -> Path:
    d = pd.read_csv(res / "baseline_daily.csv")
    sc = json.loads((res / "baseline_kpis.json").read_text())["scenario"]
    fig, ax = plt.subplots(3, 1, figsize=(9, 8.5), sharex=True)
    for i, (pol, g) in enumerate(d.groupby("policy", sort=False)):
        ax[0].plot(g.day, np.maximum(g.hi_mean, 1e-4), color=PAL[i], label=pol)
    ax[0].axhline(1, color="k", ls="--", lw=1)
    ax[0].set_yscale("log")
    ax[0].set_ylabel("Loop hazard index\n(sum of C/limit)")
    ax[0].legend(fontsize=8)
    ax[0].set_title(f"Scenario {sc}: irrigation-loop safety, bed loading and contaminant drivers", fontsize=10)
    g = d[d.policy == "sensor + guard"]
    for i, c in enumerate([c for c in d.columns if c.startswith("load_")]):
        ax[1].plot(g.day, g[c], color=PAL[i], label=c.replace("load_", "bed: "))
    ax[1].axhline(1, color="k", ls=":", lw=1)
    ax[1].set_ylabel("Bed loading S\n(sensor + guard)")
    ax[1].legend(fontsize=8, ncol=3)
    g0 = d[d.policy == "none"]
    for i, c in enumerate([c for c in d.columns if c.startswith("ratio_")]):
        ax[2].plot(g0.day, np.maximum(g0[c], 1e-4), color=PAL[i % 6], label=c.replace("ratio_", ""))
    ax[2].axhline(1, color="k", ls="--", lw=1)
    ax[2].set_yscale("log")
    ax[2].set_ylabel("C / limit per contaminant\n(no replacement)")
    ax[2].set_xlabel("Day of year")
    ax[2].legend(fontsize=7, ncol=3)
    return _save(fig, out, "fig1_baseline.png")


def fig_bleed(res: Path, out: Path) -> Path:
    b = pd.read_csv(res / "bleed_tradeoff.csv")
    g = b.groupby("bleed_ratio")
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.8))
    labels = ["Max loop hazard index", "Reuse fraction (1 - fresh/make-up)", "Annual cost (EUR)"]
    for a, col, lab in zip(ax, ["max_hi", "reuse_frac", "cost_eur"], labels, strict=True):
        m, s = g[col].mean(), g[col].std()
        a.errorbar(m.index, m.values, yerr=s.values, fmt="-o", color=PAL[0], capsize=3)
        a.set_xlabel("Bleed ratio (bleed / ET)")
        a.set_ylabel(lab)
    ax[0].axhline(1, color="k", ls="--", lw=1)
    fig.suptitle("Bleed trade-off (scenario S3, sensor + guard; mean +/- sd over replicates)", fontsize=10)
    return _save(fig, out, "fig2_bleed_tradeoff.png")


def fig_policies(res: Path, out: Path) -> Path:
    p = pd.read_csv(res / "policy_comparison.csv")
    scs = list(dict.fromkeys(p.scenario))
    pols = list(dict.fromkeys(p.policy))
    fig, ax = plt.subplots(2, len(scs), figsize=(4.2 * len(scs), 6), squeeze=False)
    for j, sc in enumerate(scs):
        for i, (col, lab) in enumerate((("exposure_h", "Hours with hazard index > 1"), ("cost_eur", "Annual cost (EUR)"))):
            g = p[p.scenario == sc].groupby("policy")[col]
            m, s = g.mean().reindex(pols), g.std().reindex(pols)
            ax[i, j].bar(range(len(pols)), m.values, yerr=s.values, color=PAL[: len(pols)], capsize=3)
            ax[i, j].set_xticks(range(len(pols)))
            ax[i, j].set_xticklabels(pols, rotation=40, ha="right", fontsize=7)
            ax[i, j].set_ylabel(lab)
            ax[0, j].set_title(f"Scenario {sc}", fontsize=10)
    return _save(fig, out, "fig3_policies.png")


def fig_detector(res: Path, out: Path) -> Path:
    d = pd.read_csv(res / "detector_oc.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    c0 = d[d.shift_sd == 0]
    ax[0].semilogy(c0.h, c0.arl_siegmund, "-", color="k", label="Siegmund approximation")
    ok = c0[c0.censored_frac < 0.05]
    ax[0].semilogy(ok.h, ok.arl_sim, "o", color=PAL[0], label="simulation (uncensored runs only)")
    ax[0].set_xlabel("CUSUM threshold h")
    ax[0].set_ylabel("In-control ARL0 (hours)")
    ax[0].legend(fontsize=8)
    for i, (s, g) in enumerate(d[d.shift_sd > 0].groupby("shift_sd")):
        ax[1].plot(g.h, g.arl_sim, "-o", color=PAL[i], label=f"shift {s:g} sd (sim)")
        ax[1].plot(g.h, g.arl_siegmund, ":", color=PAL[i])
    ax[1].set_xlabel("CUSUM threshold h")
    ax[1].set_ylabel("Detection delay (hours)")
    ax[1].legend(fontsize=8)
    fig.suptitle("CUSUM detector: false-alarm interval vs detection delay (dotted = approximation)", fontsize=10)
    return _save(fig, out, "fig4_detector_oc.png")


def fig_sensitivity(res: Path, out: Path) -> Path:
    s = pd.read_csv(res / "sensitivity_sobol.csv")
    outs = list(dict.fromkeys(s.output))
    fig, ax = plt.subplots(1, len(outs), figsize=(4.6 * len(outs), 4), squeeze=False)
    for a, o in zip(ax[0], outs, strict=True):
        g = s[s.output == o].sort_values("ST")
        y = np.arange(len(g))
        a.barh(y - 0.2, g.S1, 0.4, xerr=g.S1_conf, color=PAL[0], label="S1")
        a.barh(y + 0.2, g.ST, 0.4, xerr=g.ST_conf, color=PAL[1], label="ST")
        a.set_yticks(y)
        a.set_yticklabels(g.parameter, fontsize=8)
        a.set_title(o, fontsize=10)
        a.legend(fontsize=8)
    return _save(fig, out, "fig5_sensitivity.png")


def fig_pfas(res: Path, out: Path) -> Path:
    f = pd.read_csv(res / "pfas_robustness.csv")
    piv = f.pivot(index="draw", columns="policy", values="exposure_h")
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.scatter(piv["fixed 90 d"], piv["sensor"], color=PAL[2])
    lim = max(piv.max().max(), 1) * 1.05
    ax.plot([0, lim], [0, lim], "k--", lw=1)
    ax.set_xlabel("Hours HI > 1: fixed 90 d")
    ax.set_ylabel("Hours HI > 1: sensor (lab sampling)")
    ax.set_title("PFAS (exploratory): each point is one parameter draw", fontsize=9)
    return _save(fig, out, "fig6_pfas_robustness.png")


def make_all(res: str | Path, out: str | Path) -> list[Path]:
    res, out = Path(res), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(fig_baseline, "baseline_daily.csv"), (fig_bleed, "bleed_tradeoff.csv"), (fig_policies, "policy_comparison.csv"),
            (fig_detector, "detector_oc.csv"), (fig_sensitivity, "sensitivity_sobol.csv"), (fig_pfas, "pfas_robustness.csv")]
    return [fn(res, out) for fn, need in jobs if (res / need).exists()]
