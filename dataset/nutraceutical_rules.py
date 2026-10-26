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

# ==============================================================================
# 5. CẢNH BÁO CHO CÁC NHÓM ĐỐI TƯỢNG ĐẶC BIỆT (SPECIAL POPULATIONS)
# ==============================================================================
SPECIAL_POPULATION_WARNINGS: Dict[str, Dict[str, Any]] = {
    "pregnant": {
        "label": "Phụ nữ mang thai",
        "forbidden_terms": ["phá huyết", "hành huyết", "hoạt huyết mạnh", "trục thai", "co bóp tử cung", "độc", "hàn lạnh"],
        "warning": "Lưu ý quan trọng: Phụ nữ mang thai tuyệt đối tránh các thảo dược có tính hoạt huyết phá ứ hoặc kích thích co bóp tử cung."
    },
    "breastfeeding": {
        "label": "Phụ nữ đang cho con bú",
        "forbidden_terms": ["mất sữa", "tiêu sữa", "đắng", "độc"],
        "warning": "Phụ nữ cho con bú nên chọn thảo dược lợi sữa (như chè vằng sao thơm, đinh lăng), tránh các loại làm giảm tiết sữa."
    },
    "gastritis": {
        "label": "Người đau dạ dày / Viêm loét",
        "forbidden_terms": ["chua", "cay nóng", "kích thích dạ dày", "tiêu viêm mạnh"],
        "warning": "Người bị đau dạ dày nên tránh các thảo mộc quá chua hoặc cay nồng lúc đói."
    },
    "hypertension": {
        "label": "Người cao huyết áp",
        "forbidden_terms": ["tăng huyết áp", "cam thảo liều cao", "cay nóng"],
        "warning": "Người tăng huyết áp nên ưu tiên thảo dược hạ áp làm bền thành mạch (như hoa hòe, tâm sen, râu ngô)."
    },
    "cold_constitution": {
        "label": "Người thể hàn / Tỳ vị hư lạnh",
        "forbidden_terms": ["đại hàn", "tính hàn", "thanh nhiệt mạnh", "nhuận tràng"],
        "warning": "Người tỳ vị hư hàn, hay lạnh bụng đi lỏng nên phối thêm gừng già sao vàng hoặc tiêu sọ để cân bằng tính ấm."
    }
}

# ==============================================================================
# 6. CẨM NANG DƯỢC THIỆN & MÓN ĂN BÀI THUỐC DÂN GIAN CHUẨN XÁC (AUTHENTIC RECIPES)
# Đối chiếu trực tiếp từ Dược điển Việt Nam V và "Những cây thuốc và vị thuốc Việt Nam" (GS. Đỗ Tất Lợi)
# ==============================================================================
AUTHENTIC_FOLK_RECIPES: Dict[str, Dict[str, Any]] = {
    # 1. CHANH (Citrus aurantiifolia)
    "chanh": {
        "keywords": ["chanh", "citrus aurantiifolia", "citrus limon", "chanh ta", "chanh tây", "chanh đào"],
        "parts_used": "Nước cốt quả và vỏ quả tươi",
        "recipes": [
            {
                "recipe_id": "rec_chanh_mat_ong",
                "title": "Nước Chanh Ấm Pha Mật Ong Rừng (45°C)",
                "category": "Thức uống giải độc & Tăng sức đề kháng",
                "preparation_time": "10 phút",
                "target_benefit": "Thanh lọc đường tiêu hóa, bổ sung Vitamin C tự nhiên, tăng miễn dịch, giảm đau rát họng",
                "ingredients": [
                    "Nước cốt chanh tươi: 1/2 quả (khoảng 10–15 ml, vắt bỏ hạt để không bị đắng)",
                    "Mật ong rừng nguyên chất: 1–2 thìa cà phê (khoảng 10–15 ml)",
                    "Nước ấm: 250 ml (nhiệt độ chuẩn 40°C – 45°C, tuyệt đối không dùng nước sôi)",
                    "Gừng tươi (tùy chọn vào mùa lạnh): 1 lát mỏng giã dập"
                ],
                "step_by_step": [
                    "Bước 1: Rửa sạch quả chanh dưới vòi nước chảy, dùng muối hạt chà nhẹ bề mặt vỏ để loại bỏ bụi bẩn rồi lau khô.",
                    "Bước 2: Cắt đôi quả chanh, vắt lấy nước cốt qua rây lọc để loại bỏ hoàn toàn hạt (hạt chanh nếu ngâm nước sẽ gây vị đắng chát khó uống).",
                    "Bước 3: Chuẩn bị 250ml nước ấm từ 40°C đến 45°C (nước quá nóng trên 50°C sẽ phá hủy men enzyme quý trong mật ong và làm phân hủy Vitamin C).",
                    "Bước 4: Cho 1–2 thìa mật ong vào ly nước ấm, khuấy nhẹ tay theo một chiều cho mật ong tan hoàn toàn.",
                    "Bước 5: Rót nước cốt chanh vào ly, khuấy đều lần cuối. Nếu trời lạnh có thể thả thêm 1 lát gừng tươi để tăng tính ấm.",
                    "Bước 6: Thưởng thức từng ngụm chậm rãi khi nước còn ấm để dược chất ngấm đều qua niêm mạc họng."
                ],
                "optimal_timing": "Uống vào buổi sáng sớm ngay sau khi thức dậy (trước khi ăn sáng 20 phút) giúp đánh thức hệ tiêu hóa và thanh lọc tạng phủ.",
                "cautions": "Người bị viêm loét dạ dày tá tràng thể nặng nên giảm lượng chanh xuống còn vài giọt hoặc uống sau bữa ăn."
            },
            {
                "recipe_id": "rec_chanh_hap_duong_phen",
                "title": "Chanh Hấp Đường Phèn & Gừng Tươi Trị Ho",
                "category": "Bài thuốc si-rô dân gian trị ho & viêm họng",
                "preparation_time": "30 phút",
                "target_benefit": "Nhuận phế chỉ khái, tiêu đờm, êm dịu thanh quản, dứt cơn ho gió và ho do lạnh",
                "ingredients": [
                    "Chanh tươi (hoặc chanh đào chín mọng): 1 quả",
                    "Đường phèn vàng tự nhiên: 20–25g (giã vụn nhỏ)",
                    "Gừng tươi: 5g (khoảng 3 lát mỏng, thái sợi)",
                    "Muối hạt sạch: 1/4 thìa cà phê"
                ],
                "step_by_step": [
                    "Bước 1: Chanh ngâm trong nước muối loãng 15 phút, vớt ra để ráo rồi thái thành các lát mỏng đều nhau (khoảng 2mm).",
                    "Bước 2: Giữ nguyên vỏ và hạt chanh vì tinh dầu vỏ và chất đắng trong hạt có công năng tiêu đờm, sát trùng họng rất mạnh.",
                    "Bước 3: Xếp từng lớp lát chanh vào bát sứ nhỏ hoặc thố chưng, rải đều đường phèn, gừng thái sợi và chút muối hạt lên bề mặt.",
                    "Bước 4: Đặt bát chanh vào nồi cách thủy, đậy nắp kín để hơi nước không rơi vào bát si-rô.",
                    "Bước 5: Đun lửa vừa trong 20–25 phút cho đường phèn tan chảy hoàn toàn, lát chanh mềm nhũn và chuyển màu vàng sẫm cánh gián.",
                    "Bước 6: Tắt bếp, để nguội bớt rồi dùng thìa dầm nát lát chanh để tinh dầu hòa quyện vào nước cốt đường phèn.",
                    "Bước 7: Ngậm cả nước cốt và lát chanh trong cổ họng từ 2–3 phút rồi nuốt từ từ từng chút một."
                ],
                "optimal_timing": "Dùng 2–3 lần mỗi ngày sau bữa ăn, ngậm ấm trước khi đi ngủ giúp tránh ho đêm.",
                "cautions": "Trẻ em dưới 1 tuổi tuyệt đối không thay đường phèn bằng mật ong (nguy cơ ngộ độc Clostridium botulinum)."
            }
        ]
    },

    # 2. QUÝT / TRẦN BÌ (Citrus reticulata)
    "quyt": {
        "keywords": ["quýt", "citrus reticulata", "trần bì", "vỏ quýt", "quýt tiều"],
        "parts_used": "Vỏ quả chín phơi khô (Trần bì) và múi quả tươi",
        "recipes": [
            {
                "recipe_id": "rec_tra_tran_bi_gung",
                "title": "Trà Vỏ Quýt Sao Vàng (Trần Bì) & Gừng Ấm Trị Đầy Bụng Ho Đờm",
                "category": "Thức uống dưỡng sinh ôn trung chỉ khái",
                "preparation_time": "15 phút",
                "target_benefit": "Lý khí kiện tỳ, hóa đờm ráo thấp, trị ăn uống chậm tiêu, trướng bụng ợ hơi, ho đờm nhiều",
                "ingredients": [
                    "Trần bì (vỏ quýt chín phơi khô lâu năm): 6–10g (rửa sạch bụi phấn)",
                    "Gừng già tươi: 3 lát mỏng (đập dập)",
                    "Nước sôi: 400 ml (95°C)",
                    "Mật ong hoặc đường nâu: 1 thìa cà phê (tùy thích)"
                ],
                "step_by_step": [
                    "Bước 1: Lấy vỏ quýt khô (Trần bì), nếu là vỏ quýt tươi thì cần rửa sạch, cạo bớt phần cùi trắng bên trong để tránh vị đắng trệ.",
                    "Bước 2: Cho vỏ quýt lên chảo nóng sao nhỏ lửa khoảng 2 phút đến khi dậy mùi thơm tinh dầu đặc trưng rồi trút ra đĩa.",
                    "Bước 3: Cho trần bì đã sao vàng cùng 3 lát gừng đập dập vào ấm gốm hoặc bình giữ nhiệt chuyên dụng.",
                    "Bước 4: Châm 100ml nước sôi lắc đều tráng bình trong 10 giây rồi chắt bỏ nước tráng.",
                    "Bước 5: Rót 300ml nước sôi còn lại vào ấm, đậy nắp hãm kín trong 12–15 phút để hoạt chất flavonoid và tinh dầu khuếch tán ra nước trà.",
                    "Bước 6: Rót nước trà ra chén, thêm chút mật ong hoặc đường nâu khuấy đều và uống ấm từng ngụm."
                ],
                "optimal_timing": "Uống sau bữa ăn nhiều dầu mỡ hoặc uống vào buổi chiều tối khi thời tiết se lạnh để ấm bụng ngừa ho.",
                "cautions": "Người thể trạng âm hư hỏa vượng (người nóng trong, ho khan không đờm, họng khô rát) không nên dùng nhiều trần bì."
            }
        ]
    },

    # 3. QUẢ HỒNG BÌ (Clausena lansium)
    "hong_bi": {
        "keywords": ["hồng bì", "clausena lansium", "hoàng bì", "quất hồng bì"],
        "parts_used": "Quả chín tươi hoặc quả sấy khô",
        "recipes": [
            {
                "recipe_id": "rec_hong_bi_hap_duong_phen",
                "title": "Quả Hồng Bì Hấp Đường Phèn Tiêu Đờm Dứt Ho",
                "category": "Bài thuốc si-rô dân gian thanh phế tiêu đờm",
                "preparation_time": "25 phút",
                "target_benefit": "Tiêu đờm đặc, giảm co thắt thanh quản, trị ho gió ho cảm, kích thích tiêu hóa ăn ngon miệng",
                "ingredients": [
                    "Quả quất hồng bì chín mọng: 10–15 quả (khoảng 80–100g)",
                    "Đường phèn vàng: 25–30g (giã nhỏ)",
                    "Gừng tươi: 2 lát mỏng (thái chỉ)"
                ],
                "step_by_step": [
                    "Bước 1: Chọn những quả hồng bì chín vàng đều, không bị dập úng. Rửa sạch dưới vòi nước rồi ngâm nước muối loãng 10 phút.",
                    "Bước 2: Vớt hồng bì ra để ráo, dùng kéo cắt cuống sát quả (không bứt tay tránh làm rách vỏ quả).",
                    "Bước 3: Dùng dao khía nhẹ 3–4 đường dọc thân quả hoặc bóp nhẹ để vỏ nứt ra giúp ngấm đường phèn dễ dàng.",
                    "Bước 4: Xếp hồng bì vào thố sứ, rải đều đường phèn và gừng thái chỉ lên trên.",
                    "Bước 5: Cho thố vào nồi hấp cách thủy trong 20 phút với lửa vừa đến khi quả hồng bì teo lại, tiết ra nước cốt sánh vàng óng.",
                    "Bước 6: Tắt bếp, để nguội tự nhiên. Khi dùng múc 2–3 thìa si-rô kèm 1–2 quả hồng bì ngậm nhai nuốt cả bã."
                ],
                "optimal_timing": "Uống ấm ngày 2–3 lần sau bữa ăn hoặc mỗi khi có cơn ho kích ứng họng.",
                "cautions": "Người đang bị tiêu chảy cấp không nên ăn quá nhiều quả hồng bì tươi chưa qua hấp nhiệt."
            }
        ]
    },

    # 4. SÂM BỐ CHÍNH (Abelmoschus sagittifolius)
    "sam_bo_chinh": {
        "keywords": ["sâm bố chính", "abelmoschus sagittifolius", "thổ hào sâm", "nhân sâm phú yên"],
        "parts_used": "Củ rễ đã rửa sạch cạo vỏ sấy khô hoặc dùng tươi",
        "recipes": [
            {
                "recipe_id": "rec_sam_bo_chinh_tiem_ga",
                "title": "Canh Gà Ác Tiềm Sâm Bố Chính & Hạt Sen Đại Bổ",
                "category": "Canh tiềm dưỡng sinh bồi bổ khí huyết",
                "preparation_time": "75 phút",
                "target_benefit": "Bồi bổ nguyên khí, dưỡng tâm an thần, phục hồi sức khỏe cho người sau ốm dậy, phụ nữ sau sinh, người suy nhược",
                "ingredients": [
                    "Củ sâm bố chính tươi: 30–40g (hoặc củ khô 15–20g thái lát)",
                    "Gà ác nguyên con: 1 con (khoảng 350–450g, làm sạch bỏ nội tạng)",
                    "Hạt sen tươi: 30g (bỏ tâm sen đắng)",
                    "Táo đỏ tân cương: 5 quả (khía dọc thân)",
                    "Kỷ tử đỏ: 10g",
                    "Gừng tươi: 3 lát mỏng",
                    "Gia vị: 1 chút muối hồng hoặc nước mắm nguyên chất thanh đạm"
                ],
                "step_by_step": [
                    "Bước 1: Sơ chế gà ác xát muối hạt và gừng đập dập khử sạch mùi tanh, chần sơ qua nồi nước sôi trong 1 phút rồi vớt ra xả nước lạnh để thịt săn chắc và nước hầm trong.",
                    "Bước 2: Củ sâm bố chính rửa sạch đất cát, cạo nhẹ lớp vỏ mỏng bên ngoài, thái lát xéo dày khoảng 3mm (nếu củ khô ngâm nước ấm 20 phút cho nở mềm).",
                    "Bước 3: Hạt sen tươi rửa sạch, táo đỏ và kỷ tử rửa qua nước ấm để loại bỏ bụi phấn.",
                    "Bước 4: Xếp 1/2 lượng sâm bố chính, hạt sen và táo đỏ vào bụng gà ác, đặt gà vào thố sứ hoặc nồi đất, rải phần nguyên liệu còn lại và vài lát gừng xung quanh.",
                    "Bước 5: Châm nước dùng sôi hoặc nước dừa tươi ngập xâm xấp gà (khoảng 700–800 ml), đậy kín nắp thố.",
                    "Bước 6: Đặt thố vào nồi hấp tiềm cách thủy trong 60–75 phút với ngọn lửa nhỏ liu riu cho đến khi thịt gà mềm rục, chất ngọt và saponin từ củ sâm hòa quyện hoàn toàn vào nước canh.",
                    "Bước 7: Nêm chút muối nhạt vừa miệng (không nêm mì chính hay đường để giữ trọn vị ngọt thanh tự nhiên của củ sâm và thịt gà)."
                ],
                "optimal_timing": "Dùng nóng trong bữa ăn chính, ăn cả cái lẫn nước. Thích hợp dùng 1–2 lần mỗi tuần.",
                "cautions": "Tuyệt đối không dùng chung với củ cải trắng hoặc uống nước chè đặc trong vòng 2 giờ vì sẽ triệt tiêu dược tính bổ khí của sâm."
            }
        ]
    },

    # 5. CÂY ĐINH LĂNG (Polyscias fruticosa)
    "dinh_lang": {
        "keywords": ["đinh lăng", "polyscias fruticosa", "cây gỏi cá", "nam dương sâm"],
        "parts_used": "Lá bánh tẻ non (nấu canh/ăn gỏi) và rễ củ lâu năm (sắc nước/ngâm rượu)",
        "recipes": [
            {
                "recipe_id": "rec_canh_la_dinh_lang",
                "title": "Canh Lá Đinh Lăng Nấu Sườn Non / Cá Lóc Bổ Huyết",
                "category": "Món canh bài thuốc dưỡng sinh gia đình",
                "preparation_time": "35 phút",
                "target_benefit": "Bổ huyết tăng lực, kích thích tiêu hóa, lợi sữa cho phụ nữ sau sinh, giải trừ mệt mỏi suy nhược",
                "ingredients": [
                    "Lá đinh lăng bánh tẻ tươi: 50–70g (chọn cành lá nhỏ có răng cưa, không quá già)",
                    "Sườn non heo (hoặc cá lóc phi lê): 250–300g (chặt miếng vừa ăn)",
                    "Hành khô: 1 củ băm nhỏ",
                    "Gia vị: Muối, nước mắm ngon, hạt tiêu xay"
                ],
                "step_by_step": [
                    "Bước 1: Lá đinh lăng tuốt lấy phần lá non và ngọn mềm, ngâm nước muối loãng 10 phút, vớt ra rửa sạch để ráo nước rồi dùng tay vò nhẹ cho mềm lá.",
                    "Bước 2: Sườn non chặt khúc, chần qua nước sôi gừng để khử mùi hôi, vớt ra xả sạch.",
                    "Bước 3: Phi thơm hành khô băm với chút dầu ăn, trút sườn non vào đảo đều cùng 1 thìa nước mắm cho săn lại.",
                    "Bước 4: Đổ 800ml nước vào nồi đun sôi bùng, vớt sạch bọt trên mặt để nước canh trong vắt, sau đó hạ lửa nhỏ ninh sườn trong 20 phút cho mềm ngọt.",
                    "Bước 5: Khi sườn đã chín mềm, tăng lửa to cho nước sôi trở lại rồi thả toàn bộ lá đinh lăng vào nhấn chìm xuống nước canh.",
                    "Bước 6: Nấu sôi tiếp trong khoảng 2–3 phút cho lá chín tới (không đun quá lâu làm nát lá và bay hơi mùi thơm tinh dầu đặc trưng), nêm lại gia vị vừa ăn rồi tắt bếp ngay.",
                    "Bước 7: Múc canh ra tô, rắc chút tiêu cay nhẹ, ăn nóng cùng cơm trắng."
                ],
                "optimal_timing": "Dùng trong bữa cơm trưa hoặc chiều, thích hợp bồi dưỡng khi người có cảm giác uể oải, suy nhược.",
                "cautions": "Lá đinh lăng có chứa saponin nên không nấu lượng quá nhiều một lúc; người huyết áp thấp không nên ăn quá đặc."
            }
        ]
    },

    # 6. LÁ LỐT (Piper sarmentosum)
    "la_lot": {
        "keywords": ["lá lốt", "piper sarmentosum", "cây lá lốt"],
        "parts_used": "Lá tươi và toàn thân cây",
        "recipes": [
            {
                "recipe_id": "rec_cha_la_lot_thit_bo",
                "title": "Chả Thịt Bò Cuốn Lá Lốt Nướng Trừ Phong Thấp Đau Khớp",
                "category": "Món ăn bài thuốc ấm kinh thông lạc",
                "preparation_time": "30 phút",
                "target_benefit": "Ôn trung tán hàn, khu phong trừ thấp, giảm đau nhức xương khớp do lạnh, ấm tỳ vị chống đầy bụng",
                "ingredients": [
                    "Lá lốt tươi: 20–25 lá to nguyên vẹn (để cuốn) + 5 lá nhỏ (thái chỉ trộn nhân)",
                    "Thịt bò nạc xay: 200g (phối cùng 50g mỡ heo băm nhỏ để chả mềm ngậy không bị khô)",
                    "Hành củ, tỏi băm nhuyễn: 1 thìa",
                    "Gia vị: Nước mắm, hạt tiêu, dầu mè"
                ],
                "step_by_step": [
                    "Bước 1: Lá lốt rửa nhẹ nhàng từng lá tránh rách nát, vớt ra lau thật khô bề mặt lá.",
                    "Bước 2: Thịt bò xay ướp cùng hành tỏi băm, 5 lá lốt non thái chỉ, 1 thìa nước mắm, tiêu xay và chút dầu mè trong 15 phút cho ngấm đều gia vị.",
                    "Bước 3: Đặt lá lốt lên thớt (úp mặt bóng có gân đậm xuống dưới để khi cuốn mặt bóng lộ ra ngoài cho đẹp), cho 1 lượng nhân thịt vừa phải vào giữa.",
                    "Bước 4: Gấp 2 mép lá lại rồi cuộn tròn chặt tay, dùng cuống lá găm nhẹ để cố định mép cuốn.",
                    "Bước 5: Xếp chả vào nồi chiên không dầu hoặc áp chảo với chút dầu ăn mỏng ở nhiệt độ 160°C – 170°C trong 8–10 phút, lật mặt nướng tiếp 5 phút đến khi lá lốt chuyển màu xanh thẫm dậy mùi thơm lừng nức.",
                    "Bước 6: Gắp chả ra đĩa lót giấy thấm dầu, ăn nóng chấm nước mắm gừng ớt hoặc ăn kèm rau sống bánh tráng."
                ],
                "optimal_timing": "Ăn nóng trong bữa cơm gia đình vào những ngày thời tiết lạnh, mưa ẩm trở trời đau nhức khớp.",
                "cautions": "Người đang bị nhiệt miệng, đau mắt đỏ, táo bón (nhiệt chứng) không nên ăn quá nhiều món chiên nướng lá lốt."
            }
        ]
    },

    # 7. NGẢI CỨU (Artemisia vulgaris)
    "ngai_cuu": {
        "keywords": ["ngải cứu", "artemisia vulgaris", "ngải diệp", "thuốc cứu"],
        "parts_used": "Ngọn non và lá bánh tẻ",
        "recipes": [
            {
                "recipe_id": "rec_trung_ran_ngai_cuu",
                "title": "Trứng Gà Tráng Lá Ngải Cứu Hoạt Huyết Ấm Tử Cung",
                "category": "Món ăn bài thuốc dưỡng huyết điều kinh",
                "preparation_time": "15 phút",
                "target_benefit": "Hoạt huyết hóa ứ, điều hòa kinh nguyệt, trừ hàn thấp, ấm tử cung, trị đau đầu do thiếu máu não",
                "ingredients": [
                    "Lá ngải cứu non: 30–40g (chọn lá non xanh mướt, ngắt bỏ cọng già xơ)",
                    "Trứng gà ta: 2–3 quả",
                    "Hành tím băm: 1 củ",
                    "Gia vị: Nước mắm truyền thống, hạt tiêu"
                ],
                "step_by_step": [
                    "Bước 1: Ngải cứu nhặt rửa sạch, ngâm nước muối loãng 5 phút rồi vớt ra để ráo nước hoàn toàn.",
                    "Bước 2: Dùng dao thái ngải cứu thật nhỏ mịn (thái càng mịn trứng càng dính quyện đều và giảm độ đắng gắt).",
                    "Bước 3: Đập 2–3 quả trứng gà vào tô, cho ngải cứu đã thái mịn, hành tím băm, 1 thìa cà phê nước mắm và chút tiêu xay.",
                    "Bước 4: Dùng đũa đánh bông đều tay cho trứng và ngải cứu quyện chặt vào nhau thành hỗn hợp sánh.",
                    "Bước 5: Đun nóng chảo với 1 thìa dầu ăn, láng đều mặt chảo rồi trút hỗn hợp trứng ngải cứu vào, dàn đều hình tròn.",
                    "Bước 6: Hạ lửa vừa đậy nắp vung khoảng 2–3 phút cho mặt dưới vàng rộm và ngải cứu chín thấu, sau đó khéo léo lật mặt tráng tiếp 2 phút đến khi hai mặt vàng đều tỏa mùi thơm ngát.",
                    "Bước 7: Trút trứng ra đĩa cắt miếng tam giác vừa ăn, dùng nóng ngay khi vừa ra lò."
                ],
                "optimal_timing": "Ăn vào bữa sáng hoặc tối khi thời tiết se lạnh, phụ nữ dùng trước và sau chu kỳ kinh nguyệt rất tốt.",
                "cautions": "Phụ nữ đang mang thai 3 tháng đầu không nên ăn ngải cứu liều lượng nhiều vì có tính co bóp tử cung."
            }
        ]
    },

    # 8. TÍA TÔ (Perilla frutescens)
    "tia_to": {
        "keywords": ["tía tô", "perilla frutescens", "tử tô", "tía tô cảnh"],
        "parts_used": "Lá tươi và cành ngọn",
        "recipes": [
            {
                "recipe_id": "rec_chao_thit_tia_to",
                "title": "Cháo Thịt Băm Tía Tô & Hành Hoa Giải Cảm Đổ Mồ Hôi",
                "category": "Món cháo bài thuốc giải cảm phong hàn",
                "preparation_time": "30 phút",
                "target_benefit": "Phát hãn giải biểu, giải cảm lạnh, hạ sốt gai rét, thông mũi họng, êm bụng ấm tỳ vị",
                "ingredients": [
                    "Lá tía tô tươi: 30g (chọn lá màu tía đậm cả hai mặt)",
                    "Hành hoa: 2 nhánh",
                    "Thịt heo nạc băm: 100g",
                    "Gạo tẻ thơm: 80g",
                    "Gừng tươi: 1 nhánh nhỏ (thái chỉ sợi mỏng)",
                    "Gia vị: Nước mắm ngon, hạt tiêu đen xay"
                ],
                "step_by_step": [
                    "Bước 1: Gạo vo sạch, cho vào nồi cùng 800ml nước ninh nhừ thành cháo trắng nở bung hoa sánh mịn.",
                    "Bước 2: Thịt nạc băm ướp chút nước mắm, xào săn trên chảo với hành khô cho thơm đậm đà.",
                    "Bước 3: Lá tía tô và hành hoa rửa sạch bụi đất, vẩy thật ráo nước rồi dùng dao thái nhỏ mịn.",
                    "Bước 4: Khi cháo chín nhừ, trút thịt băm xào vào nồi cháo khuấy đều đun sôi lại trong 3 phút.",
                    "Bước 5: Múc cháo đang sôi sùng sục ra tô lớn, lập tức cho toàn bộ lá tía tô thái nhỏ, hành hoa và gừng thái chỉ vào tô cháo.",
                    "Bước 6: Rắc chút hạt tiêu cay nóng lên trên, dùng thìa trộn đều từ dưới lên cho lá tía tô chín tái giữ trọn tinh dầu thơm ngát.",
                    "Bước 7: Ăn ngay khi cháo còn bốc khói nghi ngút, sau khi ăn đắp chăn ấm để cơ thể toát mồ hôi giải trừ độc tố cảm lạnh."
                ],
                "optimal_timing": "Ăn ngay khi có triệu chứng hắt hơi, sổ mũi, ớn lạnh gai rét do trúng gió cảm mạo.",
                "cautions": "Người đang bị ra mồ hôi trộm nhiều hoặc sốt cao co giật không nên dùng quá nhiều gừng và tiêu."
            }
        ]
    },

    # 9. RAU MÁ (Centella asiatica)
    "rau_ma": {
        "keywords": ["rau má", "centella asiatica", "tích tuyết thảo", "liên tiền thảo"],
        "parts_used": "Toàn cây tươi rễ lá",
        "recipes": [
            {
                "recipe_id": "rec_nuoc_ep_rau_ma_dau_xanh",
                "title": "Nước Ép Rau Má Đậu Xanh Thanh Nhiệt Mát Gan",
                "category": "Thức uống giải khát & Dưỡng nhan mát gan",
                "preparation_time": "20 phút",
                "target_benefit": "Thanh nhiệt giải độc, mát gan lợi tiểu, hỗ trợ trị mụn nhọt nhiệt miệng, hạ sốt mùa hè",
                "ingredients": [
                    "Rau má tươi: 150–200g (chọn rau má ta lá nhỏ mọc tự nhiên, vị đậm đà)",
                    "Đậu xanh cà vỏ: 50g (đã hấp chín nhừ)",
                    "Nước lọc tinh khiết đun sôi để nguội: 400 ml",
                    "Đường phèn hoặc đường thốt nốt: 1–2 thìa (tùy độ ngọt)"
                ],
                "step_by_step": [
                    "Bước 1: Rau má nhặt sạch rễ đen và lá úa vàng, ngâm nước muối loãng 15 phút rồi rửa kỹ dưới vòi nước 3 lần cho sạch cát.",
                    "Bước 2: Đậu xanh vo sạch ngâm nước ấm 30 phút, đem hấp cách thủy khoảng 15 phút cho hạt đậu chín mềm tơi xốp.",
                    "Bước 3: Cắt ngắn rau má, cho vào máy xay sinh tố cùng 400ml nước lọc, xay nhuyễn mịn trong 1 phút.",
                    "Bước 4: Đổ hỗn hợp qua rây lọc hoặc túi vải lọc mịn vắt kiệt lấy nước cốt xanh biếc, bỏ phần bã xơ.",
                    "Bước 5: Cho phần nước cốt rau má trở lại máy xay cùng 50g đậu xanh đã hấp chín và 1–2 thìa đường phèn, bật máy xay tiếp 30 giây cho hòa quyện sánh mịn béo ngậy.",
                    "Bước 6: Rót ra ly thủy tinh, có thể thêm vài viên đá lạnh thưởng thức từng ngụm sảng khoái mát lành."
                ],
                "optimal_timing": "Uống vào buổi trưa hoặc xế chiều trong những ngày nắng nóng oi bức mệt mỏi.",
                "cautions": "Người thể hàn, đang bị đau bụng tiêu chảy hoặc phụ nữ mang thai không nên uống nước rau má tươi sống liên tục."
            }
        ]
    },

    # 10. HOA CÚC (Chrysanthemum indicum)
    "hoa_cuc": {
        "keywords": ["hoa cúc", "cúc hoa", "chrysanthemum indicum", "chrysanthemum morifolium", "kim cúc", "bạch cúc"],
        "parts_used": "Nụ hoa hoặc bông hoa cúc sấy khô",
        "recipes": [
            {
                "recipe_id": "rec_tra_hoa_cuc_ky_tu",
                "title": "Trà Hoa Cúc Vàng & Kỷ Tử Sáng Mắt Ngủ Sâu",
                "category": "Trà dưỡng sinh thanh can minh mục",
                "preparation_time": "12 phút",
                "target_benefit": "Thanh can hỏa, sáng mắt mỏi mắt do máy tính, hạ huyết áp, an dịu thần kinh, dễ đi vào giấc ngủ",
                "ingredients": [
                    "Bông cúc hoa khô: 5–8 bông (chọn cúc sấy lạnh tự nhiên không ướp diêm sinh)",
                    "Kỷ tử đỏ ngọt: 10–12 hạt",
                    "Táo đỏ: 2 quả (cắt lát mỏng)",
                    "Nước sôi: 350 ml (nhiệt độ chuẩn 90°C)"
                ],
                "step_by_step": [
                    "Bước 1: Tráng sạch ấm trà gốm hoặc bình thủy tinh chịu nhiệt bằng nước sôi để làm nóng ấm.",
                    "Bước 2: Cho hoa cúc, kỷ tử đỏ và các lát táo đỏ vào ấm trà.",
                    "Bước 3: Rót khoảng 50ml nước sôi vào lắc nhẹ trong 5 giây rồi chắt bỏ nước đầu (bước đánh thức hoa và tráng sạch bụi thảo mộc).",
                    "Bước 4: Rót tiếp 300ml nước sôi ở 90°C vào ấm, đậy kín nắp bình.",
                    "Bước 5: Hãm trà tĩnh trong 8–10 phút để các cánh hoa cúc ngậm nước nở bung xòe đều, nước trà chuyển màu vàng óng ánh tỏa hương thơm dịu mát.",
                    "Bước 6: Rót nước trà ra chén nhỏ, nhấp từng ngụm ấm áp, cảm nhận vị đắng nhẹ đầu lưỡi chuyển thành hậu ngọt thanh tao ở cuống họng."
                ],
                "optimal_timing": "Uống sau giờ làm việc căng thẳng buổi chiều hoặc trước giờ đi ngủ 45 phút giúp tĩnh tâm an giấc.",
                "cautions": "Người bị huyết áp quá thấp hoặc đang lạnh bụng tiêu chảy nên thả thêm 1 lát gừng tươi vào ấm trà."
            }
        ]
    },

    # 11. CÂY SEN (Nelumbo nucifera)
    "sen": {
        "keywords": ["sen", "nelumbo nucifera", "hạt sen", "tâm sen", "củ sen", "liên nhục", "liên tâm"],
        "parts_used": "Hạt sen, tâm sen, củ sen và lá sen",
        "recipes": [
            {
                "recipe_id": "rec_tra_tam_sen_an_than",
                "title": "Trà Tâm Sen (Liên Tâm) Sao Vàng Trị Mất Ngủ Thể Nhiệt",
                "category": "Thức uống an thần hạ hỏa",
                "preparation_time": "10 phút",
                "target_benefit": "Thanh tâm hỏa, trấn kinh an thần, hạ huyết áp, đặc trị chứng mất ngủ triền miên, hồi hộp bốc hỏa",
                "ingredients": [
                    "Tâm sen khô đã sao vàng: 2–3g (khoảng 20–30 mầm tâm sen xanh, không dùng quá liều)",
                    "Nước sôi: 250 ml (95°C)"
                ],
                "step_by_step": [
                    "Bước 1: Tâm sen bắt buộc phải được sao vàng hạ thổ trước khi dùng để khử bớt độc tính nhẹ và làm giảm bớt tính đại hàn.",
                    "Bước 2: Cho 2–3g tâm sen đã sao vàng vào ly hoặc bình hãm trà có nắp đậy.",
                    "Bước 3: Rót 250ml nước sôi già vào ly, đậy nắp kín.",
                    "Bước 4: Hãm trong 10 phút cho mầm sen chìm xuống đáy và nước trà có màu vàng xanh nhạt.",
                    "Bước 5: Uống ấm từng ngụm nhỏ. Trà có vị đắng đậm đà nhưng hậu ngọt thanh mát."
                ],
                "optimal_timing": "Uống trước khi đi ngủ khoảng 1 tiếng, dùng từng đợt 7–10 ngày rồi nghỉ, không uống thay nước cả ngày.",
                "cautions": "Người huyết áp thấp, thể trạng hư hàn hoặc trẻ nhỏ tuyệt đối không uống trà tâm sen liều cao kéo dài."
            },
            {
                "recipe_id": "rec_canh_cu_sen_suon_non",
                "title": "Canh Củ Sen Hầm Sườn Non Kiện Tỳ Bổ Huyết",
                "category": "Canh hầm dưỡng sinh bổ dưỡng gia đình",
                "preparation_time": "50 phút",
                "target_benefit": "Bổ tỳ khai vị, bổ huyết sinh tân, an thần, giải nhiệt mùa hè, người già và trẻ nhỏ ăn đều tốt",
                "ingredients": [
                    "Củ sen tươi: 1 củ (khoảng 250–300g, chọn củ mập tròn chắc tay)",
                    "Sườn non heo: 300g",
                    "Cà rốt: 1 củ",
                    "Hành hoa, ngò rí, gia vị vừa đủ"
                ],
                "step_by_step": [
                    "Bước 1: Củ sen gọt sạch vỏ ngoài, thái khoanh tròn dày khoảng 8mm, ngâm ngay vào chậu nước có pha chút nước cốt chanh hoặc muối để củ sen không bị thâm đen.",
                    "Bước 2: Sườn non chặt khúc, chần qua nước sôi gừng vớt ra xả sạch bọt bẩn.",
                    "Bước 3: Cho sườn và củ sen vào nồi cùng 1 lít nước đun sôi bùng, hạ lửa nhỏ hầm trong 35 phút cho sườn mềm và củ sen bở bùi ngọt nước.",
                    "Bước 4: Cho tiếp cà rốt tỉa hoa vào hầm thêm 10 phút cho chín tới.",
                    "Bước 5: Nêm nước mắm ngon vừa ăn, tắt bếp rắc hành hoa và ngò rí thái nhỏ lên trên."
                ],
                "optimal_timing": "Dùng nóng trong bữa cơm gia đình để thanh lọc cơ thể.",
                "cautions": "Người đang bị trướng bụng đầy hơi không nên ăn quá nhiều củ sen một lúc."
            }
        ]
    },

    # 12. GỪNG TƯƠI (Zingiber officinale)
    "gung": {
        "keywords": ["gừng", "zingiber officinale", "sinh khương", "can khương"],
        "parts_used": "Củ gừng tươi",
        "recipes": [
            {
                "recipe_id": "rec_tra_gung_mat_ong",
                "title": "Trà Gừng Tươi Mật Ong Ấm Trị Lạnh Bụng Buồn Nôn",
                "category": "Thức uống làm ấm tỳ vị chỉ thổ",
                "preparation_time": "10 phút",
                "target_benefit": "Ôn trung tán hàn, hồi dương thông mạch, trị lạnh bụng tiêu chảy, chống buồn nôn say xe, phòng cảm lạnh",
                "ingredients": [
                    "Gừng tươi già: 1 nhánh nhỏ (khoảng 15g, giữ nguyên vỏ)",
                    "Mật ong nguyên chất: 1–2 thìa cà phê",
                    "Nước sôi: 250 ml"
                ],
                "step_by_step": [
                    "Bước 1: Rửa sạch củ gừng bằng bàn chải nhỏ để loại bỏ đất cát, giữ nguyên vỏ vì vỏ gừng có tính lợi tiểu tiêu phù cân bằng với ruột gừng.",
                    "Bước 2: Dùng dao thái gừng thành 4–5 lát mỏng rồi dùng sống dao đập giập nhẹ để tinh dầu gingerol dễ hòa tan.",
                    "Bước 3: Cho gừng vào cốc, rót 250ml nước sôi già vào, đậy nắp hãm trong 8–10 phút cho nước chuyển màu vàng nhạt và dậy mùi cay nồng ấm.",
                    "Bước 4: Chờ nước trà nguội bớt xuống khoảng 45°C thì cho 1–2 thìa mật ong vào khuấy tan đều.",
                    "Bước 5: Nhấp từng ngụm nhỏ, hơi ấm của gừng và mật ong sẽ lan tỏa làm ấm khoang bụng tức thì."
                ],
                "optimal_timing": "Uống vào buổi sáng sớm hoặc khi vừa đi mưa gió lạnh về, hoặc trước khi lên xe chống say tàu xe 20 phút.",
                "cautions": "Không nên uống trà gừng vào buổi tối muộn; người đang bị đau dạ dày chảy máu hoặc sốt cao không dùng."
            }
        ]
    },

    # 13. MƯỚP ĐẮNG / KHỔ QUA (Momordica charantia)
    "kho_qua": {
        "keywords": ["mướp đắng", "khổ qua", "momordica charantia"],
        "parts_used": "Quả tươi, lá non",
        "recipes": [
            {
                "recipe_id": "rec_canh_kho_qua_nhoi_thit",
                "title": "Canh Khổ Qua Nhồi Thịt Nạc Thanh Nhiệt Giải Độc",
                "category": "Món canh dược thiện thanh nhiệt giáng hỏa",
                "preparation_time": "40 phút",
                "target_benefit": "Thanh nhiệt tả hỏa, giải khát, mát huyết giải thử, hỗ trợ hạ đường huyết và hạ men gan",
                "ingredients": [
                    "Khổ qua tươi (trái vừa, gai nở đều): 2 quả (khoảng 300g)",
                    "Thịt nạc vai xay nhuyễn: 150g",
                    "Nấm mèo (mộc nhĩ): 2 tai (ngâm nở, thái sợi nhỏ băm vụn)",
                    "Miến dong (bún tàu): 1 nhúm nhỏ (ngâm mềm cắt khúc 1cm)",
                    "Hành tím băm: 1 củ, tiêu xay: 1/2 thìa cà phê, muối hạt, nước dùng xương: 800ml"
                ],
                "step_by_step": [
                    "Bước 1: Khổ qua rửa sạch, cắt bỏ hai đầu, dùng cán thìa khoét sạch phần ruột và hạt trắng bên trong (cạo kỹ lớp màng trắng để giảm vị đắng gắt).",
                    "Bước 2: Cắt khổ qua thành từng khúc tròn dài khoảng 4–5cm, hoặc để nguyên trái rạch một đường dọc thân.",
                    "Bước 3: Trộn đều thịt xay với mộc nhĩ, bún tàu, hành tím, tiêu và 1/2 thìa cà phê bột nêm trong 10 phút cho ngấm đều gia vị.",
                    "Bước 4: Nhồi hỗn hợp thịt vào từng khúc khổ qua, ấn vừa chặt tay để thịt không bị bung ra khi nấu.",
                    "Bước 5: Đun sôi 800ml nước dùng gà hoặc nước xương, hạ nhỏ lửa rồi nhẹ nhàng thả từng khúc khổ qua vào nồi.",
                    "Bước 6: Nấu lửa vừa không đậy vung (giúp nước canh trong và giữ màu xanh tươi) trong 20–25 phút đến khi dùng đũa xiên qua thân khổ qua thấy mềm vừa tới.",
                    "Bước 7: Nêm lại chút muối nhạt, múc ra bát to, rắc hành hoa ngò rí và tiêu bột lên bề mặt, dùng nóng trong bữa cơm."
                ],
                "optimal_timing": "Dùng trong bữa cơm trưa hoặc chiều những ngày hè oi bức, người bị nóng trong sinh mụn nhọt.",
                "cautions": "Phụ nữ mang thai không nên ăn quá nhiều khổ qua do hoạt chất charantin và vicine có thể gây kích thích co bóp tử cung."
            }
        ]
    },

    # 14. DIẾP CÁ / NGƯ TINH THẢO (Houttuynia cordata)
    "diep_ca": {
        "keywords": ["diếp cá", "ngư tinh thảo", "rau dấp cá", "houttuynia cordata"],
        "parts_used": "Toàn cây trên mặt đất tươi",
        "recipes": [
            {
                "recipe_id": "rec_nuoc_ep_diep_ca_dau_xanh",
                "title": "Nước Ép Diếp Cá Đậu Xanh Thanh Nhiệt Tiêu Viêm Trĩ",
                "category": "Thức uống thảo dược tiêu viêm tán kết",
                "preparation_time": "20 phút",
                "target_benefit": "Thanh nhiệt giải độc, tiêu thũng bài nùng, lợi tiểu tiêu phù, hỗ trợ điều trị trĩ nội trĩ ngoại và mụn nhọt sưng đau",
                "ingredients": [
                    "Rau diếp cá tươi: 100g (chọn lá xanh non, tươi mới hái)",
                    "Đậu xanh cà vỏ: 50g (đã hấp chín mềm)",
                    "Đường phèn hoặc mật ong: 2 thìa cà phê (tùy khẩu vị)",
                    "Nước lọc đun sôi để nguội: 300ml, chút muối hạt"
                ],
                "step_by_step": [
                    "Bước 1: Nhặt sạch rễ già và lá úa của rau diếp cá, rửa kỹ dưới vòi nước chảy qua 3 lần nước.",
                    "Bước 2: Ngâm rau diếp cá trong chậu nước muối loãng 10 phút để khử khuẩn giun sán rồi vớt ra rổ để thật ráo nước.",
                    "Bước 3: Cho diếp cá vào máy xay sinh tố cùng 300ml nước lọc và đậu xanh đã hấp chín nhừ.",
                    "Bước 4: Xay nhuyễn mịn hỗn hợp trong 1–2 phút cho lá diếp cá và đậu xanh hòa quyện hoàn toàn.",
                    "Bước 5: Đổ hỗn hợp qua rây lọc dày hoặc túi vải ép lấy phần nước cốt sánh mịn, bỏ phần bã xơ.",
                    "Bước 6: Hòa đường phèn hoặc mật ong vào nước ép, khuấy đều cho tan, có thể cho thêm vài viên đá lạnh nếu thích uống mát."
                ],
                "optimal_timing": "Uống 1 cốc sau bữa ăn trưa hoặc buổi chiều, dùng đều đặn 3–5 ngày trong đợt nóng nhiệt bùng phát trĩ.",
                "cautions": "Người thể tạng hư hàn, lạnh bụng đi ngoài phân lỏng không nên uống vào buổi tối muộn."
            }
        ]
    },

    # 15. BẠC HÀ (Mentha arvensis)
    "bac_ha": {
        "keywords": ["bạc hà", "mentha arvensis", "húng cay"],
        "parts_used": "Thân và lá tươi hoặc phơi trong bóng râm",
        "recipes": [
            {
                "recipe_id": "rec_tra_bac_ha_mat_ong",
                "title": "Trà Bạc Hà Tươi & Mật Ong Thông Mũi Thanh Họng",
                "category": "Thức uống thảo dược tán phong nhiệt giải cảm",
                "preparation_time": "10 phút",
                "target_benefit": "Phát tán phong nhiệt, thông thoáng xoang mũi, làm dịu niêm mạc họng, hỗ trợ tiêu hóa ợ đầy",
                "ingredients": [
                    "Lá bạc hà tươi: 10–15 lá (khoảng 8g)",
                    "Nước sôi: 250ml (85°C – 90°C)",
                    "Mật ong nguyên chất: 1–2 thìa cà phê",
                    "Chanh tươi: 1 lát mỏng"
                ],
                "step_by_step": [
                    "Bước 1: Rửa sạch từng lá bạc hà dưới vòi nước nhẹ, để ráo trên khăn sạch.",
                    "Bước 2: Dùng tay vò nhẹ các lá bạc hà để làm vỡ các túi tinh dầu menthol trên bề mặt lá (không xé nát vụn).",
                    "Bước 3: Cho lá vào ly thủy tinh hoặc ấm trà, châm 250ml nước nóng khoảng 85°C (không dùng nước sôi 100°C làm bay hơi tinh dầu quý).",
                    "Bước 4: Đậy nắp ly lại ngay trong 5–7 phút để giữ kín hương thơm tinh dầu lan tỏa.",
                    "Bước 5: Mở nắp, cho mật ong và thả 1 lát chanh mỏng vào khuấy nhẹ.",
                    "Bước 6: Hít thở nhẹ nhàng làn hơi nước bốc lên mũi giúp thông xoang, sau đó uống từng ngụm ấm thanh mát sảng khoái."
                ],
                "optimal_timing": "Uống sau bữa ăn nhiều dầu mỡ để tiêu thực hoặc khi bắt đầu có dấu hiệu nghẹt mũi cảm phong nhiệt.",
                "cautions": "Không dùng tinh dầu bạc hà đậm đặc cho trẻ sơ sinh và trẻ nhỏ dưới 2 tuổi (nguy cơ ức chế hô hấp)."
            }
        ]
    },

    # 16. NGHỆ VÀNG (Curcuma longa)
    "nghe_vang": {
        "keywords": ["nghệ", "curcuma longa", "nghệ vàng", "khương hoàng", "uất kim"],
        "parts_used": "Thân rễ (củ) tươi hoặc tinh bột nghệ",
        "recipes": [
            {
                "recipe_id": "rec_nghe_mat_ong_da_day",
                "title": "Nước Cốt Nghệ Vàng Tươi Ngâm Mật Ong Phục Hồi Niêm Mạc Dạ Dày",
                "category": "Thức uống dưỡng sinh phục hồi tỳ vị",
                "preparation_time": "15 phút",
                "target_benefit": "Hành khí phá huyết, chỉ thống sinh cơ, kháng viêm ổ loét dạ dày tá tràng, phục hồi niêm mạc ruột",
                "ingredients": [
                    "Nghệ vàng già tươi: 1 củ (khoảng 25g, ruột vàng đậm)",
                    "Mật ong hoa rừng nguyên chất: 2 thìa canh",
                    "Nước ấm 40°C: 150ml"
                ],
                "step_by_step": [
                    "Bước 1: Nghệ tươi cọ sạch đất cát, cạo sạch lớp vỏ mỏng bên ngoài, rửa lại nước sạch rồi để ráo.",
                    "Bước 2: Dùng dao thái nghệ thành từng lát mỏng rồi giã thật nhuyễn hoặc cho vào cối xay mịn.",
                    "Bước 3: Cho nghệ giã nhuyễn vào miếng vải mùng sạch, vắt kiệt lấy nước cốt nghệ tươi nguyên chất (khoảng 10–15ml).",
                    "Bước 4: Hòa nước cốt nghệ tươi với 150ml nước ấm 40°C.",
                    "Bước 5: Thêm 2 thìa mật ong nguyên chất vào khuấy đều cho mật tan hoàn toàn.",
                    "Bước 6: Uống từ từ từng ngụm nhỏ để curcumin và enzyme mật ong tráng đều khắp niêm mạc thành dạ dày."
                ],
                "optimal_timing": "Uống vào buổi sáng sớm trước khi ăn sáng 30 phút hoặc khi cơn đau dạ dày râm ran xuất hiện.",
                "cautions": "Phụ nữ mang thai không dùng lượng lớn nghệ vì tính hành huyết phá ứ có thể ảnh hưởng thai kỳ."
            }
        ]
    },

    # 17. CÀ GAI LEO (Solanum procumbens)
    "ca_gai_leo": {
        "keywords": ["cà gai leo", "solanum procumbens", "cà vạnh", "cà gai dây"],
        "parts_used": "Thân, cành và rễ phơi khô",
        "recipes": [
            {
                "recipe_id": "rec_tra_ca_gai_leo_giai_doc_gan",
                "title": "Trà Cà Gai Leo Sao Thơm Mát Gan Giải Rượu",
                "category": "Thức uống bảo vệ tế bào nhu mô gan",
                "preparation_time": "20 phút",
                "target_benefit": "Hạ men gan, giải độc rượu bia tức thì, bảo vệ gan chống xơ gan và ức chế virus viêm gan",
                "ingredients": [
                    "Cà gai leo khô (thân và rễ sao vàng hạ thổ): 20–30g",
                    "Nước sạch: 1 lít"
                ],
                "step_by_step": [
                    "Bước 1: Lấy dược liệu cà gai leo khô rửa nhanh qua nước ấm để sạch bụi phấn phơi nắng, để ráo.",
                    "Bước 2: Cho cà gai leo vào ấm đun hoặc nồi gốm/inox sạch.",
                    "Bước 3: Rót 1 lít nước sạch vào đun trên lửa to đến khi sôi bùng lên.",
                    "Bước 4: Hạ lửa thật nhỏ, đậy nắp kín ấm và đun liu riu trong 10–15 phút để hoạt chất glycoalcaloid hòa tan hoàn toàn vào nước.",
                    "Bước 5: Tắt bếp, gạn lấy nước trà trong màu nâu cánh gián, có mùi thơm thảo mộc tự nhiên dịu nhẹ.",
                    "Bước 6: Rót ra ly uống ấm trong ngày hoặc uống trước/sau khi tiếp khách dùng bia rượu."
                ],
                "optimal_timing": "Uống rải rác sau bữa ăn hoặc trước khi đi ngủ, uống ngay sau chầu nhậu giúp giải rượu bảo vệ gan.",
                "cautions": "Phụ nữ mang thai hoặc đang cho con bú dưới 6 tháng không nên tự ý dùng đậm đặc."
            }
        ]
    },

    # 18. CHÈ VẰNG (Jasminum subtriplinerve)
    "che_vang": {
        "keywords": ["chè vằng", "vằng sẻ", "jasminum subtriplinerve", "dây vắng"],
        "parts_used": "Thân lá phơi sấy khô",
        "recipes": [
            {
                "recipe_id": "rec_che_vang_loi_sua_giam_can",
                "title": "Nước Chè Vằng Sẻ Hãm Ấm Lợi Sữa Co Tử Cung Sau Sinh",
                "category": "Nước uống thảo dược hồi phục sản phụ",
                "preparation_time": "15 phút",
                "target_benefit": "Kích thích tuyến sữa về dồi dào sánh đặc, hỗ trợ co hồi tử cung nhanh chóng, kháng viêm tiêu mỡ bụng sau sinh",
                "ingredients": [
                    "Chè vằng sẻ khô sạch: 20–30g (chọn loại vằng sẻ lá nhỏ thơm đắng)",
                    "Nước sôi già 100°C: 1 – 1.5 lít",
                    "Bình giữ nhiệt hoặc ấm ủ trà"
                ],
                "step_by_step": [
                    "Bước 1: Lấy chè vằng khô, cho vào rổ xả nhanh qua nước ấm để trôi bụi thảo dược.",
                    "Bước 2: Cho chè vằng vào ấm hãm hoặc bình giữ nhiệt dung tích 1.5 lít.",
                    "Bước 3: Rót khoảng 200ml nước sôi tráng đều rồi chắt bỏ nước đầu để kích thích hương vị trà.",
                    "Bước 4: Châm 1 lít nước sôi già vào bình, đậy kín nắp và ủ trong 20–30 phút cho trà ngấm.",
                    "Bước 5: Rót nước trà ra cốc, quan sát nước có màu vàng sẫm đẹp mắt, thoang thoảng mùi thơm đồng nội.",
                    "Bước 6: Uống khi nước còn ấm nóng, ban đầu có vị đắng nhẹ sau chuyển ngọt hậu sâu nơi cuống họng."
                ],
                "optimal_timing": "Uống thay nước lọc hàng ngày trong giai đoạn ở cữ cho con bú.",
                "cautions": "Phụ nữ ĐANG MANG THAI tuyệt đối không uống chè vằng vì có nguy cơ kích thích co bóp tử cung sảy thai."
            }
        ]
    },

    # 19. HOA HÒE (Styphnolobium japonicum / Sophora japonica)
    "hoa_hoe": {
        "keywords": ["hoa hòe", "hòe hoa", "styphnolobium japonicum", "sophora japonica"],
        "parts_used": "Nụ hoa chưa nở phơi khô sao vàng",
        "recipes": [
            {
                "recipe_id": "rec_tra_hoa_hoe_sao_vang_ha_huyet_ap",
                "title": "Trà Hoa Hòe Sao Vàng Bền Thành Mạch Hạ Huyết Áp",
                "category": "Thức uống dưỡng sinh tim mạch thanh can",
                "preparation_time": "15 phút",
                "target_benefit": "Lương huyết chỉ huyết, tăng cường độ bền thành mạch mao mạch nhờ Rutin tự nhiên, phòng ngừa tai biến và hạ áp",
                "ingredients": [
                    "Nụ hoa hòe khô đã sao vàng hạ thổ: 10–15g",
                    "Nước sôi già 95°C: 400ml",
                    "Ấm trà thủy tinh hoặc gốm sứ"
                ],
                "step_by_step": [
                    "Bước 1: Chuẩn bị hoa hòe đã sao vàng dậy mùi thơm như mùi cốm (nếu hoa hòe chưa sao cần cho lên chảo nóng đảo đều lửa nhỏ 2 phút).",
                    "Bước 2: Cho nụ hoa hòe vào ấm trà sạch.",
                    "Bước 3: Rót 100ml nước sôi vào lắc nhẹ tráng ấm rồi chắt bỏ nước tráng trong 10 giây.",
                    "Bước 4: Rót tiếp 300ml nước sôi già vào ấm, đậy nắp kín hãm trong 10–15 phút.",
                    "Bước 5: Nước trà tiết ra có màu vàng trong óng ánh rất đẹp mắt.",
                    "Bước 6: Rót ra chén thưởng thức từng ngụm ấm, cảm nhận hương thơm thoang thoảng ngọt bùi tự nhiên."
                ],
                "optimal_timing": "Uống sau bữa ăn sáng hoặc chiều, thích hợp cho người trung niên và cao tuổi huyết áp cao.",
                "cautions": "Người huyết áp thấp, cơ thể hay bị lạnh chân tay hoặc đi phân lỏng không nên dùng thường xuyên."
            }
        ]
    },

    # 20. SẮN DÂY (Pueraria montana / Pueraria thomsonii)
    "san_day": {
        "keywords": ["sắn dây", "cát căn", "pueraria", "pueraria montana", "pueraria thomsonii"],
        "parts_used": "Củ tươi phơi khô (Cát căn) hoặc tinh bột sắn dây ướp hoa bưởi",
        "recipes": [
            {
                "recipe_id": "rec_bot_san_day_chanh_thanh_nhiet",
                "title": "Nước Bột Sắn Dây Chanh Thanh Nhiệt Giải Độc Rượu",
                "category": "Thức uống dưỡng sinh giải nhiệt tán hỏa",
                "preparation_time": "5 phút",
                "target_benefit": "Thanh nhiệt tả hỏa, sinh tân chỉ khát, giải độc say nắng say rượu, trị rôm sảy nhức đầu nóng sốt",
                "ingredients": [
                    "Tinh bột sắn dây ta nguyên chất: 2 thìa canh (khoảng 20g)",
                    "Nước sôi để nguội: 150ml",
                    "Nước cốt chanh tươi: 1 thìa cà phê",
                    "Đường kính hoặc đường phèn: 1 thìa canh (tùy vị giác)"
                ],
                "step_by_step": [
                    "Bước 1: Cho bột sắn dây và đường vào ly thủy tinh sạch.",
                    "Bước 2: Rót 150ml nước lọc nguội vào ly, dùng thìa khuấy đều tay cho bột sắn tan mịn hoàn toàn không bị vón cục.",
                    "Bước 3: Vắt 1 thìa cà phê nước cốt chanh tươi qua rây vào ly, khuấy đều lần nữa.",
                    "Bước 4: Thưởng thức ngay từng ngụm mát lạnh thanh khiết (nếu người có cơ địa bụng yếu có thể hòa với nước sôi khuấy chín thành dạng súp trong suốt).",
                    "Bước 5: Uống nhấp từng ngụm giúp cơn khát và cảm giác nóng bức dịu đi nhanh chóng."
                ],
                "optimal_timing": "Uống vào đầu giờ chiều những ngày nắng gắt, hoặc ngay sau khi đi ngoài trời nắng to về bị háo nước.",
                "cautions": "Không uống quá 1 cốc mỗi ngày; người thể tạng hàn lạnh, trẻ nhỏ bụng yếu nên ăn bột quấy chín thay vì uống sống."
            }
        ]
    }
}

