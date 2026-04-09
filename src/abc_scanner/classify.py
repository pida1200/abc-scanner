"""Heuristická klasifikace typu stránky podle OCR textu."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class PageKind(str, Enum):
    VYSTRIHOVANKA = "vystrihovanka"
    FORMULAR = "formular"
    JINE = "jine"


# Klíčová slova / vzory (čeština, malá písmena v porovnání)
_VYSTRIHOVANKA = [
    "vystřih",
    "vystrih",
    "šablona",
    "sablona",
    "vystřihni",
    "vystrihni",
    "nůžky",
    "nuzky",
    "lep",
    "slepuj",
    "papírov",
    "papierov",
]

_FORMULAR = [
    "formulář",
    "formular",
    "objednáv",
    "objednav",
    "jméno",
    "jmeno",
    "příjmení",
    "prijmeni",
    "adresa",
    "psč",
    "psc",
    "podpis",
    "razítko",
    "razitko",
    "kupon",
    "soutěž",
    "soutez",
    "odešlete",
    "odeslete",
    "zašlete",
    "zaslete",
]


@dataclass
class Classification:
    kind: PageKind
    score: float
    hints: list[str]


def _normalize(text: str) -> str:
    return text.lower()


def classify_text(text: str) -> Classification:
    """Vrátí nejpravděpodobnější typ stránky a skóre 0–1."""
    t = _normalize(text)
    hints: list[str] = []

    v_score = 0.0
    for w in _VYSTRIHOVANKA:
        if w in t:
            v_score += 0.25
            hints.append(f"vystřihovánka:{w}")

    f_score = 0.0
    for w in _FORMULAR:
        if w in t:
            f_score += 0.2
            hints.append(f"formulář:{w}")

    # Čárkované čáry často u vystřihovánek (jen slabý signál)
    if re.search(r"[-‐‑]{3,}", text) or "· · ·" in text:
        v_score += 0.1
        hints.append("vystřihovánka:čárkované")

    v_score = min(v_score, 1.0)
    f_score = min(f_score, 1.0)

    if v_score >= f_score and v_score >= 0.25:
        return Classification(PageKind.VYSTRIHOVANKA, v_score, hints)
    if f_score >= v_score and f_score >= 0.2:
        return Classification(PageKind.FORMULAR, f_score, hints)
    return Classification(PageKind.JINE, max(v_score, f_score, 0.0), hints)


def merge_vision(
    text_cls: Classification,
    vision_score: float,
    vision_hints: list[str],
    text_len: int,
) -> Classification:
    """Zkombinuje OCR heuristiky s vizuálním skóre.

    Vizuální heuristiky jsou primárně pro vystřihovánky/modely.
    """
    hints = list(text_cls.hints)
    hints.extend(vision_hints)

    # Pokud je na stránce hodně textu (OCR), je to typicky článek, ne vystřihovánka.
    # V takovém případě nedovolíme, aby samotný vizuál přepnul typ.
    if text_len >= 800:
        return Classification(text_cls.kind, max(text_cls.score, vision_score * 0.4), hints)

    # Pokud vizuál silně naznačuje model, přepneme na vystrihovanka.
    if vision_score >= 0.55:
        return Classification(PageKind.VYSTRIHOVANKA, max(text_cls.score, vision_score), hints)

    # Pokud text už říká vystrihovanka/formular, necháme.
    if text_cls.kind != PageKind.JINE:
        return Classification(text_cls.kind, max(text_cls.score, vision_score * 0.8), hints)

    # Jinak jen zvedneme skóre "jine" pro informaci.
    return Classification(PageKind.JINE, max(text_cls.score, vision_score * 0.6), hints)
