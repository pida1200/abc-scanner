"""Vizuální heuristiky pro detekci papírových modelů (bez OCR).

Cíl: odlišit stránky typu „vystřihovánka / papírová stavebnice“ od běžného článku.
Používá OpenCV, pokud je dostupné.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover
    cv2 = None
    np = None

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None


@dataclass
class VisionScore:
    score: float
    hints: list[str]
    wheels: bool = False


def _require_cv() -> None:
    if cv2 is None or np is None:
        raise RuntimeError("Pro vizuální detekci nainstaluj opencv-python-headless a numpy.")


def _resize_gray(img, max_side: int = 1400):
    _require_cv()
    h, w = img.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return img
    scale = max_side / m
    nh = max(1, int(h * scale))
    nw = max(1, int(w * scale))
    return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)


def score_image_for_model(path: Path) -> VisionScore:
    """Vrací skóre 0-1: čím vyšší, tím spíš papírový model."""
    _require_cv()
    hints: list[str] = []

    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        return VisionScore(0.0, ["vision:nelze_nacist"])

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = _resize_gray(gray)

    # Textura písma: stránky s článkem mívají spoustu malých komponent (písmena).
    # Vystřihovánky jsou naopak spíš pár velkých tvarů + obrysy.
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    small_cc = 0
    for k in range(1, n):
        area = int(stats[k, cv2.CC_STAT_AREA])
        if 8 <= area <= 120:
            small_cc += 1
    if small_cc:
        hints.append(f"vision:small_cc={small_cc}")

    # Hrany (modely mají typicky hodně tenkých obrysů a spojů)
    edges = cv2.Canny(gray, 80, 200)
    edge_density = float((edges > 0).mean())
    if edge_density > 0.02:
        hints.append(f"vision:edges={edge_density:.3f}")

    # Kontury (mnoho oddělených dílů)
    cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnt_count = 0
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 120:  # malé šumy pryč
            cnt_count += 1
    if cnt_count > 150:
        hints.append(f"vision:contours={cnt_count}")

    # Kroužky s čísly (Hough na downsample) – jen pomocný signál, snadno přestřelí.
    small = _resize_gray(gray, max_side=900)
    blur = cv2.GaussianBlur(small, (5, 5), 0)
    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=30,
        param1=120,
        param2=38,
        minRadius=6,
        maxRadius=40,
    )
    circle_count = 0 if circles is None else int(circles.shape[1])
    # Pokud Hough "najde" stovky až tisíce kruhů, bereme to jako šum a ignorujeme.
    if circle_count > 250:
        circle_count = 0
        hints.append("vision:circles=ignored")
    elif circle_count >= 8:
        hints.append(f"vision:circles={circle_count}")

    # Detekce kol: větší kruhy ve více kusech (typicky 2-12).
    wheels = False
    big = _resize_gray(gray, max_side=1100)
    big_blur = cv2.GaussianBlur(big, (7, 7), 0)
    wheel_circles = cv2.HoughCircles(
        big_blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=90,
        param1=160,
        param2=55,
        minRadius=28,
        maxRadius=160,
    )
    wheel_count = 0 if wheel_circles is None else int(wheel_circles.shape[1])
    if 2 <= wheel_count <= 14:
        wheels = True
        hints.append(f"vision:wheels={wheel_count}")

    # Skórování: kombinace signálů, oříznuté do 0..1
    score = 0.0
    score += min(0.7, edge_density * 8.0)   # ~0.09 -> 0.72 cap
    score += min(0.2, cnt_count / 1500.0)   # 300 -> 0.2 cap
    score += min(0.15, circle_count / 60.0) # 10 -> 0.15 cap
    score = max(0.0, min(1.0, score))

    # Pokud je detekováno hodně "písmenových" komponent, přibrzdi (spíš článek).
    if small_cc >= 900:
        hints.append("vision:many_letters")
        score = min(score, 0.35)

    if wheels and score < 0.55:
        score = min(1.0, score + 0.08)

    return VisionScore(score, hints, wheels=wheels)


def score_pdf_for_model(path: Path, max_pages: int = 8) -> VisionScore:
    """Skóre pro PDF: projde první stránky a vezme max score."""
    _require_cv()
    if fitz is None:
        raise RuntimeError("Pro PDF vizuální detekci nainstaluj pymupdf (PyMuPDF).")

    doc = fitz.open(path)
    best = VisionScore(0.0, [], wheels=False)
    try:
        pages = min(len(doc), max_pages)
        for i in range(pages):
            page = doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), alpha=False)
            arr = np.frombuffer(pix.samples, dtype=np.uint8)
            img = arr.reshape(pix.height, pix.width, 3)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            gray = _resize_gray(gray)
            edges = cv2.Canny(gray, 80, 200)
            edge_density = float((edges > 0).mean())
            # rychlé skóre jen z edge density (PDF může být těžké)
            score = max(0.0, min(1.0, edge_density * 18.0))
            if score > best.score:
                best = VisionScore(
                    score,
                    [f"vision:pdf_page={i+1}", f"vision:edges={edge_density:.3f}"],
                    wheels=False,
                )
    finally:
        doc.close()

    return best

