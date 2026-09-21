"""Englische Marker-Lexika."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Generische Referenz statt "I"
# ---------------------------------------------------------------------------

GENERISCH_PRONOMEN = {
    "you", "one", "people", "everybody", "everyone", "folks",
}

# Bewusst ausgeschlossen, obwohl sie generisch gebraucht werden.
GENERISCH_AUSGESCHLOSSEN = {
    "they", "them", "somebody", "someone", "anybody", "anyone",
}

# Erstarrte Formeln mit "you", die keine generische.
GENERISCH_AUSNAHMEN = {
    "you know", "you see", "you mean", "you said", "you asked", "you're saying",
    "you are saying", "thank you", "do you", "did you", "are you", "were you",
    "have you", "has you", "can you", "could you", "would you", "will you",
    "should you", "what do you", "how do you", "if you want", "let you",
    "tell you", "telling you", "told you", "ask you", "asking you",
    "with you", "to you", "for you", "about you", "and you", "you and i",
    "you and me", "like you said", "as you say",
}

ICH_NOMINATIV = {"i", "i'm", "i've", "i'll", "i'd"}
ICH_OBLIQUE = {"me", "myself"}
ICH_POSSESSIV = {"my", "mine"}

WIR_FORMEN = {"we", "us", "our", "ours", "we're", "we've", "we'd", "we'll",
              "ourselves"}


# ---------------------------------------------------------------------------
# 2. Irrealis
# ---------------------------------------------------------------------------

IRREALIS_EINDEUTIG = {
    "would've", "could've", "should've", "might've", "must've",
    "would have", "could have", "should have", "might have",
    "wouldn't have", "couldn't have", "shouldn't have",
    "i'd have", "i would have", "i could have", "i should have",
    "if i were", "if i was", "if i had", "if it were", "if only",
    "i wish", "i wished", "wish i", "wish i had", "wish i could",
    "were to", "had i known", "as if i", "in another life",
    "in a perfect world", "what if i had",
}

# Formgleich mit Höflichkeit, Gewohnheit oder Fähigkeit.
IRREALIS_AMBIG = {
    "would", "wouldn't", "could", "couldn't", "might", "may",
    "should", "shouldn't", "ought",
}


# ---------------------------------------------------------------------------
# 3. Bedauern / Regret
# ---------------------------------------------------------------------------

REGRET_MUSTER = [
    # "I should have said something earlier"
    (r"\bi should(?:'ve| have)\b", "I should have"),
    (r"\bshould(?:'ve| have)\b.{0,30}?\b(said|done|gone|left|told|asked|stayed|known|seen)\b",
     "should have + verb"),
    (r"\bi shouldn'?t have\b|\bi should not have\b", "I shouldn't have"),
    (r"\bi could(?:'ve| have)\b", "I could have"),
    (r"\bi would(?:'ve| have)\b.{0,40}?\bif\b", "I would have … if"),
    # "if only I had", "if I had.
    (r"\bif only\b", "if only"),
    (r"\bif i had (just|only)\b", "if I had only"),
    # explizites Bedauern
    (r"\bi wish i (had|hadn'?t|could have|'?d)\b", "I wish I had"),
    (r"\bi wish\b", "I wish"),
    (r"\bi regret\b|\bregretted\b|\bregretting\b", "I regret"),
    (r"\bin hindsight\b|\blooking back\b|\bin retrospect\b", "looking back"),
    (r"\bwhy didn'?t i\b|\bwhy did i not\b", "why didn't I"),
    (r"\btoo late\b", "too late"),
    (r"\bkick myself\b|\bbeat myself up\b", "kick myself"),
    (r"\bshould have known\b|\bshould have seen\b", "should have known"),
]


# ---------------------------------------------------------------------------
# 4. Abtönung — statt Modalpartikeln
# ---------------------------------------------------------------------------

PARTIKEL_GRUPPEN = {
    "resignativ": ["anyway", "anyways", "whatever", "regardless", "either way",
                   "it is what it is", "oh well", "as usual", "same as always",
                   "no matter what", "at the end of the day", "nothing i can do"],
    "insistierend": ["really", "actually", "honestly", "truly", "obviously",
                     "clearly", "of course", "i mean it", "seriously",
                     "genuinely", "certainly", "surely"],
    "minimierend": ["just", "only", "merely", "a bit", "a little", "kind of",
                    "kinda", "sort of", "sorta", "slightly", "a tad",
                    "no big deal", "nothing much", "barely", "not that bad"],
    "abtönend": ["i suppose", "i guess", "or whatever", "or something",
                 "if that makes sense", "you know what i mean", "right",
                 "somehow", "in a way", "more or less", "pretty much"],
}

# "Right?" als Rückversicherung am Turn-Ende ist Abtönung.
PARTIKEL_POSITION_AUSNAHMEN = {"right", "really", "actually", "just", "obviously"}


# ---------------------------------------------------------------------------
# 5. Absolutismen
# ---------------------------------------------------------------------------

ABSOLUT_STUFE1 = {
    "always", "never", "nothing", "nobody", "no one", "none", "everything",
    "everyone", "everybody", "all", "every", "constantly", "permanently",
    "forever", "endless", "endlessly", "eternally", "everywhere", "nowhere",
    "every time", "each time", "every single time", "all the time",
    "not once", "never again", "no matter what", "under no circumstances",
    "without exception", "impossible", "inevitable", "inevitably",
    "invariably", "categorically", "every day of my life", "not a chance",
}

ABSOLUT_STUFE2 = {
    "definitely", "certainly", "undoubtedly", "entirely", "wholly",
    "utterly", "purely", "solely", "exclusively", "only thing",
    "nothing at all", "not at all", "not a single", "no way", "full stop",
    "beyond doubt", "without question", "flat out", "point blank",
}

# Bewusst ausgeschlossen.
ABSOLUT_AUSGESCHLOSSEN = {
    "totally", "completely", "absolutely", "literally", "super", "way",
    "insanely", "crazy", "madly", "ridiculously", "massively", "hugely",
    "terribly", "awfully", "horribly", "dead", "pretty", "quite", "rather",
    "fairly", "real", "proper",
}

# Deontischer Zwang
ZWANG = {
    "must", "mustn't", "have to", "has to", "had to", "having to",
    "got to", "gotta", "have got to", "need to", "needs to", "needed to",
    "should", "shouldn't", "ought to", "supposed to", "meant to",
    "required to", "obliged to", "forced to", "no choice", "have no choice",
    "duty", "obligation", "expected to", "expected of me", "not allowed",
}


# ---------------------------------------------------------------------------
# 6. Hecken und Vagheit
# ---------------------------------------------------------------------------

HECKEN = {
    "kind of", "kinda", "sort of", "sorta", "somewhat", "somehow",
    "maybe", "perhaps", "possibly", "probably", "presumably", "arguably",
    "i guess", "i suppose", "i think", "i believe", "i feel like", "i'd say",
    "i don't know", "i dunno", "dunno", "no idea", "not sure", "i'm not sure",
    "you know", "i mean", "or something", "or whatever", "or anything",
    "something like that", "a bit", "a little", "a little bit", "slightly",
    "more or less", "pretty much", "in a way", "in a sense", "basically",
    "essentially", "practically", "roughly", "hard to say", "hard to explain",
    "how do i put it", "how do i say this", "not really", "not exactly",
    "not quite", "sort of like", "kind of like", "if that makes sense",
    "i'm not really sure", "whatever it was", "something along those lines",
}


# ---------------------------------------------------------------------------
# 7. Kausalität und Einsicht
# ---------------------------------------------------------------------------

KAUSAL = {
    "because", "cause", "cos", "coz", "since", "therefore", "thus", "hence",
    "so that", "as a result", "results in", "resulted in", "leads to",
    "led to", "lead to", "due to", "owing to", "thanks to", "that's why",
    "which is why", "the reason", "reason why", "reasons", "cause of",
    "causes", "caused", "causing", "effect", "consequence", "consequences",
    "connected to", "connection", "linked to", "link between", "comes from",
    "came from", "stems from", "rooted in", "has to do with", "to do with",
    "explains", "explain why", "makes me", "made me", "brought on",
}

EINSICHT = {
    "realise", "realize", "realised", "realized", "realising", "realizing",
    "understand", "understood", "understanding", "figure out", "figured out",
    "figuring out", "work out", "worked out", "see now", "notice", "noticed",
    "noticing", "aware", "awareness", "makes sense", "made sense",
    "occurs to me", "occurred to me", "dawned on me", "it hit me",
    "never thought of it that way", "now that i say it",
    "now that i think about it", "saying it out loud", "new to me",
    "insight", "recognise", "recognize", "recognised", "recognized",
    "admit", "admitting", "it clicked", "penny dropped", "i see it now",
}


# ---------------------------------------------------------------------------
# 8. Zeitliche Orientierung
# ---------------------------------------------------------------------------

ZEIT_ADVERBIEN = {
    "vergangenheit": {
        "back then", "before", "earlier", "yesterday", "recently", "lately",
        "the other day", "last week", "last month", "last year", "years ago",
        "a while back", "growing up", "as a kid", "as a child",
        "when i was little", "in the past", "used to", "previously",
        "at the time", "looking back", "way back",
    },
    "gegenwart": {
        "now", "right now", "today", "currently", "presently", "at the moment",
        "these days", "nowadays", "at present", "as we speak", "this week",
        "so far", "still", "meanwhile", "in the meantime",
    },
    "zukunft": {
        "tomorrow", "soon", "later", "eventually", "someday", "one day",
        "next week", "next month", "next year", "in future", "in the future",
        "going forward", "from now on", "down the line", "upcoming",
        "afterwards", "by then", "sooner or later", "from here on",
    },
}

# Für die Tempus-Heuristik in sprachen/en.py.
HILFSVERB_PERFEKT = {
    "have", "has", "had", "i've", "we've", "they've", "you've",
    "haven't", "hasn't", "hadn't",
}
PRAETERITUM_HILFSVERB = {"was", "were", "wasn't", "weren't", "did", "didn't"}
FUTUR_HILFSVERB = {
    "will", "i'll", "we'll", "he'll", "she'll", "they'll", "you'll", "it'll",
    "won't", "shall", "gonna", "going to", "about to",
}


# ---------------------------------------------------------------------------
# 9. Negation
# ---------------------------------------------------------------------------

NEGATION = {
    "not", "no", "never", "none", "nobody", "no one", "nothing", "nowhere",
    "neither", "nor", "without",
    "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
    "can't", "cannot", "couldn't", "won't", "wouldn't", "shouldn't",
    "shan't", "mustn't", "haven't", "hasn't", "hadn't", "ain't", "nope",
    "not at all", "no way", "not really", "hardly", "barely", "scarcely",
}

# Präfixe und Suffixe, die eine Eigenschaft verneinen.
NEGATIV_PRAEFIXE = ("un", "dis", "im", "in", "ir", "non", "mis")
NEGATIV_SUFFIXE = ("less",)

# Wörter, die mit einem Negationspräfix *anfangen*, ohne.
NEGATIV_MORPH_AUSNAHMEN = {
    "under", "understand", "understood", "understanding", "until", "unless",
    "uncle", "universe", "university", "unit", "union", "unique", "united",
    "instead", "interest", "interested", "interesting", "internal", "into",
    "insight", "inside", "instance", "instant", "important", "impression",
    "improve", "impact", "implies", "imagine", "immediate", "increase",
    "indeed", "individual", "industry", "information", "initial", "input",
    "insist", "install", "instinct", "institute", "intense", "intention",
    "invite", "involve", "involved", "income", "include", "increase",
    "discuss", "discussion", "discover", "distance", "district", "display",
    "dispute", "mission", "missing", "mister", "minute", "minutes",
    "nonsense", "unlike", "unlikely", "endless", "bless", "glass", "class",
    "less", "unless", "impossible", "impatient",
}


# ---------------------------------------------------------------------------
# 10. Passiv
# ---------------------------------------------------------------------------

PASSIV_HILFSVERB = {
    "was", "were", "is", "are", "am", "been", "being", "be",
    "get", "gets", "got", "gotten", "getting",
    "wasn't", "weren't", "isn't", "aren't",
}

# Unregelmässige Partizipien II.
PARTIZIP_UNREGELMAESSIG = {
    "told", "said", "given", "taken", "made", "done", "seen", "shown", "sent",
    "brought", "bought", "caught", "taught", "thrown", "left", "kept", "held",
    "put", "set", "let", "hurt", "cut", "hit", "beaten", "broken", "chosen",
    "driven", "eaten", "fallen", "forgotten", "forgiven", "frozen", "hidden",
    "known", "laid", "lost", "meant", "met", "paid", "read", "run",
    "sold", "spoken", "spent", "stolen", "struck", "swept", "torn", "thought",
    "woken", "worn", "written", "heard", "found", "felt", "led", "built",
    "dealt", "drawn", "grown", "hung", "understood", "withdrawn", "overlooked",
    "overheard", "misunderstood", "cast", "shut", "split", "spread",
}

# Formgleich mit dem Passiv, aber prädikatives Adjektiv.
PARTIZIP_ADJEKTIVISCH = {
    "tired", "scared", "worried", "interested", "excited", "bored", "annoyed",
    "confused", "frustrated", "disappointed", "embarrassed", "ashamed",
    "surprised", "shocked", "stressed", "relaxed", "exhausted", "drained",
    "overwhelmed", "depressed", "concerned", "pleased", "satisfied", "amazed",
    "supposed", "used", "married", "divorced", "engaged", "involved",
    "related", "based", "gone", "done", "finished", "prepared", "determined",
    "convinced", "committed", "attached", "obsessed", "closed", "opened",
    "crowded", "dressed", "seated", "located", "terrified", "horrified",
    "irritated", "agitated", "isolated", "detached", "disconnected",
}


# ---------------------------------------------------------------------------
# 11. Intensivierer (eigene Spur)
# ---------------------------------------------------------------------------

INTENSIVIERER = set(ABSOLUT_AUSGESCHLOSSEN) | {
    "very", "so", "really", "extremely", "incredibly", "unbelievably",
    "enormously", "immensely", "deeply", "profoundly", "seriously",
    "genuinely", "downright", "damn", "bloody", "freaking", "so much",
    "such a", "a whole lot", "a hell of a",
}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

WORTLISTEN = {
    "generisch": GENERISCH_PRONOMEN,
    "ich_nom": ICH_NOMINATIV,
    "ich_obl": ICH_OBLIQUE,
    "ich_poss": ICH_POSSESSIV,
    "wir": WIR_FORMEN,
    "irrealis": IRREALIS_EINDEUTIG,
    "irrealis_ambig": IRREALIS_AMBIG,
    "absolut1": ABSOLUT_STUFE1,
    "absolut2": ABSOLUT_STUFE2,
    "zwang": ZWANG,
    "hecken": HECKEN,
    "kausal": KAUSAL,
    "einsicht": EINSICHT,
    "negation": NEGATION,
    "intensivierer": INTENSIVIERER,
}

for _gruppe, _woerter in PARTIKEL_GRUPPEN.items():
    WORTLISTEN["partikel_" + _gruppe] = set(_woerter)

for _zeit, _woerter in ZEIT_ADVERBIEN.items():
    WORTLISTEN["zeit_" + _zeit] = set(_woerter)

del _gruppe, _woerter, _zeit
