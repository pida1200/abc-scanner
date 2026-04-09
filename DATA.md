# Umístění skenů (nejsou v gitu)

Skeny časopisů zabírají hodně místa — v repozitáři je jen kód. Data drž **mimo projekt**.

## Kořen na disku 1 TB

Typická cesta na macOS po připojení disku:

```text
/Volumes/1TB/casopisy/
```

Skeny drž v jednom kořeni (doporučeno `casopisy`), aby šly jednoduše prohledávat a dávkově zpracovávat.

Pokud máš disk připojený jinak nebo jiné jméno svazku, uprav cestu (např. `/Volumes/Externi/casopisy`).

## Formáty

- **JPG / JPEG** — jedna stránka = jeden soubor
- **PNG, TIFF** — totéž
- **PDF** — jeden soubor může mít více stran; nástroj při OCR/projde všechny strany

## Doporučená struktura složek (příklad)

```text
/Volumes/1TB/casopisy/
  ABC/
    1985/
      01/
        strana_001.jpg
        strana_002.jpg
      1985-rocnik.pdf
    1990/
      ...
```

Strukturu si můžeš upravit podle toho, jak skenuješ — důležité je mít konzistentní pojmenování, ať jde dělat dávkové zpracování.

## Práce z repa ABC

Buď zadej absolutní cestu:

```bash
abc-scanner list "/Volumes/1TB/casopisy/ABC"
```

Nebo v adresáři `ABC` vytvoř **symbolický odkaz** jen pro sebe (do gitu ho nedávej):

```bash
ln -s "/Volumes/1TB/casopisy" ./data-casopisy
abc-scanner list ./data-casopisy/ABC
```

Soubor `data-casopisy` je v `.gitignore`, aby se omylem necommitoval.
