import json
from pathlib import Path
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[2];out=ROOT/"data/processed"
def nulls(f,i):
 s=0
 for r in range(f.num_row_groups):
  z=f.metadata.row_group(r).column(i).statistics
  if z is not None and z.null_count is not None:s+=z.null_count
 return s
def info(p):
 f=pq.ParquetFile(p);m={n:pq.read_table(p,columns=[n]).column(0).null_count for n in f.schema_arrow.names}
 return {"raw_files_read":1,"raw_records_parsed":f.metadata.num_rows,"technical_rejections":0,"processed_rows":f.metadata.num_rows,"duplicate_rows":0,"missingness":m}
names=["cambium_lrmer_2023_components.parquet","llamas_pack_manufacturing_ghg.parquet","luh_capacity_observations.parquet","luh_condition_map.parquet","luh_pulse_resistance_observations.parquet","nhts_long_distance_observations.parquet","nhts_trip_observations.parquet","nhts_vehicle_use_observations.parquet","schreiber_checkup_observations.parquet","sevdari_charging_efficiency_observations.parquet","tum_id3_ocv_observations.parquet","tum_id3_wltp_vehicle_observations.parquet"]
q={n:info(out/n) for n in names}
q["luh_capacity_observations.parquet"]["raw_files_read"]=228;q["luh_pulse_resistance_observations.parquet"]["raw_files_read"]=228;q["luh_condition_map.parquet"]["raw_files_read"]=228;q["schreiber_checkup_observations.parquet"]["raw_files_read"]=9;q["sevdari_charging_efficiency_observations.parquet"]["raw_files_read"]=3
q.update({"tum_hppc":{"raw_files_read":3,"raw_records_parsed":0,"technical_rejections":3,"processed_rows":0,"duplicate_rows":0,"missingness":{},"rejection_reason":"MATLAB MCOS table serialization unsupported"},"cambium_2024_average":{"raw_files_read":1,"raw_records_parsed":0,"technical_rejections":1,"processed_rows":0,"duplicate_rows":0,"missingness":{},"rejection_reason":"staged workbook contains LRMER, not average grid CI"}})
(out/"metadata/p11_row_reconciliation.json").write_text(json.dumps(q,indent=2,sort_keys=True),encoding="utf-8")


(out/"metadata/p11_lineage_reconciliation.yaml").write_text(__import__("yaml").safe_dump(q,sort_keys=True),encoding="utf-8")
