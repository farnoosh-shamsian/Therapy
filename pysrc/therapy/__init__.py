"""Distant reading für Therapietranskripte."""

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

# Ein Korpus pro geladener Seite.
korpus = Korpus()


def _json(objekt) -> str:
    return json.dumps(objekt, ensure_ascii=False, allow_nan=False)


# ---------------------------------------------------------------------------
# Browser-Brücke
# ---------------------------------------------------------------------------

def lade(dateien_json: str, klient: str | None = None,
         sprache: str | None = None) -> str:
    """``dateien_json`` = ``[{"name":."""
    dateien = json.loads(dateien_json)
    return _json(korpus.lade(dateien, klient_id=klient, sprache=sprache or None))


def befunde() -> str:
    """Ein Eintrag je *Datei*."""
    gesehen: list[int] = []
    raus: list[dict] = []
    for sitzung in korpus.sitzungen:
        if sitzung.befund is None or id(sitzung.befund) in gesehen:
            continue
        gesehen.append(id(sitzung.befund))
        raus.append(sitzung.befund.als_dict())
    return _json(raus)


def namensvorschlaege() -> str:
    return _json(korpus.namensvorschlaege())


def pseudonymisiere(bestaetigte_json: str | None = None,
                    ersetzen: bool = True) -> str:
    """``ersetzen=False``: Namen bleiben stehen, werden aber weiter erkannt."""
    bestaetigte = json.loads(bestaetigte_json) if bestaetigte_json else None
    return _json(korpus.pseudonymisiere(bestaetigte, ersetzen=bool(ersetzen)))


def bericht() -> str:
    return _json(korpus.bericht())


def kwic(begriff: str, klient: str | None = None, sprecher: str | None = None) -> str:
    return _json(korpus.kwic(begriff, klient or None, sprecher or None))


def kollokationen(begriff: str, klient: str, sprecher: str = KLIENT) -> str:
    return _json(korpus.kollokationen(begriff, klient, sprecher))


def klient_umbenennen(alt: str, neu: str) -> str:
    korpus.klient_umbenennen(alt, neu)
    return _json({"ok": True})


def wortverlauf(wort: str, klient: str, sprecher: str = KLIENT) -> str:
    return _json(korpus.wortverlauf(wort, klient, sprecher))


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
    """Korrigiert die erkannte Sprache einer Sitzung von."""
    korpus.sprache_setzen(sid, code)
    return _json({"ok": True, "sid": sid, "sprache": code})


def export() -> str:
    return _json(korpus.export())


def leeren() -> str:
    korpus.leeren()
    return _json({"ok": True})
