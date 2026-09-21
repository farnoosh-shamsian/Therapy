"""Kommandozeile — derselbe Code, ganzes Korpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .report import Korpus

LESBARE_ENDUNGEN = {".txt", ".vtt", ".srt", ".json", ".csv", ".tsv", ".docx", ".md"}


def _dateien_einlesen(pfade: list[Path]) -> list[dict]:
    dateien = []
    for pfad in pfade:
        if pfad.suffix.lower() == ".docx":
            dateien.append({"name": pfad.name, "inhalt": pfad.read_bytes()})
        else:
            dateien.append({"name": pfad.name,
                            "inhalt": pfad.read_text(encoding="utf-8", errors="replace")})
    return dateien


# Dateien, die in einem Transkriptordner liegen können.
NICHT_TRANSKRIPT = {"manifest.json", "package.json", "tsconfig.json"}


def _sammle(ort: Path) -> list[Path]:
    if ort.is_file():
        return [ort]
    return sorted(p for p in ort.rglob("*")
                  if p.is_file() and p.suffix.lower() in LESBARE_ENDUNGEN
                  and p.name.lower() not in NICHT_TRANSKRIPT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="therapy",
        description="Distant reading for German and English psychotherapy "
                    "transcripts. The language is detected per file.")
    unter = parser.add_subparsers(dest="befehl", required=True)

    p_aus = unter.add_parser("auswerten", help="analyse transcripts")
    p_aus.add_argument("ort", type=Path, help="file or folder")
    p_aus.add_argument("--ausgabe", type=Path, default=None,
                       help="where to write the JSON report (default: stdout)")
    p_aus.add_argument("--klient", default=None,
                       help="client id, if it is not in the filename")
    p_aus.add_argument("--keine-pseudonyme", action="store_true",
                       help="keep the real names in the text; they are still "
                            "detected, so the sociogram stays intact")
    p_aus.add_argument("--sprache", default=None, choices=["de", "en"],
                       help="force a language instead of detecting it per file")

    p_bef = unter.add_parser("befund", help="show only the ingest findings")
    p_bef.add_argument("ort", type=Path)
    p_bef.add_argument("--sprache", default=None, choices=["de", "en"],
                       help="force a language instead of detecting it per file")

    p_kwic = unter.add_parser("konkordanz", help="concordance for one term")
    p_kwic.add_argument("ort", type=Path)
    p_kwic.add_argument("begriff")
    p_kwic.add_argument("--sprecher", default=None, choices=["T", "K"])
    p_kwic.add_argument("--sprache", default=None, choices=["de", "en"],
                        help="force a language instead of detecting it per file")

    args = parser.parse_args(argv)
    pfade = _sammle(args.ort)
    if not pfade:
        print(f"No readable files under {args.ort}", file=sys.stderr)
        return 1

    korpus = Korpus()
    befunde = korpus.lade(_dateien_einlesen(pfade),
                          klient_id=getattr(args, "klient", None),
                          sprache=getattr(args, "sprache", None))

    if args.befehl == "befund":
        for b in befunde:
            print(f"\n{b['dateiname']}  [{b['format']}]")
            print(f"  turns: {b['turns']}, words: {b['woerter']}")
            print(f"  language: {b['spracheName']} ({b['spracheQuelle']}, "
                  f"confidence {b['spracheSicherheit']:.2f})")
            print(f"  speakers: {b['sprecherQuelle']} {b['labels'] or ''}")
            print(f"  timestamps: {'yes' if b['zeitstempel'] else 'no'}")
            for w in b["warnungen"]:
                print(f"  ! {w}")
            for n in b["nichtVerfuegbar"]:
                print(f"  - unavailable: {n}")
        return 0

    korpus.pseudonymisiere(
        ersetzen=not getattr(args, "keine_pseudonyme", False))

    if args.befehl == "konkordanz":
        for zeile in korpus.kwic(args.begriff, sprecher=args.sprecher):
            nr = zeile.get("nr")
            print(f"S{nr:02d} T{zeile['turn']:<4} {zeile['sprecher']}  "
                  f"…{zeile['links'][-40:]:>40} [{zeile['treffer']}] "
                  f"{zeile['rechts'][:40]}…")
        return 0

    bericht = korpus.bericht()
    text = json.dumps(bericht, ensure_ascii=False, indent=2)
    if args.ausgabe:
        args.ausgabe.write_text(text, encoding="utf-8")
        print(f"Report written: {args.ausgabe}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
