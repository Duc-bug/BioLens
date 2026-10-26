from __future__ import annotations

import json
import time
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from configs.settings import (
    DEVICE,
    SPECIES_CATALOG_PATH,
    SPECIES_KNOWLEDGE_PATH,
    EMBEDDINGS_MATRIX_PATH,
    EMBEDDINGS_LABELS_PATH,
    EMBEDDINGS_SPLITS_PATH,
    METRIC_ADAPTER_PATH,
    PROTOTYPES_MODEL_PATH,
    KNN_INDEX_PATH,
    LINEAR_SVM_MODEL_PATH,
    MLP_CLASSIFIER_PATH,
)
from dataset.knowledge_enricher import BotanicalKnowledgeEnricher
from models.feature_extractor import BotanicalDualBackbone
from models.ml_classifiers import (
    BotanicalMetricAdapter,
    CosineMLPNetwork,
    power_law_whiten_torch,
)
from models.ood_filter import TwoStageOODFilter


class BioLensInferenceEngine:
    """Pipeline nhận diện sinh vật & dược liệu thời gian thực (hỗ trợ cả Baseline v1 và Fine-tuned v2)."""

    def __init__(self) -> None:
        self.device = torch.device(DEVICE)
        self.backbone = BotanicalDualBackbone(device=DEVICE)
        self.ood_filter = TwoStageOODFilter(categories=self.backbone.categories)
        self.enricher = BotanicalKnowledgeEnricher()

        self.catalog_summary: Dict[str, Any] = {}
        self.class_idx_to_key: List[str] = []
        self.species_map: Dict[str, Dict[str, Any]] = {}
        self.knowledge_map: Dict[str, Dict[str, Any]] = {}

        # Tham số biến đổi không gian đặc trưng (Phase 2 Fine-tuned Metric Adapter)
        self.beta_pow: float = 0.55
        self.power_mean: Optional[torch.Tensor] = None
        self.metric_adapter: Optional[BotanicalMetricAdapter] = None

        # Trọng số 4 mô hình Học máy
        self.centroids: Optional[torch.Tensor] = None
        self.sub1: Optional[torch.Tensor] = None
        self.sub2: Optional[torch.Tensor] = None
        self.knn_k: int = 19
        self.knn_temp: float = 21.0
        self.inv_freq_weight: Optional[torch.Tensor] = None
        self.svm_W: Optional[torch.Tensor] = None
        self.svm_b: Optional[torch.Tensor] = None
        self.mlp_model: Optional[CosineMLPNetwork] = None
        self.X_train_half: Optional[torch.Tensor] = None
        self.y_train_t: Optional[torch.Tensor] = None

        self._load_resources()

    @torch.no_grad()
    def _transform_feature(self, feat_raw_t: torch.Tensor) -> torch.Tensor:
        """Biến đổi đặc trưng 960 chiều qua Power-Law Whitening + BotanicalMetricAdapter (nếu có)."""
        if self.power_mean is not None and self.metric_adapter is not None:
            x_w = power_law_whiten_torch(feat_raw_t, self.power_mean, beta=self.beta_pow)
            z_adapt = self.metric_adapter.encode(x_w)
            return F.normalize(0.60 * feat_raw_t + 0.25 * x_w + 0.15 * z_adapt, p=2, dim=1)
        return F.normalize(feat_raw_t, p=2, dim=1)

    def _load_resources(self) -> None:
        if SPECIES_CATALOG_PATH.exists():
            cat = json.loads(SPECIES_CATALOG_PATH.read_text(encoding="utf-8"))
            self.catalog_summary = cat.get("summary", {})
            self.class_idx_to_key = cat.get("classIdxToKey", [])
            self.species_map = cat.get("species", {})

        if SPECIES_KNOWLEDGE_PATH.exists():
            self.knowledge_map = json.loads(
                SPECIES_KNOWLEDGE_PATH.read_text(encoding="utf-8")
            )

        num_classes = len(self.class_idx_to_key) or 3570
        feat_dim = self.backbone.feature_dim

        # Tải Metric Adapter (Phase 2 Fine-tuning)
        if METRIC_ADAPTER_PATH.exists():
            try:
                ckpt = torch.load(METRIC_ADAPTER_PATH, map_location=self.device, weights_only=True)
                self.beta_pow = float(ckpt.get("beta_pow", 0.55))
                self.power_mean = ckpt["power_mean"].to(self.device, dtype=torch.float32)
                num_gen = int(ckpt.get("num_genera", 1698))
                num_fam = int(ckpt.get("num_families", 338))
                adapter = BotanicalMetricAdapter(
                    dim=feat_dim,
                    num_species=num_classes,
                    num_genera=num_gen,
                    num_families=num_fam,
                )
                adapter.load_state_dict(ckpt["adapter_state"])
                adapter.to(self.device)
                adapter.eval()
                self.metric_adapter = adapter
            except Exception:
                self.metric_adapter = None
                self.power_mean = None

        if PROTOTYPES_MODEL_PATH.exists():
            proto_npz = np.load(PROTOTYPES_MODEL_PATH)
            c_np = proto_npz["centroids"].astype(np.float32)
            self.centroids = torch.from_numpy(c_np).to(self.device)
            if "sub1" in proto_npz and "sub2" in proto_npz:
                self.sub1 = torch.from_numpy(proto_npz["sub1"].astype(np.float32)).to(self.device)
                self.sub2 = torch.from_numpy(proto_npz["sub2"].astype(np.float32)).to(self.device)
            else:
                self.sub1 = None
                self.sub2 = None

        if KNN_INDEX_PATH.exists():
            knn_npz = np.load(KNN_INDEX_PATH)
            if "k" in knn_npz:
                self.knn_k = int(knn_npz["k"])
            if "temperature" in knn_npz:
                self.knn_temp = float(knn_npz["temperature"])
            if "inv_freq_weight" in knn_npz:
                self.inv_freq_weight = torch.from_numpy(
                    knn_npz["inv_freq_weight"].astype(np.float32)
                ).to(self.device)

        if LINEAR_SVM_MODEL_PATH.exists():
            svm_npz = np.load(LINEAR_SVM_MODEL_PATH)
            w_np = svm_npz["W"].astype(np.float32)
            b_np = svm_npz["b"].astype(np.float32)
            self.svm_W = torch.from_numpy(w_np).to(self.device)
            self.svm_b = torch.from_numpy(b_np).to(self.device)

        if MLP_CLASSIFIER_PATH.exists():
            state = torch.load(MLP_CLASSIFIER_PATH, map_location=self.device, weights_only=True)
            hidden_dim = state["fc1.weight"].shape[0] if "fc1.weight" in state else 1536
            mlp = CosineMLPNetwork(
                in_dim=feat_dim,
                hidden_dim=hidden_dim,
                num_classes=num_classes,
                scale=26.0,
            )
            mlp.load_state_dict(state, strict=False)
            mlp.to(self.device)
            mlp.eval()
            self.mlp_model = mlp

        if (
            EMBEDDINGS_MATRIX_PATH.exists()
            and EMBEDDINGS_LABELS_PATH.exists()
            and EMBEDDINGS_SPLITS_PATH.exists()
        ):
            X_all = np.load(EMBEDDINGS_MATRIX_PATH)
            y_all = np.load(EMBEDDINGS_LABELS_PATH)
            splits = np.load(EMBEDDINGS_SPLITS_PATH)
            train_mask = splits == 0
            X_train_np = X_all[train_mask]
            n_tr = X_train_np.shape[0]
            feat_dim = X_train_np.shape[1]
            X_train_half = torch.empty((n_tr, feat_dim), dtype=torch.float16, device=self.device)
            with torch.no_grad():
                for start in range(0, n_tr, 8192):
                    end = min(n_tr, start + 8192)
                    batch_raw = torch.from_numpy(X_train_np[start:end].astype(np.float32)).to(self.device)
                    batch_ft = self._transform_feature(batch_raw)
                    X_train_half[start:end] = batch_ft.to(dtype=torch.float16)
            self.X_train_half = X_train_half
            self.y_train_t = torch.from_numpy(y_all[train_mask].astype(np.int64)).to(self.device)

    def reload_models_if_needed(self) -> None:
        """Tải lại trọng số mô hình nếu vừa huấn luyện xong."""
        self.ood_filter._load_calibration()
        self._load_resources()

    @torch.no_grad()
    def _compute_all_algorithm_probs(
        self, feat_t: torch.Tensor, feat_raw_t: Optional[torch.Tensor] = None
    ) -> Tuple[Dict[str, torch.Tensor], float]:
        """
        Tính phân phối xác suất của cả 4 thuật toán Học máy + Ensemble cho 1 vector đặc trưng đã qua tinh chỉnh (1, 960).
        """
        if feat_raw_t is None:
            feat_raw_t = feat_t
        num_classes = len(self.class_idx_to_key) or 3570
        probs_dict: Dict[str, torch.Tensor] = {}

        if self.centroids is not None:
            s_main = torch.matmul(feat_t, self.centroids.t())  # (1, C)
            max_cos = float(torch.max(s_main).item())
            if self.sub1 is not None and self.sub2 is not None:
                s_sub = torch.maximum(
                    torch.matmul(feat_t, self.sub1.t()),
                    torch.matmul(feat_t, self.sub2.t()),
                )
                proto_logits = (0.65 * s_main + 0.35 * s_sub) * 24.0
            else:
                proto_logits = s_main * 22.0
            probs_dict["cosine_prototype"] = F.softmax(proto_logits, dim=1)
        else:
            max_cos = 0.0
            proto_logits = torch.zeros((1, num_classes), device=self.device)
            probs_dict["cosine_prototype"] = torch.full(
                (1, num_classes), 1.0 / num_classes, device=self.device
            )

        if self.X_train_half is not None and self.y_train_t is not None:
            sim_all = torch.matmul(feat_t.half(), self.X_train_half.t()).float()
            topk_sim, topk_idx = torch.topk(sim_all, k=self.knn_k, dim=1)
            topk_labels = self.y_train_t[topk_idx]
            weights = torch.exp(self.knn_temp * (topk_sim - topk_sim[:, :1]))
            if self.inv_freq_weight is not None:
                weights = weights * self.inv_freq_weight[topk_labels]
            knn_scores = torch.zeros((1, num_classes), dtype=torch.float32, device=self.device)
            knn_scores.scatter_add_(1, topk_labels, weights)
            if self.centroids is not None:
                knn_scores = knn_scores + 0.22 * (proto_logits / 24.0)
            probs_dict["weighted_knn"] = knn_scores / (knn_scores.sum(dim=1, keepdim=True) + 1e-8)
        else:
            knn_scores = proto_logits / 24.0
            probs_dict["weighted_knn"] = probs_dict["cosine_prototype"]

        if self.svm_W is not None and self.svm_b is not None:
            svm_logits = torch.matmul(feat_t, self.svm_W.t()) + self.svm_b
            probs_dict["linear_svm"] = F.softmax(svm_logits * 1.6, dim=1)
        else:
            svm_logits = proto_logits
            probs_dict["linear_svm"] = probs_dict["cosine_prototype"]

        if self.mlp_model is not None:
            mlp_base = 0.90 * self.mlp_model(feat_raw_t) + 0.35 * self.mlp_model(feat_t)
            mlp_logits = mlp_base + 0.16 * svm_logits + 0.08 * proto_logits
            probs_dict["cosine_mlp"] = F.softmax(mlp_logits, dim=1)
        else:
            mlp_base = proto_logits
            mlp_logits = proto_logits
            probs_dict["cosine_mlp"] = probs_dict["cosine_prototype"]

        ens_logits = (
            mlp_base
            + 1.50 * knn_scores
            + 0.32 * svm_logits
            + 0.14 * proto_logits
        )
        probs_dict["ensemble"] = F.softmax(ens_logits, dim=1)
        return probs_dict, max_cos

    def get_enriched_species_info(self, species_key: str, fetch_live_wiki: bool = True) -> Dict[str, Any]:
        """Lấy thông tin chi tiết 6 mục của loài hoa/cây kèm ảnh mẫu."""
        cat_item = self.species_map.get(species_key, {})
        know_item = self.knowledge_map.get(species_key, {})

        # Nếu bật fetch_live_wiki và chưa có trích đoạn Wikipedia Tiếng Việt trong cache, tự động lấy
        if fetch_live_wiki and know_item:
            sections = know_item.get("profileSections", {})
            if not sections.get("hasWikiExtract"):
                canonical = know_item.get("canonicalName", "")
                vn_name = know_item.get("primaryVietnameseName", "")
                wiki_text = self.enricher.fetch_wikipedia_extract(canonical, vn_name)
                if wiki_text:
                    sections["overview"] = wiki_text
                    sections["hasWikiExtract"] = True

        sample_urls = [
            f"/api/image/{rel_path}"
            for rel_path in cat_item.get("sampleImagePaths", [])[:6]
        ]

        return {
            "speciesKey": species_key,
            "primaryVietnameseName": know_item.get("primaryVietnameseName") or cat_item.get("primaryVietnameseName") or f"Loài {species_key}",
            "vietnameseAliases": know_item.get("vietnameseAliases", []),
            "canonicalName": know_item.get("canonicalName") or cat_item.get("canonicalName", ""),
            "scientificName": know_item.get("scientificName") or cat_item.get("scientificName", ""),
            "vernacularNameEn": know_item.get("vernacularNameEn") or cat_item.get("vernacularNameEn", ""),
            "taxonomy": know_item.get("taxonomy", {}),
            "profileSections": know_item.get("profileSections", {}),
            "externalLinks": know_item.get("externalLinks", {}),
            "totalDatasetImages": cat_item.get("totalImages", 0),
            "sampleImageUrls": sample_urls,
        }

    def identify_image(
        self,
        pil_img: Image.Image,
        algorithm: str = "ensemble",
        organ_hint: str = "auto",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Nhận diện ảnh chụp hoa/sinh vật và trả về kết quả đầy đủ.
        """
        if self.centroids is None and PROTOTYPES_MODEL_PATH.exists():
            self.reload_models_if_needed()

        t0 = time.perf_counter()
        feat_raw_np, probs_1000 = self.backbone.extract_single_pil(pil_img)
        feat_raw_t = torch.from_numpy(feat_raw_np).unsqueeze(0).to(self.device)
        feat_t = self._transform_feature(feat_raw_t)
        feat_ft_np = feat_t[0].cpu().numpy().astype(np.float32)

        probs_dict, max_proto_cos = self._compute_all_algorithm_probs(feat_t, feat_raw_t=feat_raw_t)
        selected_alg = algorithm if algorithm in probs_dict else "ensemble"
        selected_probs = probs_dict[selected_alg][0]

        topk_vals, topk_indices = torch.topk(selected_probs, k=min(top_k, len(selected_probs)))
        topk_vals_np = topk_vals.cpu().numpy()
        topk_idx_np = topk_indices.cpu().numpy()

        top1_conf = float(topk_vals_np[0])
        top1_margin = float(topk_vals_np[0] - topk_vals_np[1]) if len(topk_vals_np) > 1 else top1_conf

        # Kiểm tra qua Bộ lọc Từ chối 2 Tầng (2-Stage OOD Rejection)
        ood_result = self.ood_filter.evaluate(
            pil_img=pil_img,
            feat_norm=feat_ft_np,
            probs_1000=probs_1000,
            max_prototype_cosine=max_proto_cos,
            top1_confidence=top1_conf,
            top1_margin=top1_margin,
        )

        # So sánh dự đoán Top-1 giữa cả 4 thuật toán Học máy
        algorithm_comparison = {}
        alg_labels = {
            "ensemble": "BioLens Hybrid Ensemble (Fine-tuned v2)",
            "cosine_mlp": "Class-Balanced SE-Residual Cosine MLP",
            "weighted_knn": "Weighted Cosine k-NN (Balanced, k=19)",
            "linear_svm": "Multi-class Linear SVM (Hard-Margin)",
            "cosine_prototype": "Cosine Prototype (Multi-Subcenter)",
        }
        for alg_key, alg_name in alg_labels.items():
            p_vec = probs_dict[alg_key][0]
            best_prob, best_idx = torch.max(p_vec, dim=0)
            b_idx = int(best_idx.item())
            s_key = self.class_idx_to_key[b_idx] if b_idx < len(self.class_idx_to_key) else str(b_idx)
            sp_item = self.species_map.get(s_key, {})
            algorithm_comparison[alg_key] = {
                "algorithmName": alg_name,
                "speciesKey": s_key,
                "vietnameseName": sp_item.get("primaryVietnameseName", s_key),
                "canonicalName": sp_item.get("canonicalName", ""),
                "confidencePercent": round(float(best_prob.item()) * 100.0, 2),
            }

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        # Nếu bị Bộ lọc OOD từ chối (chụp vật thể khác hoặc độ tương đồng quá thấp)
        if not ood_result["isAccepted"]:
            return {
                "isAccepted": False,
                "selectedAlgorithm": selected_alg,
                "organHint": organ_hint,
                "inferenceTimeMs": elapsed_ms,
                "oodCheck": ood_result,
                "message": ood_result["rejectionReason"],
                "topMatch": None,
                "candidates": [],
                "algorithmComparison": algorithm_comparison,
            }

        # Nếu ảnh hợp lệ -> Xây dựng danh sách Top-K ứng viên và Hồ sơ chi tiết loài Top-1
        candidates: List[Dict[str, Any]] = []
        proto_sims_all = (
            torch.matmul(feat_t, self.centroids.t())[0].cpu().numpy()
            if self.centroids is not None
            else np.zeros(len(selected_probs))
        )

        for rank, (cls_idx, prob_val) in enumerate(zip(topk_idx_np.tolist(), topk_vals_np.tolist()), start=1):
            s_key = self.class_idx_to_key[cls_idx] if cls_idx < len(self.class_idx_to_key) else str(cls_idx)
            fetch_wiki = rank == 1
            sp_info = self.get_enriched_species_info(s_key, fetch_live_wiki=fetch_wiki)
            cos_val = float(proto_sims_all[cls_idx]) if cls_idx < len(proto_sims_all) else max_proto_cos
            visual_match_score = round(
                min(99.5, max(prob_val * 100.0, min(1.0, (cos_val - 0.28) / 0.50) * 100.0)),
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
            "selectedAlgorithm": selected_alg,
            "organHint": organ_hint,
            "inferenceTimeMs": elapsed_ms,
            "oodCheck": ood_result,
            "message": f"Nhận diện thành công: {candidates[0]['primaryVietnameseName']} ({candidates[0]['canonicalName']})",
            "topMatch": candidates[0],
            "candidates": candidates,
            "algorithmComparison": algorithm_comparison,
        }
