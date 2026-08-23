from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

ANNUAL_KM = {"lower_use": 3218.688, "central_use": 10729.496448, "higher_use": 19312.128}
KWH_PER_KM = 0.09324077636479178
PACK_KWH = 77.413145
DT_H = 0.25
N_INTERVALS = 35064  # 365.25 days at 15-minute resolution


@dataclass(frozen=True)
class ProfileSpec:
    profile_id: str
    mileage_id: str = "central_use"
    temperature_case: str = "anchor"
    parked_soc_target: float = 0.70
    charge_events_per_week: int = 1
    charger_kw: float = 11.0
    parked_duration_case: str = "anchor"
    thermal_case: str = "managed"
    charging_policy: str = "balanced"


def profile_specs() -> list[ProfileSpec]:
    # Frozen E2: 1 anchor + 14 one-factor bounds + 2 coherent bundles.
    return [
        ProfileSpec("anchor"),
        ProfileSpec("annual_mileage_low", mileage_id="lower_use"),
        ProfileSpec("annual_mileage_high", mileage_id="higher_use"),
        ProfileSpec("cell_temperature_low", temperature_case="low"),
        ProfileSpec("cell_temperature_high", temperature_case="high"),
        ProfileSpec("parked_soc_low", parked_soc_target=0.35),
        ProfileSpec("parked_soc_high", parked_soc_target=0.88),
        ProfileSpec("charging_frequency_low", charge_events_per_week=1, charging_policy="home_23_to_08"),
        ProfileSpec("charging_frequency_high", charge_events_per_week=2, charger_kw=22.0, charging_policy="immediate"),
        ProfileSpec("charging_rate_low", charger_kw=3.7),
        ProfileSpec("charging_rate_high", charger_kw=150.0, charging_policy="immediate"),
        ProfileSpec("parked_duration_low", parked_duration_case="low"),
        ProfileSpec("parked_duration_high", parked_duration_case="high"),
        ProfileSpec("thermal_management_low", thermal_case="managed_low"),
        ProfileSpec("thermal_management_high", thermal_case="unmanaged_bounded"),
        ProfileSpec("joint_low_stress", mileage_id="lower_use", parked_soc_target=0.35,
                    charger_kw=3.7, charging_policy="home_23_to_08", temperature_case="low",
                    parked_duration_case="high", thermal_case="managed_low"),
        ProfileSpec("joint_high_stress", mileage_id="higher_use", parked_soc_target=0.88,
                    charge_events_per_week=2, charger_kw=75.0, charging_policy="immediate",
                    temperature_case="high", parked_duration_case="low", thermal_case="unmanaged_bounded"),
    ]


def _temperatures(spec: ProfileSpec, state: np.ndarray) -> np.ndarray:
    # Source-bounded proxy only. Wu's deposited driver states 15/35 C driving
    # setpoints and 30/50 C plug-in thresholds; TUM HPPC supplies 20/40 C test
    # levels. No ambient-to-cell substitution or thermophysical inference.
    if spec.temperature_case == "low" or spec.thermal_case == "managed_low":
        values = {"driving": 15.0, "charging": 30.0, "parked_not_charging": 20.0}
    elif spec.temperature_case == "high" or spec.thermal_case == "unmanaged_bounded":
        values = {"driving": 35.0, "charging": 50.0, "parked_not_charging": 40.0}
    else:
        values = {"driving": 25.0, "charging": 30.0, "parked_not_charging": 20.0}
    return np.array([values[item] for item in state], dtype=float)


def generate_profile(spec: ProfileSpec) -> tuple[pd.DataFrame, dict]:
    annual_km = ANNUAL_KM[spec.mileage_id]
    annual_energy = annual_km * KWH_PER_KM
    state = np.full(N_INTERVALS, "parked_not_charging", dtype=object)
    energy_delta = np.zeros(N_INTERVALS, dtype=float)
    distance = np.zeros(N_INTERVALS, dtype=float)
    weeks = np.arange(N_INTERVALS) // (7 * 96)
    week_ids = np.unique(weeks)
    # Whole-week energy is placed in deterministic trips. The final partial
    # week receives its exact proportional remainder; annual totals are exact.
    weights = np.array([(weeks == w).sum() for w in week_ids], dtype=float)
    week_energy = annual_energy * weights / weights.sum()
    drive_hour = 17 if spec.parked_duration_case != "low" else 8
    events = max(1, spec.charge_events_per_week)
    for pos, week in enumerate(week_ids):
        idx = np.flatnonzero(weeks == week)
        event_energy = week_energy[pos] / events
        for event in range(events):
            day_offset = int(event * max(1, 7 // events))
            start = idx[0] + min(len(idx) - 1, day_offset * 96 + drive_hour * 4)
            drive_slots = max(1, int(np.ceil(event_energy / (PACK_KWH * 0.8) * 8)))
            chosen = np.arange(start, min(start + drive_slots, idx[-1] + 1))
            if not len(chosen):
                chosen = np.array([idx[-1]])
            energy_delta[chosen] -= event_energy / len(chosen)
            distance[chosen] += (event_energy / KWH_PER_KM) / len(chosen)
            state[chosen] = "driving"
            if spec.charging_policy == "immediate":
                charge_start = int(chosen[-1] + 1)
            elif spec.charging_policy == "home_23_to_08":
                charge_start = int(idx[0] + min(len(idx) - 1, day_offset * 96 + 23 * 4))
                if charge_start <= chosen[-1]:
                    charge_start = int(chosen[-1] + 1)
            else:
                charge_start = int(chosen[-1] + 4)
            remaining = event_energy
            cursor = charge_start
            while remaining > 1e-12:
                if cursor >= N_INTERVALS:
                    cursor = max(0, int(chosen[0] - np.ceil(event_energy / (spec.charger_kw * DT_H))))
                if state[cursor] == "parked_not_charging":
                    amount = min(remaining, spec.charger_kw * DT_H)
                    energy_delta[cursor] += amount
                    state[cursor] = "charging"
                    remaining -= amount
                cursor += 1
    # Integrate around the preselected parked-SOC target. This target sets only
    # the initial condition; subsequent parked SOC emerges from energy balance.
    soc = np.empty(N_INTERVALS + 1, dtype=float)
    soc[0] = spec.parked_soc_target
    soc[1:] = soc[0] + np.cumsum(energy_delta) / PACK_KWH
    shift = 0.0
    if soc.min() < 0.1:
        shift = 0.1 - soc.min()
    if soc.max() + shift > 0.9:
        shift -= soc.max() + shift - 0.9
    soc += shift
    frame = pd.DataFrame({
        "profile_id": spec.profile_id,
        "interval_index": np.arange(N_INTERVALS, dtype=np.int32),
        "time_s": np.arange(N_INTERVALS, dtype=np.int64) * 900,
        "state": state,
        "distance_km": distance,
        "battery_energy_delta_kwh": energy_delta,
        "soc": soc[:-1],
        "cell_temperature_c": _temperatures(spec, state),
    })
    parked = frame.loc[frame.state.eq("parked_not_charging"), "soc"]
    bins = {
        "parked_soc_share_0_0p3": float((parked < 0.3).mean()),
        "parked_soc_share_0p3_0p7": float(((parked >= 0.3) & (parked <= 0.7)).mean()),
        "parked_soc_share_0p7_1": float((parked > 0.7).mean()),
    }
    summary = {
        **asdict(spec), "annual_km_target": annual_km,
        "annual_km_generated": float(frame.distance_km.sum()),
        "annual_battery_throughput_kwh_target": annual_energy,
        "annual_battery_throughput_kwh_generated": float(frame.loc[frame.battery_energy_delta_kwh < 0, "battery_energy_delta_kwh"].abs().sum()),
        "distance_relative_error": float(abs(frame.distance_km.sum() / annual_km - 1)),
        "throughput_relative_error": float(abs(frame.loc[frame.battery_energy_delta_kwh < 0, "battery_energy_delta_kwh"].abs().sum() / annual_energy - 1)),
        "soc_min": float(frame.soc.min()), "soc_max": float(frame.soc.max()), **bins,
        "temperature_implementation": "SOURCE-BOUNDED CELL-TEMPERATURE PROXY",
        "thermal_model_dependency_status": "Wu tum_model dependency absent; proxy authorized by P14.5S",
    }
    return frame, summary


def aggregate_hourly(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["hour"] = work.interval_index // 4
    hourly = work.groupby("hour", sort=True).agg(
        Time_s=("time_s", "min"), SOC=("soc", "mean"), Temperature_C=("cell_temperature_c", "mean"),
        distance_km=("distance_km", "sum"), battery_energy_delta_kwh=("battery_energy_delta_kwh", "sum"),
    ).reset_index(drop=True)
    return hourly
