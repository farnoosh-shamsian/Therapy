"""Dialogdynamik: wer redet, wie lange, wie gefragt wird, wer wen aufnimmt.

Eine Vorentscheidung, die alle Zahlen hier betrifft: **Rückkanäle sind keine
Redebeiträge.** Ein Therapeuten-Turn, der nur aus „mhm“ besteht, ist Zuhören
und kein Beitrag. Zählt man ihn mit, sieht jede Redeanteilsstatistik falsch
aus — der Therapeut scheint viel öfter dran zu sein, als er es ist. Sie werden
deshalb gezählt, aber getrennt geführt.

**Zur Zweisprachigkeit.** Die Kennzahlen hier messen in beiden Sprachen
dasselbe und heissen deshalb gleich. Was sich unterscheidet, ist das Material,
mit dem sie gemessen werden: Fragemuster, Rückkanalformeln, Stoppwörter und
die neun LSM-Kategorien kommen aus dem Sprachpaket der jeweiligen Sitzung.

Eine Zahl verdient dabei eine Warnung, die sonst nirgends steht: **Style
Matching und lexikalische Aufnahme sind zwischen den Sprachen nicht
vergleichbar.** Beide rechnen über sprachspezifische Wortmengen — deutsche
Funktionswörter gegen deutsche, englische gegen englische — und die
Kategorien haben in den beiden Sprachen unterschiedliche Grösse. Innerhalb
eines Falles ist die Zahl aussagekräftig. Zwischen einem deutschen und einem
englischen Fall ist sie es nicht — und bei einem Fall, dessen Sitzungen die
Sprache wechseln, sagt der Klientenblock das über der Kurve.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field

from . import sprachen
from .ingest import KLIENT, THERAPEUT, Sitzung, Turn
from .tokenize import Token, tokenisiere

# Kompilierte Muster je Sprache, gebaut wenn zum ersten Mal gebraucht.
_MUSTER_CACHE: dict[str, dict[str, list]] = {}


def _muster(pak) -> dict[str, list]:
    if pak.CODE not in _MUSTER_CACHE:
        quelle = pak.dialogmuster.MUSTER
        _MUSTER_CACHE[pak.CODE] = {
            schluessel: [re.compile(m) for m in quelle[schluessel]]
            for schluessel in ("frage_offen", "frage_geschlossen", "rueckkanal")
        }
    return _MUSTER_CACHE[pak.CODE]


@dataclass
class Dialogkennzahlen:
    # Redeanteil
    woerter: dict[str, int] = field(default_factory=dict)
    turns: dict[str, int] = field(default_factory=dict)
    redeanteil_t: float = 0.0
    rueckkanal_turns: int = 0
    # Turn-Längen
    laengen: dict[str, list[int]] = field(default_factory=dict)
    median_laenge: dict[str, float] = field(default_factory=dict)
    p90_laenge: dict[str, float] = field(default_factory=dict)
    # Fragen
    fragen_offen: int = 0
    fragen_geschlossen: int = 0
    fragen_gesamt: int = 0
    frage_belege: list[list] = field(default_factory=list)
    # Aufnahme und Stil
    aufnahme: float = 0.0
    aufnahme_pro_paar: list[list] = field(default_factory=list)
    lsm: float = 0.0
    lsm_verlauf: list[list] = field(default_factory=list)
    # Muster
    lang_kurz: list[int] = field(default_factory=list)

    def als_dict(self) -> dict:
        return {
            "woerter": self.woerter,
            "turns": self.turns,
            "redeanteilT": round(self.redeanteil_t, 4),
            "rueckkanalTurns": self.rueckkanal_turns,
            "medianLaenge": {k: round(v, 1) for k, v in self.median_laenge.items()},
            "p90Laenge": {k: round(v, 1) for k, v in self.p90_laenge.items()},
            "fragenOffen": self.fragen_offen,
            "fragenGeschlossen": self.fragen_geschlossen,
            "fragenGesamt": self.fragen_gesamt,
            "frageBelege": self.frage_belege,
            "aufnahme": round(self.aufnahme, 4),
            "aufnahmeProPaar": self.aufnahme_pro_paar,
            "lsm": round(self.lsm, 4),
            "lsmVerlauf": self.lsm_verlauf,
            "langKurz": self.lang_kurz,
        }


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def ist_rueckkanal(turn: Turn, sprache: str = sprachen.STANDARD) -> bool:
    """„Mhm“, „yeah“, „right“ — Zuhören, kein Redebeitrag.

    Englisch braucht hier eine spürbar längere Liste als Deutsch: „right“,
    „okay“, „sure“, „I see“ und „got it“ sind alle rückkanalfähig, und ein
    englischsprachiger Therapeut, der nur an „mhm“ gemessen wird, sieht
    gesprächiger aus, als er ist.
    """
    pak = sprachen.paket(sprache)
    text = turn.text.strip().lower()
    if len(text.split()) > 4:
        return False
    if any(m.match(text) for m in _muster(pak)["rueckkanal"]):
        return True
    worte = {w.strip(".,!?") for w in text.split()}
    return bool(worte) and worte <= pak.funktion.RUECKKANAL


def _inhaltswoerter(tokens: list[Token], pak) -> set[str]:
    """Lemmata ohne Stoppwörter. Grundlage für lexikalische Aufnahme."""
    stopp = pak.funktion.STOPPWOERTER
    return {
        pak.lemma(t.klein) for t in tokens
        if t.ist_wort and len(t.text) > 2 and t.klein not in stopp
    }


def _funktionsprofil(tokens: list[Token], pak) -> dict[str, float]:
    """Anteil jeder LSM-Kategorie an allen Wörtern des Turns."""
    woerter = [t.klein for t in tokens if t.ist_wort]
    if not woerter:
        return {}
    gesamt = len(woerter)
    return {
        kat: sum(1 for w in woerter if w in menge) / gesamt
        for kat, menge in pak.funktion.LSM_KATEGORIEN.items()
    }


def lsm_paar(a: dict[str, float], b: dict[str, float],
             pak=None) -> float:
    """Language Style Matching für ein Turn-Paar.

    Pro Kategorie 1 - |pA - pB| / (pA + pB + 0.0001), danach gemittelt.
    Der Mittelwert über Kategorien statt über die Gesamtmenge ist wichtig:
    sonst erschlägt die Artikelkategorie alle anderen.

    Beide Sprachpakete führen dieselben neun Kategorienamen, damit diese Zahl
    in einem gemischten Korpus überhaupt in einer Spalte stehen kann. Dass sie
    dort *vergleichbar* wäre, folgt daraus nicht — siehe den Moduldocstring.
    """
    if not a or not b:
        return 0.0
    pak = pak or sprachen.paket(sprachen.STANDARD)
    werte = []
    for kat in pak.funktion.LSM_KATEGORIEN:
        pa, pb = a.get(kat, 0.0), b.get(kat, 0.0)
        werte.append(1.0 - abs(pa - pb) / (pa + pb + 0.0001))
    return sum(werte) / len(werte)


def frage_typ(text: str, sprache: str = sprachen.STANDARD) -> str | None:
    """Gibt „offen“, „geschlossen“ oder None zurück.

    Offen schlägt geschlossen: „Wie war das denn, waren Sie da allein?“ ist in
    der Summe eine offene Frage mit einer Nachfrage dran. Wer sie als
    geschlossen zählt, macht das Profil systematisch schlechter, als es ist.
    Dasselbe gilt für „What was that like — were you on your own?“.
    """
    if "?" not in text:
        return None
    muster = _muster(sprachen.paket(sprache))
    klein = text.lower()
    if any(m.search(klein) for m in muster["frage_offen"]):
        return "offen"
    if any(m.search(klein) for m in muster["frage_geschlossen"]):
        return "geschlossen"
    return "geschlossen"


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------

def analysiere(sitzung: Sitzung) -> Dialogkennzahlen:
    k = Dialogkennzahlen()
    if not sitzung.hat_sprecher:
        return k
    pak = sprachen.paket(getattr(sitzung, "sprache", sprachen.STANDARD))
    code = pak.CODE

    tokens_je_turn: dict[int, list[Token]] = {}
    woerter: Counter = Counter()
    turns: Counter = Counter()
    laengen: dict[str, list[int]] = {THERAPEUT: [], KLIENT: []}

    for turn in sitzung.turns:
        toks = tokenisiere(turn.text, code)
        tokens_je_turn[turn.idx] = toks
        n = sum(1 for t in toks if t.ist_wort)
        if turn.sprecher not in (THERAPEUT, KLIENT):
            continue
        woerter[turn.sprecher] += n
        if ist_rueckkanal(turn, code):
            k.rueckkanal_turns += 1
        else:
            turns[turn.sprecher] += 1
            laengen[turn.sprecher].append(n)

    k.woerter = dict(woerter)
    k.turns = dict(turns)
    gesamt = woerter[THERAPEUT] + woerter[KLIENT]
    k.redeanteil_t = woerter[THERAPEUT] / gesamt if gesamt else 0.0
    k.laengen = laengen
    for sp in (THERAPEUT, KLIENT):
        werte = laengen[sp]
        k.median_laenge[sp] = statistics.median(werte) if werte else 0.0
        k.p90_laenge[sp] = _perzentil(werte, 0.9) if werte else 0.0

    # -- Fragen (nur Therapeutenseite) --------------------------------------
    for turn in sitzung.turns:
        if turn.sprecher != THERAPEUT:
            continue
        for satz in re.split(r"(?<=[?!.])\s+", turn.text):
            typ = frage_typ(satz, code)
            if typ is None:
                continue
            k.fragen_gesamt += 1
            if typ == "offen":
                k.fragen_offen += 1
            else:
                k.fragen_geschlossen += 1
            if len(k.frage_belege) < 400:
                k.frage_belege.append([turn.idx, typ, satz.strip()[:200]])

    # -- Aufnahme und Stilangleichung ---------------------------------------
    paare = _turn_paare(sitzung.turns, code)
    aufnahmen: list[float] = []
    lsm_werte: list[float] = []
    for klient_turn, therapeut_turn in paare:
        k_inhalt = _inhaltswoerter(tokens_je_turn[klient_turn.idx], pak)
        t_inhalt = _inhaltswoerter(tokens_je_turn[therapeut_turn.idx], pak)
        if k_inhalt:
            anteil = len(k_inhalt & t_inhalt) / len(k_inhalt)
            aufnahmen.append(anteil)
            if len(k.aufnahme_pro_paar) < 400:
                k.aufnahme_pro_paar.append(
                    [klient_turn.idx, therapeut_turn.idx, round(anteil, 3),
                     sorted(k_inhalt & t_inhalt)[:8]])
        wert = lsm_paar(_funktionsprofil(tokens_je_turn[klient_turn.idx], pak),
                        _funktionsprofil(tokens_je_turn[therapeut_turn.idx], pak),
                        pak)
        lsm_werte.append(wert)
        k.lsm_verlauf.append([therapeut_turn.idx, round(wert, 3)])

    k.aufnahme = sum(aufnahmen) / len(aufnahmen) if aufnahmen else 0.0
    k.lsm = sum(lsm_werte) / len(lsm_werte) if lsm_werte else 0.0

    # -- Muster: langer Therapeutenbeitrag, kurze Klientenantwort -----------
    if laengen[THERAPEUT] and laengen[KLIENT]:
        t_lang = _perzentil(laengen[THERAPEUT], 0.75)
        k_kurz = _perzentil(laengen[KLIENT], 0.25)
        for a, b in zip(sitzung.turns, sitzung.turns[1:]):
            if (a.sprecher == THERAPEUT and b.sprecher == KLIENT
                    and not ist_rueckkanal(b, code)):
                la = sum(1 for t in tokens_je_turn[a.idx] if t.ist_wort)
                lb = sum(1 for t in tokens_je_turn[b.idx] if t.ist_wort)
                if la >= t_lang and lb <= k_kurz:
                    k.lang_kurz.append(a.idx)

    return k


def _turn_paare(turns: list[Turn],
                sprache: str = sprachen.STANDARD) -> list[tuple[Turn, Turn]]:
    """Paare aus Klientenbeitrag und unmittelbar folgendem Therapeutenbeitrag.

    Rückkanäle werden übersprungen und nicht als Antwort gewertet.
    """
    paare: list[tuple[Turn, Turn]] = []
    for i, turn in enumerate(turns):
        if turn.sprecher != KLIENT or ist_rueckkanal(turn, sprache):
            continue
        for folge in turns[i + 1: i + 4]:
            if folge.sprecher == THERAPEUT and not ist_rueckkanal(folge, sprache):
                paare.append((turn, folge))
                break
            if folge.sprecher == KLIENT:
                break
    return paare


def _perzentil(werte: list[int], p: float) -> float:
    if not werte:
        return 0.0
    geordnet = sorted(werte)
    idx = min(len(geordnet) - 1, max(0, int(round(p * (len(geordnet) - 1)))))
    return float(geordnet[idx])


_BESCHRIFTUNG_BASIS = {
    "redeanteilT": ("Therapist talk ratio", "A",
                    "The therapist’s share of all words. Backchannels (“mhm”) count "
                    "towards the word total but not as turns of their own."),
    "medianLaenge": ("Turn length (median)", "A",
                     "Median rather than mean, because a handful of long turns "
                     "otherwise decide the number on their own."),
    "fragenOffen": ("Open questions", "B",
                    "A wh-question or an explicit invitation. Almost everyone "
                    "believes their questions are open — that is the point."),
    "aufnahme": ("Lexical uptake", "B",
                 "Share of the client’s content words that reappear in the "
                 "therapist’s next turn. Good therapy borrows words instead of "
                 "translating them."),
    "lsm": ("Style matching", "B",
            "Convergence in function-word use. Dips within a session are candidates "
            "for ruptures — candidates, not findings."),
}

# Was sich zwischen den Sprachen an der Beschriftung ändert — und nur das.
# Die Konstrukte sind dieselben; was sich unterscheidet, ist, wie sicher die
# Erkennung ist und woran sie hängt.
_BESCHRIFTUNG_JE_SPRACHE = {
    "en": {
        "fragenOffen": ("Open questions", "B",
                        "A wh-question or an explicit invitation. Almost everyone "
                        "believes their questions are open — that is the point. "
                        "English tag questions (“…, right?”) are counted as closed."),
        "aufnahme": ("Lexical uptake", "B",
                     "Share of the client’s content words that reappear in the "
                     "therapist’s next turn. Good therapy borrows words instead of "
                     "translating them. Not comparable with a German case: the "
                     "stop-word lists differ in size."),
        "lsm": ("Style matching", "B",
                "Convergence in function-word use. This is the measure’s home "
                "language — it was developed on English function words. Dips "
                "within a session are candidates for ruptures, not findings. Not "
                "comparable across languages."),
    },
}


def beschriftung(sprache: str = sprachen.STANDARD) -> dict[str, tuple[str, str, str]]:
    """Dialogbeschriftung in der Sprache der Sitzung."""
    return {**_BESCHRIFTUNG_BASIS, **_BESCHRIFTUNG_JE_SPRACHE.get(sprache, {})}


# Rückwärtskompatibler Name, deutsch — wie in markers.py.
BESCHRIFTUNG = _BESCHRIFTUNG_BASIS
