"""Verlorene Fäden."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from . import sprachen
from .dialogue import ist_rueckkanal
from .ingest import KLIENT, THERAPEUT, Sitzung, Turn
from .tokenize import tokenisiere

# Schwellen.
MIN_AFFEKT = 2               # benannte Gefühlswörter im Klientenbeitrag
MAX_AUFNAHME = 0.10          # Anteil übernommener Inhaltswörter
MAX_RUECKKEHR = 0.15         # Anteil im übernächsten Klientenbeitrag
MIN_WOERTER = 25             # absolute Untergrenze für „substanzieller Beitrag“


@dataclass
class Faden:
    sid: str
    sitzung_nr: int | None
    turn_klient: int
    turn_therapeut: int
    turn_danach: int | None
    woerter: int
    affekt: int
    affekt_woerter: list[str]
    aufnahme: float
    rueckkehr: float
    staerke: float
    inhalt: list[str] = field(default_factory=list)

    def als_dict(self) -> dict:
        return {
            "sid": self.sid, "nr": self.sitzung_nr,
            "turnKlient": self.turn_klient,
            "turnTherapeut": self.turn_therapeut,
            "turnDanach": self.turn_danach,
            "woerter": self.woerter,
            "affekt": self.affekt,
            "affektWoerter": self.affekt_woerter,
            "aufnahme": round(self.aufnahme, 3),
            "rueckkehr": round(self.rueckkehr, 3),
            "staerke": round(self.staerke, 3),
            "inhalt": self.inhalt[:10],
        }


def _inhalt(text: str, sprache: str = sprachen.STANDARD) -> set[str]:
    pak = sprachen.paket(sprache)
    stopp = pak.funktion.STOPPWOERTER
    return {
        pak.lemma(t.klein) for t in tokenisiere(text, pak.CODE)
        if t.ist_wort and len(t.text) > 2 and t.klein not in stopp
    }


def affektwoerter(text: str, sprache: str = sprachen.STANDARD) -> list[str]:
    """Benannte Gefühlswörter und Körperaffekt in einem Beitrag."""
    pak = sprachen.paket(sprache)
    emo = pak.emotion
    gefunden = []
    for t in tokenisiere(text, pak.CODE):
        if not t.ist_wort:
            continue
        w = t.klein
        if w in emo.WORT_ZU_FAMILIE or w in emo.KOERPER_AFFEKT:
            gefunden.append(w)
    return gefunden


def finde(sitzung: Sitzung) -> list[Faden]:
    """Kandidaten für verlorene Fäden in einer Sitzung."""
    if not sitzung.hat_sprecher:
        return []

    code = getattr(sitzung, "sprache", sprachen.STANDARD)
    klient_turns = [t for t in sitzung.turns
                    if t.sprecher == KLIENT and not ist_rueckkanal(t, code)]
    if len(klient_turns) < 4:
        return []

    laengen = [len(t.text.split()) for t in klient_turns]
    median = statistics.median(laengen)
    schwelle = max(MIN_WOERTER, median)

    faeden: list[Faden] = []
    for i, turn in enumerate(sitzung.turns):
        if turn.sprecher != KLIENT or ist_rueckkanal(turn, code):
            continue
        woerter = len(turn.text.split())
        if woerter < schwelle:
            continue
        affekt = affektwoerter(turn.text, code)
        if len(affekt) < MIN_AFFEKT:
            continue

        antwort = _naechster(sitzung.turns, i, THERAPEUT, code)
        if antwort is None:
            continue
        inhalt_k = _inhalt(turn.text, code)
        if not inhalt_k:
            continue
        inhalt_t = _inhalt(antwort.text, code)
        aufnahme = len(inhalt_k & inhalt_t) / len(inhalt_k)
        if aufnahme > MAX_AUFNAHME:
            continue

        danach = _naechster(sitzung.turns, antwort.idx, KLIENT, code)
        rueckkehr = 0.0
        if danach is not None:
            inhalt_d = _inhalt(danach.text, code)
            rueckkehr = len(inhalt_k & inhalt_d) / len(inhalt_k)
            if rueckkehr > MAX_RUECKKEHR:
                continue

        # Stärke aus Affekt, Länge und Rückkehr.
        affektdichte = len(affekt) / max(woerter, 1)
        komponenten = (
            affektdichte / (affektdichte + 0.04),          # Ladung
            woerter / (woerter + schwelle),                # Substanz
            1.0 - aufnahme / MAX_AUFNAHME,                 # nicht aufgegriffen
            1.0 - rueckkehr / MAX_RUECKKEHR,               # nicht zurückgekehrt
        )
        produkt = 1.0
        for wert in komponenten:
            produkt *= max(wert, 1e-6)
        staerke = produkt ** (1.0 / len(komponenten))      # geometrisches Mittel
        faeden.append(Faden(
            sid=sitzung.sid, sitzung_nr=sitzung.nummer,
            turn_klient=turn.idx, turn_therapeut=antwort.idx,
            turn_danach=danach.idx if danach else None,
            woerter=woerter, affekt=len(affekt),
            affekt_woerter=sorted(set(affekt))[:8],
            aufnahme=aufnahme, rueckkehr=rueckkehr, staerke=staerke,
            inhalt=sorted(inhalt_k - inhalt_t)[:10],
        ))

    faeden.sort(key=lambda f: -f.staerke)
    return faeden


def _naechster(turns: list[Turn], ab: int, sprecher: str,
               sprache: str = sprachen.STANDARD) -> Turn | None:
    for turn in turns[ab + 1: ab + 5]:
        if turn.sprecher == sprecher and not ist_rueckkanal(turn, sprache):
            return turn
    return None


def ueber_sitzungen(sitzungen: list[Sitzung], grenze: int = 60) -> list[Faden]:
    alle: list[Faden] = []
    for sitzung in sitzungen:
        alle.extend(finde(sitzung))
    alle.sort(key=lambda f: -f.staerke)
    return alle[:grenze]


RAHMUNG = (
    "Moments where something loaded was said and the conversation went "
    "elsewhere. Not a list of mistakes — threads are left lying for good "
    "reasons. To be re-read, not worked through."
)
