"""CLI: list | ocr | classify."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .classify import Classification, classify_text
from .ocr import path_to_text

SCAN_EXT = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".pdf",
}


def _collect_scans(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in SCAN_EXT else []
    out: list[Path] = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in SCAN_EXT:
            out.append(p)
    return out


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.slozka).resolve()
    for p in _collect_scans(root):
        print(p)
    return 0


def cmd_ocr(args: argparse.Namespace) -> int:
    path = Path(args.soubor).resolve()
    if not path.is_file():
        print(f"Soubor neexistuje: {path}", file=sys.stderr)
        return 1
    text = path_to_text(path, lang=args.lang)
    sys.stdout.write(text)
    if text and not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    root = Path(args.slozka).resolve()
    paths = _collect_scans(root)
    if not paths:
        print("Nenalezeny žádné soubory (JPG/PNG/…/PDF).", file=sys.stderr)
        return 1

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["cesta", "typ", "skore", "napovedy"])

    for p in paths:
        try:
            text = path_to_text(p, lang=args.lang)
        except Exception as e:
            writer.writerow([str(p), "chyba", "", str(e)])
            continue
        c: Classification = classify_text(text)
        hints = ";".join(c.hints[:20])
        writer.writerow([str(p), c.kind.value, f"{c.score:.3f}", hints])

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="abc-scanner", description="Časopis ABC — skenery")
    sub = parser.add_subparsers(dest="prikaz", required=True)

    p_list = sub.add_parser("list", help="Vypsat obrázky ve složce")
    p_list.add_argument("slozka", type=str)
    p_list.set_defaults(func=cmd_list)

    p_ocr = sub.add_parser("ocr", help="OCR jednoho souboru (obrázek nebo PDF)")
    p_ocr.add_argument("soubor", type=str)
    p_ocr.add_argument("--lang", default="ces+eng", help="Tesseract jazyky, např. ces+eng")
    p_ocr.set_defaults(func=cmd_ocr)

    p_cls = sub.add_parser("classify", help="Klasifikovat složku skenů JPG/PNG/…/PDF (CSV)")
    p_cls.add_argument("slozka", type=str)
    p_cls.add_argument("--lang", default="ces+eng")
    p_cls.set_defaults(func=cmd_classify)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
