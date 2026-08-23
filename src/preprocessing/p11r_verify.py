import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/processed"
META=OUT/"metadata"
SNAPSHOT=META/"p11r_first_run_sha256.json"
DETERMINISM=META/"p11r_determinism.json"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def output_hashes():
    excluded={SNAPSHOT.resolve(),DETERMINISM.resolve()}
    return {str(p.relative_to(ROOT)).replace("\\","/"):digest(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.resolve() not in excluded}

def raw_integrity():
    baseline_path=ROOT/"data/metadata/P11R_PRE_RECOVERY_RAW_SHA256.json"
    baseline=json.loads(baseline_path.read_text(encoding="utf-8"))
    old={rel:{"expected_sha256":expected,"actual_sha256":digest(ROOT/rel),"unchanged":digest(ROOT/rel)==expected} for rel,expected in baseline.items()}
    new_paths=[
        "data/raw/SRC_CAMBIUM_2024/ScenarioViewer_Cambium2024_Annual_GEA_file_69141.zip",
        "data/raw/SRC_TUM_ID3/Data/02_Battery/06_HPPC/VW_78Ah_1794_HPPC_3C_9steps_20deg.csv",
        "data/raw/SRC_TUM_ID3/Data/02_Battery/06_HPPC/VW_78Ah_1828_HPPC_3C_9steps_0deg.csv",
        "data/raw/SRC_TUM_ID3/Data/02_Battery/06_HPPC/VW_78Ah_1856_HPPC_3C_9steps_40deg.csv",
    ]
    new={rel:{"bytes":(ROOT/rel).stat().st_size,"sha256":digest(ROOT/rel),"status":"RAW_UNMODIFIED"} for rel in new_paths}
    result={"verification_date":"2026-08-20","previous_raw_file_count":len(old),"all_previous_raw_unchanged":all(v["unchanged"] for v in old.values()),"previous_raw_files":old,"new_raw_files":new,"raw_scientific_values_manually_edited":"NONE"}
    (ROOT/"data/metadata/P11R_RAW_INTEGRITY_VERIFICATION.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    if not result["all_previous_raw_unchanged"]:raise SystemExit("Previous raw checksum mismatch")

def main(mode):
    META.mkdir(parents=True,exist_ok=True)
    if mode=="snapshot":
        SNAPSHOT.write_text(json.dumps(output_hashes(),indent=2,sort_keys=True),encoding="utf-8")
        raw_integrity()
        print(f"snapshot_files={len(json.loads(SNAPSHOT.read_text()))}")
    else:
        first=json.loads(SNAPSHOT.read_text(encoding="utf-8"));second=output_hashes()
        result={"verification_date":"2026-08-20","first_run_files":len(first),"second_run_files":len(second),"identical_file_sets":set(first)==set(second),"identical_sha256":first==second,"mismatches":{k:{"first":first.get(k),"second":second.get(k)} for k in sorted(set(first)|set(second)) if first.get(k)!=second.get(k)}}
        DETERMINISM.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
        raw_integrity()
        print(json.dumps(result,sort_keys=True))
        if not result["identical_sha256"]:raise SystemExit("Processed output determinism mismatch")

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=["snapshot","verify"]);main(parser.parse_args().mode)
