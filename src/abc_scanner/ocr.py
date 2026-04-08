"""OCR přes Tesseract (ces). PDF se převádí na rastr přes PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None


def image_to_text(path: Path, lang: str = "ces+eng") -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang=lang) or ""


def pdf_to_text(path: Path, lang: str = "ces+eng", zoom: float = 2.0) -> str:
    if fitz is None:
        raise RuntimeError("Pro PDF je potřeba nainstalovat balíček pymupdf (PyMuPDF).")
    doc = fitz.open(path)
    parts: list[str] = []
    mat = fitz.Matrix(zoom, zoom)
    try:
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            mode = "RGB" if pix.alpha == 0 else "RGBA"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            if img.mode != "RGB":
                img = img.convert("RGB")
            parts.append(pytesseract.image_to_string(img, lang=lang) or "")
    finally:
        doc.close()
    return "\n".join(parts)


def path_to_text(path: Path, lang: str = "ces+eng") -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        return pdf_to_text(path, lang=lang)
    return image_to_text(path, lang=lang)
