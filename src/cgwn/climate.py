"""Synthetic hourly greenhouse climate (NW-European style) and crop water demand.

Illustrative generator, NOT observed weather. A CSV loader is provided for real data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

LATENT_HEAT_J_PER_KG = 2.45e6


@dataclass
class Climate:
    r_in: np.ndarray  # radiation inside the greenhouse, W/m2
    vpd: np.ndarray  # vapour pressure deficit inside, kPa
    doy: np.ndarray  # day of year for each hour (1..365)

    @property
    def hours(self) -> int:
        return len(self.r_in)


def _ar1(n: int, phi: float, rng: np.random.Generator) -> np.ndarray:
    x = np.zeros(n)
    e = rng.normal(0, np.sqrt(1 - phi**2), n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + e[i]
    return x


def synth_climate(site: dict, days: int, rng: np.random.Generator) -> Climate:
    h = days * 24
    t = np.arange(h)
    doy = (t // 24) % 365 + 1
    hod = t % 24
    phi = np.radians(site["latitude"])
    decl = np.radians(23.45) * np.sin(2 * np.pi * (284 + doy) / 365)
    sin_alt = np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.cos(np.radians(15.0 * (hod - 12)))
    clear = 1000.0 * np.clip(sin_alt, 0, None) ** 1.15 * 0.75
    kd = np.clip(0.7 + 0.2 * _ar1(days, 0.6, rng), 0.15, 1.0)
    r_out = clear * np.repeat(kd, 24)[:h]
    seasonal = 10.0 - 8.0 * np.cos(2 * np.pi * (doy - 15) / 365)
    amp = 4.0 - 1.5 * np.cos(2 * np.pi * (doy - 15) / 365)
    t_out = seasonal + amp * np.sin(2 * np.pi * (hod - 9) / 24) + np.repeat(_ar1(days, 0.7, rng) * 2.0, 24)[:h]
    r_in = site["transmissivity"] * r_out
    t_in = np.clip(t_out + 0.01 * r_in, site["t_min_inside"], site["t_max_inside"])
    es = 0.6108 * np.exp(17.27 * t_in / (t_in + 237.3))
    return Climate(r_in, es * (1.0 - site["rh_inside"]), doy)


def load_climate_csv(path: str, site: dict) -> Climate:
    """CSV columns: radiation_wm2 (outside), temp_c (outside); optional rh (0..1)."""
    df = pd.read_csv(path)
    r_in = site["transmissivity"] * df["radiation_wm2"].to_numpy(float)
    t_out = df["temp_c"].to_numpy(float)
    t_in = np.clip(t_out + 0.01 * r_in, site["t_min_inside"], site["t_max_inside"])
    rh = df["rh"].to_numpy(float) if "rh" in df else np.full(len(df), site["rh_inside"])
    es = 0.6108 * np.exp(17.27 * t_in / (t_in + 237.3))
    return Climate(r_in, es * (1.0 - rh), (np.arange(len(df)) // 24) % 365 + 1)


def crop_factor(doy: np.ndarray, crop: dict) -> np.ndarray:
    cf = np.where(
        doy <= crop["ramp_days"],
        crop["crop_min"] + (1 - crop["crop_min"]) * doy / crop["ramp_days"],
        np.where(doy <= crop["end_doy"], 1.0, 1 - (1 - crop["crop_final"]) * (doy - crop["end_doy"]) / (365 - crop["end_doy"])),
    )
    return np.clip(cf, 0.05, 1.0)


def et_m3_per_h(clim: Climate, crop: dict) -> np.ndarray:
    """Crop transpiration (m3/h): radiation term + VPD term, scaled by canopy development."""
    rad = crop["f_rad"] * clim.r_in * 3600.0 / LATENT_HEAT_J_PER_KG
    vpd = crop["c_vpd"] * clim.vpd * (0.3 + 0.7 * np.minimum(1.0, clim.r_in / 100.0))
    return crop_factor(clim.doy, crop) * (rad + vpd) * crop["area_m2"] / 1000.0
