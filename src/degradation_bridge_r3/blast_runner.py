from __future__ import annotations

import sys
import types
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BLAST_ROOT = ROOT / "data/raw/SRC_BLAST_LITE"
sys.dont_write_bytecode = True
if str(BLAST_ROOT) not in sys.path:
    sys.path.insert(0, str(BLAST_ROOT))
# BLAST-Lite imports its optional HSDS client at package import although the
# degradation models used here never call it. A no-I/O placeholder keeps the
# pinned scientific model code unchanged.
if "h5pyd" not in sys.modules:
    sys.modules["h5pyd"] = types.ModuleType("h5pyd")
if "geopy" not in sys.modules:
    geopy = types.ModuleType("geopy")
    geocoders = types.ModuleType("geopy.geocoders")
    geocoders.Nominatim = object
    geopy.geocoders = geocoders
    sys.modules["geopy"] = geopy
    sys.modules["geopy.geocoders"] = geocoders

from blast import models  # noqa: E402

MODEL_CLASSES = {
    "Nmc622_Gr_DENSO50Ah_Battery": models.Nmc622_Gr_DENSO50Ah_Battery,
    "Nmc811_GrSi_LGMJ1_4Ah_Battery": models.Nmc811_GrSi_LGMJ1_4Ah_Battery,
    "NMC_Gr_75Ah_A": models.NMC_Gr_75Ah_A,
    "NMC_Gr_50Ah_B1": models.NMC_Gr_50Ah_B1,
    "NMC_Gr_50Ah_B2": models.NMC_Gr_50Ah_B2,
    "Nmc811_GrSi_LGM50_5Ah_Battery": models.Nmc811_GrSi_LGM50_5Ah_Battery,
}
PRIMARY = {"Nmc622_Gr_DENSO50Ah_Battery", "Nmc811_GrSi_LGMJ1_4Ah_Battery"}


def input_domain(model, hourly: pd.DataFrame) -> tuple[bool, str, dict]:
    limits = model.experimental_range
    tmin, tmax = limits["cycling_temperature"]
    socmin, socmax = limits["soc"]
    delta_soc = np.abs(np.diff(hourly.SOC.to_numpy(), prepend=hourly.SOC.iloc[0]))
    # Contiguous charge/discharge swings, not 15-minute micro-steps.
    direction = np.sign(hourly.battery_energy_delta_kwh.to_numpy())
    turning = np.r_[True, direction[1:] != direction[:-1]]
    extrema = hourly.loc[turning, "SOC"].to_numpy()
    dod = np.abs(np.diff(extrema)) if len(extrema) > 1 else np.array([0.0])
    nonzero_dod = dod[dod > 1e-8]
    max_charge_c = float(hourly.battery_energy_delta_kwh.clip(lower=0).max() * 4 / 77.413145)
    max_discharge_c = float((-hourly.battery_energy_delta_kwh.clip(upper=0)).max() * 4 / 77.413145)
    checks = {
        "temperature": bool(hourly.Temperature_C.between(tmin, tmax, inclusive="both").all()),
        "soc": bool(hourly.SOC.between(socmin, socmax, inclusive="both").all()),
        "charge_rate": max_charge_c <= limits["max_rate_charge"] + 1e-12,
        "discharge_rate": max_discharge_c <= limits["max_rate_discharge"] + 1e-12,
        "dod": bool(len(nonzero_dod) and nonzero_dod.max() >= limits["dod"][0] - 1e-12 and nonzero_dod.max() <= limits["dod"][1] + 1e-12),
    }
    audit = {**checks, "max_charge_c": max_charge_c, "max_discharge_c": max_discharge_c,
             "max_cycle_dod": float(nonzero_dod.max()) if len(nonzero_dod) else 0.0,
             "experimental_range": limits}
    ok = all(checks.values())
    return ok, "IN_DOMAIN" if ok else "CAPACITY MODEL MEMBER OUTSIDE VALIDATED INPUT DOMAIN", audit


def run_model(model_name: str, profile_id: str, hourly: pd.DataFrame, years: int = 25) -> tuple[pd.DataFrame, dict]:
    model = MODEL_CLASSES[model_name](degradation_scalar=1)
    ok, status, audit = input_domain(model, hourly)
    base = {
        "model_name": model_name, "profile_id": profile_id,
        "model_role": "PRIMARY_NON_AVERAGED" if model_name in PRIMARY else "STRUCTURAL_SENSITIVITY",
        "degradation_scalar": 1.0, "source_native_parameters": True,
        "input_domain_status": status,
    }
    if not ok:
        rows = [{**base, "age_years": float(y), "calendar_year": 2025 + y,
                 "capacity_retention": np.nan, "capacity_state_status": "CAPACITY STATE UNSUPPORTED",
                 "long_horizon_label": "MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION" if y > 3 else "DIRECT FIELD WINDOW"}
                for y in range(years + 1)]
        return pd.DataFrame(rows), audit
    data = {"Time_s": hourly.Time_s.to_numpy(), "SOC": hourly.SOC.to_numpy(),
            "Temperature_C": hourly.Temperature_C.to_numpy()}
    model.simulate_battery_life(data, threshold_time=years, is_constant_input=True,
                                is_conserve_energy_throughput=True)
    t_years = model.stressors["t_days"] / 365.0
    q = model.outputs["q"]
    rows = []
    for year in range(years + 1):
        idx = int(np.argmin(np.abs(t_years - year)))
        value = float(q[idx])
        rows.append({**base, "age_years": float(year), "calendar_year": 2025 + year,
                     "capacity_retention": value,
                     "capacity_state_status": "MODELED" if value > 0 else "CAPACITY STATE UNSUPPORTED",
                     "long_horizon_label": "MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION" if year > 3 else "DIRECT FIELD WINDOW"})
    return pd.DataFrame(rows), audit
