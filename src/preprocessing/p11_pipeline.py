import io,json,re,zipfile,hashlib
from pathlib import Path
import numpy as np,pandas as pd,scipy.io as sio,yaml
from openpyxl import load_workbook
R=Path(__file__).resolve().parents[2]; W=R/"data/raw"; O=R/"data/processed"; M=O/"metadata"; Q={}
def sha(p):
 h=hashlib.sha512()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def save(n,d,inputs,steps):
 d.to_parquet(O/n,index=False,compression="zstd")
 m={"processed_filename":"data/processed/"+n,"input_raw_files":[str(p.relative_to(R)).replace(chr(92),"/") for p in inputs],"input_checksums_sha512":{str(p.relative_to(R)).replace(chr(92),"/"):sha(p) for p in inputs},"processing_script":"src/preprocessing/p11_pipeline.py","processing_script_sha512":sha(Path(__file__)),"canonical_units":{k:v for k,v in {"resistance_10ms_ohm":"ohm","resistance_1s_ohm":"ohm","annual_km":"km/year","trip_distance_km":"km","long_distance_km":"km","pack_ghg_kgco2e_per_kwh":"kg CO2e/kWh_pack","charging_efficiency_fraction":"fraction","grid_ci_gco2e_per_kwh":"g CO2e/kWh_end-use"}.items() if k in d.columns},"processing_date":"2026-08-20","row_count":len(d),"column_count":len(d.columns),"transformations":steps,"scientific_filtering_performed":"NONE"}
 (M/(Path(n).stem+".yaml")).write_text(yaml.safe_dump(m,sort_keys=False),encoding="utf-8")
 Q[n]={"raw_files_read":len(inputs),"raw_records_parsed":len(d),"technical_rejections":0,"processed_rows":len(d),"duplicate_rows":int(d.duplicated().sum()),"missingness":d.isna().sum().astype(int).to_dict()}
def save_hppc(files):
 import pyarrow as pa,pyarrow.parquet as pq
 out=O/"tum_id3_hppc_observations.parquet";writer=None;total=0;missing={}
 numeric={"Timeh":"time_s","DataSet":"dataset_id","tSteph":"step_time_s","tSeth":"set_time_s","Line":"protocol_line","UV":"voltage_v","IA":"current_a","AhAh":"charge_ah","AhStep":"charge_step_ah","AhSet":"charge_set_ah","WhWh":"energy_wh","T1C":"temperature_1_c","T2C":"temperature_2_c","RAC":"rac_source_value","RDC":"rdc_source_value","CycCount":"cycle_count"}
 for p,temp in files:
  offset=0
  for d in pd.read_csv(p,usecols=list(numeric)+["DateTime","Command","State"],dtype={"DateTime":"string","Command":"string","State":"string"},chunksize=250000,low_memory=False):
   d=d.reset_index(drop=True);n=len(d);x=pd.DataFrame({"source_id":"SRC_TUM_ID3","source_filename":str(p.relative_to(W)).replace(chr(92),"/"),"source_row":np.arange(offset+2,offset+n+2,dtype=np.int64),"test_temperature_c":float(temp)})
   for src,dst in numeric.items():x[dst]=pd.to_numeric(d[src],errors="coerce").astype("float64")
   for c in ("time_s","step_time_s","set_time_s"):x[c]=x[c]*3600.0
   x["datetime_raw"]=d["DateTime"].astype("string");x["command"]=d["Command"].astype("string");x["state_marker"]=d["State"].astype("string");x["parse_issue_flag"]=False
   table=pa.Table.from_pandas(x,preserve_index=False)
   if writer is None:writer=pq.ParquetWriter(out,table.schema,compression="zstd")
   writer.write_table(table);offset+=n;total+=n
   for k,v in x.isna().sum().items():missing[k]=missing.get(k,0)+int(v)
 if writer is not None:writer.close()
 meta={"processed_filename":"data/processed/tum_id3_hppc_observations.parquet","input_raw_files":[str(p.relative_to(R)).replace(chr(92),"/") for p,_ in files],"input_checksums_sha512":{str(p.relative_to(R)).replace(chr(92),"/"):sha(p) for p,_ in files},"processing_script":"src/preprocessing/p11_pipeline.py","processing_script_sha512":sha(Path(__file__)),"canonical_units":{"test_temperature_c":"degC","time_s":"s","step_time_s":"s","set_time_s":"s","voltage_v":"V","current_a":"A","charge_ah":"Ah","charge_step_ah":"Ah","charge_set_ah":"Ah","energy_wh":"Wh","temperature_1_c":"degC","temperature_2_c":"degC"},"processing_date":"2026-08-20","row_count":total,"column_count":24,"transformations":["official author CSV equivalent of selected MAT test","hours multiplied by 3600 to seconds","no filtering","no scientific derivation"],"scientific_filtering_performed":"NONE"}
 (M/"tum_id3_hppc_observations.yaml").write_text(yaml.safe_dump(meta,sort_keys=False),encoding="utf-8")
 Q["tum_id3_hppc_observations.parquet"]={"raw_files_read":len(files),"raw_records_parsed":total,"technical_rejections":0,"processed_rows":total,"duplicate_rows":0,"missingness":missing}
def zcsv(p,n):
 with zipfile.ZipFile(p) as z,z.open(n) as f:return pd.read_csv(f,sep=";",low_memory=False)
def luh():
 b=W/"SRC_LUH_2024"
 for fn,kind in [("cell_eocv2.zip","capacity"),("cell_plsv2.zip","pulse")]:
  p=b/fn; a=[]
  with zipfile.ZipFile(p) as z: names=[n for n in z.namelist() if n.endswith(".csv")]
  for n in names:
   d=zcsv(p,n);d["source_id"]="SRC_LUH_2024";d["source_filename"]=n;d["source_row"]=np.arange(2,len(d)+2);a.append(d)
  x=pd.concat(a,ignore_index=True,sort=False);x["parse_issue_flag"]=False
  if kind=="capacity":
   x=x.rename(columns={"cap_aged_est_Ah":"measured_capacity_ah","soh_cap":"capacity_soh_fraction","delta_e_Wh":"measured_energy_wh","total_q_chg_sum_Ah":"charge_throughput_ah","total_q_dischg_sum_Ah":"discharge_throughput_ah"})
   cs=["source_id","source_filename","source_row","sd_block_id","timestamp_s","age_type","age_profile","age_temp","age_soc","measured_capacity_ah","capacity_soh_fraction","measured_energy_wh","charge_throughput_ah","discharge_throughput_ah","num_cycles_op","num_cycles_checkup","parse_issue_flag"];out="luh_capacity_observations.parquet"
  else:
   x["resistance_10ms_ohm"]=pd.to_numeric(x.r_ref_10ms_mOhm,errors="coerce")*.001;x["resistance_1s_ohm"]=pd.to_numeric(x.r_ref_1s_mOhm,errors="coerce")*.001;x["baseline_candidate"]=False
   cs=["source_id","source_filename","source_row","sd_block_id","timestamp_s","soc_nom","t_avg_degC","r_ref_10ms_mOhm","r_ref_1s_mOhm","resistance_10ms_ohm","resistance_1s_ohm","baseline_candidate","parse_issue_flag"];out="luh_pulse_resistance_observations.parquet"
  save(out,x[[c for c in cs if c in x]],[p],["archive read in place","no filtering","mechanical unit conversion only"])
 cz=b/"cfg.zip";a=[]
 with zipfile.ZipFile(cz) as z:names=[n for n in z.namelist() if Path(n).name.startswith("cell_cfg_") and n.endswith(".csv")]
 for n in names:
  d=zcsv(cz,n);d["source_id"]="SRC_LUH_2024";d["source_filename"]=n;d["source_row"]=np.arange(2,len(d)+2);d["replicate_id"]=d.slave_id.astype("string")+":"+d.cell_id.astype("string");d["condition_id"]=d.parameter_id.astype("string");a.append(d)
 x=pd.concat(a,ignore_index=True,sort=False);cs=["source_id","source_filename","source_row","cell_id","replicate_id","condition_id","slave_id","parameter_id","age_type","age_temp","age_soc","age_chg_rate","age_dischg_rate","age_profile","cell_type"];save("luh_condition_map.parquet",x[[c for c in cs if c in x]],[cz],["archive read in place","identity preserved"])
def sch():
 b=W/"SRC_SCHREIBER_2025";fs=sorted(b.rglob("*.txt"));a=[]
 for p in fs:
  d=pd.read_csv(p,sep="\t",skiprows=12,encoding="cp1252",low_memory=False);d.columns=[c.lstrip("~") for c in d];x=pd.DataFrame({"source_id":"SRC_SCHREIBER_2025","source_filename":str(p.relative_to(b)).replace(chr(92),"/"),"source_row":np.arange(14,len(d)+14),"scenario":p.parent.name.replace("_scenario",""),"checkup_id":p.stem,"cu_index":int(re.search(r"CU_(\d+)",p.stem).group(1))})
  for u,v in {"Time[s]":"time_s","DataSet":"dataset_id","t-Step[s]":"step_time_s","Line":"protocol_line","Command":"command","U[V]":"voltage_v","I[A]":"current_a","Ah[Ah]":"charge_ah","Wh[Wh]":"energy_wh","Cyc-Count":"cycle_count","State":"state_marker"}.items():
   if u in d:x[v]=d[u]
  for pre,v in [("T1[","temperature_1_c"),("T2[","temperature_2_c")]:
   c=[c for c in d if c.startswith(pre)]
   if c:x[v]=d[c[0]]
  x["parse_issue_flag"]=False;a.append(x)
 x=pd.concat(a,ignore_index=True);save("schreiber_checkup_observations.parquet",x,fs,["tab parse after metadata","filename identity","no filtering"])
def tum():
 b=W/"SRC_TUM_ID3/Data";p=b/"02_Battery/04_OCV/VW_78Ah_1584_pOCV_C10_20deg.mat";ds=sio.loadmat(p,squeeze_me=True,struct_as_record=False)["Dataset"];n=len(ds.Time);x=pd.DataFrame({"source_id":"SRC_TUM_ID3","source_filename":str(p.relative_to(W)).replace(chr(92),"/"),"source_row":np.arange(1,n+1),"test_temperature_c":20.})
 for u,v in {"Time":"time_s","DataSet":"dataset_id","Line":"protocol_line","Command":"command","U":"voltage_v","I":"current_a","Ah":"charge_ah","Wh":"energy_wh","T1":"temperature_1_c","T2":"temperature_2_c","CycCount":"cycle_count","State":"state_marker"}.items():
  q=np.asarray(getattr(ds,u))
  if q.ndim==1 and len(q)==n:x[v]=q
 x["parse_issue_flag"]=False;save("tum_id3_ocv_observations.parquet",x,[p],["MAT vectors preserved"])
 w=b/"03_Vehicle/06_Cycles/02_Standard_Driving/WLTP/WLTP.csv";d=pd.read_csv(w,low_memory=False);mp={"time":"vehicle_time_ms","vehicle_speed":"vehicle_speed_kmh","hv_battery_voltage_x":"hv_battery_voltage_v","hv_battery_current":"hv_battery_current_a","hv_soc":"hv_soc_percent"};x=d[list(mp)].rename(columns=mp);x.insert(0,"source_row",np.arange(2,len(x)+2));x.insert(0,"source_filename",str(w.relative_to(W)).replace(chr(92),"/"));x.insert(0,"source_id","SRC_TUM_ID3");x["parse_issue_flag"]=False;save("tum_id3_wltp_vehicle_observations.parquet",x,[w],["observed channels only"])
 hp=b/"02_Battery/06_HPPC";save_hppc([(hp/"VW_78Ah_1828_HPPC_3C_9steps_0deg.csv",0),(hp/"VW_78Ah_1794_HPPC_3C_9steps_20deg.csv",20),(hp/"VW_78Ah_1856_HPPC_3C_9steps_40deg.csv",40)])
def cambium_average():
 p=W/"SRC_CAMBIUM_2024/ScenarioViewer_Cambium2024_Annual_GEA_file_69141.zip"
 with zipfile.ZipFile(p) as z:
  member=z.namelist()[0];d=pd.read_csv(z.open(member),skiprows=5,usecols=["scenario","gea","t","aer_load_co2e"])
 scenarios=["MidCase","LowRECost","HighRECost"];x=d.loc[d.scenario.isin(scenarios)].copy()
 x=x.rename(columns={"gea":"region","t":"calendar_year","aer_load_co2e":"grid_ci_gco2e_per_kwh"});x.insert(0,"source_filename",str(p.relative_to(W)).replace(chr(92),"/")+"#"+member);x.insert(0,"source_id","SRC_CAMBIUM_2024");x["dataset_version"]=2024;x["metric_identity"]="aer_load_co2e";x["original_unit"]="kg CO2e/MWh_end-use";x["parse_issue_flag"]=False
 x=x[["source_id","source_filename","dataset_version","scenario","region","calendar_year","metric_identity","grid_ci_gco2e_per_kwh","original_unit","parse_issue_flag"]].sort_values(["scenario","region","calendar_year"]).reset_index(drop=True)
 save("cambium_2024_average_grid_ci.parquet",x,[p],["official Scenario Viewer annual GEA export read in place","selected frozen MidCase, LowRECost, HighRECost scenarios","aer_load_co2e retained","1 kg/MWh = 1 g/kWh numerical identity","no national aggregation","no scientific filtering"])
def other():
 p=W/"SRC_NHTS_2022/csv.zip";spec={"vehv2pub.csv":(["HOUSEID","VEHID","ANNMILES","WTHHFIN"],{"HOUSEID":"household_id","VEHID":"vehicle_id","ANNMILES":"annual_miles","WTHHFIN":"survey_weight"},"nhts_vehicle_use_observations.parquet","annual_miles","annual_km"),"tripv2pub.csv":(["HOUSEID","PERSONID","TRIPID","VEHID","TRPMILES","WTTRDFIN"],{"HOUSEID":"household_id","PERSONID":"person_id","VEHID":"vehicle_id","TRPMILES":"trip_miles","WTTRDFIN":"survey_weight"},"nhts_trip_observations.parquet","trip_miles","trip_distance_km"),"ldtv2pub.csv":(["HOUSEID","PERSONID","GCDTOT","WTPERFIN"],{"HOUSEID":"household_id","PERSONID":"person_id","GCDTOT":"long_distance_miles","WTPERFIN":"survey_weight"},"nhts_long_distance_observations.parquet","long_distance_miles","long_distance_km")}
 with zipfile.ZipFile(p) as z:
  for mem,(cs,mp,fn,u,v) in spec.items():
   d=pd.read_csv(z.open(mem),usecols=cs).rename(columns=mp);d[v]=pd.to_numeric(d[u],errors="coerce")*1.609344;d.insert(0,"source_row",np.arange(2,len(d)+2));d.insert(0,"source_filename",mem);d.insert(0,"source_id","SRC_NHTS_2022");d["parse_issue_flag"]=False;save(fn,d,[p],[u+" multiplied by 1.609344","no threshold/aggregation"])
 p=W/"SRC_LLAMAS_OROZCO_2023/LIBs-LCA Supplmentary tables_final_final.xlsx";s=load_workbook(p,read_only=True,data_only=True)["S18 Future Battery impacts"];a=[]
 for st in [10,31,52,73,94,115,136]:
  for c in [4,6,8,10,12,14,16]:
   lab=str(s.cell(st,c-1).value);m=re.search(r"(2020|2030|2040|2050)",lab)
   if s.cell(st,2).value and m:a.append((s.cell(st,2).value,"Current" if lab.startswith("Current") else lab.split()[0],int(m.group(1)),s.cell(st+18,c).value,st+18,c))
 x=pd.DataFrame(a,columns=["chemistry","pathway","calendar_year","pack_ghg_kgco2e_per_kwh","source_row","source_column"]);x.insert(0,"source_filename",str(p.relative_to(W)).replace(chr(92),"/")+"#S18");x.insert(0,"source_id","SRC_LLAMAS_OROZCO_2023");x["manufacturing_geography"]=pd.NA;x["system_boundary"]="battery_production_pack_level";x["parse_issue_flag"]=False;save("llamas_pack_manufacturing_ghg.parquet",x,[p],["pack totals only","no chemistry averaging/interpolation"])
 p=W/"SRC_SEVDARI_2023/25425262_v1.zip";a=[]
 with zipfile.ZipFile(p) as z:
  for n,v in {"Efficiency_3phase_data.xlsx":"charging_efficiency_percent","Powerfactor_3phase_data.xlsx":"power_factor","Reactive_power_3phase_data.xlsx":"reactive_power_var"}.items():
   d=pd.read_excel(io.BytesIO(z.read(n)));a.append(d.melt(id_vars=["Brand"],var_name="current_a",value_name=v).rename(columns={"Brand":"vehicle_test_id"}))
 x=a[0].merge(a[1],how="outer").merge(a[2],how="outer");x["charging_efficiency_fraction"]=x.charging_efficiency_percent/100;x.insert(0,"source_row",np.arange(1,len(x)+1));x.insert(0,"source_filename","Version 1 three workbooks");x.insert(0,"source_id","SRC_SEVDARI_2023");x["parse_issue_flag"]=False;save("sevdari_charging_efficiency_observations.parquet",x,[p],["matrices unpivoted","percent divided by 100","no averaging"])
def main():
 O.mkdir(parents=True,exist_ok=True);M.mkdir(parents=True,exist_ok=True);luh();sch();tum();other();cambium_average();Q["cambium_2023_lrmer"]={"raw_files_read":1,"raw_records_parsed":0,"technical_rejections":1,"processed_rows":0,"duplicate_rows":0,"missingness":{},"rejection_reason":"year-specific CO2e is not an observed column; GWP combination deferred"};(M/"p11_row_reconciliation.json").write_text(json.dumps(Q,indent=2,sort_keys=True),encoding="utf-8")
if __name__=="__main__":main()
def extras():
 b=W/"SRC_TUM_ID3/Data";e=b/"02_Battery/01_CAD/Energy_density.xlsx";s=load_workbook(e,read_only=True,data_only=True).active;rows=[]
 for scale,col in {"cell":"B","module":"D","pack_calculated":"F","pack_measured":"H"}.items():rows.append({"scale":scale,"topology_parallel":s[f"{col}10"].value,"topology_series":s[f"{col}11"].value,"specified_capacity_ah":s[f"{col}12"].value,"specified_energy_kwh":s[f"{col}13"].value,"experimental_capacity_ah":s[f"{col}15"].value,"experimental_energy_kwh":s[f"{col}16"].value})
 (O/"tum_id3_pack_architecture.yaml").write_text(yaml.safe_dump({"source_id":"SRC_TUM_ID3","source_filename":str(e.relative_to(W)).replace(chr(92),"/"),"records":rows,"scientific_filtering_performed":"NONE"},sort_keys=False),encoding="utf-8")
 p=W/"SRC_CAMBIUM_LRMER_2023/1707947178-Cambium23_LRMER_GEAregions_0.xlsx";a=pd.read_excel(p,sheet_name="Data - Annual",header=None);met=a.iloc[2].ffill();sc=a.iloc[3].ffill();yr=a.iloc[4];rows=[]
 for c in range(15,303):
  if pd.isna(yr.iloc[c]):continue
  unit="kg/MWh" if str(met.iloc[c]).startswith("CO2 ") else "g/MWh"
  for r in range(5,len(a)):
   if pd.notna(a.iat[r,1]):rows.append((2023,str(sc.iloc[c]),str(a.iat[r,1]),int(float(yr.iloc[c])),str(met.iloc[c]),unit,a.iat[r,c],r+1,c+1))
 x=pd.DataFrame(rows,columns=["dataset_version","scenario","region","calendar_year","metric_identity","unit","metric_value","source_row","source_column"]);x.insert(0,"source_filename",str(p.relative_to(W)).replace(chr(92),"/"));x.insert(0,"source_id","SRC_CAMBIUM_LRMER_2023");x["parse_issue_flag"]=False;save("cambium_lrmer_2023_components.parquet",x,[p],["annual LRMER components unpivoted","no GWP combination","no national aggregation"])
 Q.pop("cambium_2023_lrmer",None);(M/"p11_row_reconciliation.json").write_text(json.dumps(Q,indent=2,sort_keys=True),encoding="utf-8")
if __name__=="__main__":extras()
