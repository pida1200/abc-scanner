"""OCR přes Tesseract (ces). PDF: nejdřív textová vrstva, jinak raster + OCR."""

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

MAX_OCR_SIDE = 2000


def _resize_for_ocr(img: Image.Image, max_side: int = MAX_OCR_SIDE) -> Image.Image:
    w, h = img.size
    m = max(w, h)
    if m <= max_side:
        return img
    scale = max_side / m
    nw = max(1, int(w * scale))
    nh = max(1, int(h * scale))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def image_to_text(path: Path, lang: str = "ces+eng") -> str:
    img = Image.open(path)
    img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
    if img.mode == "L":
        img = img.convert("RGB")
    img = _resize_for_ocr(img)
    return pytesseract.image_to_string(img, lang=lang) or ""


def _ocr_pdf_page(page, lang: str) -> str:
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    mode = "RGB" if pix.alpha == 0 else "RGBA"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = _resize_for_ocr(img)
    return pytesseract.image_to_string(img, lang=lang) or ""


def pdf_to_text(path: Path, lang: str = "ces+eng", zoom: float = 2.0) -> str:
    """Kompatibilita: celý PDF přes OCR (pomalé)."""
    if fitz is None:
        raise RuntimeError("Pro PDF je potřeba nainstalovat balíček pymupdf (PyMuPDF).")
    parts: list[str] = []
    doc = fitz.open(path)
    try:
        for i in range(len(doc)):
            parts.append(_ocr_pdf_page(doc[i], lang))
    finally:
        doc.close()
    return "\n".join(parts)


def pdf_iter_pages_text(path: Path, lang: str = "ces+eng", min_layer_chars: int = 40) -> list[tuple[int, str]]:
    """Jedna stránka = jedna položka. Nejdřív get_text(); pokud málo znaků → OCR."""
    if fitz is None:
        raise RuntimeError("Pro PDF je potřeba nainstalovat balíček pymupdf (PyMuPDF).")
    out: list[tuple[int, str]] = []
    doc = fitz.open(path)
    try:
        for i in range(len(doc)):
            page = doc[i]
            layer = (page.get_text() or "").strip()
            if len(layer) >= min_layer_chars:
                text = page.get_text()
            else:
                text = _ocr_pdf_page(page, lang)
            out.append((i + 1, text or ""))
    finally:
        doc.close()
    return out


def path_to_text(path: Path, lang: str = "ces+eng") -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        return pdf_to_text(path, lang=lang)
    return image_to_text(path, lang=lang)
