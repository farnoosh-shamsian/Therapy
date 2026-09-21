"""Tokenisierung, Sätze, grobe Lemmata, Komposita."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Zeichenklassen
# ---------------------------------------------------------------------------

UMLAUTE = "äöüÄÖÜß"
_WORT_INNEN = r"[A-Za-zÄÖÜäöüß0-9]"

# Ein Token ist:
_TOKEN_RE = re.compile(
    r"""
      (?P<wort>[A-Za-zÄÖÜäöüß](?:[A-Za-zÄÖÜäöüß0-9]|['’’-](?=[A-Za-zÄÖÜäöüß]))*)
    | (?P<zahl>\d+(?:[.,:]\d+)*)
    | (?P<zeichen>[^\sA-Za-zÄÖÜäöüß0-9])
    """,
    re.VERBOSE,
)

# Abkürzungen, nach denen ein Punkt kein Satzende.
ABKUERZUNGEN_DE = {
    "z.b", "d.h", "u.a", "bzw", "usw", "etc", "ca", "evtl", "ggf", "vgl",
    "bspw", "inkl", "max", "min", "ggfs", "nr", "abs", "art", "hr", "fr",
    "dr", "prof", "dipl", "med", "phil", "sog", "ua", "zb", "dh", "o.k",
    "mo", "di", "mi", "do", "fr", "sa", "so", "jan", "feb", "mär", "apr",
    "jun", "jul", "aug", "sep", "okt", "nov", "dez", "st", "bzgl",
}

ABKUERZUNGEN_EN = {
    "e.g", "i.e", "etc", "vs", "cf", "approx", "est", "no", "mr", "mrs",
    "ms", "dr", "prof", "rev", "st", "jr", "sr", "hon", "gen", "sgt",
    "mon", "tue", "tues", "wed", "thu", "thur", "thurs", "fri", "sat", "sun",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct",
    "nov", "dec", "am", "pm", "a.m", "p.m", "u.s", "u.k", "ph.d", "b.c",
}

# Rückwärtskompatibler Name.
ABKUERZUNGEN = ABKUERZUNGEN_DE

_ABKUERZUNGEN_JE_SPRACHE = {"de": ABKUERZUNGEN_DE, "en": ABKUERZUNGEN_EN}

_SATZ_ENDE_RE = re.compile(r"[.!?…]+[\"»«')\]]*\s")


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Token:
    """Ein Token mit Herkunftsadresse."""

    text: str
    start: int
    end: int
    art: str            # "wort" | "zahl" | "zeichen"
    satz: int = 0       # Satzindex innerhalb des Turns
    satz_position: int = 0   # Position im Satz; 0 = satzinitial

    @property
    def klein(self) -> str:
        return self.text.lower()

    @property
    def ist_wort(self) -> bool:
        return self.art == "wort"

    @property
    def gross_geschrieben(self) -> bool:
        return bool(self.text) and self.text[0].isupper()


# ---------------------------------------------------------------------------
# Normalisierung
# ---------------------------------------------------------------------------

_ERSETZUNGEN = {
    " ": " ", " ": " ", " ": " ",
    "‘": "'", "’": "'", "‚": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "–": "-", "—": "-", "−": "-",
    "…": "...",
}


def normalisiere(text: str) -> str:
    """Vereinheitlicht Unicode-Varianten, **ohne** die Textlänge zu ändern,"""
    text = unicodedata.normalize("NFC", text)
    for alt, neu in _ERSETZUNGEN.items():
        if alt in text:
            text = text.replace(alt, neu)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def entferne_diakritika(wort: str) -> str:
    """ä→a, ö→o, ü→u, ß→ss."""
    tabelle = {"ä": "a", "ö": "o", "ü": "u", "ß": "ss",
               "Ä": "A", "Ö": "O", "Ü": "U"}
    return "".join(tabelle.get(c, c) for c in wort)


def umlaut_rueck(wort: str) -> str:
    """Umlautrücknahme für die Lemmatisierung: Bäume→Baume→Baum, Häuser→Hauser."""
    return (wort.replace("äu", "au").replace("ä", "a")
                .replace("ö", "o").replace("ü", "u"))


# ---------------------------------------------------------------------------
# Tokenisierung
# ---------------------------------------------------------------------------

def tokenisiere(text: str, sprache: str = "de") -> list[Token]:
    """Zerlegt Text in Tokens mit Offsets."""
    tokens: list[Token] = []
    for m in _TOKEN_RE.finditer(text):
        art = m.lastgroup or "zeichen"
        tokens.append(Token(m.group(), m.start(), m.end(), art))
    _setze_satzindex(text, tokens, sprache)
    return tokens


def _setze_satzindex(text: str, tokens: list[Token], sprache: str = "de") -> None:
    abkuerzungen = _ABKUERZUNGEN_JE_SPRACHE.get(sprache, ABKUERZUNGEN_DE)
    satz = 0
    position = 0
    for i, tok in enumerate(tokens):
        tok.satz = satz
        # Nur Wörter und Zahlen zählen als Position:
        tok.satz_position = position
        if tok.art != "zeichen":
            position += 1
        if tok.art != "zeichen" or tok.text not in ".!?…":
            continue
        # Punkt nach bekannter Abkürzung beendet keinen Satz.
        if tok.text == "." and i > 0:
            vor = tokens[i - 1].text.lower()
            if vor in abkuerzungen or (len(vor) == 1 and vor.isalpha()):
                continue
        # Punkt als Teil einer Zahl ("3.
        if tok.text == "." and i > 0 and tokens[i - 1].art == "zahl":
            continue
        # Folgt kleingeschriebenes Wort, war es vermutlich kein.
        nach = next((t for t in tokens[i + 1:] if t.art != "zeichen"), None)
        if nach is not None and nach.art == "wort" and nach.text[0].islower():
            continue
        satz += 1
        position = 0


def saetze(text: str, tokens: list[Token] | None = None,
           sprache: str = "de") -> list[tuple[int, int]]:
    """Gibt Satzgrenzen als (start, end)-Offsetpaare zurück."""
    tokens = tokens if tokens is not None else tokenisiere(text, sprache)
    if not tokens:
        return []
    grenzen: list[tuple[int, int]] = []
    aktuell = tokens[0].satz
    start = tokens[0].start
    ende = tokens[0].end
    for tok in tokens:
        if tok.satz != aktuell:
            grenzen.append((start, ende))
            aktuell, start = tok.satz, tok.start
        ende = tok.end
    grenzen.append((start, ende))
    return grenzen


def woerter(tokens: list[Token]) -> list[Token]:
    return [t for t in tokens if t.ist_wort]


def kleintext(tokens: list[Token]) -> list[str]:
    return [t.klein for t in tokens if t.ist_wort]


# ---------------------------------------------------------------------------
# Grobe Lemmatisierung
# ---------------------------------------------------------------------------

_IRREGULAER = {
    # sein
    "bin": "sein", "bist": "sein", "ist": "sein", "sind": "sein", "seid": "sein",
    "war": "sein", "warst": "sein", "waren": "sein", "wart": "sein",
    "gewesen": "sein", "wäre": "sein", "wären": "sein", "sei": "sein",
    # haben
    "habe": "haben", "hab": "haben", "hast": "haben", "hat": "haben",
    "habt": "haben", "hatte": "haben", "hattest": "haben", "hatten": "haben",
    "hattet": "haben", "gehabt": "haben", "hätte": "haben", "hätten": "haben",
    # werden
    "werde": "werden", "wirst": "werden", "wird": "werden", "werdet": "werden",
    "wurde": "werden", "wurden": "werden", "worden": "werden",
    "würde": "werden", "würden": "werden", "geworden": "werden",
    # Modalverben
    "kann": "können", "kannst": "können", "könnt": "können",
    "konnte": "können", "konnten": "können", "könnte": "können",
    "könnten": "können", "gekonnt": "können",
    "muss": "müssen", "musst": "müssen", "müsst": "müssen",
    "musste": "müssen", "mussten": "müssen", "müsste": "müssen",
    "müssten": "müssen", "gemusst": "müssen",
    "soll": "sollen", "sollst": "sollen", "sollt": "sollen",
    "sollte": "sollen", "sollten": "sollen",
    "darf": "dürfen", "darfst": "dürfen", "durfte": "dürfen",
    "dürfte": "dürfen", "dürften": "dürfen",
    "will": "wollen", "willst": "wollen", "wollt": "wollen",
    "wollte": "wollen", "wollten": "wollen",
    "mag": "mögen", "magst": "mögen", "mochte": "mögen",
    "möchte": "mögen", "möchten": "mögen",
    # häufige starke Verben
    "ging": "gehen", "gingen": "gehen", "gegangen": "gehen", "geht": "gehen",
    "kam": "kommen", "kamen": "kommen", "gekommen": "kommen", "kommt": "kommen",
    "gab": "geben", "gaben": "geben", "gegeben": "geben", "gibt": "geben",
    "nahm": "nehmen", "nahmen": "nehmen", "genommen": "nehmen", "nimmt": "nehmen",
    "sah": "sehen", "sahen": "sehen", "gesehen": "sehen", "sieht": "sehen",
    "sprach": "sprechen", "gesprochen": "sprechen", "spricht": "sprechen",
    "dachte": "denken", "dachten": "denken", "gedacht": "denken",
    "wusste": "wissen", "wussten": "wissen", "gewusst": "wissen",
    "weiss": "wissen", "weiß": "wissen", "weisst": "wissen", "weißt": "wissen",
    "fand": "finden", "fanden": "finden", "gefunden": "finden",
    "blieb": "bleiben", "blieben": "bleiben", "geblieben": "bleiben",
    "hielt": "halten", "hielten": "halten", "gehalten": "halten", "hält": "halten",
    "liess": "lassen", "ließ": "lassen", "gelassen": "lassen", "lässt": "lassen",
    "tat": "tun", "taten": "tun", "getan": "tun", "tut": "tun",
    "las": "lesen", "gelesen": "lesen", "liest": "lesen",
    "fuhr": "fahren", "gefahren": "fahren", "fährt": "fahren",
    "lief": "laufen", "gelaufen": "laufen", "läuft": "laufen",
    "trug": "tragen", "getragen": "tragen", "trägt": "tragen",
    "schrieb": "schreiben", "geschrieben": "schreiben",
    "verlor": "verlieren", "verloren": "verlieren",
    "stand": "stehen", "standen": "stehen", "gestanden": "stehen", "steht": "stehen",
    "saß": "sitzen", "sass": "sitzen", "gesessen": "sitzen", "sitzt": "sitzen",
    "lag": "liegen", "lagen": "liegen", "gelegen": "liegen", "liegt": "liegen",
    "brachte": "bringen", "gebracht": "bringen", "bringt": "bringen",
    "fiel": "fallen", "gefallen": "fallen", "fällt": "fallen",
    "hieß": "heissen", "heiss": "heissen", "heißt": "heissen",
    "aß": "essen", "gegessen": "essen", "isst": "essen",
    "half": "helfen", "geholfen": "helfen", "hilft": "helfen",
    "nannte": "nennen", "genannt": "nennen", "nennt": "nennen",
    "erkannte": "erkennen", "erkannt": "erkennen",
    "verstand": "verstehen", "verstanden": "verstehen", "versteht": "verstehen",
    # Pronomen und Artikel auf eine Grundform
    "mir": "ich", "mich": "ich", "meiner": "mein", "meine": "mein",
    "meinem": "mein", "meinen": "mein", "meines": "mein",
    "dir": "du", "dich": "du", "ihm": "er", "ihn": "er",
    "uns": "wir", "euch": "ihr",
    "der": "der", "die": "der", "das": "der", "den": "der", "dem": "der",
    "des": "der", "ein": "ein", "eine": "ein", "einen": "ein", "einem": "ein",
    "einer": "ein", "eines": "ein",
}

# Reihenfolge ist Priorität. (suffix, ersatz, mindestlaenge_des_stamms)
_SUFFIXREGELN: list[tuple[str, str, int]] = [
    ("innen", "", 4),        # Kolleginnen -> Kolleg(e)
    ("ungen", "ung", 3),     # Erfahrungen -> Erfahrung
    ("heiten", "heit", 3),
    ("keiten", "keit", 3),
    ("lichen", "lich", 3),
    ("schaften", "schaft", 3),
    ("enden", "en", 3),
    ("ende", "en", 3),
    ("test", "en", 3),
    ("etest", "en", 3),
    ("erin", "er", 3),
    ("nisse", "nis", 3),
    ("eren", "ern", 3),
    ("iert", "ieren", 3),
    ("ierte", "ieren", 3),
    ("ierten", "ieren", 3),
    ("est", "en", 3),
    ("ern", "er", 3),
    ("em", "", 4),
    ("en", "", 3),
    ("er", "", 4),
    ("es", "", 4),
    ("et", "en", 3),
    ("st", "en", 3),
    ("te", "en", 3),
    ("ten", "en", 3),
    ("s", "", 4),
    ("n", "", 4),
    ("e", "", 4),
]

_PARTIZIP_RE = re.compile(r"^ge(.{3,})(t|en)$")

_lemma_cache: dict[str, str] = {}


def lemma_grob(wort: str) -> str:
    """Grobe Grundform. Deterministisch, verlustbehaftet, gecacht."""
    if wort in _lemma_cache:
        return _lemma_cache[wort]
    roh = wort
    w = wort.lower().strip("'-")
    ergebnis = w

    if not w or not w[0].isalpha():
        ergebnis = w
    elif w in _IRREGULAER:
        ergebnis = _IRREGULAER[w]
    elif len(w) <= 3:
        ergebnis = w
    else:
        # Partizip II:
        m = _PARTIZIP_RE.match(w)
        kandidat = w
        if m:
            stamm = m.group(1)
            kandidat = stamm + ("n" if stamm.endswith(("er", "el")) else "en")
        else:
            for suffix, ersatz, minlen in _SUFFIXREGELN:
                if kandidat.endswith(suffix) and len(kandidat) - len(suffix) >= minlen:
                    kandidat = kandidat[: -len(suffix)] + ersatz
                    break
        # Keine Umlautrücknahme an dieser Stelle.
        ergebnis = kandidat

    _lemma_cache[roh] = ergebnis
    return ergebnis


# ---------------------------------------------------------------------------
# Grobe Lemmatisierung, englisch
# ---------------------------------------------------------------------------

_IRREGULAER_EN = {
    # sein / haben / tun
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be",
    "been": "be", "being": "be", "i'm": "i", "you're": "you", "he's": "he",
    "she's": "she", "it's": "it", "we're": "we", "they're": "they",
    "has": "have", "had": "have", "having": "have", "i've": "i",
    "you've": "you", "we've": "we", "they've": "they",
    "does": "do", "did": "do", "done": "do", "doing": "do",
    # Modalverben auf eine Grundform
    "can": "can", "could": "can", "will": "will", "would": "will",
    "shall": "shall", "should": "shall", "may": "may", "might": "may",
    # häufige starke Verben
    "went": "go", "gone": "go", "goes": "go", "going": "go",
    "said": "say", "says": "say", "saying": "say",
    "got": "get", "gotten": "get", "gets": "get", "getting": "get",
    "made": "make", "makes": "make", "making": "make",
    "knew": "know", "known": "know", "knows": "know", "knowing": "know",
    "thought": "think", "thinks": "think", "thinking": "think",
    "took": "take", "taken": "take", "takes": "take", "taking": "take",
    "saw": "see", "seen": "see", "sees": "see", "seeing": "see",
    "came": "come", "comes": "come", "coming": "come",
    "gave": "give", "given": "give", "gives": "give", "giving": "give",
    "told": "tell", "tells": "tell", "telling": "tell",
    "felt": "feel", "feels": "feel", "feeling": "feel", "feelings": "feel",
    "became": "become", "becomes": "become", "becoming": "become",
    "left": "leave", "leaves": "leave", "leaving": "leave",
    "put": "put", "puts": "put", "putting": "put",
    "meant": "mean", "means": "mean", "meaning": "mean",
    "kept": "keep", "keeps": "keep", "keeping": "keep",
    "began": "begin", "begun": "begin", "begins": "begin",
    "heard": "hear", "hears": "hear", "hearing": "hear",
    "ran": "run", "runs": "run", "running": "run",
    "held": "hold", "holds": "hold", "holding": "hold",
    "brought": "bring", "brings": "bring", "bringing": "bring",
    "wrote": "write", "written": "write", "writes": "write",
    "sat": "sit", "sits": "sit", "sitting": "sit",
    "stood": "stand", "stands": "stand", "standing": "stand",
    "lost": "lose", "loses": "lose", "losing": "lose",
    "paid": "pay", "pays": "pay", "paying": "pay",
    "met": "meet", "meets": "meet", "meeting": "meet",
    "spoke": "speak", "spoken": "speak", "speaks": "speak",
    "lay": "lie", "lain": "lie", "lies": "lie", "lying": "lie",
    "led": "lead", "leads": "lead", "leading": "lead",
    "understood": "understand", "understands": "understand",
    "found": "find", "finds": "find", "finding": "find",
    "caught": "catch", "catches": "catch", "catching": "catch",
    "fell": "fall", "fallen": "fall", "falls": "fall", "falling": "fall",
    "broke": "break", "broken": "break", "breaks": "break",
    "chose": "choose", "chosen": "choose", "chooses": "choose",
    "forgot": "forget", "forgotten": "forget", "forgets": "forget",
    "grew": "grow", "grown": "grow", "grows": "grow",
    "drove": "drive", "driven": "drive", "drives": "drive",
    "ate": "eat", "eaten": "eat", "eats": "eat",
    "woke": "wake", "woken": "wake", "wakes": "wake",
    "hurt": "hurt", "hurts": "hurt", "hurting": "hurt",
    "let": "let", "lets": "let", "letting": "let",
    "built": "build", "builds": "build", "building": "build",
    "dealt": "deal", "deals": "deal", "dealing": "deal",
    "sent": "send", "sends": "send", "sending": "send",
    "spent": "spend", "spends": "spend", "spending": "spend",
    "sold": "sell", "sells": "sell", "selling": "sell",
    "torn": "tear", "tore": "tear", "tears": "tear",
    # unregelmässige Plurale
    "people": "people", "children": "child", "men": "man", "women": "woman",
    "feet": "foot", "teeth": "tooth", "lives": "life", "wives": "wife",
    "selves": "self", "knives": "knife",
    # Pronomen auf eine Grundform
    "me": "i", "my": "i", "mine": "i", "myself": "i",
    "him": "he", "his": "he", "himself": "he",
    "her": "she", "hers": "she", "herself": "she",
    "us": "we", "our": "we", "ours": "we", "ourselves": "we",
    "them": "they", "their": "they", "theirs": "they", "themselves": "they",
    "your": "you", "yours": "you", "yourself": "you",
    "an": "a", "the": "the",
}

# Stammendungen, nach denen ein stummes "e" zurückgeholt.
_STUMMES_E = ("c", "v", "z", "u")

_DOPPELBAR = "bdfglmnprtz"

_lemma_cache_en: dict[str, str] = {}


def lemma_grob_en(wort: str) -> str:
    """Grobe englische Grundform. Deterministisch, verlustbehaftet, gecacht."""
    if wort in _lemma_cache_en:
        return _lemma_cache_en[wort]
    roh = wort
    w = wort.lower().strip("'-")
    ergebnis = w

    if not w or not w[0].isalpha():
        ergebnis = w
    elif w in _IRREGULAER_EN:
        ergebnis = _IRREGULAER_EN[w]
    elif w.endswith("n't"):
        # "don't" → "do", "wasn't" → "be".
        ergebnis = lemma_grob_en(w[:-3]) if len(w) > 4 else w
    elif "'" in w:
        # "i'd", "she'll"
        ergebnis = lemma_grob_en(w.split("'", 1)[0]) or w
    elif len(w) <= 3:
        ergebnis = w
    else:
        ergebnis = _englische_suffixe(w)

    _lemma_cache_en[roh] = ergebnis
    return ergebnis


def _englische_suffixe(w: str) -> str:
    # Plural und 3. Person Singular
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("sses", "shes", "ches", "xes", "zes")) and len(w) > 5:
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is")) and len(w) > 3:
        return w[:-1]

    # Partizip / Präteritum und Gerundium
    for suffix in ("ing", "ed"):
        if not w.endswith(suffix) or len(w) - len(suffix) < 3:
            continue
        stamm = w[: -len(suffix)]
        if suffix == "ed" and stamm.endswith("i"):
            return stamm[:-1] + "y"          # "tried" → "try"
        # Verdoppelter Endkonsonant zurücknehmen: "running" → "run"
        if (len(stamm) > 3 and stamm[-1] == stamm[-2]
                and stamm[-1] in _DOPPELBAR):
            stamm = stamm[:-1]
        elif stamm.endswith(_STUMMES_E):
            stamm += "e"                     # "noticing" → "notice"
        return stamm

    # Adverbien auf -ly bleiben stehen:
    return w


# ---------------------------------------------------------------------------
# Kompositazerlegung
# ---------------------------------------------------------------------------

FUGEN = ("s", "es", "n", "en", "er", "e", "")
MIN_TEIL = 4


def zerlege_kompositum(
    wort: str,
    vokabular: set[str],
    min_gesamt: int = 9,
) -> list[str] | None:
    """Zerlegt ein Kompositum in zwei bis drei."""
    w = wort.lower()
    if len(w) < min_gesamt or not w.isalpha():
        return None
    bestes: list[str] | None = None
    # Von rechts: der längste bekannte Rechtskopf gewinnt.
    for schnitt in range(MIN_TEIL, len(w) - MIN_TEIL + 1):
        links_roh, rechts = w[:schnitt], w[schnitt:]
        if len(rechts) < MIN_TEIL or rechts not in vokabular:
            continue
        for fuge in FUGEN:
            if fuge and not links_roh.endswith(fuge):
                continue
            links = links_roh[: len(links_roh) - len(fuge)] if fuge else links_roh
            if len(links) < MIN_TEIL:
                continue
            if links in vokabular or umlaut_rueck(links) in vokabular:
                kandidat = [links, rechts]
                # Dreiteilige Komposita: linken Teil noch einmal versuchen.
                tiefer = zerlege_kompositum(links, vokabular, min_gesamt)
                if tiefer:
                    kandidat = tiefer + [rechts]
                if bestes is None or len(kandidat) > len(bestes):
                    bestes = kandidat
                break
        if bestes:
            break
    return bestes


def typ_token_verhaeltnis(formen: list[str], fenster: int = 100) -> float:
    """Standardisiertes Type-Token-Verhältnis (STTR)."""
    if not formen:
        return 0.0
    if len(formen) < fenster:
        return len(set(formen)) / len(formen)
    werte = []
    for i in range(0, len(formen) - fenster + 1, fenster):
        stueck = formen[i: i + fenster]
        werte.append(len(set(stueck)) / fenster)
    return sum(werte) / len(werte) if werte else 0.0
