from pathlib import Path
import json,pandas as pd,yaml
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/"data/processed"
def read(n): return pd.read_parquet(OUT/n)
def test_required_outputs_and_schemas():
 req={"luh_capacity_observations.parquet":{"source_id","source_filename","source_row","measured_capacity_ah","capacity_soh_fraction"},"luh_pulse_resistance_observations.parquet":{"r_ref_10ms_mOhm","resistance_10ms_ohm","r_ref_1s_mOhm","resistance_1s_ohm"},"schreiber_checkup_observations.parquet":{"scenario","checkup_id","cu_index","time_s","voltage_v","current_a"},"tum_id3_wltp_vehicle_observations.parquet":{"vehicle_time_ms","vehicle_speed_kmh","hv_battery_voltage_v","hv_battery_current_a"},"nhts_vehicle_use_observations.parquet":{"annual_miles","annual_km"},"cambium_lrmer_2023_components.parquet":{"dataset_version","scenario","region","calendar_year","metric_identity","unit"},"llamas_pack_manufacturing_ghg.parquet":{"chemistry","pack_ghg_kgco2e_per_kwh","system_boundary"},"sevdari_charging_efficiency_observations.parquet":{"vehicle_test_id","current_a","charging_efficiency_fraction"}}
 for n,c in req.items(): assert c<=set(read(n).columns)
def test_identity_and_units():
 p=read("luh_pulse_resistance_observations.parquet");assert (p.resistance_10ms_ohm==p.r_ref_10ms_mOhm*.001).all();assert (p.resistance_1s_ohm==p.r_ref_1s_mOhm*.001).all()
 v=read("nhts_vehicle_use_observations.parquet");assert ((v.annual_km-v.annual_miles*1.609344).abs()<1e-9).all()
 s=read("schreiber_checkup_observations.parquet");assert set(s.scenario)=={"commuter","highway"};assert s.checkup_id.notna().all()
def test_boundary_missingness_and_no_filtering():
 m=read("llamas_pack_manufacturing_ghg.parquet");assert (m.system_boundary=="battery_production_pack_level").all();assert not m.chemistry.str.fullmatch("NMC").any()
 for p in OUT.glob("*.parquet"):
  d=read(p.name);meta=yaml.safe_load((OUT/"metadata"/(p.stem+".yaml")).read_text());assert meta["row_count"]==len(d)
 # P11/P11R preprocessing is mechanically lossless.  Later scientific-layer
 # metadata may legitimately disclose source-defined eligibility filters.
 for p in (OUT/"metadata").glob("*.yaml"):
  meta=yaml.safe_load(p.read_text())
  if meta.get("processing_script")=="src/preprocessing/p11_pipeline.py":assert meta["scientific_filtering_performed"]=="NONE"
def test_p11r_outputs_are_recovered():
 assert (OUT/"tum_id3_hppc_observations.parquet").exists();assert (OUT/"cambium_2024_average_grid_ci.parquet").exists()
