"""Englische Funktionswörter: Stoppwörter, Pronomenparadigmen, LSM-Kategorien."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Pronomenparadigmen
# ---------------------------------------------------------------------------

PRONOMEN = {
    "1sg": {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"},
    "2sg": {"you", "your", "yours", "yourself", "you're", "you've", "you'll",
            "you'd"},
    "3sg_m": {"he", "him", "his", "himself", "he's", "he'd", "he'll"},
    "3sg_f": {"she", "her", "hers", "herself", "she's", "she'd", "she'll"},
    "3sg_n": {"it", "its", "itself", "it's", "it'll"},
    "1pl": {"we", "us", "our", "ours", "ourselves", "we're", "we've", "we'd",
            "we'll"},
    "2pl": {"you", "your", "yours", "yourselves"},
    "3pl": {"they", "them", "their", "theirs", "themselves", "they're",
            "they've", "they'd", "they'll"},
    "indefinit": {"one", "someone", "somebody", "anyone", "anybody", "everyone",
                  "everybody", "no one", "nobody", "something", "anything",
                  "everything", "nothing", "people", "all", "each", "none"},
    "reflexiv": {"myself", "yourself", "himself", "herself", "itself",
                 "ourselves", "yourselves", "themselves"},
    "demonstrativ": {"this", "that", "these", "those", "such"},
}

# Im Deutschen trennt die Grossschreibung höfliches "Sie".
SIEZEN_MARKER: set[str] = set()


# ---------------------------------------------------------------------------
# LSM-Kategorien
# ---------------------------------------------------------------------------

LSM_KATEGORIEN = {
    "artikel": {"a", "an", "the"},
    "praeposition": {
        "in", "on", "at", "over", "under", "before", "after", "behind",
        "beside", "between", "among", "with", "without", "by", "from", "to",
        "into", "onto", "out", "of", "off", "through", "across", "against",
        "for", "about", "around", "during", "despite", "towards", "toward",
        "within", "outside", "inside", "beyond", "past", "up", "down",
        "along", "until", "till", "since", "upon", "near", "next to",
    },
    "personalpronomen": {
        "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
        "us", "them", "myself", "yourself", "himself", "herself", "itself",
        "ourselves", "themselves", "i'm", "you're", "he's", "she's", "it's",
        "we're", "they're",
    },
    "possessivpronomen": {
        "my", "mine", "your", "yours", "his", "her", "hers", "its", "our",
        "ours", "their", "theirs",
    },
    "indefinitpronomen": {
        "one", "someone", "somebody", "something", "anyone", "anybody",
        "anything", "everyone", "everybody", "everything", "no one",
        "nobody", "nothing", "people", "all", "some", "any", "each",
        "every", "none", "both", "few", "many", "several", "most",
    },
    "hilfsverb": {
        "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "having", "do", "does", "did", "doing",
        "will", "would", "shall", "should", "can", "could", "may", "might",
        "must", "ought", "i'm", "you're", "he's", "she's", "it's", "we're",
        "they're", "i've", "you've", "we've", "they've", "i'd", "he'd",
        "she'd", "we'd", "they'd", "i'll", "you'll", "he'll", "she'll",
        "we'll", "they'll", "gonna", "gotta",
    },
    "negation": {
        "not", "no", "never", "none", "nobody", "nothing", "nowhere",
        "neither", "nor", "without", "don't", "doesn't", "didn't", "isn't",
        "aren't", "wasn't", "weren't", "can't", "cannot", "couldn't",
        "won't", "wouldn't", "shouldn't", "haven't", "hasn't", "hadn't",
        "ain't",
    },
    "konjunktion": {
        "and", "or", "but", "so", "because", "cause", "that", "if", "when",
        "while", "as", "although", "though", "unless", "until", "whereas",
        "since", "before", "after", "once", "whether", "than", "however",
        "therefore", "thus", "yet", "still", "also", "besides", "anyway",
    },
    "quantifizierer": {
        "much", "many", "little", "few", "more", "less", "fewer", "most",
        "least", "enough", "hardly", "barely", "almost", "nearly", "quite",
        "rather", "very", "so", "too", "half", "whole", "bit", "lot", "lots",
        "often", "rarely", "seldom", "always", "never", "sometimes",
        "usually", "frequently",
    },
    "hochfrequente_adverbien": {
        "then", "there", "here", "now", "still", "already", "just", "again",
        "even", "only", "really", "actually", "maybe", "perhaps", "well",
        "yeah", "anyway", "kind", "sort", "basically", "literally",
        "obviously", "probably", "definitely", "honestly", "simply",
    },
}

FUNKTIONSWOERTER: set[str] = set()
for _kat in LSM_KATEGORIEN.values():
    FUNKTIONSWOERTER |= _kat
del _kat


# ---------------------------------------------------------------------------
# Stoppwörter
# ---------------------------------------------------------------------------

_FUELLSEL = {
    "um", "umm", "uh", "uhh", "er", "erm", "ah", "ahh", "oh", "ooh", "hm",
    "hmm", "mm", "mhm", "mmhm", "huh", "yeah", "yep", "yup", "nah", "nope",
    "okay", "ok", "right", "sure", "fine", "alright", "well", "like",
    "know", "mean", "say", "said", "says", "saying", "tell", "told",
    "think", "thought", "guess", "suppose", "thing", "things", "stuff",
    "bit", "lot", "kind", "sort", "actually", "basically", "literally",
    "sorry", "please", "thanks", "thank", "gonna", "wanna", "gotta",
}

_ALLGEMEIN = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "another", "any", "anything", "are", "aren't", "around", "as",
    "at", "back", "be", "because", "been", "before", "behind", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot",
    "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
    "don't", "down", "during", "each", "either", "else", "enough", "even",
    "ever", "every", "everything", "few", "for", "from", "further", "get",
    "gets", "getting", "give", "go", "goes", "going", "got", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "however", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its",
    "itself", "just", "keep", "let", "little", "make", "makes", "many",
    "may", "maybe", "me", "might", "mine", "more", "most", "much", "must",
    "my", "myself", "near", "need", "never", "next", "no", "nor", "not",
    "nothing", "now", "of", "off", "on", "once", "one", "only", "or",
    "other", "others", "our", "ours", "ourselves", "out", "over", "own",
    "perhaps", "put", "quite", "rather", "really", "same", "see", "seem",
    "seems", "shall", "she", "should", "shouldn't", "since", "so", "some",
    "someone", "something", "still", "such", "take", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "though", "through", "to",
    "too", "under", "until", "up", "upon", "us", "use", "used", "very",
    "want", "was", "wasn't", "way", "we", "we'd", "we'll", "we're", "we've",
    "well", "went", "were", "weren't", "what", "when", "where", "whether",
    "which", "while", "who", "whom", "whose", "why", "will", "with",
    "within", "without", "won't", "would", "wouldn't", "yes", "yet", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
}

STOPPWOERTER: set[str] = _ALLGEMEIN | _FUELLSEL | FUNKTIONSWOERTER

# Diese Wörter stehen zwar in STOPPWOERTER, sind.
STOPPWORT_AUSNAHMEN = {
    "i", "never", "always", "not", "no", "must", "should", "can't", "won't",
    "everyone", "nobody",
}


# ---------------------------------------------------------------------------
# Füllwörter und Rückmeldepartikeln
# ---------------------------------------------------------------------------

RUECKKANAL = {
    "mhm", "mmhm", "mm", "mmm", "hm", "hmm", "uh huh", "uh-huh", "mm hm",
    "yeah", "yep", "yup", "yes", "right", "okay", "ok", "sure", "i see",
    "i see it", "got it", "of course", "exactly", "absolutely", "indeed",
    "gotcha", "makes sense", "understood", "true", "fair enough", "wow",
    "oh", "ah", "aha", "oh i see", "oh right", "oh okay", "hmm okay",
}

VERZOEGERUNG = {"um", "umm", "uh", "uhh", "er", "erm", "ehm", "hm", "mm"}

# Abbrüche und Selbstkorrekturen im Transkript, oft als.
ABBRUCH_ZEICHEN = ("-", "--", "/", "…", "...")
