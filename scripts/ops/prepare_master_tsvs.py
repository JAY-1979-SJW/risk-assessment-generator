"""Prepare master/rules TSVs for server load. Idempotent. No DB access."""
import csv, json, os, sys, io

SRC = {
    "controls":       "data/risk_db/master/controls_master_draft_v2.csv",
    "sn_v2":          "data/risk_db/master/sentence_normalization_sample_v2.csv",
    "sl_v2":          "data/risk_db/master/sentence_labeling_sample_v2.csv",
    "scm_v2":         "data/risk_db/master/sentence_control_mapping_sample_v2.csv",
    "rules":          "data/risk_db/rules/safety_rules.json",
}
OUT = "C:/tmp/kras_master"
os.makedirs(OUT, exist_ok=True)

def strip_bom(s):
    if isinstance(s, str) and s.startswith("﻿"):
        return s[1:]
    return s

def clean(v):
    if v is None: return ""
    return str(v).replace("\t"," ").replace("\r"," ").replace("\n"," ").strip()

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        rows = [ {strip_bom(k): v for k,v in row.items()} for row in r ]
    return rows

# ---------- 1) controls ----------
rows = read_csv(SRC["controls"])
print(f"[controls] raw {len(rows)} rows")
out = os.path.join(OUT, "controls.tsv")
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(["control_code","control_name","category","extra_json"])
    n=0
    for r in rows:
        code = clean(r.get("control_code"))
        if not code: continue
        name_ko = clean(r.get("control_name_ko"))
        category = clean(r.get("control_category"))
        extra = {k: r.get(k,"") for k in r.keys() if k not in ("control_code","control_name_ko","control_category")}
        w.writerow([code, name_ko, category, json.dumps(extra, ensure_ascii=False)])
        n+=1
    print(f"  wrote {n} -> {out}")

# ---------- 2) sentence_normalization (v2) ----------
rows = read_csv(SRC["sn_v2"])
print(f"[sn_v2] raw {len(rows)} rows")
out = os.path.join(OUT, "sentence_normalization_v2.tsv")
src_file = os.path.basename(SRC["sn_v2"])
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(["source_file","row_no","raw_sentence","normalized_sentence","version","extra_json"])
    for i,r in enumerate(rows, 1):
        raw = clean(r.get("raw_sentence_text"))
        nrm = clean(r.get("normalized_sentence_text"))
        extra = {k: r.get(k,"") for k in r.keys() if k not in ("raw_sentence_text","normalized_sentence_text")}
        w.writerow([src_file, i, raw, nrm, "v2", json.dumps(extra, ensure_ascii=False)])
print(f"  wrote {len(rows)} -> {out}")

# ---------- 3) sentence_labels (labeling v2 + control_mapping v2) ----------
out = os.path.join(OUT, "sentence_labels.tsv")
total = 0
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(["source_file","row_no","sentence","label","sub_label","extra_json"])
    # 3a labeling v2
    rows = read_csv(SRC["sl_v2"])
    src = os.path.basename(SRC["sl_v2"])
    for i,r in enumerate(rows, 1):
        sent = clean(r.get("sentence_text"))
        if not sent: continue
        label = clean(r.get("sentence_type_candidate"))
        sub   = clean(r.get("obligation_level_candidate"))
        extra = {k: r.get(k,"") for k in r.keys() if k not in ("sentence_text",)}
        w.writerow([src, i, sent, label, sub, json.dumps(extra, ensure_ascii=False)])
        total += 1
    print(f"  +sl_v2 {len(rows)}")
    # 3b sentence_control_mapping v2
    rows = read_csv(SRC["scm_v2"])
    src = os.path.basename(SRC["scm_v2"])
    for i,r in enumerate(rows, 1):
        sent = clean(r.get("sentence_text"))
        if not sent: continue
        label = clean(r.get("sentence_type"))
        sub   = clean(r.get("control_category_candidate"))
        extra = {k: r.get(k,"") for k in r.keys() if k not in ("sentence_text",)}
        w.writerow([src, i, sent, label, sub, json.dumps(extra, ensure_ascii=False)])
        total += 1
    print(f"  +scm_v2 {len(rows)}")
print(f"  wrote total {total} -> {out}")

# ---------- 4) rules (safety_rules.json → rule_sets + rules) ----------
with open(SRC["rules"], encoding="utf-8") as f:
    rd = json.load(f)
meta = rd.get("_meta", {})
rules = rd.get("rules", [])
set_tsv = os.path.join(OUT, "rule_set.tsv")
rule_tsv = os.path.join(OUT, "rules.tsv")
with open(set_tsv, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(["rule_set_name","source_file","version","description"])
    w.writerow(["safety_rules", "data/risk_db/rules/safety_rules.json", str(meta.get("version","")), clean(meta.get("description",""))])
with open(rule_tsv, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(["rule_key","pattern","action","enabled","extra_json"])
    for r in rules:
        rkey = clean(r.get("rule_id"))
        pat  = clean(r.get("condition_expr"))
        act  = clean(r.get("obligation"))
        extra = {k: r.get(k,"") for k in r.keys() if k not in ("rule_id","condition_expr","obligation")}
        w.writerow([rkey, pat, act, "t", json.dumps(extra, ensure_ascii=False)])
print(f"[rules] rule_set=1, rules={len(rules)} -> {rule_tsv}")

print("\n===== OUTPUTS =====")
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    print(f"  {p}  {os.path.getsize(p)} B")
