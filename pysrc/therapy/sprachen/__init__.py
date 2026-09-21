"""Sprachpakete — alles Sprachabhängige, und nur das."""

from __future__ import annotations

import re
from collections import Counter

CODES = ("de", "en")
STANDARD = "de"


# ---------------------------------------------------------------------------
# Abgleichsmaschinerie
# ---------------------------------------------------------------------------

class Lexikonmatcher:
    """Gleicht eine Wortliste gegen Tokens ab."""

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
    """Das Sprachpaket zu einem Code."""
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

# Zeichen, die in der einen Sprache vorkommen.
_DE_ZEICHEN = re.compile(r"[äöüÄÖÜß]")
_EN_ZEICHEN = re.compile(r"\b\w+'(s|t|re|ve|ll|d|m)\b", re.I)

_WORT_RE = re.compile(r"[a-zA-ZäöüÄÖÜß]+(?:'[a-z]{1,2})?")

MIN_WOERTER = 25          # darunter ist jede Erkennung geraten
SICHER_AB = 0.60          # Anteilsverhältnis, ab dem wir von "sicher" reden


def erkenne(text: str) -> tuple[str, float, dict]:
    """Rät die Sprache eines Textes."""
    woerter = [w.lower() for w in _WORT_RE.findall(text)]
    n = len(woerter)
    details = {"woerter": n, "de": 0, "en": 0}
    if n < MIN_WOERTER:
        return STANDARD, 0.0, details

    zaehler = Counter(woerter)
    de = sum(anzahl for wort, anzahl in zaehler.items() if wort in _DE_MARKER)
    en = sum(anzahl for wort, anzahl in zaehler.items() if wort in _EN_MARKER)

    # Orthografische Zeugen.
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
    """Sprache eines ganzen Transkripts, plus der Anteil."""
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


# Ab hier gilt die Sitzung als gemischt.
GEMISCHT_AB = 0.15
