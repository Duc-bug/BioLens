"""
Doc file csv metadata va quet cac thu muc anh de tao danh muc 3,570 loai.
Loc bo folder rac __MACOSX va chia tap train / val / test theo ti le 80 / 10 / 10.
"""
from __future__ import annotations

import csv
import json
import os
import random
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Tuple

from configs.settings import (
    DATASET_ROOT,
    METADATA_CSV_PATH,
    SPECIES_CATALOG_PATH,
    SPECIES_KNOWLEDGE_PATH,
    DATASET_SPLITS_PATH,
    MAX_IMAGES_PER_SPECIES,
    RANDOM_SEED,
    TRAIN_RATIO,
    VAL_RATIO,
)
from dataset.knowledge_enricher import BotanicalKnowledgeEnricher

VALID_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def build_full_catalog(
    max_images_per_species: int | None = MAX_IMAGES_PER_SPECIES,
    seed: int = RANDOM_SEED,
) -> Dict[str, Any]:
    """
    Quét toàn bộ thư mục dữ liệu VietMediSpecies2026 và xây dựng danh mục chuẩn.
    """
    rng = random.Random(seed)
    enricher = BotanicalKnowledgeEnricher()

    # 1. Đọc file CSV Metadata gốc
    csv_records: Dict[str, Dict[str, Any]] = {}
    with open(METADATA_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_key = str(row.get("speciesKey", "")).strip()
            if s_key:
                csv_records[s_key] = row

    # 2. Quét các thư mục loài hợp lệ (chỉ lấy thư mục tên số speciesKey, bỏ qua __MACOSX và BioLens)
    folder_names = sorted(
        [
            d
            for d in os.listdir(DATASET_ROOT)
            if d.isdigit() and (DATASET_ROOT / d).is_dir()
        ],
        key=lambda x: int(x),
    )

    species_entries: Dict[str, Dict[str, Any]] = {}
    knowledge_entries: Dict[str, Dict[str, Any]] = {}
    class_idx_to_key: List[str] = []

    total_raw_images = 0
    total_sampled_images = 0
    split_counts = {"train": 0, "val": 0, "test": 0}
    image_counts_per_species: List[int] = []
    family_counter: Counter = Counter()
    kingdom_counter: Counter = Counter()

    # Danh sách mẫu dùng để trích xuất đặc trưng (rel_path, class_idx, split_code)
    # split_code: 0 = train, 1 = val, 2 = test
    sampled_manifest: List[Tuple[str, int, int]] = []

    for class_idx, s_key in enumerate(folder_names):
        folder_path = DATASET_ROOT / s_key
        all_files = sorted(
            [
                fn
                for fn in os.listdir(folder_path)
                if not fn.startswith(".")
                and not fn.startswith("._")
                and Path(fn).suffix.lower() in VALID_IMAGE_EXTS
            ]
        )
        num_imgs = len(all_files)
        if num_imgs == 0:
            continue

        total_raw_images += num_imgs
        image_counts_per_species.append(num_imgs)
        class_idx_to_key.append(s_key)

        # Lấy mẫu đại diện mỗi loài (hoặc toàn bộ nếu max_images_per_species=None)
        if max_images_per_species is not None and num_imgs > max_images_per_species:
            selected_files = list(all_files)
            rng.shuffle(selected_files)
            selected_files = sorted(selected_files[:max_images_per_species])
        else:
            selected_files = all_files

        n_sel = len(selected_files)
        total_sampled_images += n_sel

        # Chia Stratified Train / Val / Test đảm bảo mọi loài đều có mặt trong tập Train
        shuffled = list(selected_files)
        rng.shuffle(shuffled)

        if n_sel == 1:
            n_train, n_val, n_test = 1, 0, 0
        elif n_sel == 2:
            n_train, n_val, n_test = 1, 0, 1
        elif n_sel == 3:
            n_train, n_val, n_test = 2, 0, 1
        elif n_sel <= 6:
            n_train = max(2, n_sel - 2)
            n_val = 1
            n_test = n_sel - n_train - n_val
        else:
            n_test = max(1, int(round(n_sel * (1.0 - TRAIN_RATIO - VAL_RATIO))))
            n_val = max(1, int(round(n_sel * VAL_RATIO)))
            n_train = n_sel - n_val - n_test

        for i, fn in enumerate(shuffled):
            if i < n_train:
                sp_code = 0
                split_counts["train"] += 1
            elif i < n_train + n_val:
                sp_code = 1
                split_counts["val"] += 1
            else:
                sp_code = 2
                split_counts["test"] += 1
            sampled_manifest.append((f"{s_key}/{fn}", class_idx, sp_code))

        # Ghép thông tin từ CSV và bộ làm giàu tri thức
        raw_record = csv_records.get(s_key, {"speciesKey": s_key})
        profile = enricher.build_species_profile(raw_record, fetch_online_wiki=False)

        fam = profile["taxonomy"]["family"] or "Unknown"
        king = profile["taxonomy"]["kingdom"] or "Plantae"
        family_counter[fam] += 1
        kingdom_counter[king] += 1

        sample_images = [f"{s_key}/{fn}" for fn in all_files[:8]]

        species_entries[s_key] = {
            "classIdx": class_idx,
            "speciesKey": s_key,
            "primaryVietnameseName": profile["primaryVietnameseName"],
            "vietnameseAliases": profile["vietnameseAliases"],
            "canonicalName": profile["canonicalName"],
            "scientificName": profile["scientificName"],
            "vernacularNameEn": profile["vernacularNameEn"],
            "kingdom": king,
            "kingdomVn": profile["taxonomy"]["kingdomVn"],
            "class": profile["taxonomy"]["class"],
            "classVn": profile["taxonomy"]["classVn"],
            "order": profile["taxonomy"]["order"],
            "family": profile["taxonomy"]["family"],
            "familyVn": profile["taxonomy"]["familyVn"],
            "genus": profile["taxonomy"]["genus"],
            "totalImages": num_imgs,
            "sampledImages": n_sel,
            "sampleImagePaths": sample_images,
        }
        knowledge_entries[s_key] = profile

    # Lưu danh mục và hồ sơ tri thức
    catalog_summary = {
        "totalCsvRecords": len(csv_records),
        "totalActiveSpecies": len(class_idx_to_key),
        "totalRawImages": total_raw_images,
        "totalSampledImages": total_sampled_images,
        "maxImagesPerSpeciesSetting": max_images_per_species,
        "minImagesPerSpecies": min(image_counts_per_species) if image_counts_per_species else 0,
        "maxImagesPerSpecies": max(image_counts_per_species) if image_counts_per_species else 0,
        "avgImagesPerSpecies": round(
            sum(image_counts_per_species) / max(1, len(image_counts_per_species)), 2
        ),
        "splitCounts": split_counts,
        "kingdomDistribution": dict(kingdom_counter.most_common()),
        "topFamilies": [
            {"family": fam, "speciesCount": cnt}
            for fam, cnt in family_counter.most_common(30)
        ],
    }

    catalog_payload = {
        "summary": catalog_summary,
        "classIdxToKey": class_idx_to_key,
        "species": species_entries,
    }

    SPECIES_CATALOG_PATH.write_text(
        json.dumps(catalog_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    SPECIES_KNOWLEDGE_PATH.write_text(
        json.dumps(knowledge_entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    DATASET_SPLITS_PATH.write_text(
        json.dumps(
            {
                "summary": catalog_summary,
                "manifest": sampled_manifest,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return catalog_summary
