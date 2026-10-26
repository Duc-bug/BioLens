import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.feature_extractor import extract_dataset_embeddings


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 72)
    print("BIOLENS - BƯỚC 2: TRÍCH XUẤT ĐẶC TRƯNG 3,570 LOÀI TRÊN GPU (CUDA FP16)")
    print("=" * 72)
    meta = extract_dataset_embeddings()
    print("-" * 72)
    print(f"[HOÀN TẤT] Đã trích xuất {meta['numValidSamples']:,} vector đặc trưng ({meta['featureDim']} chiều)")
    print(f"- Thiết bị xử lý : {meta['device']}")
    print(f"- Thời gian chạy : {meta['extractionTimeSeconds']}s ({meta['throughputImagesPerSec']} ảnh/giây)")


if __name__ == "__main__":
    main()
