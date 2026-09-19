"""Sprachpakete — was an diesem Werkzeug sprachabhängig ist, und nur das.

Thera.py hat als deutsches Werkzeug angefangen. Dass es jetzt auch englische
Sitzungen liest, ist kein Übersetzungsprojekt: die Marker, um die es geht,
sind grammatische und lexikalische Eigenschaften der jeweiligen Sprache, und
eine übersetzte Wortliste wäre eine Messung an der falschen Sprache.

Deshalb dieser Schnitt: **alles, was von der Sprache abhängt, steht in genau
einem Paket pro Sprache** (``de.py``, ``en.py``), und der Rest des Programms
— Konkordanz, Wechselpunkte, Soziogramm, Bericht, Oberfläche — weiss von
Sprache nichts ausser, welches Paket er fragen muss.

Ein Paket ist ein gewöhnliches Modul. Es liefert:

===========================  ================================================
``CODE`` / ``NAME``          "de" / "German"
``WORTLISTEN``               Markerschlüssel → Wortmenge
``REGRET_MUSTER``            (Regex, Anzeigename)
``emotion`` …                die vier Lexikonmodule
``NEGATION`` …               Negationsmengen und -morphologie
``ABKUERZUNGEN``             Punkt danach ist kein Satzende
``KOMPOSITA``                ob Komposita zerlegt werden (nur Deutsch)
``lemma(wort)``              grobe Grundform
``tempus`` / ``passiv``      Teilanalysen mit eigener Morphologie
``wortmarker_ok(…)``         Fehlalarmfilter pro Markerschlüssel
``negation_morph_ok(wort)``  Filter für die Negationsmorphologie
``kennzahlen(sm)``           Rohzählungen → die Zahlen der Oberfläche
``BESCHRIFTUNG``             (Anzeigename, Konfidenz, Hinweis) je Kennzahl
``KOMPOSIT_INDEX``           Gewichte für den Arc-Index
``KACHELN`` / ``ARC_REIHEN`` welche Zahlen die Oberfläche zeigt, in welcher
                             Reihenfolge
``VERGLEICHBAR``             welcher Schlüssel hier welchem Begriff entspricht
===========================  ================================================

**Was ``VERGLEICHBAR`` behauptet und was nicht.** Es sagt, dass der deutsche
Schlüssel ``man_quote`` und der englische ``generisch_quote`` denselben
*Begriff* messen — die grammatische Flucht aus der ersten Person. Es sagt
ausdrücklich **nicht**, dass die Zahlen ineinander umrechenbar sind. Deutsch
hat mit "man" ein eigenes Pronomen, Englisch behilft sich mit generischem
"you"; die Trefferquoten liegen schon deshalb auf verschiedenen Niveaus. Ein
Vergleich der *Verläufe* ist zulässig, ein Vergleich der *Höhen* nicht, und
die Oberfläche sagt das an jeder Stelle, an der beide Sprachen zusammenkommen.
"""

from __future__ import annotations

import re
from collections import Counter

CODES = ("de", "en")
STANDARD = "de"


# ---------------------------------------------------------------------------
# Abgleichsmaschinerie
# ---------------------------------------------------------------------------
#
# Steht hier und nicht in markers.py, weil die Sprachpakete sie brauchen und
# markers.py die Sprachpakete — andersherum gäbe es einen Importzyklus.

class Lexikonmatcher:
    """Gleicht eine Wortliste gegen Tokens (Einzelwörter) und gegen den
    kleingeschriebenen Turn-Text (Mehrwortausdrücke) ab.

    Warum beides: eine reine Tokenprüfung verpasst "auf keinen Fall" und
    "kind of", eine reine Textprüfung verpasst die Wortgrenzen und findet
    "nie" in "niemand" und "one" in "money".
    """

    __slots__ = ("einzeln", "phrasen_re", "name")

    def __init__(self, name: str, eintraege) -> None:
        self.name = name
        self.einzeln = {e for e in eintraege if " " not in e}
        phrasen = sorted((e for e in eintraege if " " in e), key=len, reverse=True)
        self.phrasen_re = (
            re.compile(r"(?<![\w'])(" + "|".join(re.escape(p) for p in phrasen)
                       + r")(?![\w'])")
            if phrasen else None
        )

    def treffer(self, tokens, kleintext: str) -> list[tuple[int, int, str]]:
        gefunden: list[tuple[int, int, str]] = []
        for tok in tokens:
            if tok.ist_wort and tok.klein in self.einzeln:
                gefunden.append((tok.start, tok.end, tok.klein))
        if self.phrasen_re is not None:
            for m in self.phrasen_re.finditer(kleintext):
                gefunden.append((m.start(), m.end(), m.group(1)))
        gefunden.sort()
        return gefunden


def baue_matcher(wortlisten: dict) -> dict[str, Lexikonmatcher]:
    return {name: Lexikonmatcher(name, eintraege)
            for name, eintraege in wortlisten.items()}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_PAKETE: dict[str, object] = {}


def paket(code: str | None):
    """Das Sprachpaket zu einem Code. Unbekanntes fällt auf Deutsch zurück.

    Der Import passiert verzögert, damit ein Paket nur dann in den Speicher
    kommt, wenn es gebraucht wird — im Browser ist das der Unterschied
    zwischen zwei geladenen Lexikonsätzen und einem.
    """
    code = (code or STANDARD).lower()
    if code not in CODES:
        code = STANDARD
    if code not in _PAKETE:
        if code == "en":
            from . import en
            _PAKETE["en"] = en
        else:
            from . import de
            _PAKETE["de"] = de
    return _PAKETE[code]


def name(code: str | None) -> str:
    return {"de": "German", "en": "English"}.get((code or "").lower(), "unknown")


# ---------------------------------------------------------------------------
# Spracherkennung
# ---------------------------------------------------------------------------
#
# Funktionswortprofile, kein Modell, keine Abhängigkeit. Für die Frage
# "Deutsch oder Englisch" ist das nicht die beste verfügbare Methode, aber es
# ist die, die ohne Netzwerkaufruf auskommt — und bei einem ganzen Transkript
# ist sie eindeutig. Bei zwei Sätzen ist sie es nicht, und dann sagt die
# zurückgegebene Sicherheit das auch.
#
# Die Listen sind bewusst kurz und disjunkt: nur Wörter, die in der einen
# Sprache hochfrequent und in der anderen praktisch abwesend sind. "in", "so",
# "war", "man", "die", "will", "hat", "am", "an" stehen deshalb nicht drin,
# obwohl sie deutsch häufig sind — sie sind auch englische Wörter, und ein
# geteiltes Wort trägt nichts bei.

_DE_MARKER = {
    "und", "ich", "nicht", "ist", "das", "der", "dass", "sich", "mit", "auf",
    "eine", "einen", "einem", "für", "aber", "wie", "mir", "mich", "dann",
    "noch", "auch", "habe", "hat", "wenn", "schon", "immer", "sehr", "über",
    "weil", "oder", "wir", "sie", "es", "zu", "von", "bei", "nach", "dem",
    "den", "des", "was", "wer", "wo", "ja", "nein", "halt", "eben", "mal",
    "vielleicht", "eigentlich", "irgendwie", "gefühl", "wieder", "jetzt",
}

_EN_MARKER = {
    "the", "and", "to", "of", "that", "it", "is", "was", "for", "you",
    "with", "but", "not", "have", "just", "my", "me", "about", "really",
    "know", "think", "they", "this", "there", "would", "could", "because",
    "what", "when", "how", "like", "feel", "felt", "don't", "didn't",
    "i'm", "it's", "that's", "something", "anything", "always", "never",
    "much", "very", "been", "were", "are", "him", "her", "them", "yeah",
}

# Zeichen, die in der einen Sprache vorkommen und in der anderen nicht.
_DE_ZEICHEN = re.compile(r"[äöüÄÖÜß]")
_EN_ZEICHEN = re.compile(r"\b\w+'(s|t|re|ve|ll|d|m)\b", re.I)

_WORT_RE = re.compile(r"[a-zA-ZäöüÄÖÜß]+(?:'[a-z]{1,2})?")

MIN_WOERTER = 25          # darunter ist jede Erkennung geraten
SICHER_AB = 0.60          # Anteilsverhältnis, ab dem wir von "sicher" reden


def erkenne(text: str) -> tuple[str, float, dict]:
    """Rät die Sprache eines Textes.

    Gibt ``(code, sicherheit, details)`` zurück. ``sicherheit`` liegt
    zwischen 0 und 1 und ist die relative Dominanz der Gewinnersprache —
    nicht eine Wahrscheinlichkeit im statistischen Sinn, sondern eine Zahl,
    die die Oberfläche in eine Warnung übersetzen kann.

    Bei zu wenig Material wird nicht geraten: der Rückgabewert ist dann die
    Standardsprache mit Sicherheit 0, und ``ingest.py`` macht daraus eine
    sichtbare Warnung im Befund statt einer stillen Annahme.
    """
    woerter = [w.lower() for w in _WORT_RE.findall(text)]
    n = len(woerter)
    details = {"woerter": n, "de": 0, "en": 0}
    if n < MIN_WOERTER:
        return STANDARD, 0.0, details

    zaehler = Counter(woerter)
    de = sum(anzahl for wort, anzahl in zaehler.items() if wort in _DE_MARKER)
    en = sum(anzahl for wort, anzahl in zaehler.items() if wort in _EN_MARKER)

    # Orthografische Zeugen. Umlaute gibt es im Englischen nicht, und
    # Kontraktionen mit Apostroph gibt es im Deutschen praktisch nicht.
    # Beide Signale sind schwächer gewichtet als die Wortlisten, weil ein
    # einzelner Eigenname beide auslösen kann.
    de += 2 * len(_DE_ZEICHEN.findall(text))
    en += 2 * len(_EN_ZEICHEN.findall(text))

    details["de"], details["en"] = de, en
    gesamt = de + en
    if not gesamt:
        return STANDARD, 0.0, details
    if de >= en:
        return "de", (de - en) / gesamt, details
    return "en", (en - de) / gesamt, details


def erkenne_je_turn(texte: list[str]) -> tuple[str, float, dict]:
    """Sprache eines ganzen Transkripts, plus der Anteil der Minderheitssprache.

    Zweisprachige Sitzungen kommen vor — ein Klient, der ein Zitat oder einen
    Fachbegriff in der anderen Sprache bringt, oder eine Stunde, die
    tatsächlich zwischen den Sprachen wechselt. Der erste Fall ist harmlos,
    der zweite macht jede Rate kaputt, und die beiden lassen sich am Anteil
    unterscheiden. Deshalb wird nicht nur über den Volltext entschieden,
    sondern auch gezählt, wie viele *Beiträge* der Minderheit zufallen.

    Beiträge unter :data:`MIN_WOERTER` Wörtern zählen dabei nicht mit: "Mhm"
    ist in beiden Sprachen "Mhm", und eine Sitzung aus kurzen Turns würde
    sonst als wild gemischt erscheinen.
    """
    volltext = "\n".join(texte)
    code, sicherheit, details = erkenne(volltext)

    stimmen: Counter = Counter()
    for text in texte:
        turn_code, turn_sicher, turn_details = erkenne(text)
        if turn_details["woerter"] >= MIN_WOERTER and turn_sicher >= 0.2:
            stimmen[turn_code] += 1

    bewertet = sum(stimmen.values())
    anteil_fremd = (bewertet - stimmen.get(code, 0)) / bewertet if bewertet else 0.0
    details["bewerteteTurns"] = bewertet
    details["anteilFremdsprache"] = round(anteil_fremd, 3)
    return code, sicherheit, details


# ---------------------------------------------------------------------------
# Beschriftung der sprachübergreifenden Reihen
# ---------------------------------------------------------------------------
#
# ``arc.reihen`` legt für jeden Begriff aus VERGLEICHBAR zusätzlich eine
# Reihe ``vgl_<begriff>`` an, die auch dann durchgeht, wenn ein Klient
# mitten in der Fallgeschichte die Sprache wechselt. Diese Reihen sind die
# einzige Stelle im ganzen Werkzeug, an der Zahlen aus zwei Sprachen in einer
# Kurve stehen — entsprechend steht der Vorbehalt direkt an der Beschriftung
# und nicht in einer Fussnote.

VERGLEICHBAR_BESCHRIFTUNG: dict[str, tuple[str, str, str]] = {
    "vgl_distanzierung": (
        "Distancing from the first person (across languages)", "C",
        "German counts “man”, English counts generic “you”. They are the same "
        "move away from “I” and they are not the same number — German has a "
        "dedicated pronoun for it and English does not, so the English stretch "
        "of this line sits at a different level for reasons that have nothing "
        "to do with the client. Read the shape within each stretch; do not read "
        "the step at the language change."),
    "vgl_irrealis": (
        "Counterfactual thinking (across languages)", "C",
        "German counts Subjunctive II, English counts “would have”, “if I "
        "were”, “I wish”. Same construct, different machinery, different hit "
        "rates. Same caveat as above."),
    "vgl_irrealis_ambig": (
        "Counterfactual, ambiguous forms (across languages)", "C",
        "The forms that are formally identical to something else in each "
        "language. Reported for completeness."),
}


# Ab diesem Anteil fremdsprachiger Beiträge ist eine Sitzung gemischt und
# nicht mehr "eine Sitzung mit einem Zitat drin". Der Wert ist gesetzt, nicht
# hergeleitet: unterhalb davon verschiebt eine fremdsprachige Passage die
# Raten um weniger, als die Sitzung-zu-Sitzung-Streuung ohnehin beträgt.
GEMISCHT_AB = 0.15
