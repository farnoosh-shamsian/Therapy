"""Funktionswörter: Stoppwörter, Pronomenparadigmen, LSM-Kategorien."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Pronomenparadigmen
# ---------------------------------------------------------------------------

PRONOMEN = {
    "1sg": {"ich", "mir", "mich", "mein", "meine", "meiner", "meines", "meinem",
            "meinen", "meins"},
    "2sg": {"du", "dir", "dich", "dein", "deine", "deiner", "deines", "deinem",
            "deinen", "deins"},
    "3sg_m": {"er", "ihm", "ihn", "sein", "seine", "seiner", "seines", "seinem",
              "seinen", "seins"},
    "3sg_f": {"sie", "ihr", "ihre", "ihrer", "ihres", "ihrem", "ihren"},
    "3sg_n": {"es"},
    "1pl": {"wir", "uns", "unser", "unsere", "unserer", "unseres", "unserem",
            "unseren"},
    "2pl": {"ihr", "euch", "euer", "eure", "eurer", "eures", "eurem", "euren"},
    "3pl": {"sie", "ihnen", "ihre", "ihrer", "ihren"},
    "hoeflich": {"Sie", "Ihnen", "Ihr", "Ihre", "Ihrer", "Ihrem", "Ihren"},
    "indefinit": {"man", "einem", "einen", "jemand", "niemand", "irgendwer",
                  "alle", "jeder", "keiner", "etwas", "nichts", "welche"},
    "reflexiv": {"sich", "mich", "dich", "uns", "euch"},
    "demonstrativ": {"der", "die", "das", "dieser", "diese", "dieses", "diesem",
                     "diesen", "jener", "jene", "jenes", "derjenige", "dasselbe"},
}

# "Sie" höflich vs.
SIEZEN_MARKER = {"Sie", "Ihnen", "Ihr", "Ihre", "Ihrem", "Ihren", "Ihrer"}


# ---------------------------------------------------------------------------
# LSM-Kategorien
# ---------------------------------------------------------------------------

LSM_KATEGORIEN = {
    "artikel": {
        "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen",
        "einem", "einer", "eines",
    },
    "praeposition": {
        "in", "an", "auf", "über", "unter", "vor", "hinter", "neben", "zwischen",
        "bei", "mit", "nach", "seit", "von", "zu", "aus", "durch", "für", "gegen",
        "ohne", "um", "trotz", "während", "wegen", "statt", "innerhalb", "ausserhalb",
        "außerhalb", "gegenüber", "entlang", "bis", "ab", "am", "im", "beim", "zum",
        "zur", "vom", "ins", "aufs",
    },
    "personalpronomen": {
        "ich", "du", "er", "sie", "es", "wir", "ihr", "mich", "dich", "sich",
        "uns", "euch", "mir", "dir", "ihm", "ihn", "ihnen",
    },
    "possessivpronomen": {
        "mein", "meine", "meinem", "meinen", "meiner", "meines",
        "dein", "deine", "deinem", "deinen", "deiner",
        "sein", "seine", "seinem", "seinen", "seiner",
        "ihr", "ihre", "ihrem", "ihren", "ihrer",
        "unser", "unsere", "unserem", "unseren",
        "euer", "eure", "eurem", "euren",
    },
    "indefinitpronomen": {
        "man", "jemand", "niemand", "etwas", "nichts", "alles", "alle", "jeder",
        "jede", "jedes", "keiner", "keine", "kein", "einige", "manche", "viele",
        "wenige", "mehrere", "irgendwer", "irgendwas", "irgendetwas",
    },
    "hilfsverb": {
        "bin", "bist", "ist", "sind", "seid", "war", "warst", "waren", "wart",
        "habe", "hab", "hast", "hat", "haben", "habt", "hatte", "hattest",
        "hatten", "hattet", "werde", "wirst", "wird", "werden", "werdet",
        "wurde", "wurden", "worden", "sei", "wäre", "wären", "hätte", "hätten",
        "würde", "würden", "kann", "kannst", "können", "könnt", "konnte",
        "muss", "musst", "müssen", "müsst", "soll", "sollst", "sollen",
        "darf", "darfst", "dürfen", "mag", "magst", "mögen", "möchte", "will",
        "willst", "wollen", "wollt",
    },
    "negation": {
        "nicht", "nichts", "kein", "keine", "keinen", "keinem", "keiner",
        "nie", "niemals", "niemand", "nein", "weder", "nirgends", "ohne",
    },
    "konjunktion": {
        "und", "oder", "aber", "denn", "sondern", "weil", "dass", "ob", "wenn",
        "als", "wie", "obwohl", "damit", "sodass", "während", "bevor", "nachdem",
        "seit", "falls", "indem", "sobald", "solange", "auch", "doch", "jedoch",
        "allerdings", "trotzdem", "dennoch", "deshalb", "deswegen", "also",
    },
    "quantifizierer": {
        "viel", "viele", "wenig", "wenige", "mehr", "weniger", "meist", "meiste",
        "genug", "kaum", "fast", "ziemlich", "sehr", "so", "zu", "ganz", "halb",
        "gar", "bisschen", "etwas", "einige", "manche", "oft", "selten", "immer",
        "nie", "manchmal", "häufig",
    },
    "hochfrequente_adverbien": {
        "dann", "da", "hier", "dort", "jetzt", "noch", "schon", "nur", "wieder",
        "eben", "halt", "mal", "eigentlich", "vielleicht", "wohl", "ja", "eh",
        "sowieso", "überhaupt", "natürlich", "einfach", "irgendwie", "sehr",
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
    "äh", "ähm", "hm", "hmm", "mhm", "öh", "ähem", "tja", "naja", "na",
    "ach", "ah", "oh", "okay", "ok", "gut", "genau", "richtig", "klar",
    "weisst", "weißt", "ne", "nech", "gell", "quasi", "sozusagen",
    "sagen", "sag", "sagt", "gesagt", "meine", "meinen", "denke", "glaube",
}

_ALLGEMEIN = {
    "aber", "alle", "allem", "allen", "aller", "alles", "als", "also", "am",
    "an", "andere", "anderem", "anderen", "anders", "auch", "auf", "aus",
    "bei", "beim", "bin", "bis", "bist", "da", "damit", "dann", "das",
    "dass", "dem", "den", "denn", "der", "des", "dessen", "dich", "die",
    "dies", "diese", "diesem", "diesen", "dieser", "dieses", "dir", "doch",
    "dort", "du", "durch", "ein", "eine", "einem", "einen", "einer", "eines",
    "er", "es", "etwas", "euch", "für", "gegen", "gewesen", "hab", "habe",
    "haben", "hat", "hatte", "hatten", "hier", "hin", "hinter", "ich", "ihm",
    "ihn", "ihnen", "ihr", "ihre", "ihrem", "ihren", "ihrer", "im", "in",
    "ins", "ist", "ja", "jede", "jedem", "jeden", "jeder", "jedes", "jetzt",
    "kann", "kannst", "können", "könnt", "könnte", "mal", "man", "manche",
    "mein", "meine", "meinem", "meinen", "meiner", "mich", "mir", "mit",
    "muss", "musst", "müssen", "müsst", "nach", "nachdem", "nicht", "nichts",
    "noch", "nun", "nur", "ob", "oder", "ohne", "schon", "sehr", "sein",
    "seine", "seinem", "seinen", "seiner", "seit", "selbst", "sich", "sie",
    "sind", "so", "solche", "soll", "sollen", "sollte", "sondern", "sonst",
    "über", "um", "und", "uns", "unser", "unsere", "unter", "vom", "von",
    "vor", "während", "war", "waren", "warst", "was", "weg", "weil", "weiter",
    "welche", "welchem", "welchen", "welcher", "welches", "wenn", "wer",
    "werde", "werden", "wie", "wieder", "will", "wir", "wird", "wirst", "wo",
    "wollen", "wollte", "würde", "würden", "zu", "zum", "zur", "zwar",
    "zwischen", "hatte", "hätte", "hätten", "wäre", "wären", "worden",
    "wurde", "wurden", "eigentlich", "vielleicht", "halt", "eben", "einfach",
    "immer", "mehr", "viel", "viele", "wenig", "wenige", "kaum", "fast",
    "ganz", "gar", "bisschen", "oft", "manchmal", "irgendwie", "darauf",
    "daran", "darüber", "davon", "dazu", "dabei", "dafür", "dagegen",
    "dadurch", "deshalb", "deswegen", "trotzdem", "dennoch", "jedoch",
    "allerdings", "natürlich", "überhaupt", "sowieso", "eh",
}

STOPPWOERTER: set[str] = _ALLGEMEIN | _FUELLSEL | FUNKTIONSWOERTER

# Diese Wörter stehen zwar in STOPPWOERTER, sind.
STOPPWORT_AUSNAHMEN = {"ich", "man", "nicht", "nie", "immer", "kein", "muss", "sollte"}


# ---------------------------------------------------------------------------
# Füllwörter und Rückmeldepartikeln
# ---------------------------------------------------------------------------

RUECKKANAL = {
    "mhm", "hm", "hmm", "mh", "aha", "ah", "ach so", "achso", "ja", "ja ja",
    "jaja", "genau", "okay", "ok", "verstehe", "klar", "gut", "richtig",
    "stimmt", "sicher", "natürlich", "soso", "oh", "ach", "nun ja",
}

VERZOEGERUNG = {"äh", "ähm", "öh", "öhm", "hm", "em", "ehm", "mh"}

# Abbrüche und Selbstkorrekturen im Transkript, oft als.
ABBRUCH_ZEICHEN = ("-", "--", "/", "…", "...")
