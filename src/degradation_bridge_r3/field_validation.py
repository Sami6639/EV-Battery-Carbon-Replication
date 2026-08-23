from __future__ import annotations

import json
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def _nearest_envelope(model: pd.DataFrame, coordinate: str, value: float) -> tuple[float, float, bool]:
    members = []
    for (_, _), group in model.loc[model.capacity_state_status.eq("MODELED")].groupby(["model_name", "profile_id"], sort=True):
        group = group.sort_values(coordinate)
        x, y = group[coordinate].to_numpy(), group.capacity_retention.to_numpy()
        if len(x) > 1 and x.min() <= value <= x.max():
            members.append(float(np.interp(value, x, y)))
    if not members:
        return np.nan, np.nan, False
    return min(members), max(members), True


def _score_rows(rows: pd.DataFrame, source_id: str, label_ceiling: str | None = None) -> tuple[pd.DataFrame, dict]:
    comparable = rows.loc[rows.comparable].copy()
    if comparable.empty:
        return rows, {"source_id": source_id, "status": "FAIL", "reason": "NO_COMPARABLE_FIELD_POINTS"}
    comparable["signed_error_pp"] = np.where(
        comparable.observed_retention < comparable.envelope_lower,
        (comparable.envelope_lower - comparable.observed_retention) * 100,
        np.where(comparable.observed_retention > comparable.envelope_upper,
                 (comparable.envelope_upper - comparable.observed_retention) * 100, 0.0))
    comparable["absolute_error_pp"] = comparable.signed_error_pp.abs()
    comparable["covered"] = comparable.absolute_error_pp.eq(0)
    comparable["envelope_width_pp"] = (comparable.envelope_upper - comparable.envelope_lower) * 100
    metrics = {
        "source_id": source_id, "n": int(len(comparable)),
        "median_absolute_error_pp": float(comparable.absolute_error_pp.median()),
        "signed_median_bias_pp": float(comparable.signed_error_pp.median()),
        "envelope_coverage_percent": float(comparable.covered.mean() * 100),
        "median_envelope_width_pp": float(comparable.envelope_width_pp.median()),
    }
    # Scored strata: only pre-outcome age/use bins with n>=20.
    stratum_medians = comparable.groupby("validation_stratum", sort=True).absolute_error_pp.agg(["median", "size"])
    scored = stratum_medians.loc[stratum_medians["size"] >= 20, "median"]
    metrics["maximum_scored_stratum_mdae_pp"] = float(scored.max()) if len(scored) else np.nan
    p = metrics["median_absolute_error_pp"] <= 3 and abs(metrics["signed_median_bias_pp"]) <= 1.5 and metrics["envelope_coverage_percent"] >= 80 and metrics["median_envelope_width_pp"] <= 10 and (not len(scored) or scored.max() <= 4)
    b = metrics["median_absolute_error_pp"] <= 5 and abs(metrics["signed_median_bias_pp"]) <= 3 and metrics["envelope_coverage_percent"] >= 60 and metrics["median_envelope_width_pp"] <= 15 and (not len(scored) or scored.max() <= 7)
    status = "PASS" if p else ("PASS WITH BOUNDS" if b else "FAIL")
    if label_ceiling and status == "PASS":
        status = label_ceiling
    metrics["status"] = status
    if label_ceiling:
        metrics["label_reproducibility_ceiling"] = label_ceiling
    rows = rows.merge(comparable[["observation_id", "signed_error_pp", "absolute_error_pp", "covered", "envelope_width_pp"]], on="observation_id", how="left")
    return rows, metrics


def validate_liu(model: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    source = pd.read_csv(ROOT / "data/raw/SRC_LIU_2025/Source Data & Code/Fig 2/Figure 2(h).csv")
    primary = model.loc[model.model_role.eq("PRIMARY_NON_AVERAGED")].copy()
    rows = []
    tertiles = source["Mileage (km)"].quantile([1 / 3, 2 / 3]).to_numpy()
    for i, item in source.iterrows():
        mileage = float(item["Mileage (km)"])
        lo, hi, ok = _nearest_envelope(primary, "cumulative_km", mileage)
        use_bin = "low" if mileage <= tertiles[0] else ("middle" if mileage <= tertiles[1] else "high")
        rows.append({"source_id": "SRC_LIU_2025", "observation_id": f"LIU_FIG2H_{i:04d}",
                     "vehicle_id": "NOT_AVAILABLE_IN_PUBLISHER_FIGURE_TABLE", "age_years": np.nan,
                     "cumulative_km": mileage, "observed_retention": float(item.SOH),
                     "envelope_lower": lo, "envelope_upper": hi, "comparable": ok,
                     "validation_stratum": f"use_{use_bin}",
                     "label_status": "PUBLISHER-PLOTTED SOH; OCV TABLE WITHHELD",
                     "claim_scope": "2610 accessible plotted observations; not asserted as 300 independent vehicles"})
    return _score_rows(pd.DataFrame(rows), "SRC_LIU_2025", "PASS WITH BOUNDS")


def extract_deng_archive(archive: Path, extract_root: Path) -> tuple[pd.DataFrame, dict]:
    subprocess.run(["tar", "-xf", str(archive), "-C", str(extract_root)], check=True,
                   capture_output=True, text=True)
    csv_path = extract_root / archive.with_suffix(".csv").name
    data = pd.read_csv(csv_path)
    data.columns = ["number", "record_time", "soc", "pack_voltage", "charge_current", "max_cell_voltage",
                    "min_cell_voltage", "max_temperature", "min_temperature", "available_energy", "available_capacity"]
    data["record_time"] = pd.to_datetime(data.record_time.astype("int64").astype(str),
                                          format="%Y%m%d%H%M%S", errors="coerce")
    data = data.sort_values("record_time", kind="mergesort").reset_index(drop=True)
    gaps = np.flatnonzero(data.record_time.diff().dt.total_seconds().to_numpy()[1:] > 10)
    bounds = [(0, int(gaps[0]))] if len(gaps) else [(0, len(data))]
    if len(gaps):
        bounds += [(int(gaps[i] + 1), int(gaps[i + 1])) for i in range(len(gaps) - 1)]
        bounds += [(int(gaps[-1] + 1), len(data))]
    records, rejected = [], {"short": 0, "soc_jump": 0, "current_missing": 0, "zero_soc": 0}
    for start, end in bounds:
        seg = data.iloc[start:end].copy().reset_index(drop=True)
        if len(seg) < 100:
            rejected["short"] += 1; continue
        ds = seg.soc.diff().iloc[1:]
        if (ds > 2).any() or (ds < -0.1).any():
            rejected["soc_jump"] += 1; continue
        current = seg.charge_current.astype(float).copy()
        if current.isna().sum() > len(current) * 0.1:
            rejected["current_missing"] += 1; continue
        current = current.ffill()
        if current.isna().any():
            rejected["current_missing"] += 1; continue
        delta_soc = float(seg.soc.iloc[-1] - seg.soc.iloc[0])
        if delta_soc == 0:
            rejected["zero_soc"] += 1; continue
        seconds = (seg.record_time - seg.record_time.iloc[0]).dt.total_seconds().to_numpy()
        capacity = float(np.trapezoid(current.to_numpy(), seconds) / 3600 * -1 / delta_soc * 100)
        records.append({"vehicle_id": archive.stem, "time_s": seg.record_time.iloc[0], "time_e": seg.record_time.iloc[-1],
                        "SOC_s": float(seg.soc.iloc[0]), "SOC_e": float(seg.soc.iloc[-1]),
                        "charge_capacity_ah": capacity, "Tmax": float(seg.max_temperature.mean()),
                        "Tmin": float(seg.min_temperature.mean())})
    csv_path.unlink(missing_ok=True)
    audit = {"archive": archive.name, "input_rows": int(len(data)), "gap_count": int(len(gaps)),
             "accepted_capacity_records": len(records), "rejected": rejected, "status": "COMPLETE"}
    return pd.DataFrame(records), audit


def reproduce_deng() -> tuple[pd.DataFrame, dict]:
    archives = sorted((ROOT / "data/raw/SRC_DENG_2023").glob("#*.rar"), key=lambda p: int(p.stem[1:]))
    all_frames, logs = [], []
    target = ROOT / "results/diagnostics/p145i_deng_extract"
    target.mkdir(parents=True, exist_ok=True)
    for archive in archives:
        frame, log = extract_deng_archive(archive, target)
        all_frames.append(frame); logs.append(log)
    result = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
    audit = {"archive_attempted": len(archives), "archive_completed": sum(x["status"] == "COMPLETE" for x in logs),
             "compatibility": "scipy.integrate.trapz -> numpy.trapezoid; unused imports bypassed",
             "segment_math_equivalence": "covered by deterministic unit test",
             "status": "COMPLETE" if len(logs) == 20 and all(x["status"] == "COMPLETE" for x in logs) else "DENG FIELD VALIDATION INCOMPLETE",
             "archives": logs}
    return result, audit


def validate_deng(events: pd.DataFrame, model: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    primary = model.loc[model.model_role.eq("PRIMARY_NON_AVERAGED")].copy()
    rows = []
    for vehicle, group in events.groupby("vehicle_id", sort=True):
        origin = group.time_e.min()
        for i, item in group.sort_values("time_e").reset_index(drop=True).iterrows():
            age = float((item.time_e - origin).total_seconds() / (365.25 * 86400))
            lo, hi, ok = _nearest_envelope(primary, "age_years", age)
            age_bin = "0_1" if age <= 1 else ("1_2" if age <= 2 else ("2_3" if age <= 3 else "gt3"))
            rows.append({"source_id": "SRC_DENG_2023", "observation_id": f"DENG_{vehicle}_{i:05d}",
                         "vehicle_id": vehicle, "age_years": age, "cumulative_km": np.nan,
                         "observed_retention": float(item.charge_capacity_ah / 145.0),
                         "envelope_lower": lo, "envelope_upper": hi, "comparable": ok,
                         "validation_stratum": f"age_{age_bin}",
                         "label_status": "SOURCE ALGORITHM CAPACITY / SOURCE NOMINAL 145 Ah",
                         "claim_scope": "charging-only field window; age measured from first available record"})
    return _score_rows(pd.DataFrame(rows), "SRC_DENG_2023")
