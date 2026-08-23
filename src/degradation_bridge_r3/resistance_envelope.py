from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
WINDOW = 0.025


def build_resistance_envelopes(capacity: pd.DataFrame) -> pd.DataFrame:
    luh = pd.read_parquet(ROOT / "data/processed/luh_degradation_state_observations.parquet")
    luh = luh.loc[luh.measurement_temperature_c.between(24.5, 25.5) & luh.soc_basis_percent.eq(50)].copy()
    sch = pd.read_parquet(ROOT / "data/processed/schreiber_automotive_validation_summary.parquet")
    sch["automotive_class"] = np.select(
        [sch.scenario.eq("highway") & sch.cu_index.eq(22), sch.scenario.eq("commuter") & sch.cu_index.ge(30)],
        ["EXTREME / CONDITIONAL", "EXTREME / CONDITIONAL"], default="AUTOMOTIVE_COMPATIBLE")
    class_filter = {"calendar_dominant": [1], "use_dominant": [2, 3], "mixed_union": [1, 2, 3]}
    rows = []
    for item in capacity.itertuples(index=False):
        for stress_class, age_types in class_filter.items():
            for endpoint, col in (("R10", "r10_rel"), ("R1s", "r1s_rel")):
                base = {"model_name": item.model_name, "profile_id": item.profile_id,
                        "age_years": item.age_years, "calendar_year": item.calendar_year,
                        "capacity_retention": item.capacity_retention, "stress_class": stress_class,
                        "resistance_endpoint": endpoint, "capacity_matching_window": WINDOW,
                        "measurement_temperature_c": 25.0, "reference_soc_percent": 50.0}
                if item.capacity_state_status != "MODELED" or not np.isfinite(item.capacity_retention):
                    rows.append({**base, "observation_count": 0, "cell_count": 0, "condition_count": 0,
                                 "central_p10": np.nan, "central_p90": np.nan,
                                 "automotive_outer_lower": np.nan, "automotive_outer_upper": np.nan,
                                 "resistance_state_status": "RESISTANCE STATE UNSUPPORTED"})
                    continue
                subset = luh.loc[luh.age_type.isin(age_types) & luh[col].notna() &
                                  luh.reconstructed_capacity_retention.between(item.capacity_retention - WINDOW, item.capacity_retention + WINDOW)]
                n, cells, conditions = len(subset), subset.cell_key.nunique(), subset.condition_id.nunique()
                supported = n >= 10 and cells >= 3 and conditions >= 2
                if supported:
                    p10, p90 = subset[col].quantile([0.1, 0.9]).to_numpy()
                    auto = sch.loc[sch.automotive_class.eq("AUTOMOTIVE_COMPATIBLE") &
                                   sch.capacity_retention.between(item.capacity_retention - WINDOW, item.capacity_retention + WINDOW), col]
                    outer_lo = float(min([p10, *auto.tolist()]))
                    outer_hi = float(max([p90, *auto.tolist()]))
                    status = "SUPPORTED CONDITIONAL ENVELOPE"
                else:
                    p10 = p90 = outer_lo = outer_hi = np.nan
                    status = "RESISTANCE STATE UNSUPPORTED"
                rows.append({**base, "observation_count": int(n), "cell_count": int(cells),
                             "condition_count": int(conditions), "central_p10": p10, "central_p90": p90,
                             "automotive_outer_lower": outer_lo, "automotive_outer_upper": outer_hi,
                             "extreme_schreiber_excluded_from_outer": True,
                             "resistance_state_status": status})
    return pd.DataFrame(rows)
