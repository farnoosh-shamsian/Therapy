"""Sprachpaket Englisch."""

from __future__ import annotations

import re

# ``emotion`` und ``funktion`` sehen hier ungenutzt aus.
from ..lexika_en import dialogmuster, emotion, funktion, marker as lex  # noqa: F401
from ..tokenize import ABKUERZUNGEN_EN, lemma_grob_en

CODE = "en"
NAME = "English"

WORTLISTEN = lex.WORTLISTEN
REGRET_MUSTER = lex.REGRET_MUSTER
NEGATION = lex.NEGATION
NEGATIV_PRAEFIXE = lex.NEGATIV_PRAEFIXE
NEGATIV_SUFFIXE = lex.NEGATIV_SUFFIXE
ABKUERZUNGEN = ABKUERZUNGEN_EN

# Siehe Punkt 2 im Moduldocstring.
KOMPOSITA = False
# Grossschreibung mitten im Satz ist im Englischen.
GROSSSCHREIBUNG_IST_SUBSTANTIV = False

lemma = lemma_grob_en

# Partizip II:
_PARTIZIP_ED = re.compile(r"^[a-z]{3,}ed$")


def _ist_partizip(form: str) -> bool:
    return form in lex.PARTIZIP_UNREGELMAESSIG or bool(_PARTIZIP_ED.match(form))


# ---------------------------------------------------------------------------
# Fehlalarmfilter
# ---------------------------------------------------------------------------

# Fenster links und rechts vom Treffer.
_UMFELD = 16

_SATZENDE = re.compile(r"[.!?]")


def _in_frage(klein: str, start: int) -> bool:
    """Steht der Treffer in einem Fragesatz?"""
    treffer = _SATZENDE.search(klein, start)
    return bool(treffer) and treffer.group() == "?"


def wortmarker_ok(name: str, form: str, klein: str, start: int,
                  wort_tokens: list) -> bool:
    """Fehlalarmfilter pro Markerschlüssel."""

    # -- generisches "you" --------------------------------------------------
    if name == "generisch":
        if form in lex.GENERISCH_AUSGESCHLOSSEN:
            return False
        if form != "you":
            return True                      # "one", "people", "everybody"
        if _in_frage(klein, start):
            return False
        umfeld = klein[max(0, start - _UMFELD): start + _UMFELD]
        if any(formel in umfeld for formel in lex.GENERISCH_AUSNAHMEN):
            return False
        return True

    # -- Abtönung ----------------------------------------------------------
    if name.startswith("partikel_"):
        if form not in lex.PARTIKEL_POSITION_AUSNAHMEN:
            return True
        idx = next((i for i, t in enumerate(wort_tokens) if t.start == start), None)
        if idx is None:
            return True
        if idx == 0 or wort_tokens[idx].satz != wort_tokens[idx - 1].satz:
            return False
        return True

    return True


def negation_morph_ok(wort: str) -> bool:
    """"unable", "worthless", "disconnected" — aber nicht "understand"."""
    if len(wort) < 6:
        return False
    if wort in lex.NEGATIV_MORPH_AUSNAHMEN:
        return False
    return wort.startswith(NEGATIV_PRAEFIXE) or wort.endswith(NEGATIV_SUFFIXE)


# ---------------------------------------------------------------------------
# Tempus
# ---------------------------------------------------------------------------

def tempus(wort_tokens: list, turn_idx: int, sm) -> None:
    """Grobe Tempuszuordnung pro Satz."""
    nach_satz: dict[int, list] = {}
    for tok in wort_tokens:
        nach_satz.setdefault(tok.satz, []).append(tok)

    for toks in nach_satz.values():
        formen = [t.klein for t in toks]
        anker = toks[0]
        hat_perfekt_hilfsverb = any(f in lex.HILFSVERB_PERFEKT for f in formen)
        hat_partizip = any(_ist_partizip(f) for f in formen)
        hat_futur = any(f in lex.FUTUR_HILFSVERB for f in formen)

        if hat_futur:
            sm.add("tempus_futur", turn_idx, anker.start, toks[-1].end, "future")
        elif hat_perfekt_hilfsverb and hat_partizip:
            sm.add("tempus_perfekt", turn_idx, anker.start, toks[-1].end,
                   "present perfect")
        elif any(f in lex.PRAETERITUM_HILFSVERB for f in formen) or hat_partizip:
            sm.add("tempus_praeteritum", turn_idx, anker.start, toks[-1].end,
                   "simple past")
        else:
            sm.add("tempus_praesens", turn_idx, anker.start, toks[-1].end, "present")


# ---------------------------------------------------------------------------
# Passiv
# ---------------------------------------------------------------------------
_PASSIV_FENSTER = 4


def passiv(wort_tokens: list, turn_idx: int, sm, text: str) -> None:
    """be- oder get-Hilfsverb plus Partizip II im."""
    for i, tok in enumerate(wort_tokens):
        if tok.klein not in lex.PASSIV_HILFSVERB:
            continue
        for j in range(i + 1, min(len(wort_tokens), i + _PASSIV_FENSTER + 1)):
            folgend = wort_tokens[j]
            if folgend.satz != tok.satz:
                break
            if folgend.klein in lex.PARTIZIP_ADJEKTIVISCH:
                break                       # prädikatives Adjektiv, kein Passiv
            if _ist_partizip(folgend.klein):
                sm.add("passiv", turn_idx, tok.start, folgend.end,
                       f"{tok.klein} … {folgend.klein}")
                break


# ---------------------------------------------------------------------------
# Abgeleitete Kennzahlen
# ---------------------------------------------------------------------------

def kennzahlen(sm) -> dict[str, float]:
    """Verdichtet Rohzählungen zu Kennzahlen."""
    z = sm.zaehler
    generisch, ich = z.get("generisch", 0), z.get("ich_nom", 0)
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
        "generisch_quote": (generisch / (generisch + ich)
                            if (generisch + ich) else 0.0),
        "generisch_rate": sm.rate("generisch"),
        "ich_rate": sm.rate("ich_nom"),
        "ich_nominativ_anteil": ich / (ich + ich_obl) if (ich + ich_obl) else 0.0,
        # Irrealis
        "irrealis_rate": sm.rate("irrealis"),
        "irrealis_ambig_rate": sm.rate("irrealis_ambig"),
        "bedauern_rate": sm.rate("bedauern"),
        "bedauern_anzahl": float(z.get("bedauern", 0)),
        # Abtönungsprofil
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

BESCHRIFTUNG: dict[str, tuple[str, str, str]] = {
    "generisch_quote": ("Generic “you” instead of “I”", "B",
                        "Share of generic reference among all first-person "
                        "subject slots — “you just feel awful and there’s "
                        "nothing you can do” instead of “I feel awful”. The "
                        "same move out of the first person that German makes "
                        "with “man”, but one grade less certain: English has no "
                        "dedicated pronoun for it, so the same “you” is usually "
                        "addressed to you. Questions and fixed formulas (“you "
                        "know”, “do you”) are filtered out; what remains is good "
                        "enough as a trajectory and not as an absolute figure."),
    "generisch_rate": ("Generic reference", "B",
                       "Generic “you”, “one”, “people”, “everybody” per 1000 "
                       "words. “They” and “someone” are deliberately excluded — "
                       "in a transcript they are almost always real people, and "
                       "those are counted in the sociogram where they belong."),
    "ich_nominativ_anteil": ("Self as subject", "B",
                             "“I told him” versus “it happened to me”: self in "
                             "subject position or self as the one things happen "
                             "to. An agency proxy, approximate without a parser."),
    "irrealis_rate": ("Irrealis (counterfactual)", "B",
                      "“I would have”, “if I were”, “I wish”. Counterfactual "
                      "thinking, per 1000 words. Only unambiguous periphrastic "
                      "forms are counted; bare “would”, “could” and “might” are "
                      "formally identical to politeness and to habitual past "
                      "(“we would drive down every summer”) and counted "
                      "separately. German does this morphologically and gets a "
                      "cleaner number — this is the one measure where the German "
                      "side is genuinely better off."),
    "irrealis_ambig_rate": ("Irrealis (ambiguous forms)", "C",
                            "Bare “would”, “could”, “might”, “should”. Reported "
                            "separately rather than folded into the number above."),
    "bedauern_rate": ("Regret", "A",
                      "“I should have”, “if only”, “I wish I had”, “looking "
                      "back”. Few hits, but the densest ones in the whole tool."),
    "partikel_resignativ_rate": ("Downtoners: resignative", "B",
                                 "“anyway”, “whatever”, “it is what it is”. "
                                 "English has no modal particles; it carries the "
                                 "same attitude in adverbs and fixed phrases. "
                                 "The category is the same as on the German side, "
                                 "the word material is not."),
    "partikel_insistierend_rate": ("Downtoners: insistent", "B",
                                   "“really”, “actually”, “honestly”, “of "
                                   "course”. Arguing against a position the "
                                   "speaker assumes you hold."),
    "partikel_minimierend_rate": ("Downtoners: minimising", "B",
                                  "“just”, “only”, “a bit”, “kind of”. Playing "
                                  "it down. “Just” is the single most frequent "
                                  "item here and also has a temporal reading — "
                                  "read the trajectory, not the level."),
    "partikel_abtönend_rate": ("Downtoners: softening", "B",
                               "“I suppose”, “or something”, “right?”. General "
                               "softening and appeals for agreement."),
    "absolut1_rate": ("Absolutist words", "B",
                      "“always”, “never”, “nothing”, “everyone”. This is the one "
                      "instrument here that is at home in English — the list "
                      "comes from Al-Mosaiwi & Johnstone (2018). One departure "
                      "from the original: colloquial intensifiers (“totally”, "
                      "“completely”, “literally”) are excluded, because in "
                      "spoken therapy they are slang rather than absolutist "
                      "thinking. The exclusion list is in lexika_en/marker.py."),
    "absolut2_rate": ("Absolutist words (gradual)", "C",
                      "“entirely”, “utterly”, “not at all”. Weaker tier, "
                      "reported separately."),
    "zwang_rate": ("Obligation", "B",
                   "“have to”, “supposed to”, “got to”, “should”. Mostly "
                   "periphrastic in English, and “gotta” is the commonest form "
                   "of all in speech — a list without it would count past the "
                   "language."),
    "granularitaet": ("Emotional granularity", "A",
                      "Share of named feelings in all affect vocabulary. The "
                      "move from “bad” to “slighted” is the therapeutic goal "
                      "itself — this measures differentiation, not how much "
                      "affect there is."),
    "distinkte_pro_1000": ("Distinct feeling words", "A",
                           "How many *different* feeling words per 1000 words, "
                           "regardless of how often each is used."),
    "koerperaffekt_rate": ("Body-located affect", "B",
                           "Stomach, tightness, a lump in the throat. Some "
                           "people speak consistently in the body rather than "
                           "the feeling — its own track, not a deficit."),
    "affekt_rate": ("Affect density", "B",
                    "Named feelings per 1000 words. Says nothing about intensity."),
    "vage_rate": ("Vague affect", "B",
                  "“bad”, “weird”, “off”, “fine”. The counterpart to "
                  "granularity. “Fine” and “okay” are in here on purpose: as an "
                  "answer to “how are you” they carry no information at all, and "
                  "an hour of them is the finding."),
    "tempus_perfekt_anteil": ("Past (perfect)", "B",
                              "“I have been”, “I’ve told her”. Rough tense "
                              "estimate via auxiliaries and participles."),
    "tempus_praeteritum_anteil": ("Past (simple)", "B",
                                  "“I went”, “it happened”. English splits the "
                                  "past two ways where German largely uses the "
                                  "perfect in speech — the two past shares are "
                                  "therefore not comparable across the languages, "
                                  "only their sum is."),
    "tempus_futur_anteil": ("Future", "B",
                            "“will”, “going to”, “about to”. Anxiety lives in "
                            "the future."),
    "kausal_rate": ("Causal words", "A",
                    "“because”, “that’s why”, “has to do with”. Their increase "
                    "over a course of therapy is one of the better-replicated "
                    "language findings, and this is the original English list "
                    "rather than an adaptation of it."),
    "einsicht_rate": ("Insight words", "A",
                      "“realise”, “noticed”, “makes sense”, “it clicked”. See "
                      "causal words."),
    "hecken_rate": ("Hedging and vagueness", "B",
                    "“kind of”, “I guess”, “I don’t know”, “you know”. Rises "
                    "under threat, near ruptures, and around avoided material. "
                    "Runs higher than the German figure because English "
                    "discourse markers are more frequent — compare it with "
                    "itself over time, never with a German session."),
    "negation_rate": ("Negation", "B",
                      "Defining the self by what it is not. Contractions "
                      "(“don’t”, “can’t”) are counted as the full forms they are "
                      "in speech."),
    "passiv_rate": ("Passive voice", "B",
                    "“I was told”, “I got left”. Things done to the self. "
                    "Detected via be/get plus past participle; predicative "
                    "adjectives (“I was tired”) are excluded by an explicit "
                    "list, because without it this number measures mood instead "
                    "of agency."),
    "metapher_rate": ("Metaphor candidates", "C",
                      "Words from source domains that appear in a sentence with "
                      "a mental referent. Whether they were meant "
                      "metaphorically is not something the tool decides. Useful "
                      "as a trajectory — does an image persist, mutate or "
                      "disappear — not as a number."),
    "intensivierer_rate": ("Intensifiers", "C",
                           "“totally”, “literally”, “so”. Deliberately *not* "
                           "counted as absolutist language."),
    "woerter_pro_turn": ("Words per turn", "A", "Mean turn length."),
}


KOMPOSIT_INDEX = {
    "generisch_quote": -1.0,
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


KACHELN = [
    ("generisch_quote", "prozent", "generisch"),
    ("granularitaet", "prozent", "emo_vage"),
    ("hecken_rate", "zahl1", "hecken"),
    ("irrealis_rate", "zahl1", "irrealis"),
    ("bedauern_anzahl", "zahl0", "bedauern"),
    ("absolut1_rate", "zahl1", "absolut1"),
    ("kausal_rate", "zahl1", "kausal"),
    ("einsicht_rate", "zahl1", "einsicht"),
    ("koerperaffekt_rate", "zahl1", "emo_koerper"),
    ("passiv_rate", "zahl1", "passiv"),
]

ARC_REIHEN = [
    "generisch_quote", "granularitaet", "distinkte_pro_1000", "hecken_rate",
    "absolut1_rate", "irrealis_rate", "kausal_rate", "einsicht_rate",
    "koerperaffekt_rate", "passiv_rate", "vage_rate", "zwang_rate",
    "tempus_perfekt_anteil", "tempus_praeteritum_anteil", "tempus_futur_anteil",
    "metapher_rate", "redeanteilT", "aufnahme", "lsm",
]


VERGLEICHBAR = {
    "distanzierung": "generisch_quote",
    "irrealis": "irrealis_rate",
    "irrealis_ambig": "irrealis_ambig_rate",
}
