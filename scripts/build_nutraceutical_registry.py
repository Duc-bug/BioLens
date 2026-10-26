from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Thêm đường dẫn project
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.settings import SPECIES_KNOWLEDGE_PATH, STORAGE_DIR
from dataset.nutraceutical_rules import (
    GRADE_TOXIC_FORBIDDEN,
    GRADE_MEDICINAL_ONLY,
    GRADE_BEVERAGE_INFUSION,
    GRADE_CULINARY_TONIC,
    GRADE_SPICE_AROMATIC,
    KNOWN_TOXIC_GENERA,
    KNOWN_TOXIC_FAMILIES,
    TOXIC_KEYWORDS,
    HEALTH_GOALS,
    HERB_FOOD_INCOMPATIBILITIES,
    AUTHENTIC_FOLK_RECIPES,
)

OUTPUT_REGISTRY_PATH = STORAGE_DIR / "catalog" / "nutraceutical_registry.json"


def find_authentic_folk_recipe(sp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Tìm kiếm công thức dân gian chuẩn xác từ AUTHENTIC_FOLK_RECIPES."""
    vn_name = (sp_data.get("primaryVietnameseName") or "").lower()
    canonical = (sp_data.get("canonicalName") or "").lower()
    scientific = (sp_data.get("scientificName") or "").lower()
    combined_name = f"{vn_name} {canonical} {scientific}"

    for key, item in AUTHENTIC_FOLK_RECIPES.items():
        for kw in item["keywords"]:
            # Khớp từ khóa độc lập hoặc có ranh giới từ để tránh khớp nhầm
            pattern = rf"(^|\s|/|\()({re.escape(kw)})(\s|$|/|\))"
            if re.search(pattern, combined_name):
                return item["recipes"]
            # Hoặc kw nằm trong vn_name nếu kw dài hơn 4 ký tự
            if len(kw) >= 4 and kw in vn_name:
                return item["recipes"]
    return []


def check_is_toxic(species_key: str, sp_data: Dict[str, Any]) -> tuple[bool, str]:
    """Kiem tra xem loai co nam trong danh muc doc hai/nguy hiem hay khong."""
    canonical = (sp_data.get("canonicalName") or "").lower()
    vn_name = (sp_data.get("primaryVietnameseName") or "").lower()
    taxonomy = sp_data.get("taxonomy", {})
    genus = (taxonomy.get("genus") or "").lower()
    family = (taxonomy.get("family") or "").lower()
    sections = sp_data.get("profileSections", {})
    safety = (sections.get("safetyWarning") or "").lower()
    medicinal = (sections.get("medicinalUses") or "").lower()
    overview = (sections.get("overview") or "").lower()

    # 1. Kiem tra theo Chi doc hai
    if genus in KNOWN_TOXIC_GENERA:
        return True, f"Thuộc Chi thực vật có độc tính kịch độc ({genus.capitalize()})."

    # 2. Kiem tra theo Ho doc hai (apocynaceae co nhieu cay doc)
    if family == "apocynaceae":
        # Check cac loai dac biet doc nhu truc dao, sung de
        for kw in ["nerium", "cerbera", "strophanthus", "thevetia", "chữa ngộ độc", "độc"]:
            if kw in canonical or kw in safety or kw in vn_name:
                return True, "Thuộc Họ Trúc đào (Apocynaceae) chứa glycoside tim có nguy cơ ngộ độc cao."

    # 3. Kiem tra tu khoa doc tinh trong safetyWarning va medicinalUses
    combined_text = f"{safety} {medicinal} {overview} {vn_name}"
    for kw in TOXIC_KEYWORDS:
        if kw in combined_text:
            return True, f"Cảnh báo trong tài liệu chuyên khảo: Phát hiện đặc tính '{kw}'."

    # 4. Kiem tra ten goi dac thu cay doc
    toxic_names = ["lá ngón", "trúc đào", "mã tiền", "cà độc dược", "cây sui", "ba đậu", "mướp sát", "củ dòm", "nấm độc"]
    for tn in toxic_names:
        if tn in vn_name:
            return True, f"Loài cây thuộc nhóm nguy hiểm có tiền sử gây ngộ độc ({vn_name.capitalize()})."

    return False, ""


def determine_edibility_grade(sp_data: Dict[str, Any], is_toxic: bool) -> tuple[str, str]:
    """Phan cap muc do an toan am thuc theo su that khoa hoc va ghi chep duoc dien."""
    if is_toxic:
        return GRADE_TOXIC_FORBIDDEN, "Tuyệt đối không dùng trong ẩm thực hoặc đồ uống (Nguy cơ ngộ độc)."

    # 1. Nếu có công thức dân gian chuẩn xác trong AUTHENTIC_FOLK_RECIPES
    authentic = find_authentic_folk_recipe(sp_data)
    if authentic:
        # Nếu có món canh/cháo -> CULINARY_TONIC, nếu chỉ có trà/nước ép -> BEVERAGE_INFUSION
        has_food = any("canh" in r["title"].lower() or "cháo" in r["title"].lower() or "tiềm" in r["title"].lower() or "chả" in r["title"].lower() or "trứng" in r["title"].lower() for r in authentic)
        if has_food:
            return GRADE_CULINARY_TONIC, "Dược thực đồng nguyên (Medicine and Food Homology) — Thích hợp chế biến món ăn dưỡng sinh bồi bổ."
        return GRADE_BEVERAGE_INFUSION, "Thức uống dưỡng sinh & Trà thảo dược dân gian truyền thống."

    vn_name = (sp_data.get("primaryVietnameseName") or "").lower()
    sections = sp_data.get("profileSections", {})
    parts = (sections.get("partsUsed") or "").lower()
    medicinal = (sections.get("medicinalUses") or "").lower()
    overview = (sections.get("overview") or "").lower()
    combined = f"{vn_name} {parts} {medicinal} {overview}"

    # 2. Kiểm tra nhóm Rau ăn, Canh quen thuộc có ghi nhận thực tế
    common_vegetables = [
        "rau muống", "rau dền", "rau ngót", "mồng tơi", "rau lang", "rau đay", "cải cúc",
        "bầu", "bí xanh", "bí đỏ", "mướp hương", "mướp đắng", "khổ qua", "rau má", "rau tàu bay",
        "củ mài", "hoài sơn", "hạt sen", "ngải cứu", "lá lốt", "măng tây", "chuối hột"
    ]
    for veg in common_vegetables:
        if veg in vn_name:
            return GRADE_CULINARY_TONIC, "Dược thực đồng nguyên — Cây thực phẩm dân dã kết hợp dược tính bồi bổ sức khỏe."

    # 3. Kiểm tra nhóm Gia vị & Tinh dầu quen thuộc
    common_spices = ["hành", "tỏi", "tiêu", "sả", "quế", "hồi", "thảo quả", "tía tô", "kinh giới", "mùi tàu", "húng quế", "húng chanh"]
    for sp in common_spices:
        pattern = rf"(^|\s)({re.escape(sp)})(\s|$)"
        if re.search(pattern, vn_name):
            return GRADE_SPICE_AROMATIC, "Gia vị thảo mộc kích thích tiêu hóa, khử tanh & làm ấm tỳ vị."

    # 4. Kiểm tra nhóm Trà thảo dược dân gian thực thụ
    common_teas = ["chè xanh", "trà xanh", "lá vối", "nụ vối", "atiso", "cúc hoa", "hoa cúc", "tâm sen", "chè vằng", "chè dây", "kim ngân hoa", "cỏ ngọt", "cà gai leo"]
    for ct in common_teas:
        if ct in vn_name:
            return GRADE_BEVERAGE_INFUSION, "Thích hợp hãm trà thảo mộc, nước thanh nhiệt dưỡng sinh giải độc."

    # 5. Các loài còn lại trong 3,570 loài: Là dược liệu cây rừng/thuốc chữa bệnh chuyên biệt
    return GRADE_MEDICINAL_ONLY, "Dược liệu chuyên khoa: Chỉ dùng làm thuốc sắc uống hoặc dùng ngoài theo chỉ định y học cổ truyền. Trong đời sống ẩm thực dân tộc chưa có ghi chép làm món ăn/thức uống thường ngày."


def map_health_goals(sp_data: Dict[str, Any]) -> List[str]:
    """Anh xa loai cay voi 12 the trang suc khoe."""
    sections = sp_data.get("profileSections", {})
    medicinal = (sections.get("medicinalUses") or "").lower()
    props = (sections.get("traditionalProperties") or "").lower()
    overview = (sections.get("overview") or "").lower()
    text = f"{medicinal} {props} {overview}"

    matched_goals: List[str] = []
    for goal_id, goal_info in HEALTH_GOALS.items():
        score = 0
        for kw in goal_info["keywords"]:
            if kw in text:
                score += 1
        if score >= 1:
            matched_goals.append(goal_id)

    if not matched_goals:
        matched_goals = ["bo_khi_duong_huyet", "thanh_nhiet_giai_doc"]

    return matched_goals


def generate_recipes_for_species(sp_data: Dict[str, Any], grade: str, matched_goals: List[str]) -> List[Dict[str, Any]]:
    """Trích xuất công thức dược thiện dân gian chuẩn xác (5–7 bước).
    Tuyệt đối không bịa đặt template rập khuôn cho các loài cây rừng hoặc dược liệu chuyên khoa.
    """
    if grade in (GRADE_TOXIC_FORBIDDEN, GRADE_MEDICINAL_ONLY):
        return []

    # Ưu tiên 1: Lấy trực tiếp từ cơ sở tri thức công thức chuẩn AUTHENTIC_FOLK_RECIPES
    authentic = find_authentic_folk_recipe(sp_data)
    if authentic:
        return authentic

    # Nếu không nằm trong danh mục đã được kiểm chứng ẩm thực:
    # Trả về rỗng để tránh sai sự thật y khoa.
    return []



def build_full_nutraceutical_registry():
    """Hàm chính quét toàn bộ 3,570 loài và xuất JSON registry."""
    print("🌿 Đang đọc cơ sở tri thức 3,570 loài từ:", SPECIES_KNOWLEDGE_PATH)
    if not SPECIES_KNOWLEDGE_PATH.exists():
        print(f"❌ Không tìm thấy file {SPECIES_KNOWLEDGE_PATH}!")
        return

    with open(SPECIES_KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        species_knowledge: Dict[str, Any] = json.load(f)

    total_species = len(species_knowledge)
    print(f"📌 Đã tải thành công {total_species} loài.")

    registry: Dict[str, Any] = {}
    stats = {
        GRADE_TOXIC_FORBIDDEN: 0,
        GRADE_MEDICINAL_ONLY: 0,
        GRADE_BEVERAGE_INFUSION: 0,
        GRADE_CULINARY_TONIC: 0,
        GRADE_SPICE_AROMATIC: 0,
    }

    for sp_key, sp_data in species_knowledge.items():
        is_toxic, toxic_reason = check_is_toxic(sp_key, sp_data)
        grade, grade_desc = determine_edibility_grade(sp_data, is_toxic)
        stats[grade] += 1

        matched_goals = map_health_goals(sp_data)
        recipes = generate_recipes_for_species(sp_data, grade, matched_goals)

        # Trích xuất cấm kỵ tương tác thực phẩm
        contraindications: List[str] = []
        vn_name = (sp_data.get("primaryVietnameseName") or "").lower()
        for rule in HERB_FOOD_INCOMPATIBILITIES:
            if re.search(rule["herb_pattern"], vn_name):
                for ff in rule["forbidden_foods"]:
                    contraindications.append(f"Kỵ {ff}: {rule['reason']}")

        registry[sp_key] = {
            "speciesKey": sp_key,
            "primaryVietnameseName": sp_data.get("primaryVietnameseName", ""),
            "canonicalName": sp_data.get("canonicalName", ""),
            "scientificName": sp_data.get("scientificName", ""),
            "family": sp_data.get("taxonomy", {}).get("family", ""),
            "genus": sp_data.get("taxonomy", {}).get("genus", ""),
            "edibilityGrade": grade,
            "gradeDescription": grade_desc,
            "isToxic": is_toxic,
            "toxicAlertReason": toxic_reason if is_toxic else None,
            "matchedHealthGoals": matched_goals,
            "recipesCount": len(recipes),
            "recipes": recipes,
            "contraindications": contraindications,
            "traditionalProperties": sp_data.get("profileSections", {}).get("traditionalProperties", ""),
            "partsUsed": sp_data.get("profileSections", {}).get("partsUsed", ""),
        }

    OUTPUT_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    print("\n" + "="*60)
    print("🎉 HOÀN THÀNH XÂY DỰNG NUTRACEUTICAL REGISTRY!")
    print(f"📂 Đã lưu tại: {OUTPUT_REGISTRY_PATH}")
    print(f"📊 Thống kê toàn diện trên {total_species} loài:")
    print(f"  - 🚫 {GRADE_TOXIC_FORBIDDEN} (Cực độc / Cấm ăn uống): {stats[GRADE_TOXIC_FORBIDDEN]} loài")
    print(f"  - 💊 {GRADE_MEDICINAL_ONLY} (Dược liệu chuyên khoa): {stats[GRADE_MEDICINAL_ONLY]} loài")
    print(f"  - 🍵 {GRADE_BEVERAGE_INFUSION} (Trà & Thức uống giải nhiệt): {stats[GRADE_BEVERAGE_INFUSION]} loài")
    print(f"  - 🍲 {GRADE_CULINARY_TONIC} (Dược thực đồng nguyên - Canh/Cháo/Tiềm): {stats[GRADE_CULINARY_TONIC]} loài")
    print(f"  - 🌿 {GRADE_SPICE_AROMATIC} (Gia vị & Hương liệu): {stats[GRADE_SPICE_AROMATIC]} loài")
    total_safe = stats[GRADE_BEVERAGE_INFUSION] + stats[GRADE_CULINARY_TONIC] + stats[GRADE_SPICE_AROMATIC]
    print(f"  ✨ Tổng số loài có công thức Dược thiện ứng dụng trực tiếp: {total_safe} loài.")
    print("="*60 + "\n")


if __name__ == "__main__":
    build_full_nutraceutical_registry()
