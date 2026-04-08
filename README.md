# ABC — časopis ABC (skenery)

Nástroje pro práci se **naskenovanými stránkami** časopisu ABC: výpis souborů (**JPG, PNG, PDF, …**), OCR (Tesseract) a jednoduchá klasifikace typu stránky (**vystřihovánka**, **formulář**, jiné).

**Kde leží skeny:** na disku s časopisy — viz [DATA.md](DATA.md) (typicky `/Volumes/1TB/casopisy/`). Do gitu se velké soubory **nepřidávají**.

## Požadavky

- Python 3.9+
- Pro OCR: [Tesseract](https://github.com/tesseract-ocr/tesseract) s českým jazykovým balíčkem (`ces`)

macOS (Homebrew):

```bash
brew install tesseract tesseract-lang
```

## Instalace

```bash
cd ABC
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install .
```

Bez instalace balíčku můžeš spouštět přes `PYTHONPATH`:

```bash
PYTHONPATH=src python -m abc_scanner list "/Volumes/1TB/casopisy/ABC"
```

## Použití

Výpis skenů ve složce (rekurzivně):

```bash
abc-scanner list "/Volumes/1TB/casopisy/ABC"
```

OCR jednoho souboru (obrázek nebo PDF — u PDF se čtou všechny strany):

```bash
abc-scanner ocr "/Volumes/1TB/casopisy/ABC/1985/soubor.pdf"
```

Klasifikace složky (výstup CSV na stdout):

```bash
abc-scanner classify "/Volumes/1TB/casopisy/ABC/1985" > vysledky.csv
```

Vyhledávání stránek podle předvolby **`f1`** (Formule 1, F1, týmy, Grand Prix …) — prohledá rekurzivně soubory, jejichž cesta obsahuje **`ABC`** (např. skeny pod `Komiks`):

```bash
export PATH="/opt/homebrew/bin:$PATH"
python -u -m abc_scanner search "/Volumes/1TB/comix/Komiks" --preset f1 > f1-vysledky.csv
```

- Na macOS musí být **`tesseract`** v `PATH` (typicky Homebrew: `/opt/homebrew/bin`).
- Výstup CSV se **průběžně zapisuje** (flush po hlavičce a každém nálezu); volitelně použij i **`python -u`** jako další pojistku pro nebufferovaný výstup.

## Struktura repozitáře

```
ABC/
  src/abc_scanner/   # CLI (list, ocr, classify, search)
  requirements.txt
  setup.py
  DATA.md            # kde jsou skeny na 1TB disku
  README.md
```

## Licence

Soukromý projekt — doplň podle potřeby.
