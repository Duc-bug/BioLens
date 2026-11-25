# -*- coding: utf-8 -*-
"""
Tạo Báo cáo Đồ án Học phần Học máy và Ứng dụng — BioLens Vietnam (chuẩn mẫu đen trắng VLU).
Trích xuất số liệu thực nghiệm từ ml_benchmark_results.json, extraction_meta.json,
species_catalog.json và nutraceutical_registry.json của mô hình BioCLIP 2.
"""

from __future__ import annotations

import collections
import json
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BIOLENS_DIR = Path(r"e:\VietMediSpecies2026\BioLens")
OUT_DOCX = BIOLENS_DIR / "docs" / "Bao_Cao_Toan_Tap_BioLens_Vietnam_VLU.docx"
VLU_TEMPLATE = Path(
    r"C:\Users\nthie\.gemini\antigravity\brain\a200246b-04ca-4ac0-b258-40e026e0173f\.user_uploaded\media_1795199959704_a853e725.docx"
)
VLU_LOGO_TMP = BIOLENS_DIR / "docs" / "_tmp_vlu_logo_master.png"
BLACK = RGBColor(0x00, 0x00, 0x00)


def fmt_vn(val: float, dec: int = 2) -> str:
    return f"{val:.{dec}f}".replace(".", ",")


def fmt_int(val: int) -> str:
    return f"{val:,}".replace(",", ".")


def extract_vlu_logo() -> Path | None:
    if VLU_TEMPLATE.exists():
        with zipfile.ZipFile(VLU_TEMPLATE, "r") as z:
            if "word/media/image1.png" in z.namelist():
                VLU_LOGO_TMP.write_bytes(z.read("word/media/image1.png"))
                return VLU_LOGO_TMP
    return None


def set_cell_shading(cell, fill_hex: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tcPr.append(shd)


def set_table_borders(table, color="000000", sz="4", val="single") -> None:
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), val)
        if val != "none":
            el.set(qn("w:sz"), sz)
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), color)
        borders.append(el)
    tblPr.append(borders)


def prevent_row_split(row) -> None:
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def add_page_border(section) -> None:
    sectPr = section._sectPr
    pgBorders = OxmlElement("w:pgBorders")
    pgBorders.set(qn("w:offsetFrom"), "page")
    pgBorders.set(qn("w:display"), "firstPage")
    for side in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "double")
        b.set(qn("w:sz"), "12")
        b.set(qn("w:space"), "24")
        b.set(qn("w:color"), "000000")
        pgBorders.append(b)
    sectPr.append(pgBorders)


def enable_auto_update_fields(doc: Document) -> None:
    update_el = OxmlElement("w:updateFields")
    update_el.set(qn("w:val"), "true")
    doc.settings.element.append(update_el)


def style_run(run, size=13, bold=False, italic=False) -> None:
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = BLACK


def add_word_field(p, instr: str, size: float = 12.5, bold: bool = False, italic: bool = False) -> None:
    run = p.add_run()
    style_run(run, size=size, bold=bold, italic=italic)
    for ftype in ("begin", "separate", "end"):
        if ftype == "separate":
            instrText = OxmlElement("w:instrText")
            instrText.set(qn("xml:space"), "preserve")
            instrText.text = instr
            run._r.append(instrText)
        fc = OxmlElement("w:fldChar")
        fc.set(qn("w:fldCharType"), ftype)
        run._r.append(fc)


def add_page_number_footer(section) -> None:
    section.different_first_page_header_footer = True
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(p.add_run("Trang "), 11)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    p._p.append(fld)


def add_body(doc: Document, text: str, space_after: float = 6.0, italic: bool = False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.first_line_indent = Cm(0.75)
    style_run(p.add_run(text), 13, italic=italic)
    return p


def add_bullet(doc: Document, text: str, bold_prefix: str = ""):
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.26
    p.paragraph_format.space_after = Pt(4)
    if bold_prefix:
        style_run(p.add_run(bold_prefix), 13, bold=True)
    style_run(p.add_run(text), 13)
    return p


def add_h1(doc: Document, text: str, page_break: bool = True, centered: bool = False):
    if page_break:
        doc.add_page_break()
    p = doc.add_heading(text, level=1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.keep_with_next = True
    for r in p.runs:
        style_run(r, 15, bold=True)
    return p


def add_h2(doc: Document, text: str):
    p = doc.add_heading(text, level=2)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    for r in p.runs:
        style_run(r, 13.5, bold=True)
    return p


def add_h3(doc: Document, text: str):
    p = doc.add_heading(text, level=3)
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    for r in p.runs:
        style_run(r, 13, bold=True, italic=True)
    return p


def add_caption(doc: Document, label_type: str, title_after_colon: str, is_table: bool = True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6 if is_table else 2)
    p.paragraph_format.space_after = Pt(4 if is_table else 8)
    if is_table:
        p.paragraph_format.keep_with_next = True
    style_run(p.add_run(f"{label_type} "), 12, bold=True, italic=(not is_table))
    add_word_field(p, f" SEQ {label_type} \\* ARABIC ", size=12, bold=True, italic=(not is_table))
    style_run(p.add_run(f": {title_after_colon}"), 12, bold=is_table, italic=(not is_table))
    return p


def add_styled_table(
    doc: Document,
    caption_text: str,
    headers: list[str],
    rows: list[list[str]],
    col_widths_cm: list[float] | None = None,
    bold_last_row: bool = False,
    left_cols: set[int] | None = None,
):
    add_caption(doc, "Bảng", caption_text, is_table=True)
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, color="000000", sz="4", val="single")

    hdr_row = tbl.rows[0]
    prevent_row_split(hdr_row)
    hdr_row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))

    for j, h_text in enumerate(headers):
        cell = hdr_row.cells[j]
        set_cell_shading(cell, "F2F2F2")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        style_run(p.add_run(h_text), 10.5, bold=True)

    lcols = left_cols if left_cols is not None else {0}
    for i, row_data in enumerate(rows):
        row = tbl.rows[i + 1]
        prevent_row_split(row)
        is_last = bold_last_row and (i == len(rows) - 1)
        for j, val in enumerate(row_data):
            cell = row.cells[j]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j in lcols else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            style_run(p.add_run(val), 10.5, bold=is_last)

    if col_widths_cm:
        tbl.autofit = False
        for row in tbl.rows:
            for j, w in enumerate(col_widths_cm):
                row.cells[j].width = Cm(w)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(5)


def add_figure(doc: Document, rel_path: str, caption_text: str, width_cm: float = 15.2):
    img_path = BIOLENS_DIR / rel_path
    if not img_path.exists():
        raise FileNotFoundError(f"Missing figure: {img_path}")
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(3)
    p_img.paragraph_format.keep_with_next = True
    p_img.add_run().add_picture(str(img_path), width=Cm(width_cm))
    add_caption(doc, "Hình", caption_text, is_table=False)


def add_formula(doc: Document, formula_text: str, eq_number: str):
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    set_table_borders(tbl, val="none")
    c0, c1 = tbl.rows[0].cells
    c0.width = Cm(14.0)
    c1.width = Cm(2.0)
    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(4)
    p0.paragraph_format.space_after = Pt(4)
    style_run(p0.add_run(formula_text), 12.0, italic=True)
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p1.paragraph_format.space_before = Pt(4)
    p1.paragraph_format.space_after = Pt(4)
    style_run(p1.add_run(f"({eq_number})"), 12.0)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(3)


def build_master_report() -> None:
    bench = json.loads((BIOLENS_DIR / "storage" / "reports" / "ml_benchmark_results.json").read_text(encoding="utf-8"))
    ext_meta = json.loads((BIOLENS_DIR / "storage" / "embeddings" / "extraction_meta.json").read_text(encoding="utf-8"))
    cat_data = json.loads((BIOLENS_DIR / "storage" / "catalog" / "species_catalog.json").read_text(encoding="utf-8"))
    nutra_reg = json.loads((BIOLENS_DIR / "storage" / "catalog" / "nutraceutical_registry.json").read_text(encoding="utf-8"))

    import torch
    ckpt = torch.load(BIOLENS_DIR / "storage" / "checkpoints" / "bioclip2_classifier.pt", map_location="cpu", weights_only=True)
    res_alpha_val = float(ckpt["state_dict"]["res_alpha"].item())

    grade_counts = collections.Counter()
    species_with_recipes = 0
    total_recipes = 0
    for _, prof in nutra_reg.items():
        if isinstance(prof, dict):
            g = prof.get("edibilityGrade") or "UNKNOWN"
            grade_counts[str(g)] += 1
            recs = prof.get("recipes") or []
            if recs:
                species_with_recipes += 1
                total_recipes += len(recs)

    cat_sum = cat_data["summary"]
    kd = cat_sum["kingdomDistribution"]
    m = bench["models"]
    zs = m["zero_shot_text"]
    cen = m["cosine_centroid"]
    knn = m["weighted_knn"]
    clf = m["bioclip2_classifier"]
    ms = bench["multiscaleBenchmarks"]
    hier = bench["hierarchicalAccuracy"]
    sg = bench["shotGroupBreakdown"]
    ood = bench["oodEvaluation"]
    hist = bench["trainingHistory"]

    safe_food_total = (
        grade_counts["BEVERAGE_INFUSION"]
        + grade_counts["SPICE_AROMATIC"]
        + grade_counts["CULINARY_TONIC"]
    )

    logo_path = extract_vlu_logo()
    doc = Document()

    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.0)
    add_page_border(section)
    add_page_number_footer(section)
    enable_auto_update_fields(doc)

    for st_name in ("Normal", "Heading 1", "Heading 2", "Heading 3", "TOC 1", "TOC 2", "TOC 3"):
        if st_name in doc.styles:
            st = doc.styles[st_name]
            st.font.name = "Times New Roman"
            st.font.color.rgb = BLACK
            if st_name == "Normal":
                st.font.size = Pt(13)

    # ==========================================================================
    # TRANG BÌA CHUẨN VLU
    # ==========================================================================
    def center_line(text, size=14, bold=False, italic=False, before=0, after=4):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.18
        style_run(p.add_run(text), size, bold=bold, italic=italic)

    center_line("TRƯỜNG ĐẠI HỌC VĂN LANG", 14, bold=True, before=4, after=2)
    center_line("KHOA CÔNG NGHỆ THÔNG TIN", 14, bold=True, after=14)

    if logo_path and logo_path.exists():
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(2)
        p_logo.paragraph_format.space_after = Pt(16)
        p_logo.add_run().add_picture(str(logo_path), width=Cm(4.0))

    center_line("BÁO CÁO ĐỒ ÁN HỌC PHẦN", 15, bold=True, after=4)
    center_line("HỌC MÁY VÀ ỨNG DỤNG", 16.5, bold=True, after=4)
    center_line("NGÀNH: CÔNG NGHỆ THÔNG TIN", 13.5, bold=True, after=18)

    center_line("ĐỀ TÀI:", 13.5, bold=True, after=6)
    center_line(
        "XÂY DỰNG HỆ THỐNG NHẬN DIỆN THỰC VẬT VÀ NẤM DƯỢC LIỆU VIỆT NAM\n"
        "QUY MÔ 3.570 LOÀI DỰA TRÊN MÔ HÌNH NỀN SINH HỌC BIOCLIP 2\n"
        "KẾT HỢP KIỂM SOÁT AN TOÀN Y SINH",
        14.5,
        bold=True,
        after=26,
    )

    info_tbl = doc.add_table(rows=4, cols=2)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_tbl.autofit = False
    set_table_borders(info_tbl, val="none")
    meta_rows = [
        ("Giảng viên hướng dẫn:", "ThS. Nguyễn Thái Anh"),
        ("Sinh viên thực hiện:", "Nguyễn Thiện Đức"),
        ("Mã số sinh viên:", "2373401010100"),
        ("Email liên hệ:", "nthienduc5@gmail.com"),
    ]
    for idx_r, (k_txt, v_txt) in enumerate(meta_rows):
        c0, c1 = info_tbl.rows[idx_r].cells
        c0.width = Cm(5.6)
        c1.width = Cm(7.4)
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(4)
        style_run(p0.add_run(k_txt), 13, bold=True)
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(4)
        style_run(p1.add_run(v_txt), 13, bold=(idx_r in (0, 1)))

    center_line("TP. Hồ Chí Minh, Năm 2026", 13, italic=True, before=42, after=0)

    # ==========================================================================
    # LỜI CẢM ƠN & TÓM TẮT ĐỒ ÁN
    # ==========================================================================
    add_h1(doc, "LỜI CẢM ƠN", page_break=True, centered=True)
    add_body(
        doc,
        "Em xin gửi lời cảm ơn chân thành đến ThS. Nguyễn Thái Anh, giảng viên học phần Học máy và Ứng dụng tại Khoa Công nghệ Thông tin, Trường Đại học Văn Lang. Những góp ý trực tiếp của Thầy về cách lựa chọn mô hình phù hợp với bản chất dữ liệu, kiểm soát tính trung thực của số liệu thực nghiệm và trình bày sơ đồ kỹ thuật rõ ràng đã giúp em hoàn thiện đồ án này một cách bài bản.",
    )
    add_body(
        doc,
        "Em cũng xin trân trọng cảm ơn nhóm tác giả của bộ dữ liệu mở VietMediSpecies2026 trên cổng lưu trữ Science Data Bank (SciDB) và nhóm nghiên cứu Imageomics đã công bố mô hình nền sinh học BioCLIP 2 phục vụ cộng đồng học thuật. Do thời gian và kinh nghiệm thực tế còn hạn chế, báo cáo khó tránh khỏi thiếu sót; em rất mong nhận được ý kiến nhận xét của Quý Thầy Cô để tiếp tục cải thiện hệ thống.",
    )

    add_h1(doc, "TÓM TẮT ĐỒ ÁN", page_break=False, centered=True)
    add_body(
        doc,
        f"Đồ án trình bày quá trình xây dựng và đánh giá hệ thống BioLens Vietnam nhằm hỗ trợ nhận diện tự động qua ảnh cho {fmt_int(cat_sum['totalActiveSpecies'])} loài thực vật và nấm dược liệu tại Việt Nam trên bộ dữ liệu thực địa VietMediSpecies2026 ({fmt_int(cat_sum['totalRawImages'])} ảnh hợp lệ, đối chiếu từ {fmt_int(cat_sum['totalCsvRecords'])} bản ghi phân loại chuẩn GBIF). Để giải quyết đồng thời bài toán phân loại chi tiết (fine-grained) giữa các loài cùng Chi/Họ và hiện tượng mất cân bằng số lượng mẫu, hệ thống sử dụng duy nhất một mô hình nền thị giác - ngôn ngữ sinh học là BioCLIP 2 (kiến trúc ViT-L/14, kích thước đầu vào 224×224 pixel, vector đặc trưng {ext_meta['featureDim']} chiều) kết hợp tăng cường hai góc nhìn lật ngang.",
    )
    add_body(
        doc,
        f"Trên không gian đặc trưng {ext_meta['featureDim']} chiều của BioCLIP 2, đồ án xây dựng đầu phân loại có nhánh dư chuẩn hóa Cosine mang tên BioCLIP2TaxonomicClassifier, trong đó ma trận trọng số {fmt_int(cat_sum['totalActiveSpecies'])} lớp được khởi tạo kết hợp từ biểu diễn văn bản phân cấp GBIF (trọng số 0,35) và tâm cụm ảnh huấn luyện (trọng số 0,65), sau đó huấn luyện 50 vòng lặp với kỹ thuật hiệu chỉnh Logit Adjustment (hệ số 0,50), trộn đặc trưng Mixup, làm mượt nhãn và trung bình trượt hàm mũ (EMA). Thực nghiệm độc lập trên {fmt_int(bench['numTestSamples'])} ảnh kiểm thử cho thấy mô hình đạt độ chính xác Top-1 là {fmt_vn(clf['top1Accuracy'])}%, Top-3 là {fmt_vn(clf['top3Accuracy'])}%, Top-5 là {fmt_vn(clf['top5Accuracy'])}%, Macro-F1 đạt {fmt_vn(clf['macroF1'])}% và Weighted-F1 đạt {fmt_vn(clf['weightedF1'])}%, cao hơn cả ba phương pháp đối chứng trên cùng đặc trưng gồm Zero-Shot Text ({fmt_vn(zs['top1Accuracy'])}%), Cosine Nearest Centroid ({fmt_vn(cen['top1Accuracy'])}%) và Weighted Cosine k-NN ({fmt_vn(knn['top1Accuracy'])}%).",
    )
    add_body(
        doc,
        f"Để đưa mô hình vào ứng dụng Web thực tế thông qua máy chủ FastAPI, hệ thống tích hợp bộ lọc từ chối ảnh ngoài miền hai tầng (kết hợp kiểm tra độ nét Laplacian, so khớp ngữ nghĩa Zero-Shot trên 11 câu mô tả miền của BioCLIP 2 và ngưỡng tương đồng Cosine {fmt_vn(ood['calibratedCosineThreshold'], 4)}) cùng mô-đun gợi ý dược thiện có kiểm soát an toàn y sinh: cảnh báo không ăn uống đối với {grade_counts['TOXIC_FORBIDDEN']} loài có độc, giới hạn tra cứu chuyên môn đối với {fmt_int(grade_counts['MEDICINAL_ONLY'])} loài chỉ dùng làm thuốc, và cung cấp thông tin tham khảo ẩm thực/trà thảo mộc cho {safe_food_total} loài an toàn ({species_with_recipes} loài có công thức định lượng chi tiết).",
    )

    # ==========================================================================
    # MỤC LỤC, DANH MỤC HÌNH, DANH MỤC BẢNG, CHỮ VIẾT TẮT
    # ==========================================================================
    add_h1(doc, "MỤC LỤC", page_break=True, centered=True)
    p_toc = doc.add_paragraph()
    add_word_field(p_toc, ' TOC \\o "1-3" \\h \\z \\u ', size=12)

    add_h1(doc, "DANH MỤC HÌNH VẼ", page_break=True, centered=True)
    p_tof = doc.add_paragraph()
    add_word_field(p_tof, ' TOC \\h \\z \\c "Hình" ', size=12)

    add_h1(doc, "DANH MỤC BẢNG BIỂU", page_break=False, centered=True)
    p_tot = doc.add_paragraph()
    add_word_field(p_tot, ' TOC \\h \\z \\c "Bảng" ', size=12)

    add_h1(doc, "DANH MỤC TỪ VIẾT TẮT", page_break=False, centered=True)
    add_styled_table(
        doc,
        "Giải nghĩa các ký hiệu và thuật ngữ viết tắt sử dụng trong báo cáo",
        ["Từ viết tắt", "Thuật ngữ tiếng Anh", "Nghĩa tiếng Việt trong báo cáo"],
        [
            ["API", "Application Programming Interface", "Giao diện lập trình ứng dụng"],
            ["AUC / ROC", "Area Under the ROC Curve", "Diện tích dưới đường cong đặc trưng hoạt động"],
            ["CLIP", "Contrastive Language-Image Pre-training", "Tiền huấn luyện tương phản ngôn ngữ - hình ảnh"],
            ["EMA", "Exponential Moving Average", "Trung bình trượt hàm mũ của trọng số mô hình"],
            ["FP16", "16-bit Floating Point", "Định dạng số thực dấu phẩy động bán chính xác 16-bit"],
            ["GBIF", "Global Biodiversity Information Facility", "Cơ sở dữ liệu thông tin đa dạng sinh học toàn cầu"],
            ["k-NN", "k-Nearest Neighbors", "Thuật toán k láng giềng gần nhất"],
            ["OOD", "Out-of-Distribution", "Dữ liệu nằm ngoài miền phân phối huấn luyện"],
            ["POWO", "Plants of the World Online", "Cơ sở dữ liệu thực vật thế giới của Vườn Thực vật Kew"],
            ["TTA", "Test-Time Augmentation", "Tăng cường dữ liệu tại thời điểm trích xuất/suy luận"],
            ["ViT", "Vision Transformer", "Kiến trúc Transformer áp dụng cho thị giác máy tính"],
        ],
        col_widths_cm=[2.6, 6.4, 7.0],
        left_cols={1, 2},
    )

    # ==========================================================================
    # CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI VÀ PHÂN TÍCH BÀI TOÁN
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI VÀ PHÂN TÍCH BÀI TOÁN", page_break=True)

    add_h2(doc, "1.1. Bối cảnh thực tiễn và lý do chọn đề tài")
    add_body(
        doc,
        "Việt Nam có hệ thực vật và nấm tự nhiên phong phú, trong đó hàng nghìn loài được sử dụng trong đời sống dưới dạng rau gia vị, trà thảo mộc hoặc vị thuốc cổ truyền. Tuy nhiên, việc định danh chính xác một mẫu cây hoặc nấm bắt gặp ngoài thực địa không đơn giản đối với người không có chuyên môn thực vật học. Nhiều loài khác nhau về dược tính và độc tính lại có hình dáng lá, màu sắc hoa hoặc tán nấm khá giống nhau khi quan sát bằng mắt thường.",
    )
    add_body(
        doc,
        "Trong vài năm gần đây, các mô hình thị giác máy tính đã hỗ trợ tốt việc nhận diện ảnh thực vật trên điện thoại và trình duyệt web. Dù vậy, phần lớn các đề tài thử nghiệm ở quy mô nhỏ thường chỉ phân loại từ vài chục đến vài trăm loài phổ biến, chưa phản ánh sát độ phức tạp khi số lượng lớp mở rộng lên hàng nghìn loài bản địa. Bên cạnh đó, nếu một ứng dụng chỉ dừng ở việc xuất tên loài mà thiếu bước lọc ảnh lỗi, ảnh ngoài miền (như chụp nhầm đồ vật, con người, động vật) và thiếu cảnh báo đối với các loài có độc, người dùng có thể hiểu nhầm kết quả dự đoán của máy thành khuyến nghị sử dụng trực tiếp.",
    )
    add_body(
        doc,
        "Xuất phát từ thực tế đó, đồ án chọn xây dựng hệ thống BioLens Vietnam trên bộ dữ liệu thực địa quy mô lớn VietMediSpecies2026, kết hợp giữa bài toán phân loại học máy nhiều lớp với cơ chế lọc ảnh đầu vào và tra cứu thông tin an toàn dược liệu trên giao diện Web.",
    )

    add_h2(doc, "1.2. Ba thách thức kỹ thuật cốt lõi của bài toán")
    add_body(
        doc,
        "Khi mở rộng quy mô nhận diện lên hàng nghìn loài sinh vật chụp ngoài tự nhiên, bài toán đặt ra ba khó khăn kỹ thuật rõ rệt cần giải quyết đồng thời:",
    )
    add_bullet(
        doc,
        "Các loài thuộc cùng một Chi (Genus) hoặc cùng một Họ (Family) thường chia sẻ cấu trúc cành, kiểu xếp lá và màu cánh hoa tương đồng, trong khi một loài lại biến thiên mạnh tùy theo bộ phận được chụp (hoa, lá non, quả chín, vỏ thân) và điều kiện ánh sáng thực địa.",
        bold_prefix="Thách thức về phân loại chi tiết (fine-grained classification): ",
    )
    add_bullet(
        doc,
        "Số lượng ảnh thu thập ngoài tự nhiên giữa các loài không đồng đều. Các loài cây quen thuộc có trên 100 ảnh, trong khi hàng trăm loài mọc rải rác hoặc hiếm gặp chỉ có vài ảnh đến dưới 30 ảnh. Khi huấn luyện bằng hàm mất mát thông thường, ranh giới quyết định dễ bị chèn ép về phía các lớp nhiều mẫu.",
        bold_prefix="Thách thức về mất cân bằng dữ liệu đuôi dài (long-tailed distribution): ",
    )
    add_bullet(
        doc,
        "Người dùng cuối trên môi trường Web có thể tải lên ảnh bị rung mờ, thiếu sáng, hoặc ảnh chụp màn hình máy tính, vật dụng trong nhà, thú cưng. Do hàm Softmax luôn quy tổng xác suất về 1 trên tập lớp cố định, hệ thống cần có chốt kiểm tra chất lượng và lọc ảnh ngoài miền trước khi trả kết quả.",
        bold_prefix="Thách thức về nhận diện tập mở (open-set / OOD): ",
    )

    add_h2(doc, "1.3. Mục tiêu, phạm vi nghiên cứu và bố cục báo cáo")
    add_body(
        doc,
        "Mục tiêu trọng tâm của đồ án gồm bốn nội dung: (1) Lựa chọn và khai thác một mô hình nền sinh học duy nhất phù hợp với đặc thù phân loại thực vật - nấm quy mô lớn, tránh ghép nối nhiều mô hình phụ gây nặng nề khi triển khai; (2) Thiết kế và huấn luyện đầu phân loại có khả năng giữ được độ chính xác tốt trên cả nhóm loài nhiều mẫu lẫn nhóm loài ít mẫu, đồng thời đối chiếu định lượng với các thuật toán học máy cơ sở; (3) Xây dựng bộ lọc từ chối ảnh kém chất lượng hoặc ngoài miền thực vật; và (4) Tích hợp toàn bộ quy trình vào ứng dụng Web tra cứu thực vật học kèm cảnh báo an toàn y sinh rõ ràng.",
    )
    add_body(
        doc,
        "Nội dung tiếp theo của báo cáo được tổ chức thành 5 chương: Chương 2 trình bày cơ sở lý thuyết của mô hình nền sinh học và các thuật toán phân loại; Chương 3 mô tả chi tiết bộ dữ liệu và kiến trúc đề xuất bám sát mã nguồn; Chương 4 phân tích kết quả thực nghiệm; Chương 5 trình bày kiến trúc ứng dụng Web cùng mô-đun gợi ý dược thiện an toàn; và Chương 6 tổng kết các kết quả, hạn chế thực tế và hướng cải tiến.",
    )

    # ==========================================================================
    # CHƯƠNG 2: CƠ SỞ LÝ THUYẾT
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 2. CƠ SỞ LÝ THUYẾT", page_break=True)

    add_h2(doc, "2.1. Mô hình nền thị giác - ngôn ngữ sinh học BioCLIP 2")
    add_body(
        doc,
        "Các mạng tích chập hoặc Vision Transformer huấn luyện trên tập ImageNet thông thường chủ yếu học đặc trưng phân biệt các nhóm vật thể đời sống (xe cộ, đồ gia dụng, động vật cỡ lớn), do đó thường bỏ sót những chi tiết hình thái nhỏ dùng để định danh thực vật ở cấp Loài như gân phụ của lá, đài hoa hay cấu trúc phiến nấm.",
    )
    add_body(
        doc,
        "Để khắc phục hạn chế về miền dữ liệu, Stevens và cộng sự (2024) đã đề xuất BioCLIP [3], và Gu cùng cộng sự (2025) tiếp tục mở rộng lên phiên bản BioCLIP 2 [4] sử dụng kiến trúc Vision Transformer cỡ lớn (ViT-L/14) huấn luyện tương phản trên tập dữ liệu TreeOfLife-200M gồm khoảng 214 triệu ảnh sinh vật gắn liền với chuỗi phân loại sinh học chuẩn GBIF (từ Giới, Ngành, Lớp, Bộ, Họ, Chi đến tên khoa học của Loài). Nhờ học đồng thời mối liên hệ giữa hình ảnh mẫu vật và cấu trúc phân cấp tên khoa học bằng cả bộ mã hóa ảnh (Image Encoder) lẫn bộ mã hóa văn bản (Text Encoder), không gian đặc trưng 768 chiều của BioCLIP 2 có hai tính chất thuận lợi cho đề tài:",
    )
    add_bullet(
        doc,
        "Các loài thuộc cùng Chi và cùng Họ tự động nằm gần nhau trên mặt cầu đơn vị 768 chiều, đồng thời vẫn duy trì khoảng cách góc đủ rõ để tách biệt các loài gần gũi.",
        bold_prefix="Tính phân tách hình thái theo phân cấp sinh học: ",
    )
    add_bullet(
        doc,
        "Bộ mã hóa văn bản nằm trong cùng không gian tích vô hướng với bộ mã hóa ảnh, cho phép vừa khởi tạo trọng số phân loại từ tên khoa học GBIF (hỗ trợ trực tiếp các loài ít ảnh), vừa kiểm tra ngữ nghĩa xem ảnh đầu vào có phải thực vật/nấm hay không mà không cần nạp thêm mạng phụ trợ.",
        bold_prefix="Tính đồng nhất đa phương thức ảnh - văn bản: ",
    )

    add_h2(doc, "2.2. Các phương pháp phân loại trên mặt cầu đơn vị Cosine")
    add_body(
        doc,
        "Khi mọi vector đặc trưng ảnh được chuẩn hóa độ dài bằng 1 theo chuẩn L2, tích vô hướng giữa hai vector chính là độ tương đồng góc Cosine. Trên không gian này, bốn cách tiếp cận từ đơn giản đến có tham số tinh chỉnh được xem xét trong đồ án:",
    )
    add_bullet(
        doc,
        "Không sử dụng bất kỳ ảnh huấn luyện nào; mỗi lớp được đại diện trực tiếp bởi vector văn bản trích xuất từ tên khoa học của loài đó qua Text Encoder. Ảnh kiểm thử được gán về loài có độ tương đồng Cosine lớn nhất với vector văn bản.",
        bold_prefix="Phân loại Zero-Shot bằng văn bản (Zero-Shot Text Matching): ",
    )
    add_bullet(
        doc,
        "Mỗi loài được đại diện bởi một tâm cụm duy nhất là trung bình cộng chuẩn hóa L2 của các vector ảnh huấn luyện thuộc loài đó. Phương pháp này có tốc độ suy luận nhanh nhưng nhạy cảm khi một loài có nhiều góc chụp khác biệt (hoa, lá, thân khô).",
        bold_prefix="Phân loại theo tâm cụm gần nhất (Cosine Nearest Centroid): ",
    )
    add_bullet(
        doc,
        "Giữ lại toàn bộ tập mẫu huấn luyện để tìm k mẫu gần nhất với ảnh truy vấn theo độ đo Cosine, sau đó bỏ phiếu có trọng số hàm mũ theo độ tương đồng. Phương pháp phi tham số này thích nghi tốt với các loài đa hình thái nhưng đòi hỏi lưu trữ toàn bộ ma trận đặc trưng huấn luyện.",
        bold_prefix="Thuật toán láng giềng gần nhất có trọng số (Weighted Cosine k-NN): ",
    )
    add_bullet(
        doc,
        "Áp dụng một nhánh biến đổi phi tuyến có kết nối tắt (residual connection) để điều chỉnh nhẹ vector đặc trưng theo tập dữ liệu mục tiêu, sau đó nhân tích vô hướng với ma trận trọng số lớp chuẩn hóa L2 kèm hệ số tỉ lệ nhiệt độ s [6].",
        bold_prefix="Đầu phân loại mạng nơ-ron chuẩn hóa Cosine có nhánh dư: ",
    )

    add_h2(doc, "2.3. Kỹ thuật xử lý mất cân bằng mẫu và chống quá khớp")
    add_body(
        doc,
        "Đối với tập dữ liệu có hàng nghìn lớp và phân phối mẫu lệch, việc huấn luyện mạng phân loại dễ gặp hai rủi ro: học thiên lệch về lớp nhiều ảnh và quá khớp (overfitting) trên các lớp ít ảnh. Đồ án kết hợp bốn kỹ thuật có cơ sở lý thuyết rõ ràng:",
    )
    add_bullet(
        doc,
        "Theo nghiên cứu của Menon và cộng sự (2021) [5], việc cộng thêm lượng bù tỉ lệ với logarit tần suất xuất hiện của từng lớp vào điểm logit trong quá trình tính hàm mất mát huấn luyện buộc mô hình phải tạo biên phân cách rộng hơn cho các lớp hiếm, giúp cân bằng độ chính xác giữa nhóm nhiều ảnh và ít ảnh.",
        bold_prefix="Hiệu chỉnh Logit theo phân phối tiên nghiệm (Logit Adjustment): ",
    )
    add_bullet(
        doc,
        "Nội suy tuyến tính ngẫu nhiên giữa hai vector đặc trưng trong cùng lô huấn luyện theo phân phối Beta rồi chuẩn hóa lại lên mặt cầu đơn vị [7], kết hợp làm mượt nhãn (Label Smoothing) [8] nhằm hạn chế mô hình đẩy trọng số lên quá lớn ở các mẫu nhiễu.",
        bold_prefix="Trộn đặc trưng (Feature Mixup) và Làm mượt nhãn: ",
    )
    add_bullet(
        doc,
        "Duy trì một bản sao trọng số được cập nhật mượt sau mỗi bước tối ưu theo công thức trung bình trượt hàm mũ (Polyak và Juditsky, 1992) [9], giúp giảm dao động của bộ tối ưu AdamW [10] ở giai đoạn cuối huấn luyện.",
        bold_prefix="Trung bình trượt hàm mũ trọng số (EMA): ",
    )

    add_h2(doc, "2.4. Kiểm tra chất lượng quang học và phát hiện ảnh ngoài miền")
    add_body(
        doc,
        "Độ sắc nét của ảnh số có thể được ước lượng nhanh thông qua phương sai của toán tử đạo hàm bậc hai Laplace trên ảnh mức xám: ảnh lấy nét rõ chứa nhiều biên cạnh sắc nên có phương sai lớn, ngược lại ảnh mất nét hoặc che khuất ống kính có phương sai rất thấp. Đối với các ảnh đủ độ nét nhưng chụp vật thể ngoài phạm vi nghiên cứu, phương pháp kết hợp kiểm tra ngữ nghĩa đa phương thức với ngưỡng khoảng cách Cosine cực đại tới các tâm cụm lớp [11] giúp phát hiện và từ chối dự đoán trước khi hiển thị hồ sơ loài.",
    )

    # ==========================================================================
    # CHƯƠNG 3: PHÂN TÍCH DỮ LIỆU VÀ PHƯƠNG PHÁP ĐỀ XUẤT
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 3. PHÂN TÍCH BỘ DỮ LIỆU VÀ PHƯƠNG PHÁP ĐỀ XUẤT", page_break=True)

    add_h2(doc, "3.1. Khảo sát và phân chia bộ dữ liệu VietMediSpecies2026")
    add_body(
        doc,
        f"Thực nghiệm được tiến hành trên toàn bộ bộ dữ liệu VietMediSpecies2026 [1]. Trong tệp danh mục gốc gồm {fmt_int(cat_sum['totalCsvRecords'])} bản ghi phân loại theo chuẩn GBIF [2], quy trình quét dữ liệu tự động (scripts/01_build_catalog.py) loại bỏ các tệp ẩn hệ thống và đối chiếu thực tế trên ổ đĩa, thu được {fmt_int(cat_sum['totalActiveSpecies'])} thư mục loài có ảnh thực tế với tổng cộng {fmt_int(cat_sum['totalRawImages'])} ảnh hợp lệ (0 ảnh hỏng bị loại bỏ).",
    )

    add_styled_table(
        doc,
        "Thống kê chi tiết bộ dữ liệu thực nghiệm VietMediSpecies2026 trích xuất từ danh mục hệ thống",
        ["Chỉ tiêu thống kê", "Giá trị thực tế", "Ghi chú trích xuất từ dữ liệu"],
        [
            ["Tổng số bản ghi trong tệp CSV gốc", f"{fmt_int(cat_sum['totalCsvRecords'])} bản ghi", "Đối chiếu mã định danh chuẩn GBIF"],
            ["Số loài có thư mục ảnh thực tế", f"{fmt_int(cat_sum['totalActiveSpecies'])} loài", "Gồm 1.698 Chi (Genus) và 338 Họ (Family)"],
            ["Phân bố theo 4 Giới sinh vật (Kingdom)", f"{fmt_int(kd['Plantae'])} / {kd['Fungi']} / {kd['Chromista']} / {kd['Bacteria']}", "Plantae / Fungi / Chromista / Bacteria"],
            ["Tổng số ảnh hợp lệ đưa vào thực nghiệm", f"{fmt_int(cat_sum['totalRawImages'])} ảnh", "Đọc thành công 100%, 0 ảnh lỗi định dạng"],
            ["Mật độ ảnh mỗi loài (Nhỏ nhất / TB / Lớn nhất)", f"{cat_sum['minImagesPerSpecies']} / {fmt_vn(cat_sum['avgImagesPerSpecies'])} / {cat_sum['maxImagesPerSpecies']} ảnh", "Thể hiện rõ tính chất phân phối đuôi dài"],
            ["Tập huấn luyện (Train - khoảng 80%)", f"{fmt_int(bench['numTrainSamples'])} ảnh", "Chia phân tầng (Stratified) theo từng loài, seed = 42"],
            ["Tập thẩm định (Validation - khoảng 10%)", f"{fmt_int(bench['numValSamples'])} ảnh", "Dùng chọn vòng lặp tốt nhất và hiệu chuẩn ngưỡng OOD"],
            ["Tập kiểm thử độc lập (Test - khoảng 10%)", f"{fmt_int(bench['numTestSamples'])} ảnh", "Chỉ dùng đánh giá cuối cùng, tách biệt hoàn toàn"],
        ],
        col_widths_cm=[5.6, 3.8, 6.6],
        left_cols={0, 2},
    )

    add_body(
        doc,
        f"Hình 1 minh họa 10 Họ thực vật có số lượng loài lớn nhất (dẫn đầu là Họ Đậu Fabaceae với 284 loài, Họ Cúc Asteraceae với 193 loài, Họ Hoa môi Lamiaceae với 117 loài và Họ Lan Orchidaceae với 109 loài) cùng sự phân hóa mật độ mẫu: có {fmt_int(sg['manyShot']['numSpecies'])} loài thuộc nhóm nhiều ảnh (từ 90 ảnh trở lên), {sg['mediumShot']['numSpecies']} loài thuộc nhóm trung bình (30 đến 89 ảnh) và {sg['fewShot']['numSpecies']} loài thuộc nhóm ít ảnh (dưới 30 ảnh/loài, chiếm 25,8% tổng số loài).",
    )
    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig1_phan_bo_du_lieu.png",
        "Mười Họ thực vật có nhiều loài nhất (a) và phân bố 3.570 loài theo ba nhóm mật độ ảnh huấn luyện (b)",
        width_cm=15.5,
    )

    add_h2(doc, "3.2. Quy trình trích xuất đặc trưng ảnh và văn bản bằng BioCLIP 2")
    add_body(
        doc,
        "Tổng thể luồng xử lý 5 bước của hệ thống từ lúc nhận ảnh đầu vào đến khi hiển thị hồ sơ loài và cảnh báo an toàn được trình bày ở Hình 2. Khác với các kiến trúc ghép nhiều mạng trích xuất gây tốn bộ nhớ, toàn bộ khâu biểu diễn hình ảnh, biểu diễn tên khoa học GBIF và kiểm tra ngữ nghĩa miền đều dùng chung một mô hình nền duy nhất là BioCLIP 2 (hf-hub:imageomics/bioclip-2) trong mô-đun models/feature_extractor.py.",
    )
    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig2_so_do_quy_trinh.png",
        "Sơ đồ quy trình xử lý tuần tự 5 bước của hệ thống BioLens Vietnam",
        width_cm=15.8,
    )

    add_body(
        doc,
        "Cụ thể, mỗi bức ảnh đầu vào được xoay đúng chiều dựa trên thẻ EXIF, chuyển sang không gian màu RGB (loại bỏ ảnh có cạnh nhỏ hơn 16 pixel), co giãn cạnh ngắn về kích thước round(224 × 1,05) = 235 pixel bằng phép nội suy Bicubic có khử răng cưa (antialias), cắt lấy vùng trung tâm 224×224 pixel và chuẩn hóa theo trung bình (0,4815; 0,4578; 0,4082) cùng độ lệch chuẩn (0,2686; 0,2613; 0,2758) của CLIP. Khi trích xuất đặc trưng với chế độ tăng cường hai góc nhìn lật ngang (2-View Flip TTA), ảnh gốc I và ảnh lật ngang I_flip lần lượt đi qua bộ mã hóa ảnh ViT-L/14 ở độ chính xác hỗn hợp FP16 và hợp nhất theo công thức:",
    )
    add_formula(
        doc,
        "f_1 = L2Norm(EncodeImage(I)),   f_2 = L2Norm(EncodeImage(I_flip)),   x = L2Norm(f_1 + f_2) ∈ R^768",
        "3.1",
    )
    add_body(
        doc,
        "Song song đó, hàm extract_species_text_embeddings tạo hai mẫu câu tiếng Anh chuẩn cho mỗi loài dựa trên thông tin phân loại GBIF trong danh mục: câu đầy đủ P_full = \"a photo of <Kingdom> <Class> <Order> <Family> <Genus> <CanonicalName>\" và câu ngắn P_short = \"a photo of <CanonicalName>\". Hai câu này được mã hóa qua Text Encoder của BioCLIP 2, chuẩn hóa L2 thành e_1, e_2 và tổ hợp thành vector văn bản đại diện cho từng loài c:",
    )
    add_formula(
        doc,
        "t_c = L2Norm(0,65 · e_1,c + 0,35 · e_2,c) ∈ R^768,   c ∈ {1, ..., 3570}",
        "3.2",
    )

    add_h2(doc, "3.3. Thiết kế đầu phân loại BioCLIP2TaxonomicClassifier và các mốc đối chứng")
    add_body(
        doc,
        "Hình 3 mô tả chi tiết cấu trúc toán học của đầu phân loại chính thức BioCLIP2TaxonomicClassifier được cài đặt trong tệp models/ml_classifiers.py. Mục tiêu của thiết kế này là vừa giữ nguyên cấu trúc hình học tốt sẵn có của BioCLIP 2 ở thời điểm khởi đầu, vừa cho phép mô hình điều chỉnh nhẹ ranh giới phân lớp dựa trên 248.310 ảnh thực địa Việt Nam.",
    )
    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig3_trich_dac_trung_va_4_mo_hinh.png",
        "Kiến trúc chi tiết của đầu phân loại BioCLIP2TaxonomicClassifier khởi tạo kết hợp từ văn bản GBIF và tâm cụm ảnh",
        width_cm=15.6,
    )

    add_body(
        doc,
        "Với vector đặc trưng ảnh đầu vào x ∈ R^768, nhánh biến đổi dư (residual branch) đi qua chuỗi lớp: Dropout(0,08) → Linear(768 → 1536) → BatchNorm1d(1536) → GELU → Dropout(0,22) → Linear(1536 → 768) → BatchNorm1d(768) để sinh ra vector hiệu chỉnh Δ(x). Đặc trưng sau tinh chỉnh z được tính bằng kết nối tắt có hệ số học được α (res_alpha):",
    )
    add_formula(
        doc,
        "z = L2Norm(x + α · Δ(x)) ∈ R^768,   khởi tạo α = 0,0",
        "3.3",
    )
    add_body(
        doc,
        f"Việc khởi tạo α = 0,0 đảm bảo tại bước đầu tiên, z trùng khớp hoàn toàn với đặc trưng gốc x của BioCLIP 2 (sau 50 vòng lặp huấn luyện, hệ số α hội tụ tự nhiên về giá trị {fmt_vn(res_alpha_val, 4)}). Tiếp theo, thay vì khởi tạo ngẫu nhiên ma trận trọng số phân loại W ∈ R^(3570 × 768), hệ thống kết hợp trực tiếp ma trận văn bản T từ công thức (3.2) và ma trận tâm cụm trung bình ảnh huấn luyện C:",
    )
    add_formula(
        doc,
        "W_0 = L2Norm(0,35 · T + 0,65 · C),   Logit suy luận: l(x) = s · z · L2Norm(W)^T   (với s = 26,0)",
        "3.4",
    )
    add_body(
        doc,
        "Cần lưu ý rõ sự khác biệt giữa pha huấn luyện và pha suy luận đối với kỹ thuật hiệu chỉnh Logit Adjustment trong mã nguồn: gọi π_c = N_c / N là tần suất mẫu của loài c trong tập Train. Chỉ trong lúc tính hàm mất mát huấn luyện, thành phần τ · log(π_c + 10^-8) với τ = 0,50 mới được cộng vào logit trước khi đưa vào hàm Cross-Entropy có làm mượt nhãn (ε = 0,06):",
    )
    add_formula(
        doc,
        "l^(train)_c(x) = s · z · L2Norm(w_c)^T + τ · log(π_c + 10^-8),   τ = 0,50",
        "3.5",
    )
    add_body(
        doc,
        "Ở pha suy luận trên tập Validation, tập Test và trên ứng dụng Web, mô hình không cộng lại đại lượng τ · log(π_c) mà dùng trực tiếp l(x) = s · z · L2Norm(W)^T (riêng khi hiển thị phần trăm độ tự tin trên giao diện Web, điểm logit được chia cho hệ số nhiệt độ T_web = 1,4 trước hàm Softmax để phân phối xác suất dịu hơn, không làm đổi thứ tự xếp hạng các loài).",
    )

    add_styled_table(
        doc,
        "Cấu hình kiến trúc và siêu tham số thực tế của BioCLIP2TaxonomicClassifier và 3 phương pháp đối chứng",
        ["Thành phần / Phương pháp", "Thông số cấu hình trong mã nguồn", "Vai trò kỹ thuật"],
        [
            ["1. Zero-Shot Text", "Logits = 26,0 · x · T^T (0 ảnh huấn luyện)", "Đo chất lượng gốc của không gian ảnh - chữ BioCLIP 2"],
            ["2. Cosine Nearest Centroid", "Logits = 26,0 · x · C^T (tâm trung bình chuẩn hóa L2)", "Mốc cơ sở tham số tối thiểu dựa trên tâm cụm ảnh"],
            ["3. Weighted Cosine k-NN", "k = 21, trọng số exp(24,0 · (s_j - s_1)) · w_c, w_c ∝ N_c^(-0,15)", "Mốc phi tham số dựa trên láng giềng cục bộ"],
            ["Nhánh dư của Classifier", "768 → 1536 → 768; Dropout 0,08 và 0,22; α_0 = 0,0 (học ra 0,0392)", "Tinh chỉnh nhẹ đặc trưng thực địa, chống quá khớp"],
            ["Khởi tạo trọng số lớp W_0", "L2Norm(0,35 · T + 0,65 · C); hệ số tỉ lệ Cosine s = 26,0", "Bổ sung thông tin phân loại học GBIF cho loài ít ảnh"],
            ["Tối ưu & Lịch tốc độ học", "AdamW (lr = 1,8×10^-3, weight_decay = 2,5×10^-4), CosineLR 50 epochs", "Hội tụ ổn định với kích thước lô batch_size = 1.024"],
            ["Tăng cường & Điều chuẩn", "Feature Mixup (xác suất 0,25; Beta(0,2; 0,2)), Label Smoothing 0,06", "Làm trơn biên quyết định giữa các loài gần gũi"],
            ["Logit Adjustment & EMA", "τ = 0,50 (chỉ cộng khi huấn luyện); EMA decay = 0,995 (từ epoch 10)", "Cân bằng lớp đuôi dài và ổn định trọng số kiểm thử"],
        ],
        col_widths_cm=[4.3, 6.5, 5.2],
        left_cols={0, 1, 2},
    )

    add_h2(doc, "3.4. Thiết kế bộ lọc từ chối ảnh ngoài miền hai tầng (TwoStageOODFilter)")
    add_body(
        doc,
        "Trong tệp models/ood_filter.py, trước khi chấp nhận kết quả định danh, mỗi ảnh tải lên phải vượt qua bước tiền kiểm chất lượng và hai tầng lọc liên tiếp:",
    )
    add_bullet(
        doc,
        "Ảnh được chuyển sang mức xám và đưa về kích thước 384×384 pixel để tính ba đại lượng: độ sáng trung bình μ_gray, độ lệch chuẩn tương phản σ_gray và phương sai toán tử Laplace Var(∇²I). Ảnh bị từ chối ngay nếu quá tối (μ_gray < 15,0), bị lóa trắng mất chi tiết (μ_gray > 250,0 và σ_gray < 8,0), đồng màu/che ống kính (σ_gray < 7,5), hoặc bị mờ nhòe (Var(∇²I) < 18,0).",
        bold_prefix="Bước tiền kiểm chất lượng ảnh (STAGE_0_IMAGE_QUALITY): ",
    )
    add_bullet(
        doc,
        "Hệ thống kết hợp hai tiêu chí ở Tầng 1: (i) So khớp ngữ nghĩa Zero-Shot bằng Text Encoder của BioCLIP 2 trên 11 câu mô tả thuộc 7 nhóm khái niệm (4 câu thực vật/nấm, 1 câu côn trùng thụ phấn và 6 câu ngoài miền), từ chối nếu xác suất ngoài miền > 0,55 và xác suất thực vật < 0,45; và (ii) Đo năng lượng chiếu vector đặc trưng lên không gian con PCA 64 chiều của 3.570 tâm cụm loài (subspaceEnergy), từ chối ngay khi subspaceEnergy < 0,62 nhằm chặn ảnh người, ảnh chụp màn hình và đồ vật đời thường.",
        bold_prefix="Tầng 1 - Cổng ngữ nghĩa Zero-Shot & Năng lượng không gian con PCA (STAGE_1_DOMAIN_GATE): ",
    )
    add_bullet(
        doc,
        f"Hệ thống kiểm tra đồng thời hai điều kiện: (i) Độ tương đồng Cosine lớn nhất giữa vector ảnh x và 3.570 tâm cụm loài phải đạt tối thiểu ngưỡng vận hành tính theo chặn dưới 3,5 độ lệch chuẩn của tập ảnh thực vật Validation (0,8946 - 3,5 × 0,0424 = 0,7462, cao hơn mức hiệu chuẩn tổng hợp {fmt_vn(ood['calibratedCosineThreshold'], 4)}); và (ii) Điểm logit cực đại từ BioCLIP2TaxonomicClassifier phải đạt tối thiểu 6,5 (MaxLogit ≥ 6,5) để loại bỏ các dự đoán có phân phối xác suất phẳng, thiếu độ tin cậy.",
        bold_prefix="Tầng 2 - Ngưỡng Cosine thực vật & MaxLogit (STAGE_2_OPENSET_THRESHOLD): ",
    )

    # ==========================================================================
    # CHƯƠNG 4: THỰC NGHIỆM, ĐÁNH GIÁ VÀ PHÂN TÍCH KẾT QUẢ
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 4. THỰC NGHIỆM, ĐÁNH GIÁ VÀ PHÂN TÍCH KẾT QUẢ", page_break=True)

    add_h2(doc, "4.1. Môi trường thực nghiệm và độ đo đánh giá")
    add_body(
        doc,
        f"Quá trình trích xuất đặc trưng và huấn luyện được thực hiện trên máy chủ GPU hỗ trợ CUDA ở chế độ bán chính xác FP16. Theo nhật ký thực nghiệm (extraction_meta.json), việc trích xuất 310.647 ảnh với 2 góc nhìn lật ngang qua BioCLIP 2 (ViT-L/14 @ 224×224) hoàn tất trong {fmt_vn(ext_meta['extractionTimeSeconds'])} giây (~71,25 phút), đạt thông lượng trung bình {fmt_vn(ext_meta['throughputImagesPerSec'])} ảnh/giây. Bước huấn luyện đầu phân loại BioCLIP2TaxonomicClassifier trong 50 vòng lặp trên 248.310 mẫu mất {fmt_vn(clf['trainTimeSec'])} giây (~5,28 phút).",
    )
    add_body(
        doc,
        "Để đánh giá khách quan trên bài toán mất cân bằng mẫu, báo cáo sử dụng năm chỉ số chuẩn trên tập Test độc lập (31.201 ảnh): Độ chính xác Top-1, Top-3, Top-5 (tỉ lệ mẫu có nhãn đúng nằm trong 1, 3, 5 dự đoán cao nhất), điểm Macro-F1 (trung bình cộng không trọng số của F1 từng loài, phản ánh nhạy cảm kết quả trên các loài hiếm) và điểm Weighted-F1 (trung bình F1 có trọng số theo số lượng mẫu của mỗi loài), cùng thời gian suy luận của đầu phân loại tính bằng mili-giây trên mỗi ảnh (ms/ảnh).",
    )

    add_h2(doc, "4.2. Phân tích quá trình hội tụ huấn luyện")
    add_body(
        doc,
        f"Hình 4 biểu diễn đường cong giảm hàm mất mát huấn luyện và diễn biến độ chính xác trên tập Validation (31.136 ảnh) qua 50 vòng lặp. Ngay tại vòng lặp thứ nhất, nhờ khởi tạo trọng số kết hợp văn bản GBIF và tâm cụm ảnh, mô hình đã đạt Val Top-1 là {fmt_vn(hist['valTop1'][0])}% và Val Top-5 là {fmt_vn(hist['valTop5'][0])}%. Hàm mất mát giảm đều đặn từ {fmt_vn(hist['trainLoss'][0], 4)} (Epoch 1) xuống {fmt_vn(hist['trainLoss'][9], 4)} (Epoch 10, khi bắt đầu kích hoạt đánh giá bằng trọng số EMA) và đạt {fmt_vn(hist['trainLoss'][-1], 4)} ở Epoch 50.",
    )
    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig4_hoi_tu_huan_luyen.png",
        "Diễn biến hàm mất mát huấn luyện (a) và độ chính xác Top-1, Top-5 trên tập Validation qua 50 vòng lặp (b)",
        width_cm=15.5,
    )
    add_body(
        doc,
        f"Theo tiêu chí chọn mô hình kết hợp (Val Top-1 + 0,25 × Val Top-5), điểm cực đại đạt được tại Epoch {hist['bestEpoch']} với Val Top-1 = {fmt_vn(hist['bestValTop1'])}% (Val Top-5 = {fmt_vn(hist['valTop5'][39])}%). Khi đem bộ trọng số tại Epoch {hist['bestEpoch']} kiểm tra một lần duy nhất trên tập Test độc lập, độ chính xác đạt {fmt_vn(clf['top1Accuracy'])}% (chênh lệch giữa Validation và Test chỉ là 0,21 điểm phần trăm), cho thấy các kỹ thuật Dropout hai tầng, Feature Mixup và EMA đã kiểm soát tốt hiện tượng quá khớp.",
    )

    add_h2(doc, "4.3. Đối sánh các phương pháp phân loại trên toàn bộ 3.570 loài")
    add_body(
        doc,
        "Bảng 3 và Hình 5 tổng hợp kết quả định lượng của 4 phương pháp trên cùng tập đặc trưng BioCLIP 2 (768 chiều) đối với toàn bộ 31.201 ảnh kiểm thử thuộc 3.570 loài.",
    )
    add_styled_table(
        doc,
        "Kết quả đánh giá 4 phương pháp phân loại trên toàn bộ 3.570 loài (tập Test: 31.201 ảnh)",
        ["Phương pháp phân loại", "Top-1 (%)", "Top-3 (%)", "Top-5 (%)", "Macro-F1 (%)", "Weighted-F1 (%)", "Train (s)", "Độ trễ (ms/ảnh)"],
        [
            [
                "1. BioCLIP 2 Zero-Shot (Text Prompt)",
                fmt_vn(zs["top1Accuracy"]),
                fmt_vn(zs["top3Accuracy"]),
                fmt_vn(zs["top5Accuracy"]),
                fmt_vn(zs["macroF1"]),
                fmt_vn(zs["weightedF1"]),
                fmt_vn(zs["trainTimeSec"]),
                fmt_vn(zs["latencyMsPerImage"], 3),
            ],
            [
                "2. Cosine Nearest Centroid",
                fmt_vn(cen["top1Accuracy"]),
                fmt_vn(cen["top3Accuracy"]),
                fmt_vn(cen["top5Accuracy"]),
                fmt_vn(cen["macroF1"]),
                fmt_vn(cen["weightedF1"]),
                fmt_vn(cen["trainTimeSec"], 3),
                fmt_vn(cen["latencyMsPerImage"], 3),
            ],
            [
                "3. Weighted Cosine k-NN (k = 21)",
                fmt_vn(knn["top1Accuracy"]),
                fmt_vn(knn["top3Accuracy"]),
                fmt_vn(knn["top5Accuracy"]),
                fmt_vn(knn["macroF1"]),
                fmt_vn(knn["weightedF1"]),
                fmt_vn(knn["trainTimeSec"], 3),
                fmt_vn(knn["latencyMsPerImage"], 3),
            ],
            [
                "4. BioCLIP 2 Taxonomic Classifier",
                fmt_vn(clf["top1Accuracy"]),
                fmt_vn(clf["top3Accuracy"]),
                fmt_vn(clf["top5Accuracy"]),
                fmt_vn(clf["macroF1"]),
                fmt_vn(clf["weightedF1"]),
                fmt_vn(clf["trainTimeSec"]),
                fmt_vn(clf["latencyMsPerImage"], 3),
            ],
        ],
        col_widths_cm=[4.8, 1.5, 1.5, 1.5, 1.8, 1.9, 1.5, 1.5],
        bold_last_row=True,
        left_cols={0},
    )

    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig5_so_sanh_5_mo_hinh.png",
        "Biểu đồ so sánh Top-1 Accuracy, Top-5 Accuracy và Weighted-F1 của 4 phương pháp trên 3.570 loài",
        width_cm=14.8,
    )

    add_body(
        doc,
        "Từ số liệu thực nghiệm ở Bảng 3, có thể rút ra ba nhận xét quan trọng:",
    )
    add_bullet(
        doc,
        f"Ngay cả khi chưa dùng một bức ảnh huấn luyện nào của VietMediSpecies2026, phương pháp Zero-Shot chỉ dựa trên tên khoa học GBIF đã đạt {fmt_vn(zs['top1Accuracy'])}% Top-1 và {fmt_vn(zs['top5Accuracy'])}% Top-5 trên 3.570 loài (trong khi đoán ngẫu nhiên chỉ đạt 1/3570 ≈ 0,028%). Kết quả này xác nhận BioCLIP 2 đã nắm bắt rất sát đặc trưng hình thái sinh vật.",
        bold_prefix="Hiệu quả thực tế của không gian đa phương thức BioCLIP 2: ",
    )
    add_bullet(
        doc,
        f"Khi thay vector văn bản bằng một tâm cụm ảnh trung bình (Cosine Nearest Centroid), Macro-F1 tăng đáng kể từ {fmt_vn(zs['macroF1'])}% lên {fmt_vn(cen['macroF1'])}% (+6,50 điểm %), nhưng Top-1 chỉ nhích nhẹ lên {fmt_vn(cen['top1Accuracy'])}% vì một tâm trung bình đơn lẻ chưa đại diện hết các góc chụp khác nhau của cùng một loài. Thuật toán Weighted k-NN (k = 21) giải quyết vấn đề đa góc chụp bằng cách đối chiếu trực tiếp láng giềng gần nhất, nâng Top-1 lên {fmt_vn(knn['top1Accuracy'])}%.",
        bold_prefix="Giới hạn của tâm cụm đơn và lợi ích của láng giềng cục bộ: ",
    )
    add_bullet(
        doc,
        f"Đầu phân loại tinh chỉnh BioCLIP2TaxonomicClassifier đạt kết quả cao nhất ở tất cả các thước đo: Top-1 đạt {fmt_vn(clf['top1Accuracy'])}% (+2,85 điểm % so với k-NN và +10,98 điểm % so với Centroid), Macro-F1 đạt {fmt_vn(clf['macroF1'])}% (+5,02 điểm % so với k-NN). Đồng thời, thời gian suy luận đầu phân loại chỉ mất {fmt_vn(clf['latencyMsPerImage'], 3)} ms/ảnh (nhanh gấp gần 8 lần so với k-NN {fmt_vn(knn['latencyMsPerImage'], 3)} ms/ảnh) và tệp trọng số chỉ nặng 19,51 MB, hoàn toàn loại bỏ nhu cầu lưu giữ gần 250.000 mẫu huấn luyện trên máy chủ Web.",
        bold_prefix="Lý do triển khai duy nhất BioCLIP2TaxonomicClassifier trên Web: ",
    )

    add_h2(doc, "4.4. Đánh giá đa quy mô tập loài và phân tích nhóm mật độ mẫu")
    add_body(
        doc,
        "Để quan sát sự thay đổi độ chính xác khi quy mô danh mục tăng dần từ các tập loài tiêu biểu lên toàn bộ 3.570 loài, hàm select_discriminative_benchmark_subsets xếp hạng các loài hoàn toàn dựa trên tập Validation theo công thức điểm tổng hợp: 0,65 × Độ chính xác Val của loài + 0,25 × min(1; Tổng số ảnh/100) + 0,10 × Có tên tiếng Việt bản địa, từ đó trích ra ba tập con Top-50, Top-100 và Top-500 loài để kiểm tra trên tập Test.",
    )

    add_styled_table(
        doc,
        "Độ chính xác của BioCLIP2TaxonomicClassifier theo 4 quy mô số lượng loài trên tập Test",
        ["Quy mô đánh giá", "Số mẫu Test", "Top-1 (%)", "Top-3 (%)", "Top-5 (%)", "Macro-F1 (%)", "Weighted-F1 (%)"],
        [
            [
                "Tập con Top-50 loài",
                fmt_int(ms["top50"]["bioclip2_classifier"]["numEvaluatedSamples"]),
                fmt_vn(ms["top50"]["bioclip2_classifier"]["top1Accuracy"]),
                fmt_vn(ms["top50"]["bioclip2_classifier"]["top3Accuracy"]),
                fmt_vn(ms["top50"]["bioclip2_classifier"]["top5Accuracy"]),
                fmt_vn(ms["top50"]["bioclip2_classifier"]["macroF1"]),
                fmt_vn(ms["top50"]["bioclip2_classifier"]["weightedF1"]),
            ],
            [
                "Tập con Top-100 loài",
                fmt_int(ms["top100"]["bioclip2_classifier"]["numEvaluatedSamples"]),
                fmt_vn(ms["top100"]["bioclip2_classifier"]["top1Accuracy"]),
                fmt_vn(ms["top100"]["bioclip2_classifier"]["top3Accuracy"]),
                fmt_vn(ms["top100"]["bioclip2_classifier"]["top5Accuracy"]),
                fmt_vn(ms["top100"]["bioclip2_classifier"]["macroF1"]),
                fmt_vn(ms["top100"]["bioclip2_classifier"]["weightedF1"]),
            ],
            [
                "Tập con Top-500 loài",
                fmt_int(ms["top500"]["bioclip2_classifier"]["numEvaluatedSamples"]),
                fmt_vn(ms["top500"]["bioclip2_classifier"]["top1Accuracy"]),
                fmt_vn(ms["top500"]["bioclip2_classifier"]["top3Accuracy"]),
                fmt_vn(ms["top500"]["bioclip2_classifier"]["top5Accuracy"]),
                fmt_vn(ms["top500"]["bioclip2_classifier"]["macroF1"]),
                fmt_vn(ms["top500"]["bioclip2_classifier"]["weightedF1"]),
            ],
            [
                "Toàn bộ 3.570 loài",
                fmt_int(clf["numEvaluatedSamples"]),
                fmt_vn(clf["top1Accuracy"]),
                fmt_vn(clf["top3Accuracy"]),
                fmt_vn(clf["top5Accuracy"]),
                fmt_vn(clf["macroF1"]),
                fmt_vn(clf["weightedF1"]),
            ],
        ],
        col_widths_cm=[4.2, 2.2, 1.9, 1.9, 1.9, 1.9, 2.0],
        bold_last_row=True,
        left_cols={0},
    )

    add_styled_table(
        doc,
        "Phân rã kết quả dự đoán trên tập Test theo ba nhóm mật độ ảnh huấn luyện",
        ["Nhóm mật độ mẫu", "Số loài", "Số ảnh Test", "Centroid Top-1 (%)", "Classifier Top-1 (%)", "Classifier Top-5 (%)"],
        [
            [
                "Nhiều ảnh (≥ 90 ảnh/loài)",
                fmt_int(sg["manyShot"]["numSpecies"]),
                fmt_int(sg["manyShot"]["numTestSamples"]),
                fmt_vn(sg["manyShot"]["centroidTop1"]),
                fmt_vn(sg["manyShot"]["classifierTop1"]),
                fmt_vn(sg["manyShot"]["classifierTop5"]),
            ],
            [
                "Trung bình (30 – 89 ảnh/loài)",
                fmt_int(sg["mediumShot"]["numSpecies"]),
                fmt_int(sg["mediumShot"]["numTestSamples"]),
                fmt_vn(sg["mediumShot"]["centroidTop1"]),
                fmt_vn(sg["mediumShot"]["classifierTop1"]),
                fmt_vn(sg["mediumShot"]["classifierTop5"]),
            ],
            [
                "Ít ảnh (< 30 ảnh/loài)",
                fmt_int(sg["fewShot"]["numSpecies"]),
                fmt_int(sg["fewShot"]["numTestSamples"]),
                fmt_vn(sg["fewShot"]["centroidTop1"]),
                fmt_vn(sg["fewShot"]["classifierTop1"]),
                fmt_vn(sg["fewShot"]["classifierTop5"]),
            ],
        ],
        col_widths_cm=[4.6, 1.9, 2.2, 2.4, 2.5, 2.4],
        left_cols={0},
    )

    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig6_da_quy_mo_va_nhom_mau.png",
        "Độ chính xác theo quy mô số lượng loài (a) và theo ba nhóm mật độ ảnh huấn luyện (b)",
        width_cm=15.5,
    )
    add_body(
        doc,
        f"Bảng 5 và Hình 6(b) cho thấy trên 921 loài ít ảnh (dưới 30 ảnh/loài), việc kết hợp khởi tạo văn bản GBIF với hiệu chỉnh Logit Adjustment đã nâng độ chính xác Top-1 từ {fmt_vn(sg['fewShot']['centroidTop1'])}% (Cosine Centroid) lên {fmt_vn(sg['fewShot']['classifierTop1'])}% và đạt {fmt_vn(sg['fewShot']['classifierTop5'])}% ở Top-5. Tuy nhiên, khoảng cách {fmt_vn(sg['manyShot']['classifierTop1'] - sg['fewShot']['classifierTop1'])} điểm phần trăm giữa nhóm nhiều ảnh ({fmt_vn(sg['manyShot']['classifierTop1'])}%) và nhóm ít ảnh ({fmt_vn(sg['fewShot']['classifierTop1'])}%) vẫn chỉ ra rằng các loài chỉ có vài bức ảnh huấn luyện là nguồn gây sai số chính của toàn hệ thống.",
    )

    add_h2(doc, "4.5. Đánh giá theo bậc phân loại sinh học và phân tích nhầm lẫn")
    add_body(
        doc,
        "Trong thực vật học, khi một mẫu ảnh chụp thiếu bộ phận đặc trưng (ví dụ chỉ chụp lá non chưa có hoa) dẫn đến dự đoán lệch loài, việc xác định xem dự đoán đó có còn nằm đúng trong cùng Chi hoặc cùng Họ thực vật hay không mang ý nghĩa thực tiễn lớn. Bảng 6 và Hình 7 tổng hợp độ chính xác khi ánh xạ dự đoán từ cấp Loài lên các bậc phân loại cao hơn.",
    )

    add_styled_table(
        doc,
        "Độ chính xác của BioCLIP2TaxonomicClassifier theo 4 bậc phân loại sinh học GBIF (31.201 ảnh Test)",
        ["Bậc phân loại sinh học", "Số lượng đơn vị phân loại", "Top-1 Accuracy (%)", "Top-5 Accuracy (%)"],
        [
            ["Cấp Loài (Species)", "3.570 loài", fmt_vn(hier["speciesLevel"]["top1Accuracy"]), fmt_vn(hier["speciesLevel"]["top5Accuracy"])],
            ["Cấp Chi (Genus)", "1.698 chi", fmt_vn(hier["genusLevel"]["top1Accuracy"]), fmt_vn(hier["genusLevel"]["top5Accuracy"])],
            ["Cấp Họ (Family)", "338 họ", fmt_vn(hier["familyLevel"]["top1Accuracy"]), fmt_vn(hier["familyLevel"]["top5Accuracy"])],
            ["Cấp Giới (Kingdom)", "4 giới", fmt_vn(hier["kingdomLevel"]["top1Accuracy"]), fmt_vn(hier["kingdomLevel"]["top5Accuracy"])],
        ],
        col_widths_cm=[4.8, 4.2, 3.5, 3.5],
        left_cols={0},
    )

    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig7_phan_cap_va_confusion.png",
        "Độ chính xác theo 4 bậc phân loại sinh học (a) và ma trận nhầm lẫn trên 12 loài đầu tiên của tập Top-50 (b)",
        width_cm=15.6,
    )
    add_body(
        doc,
        f"Kết quả tăng đều từ {fmt_vn(hier['speciesLevel']['top1Accuracy'])}% ở cấp Loài lên {fmt_vn(hier['genusLevel']['top1Accuracy'])}% ở cấp Chi, {fmt_vn(hier['familyLevel']['top1Accuracy'])}% ở cấp Họ (Top-5 đạt {fmt_vn(hier['familyLevel']['top5Accuracy'])}%) và {fmt_vn(hier['kingdomLevel']['top1Accuracy'])}% ở cấp Giới. Điều này cho thấy gần một nửa số trường hợp nhầm ở cấp Loài thực chất vẫn được xếp đúng vào các loài họ hàng trong cùng Họ sinh học. Quan sát ma trận nhầm lẫn 12 loài tiêu biểu ở Hình 7(b) (tổng cộng 156 ảnh kiểm thử, mỗi loài 13 ảnh), mô hình dự đoán đúng 154/156 mẫu; hai mẫu nhầm duy nhất xảy ra giữa Nấm sao đất sang Nấm xốp tía (1 ảnh) và từ Ráng bông giun sang Tổ điểu (1 ảnh), đều thuộc nhóm nấm lớn hoặc dương xỉ có sinh cảnh rừng ẩm tương tự nhau.",
    )

    add_h2(doc, "4.6. Kiểm định bộ lọc ảnh ngoài miền (OOD) và tốc độ suy luận")
    add_body(
        doc,
        "Ở Tầng 2 của bộ lọc ảnh ngoài miền, quy trình hiệu chuẩn (models/ml_classifiers.py) đối chiếu phân phối độ tương đồng Cosine lớn nhất tới 3.570 tâm cụm giữa 31.136 ảnh thực vật tập Validation và 2.500 vector ngoại lai tổng hợp (gồm 1.250 vector chuẩn hóa lấy mẫu ngẫu nhiên trên mặt cầu 768 chiều và 1.250 vector tạo bằng cách hoán vị ngẫu nhiên thứ tự các chiều của đặc trưng Validation). Ngưỡng quyết định được xác định tự động bằng trung bình cộng giữa phân vị thứ 3 của tập Validation và phân vị thứ 99,5 của tập ngoại lai tổng hợp.",
    )

    add_styled_table(
        doc,
        "Kết quả hiệu chuẩn và kiểm định bộ lọc OOD Tầng 2 trên tập Validation và mẫu tổng hợp",
        ["Thông số kiểm định OOD Tầng 2", "Giá trị thực nghiệm", "Phạm vi và ý nghĩa kỹ thuật"],
        [
            ["Trung bình ± ĐLC Cosine ảnh thực vật (Val)", f"{fmt_vn(ood['inDistMeanCosine'], 4)} ± {fmt_vn(ood['inDistStdCosine'], 4)}", "Đo trên 31.136 ảnh thực địa hợp lệ"],
            ["Trung bình ± ĐLC Cosine mẫu ngoại lai tổng hợp", f"{fmt_vn(ood['oodMeanCosine'], 4)} ± {fmt_vn(ood['oodStdCosine'], 4)}", "Đo trên 2.500 vector cầu ngẫu nhiên & hoán vị chiều"],
            ["Ngưỡng Cosine hiệu chuẩn tự động (τ_cal)", fmt_vn(ood["calibratedCosineThreshold"], 4), "Trung bình phân vị P3 (Val) và P99,5 (OOD tổng hợp)"],
            ["Tỉ lệ chấp nhận ảnh thực vật tại ngưỡng τ_cal", f"{fmt_vn(ood['inDistributionAcceptRate'])}%", "Trên 31.136 ảnh tập Validation"],
            ["Tỉ lệ từ chối mẫu tổng hợp tại ngưỡng τ_cal", f"{fmt_vn(ood['oodRejectionAccuracy'])}%", "Trên 2.500 mẫu ngoại lai tổng hợp"],
            ["Diện tích dưới đường cong ROC trên [0,00; 0,95]", fmt_vn(ood["rocAuc"], 4), "Tính bằng tích phân hình thang trên 80 mốc ngưỡng ≥ 0"],
        ],
        col_widths_cm=[5.6, 3.4, 7.0],
        left_cols={0, 2},
    )

    add_figure(
        doc,
        "docs/diagrams/academic_bw/word_fig8_kiem_dinh_ood_va_do_tre.png",
        "Phân bố độ tương đồng Cosine giữa ảnh thực vật Validation và mẫu OOD tổng hợp (a) cùng tương quan thời gian phân loại - độ chính xác Top-1 (b)",
        width_cm=15.5,
    )
    add_body(
        doc,
        f"Cần giải thích rõ hai điểm kỹ thuật trung thực từ Bảng 7 và Hình 8(a): thứ nhất, mặc dù hai phân phối tách biệt hoàn toàn quanh ngưỡng hiệu chuẩn {fmt_vn(ood['calibratedCosineThreshold'], 4)}, chỉ số ROC-AUC trong tệp báo cáo JSON ghi nhận mức {fmt_vn(ood['rocAuc'], 4)} (thay vì 1,0000) là do lưới 80 mốc ngưỡng quét từ 0,00 đến 0,95; có 1,24% vector ngẫu nhiên có giá trị Cosine cực đại nhỏ hơn 0,00 nên điểm đầu tiên tại ngưỡng 0,00 có FPR = 0,9876. Thứ hai, khi kiểm thử trực tiếp bằng ảnh đời thường trên ứng dụng Web (ảnh chân dung người, ảnh chụp màn hình giao diện, ảnh vật thể hình học và ảnh tối mờ), ngưỡng {fmt_vn(ood['calibratedCosineThreshold'], 4)} vẫn quá thấp so với miền ảnh tự nhiên của BioCLIP 2; do đó ở môi trường vận hành Web, hệ thống áp dụng đồng thời ngưỡng năng lượng PCA 64 chiều (subspaceEnergy ≥ 0,62), ngưỡng Cosine chặn dưới 3,5 độ lệch chuẩn (0,7462) và ngưỡng MaxLogit ≥ 6,5. Kiểm thử thực tế với bộ ngưỡng này từ chối 5/5 mẫu ngoài miền (gồm ảnh người với subspaceEnergy = 0,525–0,542 và MaxLogit = 5,17–5,35) trong khi vẫn chấp nhận 40/40 ảnh thực vật và nấm ngẫu nhiên từ bộ dữ liệu (subspaceEnergy = 0,719–0,901; MaxLogit ≥ 7,39).",
    )

    add_h2(doc, "4.7. Đối chiếu bối cảnh với các nghiên cứu liên quan")
    add_body(
        doc,
        "Để đặt kết quả của BioLens Vietnam trong bức tranh nghiên cứu hiện hành về nhận diện thực vật và cây thuốc bằng học sâu, Bảng 8 tổng hợp năm công trình tiêu biểu tại Việt Nam, khu vực châu Á và quy mô quốc tế. Do mỗi nghiên cứu sử dụng bộ dữ liệu, số lượng loài và điều kiện chụp khác nhau, việc đối chiếu ở đây nhằm so sánh về quy mô bài toán, kiến trúc mô hình và mức độ hoàn thiện khi triển khai thực tế chứ không so sánh hơn kém trực tiếp về phần trăm độ chính xác.",
    )

    add_styled_table(
        doc,
        "Đối chiếu bối cảnh giữa BioLens Vietnam và các nghiên cứu nhận diện thực vật, cây thuốc liên quan",
        ["Nghiên cứu", "Bộ dữ liệu & Quy mô", "Mô hình chính", "Độ chính xác công bố (theo nguồn gốc)", "Lọc OOD & An toàn dược liệu"],
        [
            [
                "Trung Nguyen Quoc & Vinh Truong Hoang (2020) [13]",
                "VNPlant-200 (200 loài / 20.000 ảnh)",
                "Xception (CNN)",
                "88,26% (trên 200 loài)",
                "Không đề cập",
            ],
            [
                "Duy Tran Nguyen Nhut et al. (2024) [14]",
                "VNPlant-200 (200 loài / 20.000 ảnh)",
                "BEiT / ViT / EfficientNet",
                "99,10% với BEiT (trên 200 loài)",
                "Không đề cập",
            ],
            [
                "Musyaffa et al. (2024) [15]",
                "IndoHerb (100 loài / 10.000 ảnh)",
                "ConvNeXt (Transfer Learning)",
                "93,00% tập chuẩn / 66,00% ảnh thực địa",
                "Không đề cập",
            ],
            [
                "Zhang et al. (2025) [16]",
                "TCMP-300 (300 loài / 52.089 ảnh)",
                "Swin-Transformer + HybridMix",
                "89,64% (trên 300 loài)",
                "Không đề cập",
            ],
            [
                "Garcin et al. (2021) [17]",
                "Pl@ntNet-300K (1.081 loài / 306.146 ảnh)",
                "ResNet-50 (phân phối đuôi dài)",
                "Đánh giá chuẩn đuôi dài quy mô lớn",
                "Chưa chuyên biệt dược liệu Việt Nam",
            ],
            [
                "BioLens Vietnam (Đồ án này)",
                "VietMediSpecies2026 (3.570 loài / 310.647 ảnh)",
                "BioCLIP 2 (ViT-L/14) + Taxonomic Classifier",
                f"{fmt_vn(clf['top1Accuracy'])}% (3.570 loài); {fmt_vn(ms['top100']['bioclip2_classifier']['top1Accuracy'])}% (Top-100); {fmt_vn(ms['top50']['bioclip2_classifier']['top1Accuracy'])}% (Top-50)",
                "Có lọc OOD 2 tầng + Web cảnh báo 176 loài độc & 3.236 loài chỉ làm thuốc",
            ],
        ],
        col_widths_cm=[3.2, 3.1, 3.0, 3.4, 3.3],
        bold_last_row=True,
        left_cols={0, 1, 2, 3, 4},
    )

    add_body(
        doc,
        f"Qua Bảng 8, có thể nhận thấy hai điểm đóng góp rõ ràng của đồ án. Thứ nhất, các nghiên cứu chuyên biệt về cây thuốc tại Việt Nam và châu Á như VNPlant-200 [13], [14], IndoHerb [15] và TCMP-300 [16] hiện tập trung ở quy mô từ 100 đến 300 loài; trong khi đó BioLens Vietnam xử lý không gian phân loại lên tới 3.570 loài (gấp 17,8 lần VNPlant-200 và gấp 3,3 lần Pl@ntNet-300K [17] về số loài) nhưng vẫn giữ mức Top-1 {fmt_vn(clf['top1Accuracy'])}% trên toàn bộ danh mục và {fmt_vn(ms['top100']['bioclip2_classifier']['top1Accuracy'])}% trên lát cắt 100 loài. Thứ hai, thay vì dừng ở bài toán phân loại tập đóng trong phòng thí nghiệm, đồ án bổ sung đầy đủ cơ chế lọc ảnh ngoài miền ở thời điểm chạy Web và phân nhóm an toàn dược thiện bao phủ toàn bộ 3.570 loài.",
    )

    # ==========================================================================
    # CHƯƠNG 5: XÂY DỰNG ỨNG DỤNG WEB VÀ MÔ-ĐUN GỢI Ý DƯỢC THIỆN AN TOÀN
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 5. XÂY DỰNG ỨNG DỤNG WEB VÀ MÔ-ĐUN GỢI Ý DƯỢC THIỆN AN TOÀN", page_break=True)

    add_h2(doc, "5.1. Kiến trúc phần mềm máy chủ FastAPI và giao diện người dùng")
    add_body(
        doc,
        "Để phục vụ nhu cầu tra cứu trực quan, toàn bộ mô hình nhận diện và cơ sở dữ liệu tri thức được đóng gói thành ứng dụng Web hoàn chỉnh sử dụng khung làm việc FastAPI ở phía máy chủ (backend/) và HTML5, CSS3, JavaScript thuần có tích hợp luồng chụp ảnh trực tiếp qua WebRTC ở phía trình duyệt (frontend/). Mô-đun BioLensInferenceEngine áp dụng mẫu thiết kế Singleton để chỉ nạp mô hình BioCLIP 2 cùng tệp trọng số phân loại (tổng dung lượng bộ tệp checkpoints chỉ 25,40 MB) một lần duy nhất khi khởi động máy chủ.",
    )

    add_styled_table(
        doc,
        "Tổng hợp các nhóm giao diện lập trình ứng dụng (REST API) thực tế trong hệ thống Backend",
        ["Nhóm chức năng", "Đường dẫn Endpoint thực tế trong mã nguồn", "Phương thức & Chức năng xử lý"],
        [
            ["Nhận diện ảnh & Kiểm thử", "/api/identify, /api/identify-demo", "POST: Kiểm định ảnh 2 tầng, định danh Top-5 loài và gắn cảnh báo dược tính"],
            ["Bách khoa 3.570 loài", "/api/species, /api/species/{species_key}, /api/image/{species_key}/{filename}", "GET: Tìm kiếm theo tên Việt/Latin, lọc theo Họ/Giới, xem hồ sơ 7 mục & ảnh mẫu"],
            ["Số liệu & Báo cáo thực nghiệm", "/api/benchmarks, /api/chart/{chart_name}, /api/download-report", "GET: Cung cấp số liệu đánh giá JSON, biểu đồ PNG và tải tệp báo cáo .docx"],
            ["Gợi ý dược thiện & Hỏi đáp", "/api/nutraceutical/recommend, /search, /metadata, /profile/{species_key}, /ask (GET & POST)", "6 endpoints tra cứu độ an toàn, lọc theo mục tiêu sức khỏe và hỏi đáp quy tắc"],
            ["Phục vụ giao diện tĩnh", "/, /favicon.ico (cùng thư mục tĩnh /static)", "2 GET routes trong backend/app.py trả trang chủ ứng dụng Web"],
        ],
        col_widths_cm=[3.6, 6.2, 6.2],
        left_cols={0, 1, 2},
    )

    add_body(
        doc,
        "Như thống kê ở Bảng 9, máy chủ cung cấp tổng cộng 14 REST API endpoints dưới tiền tố /api (trong backend/routes.py) và 2 route phục vụ trang giao diện chính (trong backend/app.py). Một chi tiết cài đặt cần ghi nhận rõ là trên giao diện nhận diện có thanh chọn bộ phận quan sát (Tự động, Hoa, Lá, Quả/Hạt, Toàn cây/Nấm) gửi tham số organ_hint lên máy chủ; ở phiên bản hiện tại, tham số này được lưu vào phản hồi JSON để ghi nhận ngữ cảnh người dùng chứ chưa làm thay đổi phép biến đổi ảnh hay bộ trọng số phân loại.",
    )

    add_h2(doc, "5.2. Cơ sở dữ liệu phân định an toàn và mô-đun gợi ý dược thiện")
    add_body(
        doc,
        "Sau khi định danh được mã loài GBIF (speciesKey), mô-đun NutraceuticalEngine (backend/nutraceutical_engine.py) đối chiếu trực tiếp với tệp cơ sở dữ liệu quy tắc storage/catalog/nutraceutical_registry.json bao phủ đủ 3.570 loài để quyết định hiển thị cảnh báo độc tính hoặc gợi ý cách chế biến tham khảo. Bảng 10 trình bày số liệu kiểm đếm chính xác của 5 nhóm phân loại an toàn trong hệ thống.",
    )

    add_styled_table(
        doc,
        "Thống kê phân nhóm mức độ an toàn của 3.570 loài trong cơ sở dữ liệu nutraceutical_registry.json",
        ["Mã phân nhóm trong hệ thống", "Số lượng loài", "Tỉ lệ (%)", "Cơ chế xử lý trên giao diện Web"],
        [
            [
                "MEDICINAL_ONLY (Dược liệu chuyên khoa)",
                fmt_int(grade_counts["MEDICINAL_ONLY"]),
                fmt_vn(grade_counts["MEDICINAL_ONLY"] * 100.0 / 3570.0),
                "Không gợi ý món ăn hàng ngày; hiển thị khuyến cáo tham khảo thầy thuốc chuyên môn",
            ],
            [
                "TOXIC_FORBIDDEN (Loài có độc tính)",
                fmt_int(grade_counts["TOXIC_FORBIDDEN"]),
                fmt_vn(grade_counts["TOXIC_FORBIDDEN"] * 100.0 / 3570.0),
                "Hiển thị khung cảnh báo nguy hiểm màu đỏ, nghiêm cấm tự ý ăn uống hoặc sắc nước",
            ],
            [
                "BEVERAGE_INFUSION (Trà & nước hãm)",
                fmt_int(grade_counts["BEVERAGE_INFUSION"]),
                fmt_vn(grade_counts["BEVERAGE_INFUSION"] * 100.0 / 3570.0),
                "Cho phép tra cứu cách pha trà thảo mộc, định lượng và lưu ý thể trạng kiêng kỵ",
            ],
            [
                "SPICE_AROMATIC (Rau gia vị & tinh dầu)",
                fmt_int(grade_counts["SPICE_AROMATIC"]),
                fmt_vn(grade_counts["SPICE_AROMATIC"] * 100.0 / 3570.0),
                "Cho phép tra cứu cách dùng làm gia vị ẩm thực và hỗ trợ tiêu hóa, giải cảm nhẹ",
            ],
            [
                "CULINARY_TONIC (Nguyên liệu món bổ)",
                fmt_int(grade_counts["CULINARY_TONIC"]),
                fmt_vn(grade_counts["CULINARY_TONIC"] * 100.0 / 3570.0),
                "Cho phép tra cứu công thức nấu canh, cháo bồi bổ kèm thời gian và liều lượng",
            ],
            [
                "Tổng cộng toàn bộ danh mục",
                "3.570",
                "100,00",
                f"Có {safe_food_total} loài nhóm thực phẩm/trà ({species_with_recipes} loài đã có {total_recipes} công thức chi tiết)",
            ],
        ],
        col_widths_cm=[4.8, 2.1, 1.8, 7.3],
        bold_last_row=True,
        left_cols={0, 3},
    )

    add_body(
        doc,
        f"Về khía cạnh an toàn y sinh thực tế, mặc dù mô-đun quy tắc chặn toàn bộ {grade_counts['TOXIC_FORBIDDEN']} loài có độc và {fmt_int(grade_counts['MEDICINAL_ONLY'])} loài dược liệu chuyên khoa khi mã loài đã được xác định đúng, bản thân mô hình thị giác phía trước vẫn tồn tại tỉ lệ sai số định danh Top-1 là {fmt_vn(100.0 - clf['top1Accuracy'])}% trên 3.570 loài. Vì vậy, hệ thống không xem kết quả nhận diện qua ảnh là kết luận khẳng định y khoa mà luôn đính kèm danh sách Top-5 loài gần giống nhất để người dùng đối chiếu hình ảnh mẫu thực địa, kèm khuyến cáo không tự ý thu hái và sử dụng cây nấm hoang dã nếu chưa được chuyên gia kiểm chứng.",
    )

    # ==========================================================================
    # CHƯƠNG 6: KẾT LUẬN, HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN
    # ==========================================================================
    add_h1(doc, "CHƯƠNG 6. KẾT LUẬN, HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN", page_break=True)

    add_h2(doc, "6.1. Tổng kết các kết quả đạt được")
    add_body(
        doc,
        "Đồ án đã hoàn thành việc thiết kế, huấn luyện và triển khai thử nghiệm hệ thống BioLens Vietnam cho bài toán nhận diện thực vật và nấm dược liệu Việt Nam trên toàn bộ 310.647 ảnh thuộc 3.570 loài của bộ dữ liệu VietMediSpecies2026. Các kết quả chính có thể tóm lược như sau:",
    )
    add_bullet(
        doc,
        f"Chuyển đổi sang kiến trúc đơn mô hình nền sinh học BioCLIP 2 (ViT-L/14, 768 chiều) kết hợp đầu phân loại có nhánh dư BioCLIP2TaxonomicClassifier khởi tạo từ văn bản phân loại GBIF và tâm cụm ảnh. Mô hình đạt {fmt_vn(clf['top1Accuracy'])}% Top-1, {fmt_vn(clf['top5Accuracy'])}% Top-5 và {fmt_vn(clf['weightedF1'])}% Weighted-F1 trên 31.201 ảnh kiểm thử độc lập, đồng thời đạt {fmt_vn(hier['familyLevel']['top1Accuracy'])}% ở cấp Họ thực vật.",
    )
    add_bullet(
        doc,
        f"Loại bỏ sự phụ thuộc vào các bộ phân loại tổ hợp cồng kềnh khi vận hành thực tế: toàn bộ tệp trọng số triển khai trên máy chủ Web chỉ chiếm 25,40 MB với độ trễ đầu phân loại trung bình {fmt_vn(clf['latencyMsPerImage'], 3)} ms/ảnh.",
    )
    add_bullet(
        doc,
        f"Tích hợp đồng bộ quy trình tiền kiểm chất lượng ảnh, lọc ngữ nghĩa ngoài miền Zero-Shot trên chính Text Encoder của BioCLIP 2 và cơ sở dữ liệu kiểm soát an toàn dược thiện phân nhóm rõ ràng cho toàn bộ 3.570 loài trên giao diện Web.",
    )

    add_h2(doc, "6.2. Các hạn chế thực tế của đề tài")
    add_body(
        doc,
        "Qua quá trình kiểm định định lượng và rà soát mã nguồn, hệ thống hiện vẫn còn bốn hạn chế cần nhìn nhận khách quan:",
    )
    add_bullet(
        doc,
        f"Độ chính xác trên nhóm 921 loài ít ảnh (dưới 30 ảnh/loài) mới đạt {fmt_vn(sg['fewShot']['classifierTop1'])}% Top-1 (thấp hơn 17,92 điểm phần trăm so với mức {fmt_vn(sg['manyShot']['classifierTop1'])}% của nhóm nhiều ảnh), do số lượng mẫu quá ít chưa bao quát hết biến thiên mùa vụ và giai đoạn sinh trưởng của cây.",
        bold_prefix="1. Độ chênh lệch hiệu năng ở nhóm loài hiếm: ",
    )
    add_bullet(
        doc,
        "Chỉ số đánh giá định lượng ở Tầng 2 của bộ lọc OOD hiện được đo trên 2.500 mẫu vector tổng hợp; đề tài chưa xây dựng được một bộ ảnh kiểm thử thực địa riêng gồm các loài cây cảnh hoặc cỏ dại nằm ngoài danh mục 3.570 loài (bài toán Near-OOD thực tế).",
        bold_prefix="2. Phạm vi kiểm thử định lượng của bộ lọc OOD Tầng 2: ",
    )
    add_bullet(
        doc,
        "Tùy chọn gợi ý bộ phận thực vật (organ_hint) trên giao diện người dùng hiện mới đóng vai trò ghi nhận thông tin đầu vào, chưa được tích hợp thành nhánh trọng số chuyên biệt cho riêng ảnh hoa, ảnh lá hay ảnh quả/thân.",
        bold_prefix="3. Chưa khai thác chuyên sâu nhãn bộ phận cây: ",
    )
    add_bullet(
        doc,
        f"Trong {safe_food_total} loài thuộc ba nhóm an toàn ẩm thực và trà thảo mộc, hiện mới có {species_with_recipes} loài được biên soạn đầy đủ công thức chế biến từng bước ({total_recipes} công thức); {safe_food_total - species_with_recipes} loài còn lại mới dừng ở mức phân loại nhóm an toàn và mô tả chung.",
        bold_prefix="4. Độ phủ công thức chi tiết trong mô-đun dược thiện: ",
    )

    add_h2(doc, "6.3. Hướng phát triển tiếp theo")
    add_body(
        doc,
        "Trong giai đoạn tiếp theo, hệ thống có thể được nâng cấp theo ba hướng khả thi: (1) Áp dụng kỹ thuật tinh chỉnh tham số hiệu quả LoRA trên một số tầng chú ý cuối của BioCLIP 2 kết hợp thông tin vùng sinh thái và mùa ra hoa tại Việt Nam để cải thiện độ chính xác cho 921 loài ít mẫu; (2) Thu thập bộ ảnh kiểm thử Near-OOD thực tế gồm các loài cây ngoài danh mục và dược liệu phơi khô để hiệu chuẩn chặt chẽ hơn cả hai tầng lọc; và (3) Phối hợp cùng tài liệu dược điển chính thống để bổ sung công thức và liều lượng chuẩn hóa cho các loài thảo mộc an toàn còn lại.",
    )

    # ==========================================================================
    # TÀI LIỆU THAM KHẢO (100% ĐÚNG TÁC GIẢ, NĂM, NỘI DUNG KỸ THUẬT)
    # ==========================================================================
    add_h1(doc, "TÀI LIỆU THAM KHẢO", page_break=True)
    refs = [
        "[1] Science Data Bank (SciDB), \"VietMediSpecies2026: Vietnamese Medicinal Species Image Dataset,\" Dataset ID d2e66ca3d73540739a39789d9b1cf989, 2026. Truy cập tại: https://www.scidb.cn/en/detail?dataSetId=d2e66ca3d73540739a39789d9b1cf989",
        "[2] GBIF Secretariat, \"GBIF Backbone Taxonomy,\" Checklist Dataset, Global Biodiversity Information Facility, 2024. Truy cập tại: https://www.gbif.org/",
        "[3] S. Stevens, J. Wu, M. J. Thompson, E. G. Campolongo, C. H. Song, D. E. Carlyn et al., \"BioCLIP: A Vision Foundation Model for the Tree of Life,\" in Proc. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2024, pp. 19412-19424.",
        "[4] J. Gu, S. Stevens, E. G. Campolongo, M. J. Thompson, N. Zhang, J. Wu et al., \"BioCLIP 2: Emergent Properties from Scaling Hierarchical Contrastive Learning,\" arXiv preprint arXiv:2505.23883, 2025.",
        "[5] A. K. Menon, S. Jayasumana, A. S. Rawat, H. Jain, A. Veit, and S. Kumar, \"Long-Tail Learning via Logit Adjustment,\" in Proc. International Conference on Learning Representations (ICLR), 2021.",
        "[6] H. Wang, Y. Wang, Z. Zhou, X. Ji, D. Gong, J. Zhou, Z. Li, and W. Liu, \"CosFace: Large Margin Cosine Loss for Deep Face Recognition,\" in Proc. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2018, pp. 5265-5274.",
        "[7] H. Zhang, M. Cisse, Y. N. Dauphin, and D. Lopez-Paz, \"mixup: Beyond Empirical Risk Minimization,\" in Proc. International Conference on Learning Representations (ICLR), 2018.",
        "[8] C. Szegedy, V. Vanhoucke, S. Ioffe, J. Shlens, and Z. Wojna, \"Rethinking the Inception Architecture for Computer Vision,\" in Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016, pp. 2818-2826.",
        "[9] B. T. Polyak and A. B. Juditsky, \"Acceleration of Stochastic Approximation by Averaging,\" SIAM Journal on Control and Optimization, vol. 30, no. 4, pp. 838-855, 1992.",
        "[10] I. Loshchilov and F. Hutter, \"Decoupled Weight Decay Regularization,\" in Proc. International Conference on Learning Representations (ICLR), 2019.",
        "[11] D. Hendrycks and K. Gimpel, \"A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks,\" in Proc. International Conference on Learning Representations (ICLR), 2017.",
        "[12] A. Radford, J. W. Kim, C. Hallacy, A. Ramesh, G. Goh, S. Agarwal et al., \"Learning Transferable Visual Models From Natural Language Supervision,\" in Proc. International Conference on Machine Learning (ICML), 2021, pp. 8748-8763.",
        "[13] T. Nguyen Quoc and V. Truong Hoang, \"VNPlant-200 - A Public and Large-Scale of Vietnamese Medicinal Plant Images Dataset,\" in Lecture Notes in Networks and Systems, Springer, 2020. DOI: 10.1007/978-3-030-49264-9_37.",
        "[14] D. T. Nguyen Nhut, T. Duong Tan, T. Nguyen Quoc et al., \"Medicinal plant recognition based on Vision Transformer and BEiT,\" Procedia Computer Science, Elsevier, 2024. DOI: 10.1016/j.procs.2024.02.165.",
        "[15] M. S. I. Musyaffa, N. Yudistira, M. A. Rahman et al., \"IndoHerb: Indonesia medicinal plants recognition using transfer learning and deep learning,\" Heliyon, Elsevier, 2024. DOI: 10.1016/j.heliyon.2024.e40606.",
        "[16] Y. Zhang, W. Sun, C. Yang et al., \"TCMP-300: A Comprehensive Traditional Chinese Medicinal Plant Dataset for Plant Recognition,\" Scientific Data, Nature Portfolio, 2025. DOI: 10.1038/s41597-025-05522-7.",
        "[17] C. Garcin, A. Joly, P. Bonnet, A. Affouard, J.-C. Lombardo et al., \"Pl@ntNet-300K: a plant image dataset with high label ambiguity and a long-tailed distribution,\" in Proc. NeurIPS Datasets and Benchmarks Track, 2021. DOI: 10.5281/zenodo.5645731.",
    ]
    for r_txt in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.9)
        style_run(p.add_run(r_txt), 12)

    doc.save(str(OUT_DOCX))
    if VLU_LOGO_TMP.exists():
        try:
            VLU_LOGO_TMP.unlink()
        except Exception:
            pass
    print(f"SAVED_WORD_REPORT_OK -> {OUT_DOCX} ({OUT_DOCX.stat().st_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    build_master_report()
