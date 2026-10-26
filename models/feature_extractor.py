from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image, ImageOps

from configs.settings import (
    DATASET_ROOT,
    DEVICE,
    USE_FP16,
    IMAGE_SIZE,
    BATCH_SIZE,
    NUM_WORKERS,
    DATASET_SPLITS_PATH,
    EMBEDDINGS_MATRIX_PATH,
    EMBEDDINGS_LABELS_PATH,
    EMBEDDINGS_SPLITS_PATH,
    EMBEDDINGS_PATHS_PATH,
    EMBEDDINGS_META_PATH,
)


def get_eval_transform(image_size: int = IMAGE_SIZE) -> transforms.Compose:
    """Chuẩn hóa ảnh đầu vào theo chuẩn ImageNet."""
    return transforms.Compose(
        [
            transforms.Resize(int(image_size * 1.14), interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


class BotanicalDualBackbone(nn.Module):
    """
    Mô hình trích xuất kép:
    - Trả về vector đặc trưng sâu 960 chiều đã chuẩn hóa L2 (dùng cho 4 thuật toán Học máy trên 3,570 loài)
    - Trả về logits 1,000 lớp ImageNet (hỗ trợ Bộ lọc Tầng 1 phát hiện đồ vật, xe cộ, động vật, màn hình...)
    """

    def __init__(self, device: str = DEVICE) -> None:
        super().__init__()
        self.device = torch.device(device)
        weights = models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        base_model = models.mobilenet_v3_large(weights=weights)
        self.features = base_model.features
        self.avgpool = base_model.avgpool
        # Lớp chiếu đặc trưng 960 -> 1280 và lớp phân loại 1280 -> 1000
        self.proj_linear = base_model.classifier[0]
        self.proj_act = base_model.classifier[1]
        self.cls_head = base_model.classifier[3]
        self.categories: List[str] = list(weights.meta.get("categories", []))
        self.feature_dim = 960
        self.to(self.device)
        self.eval()

    @torch.no_grad()
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.features(x)
        x = self.avgpool(x)
        feat_960 = torch.flatten(x, 1)
        feat_norm = F.normalize(feat_960.float(), p=2, dim=1)

        hidden = self.proj_act(self.proj_linear(feat_960))
        logits_1000 = self.cls_head(hidden).float()
        return feat_norm, logits_1000

    @torch.no_grad()
    def extract_single_pil(self, pil_img: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
        """Trích xuất vector đặc trưng (960,) và xác suất ngữ nghĩa ImageNet (1000,) cho 1 ảnh PIL."""
        img = ImageOps.exif_transpose(pil_img).convert("RGB")
        tf = get_eval_transform(IMAGE_SIZE)
        tensor = tf(img).unsqueeze(0).to(self.device)
        if USE_FP16 and self.device.type == "cuda":
            with torch.amp.autocast("cuda", dtype=torch.float16):
                feat_norm, logits_1000 = self.forward(tensor)
        else:
            feat_norm, logits_1000 = self.forward(tensor)
        probs_1000 = F.softmax(logits_1000, dim=1)
        return (
            feat_norm[0].cpu().numpy().astype(np.float32),
            probs_1000[0].cpu().numpy().astype(np.float32),
        )


class ManifestImageDataset(Dataset):
    """Dataset đọc ảnh từ manifest của 3,570 loài, tự động xử lý ảnh lỗi nếu có."""

    def __init__(self, manifest: List[Tuple[str, int, int]], root_dir: Path = DATASET_ROOT) -> None:
        self.manifest = manifest
        self.root_dir = root_dir
        self.transform = get_eval_transform(IMAGE_SIZE)

    def __len__(self) -> int:
        return len(self.manifest)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, int, int]:
        rel_path, class_idx, split_code = self.manifest[idx]
        full_path = self.root_dir / rel_path
        try:
            with Image.open(full_path) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                tensor = self.transform(im)
            valid = 1
        except Exception:
            tensor = torch.zeros((3, IMAGE_SIZE, IMAGE_SIZE), dtype=torch.float32)
            valid = 0
        return tensor, class_idx, split_code, valid


def extract_dataset_embeddings(
    batch_size: int = BATCH_SIZE,
    num_workers: int = NUM_WORKERS,
    force_recompute: bool = False,
) -> Dict[str, Any]:
    """
    Trích xuất toàn bộ vector đặc trưng cho tập dữ liệu với tăng tốc phần cứng CUDA.
    Lưu kết quả dưới dạng ma trận FP16 (.npy) siêu gọn nhẹ.
    """
    splits_data = json.loads(DATASET_SPLITS_PATH.read_text(encoding="utf-8"))
    manifest: List[Tuple[str, int, int]] = splits_data["manifest"]
    total_samples = len(manifest)

    if (
        not force_recompute
        and EMBEDDINGS_MATRIX_PATH.exists()
        and EMBEDDINGS_LABELS_PATH.exists()
        and EMBEDDINGS_SPLITS_PATH.exists()
        and EMBEDDINGS_META_PATH.exists()
    ):
        meta = json.loads(EMBEDDINGS_META_PATH.read_text(encoding="utf-8"))
        if int(meta.get("numTotalManifest", 0)) == total_samples:
            print(f"[Info] Đã có sẵn trọn bộ {meta['numValidSamples']:,} embeddings tại {EMBEDDINGS_MATRIX_PATH}")
            return meta

    # Kiểm tra xem có thể kế thừa các vector đã trích xuất trước đó không (Incremental Extraction)
    existing_path_to_idx: Dict[str, int] = {}
    existing_feats: Optional[np.ndarray] = None
    prev_time_sec = 0.0
    if (
        not force_recompute
        and EMBEDDINGS_MATRIX_PATH.exists()
        and EMBEDDINGS_PATHS_PATH.exists()
    ):
        try:
            prev_paths = json.loads(EMBEDDINGS_PATHS_PATH.read_text(encoding="utf-8"))
            existing_feats = np.load(EMBEDDINGS_MATRIX_PATH)
            if len(prev_paths) == existing_feats.shape[0]:
                existing_path_to_idx = {p: idx for idx, p in enumerate(prev_paths)}
                if EMBEDDINGS_META_PATH.exists():
                    prev_meta = json.loads(EMBEDDINGS_META_PATH.read_text(encoding="utf-8"))
                    prev_time_sec = float(prev_meta.get("extractionTimeSeconds", 0.0))
                print(
                    f"[Incremental] Tái sử dụng {len(existing_path_to_idx):,} vector đã trích xuất, "
                    f"chỉ trích xuất bổ sung {total_samples - len(existing_path_to_idx):,} ảnh còn lại..."
                )
        except Exception:
            existing_path_to_idx = {}
            existing_feats = None

    print(f"[GPU] Khởi tạo BotanicalDualBackbone trên thiết bị: {DEVICE} (FP16={USE_FP16})")
    backbone = BotanicalDualBackbone(device=DEVICE)
    feat_dim = backbone.feature_dim

    all_features = np.zeros((total_samples, feat_dim), dtype=np.float16)
    all_labels = np.zeros((total_samples,), dtype=np.int32)
    all_splits = np.zeros((total_samples,), dtype=np.uint8)
    valid_mask = np.zeros((total_samples,), dtype=bool)

    missing_manifest: List[Tuple[str, int, int]] = []
    missing_target_indices: List[int] = []

    for idx_m, (rel_p, c_idx, s_code) in enumerate(manifest):
        all_labels[idx_m] = c_idx
        all_splits[idx_m] = s_code
        prev_i = existing_path_to_idx.get(rel_p)
        if prev_i is not None and existing_feats is not None:
            all_features[idx_m] = existing_feats[prev_i]
            valid_mask[idx_m] = True
        else:
            missing_manifest.append((rel_p, c_idx, s_code))
            missing_target_indices.append(idx_m)

    num_missing = len(missing_manifest)
    t0 = time.time()

    if num_missing > 0:
        dataset = ManifestImageDataset(missing_manifest, root_dir=DATASET_ROOT)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=(DEVICE == "cuda"),
            persistent_workers=(num_workers > 0),
        )
        cursor = 0
        num_batches = len(loader)

        for b_idx, (tensors, cls_indices, split_codes, valids) in enumerate(loader):
            bsz = tensors.size(0)
            tensors = tensors.to(backbone.device, non_blocking=True)

            if USE_FP16 and backbone.device.type == "cuda":
                with torch.amp.autocast("cuda", dtype=torch.float16):
                    feats, _ = backbone(tensors)
            else:
                feats, _ = backbone(tensors)

            feats_np = feats.cpu().numpy().astype(np.float16)
            valids_np = valids.numpy().astype(bool)
            batch_targets = missing_target_indices[cursor : cursor + bsz]
            all_features[batch_targets] = feats_np
            valid_mask[batch_targets] = valids_np
            cursor += bsz

            if (b_idx + 1) % 50 == 0 or (b_idx + 1) == num_batches:
                elapsed = time.time() - t0
                speed = cursor / max(1e-5, elapsed)
                eta = (num_missing - cursor) / max(1e-5, speed)
                print(
                    f"  -> Batch [{b_idx + 1:>4}/{num_batches}] | "
                    f"Đã xử lý mới: {cursor:>7,}/{num_missing:,} ảnh ({cursor * 100.0 / num_missing:5.1f}%) | "
                    f"Tổng: {len(existing_path_to_idx) + cursor:,}/{total_samples:,} | "
                    f"Tốc độ: {speed:6.1f} ảnh/s | ETA: {eta:5.1f}s",
                    flush=True,
                )

    # Lọc các ảnh hợp lệ
    all_features = all_features[valid_mask]
    all_labels = all_labels[valid_mask]
    all_splits = all_splits[valid_mask]
    valid_paths = [manifest[i][0] for i in range(total_samples) if valid_mask[i]]

    np.save(EMBEDDINGS_MATRIX_PATH, all_features)
    np.save(EMBEDDINGS_LABELS_PATH, all_labels)
    np.save(EMBEDDINGS_SPLITS_PATH, all_splits)
    EMBEDDINGS_PATHS_PATH.write_text(json.dumps(valid_paths), encoding="utf-8")

    total_time = round(prev_time_sec + (time.time() - t0), 2)
    meta = {
        "backbone": "MobileNetV3-Large (IMAGENET1K_V2)",
        "device": "CUDA GPU Acceleration (FP16)" if torch.cuda.is_available() else "CPU",
        "featureDim": feat_dim,
        "numTotalManifest": total_samples,
        "numValidSamples": int(all_features.shape[0]),
        "numCorruptedSkipped": int(total_samples - all_features.shape[0]),
        "extractionTimeSeconds": total_time,
        "throughputImagesPerSec": round(int(all_features.shape[0]) / max(1e-5, total_time), 2),
    }
    EMBEDDINGS_META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta
