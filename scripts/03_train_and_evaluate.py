"""
Bước 3: Huấn luyện & Tinh chỉnh Chuyên sâu (Phase 2 Fine-Tuning) 4 thuật toán Học máy trên 3,570 loài (CUDA).
"""
import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configs.settings import (
    EMBEDDINGS_MATRIX_PATH,
    EMBEDDINGS_LABELS_PATH,
    EMBEDDINGS_SPLITS_PATH,
)
from models.ml_classifiers import train_and_evaluate_all_models


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 76)
    print("BIOLENS - BƯỚC 3: HUẤN LUYỆN & SO SÁNH 4 THUẬT TOÁN HỌC MÁY (3,570 LOÀI)")
    print("=" * 76)

    X_all = np.load(EMBEDDINGS_MATRIX_PATH)
    y_all = np.load(EMBEDDINGS_LABELS_PATH)
    splits = np.load(EMBEDDINGS_SPLITS_PATH)

    num_classes = int(np.max(y_all)) + 1
    summary = train_and_evaluate_all_models(X_all, y_all, splits, num_classes=num_classes)

    print("\n" + "=" * 76)
    print("BẢNG TỔNG HỢP KẾT QUẢ THỰC NGHIỆM TRÊN TẬP TEST (3,570 LOÀI):")
    print("-" * 76)
    for key, m in summary["models"].items():
        print(
            f"- {m['modelName']:<38} | Top-1: {m['top1Accuracy']:>5.2f}% | "
            f"Top-5: {m['top5Accuracy']:>5.2f}% | F1: {m['weightedF1']:>5.2f}% | "
            f"Latency: {m['latencyMsPerImage']:.3f} ms"
        )
    print("=" * 76)


if __name__ == "__main__":
    main()
