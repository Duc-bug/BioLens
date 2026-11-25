from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image, ImageOps

from configs.settings import (
    MAX_BRIGHTNESS,
    MIN_BLUR_LAPLACIAN_VAR,
    MIN_BRIGHTNESS,
    OOD_CALIBRATION_PATH,
)

# Bản đồ thông báo tiếng Việt cho từng nhóm khái niệm ngoài miền của BioCLIP 2 Text Encoder
NON_BOTANICAL_GROUP_MESSAGES = {
    "human": "Phát hiện con người hoặc trang phục, không thuộc phạm vi nhận diện thực vật & nấm dược liệu.",
    "electronics": "Phát hiện thiết bị điện tử hoặc màn hình, không phải thực vật hay nấm.",
    "furniture": "Phát hiện đồ vật nội thất / vật dụng trong nhà, không phải thực vật.",
    "vehicle": "Phát hiện phương tiện giao thông hoặc công trình nhân tạo, không phải thực vật.",
    "animal": "Phát hiện động vật, không thuộc nhóm thực vật và nấm dược liệu Việt Nam.",
    "document": "Phát hiện ảnh chụp văn bản, sơ đồ hoặc giao diện trang web, không phải mẫu thực vật.",
}


class TwoStageOODFilter:
    """
    Bộ lọc từ chối ảnh ngoài miền dựa trực tiếp trên BioCLIP 2:
    - Bước tiền kiểm (STAGE_0): Độ nét Laplacian, độ sáng, độ tương phản.
    - Tầng 1 (STAGE_1): So khớp ngữ nghĩa Zero-Shot bằng Text Encoder của BioCLIP 2
      (nhóm Thực vật/Nấm so với Người/Thiết bị/Nội thất/Phương tiện/Động vật/Tài liệu).
    - Tầng 2 (STAGE_2): Kiểm tra độ tương đồng Cosine lớn nhất với tâm cụm 3,570 loài.
    """

    def __init__(self, categories: List[str], domain_groups: Optional[List[str]] = None) -> None:
        self.categories = categories
        self.domain_groups = domain_groups or []
        self.min_cosine_sim = 0.74
        self.min_subspace_energy = 0.62
        self.min_max_logit = 6.5
        self.global_mean: Optional[np.ndarray] = None
        self.principal_axes: Optional[np.ndarray] = None
        self._load_calibration()

    def _load_calibration(self) -> None:
        if OOD_CALIBRATION_PATH.exists():
            try:
                data = json.loads(OOD_CALIBRATION_PATH.read_text(encoding="utf-8"))
                cal_th = float(data.get("minCosineSim", 0.48))
                # BioCLIP 2 có phân bố ảnh thực vật thật rất cao (mean=0.8946, std=0.0424);
                # dùng chặn dưới 3.5-sigma của ảnh thực vật thật để chặn ảnh người/đồ vật tự nhiên
                if "inDistMeanCosine" in data and "inDistStdCosine" in data:
                    real_lower = float(data["inDistMeanCosine"]) - 3.5 * float(data["inDistStdCosine"])
                    self.min_cosine_sim = round(max(cal_th, min(0.76, real_lower)), 4)
                else:
                    self.min_cosine_sim = max(0.74, cal_th)
                if "globalMean" in data and "principalAxes" in data:
                    self.global_mean = np.array(data["globalMean"], dtype=np.float32)
                    self.principal_axes = np.array(data["principalAxes"], dtype=np.float32)
            except Exception:
                pass

    @staticmethod
    def check_image_quality(pil_img: Image.Image) -> Dict[str, Any]:
        img_rgb = np.array(ImageOps.exif_transpose(pil_img).convert("RGB"))
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        gray_resized = cv2.resize(gray, (384, 384))
        laplacian_var = float(cv2.Laplacian(gray_resized, cv2.CV_64F).var())
        mean_brightness = float(gray_resized.mean())
        std_contrast = float(gray_resized.std())

        passed = True
        reason = "Chất lượng ảnh đạt yêu cầu nhận diện."
        if mean_brightness < MIN_BRIGHTNESS:
            passed = False
            reason = "Ảnh quá tối. Vui lòng chụp ở nơi đủ ánh sáng."
        elif mean_brightness > MAX_BRIGHTNESS and std_contrast < 8.0:
            passed = False
            reason = "Ảnh bị lóa trắng hoặc không có chi tiết rõ ràng."
        elif std_contrast < 7.5:
            passed = False
            reason = "Ảnh đồng màu hoặc bị che khuất ống kính."
        elif laplacian_var < MIN_BLUR_LAPLACIAN_VAR:
            passed = False
            reason = f"Ảnh bị mờ nhòe (độ nét {laplacian_var:.1f} < {MIN_BLUR_LAPLACIAN_VAR}). Vui lòng lấy nét rõ vào mẫu cây."

        return {
            "passed": passed,
            "laplacianVar": round(laplacian_var, 2),
            "meanBrightness": round(mean_brightness, 2),
            "stdContrast": round(std_contrast, 2),
            "reason": reason,
        }

    def evaluate(
        self,
        pil_img: Image.Image,
        feat_norm: np.ndarray,
        probs_domain: np.ndarray,
        max_prototype_cosine: float,
        top1_confidence: float,
        top1_margin: float,
        max_clf_logit: Optional[float] = None,
    ) -> Dict[str, Any]:
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

        prob_botanical = 0.0
        prob_non_bio = 0.0
        best_non_bio_group = "other"
        best_non_bio_val = -1.0

        for idx, p in enumerate(probs_domain.tolist()):
            grp = self.domain_groups[idx] if idx < len(self.domain_groups) else "other"
            if grp in ("botanical", "pollinator"):
                prob_botanical += float(p)
            else:
                prob_non_bio += float(p)
                if float(p) > best_non_bio_val:
                    best_non_bio_val = float(p)
                    best_non_bio_group = grp

        subspace_energy = float(max_prototype_cosine)
        has_pca = (
            self.principal_axes is not None
            and self.global_mean is not None
            and self.global_mean.shape[0] == feat_norm.shape[0]
        )
        if has_pca:
            centered = feat_norm - self.global_mean
            centered_norm = centered / (np.linalg.norm(centered) + 1e-8)
            subspace_energy = float(np.linalg.norm(self.principal_axes @ centered_norm))

        stage1_passed = True
        stage1_reason = "Ảnh thuộc miền thực vật / nấm hợp lệ."
        if len(probs_domain) > 0 and prob_non_bio > 0.55 and prob_botanical < 0.45:
            stage1_passed = False
            stage1_reason = NON_BOTANICAL_GROUP_MESSAGES.get(
                best_non_bio_group,
                "Phát hiện vật thể ngoài phạm vi thực vật và nấm dược liệu.",
            )
        elif has_pca and subspace_energy < self.min_subspace_energy:
            stage1_passed = False
            stage1_reason = (
                f"Phát hiện đối tượng ngoài miền thực vật và nấm (năng lượng không gian thực vật "
                f"{subspace_energy * 100:.1f}% < {self.min_subspace_energy * 100:.1f}%)."
            )

        stage1_info = {
            "passed": stage1_passed,
            "botanicalDomainScore": round(prob_botanical, 4),
            "probNonBotanical": round(prob_non_bio, 4),
            "subspaceEnergy": round(subspace_energy, 4),
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

        effective_threshold = self.min_cosine_sim
        logit_ok = True if max_clf_logit is None else (max_clf_logit >= self.min_max_logit)
        cos_ok = max_prototype_cosine >= effective_threshold
        stage2_passed = cos_ok and logit_ok

        if stage2_passed:
            stage2_reason = "Độ tương đồng đặc trưng đạt ngưỡng nhận diện trong 3,570 loài."
        elif not cos_ok:
            stage2_reason = (
                f"Độ tương đồng hình thái đạt {max_prototype_cosine * 100:.1f}% "
                f"(thấp hơn ngưỡng an toàn {effective_threshold * 100:.1f}%). "
                "Ảnh không khớp rõ ràng với 3,570 loài thực vật và nấm trong cơ sở dữ liệu."
            )
        else:
            stage2_reason = (
                f"Độ tự tin phân loại quá thấp (MaxLogit {max_clf_logit:.2f} < {self.min_max_logit:.1f}). "
                "Đối tượng có thể nằm ngoài danh mục 3,570 loài thực vật và nấm."
            )

        return {
            "isAccepted": stage2_passed,
            "rejectedStage": None if stage2_passed else "STAGE_2_OPENSET_THRESHOLD",
            "rejectionReason": None if stage2_passed else stage2_reason,
            "qualityMetrics": quality,
            "stage1DomainGate": stage1_info,
            "stage2ConfidenceGate": {
                "passed": stage2_passed,
                "maxCosineSimilarity": round(max_prototype_cosine, 4),
                "threshold": round(effective_threshold, 4),
                "effectiveThreshold": round(effective_threshold, 4),
                "maxLogit": round(max_clf_logit, 3) if max_clf_logit is not None else None,
                "top1Confidence": round(top1_confidence, 4),
                "top1Margin": round(top1_margin, 4),
                "reason": stage2_reason,
            },
        }
