"""CLI: list | ocr | classify."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

from .classify import Classification, classify_text
from .ocr import image_to_text, path_to_text, pdf_iter_pages_text
from .search import F1_PRESET, find_matches, path_filter

def _line_buffer_stdout_if_possible() -> None:
    """Při přesměrování do souboru ať CSV roste průběžně (ne až na konci)."""
    if sys.stdout.isatty():
        return
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except (OSError, ValueError, AttributeError, io.UnsupportedOperation):
            pass


def _flush_out() -> None:
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        raise SystemExit(0)


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

    _line_buffer_stdout_if_possible()
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["cesta", "typ", "skore", "napovedy"])
    _flush_out()

    for p in paths:
        try:
            text = path_to_text(p, lang=args.lang)
        except Exception as e:
            writer.writerow([str(p), "chyba", "", str(e)])
            _flush_out()
            continue
        c: Classification = classify_text(text)
        hints = ";".join(c.hints[:20])
        writer.writerow([str(p), c.kind.value, f"{c.score:.3f}", hints])
        _flush_out()

    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root = Path(args.slozka).resolve()
    paths = _collect_scans(root)
    filt = None if args.all_files else args.path_contains
    paths = [p for p in paths if path_filter(p, filt)]
    if args.limit and args.limit > 0:
        paths = paths[: args.limit]

    if not paths:
        print("Nenalezeny žádné soubory k prohledání.", file=sys.stderr)
        return 1

    if args.preset == "f1":
        patterns = F1_PRESET
    else:
        patterns = []

    _line_buffer_stdout_if_possible()
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["soubor", "strana", "shody"])
    _flush_out()

    lang = args.lang
    for p in paths:
        try:
            if p.suffix.lower() == ".pdf":
                pages = pdf_iter_pages_text(p, lang=lang)
                for page_no, text in pages:
                    hits = find_matches(text, patterns)
                    if hits:
                        writer.writerow([str(p), page_no, ";".join(hits)])
                        _flush_out()
            else:
                text = image_to_text(p, lang=lang)
                hits = find_matches(text, patterns)
                if hits:
                    writer.writerow([str(p), "", ";".join(hits)])
                    _flush_out()
        except Exception as e:
            writer.writerow([str(p), "", f"CHYBA:{e}"])
            _flush_out()

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

    p_search = sub.add_parser(
        "search",
        help="Najít stránky podle klíčových vzorů (preset f1 = Formule 1 / F1 / týmy…)",
    )
    p_search.add_argument("slozka", type=str, help="Kořenová složka se skeny")
    p_search.add_argument(
        "--preset",
        default="f1",
        choices=["f1"],
        help="Výchozí vzory pro vyhledávání",
    )
    p_search.add_argument(
        "--path-contains",
        default="ABC",
        metavar="TEXT",
        help="Zpracovat jen soubory, jejichž cesta obsahuje TEXT (výchozí: ABC)",
    )
    p_search.add_argument(
        "--all-files",
        action="store_true",
        help="Nefiltrovat podle cesty (všechny JPG/PNG/PDF ve složce — může být velmi pomalé)",
    )
    p_search.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max. počet souborů (0 = bez limitu)",
    )
    p_search.add_argument("--lang", default="ces+eng")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
