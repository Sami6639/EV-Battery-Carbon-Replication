"""Sensitivity of the matched storage contrasts to installed-pack resistance."""
from pathlib import Path
import pandas as pd

out = Path(__file__).resolve().parent
inputs = out.parent / 'inputs'
cases = pd.read_csv(out / 'storage_thresholds.csv')
survival = pd.read_parquet(inputs / 'p14_vehicle_survival.parquet').query(
    "survival_scenario == 'central' and current_vehicle_age_years == 8"
).set_index('years_after_conditioning').conditional_survival
grid = pd.read_parquet(inputs / 'p14_grid_pathways.parquet').query(
    "geography_level == 'US_LOAD_WEIGHTED' and pathway_role == 'PRIMARY_AVERAGE_CI'"
).pivot(index='calendar_year', columns='scenario', values='grid_ci_gco2e_per_kwh') / 1000
eta = pd.read_parquet(inputs / 'p14_charging_conversion.parquet').query(
    "scenario_id == 'central_efficiency'").charging_efficiency_fraction.item()
loss = pd.read_csv(out / 'fastsim.csv').iloc[-1].fresh_storage_loss_kwh_per_km
def extra_per_unit(case):
    return 10729.496448 * loss / eta * sum(
        survival[t] * grid.loc[case.year + t, case.grid] for t in range(case.delay))
factor = cases.apply(extra_per_unit, axis=1)
results = []
for resistance in [1.1238, 1.5, 2.0]:
    change = (resistance - 1.5) * factor
    # Only old-pack operation during deferral changes. Storage credits share the same inputs.
    results.append(cases.drop(columns=['first_root','roots']).assign(
        resistance=resistance, delta_at_099=cases.delta_at_099-change,
        delta_at_100=cases.delta_at_100-change, minimum=cases.minimum-change))
pd.concat(results, ignore_index=True).to_csv(out/'storage_resistance.csv',index=False)
