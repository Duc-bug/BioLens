import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dataset.catalog_builder import build_full_catalog


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 72)
    print("BIOLENS - BƯỚC 1: XÂY DỰNG DANH MỤC 3,570 LOÀI & HỒ SƠ DƯỢC LIỆU")
    print("=" * 72)
    t0 = time.time()
    summary = build_full_catalog()
    elapsed = time.time() - t0
    print(f"[HOÀN TẤT TRONG {elapsed:.2f}s]")
    print(f"- Tổng số bản ghi CSV GBIF        : {summary['totalCsvRecords']:,}")
    print(f"- Tổng số loài có thư mục ảnh     : {summary['totalActiveSpecies']:,}")
    print(f"- Tổng số ảnh gốc trên ổ đĩa      : {summary['totalRawImages']:,}")
    print(f"- Tổng số ảnh đưa vào tập mẫu ML  : {summary['totalSampledImages']:,}")
    print(f"- Phân chia Train / Val / Test    : {summary['splitCounts']}")
    print(f"- Phân bố theo Giới (Kingdom)     : {summary['kingdomDistribution']}")


if __name__ == "__main__":
    main()
