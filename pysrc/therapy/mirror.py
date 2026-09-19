"""Der Spiegel — über die ganze Fallgeschichte hinweg, über ihn.

Das ist der Teil, der am unangenehmsten und am nützlichsten ist. Therapeuten
werden auf den eigenen Prozess hin ausgebildet, bekommen darüber aber fast nie
quantitative Rückmeldung.

Zwei Warnungen, die in der Oberfläche stehen und nicht nur hier:

1. **Die Interventionsklassifikation ist Konfidenz C.** Regelbasiert, aus
   Mustern, ohne trainierten Klassifikator. Der absolute Anteil „Deutungen“
   trägt nichts.
2. **Der Vergleich zwischen Klienten trägt mehr als jede Einzelzahl.** Derselbe
   systematische Fehler liegt auf beiden Seiten und kürzt sich weitgehend
   heraus. „Sie deuten bei A dreimal so oft wie bei B“ ist die Frage, für die
   sich der ganze Aufwand lohnt.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import sprachen
from .dialogue import Dialogkennzahlen, ist_rueckkanal
from .ingest import THERAPEUT, Sitzung
from .lexika import intervention as lex_i
from .tokenize import tokenisiere

_MUSTER_CACHE: dict[str, dict[str, list]] = {}


def _muster(pak) -> dict[str, list]:
    if pak.CODE not in _MUSTER_CACHE:
        _MUSTER_CACHE[pak.CODE] = {
            kategorie: [re.compile(m) for m in muster]
            for kategorie, muster in pak.intervention.MUSTER.items()
        }
    return _MUSTER_CACHE[pak.CODE]


def klassifiziere(text: str, sprache: str = sprachen.STANDARD) -> str:
    """Ein Label pro Beitrag. Erster Treffer in der Prioritätsreihenfolge gewinnt.

    Beide Sprachen führen dieselben neun Kategorien in derselben Reihenfolge,
    damit ein Interventionsprofil bei einem deutschen und einem englischen
    Fall dieselben Zeilen hat. Die Muster darunter haben nichts gemeinsam.
    """
    pak = sprachen.paket(sprache)
    muster = _muster(pak)
    klein = text.lower().strip()
    for kategorie in pak.intervention.KATEGORIEN_REIHENFOLGE:
        for m in muster.get(kategorie, ()):
            if m.search(klein):
                return kategorie
    return "sonstiges"


@dataclass
class Klientenprofil:
    klient_id: str
    sitzungen: int = 0
    woerter_t: int = 0
    redeanteil: float = 0.0
    interventionen: Counter = field(default_factory=Counter)
    fragen_offen: int = 0
    fragen_geschlossen: int = 0
    aufnahme: float = 0.0
    lsm: float = 0.0
    sprachen: list[str] = field(default_factory=list)
    belege: dict[str, list] = field(default_factory=lambda: defaultdict(list))

    def anteile(self) -> dict[str, float]:
        gesamt = sum(self.interventionen.values()) or 1
        return {k: v / gesamt for k, v in self.interventionen.items()}

    def als_dict(self) -> dict:
        return {
            "klient": self.klient_id,
            "sitzungen": self.sitzungen,
            "sprachen": self.sprachen,
            "spracheName": ", ".join(sprachen.name(c) for c in self.sprachen),
            "woerterT": self.woerter_t,
            "redeanteil": round(self.redeanteil, 4),
            "interventionen": dict(self.interventionen),
            "anteile": {k: round(v, 4) for k, v in self.anteile().items()},
            "fragenOffen": self.fragen_offen,
            "fragenGeschlossen": self.fragen_geschlossen,
            "frageQuote": round(
                self.fragen_offen / (self.fragen_offen + self.fragen_geschlossen), 4
            ) if (self.fragen_offen + self.fragen_geschlossen) else None,
            "aufnahme": round(self.aufnahme, 4),
            "lsm": round(self.lsm, 4),
            "belege": {k: v[:5] for k, v in self.belege.items()},
        }


def profil(klient_id: str, sitzungen: list[Sitzung],
           dialoge: list[Dialogkennzahlen]) -> Klientenprofil:
    p = Klientenprofil(klient_id=klient_id, sitzungen=len(sitzungen))
    p.sprachen = sorted({getattr(s, "sprache", sprachen.STANDARD) for s in sitzungen})
    for sitzung in sitzungen:
        code = getattr(sitzung, "sprache", sprachen.STANDARD)
        for turn in sitzung.turns:
            if turn.sprecher != THERAPEUT:
                continue
            p.woerter_t += len(turn.text.split())
            if ist_rueckkanal(turn, code):
                p.interventionen["rueckkanal"] += 1
                continue
            kategorie = klassifiziere(turn.text, code)
            p.interventionen[kategorie] += 1
            if len(p.belege[kategorie]) < 12:
                p.belege[kategorie].append(
                    [sitzung.sid, turn.idx, turn.text[:220]])
    if dialoge:
        p.redeanteil = sum(d.redeanteil_t for d in dialoge) / len(dialoge)
        p.aufnahme = sum(d.aufnahme for d in dialoge) / len(dialoge)
        p.lsm = sum(d.lsm for d in dialoge) / len(dialoge)
        p.fragen_offen = sum(d.fragen_offen for d in dialoge)
        p.fragen_geschlossen = sum(d.fragen_geschlossen for d in dialoge)
    return p


# ---------------------------------------------------------------------------
# Vergleich zwischen Klienten
# ---------------------------------------------------------------------------

def vergleich(profile: list[Klientenprofil], min_klienten: int = 2) -> list[dict]:
    """Die Zeilen, für die die Spiegel-Ansicht gebaut wurde.

    Für jede Kennzahl: wo ist der Abstand zwischen Klienten am grössten.
    Sortiert nach Verhältnis, nicht nach Differenz — „dreimal so oft“ ist die
    Beobachtung, die etwas auslöst, „vier Prozentpunkte mehr“ nicht.
    """
    if len(profile) < min_klienten:
        return []
    zeilen: list[dict] = []
    kategorien = {k for p in profile for k in p.interventionen}
    sprache_je_klient = {p.klient_id: tuple(p.sprachen) for p in profile}

    def sprachgrenze(a: str, b: str) -> bool:
        """Liegt zwischen diesen beiden Klienten eine Sprachgrenze?

        Wenn ja, ist die Zeile nicht falsch, aber sie trägt weniger: die
        Muster, Stoppwörter und Funktionswortkategorien der beiden Sprachen
        sind unterschiedlich gross, und ein Teil des Unterschieds ist deshalb
        das Werkzeug und nicht der Therapeut. Die Oberfläche markiert solche
        Zeilen, statt sie wegzulassen — weggelassen wäre in einer gemischten
        Praxis die halbe Tabelle.
        """
        return sprache_je_klient.get(a) != sprache_je_klient.get(b)

    for kategorie in sorted(kategorien):
        werte = [(p.klient_id, p.anteile().get(kategorie, 0.0)) for p in profile]
        werte = [(k, v) for k, v in werte if v > 0]
        if len(werte) < 2:
            continue
        werte.sort(key=lambda kv: -kv[1])
        hoch, niedrig = werte[0], werte[-1]
        if niedrig[1] <= 0:
            continue
        verhaeltnis = hoch[1] / niedrig[1]
        if verhaeltnis < 1.5:
            continue
        zeilen.append({
            "kennzahl": lex_i.ANZEIGE_NAMEN.get(kategorie, kategorie),
            "schluessel": kategorie,
            "hoch": hoch[0], "hochWert": round(hoch[1], 4),
            "niedrig": niedrig[0], "niedrigWert": round(niedrig[1], 4),
            "verhaeltnis": round(verhaeltnis, 2),
            "sprachgrenze": sprachgrenze(hoch[0], niedrig[0]),
            "satz": (f"{_lesbar(kategorie)} {verhaeltnis:.1f}× more often with "
                     f"{hoch[0]} than with {niedrig[0]}."),
        })

    for schluessel, name, holen in (
        ("redeanteil", "Talk ratio", lambda p: p.redeanteil),
        ("aufnahme", "Lexical uptake", lambda p: p.aufnahme),
        ("lsm", "Style matching", lambda p: p.lsm),
        ("frageQuote", "Share of open questions",
         lambda p: (p.fragen_offen / (p.fragen_offen + p.fragen_geschlossen)
                    if (p.fragen_offen + p.fragen_geschlossen) else 0.0)),
    ):
        werte = [(p.klient_id, holen(p)) for p in profile]
        werte = [(k, v) for k, v in werte if v > 0]
        if len(werte) < 2:
            continue
        werte.sort(key=lambda kv: -kv[1])
        hoch, niedrig = werte[0], werte[-1]
        verhaeltnis = hoch[1] / niedrig[1] if niedrig[1] else None
        if verhaeltnis is None or verhaeltnis < 1.2:
            continue
        zeilen.append({
            "kennzahl": name, "schluessel": schluessel,
            "hoch": hoch[0], "hochWert": round(hoch[1], 4),
            "niedrig": niedrig[0], "niedrigWert": round(niedrig[1], 4),
            "verhaeltnis": round(verhaeltnis, 2),
            "sprachgrenze": sprachgrenze(hoch[0], niedrig[0]),
            # Eine Nachkommastelle, nicht null: bei lexikalischer Aufnahme
            # liegen die Werte im niedrigen einstelligen Prozentbereich, und
            # "1 % gegen 0 %" neben einem Verhältnis von 2,2 sieht nach einem
            # Fehler aus, obwohl nur gerundet wurde.
            "satz": (f"{name}: {hoch[1]:.1%} with {hoch[0]}, "
                     f"{niedrig[1]:.1%} with {niedrig[0]}."),
        })

    zeilen.sort(key=lambda z: -z["verhaeltnis"])
    return zeilen


def _lesbar(kategorie: str) -> str:
    return {
        "deutung": "You interpret",
        "spiegelung": "You reflect back",
        "validierung": "You validate",
        "psychoedukation": "You explain",
        "selbstoffenbarung": "You speak about yourself",
        "strukturierung": "You structure the hour",
        "frage_offen": "You ask open questions",
        "frage_geschlossen": "You ask closed questions",
        "rueckkanal": "You listen without speaking",
        "sonstiges": "Turns that fit no category appear",
    }.get(kategorie, kategorie)


# ---------------------------------------------------------------------------
# Idiolekt
# ---------------------------------------------------------------------------

def idiolekt(sitzungen_je_klient: dict[str, list[Sitzung]],
             grenze: int = 30) -> list[dict]:
    """Die eigenen Formeln über die ganze Fallgeschichte.

    Sagt er allen dieselben elf Sätze? Demütigend und nützlich.

    Gewertet wird eine Phrase nur, wenn sie bei mehreren Klienten fällt —
    sonst ist sie nicht Idiolekt, sondern gehört zu diesem einen Fall.
    """
    phrase_gesamt: Counter = Counter()
    phrase_klienten: dict[tuple, set[str]] = defaultdict(set)
    phrase_beleg: dict[tuple, list] = {}
    phrase_sprache: dict[tuple, str] = {}

    for klient_id, sitzungen in sitzungen_je_klient.items():
        for sitzung in sitzungen:
            code = getattr(sitzung, "sprache", sprachen.STANDARD)
            pak = sprachen.paket(code)
            lex = pak.intervention
            for turn in sitzung.turns:
                if turn.sprecher != THERAPEUT or ist_rueckkanal(turn, code):
                    continue
                formen = [t.klein for t in tokenisiere(turn.text, code) if t.ist_wort]
                for n in range(lex.IDIOLEKT_MIN_NGRAMM,
                               lex.IDIOLEKT_MAX_NGRAMM + 1):
                    for i in range(len(formen) - n + 1):
                        gramm = tuple(formen[i:i + n])
                        text = " ".join(gramm)
                        if text in lex.IDIOLEKT_AUSSCHLUSS:
                            continue
                        phrase_gesamt[gramm] += 1
                        phrase_klienten[gramm].add(klient_id)
                        phrase_sprache[gramm] = code
                        phrase_beleg.setdefault(gramm,
                                                [sitzung.sid, turn.idx, turn.text[:200]])

    ergebnis = []
    for gramm, anzahl in phrase_gesamt.items():
        if anzahl < lex_i.IDIOLEKT_MIN_HAEUFIGKEIT:
            continue
        if len(phrase_klienten[gramm]) < lex_i.IDIOLEKT_MIN_KLIENTEN:
            continue
        ergebnis.append({
            "phrase": " ".join(gramm),
            "laenge": len(gramm),
            "anzahl": anzahl,
            "klienten": sorted(phrase_klienten[gramm]),
            "sprache": phrase_sprache.get(gramm),
            "beleg": phrase_beleg.get(gramm),
        })

    # Längere Phrasen schlagen kürzere: wer „könnte es sein dass“ hat, braucht
    # „es sein dass“ nicht auch noch in der Liste.
    ergebnis.sort(key=lambda e: (-e["anzahl"], -e["laenge"]))
    behalten: list[dict] = []
    for eintrag in ergebnis:
        if any(eintrag["phrase"] in b["phrase"] for b in behalten):
            continue
        behalten.append(eintrag)
        if len(behalten) >= grenze:
            break
    return behalten


# Zusatzhinweis, der nur bei einer gemischtsprachigen Praxis eingeblendet wird.
HINWEIS_SPRACHGRENZE = (
    "Some of the rows below compare a client seen in German with one seen in "
    "English. Those rows are marked. They are not meaningless, but part of the "
    "gap is the tool rather than you: the two languages have differently sized "
    "pattern sets, stop-word lists and function-word categories. Talk ratio and "
    "turn length survive the crossing more or less intact. Lexical uptake and "
    "style matching do not — compare those only within one language."
)

HINWEIS = (
    "Interventions are classified by rule and are correspondingly rough "
    "(confidence C). What does not carry weight is the percentage of your turns "
    "that are interpretations. What does is the comparison between clients: the "
    "same measurement error sits on both sides. A defensible absolute figure "
    "would need annotated German therapy utterances and a trained classifier — "
    "that is real work, and it is not faked here."
)
