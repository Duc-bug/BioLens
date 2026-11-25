from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageOps
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from configs.settings import (
    BATCH_SIZE,
    BIOCLIP_MODEL_ID,
    DATASET_ROOT,
    DATASET_SPLITS_PATH,
    DEVICE,
    DOMAIN_TEXT_EMB_PATH,
    EMBEDDINGS_LABELS_PATH,
    EMBEDDINGS_MATRIX_PATH,
    EMBEDDINGS_META_PATH,
    EMBEDDINGS_PATHS_PATH,
    EMBEDDINGS_SPLITS_PATH,
    IMAGE_SIZE,
    NUM_WORKERS,
    SPECIES_CATALOG_PATH,
    SPECIES_TEXT_EMB_PATH,
    USE_FLIP_TTA,
    USE_FP16,
)

CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)

# Các khái niệm ngôn ngữ phục vụ Bộ lọc OOD Tầng 1 ngay trên chính BioCLIP 2
OOD_DOMAIN_CONCEPTS: List[Tuple[str, str, str]] = [
    ("botanical", "plant_leaf_stem", "a photo of a green plant, leaves, stem, or medicinal herb in nature"),
    ("botanical", "flower_blossom", "a close-up photo of a flower, blossom, petals, or inflorescence"),
    ("botanical", "fruit_seed_root", "a photo of plant fruits, seeds, bark, roots, or botanical specimen"),
    ("botanical", "fungi_mushroom", "a photo of a mushroom, wild fungus, or lichen growing on wood or soil"),
    ("pollinator", "insect_on_plant", "a small butterfly or bee resting on a flower or leaf"),
    ("human", "person_face_body", "a photo of a human person, face, portrait, selfie, or clothing"),
    ("electronics", "screen_device", "a photo of a computer monitor, laptop, smartphone screen, or electronics"),
    ("furniture", "indoor_object", "a photo of indoor furniture, table, chair, cup, bottle, or room interior"),
    ("vehicle", "vehicle_building", "a photo of a car, motorcycle, street, house, or man-made building"),
    ("animal", "vertebrate_animal", "a photo of a dog, cat, bird, fish, or domestic animal"),
    ("document", "text_screenshot", "a screenshot of text, document, diagram, or webpage"),
]


def get_eval_transform(image_size: int = IMAGE_SIZE) -> transforms.Compose:
    """Chuẩn hóa ảnh đầu vào cho BioCLIP 2 (Bicubic co giãn cạnh ngắn + CenterCrop + CLIP Normalize)."""
    return transforms.Compose(
        [
            transforms.Resize(
                int(round(image_size * 1.05)),
                interpolation=transforms.InterpolationMode.BICUBIC,
                antialias=True,
            ),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=CLIP_MEAN, std=CLIP_STD),
        ]
    )


def build_species_prompts(sp: Dict[str, Any]) -> List[str]:
    """Tạo câu mô tả phân loại học chuẩn GBIF cho Text Encoder của BioCLIP 2."""
    parts = [
        sp.get("kingdom", ""),
        sp.get("class", ""),
        sp.get("order", ""),
        sp.get("family", ""),
        sp.get("genus", ""),
    ]
    tax_chain = " ".join(p.strip() for p in parts if p and p.strip())
    canon = (sp.get("canonicalName") or sp.get("scientificName") or "").strip()
    prompts = []
    if tax_chain and canon:
        prompts.append(f"a photo of {tax_chain} {canon}")
    if canon:
        prompts.append(f"a photo of {canon}")
    if not prompts:
        prompts.append("a photo of a plant species")
    return prompts


class BotanicalBioCLIP2Backbone(nn.Module):
    """
    Mô hình nền duy nhất của hệ thống: BioCLIP 2 (hf-hub:imageomics/bioclip-2, ViT-L/14, 768 chiều).
    Cung cấp cả biểu diễn hình ảnh (768d) và kiểm định ngữ nghĩa OOD bằng Text Encoder của BioCLIP 2.
    """

    def __init__(self, device: str = DEVICE, load_text_if_needed: bool = True) -> None:
        super().__init__()
        import open_clip

        self.device = torch.device(device)
        model, _, _ = open_clip.create_model_and_transforms(BIOCLIP_MODEL_ID)
        self.model = model
        self.tokenizer = open_clip.get_tokenizer(BIOCLIP_MODEL_ID)
        self.feature_dim = 768
        self.transform = get_eval_transform(IMAGE_SIZE)

        self.to(self.device)
        self.eval()

        self.domain_groups: List[str] = [c[0] for c in OOD_DOMAIN_CONCEPTS]
        self.categories: List[str] = [c[1] for c in OOD_DOMAIN_CONCEPTS]
        self.domain_text_Matrix: Optional[torch.Tensor] = None
        if load_text_if_needed:
            self._init_domain_text_embeddings()

    @torch.no_grad()
    def _init_domain_text_embeddings(self) -> None:
        if DOMAIN_TEXT_EMB_PATH.exists():
            try:
                npz = np.load(DOMAIN_TEXT_EMB_PATH)
                self.domain_text_Matrix = torch.from_numpy(npz["text_embs"].astype(np.float32)).to(self.device)
                self.domain_groups = [str(x) for x in npz["groups"].tolist()]
                self.categories = [str(x) for x in npz["labels"].tolist()]
                return
            except Exception:
                pass

        texts = [c[2] for c in OOD_DOMAIN_CONCEPTS]
        embs = self.encode_texts(texts)
        self.domain_text_Matrix = embs
        np.savez_compressed(
            DOMAIN_TEXT_EMB_PATH,
            text_embs=embs.cpu().numpy().astype(np.float32),
            groups=np.array(self.domain_groups),
            labels=np.array(self.categories),
        )

    @torch.no_grad()
    def encode_texts(self, texts: List[str], batch_size: int = 256) -> torch.Tensor:
        out_list: List[torch.Tensor] = []
        for s in range(0, len(texts), batch_size):
            batch_txt = texts[s : s + batch_size]
            tokens = self.tokenizer(batch_txt).to(self.device)
            if USE_FP16 and self.device.type == "cuda":
                with torch.amp.autocast("cuda", dtype=torch.float16):
                    t_emb = self.model.encode_text(tokens)
            else:
                t_emb = self.model.encode_text(tokens)
            t_emb = F.normalize(t_emb.float(), p=2, dim=1)
            out_list.append(t_emb)
        return torch.cat(out_list, dim=0)

    @torch.no_grad()
    def forward(self, x: torch.Tensor, use_flip_tta: bool = USE_FLIP_TTA) -> torch.Tensor:
        f1 = F.normalize(self.model.encode_image(x).float(), p=2, dim=1)
        if use_flip_tta:
            f2 = F.normalize(self.model.encode_image(torch.flip(x, dims=[3])).float(), p=2, dim=1)
            f1 = F.normalize(f1 + f2, p=2, dim=1)
        return f1

    @torch.no_grad()
    def extract_single_pil(
        self, pil_img: Image.Image, use_flip_tta: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Trích xuất vector đặc trưng (768,) và phân phối xác suất ngữ nghĩa OOD cho 1 ảnh PIL."""
        img = ImageOps.exif_transpose(pil_img).convert("RGB")
        tensor = self.transform(img).unsqueeze(0).to(self.device)

        if USE_FP16 and self.device.type == "cuda":
            with torch.amp.autocast("cuda", dtype=torch.float16):
                feat_norm = self.forward(tensor, use_flip_tta=use_flip_tta)
        else:
            feat_norm = self.forward(tensor, use_flip_tta=use_flip_tta)

        if self.domain_text_Matrix is not None:
            logits_dom = 100.0 * torch.matmul(feat_norm, self.domain_text_Matrix.t())
            probs_dom = F.softmax(logits_dom, dim=1)[0].cpu().numpy().astype(np.float32)
        else:
            probs_dom = np.zeros((len(self.categories),), dtype=np.float32)

        return feat_norm[0].cpu().numpy().astype(np.float32), probs_dom


# Giữ bí danh để tương thích ngược
BotanicalDualBackbone = BotanicalBioCLIP2Backbone


class ManifestImageDataset(Dataset):
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
                if im.width < 16 or im.height < 16:
                    raise ValueError("Image too small")
                tensor = self.transform(im)
            valid = 1
        except Exception:
            tensor = torch.zeros((3, IMAGE_SIZE, IMAGE_SIZE), dtype=torch.float32)
            valid = 0
        return tensor, class_idx, split_code, valid


def extract_species_text_embeddings(backbone: BotanicalBioCLIP2Backbone) -> np.ndarray:
    """Trích xuất vector ngôn ngữ phân loại học GBIF (3570, 768) từ Text Encoder của BioCLIP 2."""
    cat = json.loads(SPECIES_CATALOG_PATH.read_text(encoding="utf-8"))
    class_idx_to_key: List[str] = cat["classIdxToKey"]
    species_map: Dict[str, Dict[str, Any]] = cat["species"]

    num_classes = len(class_idx_to_key)
    prompts_primary: List[str] = []
    prompts_short: List[str] = []
    for s_key in class_idx_to_key:
        p_list = build_species_prompts(species_map.get(s_key, {}))
        prompts_primary.append(p_list[0])
        prompts_short.append(p_list[-1])

    print(f"[Text Encoder] Mã hóa tên khoa học & phân cấp GBIF cho {num_classes:,} loài...", flush=True)
    e1 = backbone.encode_texts(prompts_primary, batch_size=256)
    e2 = backbone.encode_texts(prompts_short, batch_size=256)
    text_embs = F.normalize(0.65 * e1 + 0.35 * e2, p=2, dim=1).cpu().numpy().astype(np.float32)
    np.save(SPECIES_TEXT_EMB_PATH, text_embs)
    return text_embs


def extract_dataset_embeddings(
    batch_size: int = BATCH_SIZE,
    num_workers: int = NUM_WORKERS,
    use_flip_tta: bool = USE_FLIP_TTA,
    force_recompute: bool = False,
) -> Dict[str, Any]:
    """
    Trích xuất toàn bộ vector đặc trưng 768 chiều bằng BioCLIP 2 trên GPU FP16,
    tự động lưu checkpoint mỗi 25,000 ảnh để resume an toàn.
    """
    splits_data = json.loads(DATASET_SPLITS_PATH.read_text(encoding="utf-8"))
    manifest: List[Tuple[str, int, int]] = splits_data["manifest"]
    total_samples = len(manifest)

    if (
        not force_recompute
        and EMBEDDINGS_MATRIX_PATH.exists()
        and EMBEDDINGS_LABELS_PATH.exists()
        and EMBEDDINGS_SPLITS_PATH.exists()
        and SPECIES_TEXT_EMB_PATH.exists()
        and EMBEDDINGS_META_PATH.exists()
    ):
        meta = json.loads(EMBEDDINGS_META_PATH.read_text(encoding="utf-8"))
        if int(meta.get("numTotalManifest", 0)) == total_samples and int(meta.get("featureDim", 0)) == 768:
            print(f"[Info] Đã có sẵn trọn bộ {meta['numValidSamples']:,} embeddings BioCLIP 2 tại {EMBEDDINGS_MATRIX_PATH}")
            return meta

    print(
        f"[GPU] Khởi tạo BioCLIP 2 ({BIOCLIP_MODEL_ID} @ {IMAGE_SIZE}px) | "
        f"Device={DEVICE} | FP16={USE_FP16} | 2-ViewTTA={use_flip_tta}",
        flush=True,
    )
    backbone = BotanicalBioCLIP2Backbone(device=DEVICE, load_text_if_needed=True)
    feat_dim = backbone.feature_dim

    if force_recompute or not SPECIES_TEXT_EMB_PATH.exists():
        extract_species_text_embeddings(backbone)

    partial_feat_path = EMBEDDINGS_MATRIX_PATH.with_name("features_bioclip2_partial_fp16.npy")
    partial_mask_path = EMBEDDINGS_MATRIX_PATH.with_name("valid_mask_bioclip2_partial.npy")
    partial_state_path = EMBEDDINGS_MATRIX_PATH.with_name("extraction_state_bioclip2.json")

    all_labels = np.array([m[1] for m in manifest], dtype=np.int32)
    all_splits = np.array([m[2] for m in manifest], dtype=np.uint8)

    start_idx = 0
    prev_elapsed = 0.0
    if (
        not force_recompute
        and partial_feat_path.exists()
        and partial_mask_path.exists()
        and partial_state_path.exists()
    ):
        try:
            st = json.loads(partial_state_path.read_text(encoding="utf-8"))
            if int(st.get("totalSamples", 0)) == total_samples and int(st.get("featDim", 0)) == feat_dim:
                all_features = np.load(partial_feat_path)
                valid_mask = np.load(partial_mask_path)
                start_idx = int(st.get("processedSamples", 0))
                prev_elapsed = float(st.get("elapsedSeconds", 0.0))
                print(f"[Resume] Tiếp tục từ ảnh {start_idx:,}/{total_samples:,} (đã chạy {prev_elapsed:.1f}s)...", flush=True)
            else:
                all_features = np.zeros((total_samples, feat_dim), dtype=np.float16)
                valid_mask = np.zeros((total_samples,), dtype=bool)
        except Exception:
            all_features = np.zeros((total_samples, feat_dim), dtype=np.float16)
            valid_mask = np.zeros((total_samples,), dtype=bool)
    else:
        all_features = np.zeros((total_samples, feat_dim), dtype=np.float16)
        valid_mask = np.zeros((total_samples,), dtype=bool)

    remaining_manifest = manifest[start_idx:]
    num_remaining = len(remaining_manifest)
    t0 = time.time()
    checkpoint_interval = 25000
    next_ckpt = start_idx + checkpoint_interval

    if num_remaining > 0:
        dataset = ManifestImageDataset(remaining_manifest, root_dir=DATASET_ROOT)
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=(DEVICE == "cuda"),
            persistent_workers=(num_workers > 0),
        )
        cursor = start_idx
        num_batches = len(loader)

        for b_idx, (tensors, _, _, valids) in enumerate(loader):
            bsz = tensors.size(0)
            tensors = tensors.to(backbone.device, non_blocking=True)

            if USE_FP16 and backbone.device.type == "cuda":
                with torch.amp.autocast("cuda", dtype=torch.float16):
                    feats = backbone(tensors, use_flip_tta=use_flip_tta)
            else:
                feats = backbone(tensors, use_flip_tta=use_flip_tta)

            all_features[cursor : cursor + bsz] = feats.cpu().numpy().astype(np.float16)
            valid_mask[cursor : cursor + bsz] = valids.numpy().astype(bool)
            cursor += bsz

            if (b_idx + 1) == 5 or (b_idx + 1) % 25 == 0 or (b_idx + 1) == num_batches:
                elapsed = time.time() - t0
                done_now = cursor - start_idx
                speed = done_now / max(1e-5, elapsed)
                eta = (total_samples - cursor) / max(1e-5, speed)
                print(
                    f"  -> Batch [{b_idx + 1:>4}/{num_batches}] | "
                    f"Tổng: {cursor:>7,}/{total_samples:,} ({cursor * 100.0 / total_samples:5.1f}%) | "
                    f"Tốc độ: {speed:5.1f} ảnh/s | ETA: {eta / 60.0:5.1f} phút",
                    flush=True,
                )

            if cursor >= next_ckpt and cursor < total_samples:
                np.save(partial_feat_path, all_features)
                np.save(partial_mask_path, valid_mask)
                partial_state_path.write_text(
                    json.dumps(
                        {
                            "totalSamples": total_samples,
                            "featDim": feat_dim,
                            "processedSamples": cursor,
                            "elapsedSeconds": round(prev_elapsed + (time.time() - t0), 2),
                        }
                    ),
                    encoding="utf-8",
                )
                print(f"  [Checkpoint] Đã lưu an toàn tại {cursor:,}/{total_samples:,} ảnh.", flush=True)
                next_ckpt += checkpoint_interval

    all_features = all_features[valid_mask]
    all_labels = all_labels[valid_mask]
    all_splits = all_splits[valid_mask]
    valid_paths = [manifest[i][0] for i in range(total_samples) if valid_mask[i]]

    np.save(EMBEDDINGS_MATRIX_PATH, all_features)
    np.save(EMBEDDINGS_LABELS_PATH, all_labels)
    np.save(EMBEDDINGS_SPLITS_PATH, all_splits)
    EMBEDDINGS_PATHS_PATH.write_text(json.dumps(valid_paths), encoding="utf-8")

    for p in (partial_feat_path, partial_mask_path, partial_state_path):
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    total_time = round(prev_elapsed + (time.time() - t0), 2)
    meta = {
        "version": "bioclip2_single_model",
        "backbone": f"{BIOCLIP_MODEL_ID} (ViT-L/14, {IMAGE_SIZE}px)",
        "useFlipTTA": use_flip_tta,
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
