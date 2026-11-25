"""
BioLens - Server Execution Entrypoint
Khởi chạy máy chủ FastAPI với Uvicorn.
"""

from __future__ import annotations

import sys
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configs.settings import HOST, PORT


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 72)
    print("BIOLENS VIETNAM - HE THONG NHAN DIEN THUC VAT & NAM DUOC LIEU (BIOCLIP 2)")
    print(f"May chu dang khoi dong tai: http://{HOST}:{PORT}")
    print("=" * 72)

    uvicorn.run(
        "backend.app:app",
        host=HOST,
        port=PORT,
        reload=True,
        reload_dirs=["backend", "configs"],
        reload_excludes=["data/*", "scripts/*", "storage/*", "*.json"]
    )


if __name__ == "__main__":
    main()
