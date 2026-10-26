"""
Tu dien Quy tac & Danh muc Tri thuc Duoc thien (Medicine and Food Homology - MFH)
Phuc vu cho Engine Goi y Mon an - Thuc uong Bo duong (BioLens Nutraceutical Recommender).
Bao phu toan bo 3,570 loai thuc vat duoc lieu VietMediSpecies2026.
"""
from __future__ import annotations

from typing import Dict, List, Any, Set


# ==============================================================================
# 1. PHÂN CẤP AN TOÀN ẨM THỰC (EDIBILITY & SAFETY GRADES)
# ==============================================================================
GRADE_TOXIC_FORBIDDEN = "TOXIC_FORBIDDEN"       # Cực độc hoặc độc hại: CẤM 100% trong ẩm thực
GRADE_MEDICINAL_ONLY = "MEDICINAL_ONLY"         # Thuốc trị bệnh chuyên khoa: Không dùng làm ẩm thực đại trà
GRADE_BEVERAGE_INFUSION = "BEVERAGE_INFUSION"   # Trà thảo mộc / Nước giải nhiệt dưỡng sinh
GRADE_CULINARY_TONIC = "CULINARY_TONIC"         # Dược thực đồng nguyên: Nấu canh, cháo, hầm, tiềm bổ dưỡng
GRADE_SPICE_AROMATIC = "SPICE_AROMATIC"         # Gia vị thảo mộc & Hương liệu kích thích tiêu hóa


# ==============================================================================
# 2. BỘ LỌC ĐỘC TÍNH NGHIÊM NGẶT (STRICT TOXICITY FILTER)
# ==============================================================================
# Danh sách Chi và Họ có độc tính cao hoặc chứa ancaloit kịch độc
KNOWN_TOXIC_GENERA: Set[str] = {
    "gelsemium",      # Lá ngón (Gelsemium elegans)
    "nerium",         # Trúc đào (Nerium oleander)
    "datura",         # Cà độc dược (Datura metel)
    "strychnos",      # Mã tiền (Strychnos nux-vomica)
    "aconitum",       # Ô đầu, Phụ tử (Aconitum)
    "cerbera",        # Mướp sát (Cerbera odollam)
    "antiaris",       # Cây sui (Antiaris toxicaria)
    "abrus",          # Cam thảo dây / Cườm thảo (Abrus precatorius - hạt kịch độc)
    "ricinus",        # Thầu dầu (Ricinus communis - hạt chứa ricin)
    "croton",         # Ba đậu (Croton tiglium)
    "digitalis",      # Dương địa hoàng (Digitalis purpurea)
    "atropa",         # Cà dược Atropa
    "dieffenbachia",  # Vạn niên thanh (chứa canxi oxalat độc)
    "calotropis",     # Bồng bồng (nhựa độc)
    "euphorbia",      # Chi Đại kích / Xương rồng bát tiên (nhựa độc nguy hiểm)
    "amanita",        # Chi nấm tán độc Amanita
}

KNOWN_TOXIC_FAMILIES: Set[str] = {
    "apocynaceae",    # Họ Trúc đào (nhiều loài chứa glycoside tim kịch độc)
    "solanaceae",     # Một số chi chứa tropane alkaloid độc
}

# Các từ khóa cảnh báo trong phần safetyWarning hoặc medicinalUses
TOXIC_KEYWORDS: List[str] = [
    "cực độc", "kịch độc", "chết người", "tử vong", "ngộ độc",
    "độc tính cao", "độc bảng a", "không được uống", "không được ăn",
    "độc tính mạnh", "nguy hiểm tính mạng", "chứa alkaloid độc",
    "chứa glycoside tim độc", "co giật", "liệt hô hấp", "ngưng tim",
    "gây sảy thai", "chứa ricin", "chứa strychnin", "chứa aconitin"
]


# ==============================================================================
# 3. DANH BẠ 12 THỂ TRẠNG SỨC KHỎE & NHU CẦU DƯỠNG SINH (HEALTH GOALS)
# ==============================================================================
HEALTH_GOALS: Dict[str, Dict[str, Any]] = {
    "an_than_ngu_ngon": {
        "id": "an_than_ngu_ngon",
        "name": "Dưỡng Tâm An Thần, Trị Mất Ngủ & Giảm Stress",
        "keywords": ["mất ngủ", "khó ngủ", "stress", "hồi hộp", "lo âu", "an thần", "dưỡng tâm", "suy nhược thần kinh", "hay quên", "mộng mị"],
        "tcm_property": "Bình hòa hoặc Lương; quy kinh Tâm, Can",
        "suitable_types": [GRADE_BEVERAGE_INFUSION, GRADE_CULINARY_TONIC],
        "default_foods": ["Hạt sen", "Táo đỏ", "Long nhãn", "Gạo lứt", "Tim heo", "Thịt chim bồ câu"]
    },
    "thanh_nhiet_giai_doc": {
        "id": "thanh_nhiet_giai_doc",
        "name": "Thanh Nhiệt Giải Độc, Mát Gan & Trị Mụn Nhọt",
        "keywords": ["nóng trong", "nhiệt miệng", "mụn nhọt", "mát gan", "thanh nhiệt", "giải độc", "táo bón", "tiểu vàng", "khô khát", "bốc hỏa"],
        "tcm_property": "Tính Hàn hoặc Lương; quy kinh Can, Vị, Đại tràng",
        "suitable_types": [GRADE_BEVERAGE_INFUSION, GRADE_CULINARY_TONIC],
        "default_foods": ["Đậu xanh", "Đậu đen", "Bột sắn dây", "Mướp đắng", "Bí đao", "Thịt vịt"]
    },
    "kien_ty_tieu_hoa": {
        "id": "kien_ty_tieu_hoa",
        "name": "Kiện Tỳ Ích Vị, Hỗ Trợ Tiêu Hóa & Đầy Bụng",
        "keywords": ["đầy bụng", "chóe bụng", "tiêu hóa kém", "chậm tiêu", "ăn không ngon", "kiện tỳ", "ích vị", "viêm dạ dày", "tiêu chảy nhẹ", "tỳ vị hư hàn"],
        "tcm_property": "Tính Ôn hoặc Bình; quy kinh Tỳ, Vị",
        "suitable_types": [GRADE_CULINARY_TONIC, GRADE_SPICE_AROMATIC, GRADE_BEVERAGE_INFUSION],
        "default_foods": ["Củ mài (Hoài sơn)", "Ý dĩ", "Gừng tươi", "Gạo nếp", "Thịt gà", "Dạ dày heo"]
    },
    "bo_khi_duong_huyet": {
        "id": "bo_khi_duong_huyet",
        "name": "Bổ Khí Dưỡng Huyết, Phục Hồi Thể Lực & Sau Ốm",
        "keywords": ["suy nhược", "mệt mỏi", "thiếu máu", "hụt hơi", "hoa mắt", "chóng mặt", "sau sinh", "sau ốm dậy", "bổ khí", "dưỡng huyết", "sức đề kháng"],
        "tcm_property": "Tính Ôn hoặc Bình; quy kinh Tỳ, Phế, Thận",
        "suitable_types": [GRADE_CULINARY_TONIC, GRADE_BEVERAGE_INFUSION],
        "default_foods": ["Gà ác", "Chim bồ câu", "Sườn heo", "Táo đỏ", "Kỷ tử", "Đẳng sâm", "Thịt bò"]
    },
    "khu_phong_xuong_khop": {
        "id": "khu_phong_xuong_khop",
        "name": "Khu Phong Tán Hàn, Mạnh Gân Cốt & Đau Nhức",
        "keywords": ["đau lưng", "mỏi gối", "tê bì chân tay", "đau nhức xương khớp", "phong thấp", "gân cốt", "lạnh buốt", "thoát vị"],
        "tcm_property": "Tính Ôn; quy kinh Can, Thận",
        "suitable_types": [GRADE_CULINARY_TONIC, GRADE_SPICE_AROMATIC],
        "default_foods": ["Móng giò heo", "Đuôi bò", "Rượu nếp cẩm", "Gừng già", "Lá lốt", "Đậu đen"]
    },
    "nhuan_phe_tri_ho": {
        "id": "nhuan_phe_tri_ho",
        "name": "Nhuận Phế Chỉ Khái, Trị Ho Khan & Bổ Phổi",
        "keywords": ["ho khan", "rát họng", "viêm họng", "khản tiếng", "bổ phổi", "nhuận phế", "đờm đặc", "ho gió", "họng hạt"],
        "tcm_property": "Tính Bình hoặc Lương; quy kinh Phế",
        "suitable_types": [GRADE_BEVERAGE_INFUSION, GRADE_CULINARY_TONIC],
        "default_foods": ["Quả lê", "Bách hợp", "Mật ong rừng", "Đường phèn", "Mộc nhĩ trắng (Ngân nhĩ)"]
    },
    "ha_ap_tim_mach": {
        "id": "ha_ap_tim_mach",
        "name": "Hạ Mỡ Máu, Ổn Định Huyết Áp & Tim Mạch",
        "keywords": ["cao huyết áp", "mỡ máu", "cholesterol", "xơ vữa", "bảo vệ tim", "tuần hoàn não", "hạ áp"],
        "tcm_property": "Tính Bình hoặc Lương; quy kinh Can, Tâm",
        "suitable_types": [GRADE_BEVERAGE_INFUSION, GRADE_CULINARY_TONIC],
        "default_foods": ["Mộc nhĩ đen", "Cần tây", "Nấm hương", "Đậu nành", "Cá hồi", "Trà xanh"]
    },
    "ich_than_bo_tinh": {
        "id": "ich_than_bo_tinh",
        "name": "Bổ Thận Tráng Dương, Cường Kiện Sinh Lực",
        "keywords": ["bổ thận", "tráng dương", "sinh lý", "tiểu đêm", "mỏi lưng", "tăng sinh lực", "di tinh", "thận âm", "thận dương"],
        "tcm_property": "Tính Ôn; quy kinh Thận, Can",
        "suitable_types": [GRADE_CULINARY_TONIC, GRADE_BEVERAGE_INFUSION],
        "default_foods": ["Đuôi heo", "Tôm đồng", "Thịt dê", "Kỷ tử", "Hạt óc chó", "Hẹ xanh"]
    },
    "duong_nhan_chong_lao_hoa": {
        "id": "duong_nhan_chong_lao_hoa",
        "name": "Dưỡng Nhan Sáng Da, Chống Lão Hóa & Tươi Trẻ",
        "keywords": ["dưỡng nhan", "đẹp da", "sáng da", "chống lão hóa", "tàn nhang", "chống oxy hóa", "mịn da", "thanh xuân"],
        "tcm_property": "Tính Bình; quy kinh Can, Tỳ, Thận",
        "suitable_types": [GRADE_BEVERAGE_INFUSION, GRADE_CULINARY_TONIC],
        "default_foods": ["Táo đỏ", "Kỷ tử", "Hạt sen", "Yến sào", "Tuyết yến", "Nhựa đào", "Đậu đỏ"]
    },
    "giai_ruou_giai_doc_gan": {
        "id": "giai_ruou_giai_doc_gan",
        "name": "Giải Bia Rượu, Phục Hồi & Bảo Vệ Tế Bào Gan",
        "keywords": ["giải rượu", "say rượu", "độc gan", "men gan cao", "bảo vệ gan", "hạ men gan", "nôn nao"],
        "tcm_property": "Tính Mát; quy kinh Can, Vị",
        "suitable_types": [GRADE_BEVERAGE_INFUSION],
        "default_foods": ["Bột sắn dây", "Nước gừng mật ong", "Đậu xanh", "Cà rốt", "Nước mía"]
    },
    "giam_beo_thanh_loc": {
        "id": "giam_beo_thanh_loc",
        "name": "Giảm Mỡ Thừa, Tiêu Mỡ Bụng & Detox Cơ Thể",
        "keywords": ["giảm cân", "giảm béo", "giảm mỡ bụng", "detox", "tiêu mỡ", "thanh lọc", "nhẹ người"],
        "tcm_property": "Tính Bình hoặc Lương; quy kinh Tỳ, Vị",
        "suitable_types": [GRADE_BEVERAGE_INFUSION, GRADE_CULINARY_TONIC],
        "default_foods": ["Bí đao", "Cần tây", "Gạo lứt", "Đậu đen xanh lòng", "Bưởi"]
    },
    "loi_tieu_tieu_phu": {
        "id": "loi_tieu_tieu_phu",
        "name": "Lợi Tiểu Tiêu Phù, Thông Lâm Bài Thạch",
        "keywords": ["lợi tiểu", "tiểu buốt", "tiểu rắt", "tiêu phù", "sỏi thận", "sỏi tiết niệu", "viêm đường tiết niệu"],
        "tcm_property": "Tính Hàn hoặc Lương; quy kinh Bàng quang, Thận",
        "suitable_types": [GRADE_BEVERAGE_INFUSION],
        "default_foods": ["Râu ngô", "Bí xanh", "Đậu đỏ", "Ý dĩ"]
    }
}


# ==============================================================================
# 4. MA TRẬN CẤM KỴ TƯƠNG TÁC THỰC PHẨM - THẢO DƯỢC (CONTRAINDICATIONS)
# ==============================================================================
HERB_FOOD_INCOMPATIBILITIES: List[Dict[str, Any]] = [
    {
        "herb_pattern": "nhân sâm|đẳng sâm|bố chính sâm|sâm",
        "forbidden_foods": ["củ cải trắng", "củ cải đỏ", "trà đặc", "nước chè xanh đậm", "hải sản tanh"],
        "reason": "Củ cải và chè đặc có tính phá khí, triệt tiêu hoàn toàn công năng đại bổ nguyên khí của các loại sâm."
    },
    {
        "herb_pattern": "hà thủ ô",
        "forbidden_foods": ["hành củ", "tỏi", "tiêu đen", "ớt", "cải củ", "tiết động vật"],
        "reason": "Các gia vị cay nóng và tiết động vật làm hao tổn tinh huyết, giảm tác dụng bổ can thận, đen tóc của Hà thủ ô."
    },
    {
        "herb_pattern": "ba kích",
        "forbidden_foods": ["thịt gà", "rau muống"],
        "reason": "Thịt gà kỵ với dược tính ôn thận tráng dương của Ba kích theo kinh nghiệm ẩm thực phương Đông."
    },
    {
        "herb_pattern": "hoàng liên|hoàng bá|hoàng cầm",
        "forbidden_foods": ["thịt lợn", "đồ ăn cay nóng"],
        "reason": "Hoàng liên có tính đại hàn, kỵ với thịt lợn gây trệ khí, giảm hiệu quả thanh nhiệt táo thấp."
    },
    {
        "herb_pattern": "cam thảo",
        "forbidden_foods": ["cá chép", "thịt lợn mỡ"],
        "reason": "Cam thảo dùng lượng nhiều kết hợp cá chép dễ gây tích nước, tăng huyết áp."
    },
    {
        "herb_pattern": "kinh giới",
        "forbidden_foods": ["thịt cua", "thịt cá lóc", "thịt gà"],
        "reason": "Kinh giới kỵ thịt gà và cua đồng, dễ gây dị ứng hoặc đầy bụng khó tiêu."
    },
    {
        "herb_pattern": "bạc hà",
        "forbidden_foods": ["mai rùa", "thịt ba ba"],
        "reason": "Bạc hà tính tân lương sơ tán phong nhiệt, kỵ với tính bổ âm nê trệ của ba ba."
    }
]

# Chống chỉ định theo nhóm đối tượng nhạy cảm
SPECIAL_POPULATION_WARNINGS: Dict[str, Dict[str, Any]] = {
    "pregnancy": {
        "label": "Phụ nữ mang thai",
        "forbidden_terms": ["phá huyết", "hoạt huyết mạnh", "trục ứ", "sảy thai", "thông kinh", "co bóp tử cung"],
        "warning": "CẢNH BÁO: Thảo mộc có tính hoạt huyết hoặc thông kinh mạnh, tuyệt đối không dùng cho phụ nữ có thai."
    },
    "hypertension": {
        "label": "Người cao huyết áp",
        "forbidden_terms": ["tăng huyết áp", "cam thảo liều cao", "đại nhiệt"],
        "warning": "LƯU Ý: Người huyết áp cao không nên dùng liều lượng lớn hoặc kéo dài, tránh gây tăng áp lực mạch máu."
    },
    "cold_constitution": {
        "label": "Người thể trạng Tỳ Vị Hư Hàn (sợ lạnh, hay đau bụng tiêu chảy)",
        "forbidden_terms": ["đại hàn", "tính hàn mạnh", "thanh nhiệt tống tả"],
        "warning": "LƯU Ý: Thảo dược tính hàn cần phối hợp thêm vài lát gừng tươi hoặc vỏ quýt (trần bì) để làm ấm tỳ vị."
    }
}
