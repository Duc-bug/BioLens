from __future__ import annotations

import json
import urllib.parse
from typing import Dict, Any, List, Optional
import requests

from configs.settings import WIKI_CACHE_PATH
from dataset.herbal_knowledge import (
    KINGDOM_VN_MAP,
    CLASS_VN_MAP,
    get_family_profile,
)


def parse_vietnamese_names(raw_vn: str) -> List[str]:
    """Tách chuỗi tên tiếng Việt (ngăn cách bởi dấu ; hoặc ,) thành danh sách các tên gọi."""
    if not raw_vn or not raw_vn.strip():
        return []
    parts = []
    for chunk in raw_vn.replace(";", ",").split(","):
        cleaned = chunk.strip().strip('"').strip("'")
        if cleaned and cleaned not in parts:
            parts.append(cleaned)
    return parts


class BotanicalKnowledgeEnricher:
    """Tổng hợp hồ sơ 6 mục chi tiết bằng Tiếng Việt cho từng loài hoa/cây dược liệu."""

    def __init__(self) -> None:
        self._wiki_cache: Dict[str, str] = {}
        self._load_wiki_cache()

    def _load_wiki_cache(self) -> None:
        if WIKI_CACHE_PATH.exists():
            try:
                self._wiki_cache = json.loads(
                    WIKI_CACHE_PATH.read_text(encoding="utf-8")
                )
            except Exception:
                self._wiki_cache = {}

    def _save_wiki_cache(self) -> None:
        try:
            WIKI_CACHE_PATH.write_text(
                json.dumps(self._wiki_cache, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def fetch_wikipedia_extract(
        self,
        canonical_name: str,
        primary_vn_name: str = "",
        timeout: float = 2.8,
        save_immediately: bool = True,
    ) -> Optional[str]:
        """
        Truy vấn nhanh tóm tắt bách khoa từ Wikipedia Tiếng Việt (ưu tiên theo tên khoa học
        hoặc tên tiếng Việt chính, kết hợp MediaWiki Search API khi không khớp tiêu đề trực tiếp)
        và lưu vào cache cục bộ.
        """
        cache_key = canonical_name.strip() or primary_vn_name.strip()
        if not cache_key:
            return None
        if cache_key in self._wiki_cache:
            return self._wiki_cache[cache_key] or None

        clean_vn = primary_vn_name.strip()
        if clean_vn.startswith("Loài "):
            clean_vn = ""
        candidates = [q.strip() for q in [canonical_name, clean_vn] if q and q.strip()]
        headers = {
            "User-Agent": "BioLensBotanicalResearch/2.0 (https://github.com/biolens-vietnam; contact@biolens.vn)",
            "Accept": "application/json",
        }

        def _fetch_rest_summary(title: str) -> Optional[str]:
            encoded = urllib.parse.quote(title.strip().replace(" ", "_"))
            url = f"https://vi.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                extract = (data.get("extract") or "").strip()
                if len(extract) > 45 and data.get("type") != "disambiguation":
                    return extract
            elif resp.status_code == 429:
                raise RuntimeError("rate_limited")
            return None

        rate_limited = False
        # Tầng 1: Tra cứu trực tiếp qua REST Summary API
        for query in candidates:
            try:
                extract = _fetch_rest_summary(query)
                if extract:
                    self._wiki_cache[cache_key] = extract
                    if save_immediately:
                        self._save_wiki_cache()
                    return extract
            except RuntimeError:
                rate_limited = True
            except Exception:
                continue

        # Tầng 2: Tra cứu dự phòng qua MediaWiki Action Search API nếu tên có khoảng trắng hoặc đồng danh
        for query in candidates:
            try:
                search_url = (
                    "https://vi.wikipedia.org/w/api.php"
                    f"?action=query&list=search&srsearch={urllib.parse.quote(query)}"
                    "&utf8=1&format=json&srlimit=2"
                )
                s_resp = requests.get(search_url, headers=headers, timeout=timeout)
                if s_resp.status_code == 429:
                    rate_limited = True
                    continue
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    hits = s_data.get("query", {}).get("search", [])
                    for hit in hits:
                        hit_title = (hit.get("title") or "").strip()
                        snippet = (hit.get("snippet") or "").lower()
                        q_lower = query.lower()
                        if hit_title and (
                            q_lower in hit_title.lower()
                            or q_lower in snippet
                            or "thực vật" in snippet
                            or "loài" in snippet
                            or "chi " in snippet
                            or "họ " in snippet
                        ):
                            extract = _fetch_rest_summary(hit_title)
                            if extract:
                                self._wiki_cache[cache_key] = extract
                                if save_immediately:
                                    self._save_wiki_cache()
                                return extract
            except RuntimeError:
                rate_limited = True
            except Exception:
                continue

        # Chỉ đánh dấu rỗng khi xác nhận không có bài viết (không ghi rỗng nếu bị giới hạn tốc độ mạng)
        if not rate_limited:
            self._wiki_cache[cache_key] = ""
            if save_immediately:
                self._save_wiki_cache()
        return None

    def build_species_profile(
        self, record: Dict[str, Any], fetch_online_wiki: bool = False
    ) -> Dict[str, Any]:
        """
        Xây dựng Thẻ Hồ sơ Loài (Species Encyclopedia Card) đầy đủ 6 mục Tiếng Việt.
        """
        species_key = str(record.get("speciesKey", "")).strip()
        canonical_name = (
            record.get("canonicalName") or record.get("species") or ""
        ).strip()
        scientific_name = (
            record.get("scientificName") or canonical_name
        ).strip()
        vernacular_en = (record.get("vernacularName") or "").strip()
        raw_vn = (record.get("vietnameseName") or "").strip()
        vn_names = parse_vietnamese_names(raw_vn)

        kingdom = (record.get("kingdom") or "Plantae").strip()
        phylum = (record.get("phylum") or "").strip()
        class_name = (record.get("class") or "").strip()
        order_name = (record.get("order") or "").strip()
        family = (record.get("family") or "").strip()
        genus = (record.get("genus") or "").strip()
        published_in = (record.get("publishedIn") or "").strip()

        primary_vn_name = vn_names[0] if vn_names else f"Loài {canonical_name}"
        other_vn_names = vn_names[1:] if len(vn_names) > 1 else []

        fam_info = get_family_profile(family, kingdom, genus=genus)
        kingdom_vn = KINGDOM_VN_MAP.get(kingdom, kingdom)
        class_vn = CLASS_VN_MAP.get(class_name, class_name or "Chưa phân lớp")

        # Kiểm tra tóm tắt Wikipedia Tiếng Việt (từ cache hoặc truy vấn trực tiếp khi nhận diện)
        wiki_extract = None
        if fetch_online_wiki:
            wiki_extract = self.fetch_wikipedia_extract(canonical_name, primary_vn_name)
        elif canonical_name in self._wiki_cache and self._wiki_cache[canonical_name]:
            wiki_extract = self._wiki_cache[canonical_name]

        # 1. Tổng quan về loài hoa / sinh vật
        alias_text = (
            f" (còn gọi trong dân gian là: {', '.join(other_vn_names)})"
            if other_vn_names
            else ""
        )
        en_text = f", tên tiếng Anh thông dụng là '{vernacular_en}'" if vernacular_en else ""

        if wiki_extract:
            overview = (
                f"{wiki_extract} "
                f"[Phân loại chuẩn GBIF #{species_key}: Chi {genus or 'Chưa rõ'}, {fam_info['family_vn']}, {class_vn}]."
            )
        else:
            overview = (
                f"{primary_vn_name}{alias_text} có danh pháp khoa học là {scientific_name}{en_text}. "
                f"Đây là một loài thuộc chi {genus or 'Chưa rõ'}, {fam_info['family_vn']}, {class_vn}. "
                f"{fam_info['growth_form']}"
            )

        # 2. Đặc điểm hình thái (Hoa - Lá - Thân - Quả)
        morphology_flower = fam_info["flower_traits"]
        morphology_leaf_stem = fam_info["leaf_stem_traits"]

        # 3. Phân bố & Môi trường sống
        pub_note = (
            f" Được mô tả khoa học lần đầu trong tài liệu gốc: {published_in}."
            if published_in
            else ""
        )
        habitat_distribution = f"{fam_info['habitat']}{pub_note}"

        # 4. Bộ phận dùng, Hoạt chất, Tính vị & Công dụng Dược liệu / Đời sống
        parts_used = fam_info["parts_used"]
        active_compounds = fam_info.get(
            "active_compounds",
            "Các hợp chất thứ cấp tự nhiên đặc trưng của họ thực vật (Polyphenol, Flavonoid, Terpenoid, Phytosterol).",
        )
        traditional_properties = fam_info.get(
            "traditional_properties",
            "Đông y truyền thống phân loại theo tính vị (Hàn/Nhiệt/Ôn/Lương) và quy kinh đặc trưng của từng bộ phận thu hái.",
        )
        medicinal_uses = (
            f"Theo dữ liệu đa dạng sinh học dược liệu Việt Nam (VietMediSpecies2026) và đặc trưng {fam_info['family_vn']}: "
            f"{fam_info['medicinal_uses']}"
        )

        # 5. Lưu ý an toàn & Độc tính
        safety_warning = fam_info["safety_note"]

        # 6. Nguồn dữ liệu đối chiếu xác thực
        data_sources = [
            f"GBIF Backbone Taxonomy (ID #{species_key})",
            "VietMediSpecies2026 Metadata Dataset",
            f"Chuyên khảo Dược liệu ({fam_info['family_vn']})",
        ]
        if wiki_extract:
            data_sources.append("Wikipedia Tiếng Việt (Đã xác thực & Lưu Cache)")

        return {
            "speciesKey": species_key,
            "primaryVietnameseName": primary_vn_name,
            "vietnameseAliases": other_vn_names,
            "allVietnameseNames": vn_names,
            "canonicalName": canonical_name,
            "scientificName": scientific_name,
            "vernacularNameEn": vernacular_en,
            "taxonomy": {
                "kingdom": kingdom,
                "kingdomVn": kingdom_vn,
                "phylum": phylum,
                "class": class_name,
                "classVn": class_vn,
                "order": order_name,
                "family": family,
                "familyVn": fam_info["family_vn"],
                "genus": genus,
            },
            "profileSections": {
                "overview": overview,
                "morphologyFlower": morphology_flower,
                "morphologyLeafStem": morphology_leaf_stem,
                "habitatDistribution": habitat_distribution,
                "partsUsed": parts_used,
                "activeCompounds": active_compounds,
                "traditionalProperties": traditional_properties,
                "medicinalUses": medicinal_uses,
                "safetyWarning": safety_warning,
                "hasWikiExtract": bool(wiki_extract),
                "dataSources": data_sources,
            },
            "externalLinks": {
                "gbifUrl": f"https://www.gbif.org/species/{species_key}",
                "powoUrl": f"https://powo.science.kew.org/results?q={urllib.parse.quote(canonical_name)}",
                "wikiViSearchUrl": f"https://vi.wikipedia.org/w/index.php?search={urllib.parse.quote(primary_vn_name if vn_names else canonical_name)}",
            },
        }
