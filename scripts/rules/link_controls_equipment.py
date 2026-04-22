"""controls_master_draft_v2 의 related_equipment_codes 를 equipment_master 의 EQ_* 코드로 보정.

입력
  - data/risk_db/master/controls_master_draft_v2.csv
  - data/risk_db/equipment/equipment_master.json
출력 (in-place 갱신 후 통계 리포트 stdout)
  - data/risk_db/master/controls_master_draft_v2.csv (related_equipment_codes 컬럼)
  - data/risk_db/master/controls_equipment_linkage.csv (검토용 매트릭스)
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "data/risk_db/master/controls_master_draft_v2.csv"
EQ_MASTER = ROOT / "data/risk_db/equipment/equipment_master.json"
LINKAGE_OUT = ROOT / "data/risk_db/master/controls_equipment_linkage.csv"

# control_code → [EQ_* codes that naturally apply]
# alias 키가 필요한 케이스는 comment 로 표기 (신규 equipment 후보는 eq_candidate 리턴)
CONTROL_EQUIPMENT_MAP: dict[str, list[str]] = {
    # engineering
    "ctrl_fall_protection_install": ["EQ_SCAFF", "EQ_MOVSCAFF", "EQ_SYST_SCAFF", "EQ_AWP", "EQ_SCISSORLIFT", "EQ_LADDER_MOV"],
    "ctrl_local_ventilation_install": ["EQ_WELDER_ARC", "EQ_WELDER_GAS", "EQ_SPRAY_GUN", "EQ_GRINDER"],
    "ctrl_guard_installation": ["EQ_GRINDER", "EQ_CIRCULAR_SAW", "EQ_DRILL", "EQ_REBAR_CUTTER", "EQ_CONCRETE_MIXER"],
    "ctrl_lockout_tagout": ["EQ_DIST_PANEL", "EQ_GENERATOR", "EQ_AIRCOMP", "EQ_CONCRETE_MIXER"],
    "ctrl_electrical_isolation": ["EQ_DIST_PANEL", "EQ_GENERATOR", "EQ_WELDER_ARC"],
    "ctrl_confined_space_ventilation": ["EQ_MANHOLE_BLOWER"],
    "ctrl_drop_prevention": ["EQ_CRANE_TOWER", "EQ_CRANE_MOB", "EQ_HOIST", "EQ_SCAFF"],
    "ctrl_harness_attachment": ["EQ_SCAFF", "EQ_AWP", "EQ_SCISSORLIFT", "EQ_LADDER_MOV"],
    "ctrl_dust_suppression": ["EQ_JACKHAMMER", "EQ_GRINDER", "EQ_CONCRETE_MIXER", "EQ_EXCAV"],
    "ctrl_chemical_storage_segregation": ["EQ_GAS_CYLINDER"],
    "ctrl_excavation_shoring": ["EQ_EXCAV", "EQ_BULLDOZER"],
    "ctrl_scaffold_install_std": ["EQ_SCAFF", "EQ_MOVSCAFF", "EQ_SYST_SCAFF"],
    "ctrl_machine_emergency_stop": ["EQ_CONCRETE_MIXER", "EQ_HOIST", "EQ_CONC_PUMP"],
    # ppe
    "ctrl_ppe_wear": [],  # 모든 장비 횡단 — 특정 장비 링크 지양 (장비 무관)
    "ctrl_ppe_provision": [],
    # training (장비 무관)
    "ctrl_special_training": [],
    "ctrl_pre_work_briefing": [],
    "ctrl_safety_training_general": [],
    # inspection
    "ctrl_periodic_inspection": [],  # 모든 장비 — 장비 횡단
    "ctrl_pre_work_inspection": [],
    "ctrl_atmospheric_measurement": ["EQ_MANHOLE_BLOWER"],
    "ctrl_working_environment_measurement": [],
    "ctrl_checklist_verification": [],
    "ctrl_scaffold_inspection": ["EQ_SCAFF", "EQ_MOVSCAFF", "EQ_SYST_SCAFF"],
    "ctrl_pre_energization_check": ["EQ_DIST_PANEL", "EQ_WELDER_ARC"],
    "ctrl_lifting_equipment_inspection": ["EQ_CRANE_TOWER", "EQ_CRANE_MOB", "EQ_HOIST"],
    "ctrl_electrical_equipment_inspection": ["EQ_DIST_PANEL", "EQ_WELDER_ARC", "EQ_DRILL", "EQ_GRINDER", "EQ_GENERATOR"],
    # document
    "ctrl_msds_posting": [],
    "ctrl_record_retention": [],
    "ctrl_work_plan_preparation": [],
    "ctrl_safety_sign_posting": [],
    "ctrl_incident_report": [],
    "ctrl_lifting_work_plan": ["EQ_CRANE_TOWER", "EQ_CRANE_MOB", "EQ_HOIST"],
    # supervision
    "ctrl_supervisor_assignment": [],
    "ctrl_signalman_assignment": ["EQ_CRANE_TOWER", "EQ_CRANE_MOB", "EQ_HOIST", "EQ_FORKLIFT"],
    "ctrl_standby_person_assignment": ["EQ_MANHOLE_BLOWER"],
    "ctrl_fire_watch_assignment": ["EQ_WELDER_ARC", "EQ_WELDER_GAS", "EQ_GRINDER"],
    "ctrl_crane_signal_rule": ["EQ_CRANE_TOWER", "EQ_CRANE_MOB", "EQ_HOIST"],
    "ctrl_work_leader_designation": ["EQ_EXCAV", "EQ_BULLDOZER", "EQ_FORKLIFT", "EQ_ROLLER", "EQ_CONC_PUMP", "EQ_ASPHALT_PAVER"],
    # permit
    "ctrl_work_permit_issue": [],
    "ctrl_confined_space_permit": ["EQ_MANHOLE_BLOWER"],
    "ctrl_hot_work_permit": ["EQ_WELDER_ARC", "EQ_WELDER_GAS", "EQ_GRINDER"],
    "ctrl_excavation_permit": ["EQ_EXCAV", "EQ_BULLDOZER"],
    "ctrl_height_work_permit": ["EQ_SCAFF", "EQ_MOVSCAFF", "EQ_AWP", "EQ_SCISSORLIFT"],
    # administrative (장비 무관 다수)
    "ctrl_access_restriction": [],
    "ctrl_work_zone_separation": [],
    "ctrl_simultaneous_work_coordination": [],
    "ctrl_work_area_demarcation": [],
    "ctrl_work_hour_restriction": [],
    # emergency
    "ctrl_emergency_evacuation": [],
    "ctrl_first_aid_setup": [],
    "ctrl_fire_extinguisher_setup": ["EQ_WELDER_ARC", "EQ_WELDER_GAS"],
    # health
    "ctrl_special_health_check": [],
    "ctrl_exposure_monitoring": [],
    "ctrl_noise_exposure_limit": ["EQ_JACKHAMMER", "EQ_GRINDER", "EQ_CIRCULAR_SAW", "EQ_AIRCOMP", "EQ_PILEDRIVER"],
    "ctrl_heat_stress_management": [],
    # housekeeping
    "ctrl_housekeeping_cleanup": [],
    "ctrl_slip_prevention": [],
    "ctrl_hot_work_area_clear": ["EQ_WELDER_ARC", "EQ_WELDER_GAS"],
    # traffic
    "ctrl_traffic_guide_assignment": ["EQ_EXCAV", "EQ_FORKLIFT", "EQ_BULLDOZER", "EQ_ROLLER"],
    "ctrl_backup_alarm_use": ["EQ_EXCAV", "EQ_FORKLIFT", "EQ_BULLDOZER", "EQ_ROLLER"],
    "ctrl_vehicle_path_separation": ["EQ_EXCAV", "EQ_FORKLIFT", "EQ_BULLDOZER"],
    "ctrl_speed_limit": ["EQ_FORKLIFT", "EQ_EXCAV"],
}


def equipment_codes() -> list[str]:
    with EQ_MASTER.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [e["code"] for e in data["equipment"]]


def main() -> None:
    known_codes = set(equipment_codes())
    # 1) referenced 중 master 에 없는 code 는 신규 후보로 분류
    referenced_codes: set[str] = set()
    for codes in CONTROL_EQUIPMENT_MAP.values():
        referenced_codes.update(codes)
    missing = referenced_codes - known_codes
    if missing:
        print(f"[WARN] referenced but not in master: {sorted(missing)}")

    # 2) master CSV 갱신
    rows = []
    with MASTER.open("r", encoding="utf-8-sig", newline="") as f:
        fieldnames = None
        for r in csv.DictReader(f):
            if fieldnames is None:
                fieldnames = list(r.keys())
            mapping = CONTROL_EQUIPMENT_MAP.get(r["control_code"])
            if mapping is not None:
                r["related_equipment_codes"] = ",".join(mapping)
            rows.append(r)

    with MASTER.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # 3) linkage 매트릭스 CSV
    eq_to_controls: dict[str, list[str]] = {eq: [] for eq in known_codes}
    for r in rows:
        rel = [c for c in (r["related_equipment_codes"].split(",") if r["related_equipment_codes"] else []) if c]
        for eq in rel:
            if eq in eq_to_controls:
                eq_to_controls[eq].append(r["control_code"])

    with LINKAGE_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["equipment_code", "linked_controls_count", "linked_control_codes"])
        for eq in sorted(known_codes):
            w.writerow([eq, len(eq_to_controls[eq]), ",".join(sorted(eq_to_controls[eq]))])

    # 4) 통계
    linked_controls = sum(1 for r in rows if r["related_equipment_codes"])
    linked_equip = sum(1 for eq, cs in eq_to_controls.items() if cs)
    print(f"[controls_with_equipment] {linked_controls}/{len(rows)} ({linked_controls/len(rows)*100:.0f}%)")
    print(f"[equipment_with_controls] {linked_equip}/{len(known_codes)} ({linked_equip/len(known_codes)*100:.0f}%)")
    orphan_eq = [eq for eq, cs in eq_to_controls.items() if not cs]
    if orphan_eq:
        print(f"[orphan_equipment] {orphan_eq}")


if __name__ == "__main__":
    main()
