"""Thera.py — distant reading für deutsche und englische Therapietranskripte.

    In jeder Stunde vorhanden. Lesbar erst über das Jahr.

Dieses Paket ist bewusst ein normales Python-Paket und kein Inline-Skript:
derselbe Code läuft im Browser über Pyodide **und** lokal per ``pip install``
über ein ganzes Korpus, und er lässt sich in einer CI testen.

Öffentliche Oberfläche für die Browser-Brücke sind die Funktionen ganz unten.
Sie geben allesamt JSON-*Strings* zurück, nicht Python-Objekte. Das ist eine
bewusste Entscheidung: die Grenze zwischen Python und JavaScript bleibt damit
eine einzige, gut sichtbare Stelle, statt über Proxy-Objekte im ganzen
Frontend zu verlaufen.
"""

from __future__ import annotations

import json

from . import sprachen
from .ingest import KLIENT, THERAPEUT, UNBEKANNT, Befund, Sitzung, Turn, lies
from .report import VERSION, Korpus

__all__ = [
    "VERSION", "Korpus", "Sitzung", "Turn", "Befund", "lies",
    "THERAPEUT", "KLIENT", "UNBEKANNT",
    "korpus", "lade", "befunde", "namensvorschlaege", "pseudonymisiere",
    "bericht", "kwic", "kollokationen", "ausschnitt", "belege", "turns",
    "namenstabelle", "sprecher_tauschen", "sprache_setzen", "export", "leeren",
    "sprachen",
]

# Ein Korpus pro geladener Seite. Der Zustand lebt hier und nirgends sonst.
korpus = Korpus()


def _json(objekt) -> str:
    return json.dumps(objekt, ensure_ascii=False, allow_nan=False)


# ---------------------------------------------------------------------------
# Browser-Brücke
# ---------------------------------------------------------------------------

def lade(dateien_json: str, klient: str | None = None,
         sprache: str | None = None) -> str:
    """``dateien_json`` = ``[{"name": …, "inhalt": …, "klient": …, "sprache": …}, …]``.

    ``sprache`` ist optional und überschreibt die Erkennung für alle Dateien
    dieses Aufrufs. Ohne sie entscheidet der Dateiname, und ohne Hinweis dort
    die Erkennung — siehe ``ingest.bestimme_sprache``.
    """
    dateien = json.loads(dateien_json)
    return _json(korpus.lade(dateien, klient_id=klient, sprache=sprache or None))


def befunde() -> str:
    return _json([s.befund.als_dict() for s in korpus.sitzungen if s.befund])


def namensvorschlaege() -> str:
    return _json(korpus.namensvorschlaege())


def pseudonymisiere(bestaetigte_json: str | None = None) -> str:
    bestaetigte = json.loads(bestaetigte_json) if bestaetigte_json else None
    return _json(korpus.pseudonymisiere(bestaetigte))


def bericht() -> str:
    return _json(korpus.bericht())


def kwic(begriff: str, klient: str | None = None, sprecher: str | None = None) -> str:
    return _json(korpus.kwic(begriff, klient or None, sprecher or None))


def kollokationen(begriff: str, klient: str, sprecher: str = KLIENT) -> str:
    return _json(korpus.kollokationen(begriff, klient, sprecher))


def ausschnitt(klient: str, sid: str, turn: int, start: int, end: int) -> str:
    return _json(korpus.ausschnitt(klient, sid, int(turn), int(start), int(end)))


def belege(klient: str, marker: str, sprecher: str = KLIENT,
           sid: str | None = None) -> str:
    return _json(korpus.belege(klient, marker, sprecher, sid or None))


def turns(sid: str, von: int = 0, bis: int = 10_000) -> str:
    return _json(korpus.turns(sid, int(von), int(bis)))


def namenstabelle() -> str:
    return _json(korpus.namenstabelle())


def sprecher_tauschen(sid: str) -> str:
    korpus.sprecher_tauschen(sid)
    return _json({"ok": True, "sid": sid})


def sprache_setzen(sid: str, code: str) -> str:
    """Korrigiert die erkannte Sprache einer Sitzung von Hand."""
    korpus.sprache_setzen(sid, code)
    return _json({"ok": True, "sid": sid, "sprache": code})


def export() -> str:
    return _json(korpus.export())


def leeren() -> str:
    korpus.leeren()
    return _json({"ok": True})
