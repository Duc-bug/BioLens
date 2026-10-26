from __future__ import annotations

import json
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageOps

from configs.settings import (
    MIN_BLUR_LAPLACIAN_VAR,
    MIN_BRIGHTNESS,
    MAX_BRIGHTNESS,
    OOD_CALIBRATION_PATH,
)

# Phân nhóm ngữ nghĩa trong 1,000 lớp chuẩn ImageNet-1K
# 1. Động vật có xương sống (chó, mèo, chim, cá, thú...) - KHÔNG phải thực vật/nấm
VERTEBRATE_ANIMAL_INDICES = set(range(0, 300)) | set(range(327, 398))

# 2. Côn trùng thường đậu trên hoa/lá (bướm, ong, bọ rùa...) - Cho phép xuất hiện trong ảnh chụp hoa
POLLINATOR_INSECT_INDICES = set(range(300, 327))

# 3. Các lớp Thực vật, Hoa, Quả, Lá, Nấm, Hạt và bối cảnh vườn thực vật
BOTANICAL_AND_FUNGI_INDICES = (
    set(range(936, 959))  # Rau củ quả, trái cây tự nhiên, bó cỏ
    | set(range(984, 999))  # Hoa cúc, hoa lan, cải dầu, quả sồi, tầm xuân, hạt dẻ, các loài nấm
    | {
        738,  # pot, flowerpot (chậu hoa/cây cảnh)
        883,  # vase (bình cắm hoa)
        580,  # greenhouse, nursery (nhà kính trồng cây)
        410,  # apiary (thùng ong vườn hoa)
        716,  # picket fence (hàng rào cây)
        912,  # worm fence (hàng rào gỗ)
        970, 972, 973, 975, 977, 978, 979, 980,  # Cảnh quan tự nhiên
    }
)

# 4. Các lớp Đồ vật nhân tạo, Nội thất, Điện tử, Phương tiện, Trang phục, Đồ ăn chế biến
MAN_MADE_AND_INDOOR_INDICES = (
    (set(range(398, 936)) | set(range(959, 970)) | {999})
    - BOTANICAL_AND_FUNGI_INDICES
)

# Từ khóa nhận diện nhanh nhóm vật thể ngoại lai để giải thích rõ bằng tiếng Việt
HUMAN_AND_CLOTHING_KEYWORDS = {
    "suit", "shirt", "jean", "sweatshirt", "cardigan", "jacket", "coat", "tie",
    "hat", "cap", "helmet", "sunglasses", "wig", "mask", "lab coat", "uniform",
    "pajama", "sock", "shoe", "sandal", "boot", "lipstick", "seat belt",
}
ELECTRONICS_KEYWORDS = {
    "monitor", "screen", "television", "laptop", "notebook", "desktop computer",
    "keyboard", "mouse", "cellular telephone", "iPod", "remote control", "modem",
    "printer", "joystick", "microphone", "loudspeaker", "camera", "oscilloscope",
}
FURNITURE_INDOOR_KEYWORDS = {
    "chair", "couch", "sofa", "desk", "table", "bed", "wardrobe", "bookcase",
    "cabinet", "curtain", "lamp", "pillow", "quilt", "refrigerator", "microwave",
    "stove", "washer", "bathtub", "toilet", "sink", "mug", "cup", "bottle",
    "plate", "bowl", "spoon", "fork", "knife", "book", "envelope", "pen", "pencil",
}
VEHICLE_BUILDING_KEYWORDS = {
    "car", "cab", "minivan", "limousine", "jeep", "truck", "trailer", "bus",
    "trolleybus", "train", "locomotive", "motorcycle", "moped", "bicycle",
    "tricycle", "airliner", "airplane", "helicopter", "boat", "ship", "bridge",
    "castle", "church", "mosque", "palace", "cinema", "library", "restaurant",
    "shop", "street", "traffic light",
}


class TwoStageOODFilter:
    """
    Hệ thống Kiểm duyệt 2 Tầng (2-Stage Out-of-Distribution Rejection):
    - Tiền kiểm tra: Độ nét (Blur), Độ sáng (Brightness), Độ tương phản.
    - Tầng 1 (Semantic Domain Gate): Phân biệt ảnh Thực vật/Hoa/Nấm với Đồ vật/Người/Xe cộ/Động vật.
    - Tầng 2 (Open-Set Similarity & Subspace Gate): Đối chiếu trong không gian 960 chiều của 3,570 loài.
    """

    def __init__(self, categories: List[str]) -> None:
        self.categories = categories
        self.min_cosine_sim = 0.43
        self.min_subspace_energy = 0.52
        self.global_mean: Optional[np.ndarray] = None
        self.principal_axes: Optional[np.ndarray] = None
        self._load_calibration()

    def _load_calibration(self) -> None:
        if OOD_CALIBRATION_PATH.exists():
            try:
                data = json.loads(OOD_CALIBRATION_PATH.read_text(encoding="utf-8"))
                self.min_cosine_sim = float(data.get("minCosineSim", 0.43))
                self.min_subspace_energy = float(data.get("minSubspaceEnergy", 0.52))
                if "globalMean" in data and "principalAxes" in data:
                    self.global_mean = np.array(data["globalMean"], dtype=np.float32)
                    self.principal_axes = np.array(data["principalAxes"], dtype=np.float32)
            except Exception:
                pass

    @staticmethod
    def check_image_quality(pil_img: Image.Image) -> Dict[str, Any]:
        """Kiểm tra chất lượng vật lý của ảnh (độ nét, độ sáng, độ tương phản)."""
        img_rgb = np.array(ImageOps.exif_transpose(pil_img).convert("RGB"))
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

        # Resize về kích thước chuẩn để tính phương sai Laplacian ổn định
        gray_resized = cv2.resize(gray, (384, 384))
        laplacian_var = float(cv2.Laplacian(gray_resized, cv2.CV_64F).var())
        mean_brightness = float(gray_resized.mean())
        std_contrast = float(gray_resized.std())

        # Tính tỉ lệ màu sắc tự nhiên (xanh lá, vàng/đỏ/hồng/tím hoa, nâu gỗ)
        hsv = cv2.cvtColor(cv2.resize(img_rgb, (256, 256)), cv2.COLOR_RGB2HSV)
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]
        colorful_ratio = float(np.mean((sat > 28) & (val > 30)))

        passed = True
        reason = "Chất lượng ảnh đạt chuẩn nhận diện."

        if mean_brightness < MIN_BRIGHTNESS:
            passed = False
            reason = "Ảnh quá tối (độ sáng trung bình quá thấp). Vui lòng chụp ở nơi đủ ánh sáng."
        elif mean_brightness > MAX_BRIGHTNESS and std_contrast < 8.0:
            passed = False
            reason = "Ảnh bị lóa trắng hoặc không có nội dung rõ ràng."
        elif std_contrast < 7.5:
            passed = False
            reason = "Ảnh đồng màu hoặc bị che khuất ống kính, không có chi tiết hình thái."
        elif laplacian_var < MIN_BLUR_LAPLACIAN_VAR:
            passed = False
            reason = f"Ảnh bị mờ nhòe (chỉ số độ nét {laplacian_var:.1f} < {MIN_BLUR_LAPLACIAN_VAR}). Vui lòng lấy nét rõ vào hoa hoặc lá."

        return {
            "passed": passed,
            "laplacianVar": round(laplacian_var, 2),
            "meanBrightness": round(mean_brightness, 2),
            "stdContrast": round(std_contrast, 2),
            "colorfulRatio": round(colorful_ratio, 3),
            "reason": reason,
        }

    def _explain_non_botanical_object(self, top_indices: List[int]) -> str:
        """Dịch tên lớp ImageNet ngoại lai sang lời giải thích tiếng Việt tự nhiên."""
        top_labels = [
            self.categories[i].lower() if i < len(self.categories) else f"class_{i}"
            for i in top_indices[:3]
        ]
        joined = " | ".join(top_labels)

        def has_kw(keywords: set[str]) -> bool:
            for lbl in top_labels:
                words = set(lbl.replace(",", " ").replace("-", " ").split())
                if (words & keywords) or (lbl in keywords):
                    return True
            return False

        if has_kw(ELECTRONICS_KEYWORDS):
            return f"Phát hiện thiết bị điện tử / màn hình ({top_labels[0]}), không phải sinh vật hay thực vật."
        if has_kw(FURNITURE_INDOOR_KEYWORDS):
            return f"Phát hiện đồ vật nội thất / vật dụng đời sống ({top_labels[0]}), không phải hoa hay thực vật."
        if has_kw(HUMAN_AND_CLOTHING_KEYWORDS):
            return f"Phát hiện con người / trang phục / phụ kiện ({top_labels[0]}), không thuộc phạm vi nhận diện thực vật."
        if has_kw(VEHICLE_BUILDING_KEYWORDS):
            return f"Phát hiện phương tiện giao thông / công trình kiến trúc ({top_labels[0]}), không phải thực vật."

        if top_indices[0] in VERTEBRATE_ANIMAL_INDICES:
            return f"Phát hiện động vật ({top_labels[0]}), không thuộc nhóm Thực vật & Nấm dược liệu Việt Nam."

        return f"Phát hiện vật thể ngoài phạm vi thực vật học ({joined})."

    def evaluate(
        self,
        pil_img: Image.Image,
        feat_norm: np.ndarray,
        probs_1000: np.ndarray,
        max_prototype_cosine: float,
        top1_confidence: float,
        top1_margin: float,
    ) -> Dict[str, Any]:
        """
        Đánh giá toàn diện qua 2 tầng lọc OOD:
        Trả về trạng thái isAccepted (True/False) cùng điểm số chi tiết của từng tầng.
        """
        # Bước 0: Kiểm tra chất lượng ảnh
        quality = self.check_image_quality(pil_img)
        if not quality["passed"]:
            return {
                "isAccepted": False,
                "rejectedStage": "STAGE_0_IMAGE_QUALITY",
                "rejectionReason": quality["reason"],
                "qualityMetrics": quality,
                "stage1DomainGate": {"passed": False, "botanicalScore": 0.0},
                "stage2ConfidenceGate": {"passed": False, "maxCosineSimilarity": round(max_prototype_cosine, 4)},
            }

        # Bước 1: Semantic Domain Gate (Lọc miền Thực vật / Nấm so với Vật thể nhân tạo / Động vật)
        prob_botanical = float(sum(probs_1000[i] for i in BOTANICAL_AND_FUNGI_INDICES))
        prob_pollinator = float(sum(probs_1000[i] for i in POLLINATOR_INSECT_INDICES))
        prob_vertebrate = float(sum(probs_1000[i] for i in VERTEBRATE_ANIMAL_INDICES))
        prob_man_made = float(sum(probs_1000[i] for i in MAN_MADE_AND_INDOOR_INDICES))

        top5_imagenet_idx = np.argsort(probs_1000)[::-1][:5].tolist()
        top5_imagenet_labels = [
            {
                "label": self.categories[i] if i < len(self.categories) else str(i),
                "prob": round(float(probs_1000[i]), 4),
            }
            for i in top5_imagenet_idx
        ]

        # Tính năng lượng chiếu lên không gian con thực vật học (Subspace Projection Energy)
        subspace_energy = float(max_prototype_cosine)
        if self.principal_axes is not None and self.global_mean is not None:
            centered = feat_norm - self.global_mean
            centered_norm = centered / (np.linalg.norm(centered) + 1e-8)
            proj = self.principal_axes @ centered_norm
            subspace_energy = float(np.linalg.norm(proj))

        # Điểm tổng hợp miền sinh vật học (Botanical Domain Score)
        # Lưu ý: ImageNet-1K chỉ có một vài lớp hoa nên nhiều loài hoa nhiệt đới sẽ có xác suất ImageNet phân tán (top1_prob thấp).
        # Ngược lại, nếu chụp đồ vật nhân tạo/động vật thật, xác suất Top-3 của nhóm ngoại lai sẽ tập trung rất cao (> 0.50).
        top3_non_bio_prob = float(
            sum(
                probs_1000[i]
                for i in top5_imagenet_idx[:3]
                if i in MAN_MADE_AND_INDOOR_INDICES or i in VERTEBRATE_ANIMAL_INDICES
            )
        )

        botanical_domain_score = min(
            0.99,
            0.45 * min(1.0, max(0.0, (max_prototype_cosine - 0.25) / 0.45))
            + 0.35 * min(1.0, subspace_energy / 0.80)
            + 0.20 * max(0.0, 1.0 - top3_non_bio_prob),
        )

        # Quy tắc từ chối ở Tầng 1:
        stage1_passed = True
        stage1_reason = "Ảnh thuộc miền Thực vật / Sinh vật tự nhiên hợp lệ."

        if top3_non_bio_prob > 0.52 and prob_botanical < 0.08 and max_prototype_cosine < 0.56:
            stage1_passed = False
            stage1_reason = self._explain_non_botanical_object(top5_imagenet_idx)
        elif botanical_domain_score < 0.36 and max_prototype_cosine < 0.46:
            stage1_passed = False
            stage1_reason = self._explain_non_botanical_object(top5_imagenet_idx)

        stage1_info = {
            "passed": stage1_passed,
            "botanicalDomainScore": round(botanical_domain_score, 4),
            "probBotanicalAndFungi": round(prob_botanical, 4),
            "probManMadeObject": round(prob_man_made, 4),
            "probVertebrateAnimal": round(prob_vertebrate, 4),
            "subspaceEnergy": round(subspace_energy, 4),
            "topImageNetConcepts": top5_imagenet_labels[:3],
            "reason": stage1_reason,
        }

        if not stage1_passed:
            return {
                "isAccepted": False,
                "rejectedStage": "STAGE_1_DOMAIN_GATE",
                "rejectionReason": stage1_reason,
                "qualityMetrics": quality,
                "stage1DomainGate": stage1_info,
                "stage2ConfidenceGate": {
                    "passed": False,
                    "maxCosineSimilarity": round(max_prototype_cosine, 4),
                    "threshold": round(self.min_cosine_sim, 4),
                },
            }

        # Bước 2: Open-Set Species Confidence Gate (Kiểm tra độ tương đồng với 3,570 loài)
        stage2_passed = True
        stage2_reason = "Độ tương đồng đặc trưng đạt chuẩn nhận diện trong CSDL 3,570 loài."

        # Nếu ảnh có một phần vật thể nhân tạo lấn át và độ tương đồng cosine thấp
        effective_threshold = self.min_cosine_sim
        if prob_man_made > 0.40 and prob_botanical < 0.15:
            effective_threshold = max(effective_threshold, 0.49)

        if max_prototype_cosine < effective_threshold:
            stage2_passed = False
            if prob_man_made > 0.35 or prob_vertebrate > 0.30:
                stage2_reason = (
                    self._explain_non_botanical_object(top5_imagenet_idx)
                    + f" (Độ tương đồng thực vật học {max_prototype_cosine:.2f} < ngưỡng {effective_threshold:.2f})."
                )
            else:
                stage2_reason = (
                    f"Không nhận diện được chính xác loài này: Độ tương đồng hình thái đạt {max_prototype_cosine * 100:.1f}% "
                    f"(thấp hơn ngưỡng an toàn {effective_threshold * 100:.1f}%). Có thể ảnh chụp quá xa, góc chụp khuất "
                    f"hoặc loài sinh vật này nằm ngoài 3,570 loài của bộ dữ liệu VietMediSpecies2026."
                )

        stage2_info = {
            "passed": stage2_passed,
            "maxCosineSimilarity": round(max_prototype_cosine, 4),
            "effectiveThreshold": round(effective_threshold, 4),
            "top1Confidence": round(top1_confidence, 4),
            "top1Margin": round(top1_margin, 4),
            "reason": stage2_reason,
        }

        return {
            "isAccepted": stage2_passed,
            "rejectedStage": None if stage2_passed else "STAGE_2_OPENSET_THRESHOLD",
            "rejectionReason": None if stage2_passed else stage2_reason,
            "qualityMetrics": quality,
            "stage1DomainGate": stage1_info,
            "stage2ConfidenceGate": stage2_info,
        }
