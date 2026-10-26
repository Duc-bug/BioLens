"""
Engine Goi y Mon an - Thuc uong Bo duong (Nutraceutical & Functional Diet Recommender)
Tich hop trong he thong BioLens / BioLens-X.
Xu ly da muc tieu: An toan thuc pham, Cong nang duong sinh, Tuong thich am thuc va Ca nhan hoa the trang.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from configs.settings import STORAGE_DIR
from dataset.nutraceutical_rules import (
    HEALTH_GOALS,
    GRADE_TOXIC_FORBIDDEN,
    GRADE_MEDICINAL_ONLY,
    GRADE_BEVERAGE_INFUSION,
    GRADE_CULINARY_TONIC,
    GRADE_SPICE_AROMATIC,
    HERB_FOOD_INCOMPATIBILITIES,
    SPECIAL_POPULATION_WARNINGS,
)

REGISTRY_PATH = STORAGE_DIR / "catalog" / "nutraceutical_registry.json"


class NutraceuticalEngine:
    def __init__(self, registry_path: Path = REGISTRY_PATH):
        self.registry_path = registry_path
        self._registry: Dict[str, Any] = {}
        self._load_registry()

    def _load_registry(self):
        """Nap file database nutraceutical_registry.json."""
        if not self.registry_path.exists():
            print(f"⚠️ [NutraceuticalEngine] Chưa tìm thấy {self.registry_path}, đang chờ sinh dữ liệu...")
            return

        with open(self.registry_path, "r", encoding="utf-8") as f:
            self._registry = json.load(f)
        print(f"✅ [NutraceuticalEngine] Đã tải cơ sở tri thức ẩm thực của {len(self._registry)} loài.")

    def get_profile(self, species_key: str) -> Optional[Dict[str, Any]]:
        """Lay ho so am thuc cua 1 loai theo speciesKey GBIF."""
        return self._registry.get(str(species_key))

    def recommend_for_species(
        self,
        species_key: str,
        health_goal: Optional[str] = None,
        user_constitution: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Goi y mon an / thuc uong duong sinh theo loai cay vua chup duoc.
        Kiem tra an toan doc tinh tuyet doi truoc khi tra ve ket qua.
        """
        profile = self.get_profile(species_key)
        if not profile:
            return {
                "success": False,
                "speciesKey": species_key,
                "message": f"Không tìm thấy thông tin ẩm thực cho mã loài {species_key}."
            }

        # 1. Kiem tra neu la loai doc
        if profile.get("isToxic") or profile.get("edibilityGrade") == GRADE_TOXIC_FORBIDDEN:
            return {
                "success": True,
                "speciesKey": species_key,
                "isSafe": False,
                "edibilityGrade": GRADE_TOXIC_FORBIDDEN,
                "alertLevel": "DANGER_CRITICAL",
                "warningTitle": "🚫 CẢNH BÁO NGUY HIỂM: CÂY CÓ ĐỘC — CẤM ĂN UỐNG",
                "warningMessage": (
                    f"Loài cây này ({profile.get('primaryVietnameseName')}) được xác định chứa hoạt chất có độc tính cao. "
                    f"Lý do: {profile.get('toxicAlertReason', 'Chứa độc tính nguy hiểm')}. "
                    f"TUYỆT ĐỐI KHÔNG sử dụng làm rau ăn, pha trà, ngâm rượu hoặc nấu nướng dưới bất kỳ hình thức nào."
                ),
                "recipes": [],
                "contraindications": ["Tuyệt đối cấm dùng trong ẩm thực."],
            }

        # 2. Kiem tra neu la loai duoc lieu chuyen dung (khong lam am thuc dai tra)
        if profile.get("edibilityGrade") == GRADE_MEDICINAL_ONLY:
            return {
                "success": True,
                "speciesKey": species_key,
                "isSafe": False,
                "edibilityGrade": GRADE_MEDICINAL_ONLY,
                "alertLevel": "CAUTION_RESTRICTED",
                "warningTitle": "⚠️ DƯỢC LIỆU CHUYÊN KHOA — KHÔNG NÊN TỰ Ý NẤU ĂN",
                "warningMessage": (
                    f"Loài này ({profile.get('primaryVietnameseName')}) chủ yếu dùng làm thuốc điều trị chuyên khoa "
                    f"hoặc có dược tính mạnh. Cần có sự hướng dẫn và kê đơn liều lượng chính xác từ bác sĩ y học cổ truyền."
                ),
                "recipes": [],
                "contraindications": ["Không dùng làm thực phẩm hàng ngày."],
            }

        # 3. Loai an toan: Loc danh sach cong thuc
        recipes = list(profile.get("recipes", []))
        if health_goal and health_goal in HEALTH_GOALS:
            goal_meta = HEALTH_GOALS[health_goal]
            filtered = [r for r in recipes if health_goal in profile.get("matchedHealthGoals", [])]
            if filtered:
                recipes = filtered

        # 4. Kiem tra them cac luu y dac thu the trang
        population_warnings: List[str] = []
        if user_constitution and user_constitution in SPECIAL_POPULATION_WARNINGS:
            pop_rule = SPECIAL_POPULATION_WARNINGS[user_constitution]
            combined_desc = f"{profile.get('traditionalProperties', '')} {profile.get('gradeDescription', '')}".lower()
            for kw in pop_rule["forbidden_terms"]:
                if kw in combined_desc:
                    population_warnings.append(pop_rule["warning"])
                    break

        return {
            "success": True,
            "speciesKey": species_key,
            "isSafe": True,
            "edibilityGrade": profile.get("edibilityGrade"),
            "gradeDescription": profile.get("gradeDescription"),
            "primaryVietnameseName": profile.get("primaryVietnameseName"),
            "canonicalName": profile.get("canonicalName"),
            "matchedHealthGoals": [HEALTH_GOALS[g]["name"] for g in profile.get("matchedHealthGoals", []) if g in HEALTH_GOALS],
            "recipes": recipes,
            "contraindications": profile.get("contraindications", []),
            "populationWarnings": population_warnings,
            "traditionalProperties": profile.get("traditionalProperties", ""),
            "partsUsed": profile.get("partsUsed", ""),
        }

    def search_by_symptom(
        self,
        query: str,
        user_constitution: Optional[str] = None,
        grade_filter: Optional[str] = None,
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Tim kiem duoc thien va mon an duong sinh theo trieu chung hoac nhu cau nguoi dung.
        Vi du: "mất ngủ", "nóng trong nhiệt miệng", "bồi bổ sau ốm", "đau nhức xương khớp".
        """
        query_norm = query.lower().strip()
        scored_candidates: List[tuple[float, Dict[str, Any]]] = []

        # Xac dinh health_goal phu hop nhat tu query
        matched_goal_ids = []
        for goal_id, goal_meta in HEALTH_GOALS.items():
            for kw in goal_meta["keywords"]:
                if kw in query_norm or query_norm in kw:
                    matched_goal_ids.append(goal_id)
                    break

        for sp_key, item in self._registry.items():
            # Bo qua cay doc hoac cay chi dung lam thuoc
            if item.get("isToxic") or item.get("edibilityGrade") in (GRADE_TOXIC_FORBIDDEN, GRADE_MEDICINAL_ONLY):
                continue

            if grade_filter and item.get("edibilityGrade") != grade_filter:
                continue

            score = 0.0
            sp_goals = item.get("matchedHealthGoals", [])
            sp_name = item.get("primaryVietnameseName", "").lower()
            sp_prop = item.get("traditionalProperties", "").lower()

            # Diem trung khop goal
            for gid in matched_goal_ids:
                if gid in sp_goals:
                    score += 3.0

            # Diem trung khop truc tiep ten goi hoac tinh vi
            if query_norm in sp_name:
                score += 5.0
            for term in query_norm.split():
                if len(term) >= 2 and term in sp_prop:
                    score += 1.0

            if score > 0:
                scored_candidates.append((score, item))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_candidates[:top_k]

        results = []
        for score, item in top_items:
            results.append({
                "speciesKey": item.get("speciesKey"),
                "primaryVietnameseName": item.get("primaryVietnameseName"),
                "canonicalName": item.get("canonicalName"),
                "edibilityGrade": item.get("edibilityGrade"),
                "gradeDescription": item.get("gradeDescription"),
                "relevanceScore": round(score, 2),
                "matchedHealthGoals": [HEALTH_GOALS[g]["name"] for g in item.get("matchedHealthGoals", []) if g in HEALTH_GOALS],
                "recipes": item.get("recipes", []),
                "contraindications": item.get("contraindications", []),
                "traditionalProperties": item.get("traditionalProperties", "")
            })

        return results

    def get_categories_metadata(self) -> Dict[str, Any]:
        """Tra ve danh muc the trang va quy tac am thuc cho Frontend UI."""
        return {
            "healthGoals": [
                {
                    "id": k,
                    "name": v["name"],
                    "keywords": v["keywords"][:4],
                    "tcmProperty": v["tcm_property"]
                }
                for k, v in HEALTH_GOALS.items()
            ],
            "edibilityGrades": [
                {"id": GRADE_CULINARY_TONIC, "name": "Canh & Cháo Dưỡng Sinh", "badge": "🍲 Canh/Cháo"},
                {"id": GRADE_BEVERAGE_INFUSION, "name": "Trà & Nước Dưỡng Sinh", "badge": "🍵 Trà Thảo Mộc"},
                {"id": GRADE_SPICE_AROMATIC, "name": "Gia Vị & Thảo Mộc Thơm", "badge": "🌿 Gia Vị"},
            ],
            "specialPopulations": [
                {"id": k, "label": v["label"]} for k, v in SPECIAL_POPULATION_WARNINGS.items()
            ]
        }
