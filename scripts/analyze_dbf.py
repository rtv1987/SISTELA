"""Reproducible FACT report; no import into domain tables and no DBF writes."""

import argparse
import json
from collections import Counter
from pathlib import Path

from sistela.parsers.dbf import read_dbf

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT)
    parser.add_argument("--encoding", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/sistela-dbf-analysis.md")
    args = parser.parse_args()
    tables = {p.name: read_dbf(p, encoding=args.encoding) for p in sorted(args.input.glob("*.dbf"))}
    if not tables:
        raise SystemExit("No DBF files found")
    lines = [
        "# SISTELA DBF analizė",
        "",
        "Atlikta 2026-09-28. FACT = perskaityti baitai ir įrašų patikra;",
        "INFERENCE = siūloma domeno reikšmė; UNKNOWN = nepatvirtinta.",
        "",
        "## FACT: bendras formatas",
        "",
        "Visi pateikti failai: version 0x30 (Visual FoxPro), LDID=3.",
        "dbfread pagal žymą parenka cp1252. Šiam rinkiniui aiškiai naudota cp1257.",
        "cp1257 tekstas „Įeigos kontrolinis įrenginys“ sutampa su pvz.xlsx C15.",
        "Visi įrašai dekoduoti strict režimu; N/F skaičiai skaitomi kaip Decimal.",
        "Blank skaitinis laukas lieka null. Visi šaltiniai tik skaityti.",
        "",
        "| Failas | Laukai | Deklaruota | Aktyvių | Ištrintų |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, t in tables.items():
        lines.append(
            f"| {name} | {len(t.fields)} | {t.declared_records} | {len(t.records)} | {t.deleted_records} |"
        )
    for name, t in tables.items():
        lines += [
            "",
            f"## FACT: {name}",
            "",
            f"SHA-256: `{t.checksum}`",
            "",
            "| Laukas | Tipas | Baitai | Dešimtainės vietos |",
            "|---|---|---:|---:|",
        ]
        for f in t.fields:
            lines.append(f"| {f.name} | {f.type} | {f.length} | {f.decimals} |")
        # Minimal, useful examples; omit project addresses and people.
        selected = {
            "SAMATA",
            "SKYRIUS",
            "SAM_EILUTE",
            "DET_EILUTE",
            "GRUP",
            "IKAINIS",
            "KODAS",
            "MATOVNT",
            "MATO_PAV",
            "KIEKIS",
            "KAINA",
            "PAVADIN",
            "POZ",
            "POZYMIS",
        }
        samples = [{k: v for k, v in row.items() if k in selected} for row in t.records[:3]]
        for sample in samples:
            if len(str(sample.get("PAVADIN", ""))) > 100:
                sample["PAVADIN"] = "[ilgas objekto pavadinimas praleistas]"
        lines += [
            "",
            "Pirmų įrašų pasirinktų laukų reikšmės (Decimal pateikti eilutėmis):",
            "",
            "```json",
            json.dumps(samples, ensure_ascii=False, indent=2, default=str),
            "```",
        ]

    key_fields = (
        "KOMPLEKSAS",
        "OBJEKTAS",
        "RANGOVAS",
        "SAMATA",
        "SKYRIUS",
        "SUSDARB1",
        "SAM_EILUTE",
        "DET_EILUTE",
    )

    def key(row):
        return tuple(row[k] for k in key_fields)

    if "sd25-04-14.dbf" in tables and "dd25-04-14.dbf" in tables:
        sd = tables["sd25-04-14.dbf"].records
        dd = tables["dd25-04-14.dbf"].records
        parents = Counter(key(row) for row in sd)
        headers = [row for row in dd if row["GRUP"] == 10]
        unmatched = sum(key(row) not in parents for row in dd)
        header_keys = Counter(key(row) for row in headers)
        mismatches = sum(
            not any(
                key(h) == key(s) and h["IKAINIS"] == s["IKAINIS"] and h["KIEKIS"] == s["KIEKIS"]
                for h in headers
            )
            for s in sd
        )
        lines += [
            "",
            "## FACT: jungčių patikra šiame rinkinyje",
            "",
            f"Kandidatinis raktas: `{', '.join(key_fields)}`.",
            f"sd eilučių {len(sd)}, unikalių raktų {len(parents)}, dd eilučių {len(dd)}.",
            f"dd be sd rakto: {unmatched}. dd GRUP=10 įrašų: {len(headers)}, unikalių raktų: {len(header_keys)}.",
            f"sd be sutampančio dd GRUP=10 kodo ir kiekio: {mismatches}.",
            "dd GRUP pasiskirstymas: " + str(dict(Counter(str(r["GRUP"]) for r in dd))) + ".",
        ]
    lines += [
        "",
        "## INFERENCE: reikšmės, ribotos šiam archyvui",
        "",
        "- sd panašu į sąmatos pozicijas; pavadinimo lauko nėra. dd GRUP=10 duoda",
        "  tos pačios pozicijos istorinio aprašymo tekstą ir tekstinį vienetą.",
        "- dd GRUP=20/30/40 panašu į darbo / medžiagų / mechanizmų išteklius.",
        "  Tai hipotezė pagal laukus ir pavyzdžius, ne patvirtinta SISTELA specifikacija.",
        "- pd panašu į išteklių kainų sąrašą; KODAS nėra automatiškai darbų normatyvas.",
        "- nd turi projekto, sąmatų ir skyrių pavadinimus; POZ lygmenų semantika dar nepatvirtinta.",
        "- td panašu į sumas / išlaidų grupes; skaičiavimo taisyklės nepatvirtintos.",
        "- od tuščias: schema patvirtinta, įrašų semantika nenustatyta.",
        "",
        "## UNKNOWN / TODO",
        "",
        "- Originalūs normatyvų katalogo pavadinimai. dd PAVADIN gali būti pervadintas.",
        "- Pilnas MATOVNT kodų žodynas ir 100m konversijų taisyklės.",
        "- nd/pd/td/od tarpusavio jungtys, null ir koeficientų semantika už šio archyvo ribų.",
        "- DBF archyvo atkūrimo, indeksų ir memo reikalavimai SISTELA programoje.",
        "- Sąmatos kainodaros atkartojimas, rašymas ir round-trip neįgyvendinti.",
        "",
        "## Saugus tolimesnis importas",
        "",
        "Galima pateikti vartotojui sd + dd GRUP=10 istorinio kodo/aprašymo kandidatus",
        "su šaltinio nuoroda. Jų negalima automatiškai laikyti patvirtintais mappingais ar",
        "originaliais normatyvų pavadinimais. Reikalinga žmogaus patvirtinimo eiga (6 fazė).",
        "",
    ]
    output = args.output.resolve()
    inputs = {p.resolve() for p in args.input.glob("*.dbf")}
    if output in inputs or output.suffix.lower() != ".md":
        raise SystemExit("Output must be a Markdown report, not a source file")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Inspected {len(tables)} DBFs; report: {output}")


if __name__ == "__main__":
    main()
