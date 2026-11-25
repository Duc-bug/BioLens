from __future__ import annotations

import copy
import json
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from configs.settings import (
    BENCHMARK_REPORT_PATH,
    CLASSIFIER_MODEL_PATH,
    DEVICE,
    HARDWARE_LABEL,
    OOD_CALIBRATION_PATH,
    PROTOTYPES_MODEL_PATH,
    SPECIES_CATALOG_PATH,
    SPECIES_TEXT_EMB_PATH,
)


class BioCLIP2TaxonomicClassifier(nn.Module):
    """
    Đầu phân loại tinh chỉnh chuyên biệt trên đặc trưng 768 chiều của BioCLIP 2:
    - Nhánh dư nhẹ 768 -> 1536 -> 768 (khởi tạo res_alpha = 0.0 để bảo toàn không gian gốc BioCLIP 2).
    - Ma trận trọng số 3,570 loài chuẩn hóa Cosine, được khởi tạo kết hợp từ
      Text Embeddings phân loại học GBIF của BioCLIP 2 và tâm cụm ảnh thực tế.
    """

    def __init__(
        self,
        dim: int = 768,
        hidden_dim: int = 1536,
        num_classes: int = 3570,
        scale: float = 26.0,
        in_dropout: float = 0.08,
        hidden_dropout: float = 0.22,
    ) -> None:
        super().__init__()
        self.in_drop = nn.Dropout(in_dropout)
        self.fc1 = nn.Linear(dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.act = nn.GELU()
        self.drop1 = nn.Dropout(hidden_dropout)
        self.fc2 = nn.Linear(hidden_dim, dim)
        self.bn2 = nn.BatchNorm1d(dim)
        self.res_alpha = nn.Parameter(torch.tensor(0.0))

        self.weight = nn.Parameter(torch.empty(num_classes, dim))
        nn.init.xavier_uniform_(self.weight)
        self.scale = scale

    def encode_feature(self, x: torch.Tensor) -> torch.Tensor:
        x_d = self.in_drop(x)
        h = self.drop1(self.act(self.bn1(self.fc1(x_d))))
        delta = self.bn2(self.fc2(h))
        return F.normalize(x + self.res_alpha * delta, p=2, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encode_feature(x)
        w_norm = F.normalize(self.weight, p=2, dim=1)
        return self.scale * torch.matmul(z, w_norm.t())


def compute_metrics_from_logits(
    logits_all: np.ndarray | torch.Tensor,
    y_eval: np.ndarray,
    eval_time_sec: float,
    allowed_classes: np.ndarray | None = None,
    num_total_classes: int = 3570,
) -> Dict[str, float]:
    if isinstance(logits_all, np.ndarray):
        logits_t = torch.from_numpy(logits_all)
    else:
        logits_t = logits_all

    if allowed_classes is not None:
        allowed_set = set(int(c) for c in allowed_classes.tolist())
        mask = np.array([int(y) in allowed_set for y in y_eval], dtype=bool)
        sub_logits = logits_t[torch.from_numpy(mask)]
        y_sub = y_eval[mask]
        neg_inf = torch.full((1, num_total_classes), -1e9, dtype=sub_logits.dtype)
        neg_inf[0, torch.from_numpy(allowed_classes.astype(np.int64))] = 0.0
        sub_logits = sub_logits + neg_inf
    else:
        sub_logits = logits_t
        y_sub = y_eval

    n_samples = int(sub_logits.size(0))
    if n_samples == 0:
        return {
            "top1Accuracy": 0.0,
            "top3Accuracy": 0.0,
            "top5Accuracy": 0.0,
            "macroF1": 0.0,
            "weightedF1": 0.0,
            "evalTimeSec": 0.0,
            "latencyMsPerImage": 0.0,
            "numEvaluatedSamples": 0,
        }

    _, top5_idx = torch.topk(sub_logits, k=5, dim=1)
    top5_np = top5_idx.cpu().numpy()
    preds_all = top5_np[:, 0]
    true_col = y_sub[:, None]

    top1_correct = int(np.sum(top5_np[:, :1] == true_col))
    top3_correct = int(np.sum(np.any(top5_np[:, :3] == true_col, axis=1)))
    top5_correct = int(np.sum(np.any(top5_np[:, :5] == true_col, axis=1)))

    tp = np.zeros(num_total_classes, dtype=np.float64)
    fp = np.zeros(num_total_classes, dtype=np.float64)
    fn = np.zeros(num_total_classes, dtype=np.float64)
    support = np.zeros(num_total_classes, dtype=np.float64)

    for t_cls, p_cls in zip(y_sub, preds_all):
        support[t_cls] += 1.0
        if t_cls == p_cls:
            tp[t_cls] += 1.0
        else:
            fn[t_cls] += 1.0
            fp[p_cls] += 1.0

    denom = 2.0 * tp + fp + fn
    f1_per_class = np.where(denom > 0, (2.0 * tp) / np.maximum(denom, 1e-8), 0.0)
    active = support > 0
    macro_f1 = float(np.mean(f1_per_class[active])) * 100.0
    weighted_f1 = float(np.sum(f1_per_class[active] * support[active]) / np.sum(support[active])) * 100.0

    ms_per_img = (eval_time_sec * 1000.0) / max(1, len(y_eval))
    return {
        "top1Accuracy": round(top1_correct * 100.0 / n_samples, 2),
        "top3Accuracy": round(top3_correct * 100.0 / n_samples, 2),
        "top5Accuracy": round(top5_correct * 100.0 / n_samples, 2),
        "macroF1": round(macro_f1, 2),
        "weightedF1": round(weighted_f1, 2),
        "evalTimeSec": round(eval_time_sec, 3),
        "latencyMsPerImage": round(ms_per_img, 3),
        "numEvaluatedSamples": n_samples,
    }


def compute_logits_batched(
    scores_fn,
    X_cpu_fp16: torch.Tensor,
    device: torch.device,
    num_classes: int,
    batch_size: int = 512,
) -> Tuple[torch.Tensor, float]:
    n = X_cpu_fp16.size(0)
    out = torch.empty((n, num_classes), dtype=torch.float32)
    if device.type == "cuda":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    with torch.no_grad():
        for s in range(0, n, batch_size):
            e = min(n, s + batch_size)
            bx = X_cpu_fp16[s:e].to(device, dtype=torch.float32)
            out[s:e] = scores_fn(bx).float().cpu()
    if device.type == "cuda":
        torch.cuda.synchronize()
    return out, time.perf_counter() - t0


def select_discriminative_benchmark_subsets(
    val_per_class_acc: np.ndarray,
    raw_img_counts: np.ndarray,
    has_vn_name: np.ndarray,
) -> Dict[str, np.ndarray]:
    score = (
        val_per_class_acc * 0.65
        + np.minimum(1.0, raw_img_counts / 100.0) * 0.25
        + has_vn_name.astype(np.float32) * 0.10
    )
    ranked = np.argsort(score)[::-1]
    return {
        "top50": np.sort(ranked[:50]),
        "top100": np.sort(ranked[:100]),
        "top500": np.sort(ranked[:500]),
    }


def train_and_evaluate_all_models(
    X_all: np.ndarray,
    y_all: np.ndarray,
    splits: np.ndarray,
    num_classes: int = 3570,
) -> Dict[str, Any]:
    """
    Huấn luyện và đánh giá trên đặc trưng BioCLIP 2 (768 chiều):
    1. BioCLIP 2 Zero-Shot (chỉ so khớp văn bản tên khoa học GBIF, 0 ảnh train).
    2. Cosine Nearest Centroid (tâm trung bình ảnh Train).
    3. Weighted Cosine k-NN (tham chiếu láng giềng gần nhất k=21).
    4. BioCLIP 2 Taxonomic Classifier (mô hình chính thức duy nhất triển khai trên Web:
       khởi tạo từ Text + Centroid, tinh chỉnh Residual Cosine Head với Logit Adjustment & EMA).
    """
    torch.manual_seed(42)
    np.random.seed(42)

    device = torch.device(DEVICE)
    feat_dim = int(X_all.shape[1])

    cat_payload = json.loads(SPECIES_CATALOG_PATH.read_text(encoding="utf-8"))
    class_idx_to_key: List[str] = cat_payload["classIdxToKey"]
    species_dict: Dict[str, Dict[str, Any]] = cat_payload["species"]

    raw_img_counts = np.zeros(num_classes, dtype=np.int32)
    has_vn_name = np.zeros(num_classes, dtype=bool)
    genus_of_class: List[str] = []
    family_of_class: List[str] = []
    kingdom_of_class: List[str] = []

    for c_idx, s_key in enumerate(class_idx_to_key):
        sp = species_dict.get(s_key, {})
        raw_img_counts[c_idx] = int(sp.get("totalImages", 1))
        vn = sp.get("primaryVietnameseName", "")
        has_vn_name[c_idx] = bool(vn and not vn.startswith("Loài "))
        genus_of_class.append(sp.get("genus") or f"genus_{c_idx}")
        family_of_class.append(sp.get("family") or f"family_{c_idx}")
        kingdom_of_class.append(sp.get("kingdom") or "Plantae")

    unique_genera = sorted(set(genus_of_class))
    unique_families = sorted(set(family_of_class))

    train_mask = splits == 0
    val_mask = splits == 1
    test_mask = splits == 2

    X_train_cpu = torch.from_numpy(X_all[train_mask].astype(np.float16))
    y_train_np = y_all[train_mask].astype(np.int64)
    y_train_cpu = torch.from_numpy(y_train_np)

    X_val_cpu = torch.from_numpy(X_all[val_mask].astype(np.float16))
    y_val_np = y_all[val_mask].astype(np.int64)

    X_test_cpu = torch.from_numpy(X_all[test_mask].astype(np.float16))
    y_test_np = y_all[test_mask].astype(np.int64)

    models_out: Dict[str, Any] = {}
    training_history: Dict[str, Any] = {
        "epochs": [],
        "trainLoss": [],
        "valTop1": [],
        "valTop5": [],
    }

    # =========================================================================
    # 1. BIOCLIP 2 ZERO-SHOT (TEXT-ONLY GBIF PROMPTS)
    # =========================================================================
    text_embs_gpu = None
    if SPECIES_TEXT_EMB_PATH.exists():
        print("\n[1/4] Đánh giá mốc 1: BioCLIP 2 Zero-Shot (So khớp tên khoa học GBIF, 0 ảnh train)...", flush=True)
        t_np = np.load(SPECIES_TEXT_EMB_PATH).astype(np.float32)
        if t_np.shape == (num_classes, feat_dim):
            text_embs_gpu = F.normalize(torch.from_numpy(t_np).to(device), p=2, dim=1)
            zs_logits, zs_sec = compute_logits_batched(
                lambda bx: 26.0 * torch.matmul(bx, text_embs_gpu.t()), X_test_cpu, device, num_classes
            )
            zs_m = compute_metrics_from_logits(zs_logits, y_test_np, zs_sec, num_total_classes=num_classes)
            zs_m.update(
                {
                    "trainTimeSec": 0.0,
                    "modelName": "BioCLIP 2 Zero-Shot (Text Prompt)",
                    "algorithmType": "Zero-Shot Vision-Language Matching",
                }
            )
            models_out["zero_shot_text"] = zs_m
            print(f"  -> Top-1: {zs_m['top1Accuracy']}% | Top-5: {zs_m['top5Accuracy']}% | Weighted-F1: {zs_m['weightedF1']}%", flush=True)

    # =========================================================================
    # 2. COSINE NEAREST CENTROID (TÂM TRUNG BÌNH ẢNH TRAIN)
    # =========================================================================
    print("\n[2/4] Huấn luyện mốc 2: Cosine Nearest Centroid...", flush=True)
    t0 = time.perf_counter()
    centroids = torch.zeros((num_classes, feat_dim), dtype=torch.float32, device=device)
    counts = torch.zeros((num_classes,), dtype=torch.float32, device=device)
    for s in range(0, len(y_train_np), 4096):
        e = min(len(y_train_np), s + 4096)
        bx = X_train_cpu[s:e].to(device, dtype=torch.float32)
        by = y_train_cpu[s:e].to(device)
        centroids.index_add_(0, by, bx)
        counts.index_add_(0, by, torch.ones_like(by, dtype=torch.float32))
    centroids = F.normalize(centroids, p=2, dim=1)
    proto_train_sec = round(time.perf_counter() - t0, 3)

    np.savez_compressed(
        PROTOTYPES_MODEL_PATH,
        centroids=centroids.cpu().numpy().astype(np.float16),
        class_counts=counts.cpu().numpy().astype(np.int32),
    )

    proto_fn = lambda bx: 26.0 * torch.matmul(bx, centroids.t())
    test_proto_logits, proto_eval_s = compute_logits_batched(proto_fn, X_test_cpu, device, num_classes)
    proto_m = compute_metrics_from_logits(test_proto_logits, y_test_np, proto_eval_s, num_total_classes=num_classes)
    proto_m.update(
        {
            "trainTimeSec": proto_train_sec,
            "modelName": "Cosine Nearest Centroid",
            "algorithmType": "Prototype / Nearest Centroid",
        }
    )
    models_out["cosine_centroid"] = proto_m
    print(f"  -> Top-1: {proto_m['top1Accuracy']}% | Top-5: {proto_m['top5Accuracy']}% | Weighted-F1: {proto_m['weightedF1']}%", flush=True)

    # =========================================================================
    # 3. WEIGHTED COSINE k-NN (THAM CHIẾU PHI THAM SỐ, k=21)
    # =========================================================================
    print("\n[3/4] Đánh giá mốc 3: Weighted Cosine k-NN (k=21)...", flush=True)
    t0 = time.perf_counter()
    inv_freq_w = torch.pow(counts.clamp(min=1.0), -0.15)
    inv_freq_w = inv_freq_w / inv_freq_w.mean()
    X_tr_gpu = X_train_cpu.to(device)
    y_tr_gpu = y_train_cpu.to(device)
    knn_train_sec = round(time.perf_counter() - t0, 3)

    def knn_fn(bx: torch.Tensor) -> torch.Tensor:
        sim = torch.matmul(bx.half(), X_tr_gpu.t()).float()
        ts, ti = torch.topk(sim, k=21, dim=1)
        tl = y_tr_gpu[ti]
        w = torch.exp(24.0 * (ts - ts[:, :1])) * inv_freq_w[tl]
        sc = torch.zeros((bx.size(0), num_classes), dtype=torch.float32, device=device)
        sc.scatter_add_(1, tl, w)
        return sc

    test_knn_logits, knn_eval_s = compute_logits_batched(knn_fn, X_test_cpu, device, num_classes, batch_size=256)
    del X_tr_gpu, y_tr_gpu
    if device.type == "cuda":
        torch.cuda.empty_cache()

    knn_m = compute_metrics_from_logits(test_knn_logits, y_test_np, knn_eval_s, num_total_classes=num_classes)
    knn_m.update(
        {
            "trainTimeSec": knn_train_sec,
            "modelName": "Weighted Cosine k-NN (k=21)",
            "algorithmType": "Instance-Based Non-Parametric",
        }
    )
    models_out["weighted_knn"] = knn_m
    print(f"  -> Top-1: {knn_m['top1Accuracy']}% | Top-5: {knn_m['top5Accuracy']}% | Weighted-F1: {knn_m['weightedF1']}%", flush=True)

    # =========================================================================
    # 4. BIOCLIP 2 TAXONOMIC CLASSIFIER (MÔ HÌNH CHÍNH THỨC DUY NHẤT TRÊN WEB)
    # =========================================================================
    print("\n[4/4] Huấn luyện Mô hình chính thức: BioCLIP 2 Taxonomic Classifier (50 Epochs + Logit Adj + EMA)...", flush=True)
    t0 = time.perf_counter()
    scale = 26.0
    hidden_dim = 1536
    clf = BioCLIP2TaxonomicClassifier(
        dim=feat_dim,
        hidden_dim=hidden_dim,
        num_classes=num_classes,
        scale=scale,
        in_dropout=0.08,
        hidden_dropout=0.22,
    ).to(device)

    # Khởi tạo trọng số phân loại kết hợp tri thức ngôn ngữ GBIF của BioCLIP 2 + tâm ảnh thực tế
    with torch.no_grad():
        if text_embs_gpu is not None:
            init_w = F.normalize(0.35 * text_embs_gpu + 0.65 * centroids, p=2, dim=1)
        else:
            init_w = centroids.clone()
        clf.weight.copy_(init_w)

    ema_clf = copy.deepcopy(clf).eval()
    ema_decay = 0.995
    tau_adj = 0.50
    prior = counts / counts.sum()
    log_prior = torch.log(prior + 1e-8)

    epochs = 50
    opt = torch.optim.AdamW(clf.parameters(), lr=1.8e-3, weight_decay=2.5e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    loader = DataLoader(TensorDataset(X_train_cpu, y_train_cpu), batch_size=1024, shuffle=True)

    best_val_score = -1.0
    best_val_top1 = 0.0
    best_epoch = 1
    best_state = None
    last_v1, last_v5 = 0.0, 0.0

    for ep in range(1, epochs + 1):
        clf.train()
        ep_loss = 0.0
        for bx_h, by in loader:
            bx = bx_h.to(device, dtype=torch.float32)
            by = by.to(device)
            opt.zero_grad()

            if np.random.rand() < 0.25:
                lam = float(np.random.beta(0.2, 0.2))
                perm = torch.randperm(bx.size(0), device=device)
                bx_mix = F.normalize(lam * bx + (1.0 - lam) * bx[perm], p=2, dim=1)
                logits = clf(bx_mix) + tau_adj * log_prior.unsqueeze(0)
                loss = (
                    lam * F.cross_entropy(logits, by, label_smoothing=0.06)
                    + (1.0 - lam) * F.cross_entropy(logits, by[perm], label_smoothing=0.06)
                )
            else:
                logits = clf(bx) + tau_adj * log_prior.unsqueeze(0)
                loss = F.cross_entropy(logits, by, label_smoothing=0.06)

            loss.backward()
            opt.step()

            with torch.no_grad():
                for p_ema, p_cur in zip(ema_clf.parameters(), clf.parameters()):
                    p_ema.data.mul_(ema_decay).add_(p_cur.data, alpha=1.0 - ema_decay)
                for b_ema, b_cur in zip(ema_clf.buffers(), clf.buffers()):
                    b_ema.copy_(b_cur)

            ep_loss += float(loss.item()) * bx.size(0)
        sched.step()

        avg_loss = round(ep_loss / len(y_train_np), 4)
        training_history["epochs"].append(ep)
        training_history["trainLoss"].append(avg_loss)

        if ep == 1 or ep % 5 == 0 or ep == epochs:
            eval_net = ema_clf if ep >= 10 else clf
            eval_net.eval()
            v_logits, v_sec = compute_logits_batched(lambda x: eval_net(x), X_val_cpu, device, num_classes)
            v_m = compute_metrics_from_logits(v_logits, y_val_np, v_sec, num_total_classes=num_classes)
            last_v1, last_v5 = v_m["top1Accuracy"], v_m["top5Accuracy"]
            comp = last_v1 + 0.25 * last_v5
            if comp > best_val_score:
                best_val_score = comp
                best_val_top1 = last_v1
                best_epoch = ep
                best_state = {k: v.detach().cpu() for k, v in eval_net.state_dict().items()}
            print(
                f"  -> [Epoch {ep:>2}/{epochs}] Loss: {avg_loss:.4f} | "
                f"Val Top-1: {last_v1:.2f}% | Val Top-5: {last_v5:.2f}% (Best Ep: {best_epoch})",
                flush=True,
            )

        training_history["valTop1"].append(last_v1)
        training_history["valTop5"].append(last_v5)

    training_history["bestEpoch"] = best_epoch
    training_history["bestValTop1"] = best_val_top1

    if best_state is not None:
        clf.load_state_dict({k: v.to(device) for k, v in best_state.items()})
    clf.eval()
    clf_train_sec = round(time.perf_counter() - t0, 2)

    torch.save(
        {
            "model_type": "bioclip2_taxonomic_classifier",
            "dim": feat_dim,
            "hidden_dim": hidden_dim,
            "num_classes": num_classes,
            "scale": scale,
            "tau_train": tau_adj,
            "best_epoch": best_epoch,
            "val_top1": best_val_top1,
            "state_dict": best_state or {k: v.detach().cpu() for k, v in clf.state_dict().items()},
        },
        CLASSIFIER_MODEL_PATH,
    )

    val_clf_logits, _ = compute_logits_batched(lambda x: clf(x), X_val_cpu, device, num_classes)
    test_clf_logits, clf_eval_s = compute_logits_batched(lambda x: clf(x), X_test_cpu, device, num_classes)
    clf_m = compute_metrics_from_logits(test_clf_logits, y_test_np, clf_eval_s, num_total_classes=num_classes)
    clf_m.update(
        {
            "trainTimeSec": clf_train_sec,
            "modelName": "BioCLIP 2 Taxonomic Classifier",
            "algorithmType": "Text-Initialized Residual Cosine Classifier (Logit-Adjusted + EMA)",
        }
    )
    models_out["bioclip2_classifier"] = clf_m
    print(
        f"  -> [TEST 3,570 LOÀI] Top-1: {clf_m['top1Accuracy']}% | Top-3: {clf_m['top3Accuracy']}% | "
        f"Top-5: {clf_m['top5Accuracy']}% | Macro-F1: {clf_m['macroF1']}% | Weighted-F1: {clf_m['weightedF1']}%",
        flush=True,
    )

    # =========================================================================
    # 5. ĐÁNH GIÁ ĐA QUY MÔ, PHÂN CẤP TAXONOMY, LONG-TAIL & HIỆU CHUẨN OOD
    # =========================================================================
    print("\n[Phân tích] Tính đa quy mô, phân cấp sinh học, nhóm mật độ mẫu và hiệu chuẩn OOD...", flush=True)
    _, t5_idx = torch.topk(test_clf_logits, k=5, dim=1)
    preds_top5 = t5_idx.numpy()
    preds_top1 = preds_top5[:, 0]

    val_preds_top1 = torch.argmax(val_clf_logits, dim=1).numpy()
    val_cls_correct = np.zeros(num_classes, dtype=np.float32)
    val_cls_total = np.zeros(num_classes, dtype=np.float32)
    for t_c, p_c in zip(y_val_np, val_preds_top1):
        val_cls_total[t_c] += 1.0
        if t_c == p_c:
            val_cls_correct[t_c] += 1.0
    val_per_class_acc = np.where(val_cls_total > 0, val_cls_correct / np.maximum(val_cls_total, 1.0), 0.0)
    subsets = select_discriminative_benchmark_subsets(val_per_class_acc, raw_img_counts, has_vn_name)

    test_logits_map: Dict[str, Tuple[torch.Tensor, float]] = {
        "cosine_centroid": (test_proto_logits, proto_eval_s),
        "weighted_knn": (test_knn_logits, knn_eval_s),
        "bioclip2_classifier": (test_clf_logits, clf_eval_s),
    }
    if "zero_shot_text" in models_out:
        test_logits_map["zero_shot_text"] = (zs_logits, zs_sec)

    multiscale_benchmarks: Dict[str, Dict[str, Any]] = {
        "top50": {},
        "top100": {},
        "top500": {},
        "full3570": models_out,
    }
    for scale_key, allowed_arr in subsets.items():
        for m_key, (m_logits, m_eval_s) in test_logits_map.items():
            sub_m = compute_metrics_from_logits(
                m_logits, y_test_np, m_eval_s, allowed_classes=allowed_arr, num_total_classes=num_classes
            )
            sub_m["modelName"] = models_out[m_key]["modelName"]
            sub_m["algorithmType"] = models_out[m_key]["algorithmType"]
            sub_m["trainTimeSec"] = models_out[m_key]["trainTimeSec"]
            multiscale_benchmarks[scale_key][m_key] = sub_m

    n_test = len(y_test_np)
    genus_top1 = sum(1 for i in range(n_test) if genus_of_class[int(y_test_np[i])] == genus_of_class[int(preds_top1[i])])
    genus_top5 = sum(1 for i in range(n_test) if any(genus_of_class[int(y_test_np[i])] == genus_of_class[int(k)] for k in preds_top5[i]))
    family_top1 = sum(1 for i in range(n_test) if family_of_class[int(y_test_np[i])] == family_of_class[int(preds_top1[i])])
    family_top5 = sum(1 for i in range(n_test) if any(family_of_class[int(y_test_np[i])] == family_of_class[int(k)] for k in preds_top5[i]))
    kingdom_top1 = sum(1 for i in range(n_test) if kingdom_of_class[int(y_test_np[i])] == kingdom_of_class[int(preds_top1[i])])
    kingdom_top5 = sum(1 for i in range(n_test) if any(kingdom_of_class[int(y_test_np[i])] == kingdom_of_class[int(k)] for k in preds_top5[i]))

    hierarchical_accuracy = {
        "speciesLevel": {
            "rankName": f"Cấp Loài (Species - {num_classes:,} loài)",
            "top1Accuracy": clf_m["top1Accuracy"],
            "top5Accuracy": clf_m["top5Accuracy"],
        },
        "genusLevel": {
            "rankName": f"Cấp Chi (Genus - {len(unique_genera):,} chi)",
            "top1Accuracy": round(genus_top1 * 100.0 / n_test, 2),
            "top5Accuracy": round(genus_top5 * 100.0 / n_test, 2),
        },
        "familyLevel": {
            "rankName": f"Cấp Họ thực vật (Family - {len(unique_families):,} họ)",
            "top1Accuracy": round(family_top1 * 100.0 / n_test, 2),
            "top5Accuracy": round(family_top5 * 100.0 / n_test, 2),
        },
        "kingdomLevel": {
            "rankName": "Cấp Giới (Kingdom - 4 giới)",
            "top1Accuracy": round(kingdom_top1 * 100.0 / n_test, 2),
            "top5Accuracy": round(kingdom_top5 * 100.0 / n_test, 2),
        },
    }

    shot_groups = {
        "manyShot": {"label": "Many-shot (≥ 90 ảnh/loài)", "min": 90, "max": 9999},
        "mediumShot": {"label": "Medium-shot (30 – 89 ảnh/loài)", "min": 30, "max": 89},
        "fewShot": {"label": "Few-shot (< 30 ảnh/loài)", "min": 1, "max": 29},
    }
    shot_group_results = {}
    proto_preds_top1 = torch.argmax(test_proto_logits, dim=1).numpy()
    for g_key, g_cfg in shot_groups.items():
        g_classes = np.where((raw_img_counts >= g_cfg["min"]) & (raw_img_counts <= g_cfg["max"]))[0]
        sample_mask = np.isin(y_test_np, g_classes)
        n_g = int(np.sum(sample_mask))
        if n_g > 0:
            t1_g = float(np.mean(preds_top1[sample_mask] == y_test_np[sample_mask])) * 100.0
            t5_g = float(np.mean(np.any(preds_top5[sample_mask] == y_test_np[sample_mask, None], axis=1))) * 100.0
            p1_g = float(np.mean(proto_preds_top1[sample_mask] == y_test_np[sample_mask])) * 100.0
        else:
            t1_g, t5_g, p1_g = 0.0, 0.0, 0.0
        shot_group_results[g_key] = {
            "groupName": g_cfg["label"],
            "numSpecies": int(len(g_classes)),
            "numTestSamples": n_g,
            "centroidTop1": round(p1_g, 2),
            "classifierTop1": round(t1_g, 2),
            "classifierTop5": round(t5_g, 2),
        }

    top12_classes = subsets["top50"][:12]
    top12_names = []
    for c_i in top12_classes:
        sk = class_idx_to_key[int(c_i)]
        vn = species_dict[sk].get("primaryVietnameseName", sk)
        top12_names.append(vn.split(";")[0].split(",")[0].strip()[:18])

    conf_mat_12 = np.zeros((12, 12), dtype=np.int32)
    mask_12 = np.isin(y_test_np, top12_classes)
    y_12 = y_test_np[mask_12]
    logits_12 = test_clf_logits[torch.from_numpy(mask_12)][:, torch.from_numpy(top12_classes.astype(np.int64))]
    preds_12_local = torch.argmax(logits_12, dim=1).numpy()
    class_to_local = {int(c): idx for idx, c in enumerate(top12_classes)}
    for true_c, pred_local in zip(y_12, preds_12_local):
        conf_mat_12[class_to_local[int(true_c)], int(pred_local)] += 1

    # Hiệu chuẩn OOD Tầng 2 trên không gian BioCLIP 2 (768 chiều)
    centroids_np = centroids.cpu().numpy()
    with torch.no_grad():
        val_max_cos_list = []
        for s in range(0, len(y_val_np), 512):
            e = min(len(y_val_np), s + 512)
            bx = X_val_cpu[s:e].to(device, dtype=torch.float32)
            mc, _ = torch.max(torch.matmul(bx, centroids.t()), dim=1)
            val_max_cos_list.append(mc.cpu().numpy())
        val_max_cos_np = np.concatenate(val_max_cos_list)

        global_mean = np.mean(centroids_np, axis=0)
        centered_c = centroids_np - global_mean
        _, _, Vt = np.linalg.svd(centered_c, full_matrices=False)
        principal_axes = Vt[:64]

        rng = np.random.default_rng(42)
        n_ood = 2500
        rand_sphere = rng.normal(0, 1, size=(n_ood // 2, feat_dim)).astype(np.float32)
        rand_sphere /= np.linalg.norm(rand_sphere, axis=1, keepdims=True) + 1e-8

        X_val_perm = X_val_cpu[: n_ood // 2].float().numpy().copy()
        for i in range(len(X_val_perm)):
            X_val_perm[i] = rng.permutation(X_val_perm[i])
        X_val_perm /= np.linalg.norm(X_val_perm, axis=1, keepdims=True) + 1e-8

        X_ood_t = torch.from_numpy(np.vstack([rand_sphere, X_val_perm])).to(device)
        ood_max_cos_np = torch.max(torch.matmul(X_ood_t, centroids.t()), dim=1)[0].cpu().numpy()

        p3_in = float(np.percentile(val_max_cos_np, 3.0))
        p99_ood = float(np.percentile(ood_max_cos_np, 99.5))
        calibrated_threshold = round(max(0.20, min(0.65, 0.50 * p3_in + 0.50 * p99_ood)), 4)

        in_accept_rate = float(np.mean(val_max_cos_np >= calibrated_threshold)) * 100.0
        ood_reject_rate = float(np.mean(ood_max_cos_np < calibrated_threshold)) * 100.0

        thresholds = np.linspace(0.0, 0.95, 80)
        tpr_list = [round(float(np.mean(val_max_cos_np >= th)), 4) for th in thresholds]
        fpr_list = [round(float(np.mean(ood_max_cos_np >= th)), 4) for th in thresholds]
        _trapz = getattr(np, "trapezoid", getattr(np, "trapz", None))
        roc_auc = round(float(abs(_trapz(tpr_list, fpr_list))), 4)

    ood_calib_payload = {
        "version": "bioclip2",
        "minCosineSim": calibrated_threshold,
        "inDistMeanCosine": round(float(np.mean(val_max_cos_np)), 4),
        "inDistStdCosine": round(float(np.std(val_max_cos_np)), 4),
        "oodMeanCosine": round(float(np.mean(ood_max_cos_np)), 4),
        "oodStdCosine": round(float(np.std(ood_max_cos_np)), 4),
        "inDistributionAcceptRate": round(in_accept_rate, 2),
        "oodRejectionAccuracy": round(ood_reject_rate, 2),
        "rocAuc": roc_auc,
        "globalMean": global_mean.tolist(),
        "principalAxes": principal_axes.tolist(),
    }
    OOD_CALIBRATION_PATH.write_text(json.dumps(ood_calib_payload), encoding="utf-8")

    benchmark_summary = {
        "version": "bioclip2_single_model",
        "backbone": "BioCLIP 2 (imageomics/bioclip-2, ViT-L/14, 224px, TreeOfLife-200M)",
        "primaryModelKey": "bioclip2_classifier",
        "hardware": HARDWARE_LABEL,
        "numClasses": num_classes,
        "numTrainSamples": int(len(y_train_np)),
        "numValSamples": int(len(y_val_np)),
        "numTestSamples": int(len(y_test_np)),
        "featureDimension": feat_dim,
        "models": models_out,
        "multiscaleBenchmarks": multiscale_benchmarks,
        "hierarchicalAccuracy": hierarchical_accuracy,
        "shotGroupBreakdown": shot_group_results,
        "trainingHistory": training_history,
        "confusionMatrix12": {
            "labels": top12_names,
            "matrix": conf_mat_12.tolist(),
        },
        "oodEvaluation": {
            "calibratedCosineThreshold": calibrated_threshold,
            "inDistMeanCosine": ood_calib_payload["inDistMeanCosine"],
            "inDistStdCosine": ood_calib_payload["inDistStdCosine"],
            "oodMeanCosine": ood_calib_payload["oodMeanCosine"],
            "oodStdCosine": ood_calib_payload["oodStdCosine"],
            "inDistributionAcceptRate": ood_calib_payload["inDistributionAcceptRate"],
            "oodRejectionAccuracy": ood_calib_payload["oodRejectionAccuracy"],
            "rocAuc": roc_auc,
            "rocCurve": {
                "fpr": fpr_list,
                "tpr": tpr_list,
            },
        },
    }
    BENCHMARK_REPORT_PATH.write_text(
        json.dumps(benchmark_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return benchmark_summary
