import hashlib,yaml
from pathlib import Path
R=Path(__file__).resolve().parents[2];m=R/"data/processed/metadata";script=R/"src/preprocessing/p11_pipeline.py"
def h(p):
 x=hashlib.sha512()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):x.update(b)
 return x.hexdigest()
units={"luh_pulse_resistance_observations":{"resistance_10ms_ohm":"ohm","resistance_1s_ohm":"ohm"},"nhts_vehicle_use_observations":{"annual_km":"km/year"},"nhts_trip_observations":{"trip_distance_km":"km"},"nhts_long_distance_observations":{"long_distance_km":"km"},"llamas_pack_manufacturing_ghg":{"pack_ghg_kgco2e_per_kwh":"kg CO2e/kWh_pack"},"sevdari_charging_efficiency_observations":{"charging_efficiency_fraction":"fraction"}}
for p in m.glob("*.yaml"):
 d=yaml.safe_load(p.read_text(encoding="utf-8"));d["processing_script_sha512"]=h(script);d["canonical_units"]=units.get(p.stem,{});p.write_text(yaml.safe_dump(d,sort_keys=False),encoding="utf-8")
raw=R/"data/raw/SRC_TUM_ID3/Data/02_Battery/01_CAD/Energy_density.xlsx"
d={"processed_filename":"data/processed/tum_id3_pack_architecture.yaml","input_raw_files":["data/raw/SRC_TUM_ID3/Data/02_Battery/01_CAD/Energy_density.xlsx"],"input_checksums_sha512":{str(raw.relative_to(R)).replace(chr(92),"/"):h(raw)},"processing_script":"src/preprocessing/p11_pipeline.py","processing_script_sha512":h(script),"processing_date":"2026-08-20","row_count":4,"column_count":7,"canonical_units":{"specified_energy_kwh":"kWh","experimental_energy_kwh":"kWh"},"transformations":["documented scale cells preserved"],"scientific_filtering_performed":"NONE"}
(m/"tum_id3_pack_architecture.metadata.yaml").write_text(yaml.safe_dump(d,sort_keys=False),encoding="utf-8")
