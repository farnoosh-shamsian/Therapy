"""Sprachpaket Deutsch.

Der Inhalt dieses Moduls stand bis zur Zweisprachigkeit direkt in
``markers.py``. Er ist unverändert hierher gezogen worden, nicht umgeschrieben
— die deutschen Zahlen sollen nach dem Umbau dieselben sein wie vorher, und
die Tests in ``tests/test_marker.py`` prüfen genau das.

Was hier steht, ist deutsche Morphologie: Partizip-II-Bildung, das
werden-Passiv, die Hilfsverb-Tempusheuristik und der Positionsfilter für
Modalpartikeln. Nichts davon hat im englischen Paket ein Gegenstück, das
bloss andere Wörter hätte — das englische Paket macht dieselben Aufgaben mit
anderer Mechanik, und das ist der Grund, warum es zwei Pakete gibt und nicht
eine Funktion mit einer Wortliste als Parameter.
"""

from __future__ import annotations

import re

# ``emotion``, ``funktion`` und ``intervention`` sehen hier ungenutzt aus und
# sind es nicht: sie gehören zum Paketvertrag. dialogue.py, mirror.py,
# threads.py und people.py greifen sie als ``pak.funktion`` usw. ab.
from ..lexika import emotion, funktion, intervention, marker as lex  # noqa: F401
from ..tokenize import ABKUERZUNGEN_DE, lemma_grob

CODE = "de"
NAME = "German"

WORTLISTEN = lex.WORTLISTEN
REGRET_MUSTER = lex.REGRET_MUSTER
NEGATION = lex.NEGATION
NEGATIV_PRAEFIXE = lex.NEGATIV_PRAEFIXE
NEGATIV_SUFFIXE = lex.NEGATIV_SUFFIXE
ABKUERZUNGEN = ABKUERZUNGEN_DE

# Nur das Deutsche schreibt Substantive gross und bildet geschlossene
# Komposita. Beides nutzt ``markers.py`` aus; im englischen Paket stehen die
# Schalter auf False, und die Oberfläche lässt die entsprechenden Blöcke weg,
# statt sie leer anzuzeigen.
KOMPOSITA = True
GROSSSCHREIBUNG_IST_SUBSTANTIV = True

lemma = lemma_grob

# Partizip II ohne "ge-" (untrennbare Präfixe) bzw. mit.
_PARTIZIP2 = re.compile(
    r"\b(?:ge\w{2,}(?:t|en)|(?:be|ver|er|ent|emp|zer|miss)\w{2,}(?:t|en))\b")


# ---------------------------------------------------------------------------
# Fehlalarmfilter
# ---------------------------------------------------------------------------

def wortmarker_ok(name: str, form: str, klein: str, start: int,
                  wort_tokens: list) -> bool:
    """Filtert die offensichtlichsten Fehlalarme aus der Partikelzählung.

    "Ja." als Antwort ist keine Modalpartikel. "Nur" am Satzanfang ist
    Fokuspartikel. Mehr ist ohne Parser nicht drin, und der Rest wird in der
    Oberfläche als bekannte Unschärfe benannt.
    """
    if not name.startswith("partikel_"):
        return True
    if form not in lex.PARTIKEL_POSITION_AUSNAHMEN:
        return True
    idx = next((i for i, t in enumerate(wort_tokens) if t.start == start), None)
    if idx is None:
        return True
    # Erstes Wort im Satz → eher Antwort-/Fokuspartikel als Modalpartikel.
    if idx == 0 or wort_tokens[idx].satz != wort_tokens[idx - 1].satz:
        return False
    return True


def negation_morph_ok(wort: str) -> bool:
    """"unfähig", "wertlos", "sinnlos" — aber nicht "Unterschied", "Losung"."""
    return (len(wort) >= 7
            and (wort.startswith(NEGATIV_PRAEFIXE) or wort.endswith(NEGATIV_SUFFIXE)))


# ---------------------------------------------------------------------------
# Tempus
# ---------------------------------------------------------------------------

def tempus(wort_tokens: list, turn_idx: int, sm) -> None:
    """Grobe Tempuszuordnung pro Satz über Hilfsverben.

    Ein Satz wird höchstens einem Tempus zugeschlagen, Priorität:
    Futur > Perfekt > Präteritum > Präsens. Ohne Partizip zählt "werden"
    nicht als Futur, sonst wird jedes Passiv zur Zukunft.
    """
    nach_satz: dict[int, list] = {}
    for tok in wort_tokens:
        nach_satz.setdefault(tok.satz, []).append(tok)

    for toks in nach_satz.values():
        formen = [t.klein for t in toks]
        anker = toks[0]
        hat_partizip = any(_PARTIZIP2.fullmatch(f) for f in formen)
        hat_infinitiv = any(f.endswith("en") and len(f) > 4 for f in formen)

        if (any(f in lex.FUTUR_HILFSVERB for f in formen)
                and hat_infinitiv and not hat_partizip):
            sm.add("tempus_futur", turn_idx, anker.start, toks[-1].end, "Futur")
        elif any(f in lex.HILFSVERB_PERFEKT for f in formen) and hat_partizip:
            sm.add("tempus_perfekt", turn_idx, anker.start, toks[-1].end, "Perfekt")
        elif any(f in lex.HILFSVERB_PRAETERITUM_SEIN_HABEN for f in formen):
            sm.add("tempus_praeteritum", turn_idx, anker.start, toks[-1].end,
                   "Präteritum")
        else:
            sm.add("tempus_praesens", turn_idx, anker.start, toks[-1].end, "Präsens")


# ---------------------------------------------------------------------------
# Passiv
# ---------------------------------------------------------------------------

def passiv(wort_tokens: list, turn_idx: int, sm, text: str) -> None:
    """werden-Hilfsverb plus Partizip II im selben Satz."""
    for i, tok in enumerate(wort_tokens):
        if tok.klein not in lex.PASSIV_HILFSVERB:
            continue
        for j in range(i + 1, min(len(wort_tokens), i + 9)):
            folgend = wort_tokens[j]
            if folgend.satz != tok.satz:
                break
            if _PARTIZIP2.fullmatch(folgend.klein):
                sm.add("passiv", turn_idx, tok.start, folgend.end,
                       f"{tok.klein} … {folgend.klein}")
                break


# ---------------------------------------------------------------------------
# Abgeleitete Kennzahlen
# ---------------------------------------------------------------------------

def kennzahlen(sm) -> dict[str, float]:
    """Verdichtet die Rohzählungen zu den Zahlen, die in der Oberfläche stehen."""
    z = sm.zaehler
    man, ich = z.get("man", 0), z.get("ich_nom", 0)
    ich_obl = z.get("ich_obl", 0)
    perfekt = z.get("tempus_perfekt", 0)
    praet = z.get("tempus_praeteritum", 0)
    praes = z.get("tempus_praesens", 0)
    futur = z.get("tempus_futur", 0)
    tempus_gesamt = perfekt + praet + praes + futur or 1

    affekt_gesamt = sum(z.get("emo_" + f, 0) for f in emotion.FAMILIEN)
    vage = z.get("emo_vage", 0)
    affekt_alle = affekt_gesamt + vage or 1

    return {
        # Distanzierung
        "man_quote": man / (man + ich) if (man + ich) else 0.0,
        "man_rate": sm.rate("man"),
        "ich_rate": sm.rate("ich_nom"),
        "ich_nominativ_anteil": ich / (ich + ich_obl) if (ich + ich_obl) else 0.0,
        "du_generisch_rate": sm.rate("du_generisch"),
        # Irrealis
        "konjunktiv2_rate": sm.rate("konjunktiv2"),
        "konjunktiv2_ambig_rate": sm.rate("konjunktiv2_ambig"),
        "bedauern_rate": sm.rate("bedauern"),
        "bedauern_anzahl": float(z.get("bedauern", 0)),
        # Partikelprofil
        **{f"partikel_{g}_rate": sm.rate("partikel_" + g)
           for g in lex.PARTIKEL_GRUPPEN},
        # Absolutismus und Zwang
        "absolut1_rate": sm.rate("absolut1"),
        "absolut2_rate": sm.rate("absolut2"),
        "zwang_rate": sm.rate("zwang"),
        # Affekt
        "affekt_rate": 1000.0 * affekt_gesamt / (sm.woerter or 1),
        "vage_rate": sm.rate("emo_vage"),
        "granularitaet": affekt_gesamt / affekt_alle,
        "distinkte_emotionslemmata": float(len(sm.emo_lemmata)),
        "distinkte_pro_1000": 1000.0 * len(sm.emo_lemmata) / (sm.woerter or 1),
        "koerperaffekt_rate": sm.rate("emo_koerper"),
        "affekt_verneint_rate": sm.rate("affekt_verneint"),
        # Zeit
        "tempus_perfekt_anteil": perfekt / tempus_gesamt,
        "tempus_praeteritum_anteil": praet / tempus_gesamt,
        "tempus_praesens_anteil": praes / tempus_gesamt,
        "tempus_futur_anteil": futur / tempus_gesamt,
        "zeit_vergangenheit_rate": sm.rate("zeit_vergangenheit"),
        "zeit_gegenwart_rate": sm.rate("zeit_gegenwart"),
        "zeit_zukunft_rate": sm.rate("zeit_zukunft"),
        # Verarbeitung
        "kausal_rate": sm.rate("kausal"),
        "einsicht_rate": sm.rate("einsicht"),
        "hecken_rate": sm.rate("hecken"),
        "negation_rate": sm.rate("negation"),
        "passiv_rate": sm.rate("passiv"),
        "intensivierer_rate": sm.rate("intensivierer"),
        # Bilder
        "metapher_rate": 1000.0 * sum(sm.metapher_domaenen.values()) / (sm.woerter or 1),
        # Grundgrössen
        "woerter": float(sm.woerter),
        "turns": float(sm.turns),
        "woerter_pro_turn": sm.woerter / sm.turns if sm.turns else 0.0,
    }


# ---------------------------------------------------------------------------
# Beschriftung für die Oberfläche
# ---------------------------------------------------------------------------
#
# (Schlüssel, Anzeigename, Konfidenz, Kurzhinweis). Der Hinweis ist die
# einfache Notiz, was die Zahl tragen kann — er steht an jedem Panel, nicht
# in einer Fussnote.

BESCHRIFTUNG: dict[str, tuple[str, str, str]] = {
    "man_quote": ("“man” instead of “ich”", "A",
                  "Share of “man” among all nominative self-references. German’s "
                  "grammatical escape hatch out of the first person — “man fühlt "
                  "sich dann halt schlecht” instead of “ich fühle mich schlecht”. "
                  "Rises with distancing, falls when experience is claimed. English "
                  "has no equivalent pronoun; in English sessions the same idea is "
                  "measured through generic “you”, one confidence grade lower."),
    "ich_nominativ_anteil": ("Self as subject", "B",
                             "“Ich habe ihm gesagt” versus “mir ist das passiert”: "
                             "self in subject position or self as the one things "
                             "happen to. An agency proxy, approximate without a parser."),
    "konjunktiv2_rate": ("Subjunctive II", "A",
                         "Counterfactual and irrealis thinking, per 1000 words. Only "
                         "unambiguous umlaut forms are counted; “sollte”/“wollte” are "
                         "formally identical to the past tense and counted separately."),
    "bedauern_rate": ("Regret", "A",
                      "“hätte ich nur”, “wenn ich doch”, “hätte … sollen”. Few hits, "
                      "but the densest ones in the whole tool."),
    "partikel_resignativ_rate": ("Particles: resignative", "B",
                                 "“halt”, “eben”, “sowieso”. “Das ist halt so” is "
                                 "resignation in three words — German carries in "
                                 "these particles what English puts in tone of voice."),
    "partikel_insistierend_rate": ("Particles: insistent", "B",
                                   "“doch”, “ja”, “wohl”. Arguing against a position "
                                   "the speaker assumes you hold."),
    "partikel_minimierend_rate": ("Particles: minimising", "B",
                                  "“nur”, “bloß”, “bisschen”. Playing it down."),
    "partikel_abtönend_rate": ("Particles: softening", "B", "General softening."),
    "absolut1_rate": ("Absolutist words", "B",
                      "“immer”, “nie”, “nichts”, “jeder”. Colloquial intensifiers "
                      "(“total”, “voll”, “ganz”) are deliberately excluded — in "
                      "spoken German they are slang, not absolutist thinking. The "
                      "exclusion list is in lexika/marker.py."),
    "absolut2_rate": ("Absolutist words (gradual)", "C",
                      "“völlig”, “absolut”, “gar nicht”. Weaker tier, reported "
                      "separately."),
    "zwang_rate": ("Obligation", "B",
                   "“muss”, “soll”, “darf nicht”. German grammaticalises deontic "
                   "modality far more than English, so it gets its own category "
                   "instead of inflating the absolutist count."),
    "granularitaet": ("Emotional granularity", "A",
                      "Share of named feelings in all affect vocabulary. The move "
                      "from “schlecht” to “gekränkt” is the therapeutic goal itself — "
                      "this measures differentiation, not how much affect there is."),
    "distinkte_pro_1000": ("Distinct feeling words", "A",
                           "How many *different* feeling words per 1000 words, "
                           "regardless of how often each is used."),
    "koerperaffekt_rate": ("Body-located affect", "B",
                           "Stomach, tightness, a lump in the throat. Some people "
                           "speak consistently in the body rather than the feeling — "
                           "its own track, not a deficit."),
    "affekt_rate": ("Affect density", "B",
                    "Named feelings per 1000 words. Says nothing about intensity."),
    "vage_rate": ("Vague affect", "B",
                  "“schlecht”, “komisch”, “irgendwie blöd”. The counterpart to "
                  "granularity."),
    "tempus_perfekt_anteil": ("Past (perfect)", "B",
                              "Rough tense estimate via auxiliaries. Rumination "
                              "lives in the past."),
    "tempus_futur_anteil": ("Future", "B",
                            "Anxiety lives in the future. “werden” without a past "
                            "participle."),
    "kausal_rate": ("Causal words", "A",
                    "“weil”, “deshalb”, “Zusammenhang”. Their increase over a course "
                    "of therapy is one of the better-replicated language findings. "
                    "Adapted from an English instrument."),
    "einsicht_rate": ("Insight words", "A",
                      "“verstehe”, “gemerkt”, “klar geworden”. See causal words."),
    "hecken_rate": ("Hedging and vagueness", "B",
                    "“irgendwie”, “eigentlich”, “keine Ahnung”. Rises under threat, "
                    "near ruptures, and around avoided material."),
    "negation_rate": ("Negation", "B",
                      "Defining the self by what it is not."),
    "passiv_rate": ("Passive voice", "B",
                    "“wurde … gemacht”. Things done to the self. Detected via "
                    "“werden” plus past participle."),
    "metapher_rate": ("Metaphor candidates", "C",
                      "Words from source domains that appear in a sentence with a "
                      "mental referent. Whether they were meant metaphorically is "
                      "not something the tool decides. Useful as a trajectory — "
                      "does an image persist, mutate or disappear — not as a number."),
    "du_generisch_rate": ("Generic “du”", "C",
                          "“Du denkst dann, das geht nie vorbei.” A second form of "
                          "distancing."),
    "intensivierer_rate": ("Intensifiers", "C",
                           "“total”, “voll”, “krass”. Deliberately *not* counted as "
                           "absolutist language."),
    "woerter_pro_turn": ("Words per turn", "A", "Mean turn length."),
}


# Diese Marker tragen den Kompositindex der Arc-Ansicht. Vorzeichen sagt, in
# welche Richtung "mehr" zeigt: +1 = mehr Aneignung/Verarbeitung.
KOMPOSIT_INDEX = {
    "man_quote": -1.0,
    "hecken_rate": -0.7,
    "absolut1_rate": -0.7,
    "passiv_rate": -0.5,
    "vage_rate": -0.7,
    "granularitaet": +1.0,
    "distinkte_pro_1000": +0.8,
    "kausal_rate": +0.8,
    "einsicht_rate": +1.0,
    "ich_nominativ_anteil": +0.5,
}


# Welche Kacheln die Sitzungskarte zeigt, in welcher Reihenfolge, und welche
# Trefferliste ein Klick öffnet. Stand bis zur Zweisprachigkeit in views.js;
# steht jetzt hier, weil die Auswahl eine sprachliche Entscheidung ist und
# keine gestalterische.
#
#   (Kennzahl, Format, Markerschlüssel für die Belegliste)
KACHELN = [
    ("man_quote", "prozent", "man"),
    ("granularitaet", "prozent", "emo_vage"),
    ("hecken_rate", "zahl1", "hecken"),
    ("konjunktiv2_rate", "zahl1", "konjunktiv2"),
    ("bedauern_anzahl", "zahl0", "bedauern"),
    ("absolut1_rate", "zahl1", "absolut1"),
    ("kausal_rate", "zahl1", "kausal"),
    ("einsicht_rate", "zahl1", "einsicht"),
    ("koerperaffekt_rate", "zahl1", "emo_koerper"),
    ("passiv_rate", "zahl1", "passiv"),
]

# Kleine Vielfache in der Arc-Ansicht.
ARC_REIHEN = [
    "man_quote", "granularitaet", "distinkte_pro_1000", "hecken_rate",
    "absolut1_rate", "konjunktiv2_rate", "kausal_rate", "einsicht_rate",
    "koerperaffekt_rate", "passiv_rate", "vage_rate", "zwang_rate",
    "tempus_perfekt_anteil", "tempus_futur_anteil", "metapher_rate",
    "redeanteilT", "aufnahme", "lsm",
]


# Begriff → Schlüssel in dieser Sprache. Siehe die Warnung im Paketdocstring:
# vergleichbar heisst "misst denselben Begriff", nicht "ist dieselbe Zahl".
VERGLEICHBAR = {
    "distanzierung": "man_quote",
    "irrealis": "konjunktiv2_rate",
    "irrealis_ambig": "konjunktiv2_ambig_rate",
}
