from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

def load(name):
    return pd.read_parquet(ROOT / "data" / "processed" / name)

mob = load("p14_mobility_use_scenarios.parquet")
service = load("p14_mobility_service_requirements.parquet")
surv = load("p14_vehicle_survival.parquet")
grid = load("p14_grid_pathways.parquet")
mfg = load("p14_battery_manufacturing_pathways.parquet")
chg = load("p14_charging_conversion.parquet")
energy = load("p13_incremental_energy_penalty.parquet")

print("=" * 78)
print("P15R-A3 — VALUE & BOUNDARY MAPPING AUDIT")
print("=" * 78)

print("\nMOBILITY USE")
print(
    mob[
        ["scenario_id", "quantile", "annual_km"]
    ].drop_duplicates().sort_values("annual_km").to_string(index=False)
)

print("\nMOBILITY SERVICE")
print(
    service[
        ["scenario_id", "quantile", "required_single_service_distance_km"]
    ].drop_duplicates().sort_values(
        "required_single_service_distance_km"
    ).to_string(index=False)
)

print("\nSURVIVAL SCENARIOS")
print("scenario:", sorted(surv["survival_scenario"].dropna().unique().tolist()))
print(
    "scale years:",
    sorted(
        surv["logistic_scale_years_assumption"]
        .dropna()
        .unique()
        .tolist()
    ),
)
print(
    "current vehicle ages:",
    [int(x) for x in sorted(surv["current_vehicle_age_years"].unique().tolist())]
)

print("\nGRID")
print("pathway roles:", sorted(grid["pathway_role"].dropna().unique().tolist()))
print("scenarios:", sorted(grid["scenario"].dropna().unique().tolist()))
print("geography levels:", sorted(grid["geography_level"].dropna().unique().tolist()))
print("years:", [int(x) for x in sorted(grid["calendar_year"].unique().tolist())])
print(
    "grid CI range:",
    float(grid["grid_ci_gco2e_per_kwh"].min()),
    "to",
    float(grid["grid_ci_gco2e_per_kwh"].max()),
    "gCO2e/kWh",
)

print("\nBATTERY MANUFACTURING")
print("chemistries:", sorted(mfg["chemistry"].dropna().unique().tolist()))
print("pathways:", sorted(mfg["pathway"].dropna().unique().tolist()))
print("benchmark types:", sorted(mfg["benchmark_type"].dropna().unique().tolist()))
print("years:", [int(x) for x in sorted(mfg["calendar_year"].unique().tolist())])
print(
    "pack GHG range:",
    float(mfg["pack_ghg_kgco2e_per_kwh"].min()),
    "to",
    float(mfg["pack_ghg_kgco2e_per_kwh"].max()),
    "kgCO2e/kWh_pack",
)

print("\nCHARGING")
print(
    chg[
        [
            "scenario_id",
            "quantile",
            "charging_efficiency_fraction",
            "l2_to_l3_multiplier",
        ]
    ].drop_duplicates().to_string(index=False)
)

print("\nP13 ENERGY")
print("resistance specifications:",
      sorted(energy["resistance_specification"].dropna().unique().tolist()))
print("physical envelope classes:",
      sorted(energy["physical_envelope_class"].dropna().unique().tolist()))
print("domain statuses:",
      sorted(energy["valid_domain_status"].dropna().unique().tolist()))
print("drive cycles:",
      sorted(energy["drive_cycle"].dropna().unique().tolist()))
print("cell resistance shares:",
      sorted(energy["cell_resistance_share"].dropna().unique().tolist()))
print(
    "fresh L2 range:",
    float(energy["fresh_battery_side_kwh_per_km"].min()),
    "to",
    float(energy["fresh_battery_side_kwh_per_km"].max()),
)
print(
    "aged L2 range:",
    float(energy["aged_battery_side_kwh_per_km"].min()),
    "to",
    float(energy["aged_battery_side_kwh_per_km"].max()),
)

assert (chg["charging_efficiency_fraction"] > 0).all()
assert (chg["charging_efficiency_fraction"] <= 1).all()
assert (grid["grid_ci_gco2e_per_kwh"] >= 0).all()
assert (mfg["pack_ghg_kgco2e_per_kwh"] >= 0).all()
assert (mob["annual_km"] > 0).all()
assert (energy["fresh_battery_side_kwh_per_km"] > 0).all()

print("\n" + "=" * 78)
print("P15R-A3 PASS — VALUES AND ACCOUNTING BOUNDARIES AUDITED")
print("NO LIFECYCLE GHG CALCULATED")
print("NO DELTAG CALCULATED")
print("NO CARBON CLASSIFICATION PRODUCED")
print("=" * 78)