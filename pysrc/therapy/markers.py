"""Die Marker — Zählung mit Rückfahrkarte."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import sprachen
from .ingest import KLIENT, THERAPEUT, Sitzung, Turn
from .tokenize import Token, tokenisiere, zerlege_kompositum

# ---------------------------------------------------------------------------
# Abgleichsmaschinerie je Sprache
# ---------------------------------------------------------------------------

_MATCHER_CACHE: dict[str, dict[str, sprachen.Lexikonmatcher]] = {}
_REGRET_CACHE: dict[str, list] = {}


def _matcher(pak) -> dict[str, sprachen.Lexikonmatcher]:
    if pak.CODE not in _MATCHER_CACHE:
        matcher = sprachen.baue_matcher(pak.WORTLISTEN)
        emo = pak.emotion
        matcher["emo_vage"] = sprachen.Lexikonmatcher("emo_vage", emo.VAGER_AFFEKT)
        matcher["emo_koerper"] = sprachen.Lexikonmatcher("emo_koerper",
                                                         emo.KOERPER_AFFEKT)
        for fam, woerter in emo.FAMILIEN.items():
            matcher["emo_" + fam] = sprachen.Lexikonmatcher("emo_" + fam, woerter)
        for dom, woerter in emo.METAPHERN_DOMAENEN.items():
            matcher["met_" + dom] = sprachen.Lexikonmatcher("met_" + dom, woerter)
        _MATCHER_CACHE[pak.CODE] = matcher
    return _MATCHER_CACHE[pak.CODE]


def _regret(pak) -> list:
    if pak.CODE not in _REGRET_CACHE:
        _REGRET_CACHE[pak.CODE] = [(re.compile(muster), name)
                                   for muster, name in pak.REGRET_MUSTER]
    return _REGRET_CACHE[pak.CODE]


# ---------------------------------------------------------------------------
# Ergebnisstrukturen
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Treffer:
    """Ein Markertreffer, adressierbar bis aufs Zeichen."""

    marker: str
    turn: int
    start: int
    end: int
    form: str

    def als_liste(self) -> list:
        # Kompakte Form für die JSON-Brücke:
        return [self.turn, self.start, self.end, self.form]


@dataclass
class SprecherMarker:
    """Alle Marker eines Sprechers in einer Sitzung."""

    sprecher: str
    sprache: str = "de"
    woerter: int = 0
    turns: int = 0
    saetze: int = 0
    zaehler: Counter = field(default_factory=Counter)
    treffer: dict[str, list[Treffer]] = field(default_factory=lambda: defaultdict(list))
    emo_lemmata: Counter = field(default_factory=Counter)
    emo_familien: Counter = field(default_factory=Counter)
    emo_verneint: Counter = field(default_factory=Counter)
    metapher_domaenen: Counter = field(default_factory=Counter)
    komposita: Counter = field(default_factory=Counter)

    def rate(self, schluessel: str) -> float:
        """Treffer pro 1000 Wörter."""
        if not self.woerter:
            return 0.0
        return 1000.0 * self.zaehler.get(schluessel, 0) / self.woerter

    def add(self, marker: str, turn: int, start: int, end: int, form: str) -> None:
        self.zaehler[marker] += 1
        self.treffer[marker].append(Treffer(marker, turn, start, end, form))


# ---------------------------------------------------------------------------
# Hauptanalyse
# ---------------------------------------------------------------------------

def analysiere_sitzung(sitzung: Sitzung, vokabular: set[str] | None = None
                       ) -> dict[str, SprecherMarker]:
    """Zählt alle Marker pro Sprecher."""
    code = getattr(sitzung, "sprache", sprachen.STANDARD)
    pak = sprachen.paket(code)
    ergebnis: dict[str, SprecherMarker] = {
        THERAPEUT: SprecherMarker(THERAPEUT, code),
        KLIENT: SprecherMarker(KLIENT, code),
    }
    for turn in sitzung.turns:
        if turn.sprecher not in ergebnis:
            continue
        _analysiere_turn(turn, ergebnis[turn.sprecher], vokabular, pak)
    return ergebnis


def _analysiere_turn(turn: Turn, sm: SprecherMarker, vokabular: set[str] | None,
                     pak) -> None:
    text = turn.text
    klein = text.lower()
    tokens = tokenisiere(text, pak.CODE)
    wort_tokens = [t for t in tokens if t.ist_wort]
    if not wort_tokens:
        return

    sm.woerter += len(wort_tokens)
    sm.turns += 1
    sm.saetze += (wort_tokens[-1].satz - wort_tokens[0].satz) + 1

    matcher = _matcher(pak)

    # -- 1. Wortlistenmarker ------------------------------------------------
    for name, m in matcher.items():
        if name.startswith("emo_") or name.startswith("met_"):
            continue            # eigene Behandlung weiter unten
        for start, end, form in m.treffer(tokens, klein):
            if not pak.wortmarker_ok(name, form, klein, start, wort_tokens):
                continue
            sm.add(name, turn.idx, start, end, form)

    # -- 2. Bedauern --------------------------------------------------------
    for muster, name in _regret(pak):
        for m in muster.finditer(klein):
            sm.add("bedauern", turn.idx, m.start(), m.end(), name)

    # -- 3. Tempus ----------------------------------------------------------
    pak.tempus(wort_tokens, turn.idx, sm)

    # -- 4. Passiv ----------------------------------------------------------
    pak.passiv(wort_tokens, turn.idx, sm, text)

    # -- 5. Affekt ----------------------------------------------------------
    _affekt(tokens, wort_tokens, klein, turn.idx, sm, vokabular, pak, matcher)

    # -- 6. Metaphern -------------------------------------------------------
    _metaphern(tokens, wort_tokens, klein, turn.idx, sm, pak, matcher)

    # -- 7. Negationsmorphologie -------------------------------------------
    for tok in wort_tokens:
        if pak.negation_morph_ok(tok.klein):
            sm.add("negation_morph", turn.idx, tok.start, tok.end, tok.klein)


# ---------------------------------------------------------------------------
# Teilanalysen
# ---------------------------------------------------------------------------

def _affekt(tokens: list[Token], wort_tokens: list[Token], klein: str,
            turn_idx: int, sm: SprecherMarker, vokabular: set[str] | None,
            pak, matcher) -> None:
    """Emotionsfamilien, vager Affekt, Körperaffekt — plus Kompositazerlegung."""
    emo = pak.emotion
    verneint_positionen = _negationsfenster(wort_tokens, pak)

    def eintragen(marker: str, start: int, end: int, form: str, familie: str | None):
        sm.add(marker, turn_idx, start, end, form)
        if familie:
            verneint = any(s <= start < e for s, e in verneint_positionen)
            if verneint:
                sm.emo_verneint[familie] += 1
                sm.add("affekt_verneint", turn_idx, start, end, form)
            else:
                sm.emo_familien[familie] += 1
                sm.emo_lemmata[pak.lemma(form)] += 1

    for name, m in matcher.items():
        if not name.startswith("emo_"):
            continue
        familie = name[4:] if name not in ("emo_vage", "emo_koerper") else None
        for start, end, form in m.treffer(tokens, klein):
            eintragen(name, start, end, form, familie)

    if not (pak.KOMPOSITA and vokabular):
        return

    # Komposita aufmachen und die Teile noch einmal.
    for tok in wort_tokens:
        # Gross geschrieben und nicht satzinitial:
        if len(tok.text) < 9 or not tok.gross_geschrieben or tok.satz_position == 0:
            continue
        teile = zerlege_kompositum(tok.klein, vokabular)
        if not teile:
            continue
        sm.komposita[tok.klein] += 1
        sm.add("kompositum", turn_idx, tok.start, tok.end, "+".join(teile))
        for teil in teile:
            for familie in emo.WORT_ZU_FAMILIE.get(teil, ()):
                sm.emo_familien[familie] += 1
                sm.emo_lemmata[teil] += 1
                sm.zaehler["emo_" + familie] += 1
            if teil in emo.KOERPER_AFFEKT:
                sm.zaehler["emo_koerper"] += 1


def _negationsfenster(wort_tokens: list[Token], pak) -> list[tuple[int, int]]:
    """Offsetbereiche, die rechts von einer Negation liegen."""
    fenster = pak.emotion.NEGATIONS_FENSTER
    bereiche: list[tuple[int, int]] = []
    for i, tok in enumerate(wort_tokens):
        if tok.klein not in pak.NEGATION:
            continue
        ende = i + fenster
        rechts = wort_tokens[min(ende, len(wort_tokens) - 1)]
        if rechts.satz != tok.satz:
            rechts = next((t for t in reversed(wort_tokens[i:ende + 1])
                           if t.satz == tok.satz), tok)
        bereiche.append((tok.end, rechts.end))
    return bereiche


def _metaphern(tokens: list[Token], wort_tokens: list[Token], klein: str,
               turn_idx: int, sm: SprecherMarker, pak, matcher) -> None:
    """Metaphernkandidaten — Konfidenz C."""
    emo = pak.emotion
    selbstbezug = set(pak.WORTLISTEN.get("ich_nom", ())) | set(
        pak.WORTLISTEN.get("ich_obl", ()))

    mentale_saetze = set()
    for tok in wort_tokens:
        w = tok.klein
        if (w in emo.WORT_ZU_FAMILIE or w in emo.VAGER_AFFEKT
                or w in selbstbezug or w in emo.KOERPER_AFFEKT):
            mentale_saetze.add(tok.satz)
    if not mentale_saetze:
        return

    satz_von_offset = {t.start: t.satz for t in wort_tokens}
    for name, m in matcher.items():
        if not name.startswith("met_"):
            continue
        domaene = name[4:]
        for start, end, form in m.treffer(tokens, klein):
            satz = satz_von_offset.get(start)
            if satz is None or satz not in mentale_saetze:
                continue
            sm.add(name, turn_idx, start, end, form)
            sm.metapher_domaenen[domaene] += 1


# ---------------------------------------------------------------------------
# Abgeleitete Kennzahlen und Beschriftung
# ---------------------------------------------------------------------------

def kennzahlen(sm: SprecherMarker) -> dict[str, float]:
    """Verdichtet Rohzählungen zu Kennzahlen."""
    return sprachen.paket(sm.sprache).kennzahlen(sm)


def beschriftung(sprache: str = sprachen.STANDARD) -> dict[str, tuple[str, str, str]]:
    """(Anzeigename, Konfidenz, Hinweis) je Kennzahl."""
    return sprachen.paket(sprache).BESCHRIFTUNG


def komposit_index(sprache: str = sprachen.STANDARD) -> dict[str, float]:
    """Gewichte des Arc-Index."""
    return sprachen.paket(sprache).KOMPOSIT_INDEX


# Rückwärtskompatible Namen.
BESCHRIFTUNG = sprachen.paket("de").BESCHRIFTUNG
KOMPOSIT_INDEX = sprachen.paket("de").KOMPOSIT_INDEX
