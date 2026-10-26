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

    def answer_plant_question(self, question: str, species_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Trả lời câu hỏi tự nhiên về thảo mộc & ẩm thực dược thiện ("Hỏi cây gì cũng biết").
        Dựa trên 100% cơ sở dữ liệu Dược điển và dân gian đã kiểm chứng, tuyệt đối không bịa đặt.
        """
        q = question.strip().lower()
        if not q:
            return {
                "success": False,
                "answer": "Vui lòng nhập câu hỏi về loài cây hoặc món ăn bạn quan tâm.",
                "suggestedQuestions": [
                    "Cây chanh pha nước sôi 100°C có tốt không?",
                    "Cây ngải cứu bà bầu ăn được không?",
                    "Cây lá lốt ăn với món gì bổ xương khớp?",
                    "Bị ho khan rát họng nên uống trà gì?"
                ]
            }

        target_species: Optional[Dict[str, Any]] = None

        # 1. Nếu người dùng chỉ định sẵn species_key
        if species_key and str(species_key) in self._registry:
            target_species = self._registry[str(species_key)]
        else:
            # Tìm kiếm loài cây được nhắc đến trong câu hỏi
            best_match = None
            max_len = 0
            for sp_k, sp_info in self._registry.items():
                vn_name = (sp_info.get("primaryVietnameseName") or "").lower()
                can_name = (sp_info.get("canonicalName") or "").lower()
                
                # Khớp với tên tiếng Việt (ưu tiên tên dài hơn để tránh nhầm)
                if vn_name and len(vn_name) >= 3 and vn_name in q:
                    if len(vn_name) > max_len:
                        max_len = len(vn_name)
                        best_match = sp_info
                # Khớp với tên khoa học
                elif can_name and len(can_name) >= 4 and can_name in q:
                    if len(can_name) > max_len:
                        max_len = len(can_name)
                        best_match = sp_info

            target_species = best_match

        # 2. TRƯỜNG HỢP CÂU HỎI VỀ MỘT LOÀI CỤ THỂ
        if target_species:
            sp_name = target_species.get("primaryVietnameseName") or target_species.get("canonicalName")
            is_toxic = target_species.get("isToxic", False)
            grade = target_species.get("edibilityGrade")
            grade_desc = target_species.get("gradeDescription", "")
            recipes = target_species.get("recipes", [])
            contraindications = target_species.get("contraindications", [])
            properties = target_species.get("traditionalProperties", "")

            # A. Câu hỏi về ĐỘC TÍNH / ĂN ĐƯỢC KHÔNG
            if any(k in q for k in ["ăn được không", "uống được không", "có độc không", "an toàn không", "ăn sống", "độc hay không"]):
                if is_toxic:
                    answer_text = (
                        f"🚫 **CẢNH BÁO NGUY HIỂM:** Loài **{sp_name}** ({target_species.get('canonicalName')}) "
                        f"là loài thực vật CÓ ĐỘC TÍNH NGUY HIỂM.\n\n"
                        f"- **Nguy cơ:** {target_species.get('toxicAlertReason', 'Chứa hoạt chất kịch độc')}.\n"
                        f"- **Khuyến cáo:** TUYỆT ĐỐI KHÔNG ăn, không uống, không ngâm rượu hay sử dụng trong bất kỳ món ăn đồ uống nào!"
                    )
                elif grade == GRADE_MEDICINAL_ONLY:
                    answer_text = (
                        f"⚠️ **DƯỢC LIỆU CHUYÊN KHOA:** Loài **{sp_name}** ({target_species.get('canonicalName')}) "
                        f"theo Dược điển chủ yếu dùng làm thuốc điều trị bệnh chuyên biệt hoặc dùng ngoài da.\n\n"
                        f"- **Tình trạng ẩm thực:** {grade_desc}\n"
                        f"- **Khuyến cáo y khoa:** Không nên tự ý chế biến làm món ăn hàng ngày khi chưa có chỉ định liều lượng từ thầy thuốc YHCT."
                    )
                else:
                    parts = target_species.get("partsUsed") or "bộ phận phù hợp"
                    answer_text = (
                        f"✅ **AN TOÀN TRONG ẨM THỰC:** Loài **{sp_name}** là cây thực phẩm / thảo dược lành tính ({grade_desc}).\n\n"
                        f"- **Bộ phận thường dùng:** {parts}.\n"
                        f"- **Tính vị YHCT:** {properties or 'Tính bình, thanh mát'}.\n"
                        f"- **Số công thức dân gian chuẩn:** Hiện có {len(recipes)} bài thuốc ẩm thực được ghi nhận trong Dược điển và dân gian."
                    )
                return {
                    "success": True,
                    "species": target_species,
                    "questionType": "edibility_check",
                    "answer": answer_text,
                    "recipes": recipes,
                    "contraindications": contraindications
                }

            # B. Câu hỏi về MÓN ĂN / CÁCH LÀM / CHẾ BIẾN / PHA CHẾ
            if any(k in q for k in ["nấu món gì", "chế biến", "cách làm", "cách nấu", "pha trà", "công thức", "pha nước", "hấp", "làm gì"]):
                if is_toxic:
                    return {
                        "success": True,
                        "species": target_species,
                        "questionType": "toxic_block",
                        "answer": f"🚫 Loài **{sp_name}** là cây có độc tính nguy hiểm ({target_species.get('toxicAlertReason')}), tuyệt đối cấm nấu nướng hoặc chế biến ẩm thực!"
                    }
                if not recipes:
                    return {
                        "success": True,
                        "species": target_species,
                        "questionType": "no_recipe",
                        "answer": (
                            f"ℹ️ **Thông tin Dược điển:** Loài **{sp_name}** ({target_species.get('canonicalName')}) "
                            f"được xếp vào nhóm dược liệu điều trị chuyên khoa. Trong văn hóa ẩm thực dân gian Việt Nam "
                            f"CHƯA CÓ ghi nhận làm món ăn hoặc thức uống thường nhật. "
                            f"BioLens tuân thủ nguyên tắc y học chính xác: Không tự ý bịa đặt công thức nấu ăn cho các loài cây rừng hay thuốc chuyên khoa."
                        )
                    }
                # Có công thức chuẩn
                rec_titles = "\n".join([f"• **{r['title']}** ({r['category']}): {r['target_benefit']}" for r in recipes])
                answer_text = (
                    f"🍲 **CÁC MÓN ĂN - BÀI THUỐC TỪ {sp_name.upper()}:**\n\n"
                    f"{rec_titles}\n\n"
                    f"👉 *Bạn có thể bấm vào thẻ công thức bên dưới để xem chi tiết đầy đủ 5–7 bước sơ chế, định lượng gam, thời gian và nhiệt độ nấu chuẩn xác.*"
                )
                return {
                    "success": True,
                    "species": target_species,
                    "questionType": "recipes_list",
                    "answer": answer_text,
                    "recipes": recipes,
                    "contraindications": contraindications
                }

            # C. Câu hỏi về CẤM KỴ / KIÊNG ĂN GÌ / BÀ BẦU
            if any(k in q for k in ["kỵ", "kiêng", "bà bầu", "mang thai", "tránh", "không nên"]):
                incompat = target_species.get("contraindications", [])
                cautions_list = [r.get("cautions") for r in recipes if r.get("cautions")]
                lines = []
                if incompat:
                    lines.append("🚫 **Tương kỵ thực phẩm theo YHCT:**")
                    for inc in incompat:
                        lines.append(f"- {inc}")
                if cautions_list:
                    lines.append("\n⚠️ **Lưu ý an toàn sức khỏe:**")
                    for c in cautions_list:
                        lines.append(f"- {c}")
                if not lines:
                    lines.append(f"Loài **{sp_name}** chưa ghi nhận kiêng kỵ đặc biệt gay gắt, tuy nhiên nên dùng với lượng vừa phải thanh đạm.")

                return {
                    "success": True,
                    "species": target_species,
                    "questionType": "contraindications",
                    "answer": "\n".join(lines),
                    "recipes": recipes
                }

            # D. Câu hỏi chung về CÔNG DỤNG / TÍNH CHẤT
            answer_text = (
                f"🌿 **THÔNG TIN DƯỢC LIỆU: {sp_name.upper()}**\n\n"
                f"- **Tên khoa học:** *{target_species.get('canonicalName')}* ({target_species.get('family', '')})\n"
                f"- **Phân loại ẩm thực:** {grade_desc}\n"
                f"- **Tính vị quy kinh:** {properties or 'Đang cập nhật'}\n"
                f"- **Công dụng chính:** {', '.join(target_species.get('matchedHealthGoals', [])[:3])}\n"
            )
            if recipes:
                answer_text += f"\n- **Gợi ý món:** Có {len(recipes)} công thức dược thiện dân gian chi tiết kèm theo."
            return {
                "success": True,
                "species": target_species,
                "questionType": "general_info",
                "answer": answer_text,
                "recipes": recipes,
                "contraindications": contraindications
            }

        # 3. TRƯỜNG HỢP CÂU HỎI VỀ TRIỆU CHỨNG / NHU CẦU SỨC KHỎE (KHÔNG NÊU TÊN CÂY)
        symptom_results = self.search_by_symptom(q, top_k=4)
        if symptom_results:
            top_names = [f"**{item['primaryVietnameseName']}**" for item in symptom_results]
            all_recipes = []
            for item in symptom_results:
                all_recipes.extend(item.get("recipes", []))

            answer_text = (
                f"🌿 **GỢI Ý THẢO MỘC & DƯỢC THIỆN PHÙ HỢP:**\n\n"
                f"Dựa trên nhu cầu *'{question}'*, y học dân gian khuyến nghị sử dụng các loài thảo mộc như: {', '.join(top_names)}.\n\n"
                f"Các bài thuốc món ăn dưới đây đã được kiểm chứng về tính an toàn và hiệu quả theo Dược điển Việt Nam."
            )
            return {
                "success": True,
                "questionType": "symptom_search",
                "answer": answer_text,
                "recipes": all_recipes[:6],
                "matchedSpecies": symptom_results
            }

        # 4. KHÔNG TÌM THẤY THÔNG TIN PHÙ HỢP
        return {
            "success": False,
            "answer": (
                f"Xin lỗi, BioLens chưa tìm thấy thông tin phù hợp cho câu hỏi: *'{question}'*.\n\n"
                f"💡 **Mẹo:** Bạn có thể hỏi về tên một cây cụ thể (ví dụ: *'Chanh', 'Ngải cứu', 'Lá lốt', 'Hoa cúc', 'Đinh lăng'*), "
                f"hoặc hỏi theo nhu cầu sức khỏe (ví dụ: *'mất ngủ', 'thanh nhiệt mát gan', 'trị ho khan', 'giải rượu'*)."
            ),
            "suggestedQuestions": [
                "Cây chanh pha nước sôi 100°C có tốt không?",
                "Cây ngải cứu bà bầu ăn được không?",
                "Cây sâm bố chính nấu món gì bồi bổ?",
                "Người bị mất ngủ nên uống trà gì?"
            ]
        }
