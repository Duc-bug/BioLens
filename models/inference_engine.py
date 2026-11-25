from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from backend.advanced_utils import SingletonMeta, TorchInferenceContext, execution_timer
from configs.settings import (
    CLASSIFIER_MODEL_PATH,
    DEVICE,
    PROTOTYPES_MODEL_PATH,
    SPECIES_CATALOG_PATH,
    SPECIES_KNOWLEDGE_PATH,
)
from dataset.knowledge_enricher import BotanicalKnowledgeEnricher
from models.feature_extractor import BotanicalBioCLIP2Backbone
from models.ml_classifiers import BioCLIP2TaxonomicClassifier
from models.ood_filter import TwoStageOODFilter


class BioLensInferenceEngine(metaclass=SingletonMeta):
    """
    BioLens Engine suy luận thời gian thực sử dụng duy nhất mô hình nền BioCLIP 2
    cùng đầu phân loại tinh chỉnh BioCLIP2TaxonomicClassifier.
    """

    def __init__(self) -> None:
        self.device = torch.device(DEVICE)
        self.backbone = BotanicalBioCLIP2Backbone(device=DEVICE, load_text_if_needed=True)
        self.ood_filter = TwoStageOODFilter(
            categories=self.backbone.categories,
            domain_groups=self.backbone.domain_groups,
        )
        self.enricher = BotanicalKnowledgeEnricher()

        self.catalog_summary: Dict[str, Any] = {}
        self.class_idx_to_key: List[str] = []
        self.species_map: Dict[str, Dict[str, Any]] = {}
        self.knowledge_map: Dict[str, Dict[str, Any]] = {}

        self.centroids: Optional[torch.Tensor] = None
        self.classifier: Optional[BioCLIP2TaxonomicClassifier] = None

        self._load_resources()

    def _load_resources(self) -> None:
        if SPECIES_CATALOG_PATH.exists():
            cat = json.loads(SPECIES_CATALOG_PATH.read_text(encoding="utf-8"))
            self.catalog_summary = cat.get("summary", {})
            self.class_idx_to_key = cat.get("classIdxToKey", [])
            self.species_map = cat.get("species", {})

        if SPECIES_KNOWLEDGE_PATH.exists():
            self.knowledge_map = json.loads(SPECIES_KNOWLEDGE_PATH.read_text(encoding="utf-8"))

        num_classes = len(self.class_idx_to_key) or 3570
        feat_dim = self.backbone.feature_dim

        if PROTOTYPES_MODEL_PATH.exists():
            try:
                proto_npz = np.load(PROTOTYPES_MODEL_PATH)
                c_np = proto_npz["centroids"].astype(np.float32)
                if c_np.shape[1] == feat_dim:
                    self.centroids = torch.from_numpy(c_np).to(self.device)
            except Exception:
                self.centroids = None

        if CLASSIFIER_MODEL_PATH.exists():
            try:
                ckpt = torch.load(CLASSIFIER_MODEL_PATH, map_location=self.device, weights_only=True)
                clf = BioCLIP2TaxonomicClassifier(
                    dim=int(ckpt.get("dim", feat_dim)),
                    hidden_dim=int(ckpt.get("hidden_dim", 1536)),
                    num_classes=int(ckpt.get("num_classes", num_classes)),
                    scale=float(ckpt.get("scale", 26.0)),
                )
                clf.load_state_dict(ckpt["state_dict"], strict=True)
                clf.to(self.device).eval()
                self.classifier = clf
            except Exception:
                self.classifier = None

        self.ood_filter._load_calibration()

    def reload_models_if_needed(self) -> None:
        self._load_resources()

    @execution_timer(attach_result_key="inferenceTimeMs")
    def identify_image(
        self,
        pil_img: Image.Image,
        algorithm: str = "bioclip2_classifier",
        organ_hint: str = "auto",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        if self.classifier is None and CLASSIFIER_MODEL_PATH.exists():
            self.reload_models_if_needed()

        t0 = time.perf_counter()
        num_classes = len(self.class_idx_to_key) or 3570

        with TorchInferenceContext(device=self.device.type):
            feat_np, probs_domain = self.backbone.extract_single_pil(pil_img, use_flip_tta=True)
            feat_t = torch.from_numpy(feat_np).unsqueeze(0).to(self.device)

            if self.centroids is not None:
                proto_sims_t = torch.matmul(feat_t, self.centroids.t())[0]
                max_proto_cos = float(torch.max(proto_sims_t).item())
                proto_probs = F.softmax(26.0 * proto_sims_t.unsqueeze(0), dim=1)[0]
                proto_sims_np = proto_sims_t.cpu().numpy()
            else:
                max_proto_cos = 0.0
                proto_probs = torch.full((num_classes,), 1.0 / num_classes, device=self.device)
                proto_sims_np = np.zeros(num_classes, dtype=np.float32)

            if self.classifier is not None:
                clf_logits = self.classifier(feat_t)
                max_clf_logit = float(torch.max(clf_logits).item())
                clf_probs = F.softmax(clf_logits / 1.4, dim=1)[0]
            else:
                max_clf_logit = max_proto_cos * 26.0
                clf_probs = proto_probs

        selected_probs = proto_probs if algorithm.lower().strip() in ("centroid", "cosine_centroid", "prototypes") else clf_probs
        topk_vals, topk_indices = torch.topk(selected_probs, k=min(top_k, len(selected_probs)))
        topk_vals_np = topk_vals.cpu().numpy()
        topk_idx_np = topk_indices.cpu().numpy()

        top1_conf = float(topk_vals_np[0])
        top1_margin = float(topk_vals_np[0] - topk_vals_np[1]) if len(topk_vals_np) > 1 else top1_conf

        ood_result = self.ood_filter.evaluate(
            pil_img=pil_img,
            feat_norm=feat_np,
            probs_domain=probs_domain,
            max_prototype_cosine=max_proto_cos,
            top1_confidence=top1_conf,
            top1_margin=top1_margin,
            max_clf_logit=max_clf_logit,
        )

        algorithm_comparison = {}
        for alg_key, alg_name, p_vec in [
            ("bioclip2_classifier", "BioCLIP 2 Taxonomic Classifier", clf_probs),
            ("cosine_centroid", "Cosine Nearest Centroid", proto_probs),
        ]:
            best_prob, best_idx = torch.max(p_vec, dim=0)
            b_idx = int(best_idx.item())
            s_key = self.class_idx_to_key[b_idx] if b_idx < len(self.class_idx_to_key) else str(b_idx)
            sp_item = self.species_map.get(s_key, {})
            algorithm_comparison[alg_key] = {
                "algorithmName": alg_name,
                "speciesKey": s_key,
                "vietnameseName": sp_item.get("primaryVietnameseName", f"Loài {s_key}"),
                "canonicalName": sp_item.get("canonicalName", ""),
                "confidencePercent": round(float(best_prob.item()) * 100.0, 2),
            }

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        if not ood_result["isAccepted"]:
            return {
                "isAccepted": False,
                "selectedAlgorithm": "bioclip2_classifier",
                "organHint": organ_hint,
                "inferenceTimeMs": elapsed_ms,
                "oodCheck": ood_result,
                "message": ood_result["rejectionReason"],
                "topMatch": None,
                "candidates": [],
                "algorithmComparison": algorithm_comparison,
            }

        candidates: List[Dict[str, Any]] = []
        for rank, (cls_idx, prob_val) in enumerate(zip(topk_idx_np.tolist(), topk_vals_np.tolist()), start=1):
            s_key = self.class_idx_to_key[cls_idx] if cls_idx < len(self.class_idx_to_key) else str(cls_idx)
            sp_info = self.get_enriched_species_info(s_key, fetch_live_wiki=(rank == 1))
            cos_val = float(proto_sims_np[cls_idx]) if cls_idx < len(proto_sims_np) else max_proto_cos
            visual_match_score = round(
                min(99.5, max(prob_val * 100.0, min(1.0, (cos_val - 0.25) / 0.50) * 100.0)),
                1,
            )
            candidates.append(
                {
                    "rank": rank,
                    "confidencePercent": round(prob_val * 100.0, 2),
                    "cosineSimilarity": round(cos_val, 4),
                    "visualMatchScore": visual_match_score,
                    **sp_info,
                }
            )

        return {
            "isAccepted": True,
            "selectedAlgorithm": "bioclip2_classifier",
            "organHint": organ_hint,
            "inferenceTimeMs": elapsed_ms,
            "oodCheck": ood_result,
            "message": f"Nhận diện thành công: {candidates[0]['primaryVietnameseName']} ({candidates[0]['canonicalName']})",
            "topMatch": candidates[0],
            "candidates": candidates,
            "algorithmComparison": algorithm_comparison,
        }

    def get_enriched_species_info(
        self,
        species_key: str,
        fetch_live_wiki: bool = True,
    ) -> Dict[str, Any]:
        cat_item = self.species_map.get(species_key, {})
        know_item = self.knowledge_map.get(species_key, {})

        if fetch_live_wiki and know_item:
            sections = know_item.get("profileSections", {})
            if not sections.get("hasWikiExtract"):
                canonical = know_item.get("canonicalName") or cat_item.get("canonicalName", "")
                vn_name = know_item.get("primaryVietnameseName") or cat_item.get("primaryVietnameseName", "")
                wiki_text = self.enricher.fetch_wikipedia_extract(canonical, vn_name)
                if wiki_text:
                    sections["overview"] = wiki_text
                    sections["hasWikiExtract"] = True

        sample_urls = [
            f"/api/image/{rel_path}"
            for rel_path in cat_item.get("sampleImagePaths", [])[:6]
        ]
        canonical = know_item.get("canonicalName") or cat_item.get("canonicalName", "")
        primary_vn = (
            know_item.get("primaryVietnameseName")
            or cat_item.get("primaryVietnameseName")
            or f"Loài {species_key}"
        )

        return {
            "speciesKey": species_key,
            "primaryVietnameseName": primary_vn,
            "vietnameseAliases": know_item.get("vietnameseAliases", cat_item.get("vietnameseAliases", [])),
            "canonicalName": canonical,
            "scientificName": know_item.get("scientificName") or cat_item.get("scientificName", canonical),
            "vernacularNameEn": know_item.get("vernacularNameEn") or cat_item.get("vernacularNameEn", ""),
            "taxonomy": know_item.get("taxonomy", cat_item.get("taxonomy", {})),
            "profileSections": know_item.get("profileSections", {}),
            "externalLinks": know_item.get("externalLinks", {
                "gbifUrl": f"https://www.gbif.org/species/{species_key}",
                "powoUrl": f"https://powo.science.kew.org/results?q={canonical}",
                "wikiViSearchUrl": f"https://vi.wikipedia.org/wiki/Special:Search?search={canonical}",
            }),
            "totalDatasetImages": cat_item.get("totalImages", 0),
            "sampleImageUrls": sample_urls,
        }
