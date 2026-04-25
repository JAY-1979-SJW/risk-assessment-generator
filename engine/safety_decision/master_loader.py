"""
MasterLoader — YAML 마스터 파일 로드 및 인덱스 구축 (read-only)
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
SAFETY_DIR = ROOT / "data/masters/safety"


class MasterLoader:
    """모든 마스터 YAML을 메모리에 로드하고 ID 기반 lookup을 제공한다."""

    def __init__(self) -> None:
        self._eq_index: dict[str, dict] = {}
        self._doc_index: dict[str, dict] = {}
        self._wt_index: dict[str, dict] = {}
        self._train_index: dict[str, dict] = {}
        self._insp_index: dict[str, dict] = {}
        self._clause_index: dict[str, dict] = {}

        # mapping: key → list of mapping rows
        self._eq_doc: dict[str, list[dict]] = {}
        self._eq_train: dict[str, list[dict]] = {}
        self._eq_insp: dict[str, dict] = {}       # equipment_code → inspection row
        self._wt_doc: dict[str, list[dict]] = {}
        self._wt_train: dict[str, list[dict]] = {}

        # compliance links: (target_type, target_id) → list of link rows
        self._clink_by_target: dict[tuple[str, str], list[dict]] = {}

        self._load_all()

    # ── 내부 로더 ────────────────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: Path) -> dict | list:
        if not path.exists():
            raise FileNotFoundError(f"마스터 파일 없음: {path}")
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 파싱 오류 {path.name}: {e}") from e

    def _load_all(self) -> None:
        # equipment_types (중첩 구조)
        data = self._load_yaml(SAFETY_DIR / "equipment/equipment_types.yml")
        for group in data.get("equipment_types", []):
            for eq in group.get("equipment", []):
                if "code" in eq:
                    self._eq_index[eq["code"]] = eq

        # document_catalog
        data = self._load_yaml(SAFETY_DIR / "documents/document_catalog.yml")
        for doc in data.get("documents", []):
            if "id" in doc:
                self._doc_index[doc["id"]] = doc

        # work_types
        data = self._load_yaml(SAFETY_DIR / "work_types.yml")
        for wt in data.get("work_types", []):
            if "code" in wt:
                self._wt_index[wt["code"]] = wt

        # training_types
        data = self._load_yaml(SAFETY_DIR / "training/training_types.yml")
        for t in data.get("training_types", []):
            if "training_code" in t:
                self._train_index[t["training_code"]] = t

        # inspection_types
        data = self._load_yaml(SAFETY_DIR / "inspection/inspection_types.yml")
        for i in data.get("inspection_types", []):
            if "inspection_code" in i:
                self._insp_index[i["inspection_code"]] = i

        # compliance_clauses
        data = self._load_yaml(SAFETY_DIR / "compliance/compliance_clauses.yml")
        for c in data.get("compliance_clauses", []):
            if "id" in c:
                self._clause_index[c["id"]] = c

        # mappings
        self._eq_doc = self._load_mapping(
            SAFETY_DIR / "mappings/equipment_document_requirements.yml",
            key="equipment_code",
        )
        self._eq_train = self._load_mapping(
            SAFETY_DIR / "mappings/equipment_training_requirements.yml",
            key="equipment_code",
        )
        # equipment_inspection_requirements (equipment_code → single row)
        insp_path = SAFETY_DIR / "mappings/equipment_inspection_requirements.yml"
        if insp_path.exists():
            insp_data = self._load_yaml(insp_path)
            for row in insp_data.get("requirements", []):
                code = str(row.get("equipment_code", ""))
                if code:
                    self._eq_insp[code] = row

        self._wt_doc = self._load_mapping(
            SAFETY_DIR / "mappings/work_document_requirements.yml",
            key="work_type_code",
        )
        self._wt_train = self._load_mapping(
            SAFETY_DIR / "mappings/work_training_requirements.yml",
            key="work_type_code",
        )

        # compliance_links
        data = self._load_yaml(SAFETY_DIR / "compliance/compliance_links.yml")
        for lk in data.get("compliance_links", []):
            key = (str(lk.get("target_type", "")), str(lk.get("target_id", "")))
            self._clink_by_target.setdefault(key, []).append(lk)

    def _load_mapping(self, path: Path, key: str) -> dict[str, list[dict]]:
        data = self._load_yaml(path)
        index: dict[str, list[dict]] = {}
        for row in data.get("requirements", []):
            k = str(row.get(key, ""))
            if k:
                index.setdefault(k, []).append(row)
        return index

    # ── 공개 lookup ──────────────────────────────────────────────────────

    def get_equipment(self, code: str) -> dict:
        if code not in self._eq_index:
            raise ValueError(f"장비 코드 미등록: '{code}'")
        return self._eq_index[code]

    def get_work_type(self, code: str) -> dict:
        if code not in self._wt_index:
            raise ValueError(f"작업 유형 코드 미등록: '{code}'")
        return self._wt_index[code]

    def get_document(self, doc_id: str) -> dict | None:
        return self._doc_index.get(doc_id)

    def get_training(self, training_code: str) -> dict | None:
        return self._train_index.get(training_code)

    def get_inspection(self, inspection_code: str) -> dict | None:
        return self._insp_index.get(inspection_code)

    def eq_insp_requirement(self, equipment_code: str) -> dict | None:
        return self._eq_insp.get(equipment_code)

    def all_inspection_codes(self) -> set[str]:
        return set(self._insp_index)

    def get_clause(self, clause_id: str) -> dict | None:
        return self._clause_index.get(clause_id)

    def eq_doc_requirements(self, equipment_code: str) -> list[dict]:
        return self._eq_doc.get(equipment_code, [])

    def eq_train_requirements(self, equipment_code: str) -> list[dict]:
        return self._eq_train.get(equipment_code, [])

    def wt_doc_requirements(self, work_type_code: str) -> list[dict]:
        return self._wt_doc.get(work_type_code, [])

    def wt_train_requirements(self, work_type_code: str) -> list[dict]:
        return self._wt_train.get(work_type_code, [])

    def compliance_links(self, target_type: str, target_id: str) -> list[dict]:
        return self._clink_by_target.get((target_type, target_id), [])

    def all_equipment_codes(self) -> set[str]:
        return set(self._eq_index)

    def all_work_type_codes(self) -> set[str]:
        return set(self._wt_index)
