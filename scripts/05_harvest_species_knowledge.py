"""
Bước 5: Thu thập & Làm giàu Tri thức Thực vật - Dược liệu Đa nguồn (Multi-Source Botanical Knowledge Harvester).
- Tiền truy vấn đa luồng (Multi-threaded Pre-fetching) tóm tắt bách khoa từ Wikipedia Tiếng Việt (vi.wikipedia.org)
  cho các loài có tần suất xuất hiện cao và có tên tiếng Việt dược liệu.
- Lưu trữ bền vững vào storage/catalog/wiki_cache.json và tái tạo toàn bộ 3,570 hồ sơ loài
  trong storage/catalog/species_knowledge.json (kèm hoạt chất sinh học, tính vị Đông y và nguồn dữ liệu xác thực).
"""
from __future__ import annotations

import csv
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configs.settings import (
    METADATA_CSV_PATH,
    SPECIES_CATALOG_PATH,
    SPECIES_KNOWLEDGE_PATH,
    WIKI_CACHE_PATH,
)
from dataset.herbal_knowledge import GENUS_SPECIAL_NOTES, FAMILY_KNOWLEDGE_DB
from dataset.knowledge_enricher import BotanicalKnowledgeEnricher, parse_vietnamese_names


def harvest_knowledge(max_online_species: int = 200, max_workers: int = 4) -> Dict[str, Any]:
    t0 = time.time()
    enricher = BotanicalKnowledgeEnricher()
    # Làm sạch các mục cache rỗng trước đó bị chặn bởi giới hạn tốc độ (HTTP 429)
    enricher._wiki_cache = {k: v for k, v in enricher._wiki_cache.items() if v}

    # 1. Đọc danh mục hiện tại để xếp hạng ưu tiên các loài phổ biến và có tên tiếng Việt
    catalog_data = json.loads(SPECIES_CATALOG_PATH.read_text(encoding="utf-8"))
    species_map: Dict[str, Dict[str, Any]] = catalog_data.get("species", {})

    # 2. Đọc toàn bộ bản ghi gốc từ CSV
    csv_records: Dict[str, Dict[str, Any]] = {}
    with open(METADATA_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s_key = str(row.get("speciesKey", "")).strip()
            if s_key:
                csv_records[s_key] = row

    # 3. Lọc danh sách các loài ưu tiên cần tra cứu online từ Wikipedia Tiếng Việt
    candidates: List[Tuple[int, str, str, str]] = []
    for s_key, sp_info in species_map.items():
        raw_rec = csv_records.get(s_key, {})
        canonical = (raw_rec.get("canonicalName") or sp_info.get("canonicalName") or "").strip()
        vn_names = parse_vietnamese_names(raw_rec.get("vietnameseName") or "")
        primary_vn = vn_names[0] if vn_names else ""
        total_imgs = int(sp_info.get("totalImages", 0))

        # Ưu tiên loài có tên tiếng Việt rõ ràng và nhiều ảnh
        priority_score = total_imgs + (1000 if primary_vn else 0)
        if canonical and canonical not in enricher._wiki_cache:
            candidates.append((priority_score, s_key, canonical, primary_vn))

    candidates.sort(key=lambda x: x[0], reverse=True)
    to_fetch = candidates[:max_online_species]

    print(f"- Tổng số loài hoạt động trong hệ thống : {len(species_map):,}")
    print(f"- Số loài đã có sẵn trong Wiki Cache    : {len(enricher._wiki_cache):,}")
    print(f"- Số loài ưu tiên truy vấn mới đa luồng : {len(to_fetch):,} (workers={max_workers})")

    fetched_success = 0
    if to_fetch:
        def _worker(item: Tuple[int, str, str, str]) -> Tuple[str, str | None]:
            _, _, canonical_name, vn_name = item
            ext = enricher.fetch_wikipedia_extract(
                canonical_name=canonical_name,
                primary_vn_name=vn_name,
                timeout=2.5,
                save_immediately=False,
            )
            return canonical_name, ext

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_worker, item) for item in to_fetch]
            for idx, fut in enumerate(as_completed(futures), 1):
                try:
                    _, ext = fut.result()
                    if ext:
                        fetched_success += 1
                except Exception:
                    pass
                if idx % 50 == 0 or idx == len(to_fetch):
                    print(f"  + Tiến độ thu thập Wikipedia: {idx}/{len(to_fetch)} loài (Thành công mới: {fetched_success})")

        # Lưu toàn bộ cache xuống đĩa 1 lần
        enricher._save_wiki_cache()

    # 4. Tái tạo toàn bộ 3,570 hồ sơ loài trong species_knowledge.json với cấu trúc 8 mục mở rộng
    knowledge_entries: Dict[str, Dict[str, Any]] = {}
    wiki_enriched_count = 0
    genus_enriched_count = 0
    family_monograph_count = 0

    for s_key in sorted(species_map.keys(), key=lambda x: int(x)):
        raw_rec = csv_records.get(s_key, {"speciesKey": s_key})
        profile = enricher.build_species_profile(raw_rec, fetch_online_wiki=False)
        if profile["profileSections"].get("hasWikiExtract"):
            wiki_enriched_count += 1
        genus = profile["taxonomy"].get("genus", "")
        family = profile["taxonomy"].get("family", "")
        if genus in GENUS_SPECIAL_NOTES:
            genus_enriched_count += 1
        if family in FAMILY_KNOWLEDGE_DB:
            family_monograph_count += 1
        knowledge_entries[s_key] = profile

    SPECIES_KNOWLEDGE_PATH.write_text(
        json.dumps(knowledge_entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    elapsed = time.time() - t0
    stats = {
        "totalSpeciesProfiles": len(knowledge_entries),
        "wikiCachedTotal": sum(1 for v in enricher._wiki_cache.values() if v),
        "wikiEnrichedActiveSpecies": wiki_enriched_count,
        "genusEnrichedActiveSpecies": genus_enriched_count,
        "familyMonographActiveSpecies": family_monograph_count,
        "elapsedSeconds": round(elapsed, 2),
    }
    return stats


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 76)
    print("BIOLENS - BƯỚC 5: THU THẬP & LÀM GIÀU TRI THỨC DƯỢC LIỆU ĐA NGUỒN (3,570 LOÀI)")
    print("=" * 76)
    stats = harvest_knowledge(max_online_species=180, max_workers=4)
    print("-" * 76)
    print(f"[HOÀN TẤT TRONG {stats['elapsedSeconds']}s]")
    print(f"- Tổng số hồ sơ loài đã chuẩn hóa 8 mục : {stats['totalSpeciesProfiles']:,} loài")
    print(f"- Số loài tích hợp bài viết Wikipedia   : {stats['wikiEnrichedActiveSpecies']:,} loài")
    print(f"- Số loài tích hợp chuyên khảo cấp Họ   : {stats['familyMonographActiveSpecies']:,} loài")
    print(f"- Số loài tích hợp chuyên khảo cấp Chi  : {stats['genusEnrichedActiveSpecies']:,} loài")
    print(f"- File xuất                             : {SPECIES_KNOWLEDGE_PATH}")


if __name__ == "__main__":
    main()
