"""Vyhledávání stránek podle klíčových slov v textu (OCR / PDF text)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Předvolby pro „modely / témata kolem Formule 1“ (OCR umí zkreslit text — držíme široké vzory)
F1_PRESET: list[re.Pattern[str]] = [
    re.compile(r"\bF[-\s]?1\b", re.IGNORECASE),
    re.compile(r"formule\s*1", re.IGNORECASE),
    re.compile(r"formula\s*1", re.IGNORECASE),
    re.compile(r"grand\s+prix", re.IGNORECASE),
    re.compile(r"scuderia", re.IGNORECASE),
    re.compile(r"ferrari", re.IGNORECASE),
    re.compile(r"mclaren", re.IGNORECASE),
    re.compile(r"williams", re.IGNORECASE),
    re.compile(r"závodní\s+aut", re.IGNORECASE),
    re.compile(r"zavodni\s+aut", re.IGNORECASE),
    re.compile(r"vůz\s+F1", re.IGNORECASE),
    re.compile(r"vuz\s+F1", re.IGNORECASE),
]


@dataclass
class Match:
    path: str
    page: int | None  # 1-based pro PDF; None u obrázku
    matched: list[str]


def find_matches(text: str, patterns: list[re.Pattern[str]]) -> list[str]:
    if not text or not text.strip():
        return []
    found: list[str] = []
    seen: set[str] = set()
    for pat in patterns:
        m = pat.search(text)
        if m:
            key = m.group(0).strip()
            if key and key.lower() not in seen:
                seen.add(key.lower())
                found.append(key)
    return found


def path_filter(path: Path, contains: str | None) -> bool:
    if contains is None or contains == "":
        return True
    c = contains.lower()
    return c in str(path).lower()
