# P11 Canonical Data Dictionary

This dictionary is frozen for P11 extraction. Every output also carries `source_id` and `source_filename`; nulls reproduce source missingness. `LOSSLESS_DERIVED` means a deterministic identity, label parse, or unit conversion. No `SCIENTIFIC_DERIVED` field is permitted in P11.

## Common provenance fields

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| source_id | Frozen source identity | manifest `source_id` | — | — | string | required | exact constant | LOSSLESS_DERIVED | provenance |
| source_filename | Raw member/path | archive member or file path | — | — | string | required | workspace-relative path | LOSSLESS_DERIVED | provenance |
| source_row | One-based source data-row locator | physical row | row | row | int64 | required | preserve/assign monotonically | LOSSLESS_DERIVED | audit |
| parse_issue_flag | Technical parse anomaly | parser result | — | — | boolean | required | true only for malformed/non-finite type anomalies; never filters | LOSSLESS_DERIVED | QA |

## Luh ageing observations

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| cell_id | Test-cell identifier | `cfg.zip` / `cell_id` | — | — | string | required when supplied | string preservation | OBSERVED | identity |
| replicate_id | Physical replicate identifier | `cfg.zip` / `slave_id` + `cell_id` | — | — | string | nullable | exact composite, no grouping | LOSSLESS_DERIVED | identity |
| condition_id | Ageing condition | all three archives / `parameter_id`, `age_*` | — | — | string | nullable | source label or exact tuple | LOSSLESS_DERIVED | stratification |
| ageing_type | Calendar/cycle ageing | `age_type` | — | — | string | nullable | preserve source code | OBSERVED | exposure context |
| ageing_profile | Cycling profile | `age_profile` | — | — | string | nullable | preserve | OBSERVED | exposure context |
| timestamp_s | Test timestamp | `timestamp_s` | s | s | float64 | nullable | numeric parse only | OBSERVED | sequence |
| cycle_count | Operational/check-up count | `num_cycles_op`, `num_cycles_checkup` | cycles | cycles | float64 | nullable | preserve separate columns | OBSERVED | exposure |
| charge_throughput_ah | Cumulative charge throughput | `total_q_chg_sum_Ah` | Ah | Ah | float64 | nullable | preserve; no Ah→kWh | OBSERVED | exposure |
| discharge_throughput_ah | Cumulative discharge throughput | `total_q_dischg_sum_Ah` | Ah | Ah | float64 | nullable | preserve | OBSERVED | exposure |
| measured_capacity_ah | Estimated aged capacity | `cap_aged_est_Ah` | Ah | Ah | float64 | nullable | preserve | OBSERVED | capacity state |
| capacity_soh_fraction | Source-supplied capacity SOH | `soh_cap` | fraction | fraction | float64 | nullable | preserve, no clipping | OBSERVED | capacity state |
| measured_energy_wh | Check-up energy | `delta_e_Wh` | Wh | Wh | float64 | nullable | preserve | OBSERVED | capacity/energy state |
| soc_fraction | SOC at pulse/check-up | `soc_nom`, `soc_est_start/end` | fraction | fraction | float64 | nullable | preserve | OBSERVED | state |
| temperature_c | Test/cell temperature | `t_avg_degC`, `t_start/end_degC`, `age_temp` | °C | °C | float64 | nullable | preserve | OBSERVED | state |
| resistance_10ms_ohm | 10-ms reference resistance | `r_ref_10ms_mOhm` | mΩ | Ω | float64 | nullable | multiply by 0.001 | LOSSLESS_DERIVED | loss state |
| resistance_1s_ohm | 1-s reference resistance | `r_ref_1s_mOhm` | mΩ | Ω | float64 | nullable | multiply by 0.001 | LOSSLESS_DERIVED | loss state |
| baseline_candidate | Record is mechanically eligible for later baseline review | earliest/source context | — | — | boolean | required | descriptive flag only; no R/R0 calculation | LOSSLESS_DERIVED | later validation |

## Schreiber validation records

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| scenario | Validation duty cycle | filename `commuter`/`highway` | — | — | string | required | filename parse | LOSSLESS_DERIVED | validation stratum |
| checkup_id | Check-up identity | filename / `CU_*` | — | — | string | required | preserve | LOSSLESS_DERIVED | identity |
| cu_index | Check-up index | filename / `CU_*` | — | — | int64 | required | integer parse | LOSSLESS_DERIVED | sequence |
| time_s | Elapsed time | `Time[s]` | s | s | float64 | nullable | preserve | OBSERVED | sequence |
| dataset_id | Instrument dataset marker | `DataSet` | — | — | string | nullable | preserve | OBSERVED | protocol |
| step_time_s | Step elapsed time | `t-Step[s]` | s | s | float64 | nullable | preserve | OBSERVED | protocol |
| protocol_line | Test-plan line | `Line` | — | — | string | nullable | preserve | OBSERVED | protocol |
| command | Test command | `Command` | — | — | string | nullable | preserve | OBSERVED | protocol |
| voltage_v | Cell voltage | `U[V]` | V | V | float64 | nullable | preserve | OBSERVED | measurement |
| current_a | Cell current | `I[A]` | A | A | float64 | nullable | preserve | OBSERVED | measurement |
| charge_ah | Accumulated charge | `Ah[Ah]` | Ah | Ah | float64 | nullable | preserve | OBSERVED | measurement |
| energy_wh | Accumulated energy | `Wh[Wh]` | Wh | Wh | float64 | nullable | preserve | OBSERVED | measurement |
| temperature_1_c | Temperature channel 1 | `T1[°C]` | °C | °C | float64 | nullable | encoding-normalized header only | OBSERVED | measurement |
| temperature_2_c | Temperature channel 2 | `T2[°C]` | °C | °C | float64 | nullable | encoding-normalized header only | OBSERVED | measurement |
| cycle_count | Cycle counter | `Cyc-Count` | cycles | cycles | float64 | nullable | preserve | OBSERVED | exposure |
| state_marker | Instrument state | `State` | — | — | string | nullable | preserve | OBSERVED | protocol |

## TUM ID.3 validation records

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| test_temperature_c | OCV/HPPC test temperature | filename `*deg` | °C | °C | float64 | nullable | filename parse | LOSSLESS_DERIVED | validation context |
| time_s | Cell-test elapsed time | OCV `Dataset.Time` | s | s | float64 | nullable | preserve | OBSERVED | sequence |
| voltage_v | Cell-test voltage | OCV `Dataset.U` | V | V | float64 | nullable | preserve | OBSERVED | measurement |
| current_a | Cell-test current | OCV `Dataset.I` | A | A | float64 | nullable | preserve | OBSERVED | measurement |
| charge_ah | Cell-test charge | OCV `Dataset.Ah` | Ah | Ah | float64 | nullable | preserve | OBSERVED | measurement |
| energy_wh | Cell-test energy | OCV `Dataset.Wh` | Wh | Wh | float64 | nullable | preserve | OBSERVED | measurement |
| vehicle_time_ms | Vehicle log timestamp | WLTP `time` | ms since epoch | ms since epoch | int64 | required | preserve | OBSERVED | sequence |
| vehicle_speed_kmh | Vehicle speed | WLTP `vehicle_speed` | km/h | km/h | float64 | nullable | preserve | OBSERVED | vehicle validation |
| hv_battery_voltage_v | HV battery voltage | WLTP `hv_battery_voltage_x` | V | V | float64 | nullable | preserve | OBSERVED | vehicle validation |
| hv_battery_current_a | HV battery current | WLTP `hv_battery_current` | A | A | float64 | nullable | preserve | OBSERVED | vehicle validation |
| hv_soc_percent | HV SOC | WLTP `hv_soc` | % | % | float64 | nullable | preserve; no inferred fraction | OBSERVED | vehicle validation |
| topology_parallel | Parallel cells | Energy_density / row 10 | count | count | int64 | nullable | preserve by scale | OBSERVED | architecture |
| topology_series | Series cells | Energy_density / row 11 | count | count | int64 | nullable | preserve by scale | OBSERVED | architecture |
| energy_kwh | Documented energy by scale/basis | Energy_density / rows 13–16, 67 | kWh | kWh | float64 | nullable | preserve with basis label | OBSERVED | architecture |
| dataset_id | Instrument dataset marker | HPPC CSV `DataSet` | — | — | float64 | nullable | numeric preservation | OBSERVED | protocol |
| protocol_line | Test-plan/SOC-step line identifier | HPPC CSV `Line` | — | — | float64 | nullable | numeric preservation; no SOC inference | OBSERVED | protocol |
| step_time_s | Step elapsed time | HPPC CSV `tSteph` | h | s | float64 | nullable | multiply by 3600 | LOSSLESS_DERIVED | protocol |
| set_time_s | Set elapsed time | HPPC CSV `tSeth` | h | s | float64 | nullable | multiply by 3600 | LOSSLESS_DERIVED | protocol |
| datetime_raw | Author timestamp text | HPPC CSV `DateTime` | — | — | string | nullable | preserve text | OBSERVED | sequence |
| charge_step_ah | Step charge accumulator | HPPC CSV `AhStep` | Ah | Ah | float64 | nullable | preserve | OBSERVED | measurement |
| charge_set_ah | Set charge accumulator | HPPC CSV `AhSet` | Ah | Ah | float64 | nullable | preserve | OBSERVED | measurement |
| rac_source_value | Author RAC channel | HPPC CSV `RAC` | source-defined | source-defined | float64 | nullable | preserve without resistance interpretation | OBSERVED | validation evidence |
| rdc_source_value | Author RDC channel | HPPC CSV `RDC` | source-defined | source-defined | float64 | nullable | preserve without resistance interpretation | OBSERVED | validation evidence |

## NHTS mobility records

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| household_id | Household identifier | `HOUSEID` | — | — | string | required | preserve | OBSERVED | identity |
| person_id | Person identifier | `PERSONID` | — | — | string | nullable by table | preserve | OBSERVED | identity |
| vehicle_id | Household vehicle identifier | `VEHID` | — | — | string | nullable by table | preserve | OBSERVED | identity |
| annual_miles | Reported annual vehicle mileage | vehicle / `ANNMILES` | mi/year | mi/year | float64 | nullable; source codes retained separately | preserve | OBSERVED | annual use |
| annual_km | Reported annual mileage in km | `ANNMILES` | mi/year | km/year | float64 | nullable | multiply valid numeric value by 1.609344; no threshold filtering | LOSSLESS_DERIVED | annual use |
| trip_miles | Reported trip distance | trip / `TRPMILES` | mi | mi | float64 | nullable | preserve | OBSERVED | mobility service |
| trip_distance_km | Trip distance | `TRPMILES` | mi | km | float64 | nullable | multiply by 1.609344 | LOSSLESS_DERIVED | mobility service |
| long_distance_miles | Great-circle long trip distance | long-distance / `GCDTOT` | mi | mi | float64 | nullable | preserve | OBSERVED | range evidence |
| long_distance_km | Great-circle long trip distance | `GCDTOT` | mi | km | float64 | nullable | multiply by 1.609344 | LOSSLESS_DERIVED | range evidence |
| survey_weight | Published survey weight | `WTHHFIN`, `WTTRDFIN`, `WTPERFIN` | weight | weight | float64 | nullable | preserve; no aggregation | OBSERVED | later inference |

## Electricity records

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| dataset_version | Cambium vintage | workbook identity | year | year | int64 | required | constant 2023/2024 | LOSSLESS_DERIVED | provenance |
| scenario | Cambium scenario | grouped sheet header | — | — | string | required | preserve | OBSERVED | scenario |
| region | GEA region | `Region` | — | — | string | required | preserve | OBSERVED | geography |
| calendar_year | Projection year | grouped column header | year | year | int64 | required | header parse | LOSSLESS_DERIVED | time |
| metric_identity | Emission metric/stage | grouped header | — | — | string | required | explicit label | LOSSLESS_DERIVED | boundary |
| grid_ci_gco2e_per_kwh | Average grid CI | Cambium 2024 Scenario Viewer `aer_load_co2e` | kg CO2e/MWh_end-use | g CO2e/kWh_end-use | float64 | required for selected scenarios/regions/years | numerical identity: 1 kg/MWh = 1 g/kWh | LOSSLESS_DERIVED | primary electricity input |
| lrmer_gco2e_per_kwh | Long-run marginal CO2e rate | Cambium `Data - Annual` combined CO2e scenario/year columns | kg/MWh | g CO2e/kWh | float64 | nullable | 1 kg/MWh = 1 g/kWh | LOSSLESS_DERIVED | sensitivity only |

## Manufacturing records

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| chemistry | Source-defined chemistry | Llamas-Orozco S18 block label | — | — | string | required | preserve exact chemistry (including NMC811) | OBSERVED | manufacturing stratum |
| manufacturing_geography | Manufacturing geography | source scenario when explicit | — | — | string | nullable | preserve; never infer | OBSERVED | manufacturing stratum |
| pathway | Current/SPS/SDS | S18 column header | — | — | string | required | parse exact header | LOSSLESS_DERIVED | scenario |
| calendar_year | Scenario year | S18 column header | year | year | int64 | required | parse | LOSSLESS_DERIVED | time |
| pack_ghg_kgco2e_per_kwh | Total pack-production GHG | S18 `Total per kWh battery` / `Emissions` | kg CO2e/kWh | kg CO2e/kWh_pack | float64 | required | preserve; source explicitly states battery-production per kWh | OBSERVED | pack manufacturing |
| system_boundary | Source boundary | S18 title/total label | — | — | string | required | `battery_production_pack_level` | LOSSLESS_DERIVED | boundary |

## Sevdari charging validation records

| canonical_name | scientific meaning | source / original field | original unit | canonical unit | dtype | allowed/null behavior | transformation rule | status | scientific role |
|---|---|---|---|---|---|---|---|---|---|
| vehicle_test_id | Vehicle/model test identity | workbook `Brand` | — | — | string | required | preserve | OBSERVED | identity |
| current_a | Three-phase charging-current setpoint | workbook column header | A | A | float64 | required | header parse | LOSSLESS_DERIVED | test condition |
| charging_efficiency_fraction | Measured charging efficiency | `Efficiency_3phase_data.xlsx` cell | % | fraction | float64 | nullable | divide by 100; no averaging | LOSSLESS_DERIVED | validation measurement |
| power_factor | Measured power factor | `Powerfactor_3phase_data.xlsx` cell | fraction | fraction | float64 | nullable | preserve | OBSERVED | electrical context |
| reactive_power_var | Measured reactive power | `Reactive_power_3phase_data.xlsx` cell | var | var | float64 | nullable | preserve | OBSERVED | electrical context |

## Explicitly deferred fields

- Final `R/R0`: `BASELINE_DEFINITION_VALIDATION_REQUIRED`; absolute 10-ms and 1-s values are retained.
- National Cambium series: `NATIONAL_AGGREGATION_VALIDATION_REQUIRED`; no weighting rule is chosen.
- NHTS mobility quantiles/thresholds: later methodological validation; no threshold is applied.
- HPPC scientific resistance/SOC derivations remain deferred; official CSV channels are canonicalized without fitting or SOC inference.
