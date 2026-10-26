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
    SPECIAL_POPULATION_WARNINGS,
)

OUTPUT_REGISTRY_PATH = STORAGE_DIR / "catalog" / "nutraceutical_registry.json"


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
    """Phan cap muc do an toan am thuc."""
    if is_toxic:
        return GRADE_TOXIC_FORBIDDEN, "Tuyệt đối không dùng trong ẩm thực hoặc đồ uống (Nguy cơ ngộ độc)."

    vn_name = (sp_data.get("primaryVietnameseName") or "").lower()
    sections = sp_data.get("profileSections", {})
    parts = (sections.get("partsUsed") or "").lower()
    medicinal = (sections.get("medicinalUses") or "").lower()
    overview = (sections.get("overview") or "").lower()
    combined = f"{vn_name} {parts} {medicinal} {overview}"

    # 1. Kiem tra nhom Gia vi & Tinh dau
    spice_kws = ["gia vị", "hương liệu", "quế", "hồi", "thảo quả", "gừng", "sả", "hành", "tỏi", "tiêu", "tía tô", "kinh giới", "mùi tàu", "húng quế"]
    for kw in spice_kws:
        if kw in combined:
            return GRADE_SPICE_AROMATIC, "Gia vị thảo mộc kích thích tiêu hóa, tạo hương thơm & làm ấm tỳ vị."

    # 2. Kiem tra nhom Canh, Chao, Ham bo duong (Culinary Tonic)
    culinary_kws = [
        "nấu canh", "hầm", "cháo", "nấu cháo", "xào", "luộc", "ăn sống", "làm rau", "rau rừng",
        "củ mài", "hoài sơn", "sâm bố chính", "đẳng sâm", "ý dĩ", "hạt sen", "ngải cứu",
        "lá lốt", "đương quy", "bổ dưỡng", "thực phẩm", "trái cây", "quả ăn được", "măng"
    ]
    for kw in culinary_kws:
        if kw in combined:
            return GRADE_CULINARY_TONIC, "Dược thực đồng nguyên (Medicine and Food Homology) — Thích hợp nấu canh, cháo, hầm tiềm bồi bổ."

    # 3. Kiem tra nhom Tra & Thuc uong duong sinh (Beverage Infusion)
    beverage_kws = [
        "uống thay trà", "hãm trà", "pha trà", "nước sắc", "thanh nhiệt", "giải khát", "hoa cúc",
        "lá sen", "lá vối", "đinh lăng", "bạc hà", "kim ngân hoa", "cỏ ngọt", "atiso",
        "chè vằng", "trà thảo mộc", "mát gan", "hạ sốt"
    ]
    for kw in beverage_kws:
        if kw in combined:
            return GRADE_BEVERAGE_INFUSION, "Thích hợp hãm trà thảo mộc, nước thanh lọc dưỡng sinh hàng ngày."

    # 4. Neu khong thuoc cac nhom tren: Thuoc tri benh chuyen biet
    return GRADE_MEDICINAL_ONLY, "Dược liệu chuyên dụng: Khuyến cáo dùng làm thuốc có kiểm soát liều lượng, không dùng làm ẩm thực đại trà."


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

    # Mac dinh neu it qua, gan muc phu hop
    if not matched_goals:
        matched_goals = ["bo_khi_duong_huyet", "thanh_nhiet_giai_doc"]

    return matched_goals


def generate_recipes_for_species(sp_data: Dict[str, Any], grade: str, matched_goals: List[str]) -> List[Dict[str, Any]]:
    """Sinh cong thuc mon an - thuc uong duong sinh cho loai."""
    if grade in (GRADE_TOXIC_FORBIDDEN, GRADE_MEDICINAL_ONLY):
        return []

    vn_name = sp_data.get("primaryVietnameseName") or sp_data.get("canonicalName")
    sections = sp_data.get("profileSections", {})
    parts_raw = sections.get("partsUsed") or "Lá hoặc thân"
    primary_goal_id = matched_goals[0] if matched_goals else "bo_khi_duong_huyet"
    goal_meta = HEALTH_GOALS.get(primary_goal_id, HEALTH_GOALS["bo_khi_duong_huyet"])

    recipes: List[Dict[str, Any]] = []

    # Cong thuc 1: Tra / Thuc uong duong sinh
    if grade in (GRADE_BEVERAGE_INFUSION, GRADE_CULINARY_TONIC, GRADE_SPICE_AROMATIC):
        recipes.append({
            "recipe_id": f"rec_tea_{sp_data.get('speciesKey')}",
            "title": f"Trà Thảo Mộc Dưỡng Sinh {vn_name}",
            "category": "Thức uống dưỡng sinh & Trà thảo dược",
            "preparation_time": "15 phút",
            "target_benefit": goal_meta["name"],
            "ingredients": [
                f"{vn_name} (Khô: 8–12g hoặc Tươi: 20–30g, rửa sạch ráo nước)",
                "Táo đỏ tân cương: 3 quả (cắt lát)",
                "Kỷ tử: 10 hạt",
                "Nước sôi: 500 – 700 ml (90°C – 95°C)"
            ],
            "step_by_step": [
                "Bước 1: Rửa sạch thảo dược bằng nước ấm để loại bỏ bụi phấn tự nhiên.",
                "Bước 2: Cho thảo mộc, táo đỏ và kỷ tử vào ấm trà gốm hoặc bình giữ nhiệt.",
                "Bước 3: Rót 200ml nước sôi lắc nhẹ để tráng trà rồi chắt bỏ nước đầu.",
                "Bước 4: Châm 500ml nước sôi còn lại, đậy nắp hãm trong 12–15 phút để hoạt chất khuếch tán.",
                "Bước 5: Thưởng thức từng ngụm ấm trong ngày (có thể thêm 1 thìa mật ong hoặc cỏ ngọt nếu thích vị ngọt thanh)."
            ],
            "optimal_timing": "Uống ấm sau bữa ăn sáng 30 phút hoặc đầu giờ chiều giúp tỉnh táo, thanh lọc tạng phủ.",
            "cautions": "Không uống trà quá đặc trước giờ ngủ đối với người nhạy cảm với vị chát."
        })

    # Cong thuc 2: Canh / Sup tiem bo duong
    if grade in (GRADE_CULINARY_TONIC, GRADE_SPICE_AROMATIC):
        food_partner = goal_meta["default_foods"][0] if goal_meta.get("default_foods") else "Gà ác hoặc Sườn heo"
        recipes.append({
            "recipe_id": f"rec_soup_{sp_data.get('speciesKey')}",
            "title": f"Canh Tiềm Dưỡng Khí {vn_name} Phối {food_partner}",
            "category": "Canh hầm & Súp tiềm bồi bổ",
            "preparation_time": "60–90 phút",
            "target_benefit": f"Bổ khí huyết, trợ lực tiêu hóa & {goal_meta['name'].lower()}",
            "ingredients": [
                f"{vn_name}: 20–30g (thân, lá hoặc củ sơ chế sạch)",
                f"{food_partner}: 300–400g (chặt miếng vừa ăn, chần qua nước sôi gừng)",
                "Hạt sen tươi (hoặc khô ngâm mềm): 30g",
                "Gừng tươi: 3 lát mỏng",
                "Gia vị: 1 chút muối hồng hoặc nước mắm truyền thống thanh đạm"
            ],
            "step_by_step": [
                f"Bước 1: Sơ chế {food_partner} chần qua nước sôi pha rượu gừng để khử mùi tanh, vớt ra xả nước lạnh.",
                f"Bước 2: Thảo dược {vn_name} ngâm nước muối loãng 10 phút, vớt ra để ráo.",
                "Bước 3: Cho nguyên liệu vào thố sứ hoặc nồi đất, đổ ngập nước (khoảng 800ml - 1 lít).",
                "Bước 4: Đun sôi bùng, vớt bọt sạch rồi hạ lửa thật nhỏ (hoặc tiềm cách thủy) trong 60 phút đến khi thịt mềm rục.",
                "Bước 5: Nêm chút muối nhạt vừa miệng, thêm vài cọng hành hoa hoặc ngò rí rồi tắt bếp."
            ],
            "optimal_timing": "Dùng nóng trong bữa ăn chính, thích hợp bồi dưỡng cuối tuần cho người mệt mỏi.",
            "cautions": "Nên ăn nhạt để thận không phải làm việc quá tải và dược chất hấp thu tốt nhất."
        })

    # Cong thuc 3: Chao duong sinh
    if grade in (GRADE_CULINARY_TONIC,):
        recipes.append({
            "recipe_id": f"rec_congee_{sp_data.get('speciesKey')}",
            "title": f"Cháo Dưỡng Sinh {vn_name} & Hạt Sen Ý Dĩ",
            "category": "Cháo dưỡng sinh dễ hấp thu",
            "preparation_time": "45 phút",
            "target_benefit": "Kiện tỳ dưỡng vị, êm dịu đường tiêu hóa, an giấc",
            "ingredients": [
                f"{vn_name} (nước cốt sắc hoặc băm nhuyễn): 15–20g",
                "Gạo tẻ thơm trộn gạo nếp: 80g",
                "Hạt sen hoặc Ý dĩ: 25g",
                "Nước hầm xương hoặc nước luộc rau củ: 1 lít"
            ],
            "step_by_step": [
                "Bước 1: Vo sạch gạo và ý dĩ/hạt sen, ngâm nước ấm 20 phút cho nở hạt.",
                "Bước 2: Sắc thảo dược lấy 200ml nước cốt đặc (hoặc băm nhỏ lá nếu ăn được bã).",
                "Bước 3: Ninh gạo cùng nước dùng đến khi cháo chín nhừ, nở bung hoa.",
                "Bước 4: Đổ nước cốt thảo dược vào khuấy đều tay trên lửa nhỏ thêm 10 phút.",
                "Bước 5: Múc ra bát, rắc chút tiêu cay nhẹ, ăn lúc cháo còn bốc khói ấm."
            ],
            "optimal_timing": "Ăn vào bữa sáng hoặc bữa xế chiều khi bụng đói nhẹ.",
            "cautions": "Người tiểu đường nên ăn cháo nguyên hạt, không hầm quá nhuyễn."
        })

    return recipes


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
