"""
Khởi chạy nhanh Server ứng dụng Web BioLens tại http://127.0.0.1:8000
"""
import sys
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configs.settings import HOST, PORT


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 72)
    print(f"Đang khởi động BioLens Web Server tại: http://{HOST}:{PORT}")
    print("=" * 72)
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=False)
