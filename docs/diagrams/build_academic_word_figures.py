# -*- coding: utf-8 -*-
"""
Tạo bộ 8 hình vẽ và biểu đồ phong cách học thuật tối giản (đen - trắng - xám ghi,
khung vuông gọn như Visio/Draw.io, có họa tiết gạch chéo để in đen trắng rõ nét)
dùng 100% dữ liệu thật của BioCLIP 2 từ ml_benchmark_results.json và species_catalog.json.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ROOT = Path(r"e:\VietMediSpecies2026\BioLens")
BENCH_JSON = ROOT / "storage" / "reports" / "ml_benchmark_results.json"
CAT_JSON = ROOT / "storage" / "catalog" / "species_catalog.json"
OUT_DIR = ROOT / "docs" / "diagrams" / "academic_bw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9.2,
    "axes.titlesize": 10.2,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.2,
    "axes.edgecolor": "#222222",
    "axes.linewidth": 0.85,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.2,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
})

C_BLACK = "#1A1A1A"
C_DARK = "#2F3E4E"
C_MID = "#64748B"
C_LIGHT = "#CBD5E1"
C_PALE = "#F1F5F9"
C_WHITE = "#FFFFFF"


def fmt_vn(val: float, dec: int = 2) -> str:
    return f"{val:.{dec}f}".replace(".", ",")


def visio_box(ax, x, y, w, h, title, body, header_fill="#E2E8F0", fs_t=8.4, fs_b=7.6, title_h=0.44):
    outer = patches.Rectangle(
        (x, y), w, h, facecolor=C_WHITE, edgecolor=C_BLACK, linewidth=1.05
    )
    ax.add_patch(outer)
    hdr = patches.Rectangle(
        (x, y + h - title_h), w, title_h, facecolor=header_fill, edgecolor=C_BLACK, linewidth=0.9
    )
    ax.add_patch(hdr)
    ax.text(x + w / 2, y + h - title_h / 2, title, color=C_BLACK,
            ha="center", va="center", fontsize=fs_t, fontweight="bold")
    ax.text(x + w / 2, y + (h - title_h) / 2, body, color=C_BLACK,
            ha="center", va="center", fontsize=fs_b, linespacing=1.35)


def visio_arrow(ax, x1, y1, x2, y2, label=""):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=C_BLACK, lw=1.1, mutation_scale=11)
    )
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + 0.10
        ax.text(mx, my, label, ha="center", va="bottom", fontsize=7.3, color=C_BLACK,
                bbox=dict(boxstyle="square,pad=0.10", fc=C_WHITE, ec="none"))


def fig1_eda(cat: dict, bench: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.0), gridspec_kw={"width_ratios": [1.3, 1.0]})

    top_fams = cat["summary"]["topFamilies"][:10][::-1]
    f_names = [f["family"] for f in top_fams]
    f_cnts = [f["speciesCount"] for f in top_fams]

    y = np.arange(len(f_names))
    bars = ax1.barh(y, f_cnts, height=0.62, color=C_MID, edgecolor=C_BLACK, linewidth=0.8)
    for b in bars:
        w = b.get_width()
        ax1.text(w + 4, b.get_y() + b.get_height() / 2, f"{int(w)}",
                 va="center", ha="left", fontsize=8.0, color=C_BLACK)
    ax1.set_yticks(y)
    ax1.set_yticklabels(f_names)
    ax1.set_xlabel("Số lượng loài")
    ax1.set_xlim(0, 325)
    ax1.grid(axis="x", linestyle=":", alpha=0.6, color="#888888")
    ax1.set_axisbelow(True)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_title("(a) 10 Họ thực vật có nhiều loài nhất")

    sg = bench["shotGroupBreakdown"]
    g_labels = ["Nhiều ảnh\n(≥ 90 ảnh/loài)", "Trung bình\n(30–89 ảnh/loài)", "Ít ảnh\n(< 30 ảnh/loài)"]
    g_sp = [sg["manyShot"]["numSpecies"], sg["mediumShot"]["numSpecies"], sg["fewShot"]["numSpecies"]]
    x = np.arange(3)
    hatches = ["", "//", ".."]
    fills = [C_DARK, C_MID, C_LIGHT]
    for i in range(3):
        ax2.bar(x[i], g_sp[i], width=0.52, color=fills[i], edgecolor=C_BLACK, linewidth=0.9, hatch=hatches[i])
        pct = g_sp[i] * 100.0 / 3570.0
        ax2.text(x[i], g_sp[i] + 45, f"{g_sp[i]} loài\n({fmt_vn(pct, 1)}%)",
                 ha="center", va="bottom", fontsize=8.0, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(g_labels)
    ax2.set_ylabel("Số lượng loài")
    ax2.set_ylim(0, 2550)
    ax2.grid(axis="y", linestyle=":", alpha=0.6, color="#888888")
    ax2.set_axisbelow(True)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_title("(b) Phân bố 3.570 loài theo mật độ mẫu")

    fig.tight_layout(w_pad=2.2)
    fig.savefig(OUT_DIR / "word_fig1_phan_bo_du_lieu.png")
    plt.close(fig)


def fig2_pipeline(bench: dict) -> None:
    th_cal = bench["oodEvaluation"]["calibratedCosineThreshold"]
    fig, ax = plt.subplots(figsize=(12.2, 3.6))
    ax.set_xlim(0, 12.2)
    ax.set_ylim(0, 3.6)
    ax.axis("off")

    steps = [
        (0.12, 0.65, 2.12, 2.35, "1. Tiền xử lý ảnh",
         "Xoay ảnh theo EXIF\nChuyển hệ màu RGB\nCo giãn Bicubic 1,05x (235px)\nCắt tâm 224×224, chuẩn CLIP\nTạo bản lật ngang (2-View)"),
        (2.55, 0.65, 2.16, 2.35, "2. Mô hình nền BioCLIP 2",
         "Mô hình nền ViT-L/14\n(TreeOfLife-200M)\nChuẩn hóa L2 từng góc nhìn\nHợp nhất L2: 768 chiều\nText Encoder: 11 câu miền"),
        (5.02, 0.65, 2.14, 2.35, "3. Kiểm định đầu vào",
         f"Tiền kiểm độ nét Laplacian\n& độ sáng, tương phản\nTầng 1: Ngữ nghĩa Zero-Shot\nTầng 2: Cosine tâm cụm\n(ngưỡng ≥ {fmt_vn(th_cal, 4)})"),
        (7.47, 0.65, 2.14, 2.35, "4. Phân loại 3.570 loài",
         "Đầu phân loại tinh chỉnh\nBioCLIP2TaxonomicClassifier\nNhánh dư 768→1536→768\nKhởi tạo từ Text + Centroid\nChia nhiệt độ T = 1,4"),
        (9.92, 0.65, 2.16, 2.35, "5. Hồ sơ & An toàn y sinh",
         "Tra cứu 7 mục thực vật học\nCảnh báo 176 loài có độc\n3.236 loài chỉ dùng làm thuốc\nGợi ý 158 loài trà/món ăn\n(70 loài có công thức)"),
    ]
    for x, y, w, h, t, b in steps:
        visio_box(ax, x, y, w, h, t, b, header_fill="#E5E7EB", fs_t=7.7, fs_b=7.2, title_h=0.46)

    for i in range(len(steps) - 1):
        x1 = steps[i][0] + steps[i][2] + 0.03
        x2 = steps[i + 1][0] - 0.03
        visio_arrow(ax, x1, 1.82, x2, 1.82)

    ax.text(6.1, 0.22,
            "Luồng xử lý tuần tự từ ảnh đầu vào đến kết quả định danh loài và kiểm soát an toàn dược liệu trên giao diện Web",
            ha="center", va="center", fontsize=8.0, style="italic", color="#333333")
    fig.savefig(OUT_DIR / "word_fig2_so_do_quy_trinh.png")
    plt.close(fig)


def fig3_bioclip2_architecture(bench: dict) -> None:
    clf_m = bench["models"]["bioclip2_classifier"]
    fig, ax = plt.subplots(figsize=(11.4, 4.9))
    ax.set_xlim(0, 11.4)
    ax.set_ylim(0, 4.9)
    ax.axis("off")

    visio_box(
        ax, 0.15, 2.75, 2.25, 1.65,
        "Luồng Ảnh thực địa",
        "Ảnh gốc I & ảnh lật ngang\nKích thước 224×224 px\nQua BioCLIP 2 Image Encoder\n(ViT-L/14, FP16)",
        header_fill="#E5E7EB", fs_t=8.1, fs_b=7.3, title_h=0.42
    )
    visio_box(
        ax, 0.15, 0.55, 2.25, 1.65,
        "Luồng Văn bản GBIF",
        "Chuỗi phân cấp Giới..Chi\n+ Tên khoa học 3.570 loài\nQua BioCLIP 2 Text Encoder\n(0,65 câu dài + 0,35 câu ngắn)",
        header_fill="#E5E7EB", fs_t=8.1, fs_b=7.3, title_h=0.42
    )

    visio_box(
        ax, 2.90, 2.75, 2.25, 1.65,
        "Đặc trưng x & Tâm cụm C",
        "Vector ảnh chuẩn hóa L2:\nx ∈ R^768\nTâm trung bình tập Train:\nC ∈ R^(3570 × 768)",
        header_fill="#E5E7EB", fs_t=8.0, fs_b=7.3, title_h=0.42
    )
    visio_box(
        ax, 2.90, 0.55, 2.25, 1.65,
        "Ma trận Văn bản T",
        "Biểu diễn ngôn ngữ sinh học\ncho toàn bộ 3.570 loài:\nT ∈ R^(3570 × 768)\n(Zero-Shot Top-1: 78,37%)",
        header_fill="#E5E7EB", fs_t=8.0, fs_b=7.3, title_h=0.42
    )

    visio_box(
        ax, 5.65, 2.65, 2.65, 1.80,
        "Nhánh dư Tinh chỉnh Đặc trưng",
        "Dropout(0,08) → FC(768→1536)\n→ BatchNorm1d → GELU\n→ Dropout(0,22) → FC(1536→768)\n→ BatchNorm1d → Δ(x)\nz = L2Norm(x + α·Δ(x)), α = 0,0392",
        header_fill="#D1D5DB", fs_t=8.0, fs_b=7.2, title_h=0.42
    )
    visio_box(
        ax, 5.65, 0.55, 2.65, 1.65,
        "Khởi tạo Ma trận Trọng số W",
        "Kết hợp đa phương thức:\nW_0 = L2Norm(0,35·T + 0,65·C)\nBảo toàn tri thức phân loại học\ncho nhóm loài ít mẫu (<30 ảnh)",
        header_fill="#D1D5DB", fs_t=8.0, fs_b=7.2, title_h=0.42
    )

    visio_box(
        ax, 8.80, 1.15, 2.45, 2.75,
        "Đầu phân loại Cosine",
        f"Logits: s · z · L2Norm(W)^T\n(hệ số tỉ lệ s = 26,0)\n\nHuấn luyện (50 epochs):\n+ 0,50·log(π_c), Mixup (0,25)\nLabel Smoothing (0,06), EMA\n\nKết quả Test (31.201 ảnh):\nTop-1: {fmt_vn(clf_m['top1Accuracy'])}% | Top-5: {fmt_vn(clf_m['top5Accuracy'])}%",
        header_fill="#CBD5E1", fs_t=8.1, fs_b=7.2, title_h=0.45
    )

    visio_arrow(ax, 2.42, 3.57, 2.88, 3.57)
    visio_arrow(ax, 2.42, 1.37, 2.88, 1.37)
    visio_arrow(ax, 5.17, 3.57, 5.63, 3.57, "x")
    visio_arrow(ax, 5.17, 2.95, 5.63, 1.65, "0,65·C")
    visio_arrow(ax, 5.17, 1.37, 5.63, 1.37, "0,35·T")
    visio_arrow(ax, 8.32, 3.55, 8.78, 2.85, "z")
    visio_arrow(ax, 8.32, 1.37, 8.78, 2.15, "W")

    fig.savefig(OUT_DIR / "word_fig3_trich_dac_trung_va_4_mo_hinh.png")
    plt.close(fig)


def fig4_training_curves(bench: dict) -> None:
    hist = bench["trainingHistory"]
    eps = hist["epochs"]
    loss = hist["trainLoss"]
    val1 = hist["valTop1"]
    val5 = hist["valTop5"]
    best_ep = hist["bestEpoch"]
    best_v1 = hist["bestValTop1"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.8))

    ax1.plot(eps, loss, color=C_BLACK, lw=1.6, marker="o", markevery=5, markersize=3.8,
             label="Train Loss (Cross-Entropy + Logit Adj)")
    ax1.set_xlabel("Vòng lặp huấn luyện (Epoch)")
    ax1.set_ylabel("Giá trị hàm mất mát")
    ax1.set_xlim(0, 52)
    ax1.set_ylim(0.85, 1.88)
    ax1.grid(True, linestyle=":", alpha=0.6, color="#888888")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.legend(loc="upper right", frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    ax1.set_title("(a) Hàm mất mát huấn luyện qua 50 Epochs")

    eval_idx = [i for i, ep in enumerate(eps) if ep == 1 or ep % 5 == 0 or ep == eps[-1]]
    ev_eps = [eps[i] for i in eval_idx]
    ev_v1 = [val1[i] for i in eval_idx]
    ev_v5 = [val5[i] for i in eval_idx]

    ax2.plot(ev_eps, ev_v1, color=C_BLACK, lw=1.7, marker="o", markersize=4.0, label="Val Top-1 (%)")
    ax2.plot(ev_eps, ev_v5, color=C_MID, lw=1.7, linestyle="-.", marker="s", markersize=3.8, label="Val Top-5 (%)")
    ax2.axvline(best_ep, color=C_DARK, linestyle="--", lw=1.2,
                label=f"Epoch chọn lưu ({best_ep}: {fmt_vn(best_v1)}%)")
    ax2.set_xlabel("Vòng lặp huấn luyện (Epoch)")
    ax2.set_ylabel("Độ chính xác trên tập Validation (%)")
    ax2.set_xlim(0, 52)
    ax2.set_ylim(84.0, 98.2)
    ax2.grid(True, linestyle=":", alpha=0.6, color="#888888")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(loc="lower right", frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    ax2.set_title("(b) Hội tụ độ chính xác trên tập Validation")

    fig.tight_layout(w_pad=2.2)
    fig.savefig(OUT_DIR / "word_fig4_hoi_tu_huan_luyen.png")
    plt.close(fig)


def fig5_model_comparison(bench: dict) -> None:
    m = bench["models"]
    keys = ["zero_shot_text", "cosine_centroid", "weighted_knn", "bioclip2_classifier"]
    labels = [
        "BioCLIP 2 Zero-Shot\n(Text Prompt GBIF)",
        "Cosine Nearest\nCentroid",
        "Weighted Cosine\nk-NN (k=21)",
        "BioCLIP 2 Taxonomic\nClassifier (Chính)",
    ]
    t1 = [m[k]["top1Accuracy"] for k in keys]
    t5 = [m[k]["top5Accuracy"] for k in keys]
    wf1 = [m[k]["weightedF1"] for k in keys]

    fig, ax = plt.subplots(figsize=(9.2, 4.1))
    x = np.arange(len(keys))
    w = 0.25
    b1 = ax.bar(x - w, t1, width=w, color=C_DARK, edgecolor=C_BLACK, lw=0.85, label="Top-1 Accuracy (%)")
    b2 = ax.bar(x, t5, width=w, color=C_LIGHT, edgecolor=C_BLACK, lw=0.85, hatch="//", label="Top-5 Accuracy (%)")
    b3 = ax.bar(x + w, wf1, width=w, color=C_MID, edgecolor=C_BLACK, lw=0.85, hatch="..", label="Weighted-F1 (%)")

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.8, fmt_vn(h, 2),
                    ha="center", va="bottom", fontsize=7.4, fontweight="bold", color=C_BLACK)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Tỉ lệ (%)")
    ax.set_ylim(0, 106)
    ax.grid(axis="y", linestyle=":", alpha=0.6, color="#888888")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="lower right", frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "word_fig5_so_sanh_5_mo_hinh.png")
    plt.close(fig)


def fig6_multiscale_and_shots(bench: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.9))

    scales = ["top50", "top100", "top500", "full3570"]
    s_lbl = ["Top-50\nloài", "Top-100\nloài", "Top-500\nloài", "Toàn bộ\n3.570 loài"]
    s_t1 = [bench["multiscaleBenchmarks"][s]["bioclip2_classifier"]["top1Accuracy"] for s in scales]
    s_t5 = [bench["multiscaleBenchmarks"][s]["bioclip2_classifier"]["top5Accuracy"] for s in scales]

    x1 = np.arange(4)
    w1 = 0.34
    b1 = ax1.bar(x1 - w1 / 2, s_t1, width=w1, color=C_DARK, edgecolor=C_BLACK, lw=0.85, label="Top-1 (%)")
    b2 = ax1.bar(x1 + w1 / 2, s_t5, width=w1, color=C_LIGHT, edgecolor=C_BLACK, lw=0.85, hatch="//", label="Top-5 (%)")
    for idx_b, bars in enumerate((b1, b2)):
        dx = -0.04 if idx_b == 0 else 0.04
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2 + dx, h + 0.9, fmt_vn(h, 2) + "%",
                     ha="center", va="bottom", fontsize=7.2, fontweight="bold")
    ax1.set_xticks(x1)
    ax1.set_xticklabels(s_lbl)
    ax1.set_ylabel("Độ chính xác (%)")
    ax1.set_ylim(0, 108)
    ax1.grid(axis="y", linestyle=":", alpha=0.6, color="#888888")
    ax1.set_axisbelow(True)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.legend(loc="lower left", frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    ax1.set_title("(a) Kết quả theo quy mô số lượng loài")

    sg = bench["shotGroupBreakdown"]
    g_keys = ["manyShot", "mediumShot", "fewShot"]
    g_lbl = [
        f"Nhiều ảnh\n(≥90 ảnh, {sg['manyShot']['numSpecies']} loài)",
        f"Trung bình\n(30–89 ảnh, {sg['mediumShot']['numSpecies']} loài)",
        f"Ít ảnh\n(<30 ảnh, {sg['fewShot']['numSpecies']} loài)",
    ]
    p1 = [sg[k]["centroidTop1"] for k in g_keys]
    e1 = [sg[k]["classifierTop1"] for k in g_keys]
    e5 = [sg[k]["classifierTop5"] for k in g_keys]

    x2 = np.arange(3)
    w2 = 0.25
    g1 = ax2.bar(x2 - w2, p1, width=w2, color=C_WHITE, edgecolor=C_BLACK, lw=0.85, hatch="..", label="Centroid Top-1")
    g2 = ax2.bar(x2, e1, width=w2, color=C_DARK, edgecolor=C_BLACK, lw=0.85, label="Classifier Top-1")
    g3 = ax2.bar(x2 + w2, e5, width=w2, color=C_LIGHT, edgecolor=C_BLACK, lw=0.85, hatch="//", label="Classifier Top-5")
    for bars in (g1, g2, g3):
        for bar in bars:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2, h + 1.0, fmt_vn(h, 1) + "%",
                     ha="center", va="bottom", fontsize=7.2, fontweight="bold")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(g_lbl, fontsize=8.0)
    ax2.set_ylabel("Độ chính xác (%)")
    ax2.set_ylim(0, 108)
    ax2.grid(axis="y", linestyle=":", alpha=0.6, color="#888888")
    ax2.set_axisbelow(True)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(loc="lower left", frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    ax2.set_title("(b) Kết quả theo mật độ ảnh huấn luyện")

    fig.tight_layout(w_pad=2.0)
    fig.savefig(OUT_DIR / "word_fig6_da_quy_mo_va_nhom_mau.png")
    plt.close(fig)


def fig7_taxonomy_and_cm(bench: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.3), gridspec_kw={"width_ratios": [1.0, 1.18]})

    hier = bench["hierarchicalAccuracy"]
    keys = ["speciesLevel", "genusLevel", "familyLevel", "kingdomLevel"]
    labels = ["Loài\n(3.570)", "Chi\n(1.698)", "Họ\n(338)", "Giới\n(4)"]
    t1 = [hier[k]["top1Accuracy"] for k in keys]
    t5 = [hier[k]["top5Accuracy"] for k in keys]

    x = np.arange(4)
    w = 0.34
    b1 = ax1.bar(x - w / 2, t1, width=w, color=C_DARK, edgecolor=C_BLACK, lw=0.85, label="Top-1 (%)")
    b2 = ax1.bar(x + w / 2, t5, width=w, color=C_LIGHT, edgecolor=C_BLACK, lw=0.85, hatch="//", label="Top-5 (%)")
    for idx_b, bars in enumerate((b1, b2)):
        dx = -0.06 if idx_b == 0 else 0.06
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2 + dx, h + 0.9, fmt_vn(h, 2) + "%",
                     ha="center", va="bottom", fontsize=6.9, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("Độ chính xác (%)")
    ax1.set_ylim(0, 108)
    ax1.grid(axis="y", linestyle=":", alpha=0.6, color="#888888")
    ax1.set_axisbelow(True)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.legend(loc="lower right", frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    ax1.set_title("(a) Độ chính xác theo 4 bậc phân loại")

    cm_data = bench["confusionMatrix12"]
    c_labels = cm_data["labels"]
    mat = np.array(cm_data["matrix"], dtype=np.int32)
    im = ax2.imshow(mat, cmap="Greys", vmin=0, vmax=max(1, int(mat.max())), aspect="auto")
    ax2.set_xticks(np.arange(len(c_labels)))
    ax2.set_yticks(np.arange(len(c_labels)))
    ax2.set_xticklabels(c_labels, rotation=42, ha="right", fontsize=7.2)
    ax2.set_yticklabels(c_labels, fontsize=7.4)
    ax2.set_xlabel("Loài dự đoán")
    ax2.set_ylabel("Loài thực tế")
    ax2.set_title("(b) Ma trận nhầm lẫn trên 12 loài tiêu biểu (Test)")

    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            if mat[i, j] > 0:
                col = "white" if mat[i, j] > 6 else C_BLACK
                ax2.text(j, i, str(mat[i, j]), ha="center", va="center",
                         color=col, fontsize=7.5, fontweight="bold")
    cbar = fig.colorbar(im, ax=ax2, fraction=0.042, pad=0.03)
    cbar.set_label("Số ảnh kiểm thử", fontsize=8.0)

    fig.tight_layout(w_pad=2.0)
    fig.savefig(OUT_DIR / "word_fig7_phan_cap_va_confusion.png")
    plt.close(fig)


def fig8_ood_and_latency(bench: dict) -> None:
    ood = bench["oodEvaluation"]
    m = bench["models"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 3.9))

    xs = np.linspace(0.0, 1.0, 400)
    mu_in, sd_in = ood["inDistMeanCosine"], ood["inDistStdCosine"]
    mu_oo, sd_oo = ood["oodMeanCosine"], ood["oodStdCosine"]
    pdf_in = np.exp(-0.5 * ((xs - mu_in) / max(sd_in, 1e-4)) ** 2)
    pdf_oo = np.exp(-0.5 * ((xs - mu_oo) / max(sd_oo, 1e-4)) ** 2)

    ax1.fill_between(xs, pdf_in, color=C_MID, alpha=0.35, label=f"Ảnh thực vật Val (TB={fmt_vn(mu_in, 4)})")
    ax1.plot(xs, pdf_in, color=C_BLACK, lw=1.6)
    ax1.fill_between(xs, pdf_oo, color=C_LIGHT, alpha=0.65, hatch="//", label=f"Mẫu OOD tổng hợp (TB={fmt_vn(mu_oo, 4)})")
    ax1.plot(xs, pdf_oo, color="#555555", lw=1.4)
    ax1.axvline(ood["calibratedCosineThreshold"], color=C_BLACK, linestyle="--", lw=1.4,
                label=f"Ngưỡng hiệu chuẩn ({fmt_vn(ood['calibratedCosineThreshold'], 4)})")
    ax1.axvline(0.35, color=C_DARK, linestyle=":", lw=1.4, label="Ngưỡng sàn mặc định (0,35)")

    ax1.set_xlabel("Độ tương đồng Cosine lớn nhất với 3.570 tâm cụm")
    ax1.set_ylabel("Mật độ chuẩn hóa")
    ax1.set_xlim(0.0, 1.0)
    ax1.set_ylim(0, 1.18)
    ax1.grid(True, linestyle=":", alpha=0.6, color="#888888")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.61, 0.98), fontsize=7.1, frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    ax1.set_title("(a) Phân bố điểm Cosine (Val vs. OOD tổng hợp)")

    items = [
        ("zero_shot_text", "Zero-Shot Text", "^", (0.004, -2.6)),
        ("cosine_centroid", "Cosine Centroid", "s", (0.004, 1.0)),
        ("weighted_knn", "Weighted k-NN", "o", (-0.027, -2.6)),
        ("bioclip2_classifier", "BioCLIP 2 Classifier", "*", (0.004, -0.8)),
    ]
    for k, name, mk, (dx, dy) in items:
        lat = m[k]["latencyMsPerImage"]
        t1 = m[k]["top1Accuracy"]
        sz = 165 if k == "bioclip2_classifier" else 85
        ax2.scatter(lat, t1, s=sz, color=C_BLACK if k == "bioclip2_classifier" else C_MID,
                    marker=mk, edgecolors=C_BLACK, linewidths=0.9, zorder=5)
        ax2.annotate(f"{name}\n({fmt_vn(t1)}% | {fmt_vn(lat, 3)} ms)",
                     xy=(lat, t1), xytext=(lat + dx, t1 + dy),
                     fontsize=7.4, fontweight="bold" if k == "bioclip2_classifier" else "normal")

    pf_x = [m["cosine_centroid"]["latencyMsPerImage"], m["bioclip2_classifier"]["latencyMsPerImage"]]
    pf_y = [m["cosine_centroid"]["top1Accuracy"], m["bioclip2_classifier"]["top1Accuracy"]]
    ax2.plot(pf_x, pf_y, linestyle="--", color=C_BLACK, lw=1.2, label="Đường hiệu quả tốc độ - độ chính xác")

    ax2.set_xlabel("Thời gian phân loại trên đặc trưng (ms/ảnh)")
    ax2.set_ylabel("Độ chính xác Top-1 (%)")
    ax2.set_xlim(0.0, 0.090)
    ax2.set_ylim(74, 93)
    ax2.grid(True, linestyle=":", alpha=0.6, color="#888888")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.legend(loc="lower right", frameon=True, facecolor=C_WHITE, edgecolor=C_BLACK)
    ax2.set_title("(b) Thời gian phân loại và Độ chính xác Top-1")

    fig.tight_layout(w_pad=2.0)
    fig.savefig(OUT_DIR / "word_fig8_kiem_dinh_ood_va_do_tre.png")
    plt.close(fig)


def main() -> None:
    bench = json.loads(BENCH_JSON.read_text(encoding="utf-8"))
    cat = json.loads(CAT_JSON.read_text(encoding="utf-8"))
    fig1_eda(cat, bench)
    fig2_pipeline(bench)
    fig3_bioclip2_architecture(bench)
    fig4_training_curves(bench)
    fig5_model_comparison(bench)
    fig6_multiscale_and_shots(bench)
    fig7_taxonomy_and_cm(bench)
    fig8_ood_and_latency(bench)
    print("GENERATED_8_BIOCLIP2_WORD_FIGURES_OK")


if __name__ == "__main__":
    main()
