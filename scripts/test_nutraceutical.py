"""
Script Kiem thu He thong Duoc thien (Nutraceutical Recommender Integration Test)
Kiem tra tinh dung dan cua toan bo pipeline: Safety Gating, Recommendation, Search.
"""
import sys
from pathlib import Path

# Thêm đường dẫn project
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.nutraceutical_engine import NutraceuticalEngine


def run_tests():
    print("==================================================")
    print("🧪 BẮT ĐẦU KIỂM THỬ NUTRACEUTICAL RECOMMENDER")
    print("==================================================")

    engine = NutraceuticalEngine()
    assert len(engine._registry) > 0, "Database trống!"
    print(f"✅ 1. Database nạp thành công: {len(engine._registry)} loài.")

    # Test 2: Thử nghiệm loài Dược thực đồng nguyên (Sâm bố chính - 3940600)
    res_safe = engine.recommend_for_species("3940600")
    assert res_safe["success"] is True, "Lỗi truy vấn Sâm bố chính"
    assert res_safe["isSafe"] is True, "Sâm bố chính phải an toàn!"
    assert len(res_safe["recipes"]) > 0, "Phải có công thức nấu ăn cho Sâm bố chính"
    print(f"✅ 2. Test loài an toàn (Sâm bố chính):")
    print(f"   - Phân hạng: {res_safe['edibilityGrade']}")
    print(f"   - Số công thức sinh ra: {len(res_safe['recipes'])}")
    print(f"   - Món tiêu biểu: {res_safe['recipes'][0]['title']}")

    # Test 3: Thử nghiệm loài có độc (Tìm loài độc trong registry)
    toxic_key = None
    for k, v in engine._registry.items():
        if v.get("isToxic") and "ngón" in v.get("primaryVietnameseName", "").lower():
            toxic_key = k
            break
    if not toxic_key:
        for k, v in engine._registry.items():
            if v.get("isToxic"):
                toxic_key = k
                break

    assert toxic_key is not None, "Không tìm thấy loài độc nào trong registry!"
    res_toxic = engine.recommend_for_species(toxic_key)
    assert res_toxic["isSafe"] is False, "Bộ lọc độc tính thất bại!"
    assert res_toxic["alertLevel"] == "DANGER_CRITICAL", "Mức độ cảnh báo phải là DANGER_CRITICAL!"
    assert len(res_toxic["recipes"]) == 0, "Cây độc tuyệt đối không được có công thức ăn uống!"
    print(f"✅ 3. Test loài có độc (Mã {toxic_key} - {engine._registry[toxic_key].get('primaryVietnameseName')}):")
    print(f"   - Chặn thành công: isSafe = {res_toxic['isSafe']}")
    print(f"   - Cảnh báo: {res_toxic['warningTitle']}")
    print(f"   - Số công thức: {len(res_toxic['recipes'])} (Chặn 100%)")

    # Test 4: Thử nghiệm tìm kiếm theo triệu chứng ("mất ngủ", "nóng trong")
    search_res = engine.search_by_symptom("mất ngủ", top_k=5)
    assert len(search_res) > 0, "Không tìm thấy kết quả cho triệu chứng mất ngủ!"
    print(f"✅ 4. Test tìm kiếm theo triệu chứng 'mất ngủ':")
    print(f"   - Tìm thấy: {len(search_res)} loài thảo dược bổ trợ")
    for idx, c in enumerate(search_res[:3], 1):
        print(f"     {idx}. {c['primaryVietnameseName']} ({c['canonicalName']}) - Điểm: {c['relevanceScore']}")

    # Test 5: Metadata
    meta = engine.get_categories_metadata()
    assert len(meta["healthGoals"]) == 12, "Phải có đúng 12 thể trạng sức khỏe!"
    print(f"✅ 5. Test Metadata: Có đầy đủ {len(meta['healthGoals'])} thể trạng và {len(meta['edibilityGrades'])} phân hạng ẩm thực.")

    print("\n🎉 TOÀN BỘ 5/5 BÀI TEST TÍCH HỢP ĐỀU ĐẠT CHUẨN XUẤT SẮC!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
