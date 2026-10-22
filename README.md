# 🌿 BioLens Vietnam — Hệ thống Nhận diện Sinh vật & Thực vật Dược liệu Việt Nam qua Ảnh (3,570 Loài)

[![Dataset: VietMediSpecies2026](https://img.shields.io/badge/Dataset-VietMediSpecies2026%20(SciDB)-1E5631?style=flat-square)](https://www.scidb.cn/en/detail?dataSetId=d2e66ca3d73540739a39789d9b1cf989#p5)
[![Species: 3,570](https://img.shields.io/badge/Taxonomy-3,570%20Species%20(GBIF)-2D7A47?style=flat-square)](https://www.gbif.org/)
[![Images: 310,647](https://img.shields.io/badge/Full%20Dataset-310,647%20Images-1E5631?style=flat-square)](https://www.scidb.cn/en/detail?dataSetId=d2e66ca3d73540739a39789d9b1cf989#p5)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square)](https://www.python.org/)
[![PyTorch CUDA FP16](https://img.shields.io/badge/PyTorch-CUDA%20Mixed%20Precision%20FP16-EE4C2C?style=flat-square)](https://pytorch.org/)

**Đồ án Môn Học máy và Ứng dụng (Machine Learning & Applications)**  
**Bộ dữ liệu thực nghiệm chính thức:** `VietMediSpecies2026` — **3,570 loài có ảnh thực tế / 310,647 ảnh thực địa / 4,799 bản ghi chuẩn GBIF**.

---

## 📌 1. Tổng quan Dự án & Ba Mục tiêu Cốt lõi

**BioLens Vietnam** là hệ thống nhận diện quang học và tra cứu bách khoa thực vật/dược liệu Việt Nam đầu-cuối (End-to-End), giải quyết đồng thời 3 bài toán thực tiễn:

1. **Định danh chính xác trên quy mô lớn (Extreme-Scale 3,570 Species Classification)**:
   - Trích xuất đặc trưng hình thái sâu 960 chiều từ `MobileNetV3-Large` (`IMAGENET1K_V2`, tăng tốc GPU CUDA `FP16`) trên **100% bộ dữ liệu (310,647 ảnh)**.
   - Áp dụng **Quy trình 5 Tầng Chuẩn hóa Dữ liệu & Chống Học vẹt**: Chuẩn hóa quang học Z-Score RGB $\rightarrow$ Power-Law Whitening ($\alpha=0.55$) $\rightarrow$ L2 Hypersphere Normalization $\rightarrow$ BatchNorm1d + Label Smoothing + Logit Adjustment $\rightarrow$ Multi-Stage Dropout (`0.08` & `0.22`) + Early Stopping.
   - Tinh chỉnh không gian đặc trưng bằng mạng đa nhiệm phân cấp **`BotanicalMetricAdapter`** (huấn luyện đồng thời trên 3 bậc: *Loài - Chi - Họ*) và đối sánh 4 thuật toán Học máy (`Cosine Prototype`, `Weighted Cosine k-NN`, `Multi-class Linear SVM`, `Class-Balanced Cosine MLP`) cùng mô hình kết hợp **`BioLens Hybrid Ensemble`**.
2. **Hồ sơ Thực vật & Dược liệu 7 Mục Đa nguồn (Multi-Source Botanical Knowledge Harvesting)**:
   - Kết hợp dữ liệu phân loại chuẩn **GBIF**, từ điển **Chuyên khảo Dược liệu Cấp Họ & Cấp Chi** (`herbal_knowledge.py`) và bộ thu thập đa luồng từ **Wikipedia Tiếng Việt** (`05_harvest_species_knowledge.py`).
   - Cung cấp 7 mục chuyên sâu: *(1) Giới thiệu tổng quan, (2) Đặc điểm Hoa & Cụm hoa, (3) Đặc điểm Lá - Thân - Quả/Rễ, (4) Phân bố & Sinh thái tại Việt Nam, (5) Bộ phận dùng & Công dụng dược liệu, (6) Hoạt chất sinh học & Tính vị — Quy kinh Đông y, (7) Lưu ý an toàn & Độc tính*.
3. **Từ chối Nhận diện khi chụp Vật thể Lạ (2-Stage Open-Set OOD Rejection)**:
   - Khi người dùng đưa ảnh chụp con người, bàn ghế, màn hình máy tính, phương tiện giao thông, thú cưng hoặc ảnh bị mờ/tối đen, **Bộ lọc OOD 2 Tầng** tự động từ chối (`ROC-AUC = 0.9999`, tỉ lệ chặn ảnh lạ `100.0%`).

---

## 📥 2. Link Tải Bộ Dữ liệu (`VietMediSpecies2026`) & Cấu trúc Giải nén

Để tự huấn luyện lại (reproduce) hoặc chạy hệ thống trên toàn bộ 310,647 ảnh gốc, hãy tải bộ dữ liệu từ cổng lưu trữ dữ liệu khoa học quốc tế **Science Data Bank (SciDB)**:

### 🔗 Liên kết Tải Dữ liệu Chính thức
- **Trang chủ Dataset trên SciDB**: **[https://www.scidb.cn/en/detail?dataSetId=d2e66ca3d73540739a39789d9b1cf989#p5](https://www.scidb.cn/en/detail?dataSetId=d2e66ca3d73540739a39789d9b1cf989#p5)**
- **Dataset ID**: `d2e66ca3d73540739a39789d9b1cf989`
- **Cơ sở dữ liệu phân loại học đối chiếu**: [GBIF Backbone Taxonomy](https://www.gbif.org/) & [Royal Botanic Gardens, Kew (POWO)](https://powo.science.kew.org/)
- **Thành phần tải về từ SciDB**:
  1. File bảng danh mục chuẩn: `VietMediSpecies2026_metadata_dataset.csv` (`4,799` bản ghi loài chuẩn GBIF kèm tên Tiếng Việt, tên Khoa học, Giới, Ngành, Lớp, Bộ, Họ, Chi).
  2. Các gói nén ảnh thực địa giải nén thành **3,570 thư mục loài** (mỗi thư mục được đặt tên theo mã định danh số `speciesKey` của GBIF, ví dụ `3940600/` là *Sâm bố chính*, `2882449/` là *Sen hồng*...), tổng cộng **310,647 bức ảnh** (`.jpg`, `.jpeg`, `.png`, `.webp`).

### 📂 Sơ đồ Đặt Thư mục Dữ liệu trên Máy
Sau khi tải về và giải nén, bạn có thể đặt thư mục mã nguồn `BioLens` nằm ngay bên trong thư mục chứa dữ liệu (hoặc đặt ở bất kỳ đâu và trỏ đường dẫn trong file `.env`):

```text
E:/VietMediSpecies2026/                         <-- Thư mục gốc chứa Dataset (BIOLENS_DATASET_ROOT)
├── VietMediSpecies2026_metadata_dataset.csv    <-- File Metadata 4,799 bản ghi GBIF (BIOLENS_METADATA_CSV)
├── 3940600/                                    <-- Thư mục ảnh loài Sâm bố chính (Abelmoschus sagittifolius)
│   ├── 0001.jpg
│   └── ...
├── 2882449/                                    <-- Thư mục ảnh loài Sen hồng (Nelumbo nucifera)
├── ...                                         <-- Toàn bộ 3,570 thư mục loài (310,647 ảnh)
└── BioLens/                                    <-- Thư mục mã nguồn Repository này
    ├── configs/
    ├── dataset/
    ├── models/
    ├── backend/
    ├── frontend/
    ├── scripts/
    ├── storage/
    └── run_server.py
```

---

## 🛠️ 3. Hướng dẫn Cài đặt & Huấn luyện Mô hình từ A–Z (Training Guide)

### Bước 0: Cài đặt Môi trường Python & Cấu hình Đường dẫn (`.env`)

Yêu cầu hệ thống: **Python 3.10+** và khuyến nghị có **GPU NVIDIA hỗ trợ CUDA** (tối thiểu 4 GB VRAM) để tăng tốc trích xuất đặc trưng và huấn luyện `FP16`.

```bash
# 1. Di chuyển vào thư mục mã nguồn BioLens
cd BioLens

# 2. Tạo môi trường ảo (khuyên dùng) và cài đặt các thư viện phụ thuộc
python -m venv .venv
# Trên Windows PowerShell:
.venv\Scripts\Activate.ps1
# Trên Linux / macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# 3. Tạo file cấu hình .env từ file mẫu .env.example
cp .env.example .env
```

Mở file `.env` vừa tạo để kiểm tra đường dẫn dữ liệu của bạn:
```ini
BIOLENS_DATASET_ROOT=E:/VietMediSpecies2026
BIOLENS_METADATA_CSV=E:/VietMediSpecies2026_metadata_dataset.csv
BIOLENS_STORAGE_DIR=E:/VietMediSpecies2026/BioLens/storage
# Đặt 0 để huấn luyện trên toàn bộ 100% dữ liệu (310,647 ảnh)
BIOLENS_MAX_IMAGES_PER_SPECIES=0
```

---

### ⚡ Cách 1: Chạy Tự động Toàn bộ Pipeline Huấn luyện chỉ với 1 Lệnh

Nếu bạn muốn máy tự động chạy liền mạch cả 5 bước (từ quét dữ liệu $\rightarrow$ trích xuất đặc trưng $\rightarrow$ huấn luyện 4 mô hình + Ensemble $\rightarrow$ thu thập tri thức dược liệu $\rightarrow$ xuất 11 biểu đồ & báo cáo Word):

```bash
python scripts/run_full_pipeline.py
```

*(Mẹo: Nếu đã trích xuất xong file `features_fp16.npy` và chỉ muốn huấn luyện lại các thuật toán phân loại, bạn có thể chạy nhanh bằng lệnh: `python scripts/run_full_pipeline.py --skip-extract`)*.

---

### 🔍 Cách 2: Chạy Từng Bước Độc lập (Step-by-Step Training)

Bạn có thể chạy và kiểm tra kết quả của từng công đoạn theo thứ tự sau:

#### **Bước 1 — Quét Dữ liệu, Làm sạch & Chia tập Stratified 80/10/10**
```bash
python scripts/01_build_catalog.py
```
- **Chức năng**: Tự động loại bỏ thư mục rác `__MACOSX` và file ẩn `._*`, đối chiếu 3,570 thư mục ảnh với 4,799 bản ghi GBIF trong CSV, và chia Stratified thành: **Train (`248,310` ảnh - 80%)**, **Validation (`31,136` ảnh - 10%)**, **Test (`31,201` ảnh - 10%)**.
- **Đầu ra**: `storage/catalog/species_catalog.json`, `storage/catalog/dataset_splits.json`, `storage/catalog/species_knowledge.json`.

#### **Bước 2 — Trích xuất Vector Đặc trưng Hình thái 960 chiều trên GPU (`FP16`)**
```bash
python scripts/02_extract_features.py
```
- **Chức năng**: Đưa toàn bộ 310,647 ảnh qua mạng `BotanicalDualBackbone` (`MobileNetV3-Large IMAGENET1K_V2` với Mixed Precision `FP16` và chuẩn hóa quang học Z-Score RGB). Hỗ trợ **Incremental Resume** (tự động lưu tiến độ và nối tiếp nếu bị ngắt giữa chừng).
- **Đầu ra**: `storage/embeddings/features_fp16.npy` (`310,647 × 960`), `labels_int32.npy`, `splits_uint8.npy`, `extraction_meta.json`.

#### **Bước 3 — Chuẩn hóa 5 Tầng, Fine-tune Metric Adapter & Huấn luyện 4 Mô hình Học máy + Ensemble**
```bash
python scripts/03_train_and_evaluate.py
```
- **Chức năng**:
  1. Áp dụng **Power-Law Whitening ($\alpha=0.55$)** và huấn luyện mạng đa nhiệm phân cấp **`BotanicalMetricAdapter`** (`28 Epochs`, học đồng thời trên 3 bậc *Loài - Chi - Họ*, kèm Dual Dropout `0.08` & `0.22`).
  2. Huấn luyện và đánh giá 4 thuật toán Học máy + mô hình kết hợp:
     - **Model 1**: `Attention-Pruned Multi-Subcenter Cosine Prototype` (2 tâm phụ/loài).
     - **Model 2**: `Inverse Class-Frequency Balanced Cosine k-NN` ($k = 19, \tau = 21.0$).
     - **Model 3**: `Hard-Margin Multi-class Linear SVM` (`40 Epochs`, Crammer-Singer Hinge Loss + Logit Adjustment).
     - **Model 4**: `Class-Balanced SE-Residual Cosine MLP` (`48 Epochs`, Manifold Mixup, CosFace Margin, Multi-Stage Dropout & Best Validation Checkpoint).
     - **Model 5**: `BioLens Hybrid Ensemble` (kết hợp có trọng số 4 mô hình trên).
  3. Hiệu chuẩn ngưỡng **Bộ lọc Từ chối Vật thể Lạ 2 Tầng (2-Stage OOD Gate)** và xuất bảng đối sánh **Ablation Study (Phần 1 Baseline vs Phần 2 Fine-tuned)** cùng đánh giá đa quy mô (`Top-50`, `Top-100`, `Top-500`, `Full 3,570 loài`).
- **Đầu ra**: Trọng số mô hình tại `storage/checkpoints/classifiers_bundle.pt` và báo cáo định lượng tại `storage/reports/benchmark_report.json`.

#### **Bước 4 — Thu thập & Làm giàu Tri thức Thực vật - Dược liệu Đa nguồn**
```bash
python scripts/05_harvest_species_knowledge.py
```
- **Chức năng**: Tiền truy vấn đa luồng (Multi-threaded) tới Wikipedia Tiếng Việt (REST Summary API + MediaWiki Search API) kết hợp từ điển Chuyên khảo Dược liệu Cấp Họ & Cấp Chi để hoàn thiện hồ sơ 7 mục cho toàn bộ 3,570 loài.
- **Đầu ra**: `storage/catalog/wiki_cache.json` và cập nhật `storage/catalog/species_knowledge.json`.

#### **Bước 5 — Vẽ 11 Biểu đồ Khoa học (300 DPI) & Xuất Báo cáo Đồ án Word (`.docx`)**
```bash
python scripts/04_generate_word_report.py
```
- **Chức năng**: Tự động vẽ 11 biểu đồ phân tích thực nghiệm độ phân giải cao vào `storage/reports/` và tổng hợp thành file báo cáo Word hoàn chỉnh `Bao_Cao_Do_An_BioLens_Phan_2_Finetuned_Day_Du.docx` (đồng thời bảo toàn bản báo cáo cũ Phần 1 tại `Bao_Cao_Do_An_BioLens_Phan_1_Baseline.docx`).

---

### 🌐 Bước 6: Khởi chạy Ứng dụng Web BioLens
Sau khi đã có mô hình (hoặc chạy trực tiếp từ bộ checkpoint đã huấn luyện), khởi động máy chủ FastAPI bằng lệnh:

```bash
python run_server.py
```
Mở trình duyệt truy cập: **`http://127.0.0.1:8000`**

---

## 📊 4. Kết quả Thực nghiệm & Đối sánh Ablation Study (Phần 1 vs Phần 2)

### 4.1. Bảng Đối sánh Ablation Study trên Toàn bộ 3,570 Loài (Full 100% Dataset — 310,647 Ảnh)
Việc mở rộng huấn luyện lên **100% dữ liệu (310,647 ảnh)** kết hợp **Quy trình 5 Tầng Chuẩn hóa & Chống Học vẹt** và **Fine-tune Không gian Đặc trưng (`BotanicalMetricAdapter`)** ở **Phần 2 (`v2_finetuned`)** tạo ra bước nhảy vọt về độ chính xác trên tập Test độc lập (`31,201` ảnh) so với **Phần 1 (`v1_baseline`)**:

| Mô hình Học máy | Phần 1 Top-1 (`v1`) | Phần 2 Top-1 (`v2`) | Mức tăng Top-1 | Phần 1 Top-5 (`v1`) | Phần 2 Top-5 (`v2`) | Mức tăng Top-5 | Weighted F1 (`v1 → v2`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Cosine Prototype Classifier** | 13.80% | **20.11%** | **+6.31%** | 25.63% | **34.97%** | **+9.34%** | 12.01% → **20.07%** |
| **2. Weighted Cosine k-NN** | 19.50% | **36.85%** | **+17.35%** | 30.24% | **50.79%** | **+20.55%** | 18.12% → **36.36%** |
| **3. Multi-class Linear SVM** | 19.03% | **31.49%** | **+12.46%** | 35.50% | **50.59%** | **+15.09%** | 18.07% → **29.55%** |
| **4. Class-Balanced Cosine MLP** | 28.14% | **38.57%** | **+10.43%** | 46.78% | **59.04%** | **+12.26%** | 25.95% → **37.27%** |
| **5. BioLens Hybrid Ensemble** | 29.17% | **41.01%** | **+11.84%** | 47.49% | **60.86%** | **+13.37%** | 26.98% → **39.89%** |

> **Ý nghĩa thống kê:** Trên không gian phân loại cực lớn **3,570 loài**, xác suất đoán ngẫu nhiên (Random Guess) chỉ là **`0.028%`**. Độ chính xác Top-1 của **`BioLens Hybrid Ensemble`** đạt **`41.01%`** (gấp **1,464 lần** ngẫu nhiên) và Top-5 đạt **`60.86%`**. Ở bậc **Họ thực vật (Family - 338 họ)**, hệ thống đạt **`71.23%` Top-5** và ở bậc **Giới (Kingdom)** đạt **`99.78%` Top-5**.

### 4.2. Hiệu năng theo Đa quy mô Số lượng Loài (Multi-Scale Evaluation — Phiên bản Fine-tuned v2)

| Quy mô Đánh giá (Chọn khách quan từ tập Validation) | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Weighted F1 | Độ trễ Suy luận |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Tập Chuẩn Top-50 Loài Hoa & Dược liệu Tiêu biểu** | **92.48%** | **96.41%** | **97.71%** | **92.45%** | `0.014 ms` |
| **Tập Chuẩn Top-100 Loài Phổ biến tại Việt Nam** | **88.10%** | **95.06%** | **96.28%** | **88.08%** | `0.081 ms` |
| **Tập Mở rộng Top-500 Loài** | **75.23%** | **86.11%** | **89.89%** | **74.82%** | `0.086 ms` |
| **Toàn bộ 3,570 Loài (Extreme Full-Scale — 31,201 ảnh Test)** | **41.01%** | **55.01%** | **60.86%** | **39.89%** | `0.081 ms` |

---

## 🏗️ 5. Cấu trúc Thư mục Mã nguồn (Project Structure)

```text
BioLens/
├── configs/
│   └── settings.py                      # Cấu hình trung tâm (Biến môi trường .env & Đường dẫn)
├── dataset/
│   ├── catalog_builder.py               # Quét 3,570 thư mục loài, lọc sạch __MACOSX & chia Stratified 80/10/10
│   ├── herbal_knowledge.py              # Từ điển Chuyên khảo Dược liệu Cấp Họ & Cấp Chi Việt Nam
│   └── knowledge_enricher.py            # Tổng hợp Hồ sơ 7 mục + Kết nối Wikipedia / GBIF / Kew POWO
├── models/
│   ├── feature_extractor.py             # Mạng trích xuất kép BotanicalDualBackbone (CUDA FP16 + Resume)
│   ├── ml_classifiers.py                # Chuẩn hóa 5 tầng, Metric Adapter & 4 thuật toán ML + Ensemble
│   ├── ood_filter.py                    # Bộ lọc 2 tầng từ chối nhận diện vật thể lạ (2-Stage OOD Gate)
│   └── inference_engine.py              # Động cơ suy luận thời gian thực trên GPU
├── backend/
│   ├── app.py                           # Khởi tạo FastAPI Server & Static Mounts
│   └── routes.py                        # Hệ thống REST API (/api/identify, /api/species, /api/benchmarks...)
├── frontend/
│   ├── index.html                       # Giao diện Thực vật học Sáng Tối giản (Clean Light Botanical UI)
│   ├── css/main.css                     # Stylesheet chuẩn thiết kế hiện đại
│   └── js/
│       ├── camera.js                    # Điều khiển ống kính Camera WebRTC trực tiếp
│       └── app.js                       # Điều phối nhận diện, Bách khoa 3,570 loài & Bảng thực nghiệm ML
├── scripts/
│   ├── run_full_pipeline.py             # Chạy tự động toàn bộ 5 bước chỉ với 1 lệnh duy nhất
│   ├── 01_build_catalog.py              # Bước 1: Xây dựng danh mục 3,570 loài & chia tập Train/Val/Test
│   ├── 02_extract_features.py           # Bước 2: Trích xuất 310,647 vector đặc trưng 960 chiều (FP16)
│   ├── 03_train_and_evaluate.py         # Bước 3: Fine-tune mô hình, đánh giá Đa quy mô & Ablation Study
│   ├── 04_generate_word_report.py       # Bước 5: Vẽ 11 biểu đồ 300 DPI & Xuất Báo cáo Word (.docx)
│   └── 05_harvest_species_knowledge.py  # Bước 4: Thu thập đa luồng tri thức từ Wikipedia Tiếng Việt
├── docs/
│   └── ARCHITECTURE.md                  # Tài liệu kiến trúc hệ thống & công thức toán học chi tiết
├── storage/
│   ├── catalog/
│   │   └── wiki_cache.json              # Bộ nhớ đệm bài viết bách khoa Wikipedia Tiếng Việt đã xác thực
│   └── reports/
│       ├── v1_baseline/                 # Lưu trữ nguyên vẹn Báo cáo Word & Biểu đồ Phần 1 (Baseline v1)
│       ├── v2_finetuned/                # Lưu trữ Báo cáo Word & 11 Biểu đồ Phần 2 (Fine-tuned v2)
│       ├── Bao_Cao_Do_An_BioLens_Phan_1_Baseline.docx
│       ├── Bao_Cao_Do_An_BioLens_Phan_2_Finetuned_Day_Du.docx
│       └── Bao_Cao_Do_An_BioLens_Hoc_May_Va_Ung_Dung.docx
├── .env.example                         # File mẫu cấu hình biến môi trường
├── .gitignore                           # Cấu hình loại trừ file nhị phân nặng khi đẩy lên GitHub
├── requirements.txt                     # Danh sách thư viện phụ thuộc
└── run_server.py                        # Điểm khởi chạy ứng dụng Web BioLens
```
