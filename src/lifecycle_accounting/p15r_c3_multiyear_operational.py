from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

C1 = ROOT / "results/intermediate/p15r_c1_accounting_components_2025.parquet"
C2 = ROOT / "results/intermediate/p15r_c2_residual_service_weights.parquet"
GRID = ROOT / "data/processed/p14_grid_pathways.parquet"

ANNUAL_OUT = ROOT / "results/intermediate/p15r_c3_annual_operational_components.parquet"
SUMMARY_OUT = ROOT / "results/intermediate/p15r_c3_residual_operational_components.parquet"

print("=" * 78)
print("P15R-C3 — MULTI-YEAR OPERATIONAL GHG COMPONENT ACCOUNTING")
print("=" * 78)

# ------------------------------------------------------------
# 1. LOAD
# ------------------------------------------------------------

base = pd.read_parquet(C1)
service = pd.read_parquet(C2)
grid = pd.read_parquet(GRID)

# ------------------------------------------------------------
# 2. PRIMARY RESIDUAL-SERVICE CONTEXT
# ------------------------------------------------------------

service = service.loc[
    (service["survival_scenario"] == "central")
    & (service["current_vehicle_age_years"] == 0)
].copy()

assert len(service) == 26

service["decision_calendar_year"] = 2025
service["operation_year"] = (
    service["decision_calendar_year"]
    + service["years_after_conditioning"]
)

assert service["operation_year"].min() == 2025
assert service["operation_year"].max() == 2050

# ------------------------------------------------------------
# 3. PRIMARY GRID SERIES
# ------------------------------------------------------------

g = grid.loc[
    (grid["pathway_role"] == "PRIMARY_AVERAGE_CI")
    & (grid["geography_level"] == "US_LOAD_WEIGHTED")
    & (grid["region"] == "US_LOAD_WEIGHTED")
    & (grid["scenario"].isin(["MidCase", "LowRECost", "HighRECost"]))
    & (grid["calendar_year"].between(2025, 2050))
].copy()

g = g[
    [
        "scenario",
        "calendar_year",
        "grid_ci_gco2e_per_kwh",
    ]
].rename(
    columns={
        "scenario": "grid_scenario",
        "calendar_year": "operation_year",
    }
)

assert len(g) == 3 * 26

# ------------------------------------------------------------
# 4. REMOVE C1 SINGLE-YEAR OPERATIONAL VALUES
#    WE KEEP ONLY L2/L3 PER-KM IDENTITIES AND CONTEXT
# ------------------------------------------------------------

drop_cols = [
    "continue_annual_grid_kwh",
    "replace_annual_grid_kwh",
    "continue_operational_kgco2e",
    "replace_operational_kgco2e",
    "grid_ci_gco2e_per_kwh",
]

base = base.drop(
    columns=[c for c in drop_cols if c in base.columns]
)

# ------------------------------------------------------------
# 5. EXPAND EACH STATE/CONTEXT ACROSS RESIDUAL YEARS
# ------------------------------------------------------------

annual = base.merge(
    service[
        [
            "operation_year",
            "years_after_conditioning",
            "conditional_survival",
            "expected_service_km",
        ]
    ],
    how="cross",
)

annual = annual.merge(
    g,
    on=["grid_scenario", "operation_year"],
    how="left",
    validate="many_to_one",
)

if annual["grid_ci_gco2e_per_kwh"].isna().any():
    raise RuntimeError(
        "P15R-C3 FAIL — missing grid CI after annual merge."
    )

# ------------------------------------------------------------
# 6. POLICY-SPECIFIC GRID ELECTRICITY
# ------------------------------------------------------------

annual["continue_grid_kwh"] = (
    annual["continue_l3_kwh_per_km"]
    * annual["expected_service_km"]
)

annual["replace_grid_kwh"] = (
    annual["replace_l3_kwh_per_km"]
    * annual["expected_service_km"]
)

# ------------------------------------------------------------
# 7. POLICY-SPECIFIC OPERATIONAL GHG
#
# g CO2e/kWh × kWh / 1000 = kg CO2e
# ------------------------------------------------------------

annual["continue_operational_kgco2e"] = (
    annual["continue_grid_kwh"]
    * annual["grid_ci_gco2e_per_kwh"]
    / 1000.0
)

annual["replace_operational_kgco2e"] = (
    annual["replace_grid_kwh"]
    * annual["grid_ci_gco2e_per_kwh"]
    / 1000.0
)

# ------------------------------------------------------------
# 8. SAFETY FLAGS
# ------------------------------------------------------------

annual["accounting_stage"] = "P15R-C3"
annual["lifecycle_total_calculated"] = False
annual["delta_g_calculated"] = False
annual["decision_bounds_calculated"] = False
annual["carbon_classification_produced"] = False
annual["replacement_optimization_performed"] = False

assert (annual["continue_operational_kgco2e"] >= 0).all()
assert (annual["replace_operational_kgco2e"] >= 0).all()

# ------------------------------------------------------------
# 9. RESIDUAL-HORIZON COMPONENT SUMMARY
# ------------------------------------------------------------

group_cols = [
    "degradation_state_id",
    "source_id",
    "physical_envelope_class",
    "valid_domain_status",
    "topology_id",
    "nominal_pack_voltage_v",
    "cell_resistance_share",
    "fresh_usable_window_fraction",
    "capacity_retention",
    "relative_resistance",
    "grid_scenario",
    "manufacturing_pathway",
    "replacement_chemistry",
    "replacement_pack_kwh",
    "pack_ghg_kgco2e_per_kwh",
    "replacement_manufacturing_kgco2e",
]

summary = (
    annual.groupby(group_cols, as_index=False)
    .agg(
        expected_residual_service_km=(
            "expected_service_km",
            "sum",
        ),
        continue_residual_grid_kwh=(
            "continue_grid_kwh",
            "sum",
        ),
        replace_residual_grid_kwh=(
            "replace_grid_kwh",
            "sum",
        ),
        continue_residual_operational_kgco2e=(
            "continue_operational_kgco2e",
            "sum",
        ),
        replace_residual_operational_kgco2e=(
            "replace_operational_kgco2e",
            "sum",
        ),
    )
)

summary["accounting_stage"] = "P15R-C3"
summary["lifecycle_total_calculated"] = False
summary["delta_g_calculated"] = False
summary["decision_bounds_calculated"] = False
summary["carbon_classification_produced"] = False
summary["replacement_optimization_performed"] = False

# ------------------------------------------------------------
# 10. WRITE
# ------------------------------------------------------------

annual.to_parquet(ANNUAL_OUT, index=False)
summary.to_parquet(SUMMARY_OUT, index=False)

# ------------------------------------------------------------
# 11. REPORT
# ------------------------------------------------------------

print(f"\nAnnual rows: {len(annual):,}")
print(f"Residual summary rows: {len(summary):,}")

print(
    "Expected residual service:",
    float(summary["expected_residual_service_km"].min()),
    "to",
    float(summary["expected_residual_service_km"].max()),
    "km",
)

print("\nContinue residual operational GHG:")
print(
    float(summary["continue_residual_operational_kgco2e"].min()),
    "to",
    float(summary["continue_residual_operational_kgco2e"].max()),
    "kg CO2e",
)

print("\nReplace residual operational GHG:")
print(
    float(summary["replace_residual_operational_kgco2e"].min()),
    "to",
    float(summary["replace_residual_operational_kgco2e"].max()),
    "kg CO2e",
)

print("\nOutputs:")
print(ANNUAL_OUT.relative_to(ROOT))
print(SUMMARY_OUT.relative_to(ROOT))

print("\n" + "=" * 78)
print("P15R-C3 PASS — MULTI-YEAR OPERATIONAL COMPONENTS VERIFIED")
print("SURVIVAL AND GRID CALENDAR ALIGNMENT VERIFIED")
print("NO LIFECYCLE TOTAL CALCULATED")
print("NO DELTAG CALCULATED")
print("NO IDENTIFIED DECISION BOUNDS CALCULATED")
print("NO CARBON CLASSIFICATION PRODUCED")
print("NO REPLACEMENT OPTIMIZATION PERFORMED")
print("=" * 78)