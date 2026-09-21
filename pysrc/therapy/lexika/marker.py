"""Deutsche Marker-Lexika."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

MAN_NOMINATIV = {"man"}
MAN_OBLIQUE_AMBIG = {"einem", "einen"}  # gezählt, aber nicht in der Quote

ICH_NOMINATIV = {"ich"}
ICH_OBLIQUE = {"mir", "mich"}
ICH_POSSESSIV = {
    "mein", "meine", "meiner", "meines", "meinem", "meinen", "meins",
}

# Generisches „du“: auch Distanzierung.
DU_GENERISCH = {"du", "dir", "dich", "dein", "deine", "deinem", "deinen"}

WIR_FORMEN = {"wir", "uns", "unser", "unsere", "unserem", "unseren", "unserer"}


# ---------------------------------------------------------------------------
# 2. Konjunktiv II
# ---------------------------------------------------------------------------

KONJUNKTIV2_EINDEUTIG = {
    # sein / haben / werden
    "wäre", "wären", "wärst", "wärest", "wäret", "wärt",
    "hätte", "hätten", "hättest", "hättet",
    "würde", "würden", "würdest", "würdet",
    # Modalverben mit Umlaut
    "könnte", "könnten", "könntest", "könntet",
    "müsste", "müssten", "müsstest", "müsstet", "müßte", "müßten",
    "dürfte", "dürften", "dürftest", "dürftet",
    "möchte", "möchten", "möchtest", "möchtet",
    # starke Verben
    "ginge", "gingen", "gingest",
    "käme", "kämen", "kämst", "kämest",
    "gäbe", "gäben", "gäbst", "gäbest",
    "täte", "täten", "tätest",
    "wüsste", "wüssten", "wüsstest", "wüßte", "wüßten",
    "bräuchte", "bräuchten", "bräuchtest",
    "stünde", "stünden", "stände", "ständen",
    "fände", "fänden", "fändest",
    "sähe", "sähen", "sähest",
    "hieße", "hießen",
    "läge", "lägen",
    "bliebe", "blieben",
    "nähme", "nähmen",
    "hielte", "hielten",
    "liefe", "liefen",
    "zöge", "zögen",
    "verlöre", "verlören",
    "bekäme", "bekämen",
    "bliebe", "blieben",
    "flöge", "flögen",
    "schriebe", "schrieben",
    "spräche", "sprächen",
    "träfe", "träfen",
    "trüge", "trügen",
    "läse", "läsen",
    "hülfe", "hälfe",
}

# Formgleich mit Präteritum. Separat gezählt.
KONJUNKTIV2_AMBIG = {
    "sollte", "sollten", "solltest", "solltet",
    "wollte", "wollten", "wolltest", "wolltet",
    "konnte", "konnten", "konntest",   # ohne Umlaut = Präteritum, aber oft vertippt/gesprochen
    "musste", "mussten", "musstest", "mußte", "mußten",
    "machte", "machten", "sagte", "sagten", "dachte", "dachten",
}


# ---------------------------------------------------------------------------
# 3. Bedauern / Regret
# ---------------------------------------------------------------------------

REGRET_MUSTER = [
    # "hätte ich nur früher …", "wenn ich.
    (r"\bhätte ich (nur|doch|bloß|blos|mal)\b", "hätte ich nur"),
    (r"\bwenn ich (nur|doch|bloß|blos)\b", "wenn ich doch"),
    (r"\bwäre ich (nur|doch|bloß|blos)\b", "wäre ich nur"),
    # "ich hätte … sollen/müssen/können"
    (r"\bhätte ich .{0,40}?\b(sollen|müssen|können|dürfen)\b", "hätte … sollen"),
    (r"\bich hätte .{0,40}?\b(sollen|müssen|können|dürfen)\b", "ich hätte … sollen"),
    (r"\bhätte .{0,25}?\bnicht\b .{0,25}?\b(sollen|dürfen)\b", "hätte nicht sollen"),
    # explizites Bedauern
    (r"\bbereue\b|\bbereut\b|\bbedaure\b|\bbedauert\b", "bereue"),
    (r"\bim nachhinein\b", "im Nachhinein"),
    (r"\brückblickend\b|\bim rückblick\b", "rückblickend"),
    (r"\bwarum habe ich (das )?nicht\b|\bwarum hab ich (das )?nicht\b", "warum habe ich nicht"),
    (r"\bich wünschte\b", "ich wünschte"),
    (r"\bzu spät\b", "zu spät"),
    (r"\bhätte anders\b|\banders gemacht hätte\b", "hätte anders"),
]


# ---------------------------------------------------------------------------
# 4. Modalpartikeln
# ---------------------------------------------------------------------------

PARTIKEL_GRUPPEN = {
    "resignativ": ["halt", "eben", "nun mal", "nunmal", "sowieso", "ohnehin", "eh"],
    "insistierend": ["doch", "ja", "wohl", "schon", "durchaus", "sehr wohl"],
    "minimierend": ["nur", "bloß", "blos", "lediglich", "gerade mal", "grade mal",
                    "bisschen", "kurz mal"],
    "abtönend": ["einfach", "mal", "denn", "etwa", "auch", "ruhig"],
}

# „ja“ am Turn-Anfang zählt nicht.
PARTIKEL_POSITION_AUSNAHMEN = {"ja", "doch", "schon", "eben"}


# ---------------------------------------------------------------------------
# 5. Absolutismen
# ---------------------------------------------------------------------------

ABSOLUT_STUFE1 = {
    "immer", "nie", "niemals", "nichts", "niemand", "keiner", "keine", "keines",
    "keinem", "keinen", "alles", "alle", "jeder", "jede", "jedes", "jedem", "jeden",
    "ständig", "permanent", "dauernd", "durchgehend", "ausnahmslos", "sämtliche",
    "überall", "nirgends", "nirgendwo", "jedesmal", "jedes mal", "unmöglich",
    "ewig", "endlos", "grundsätzlich", "prinzipiell", "zwangsläufig",
    "nie wieder", "für immer", "auf keinen fall", "in keinster weise",
    "ohne ausnahme", "kein einziges mal", "nicht ein einziges",
}

ABSOLUT_STUFE2 = {
    "völlig", "vollkommen", "vollständig", "absolut", "definitiv", "zweifellos",
    "gänzlich", "restlos", "ausschliesslich", "ausschließlich", "einzig",
    "purer", "pure", "reiner", "reine", "nur noch", "gar nicht", "überhaupt nicht",
    "überhaupt nichts", "gar nichts", "gar keine", "gar kein",
}

# Bewusst ausgeschlossen: Umgangssprache, kein Absolutismus.
ABSOLUT_AUSGESCHLOSSEN = {
    "total", "voll", "ganz", "echt", "richtig", "mega", "super", "ziemlich",
    "krass", "extrem", "wahnsinnig", "unheimlich", "furchtbar", "schrecklich",
    "tierisch", "irre", "brutal", "megamässig",
}

# Deontischer Zwang — eigene Kategorie, nicht Absolutismus.
ZWANG = {
    "muss", "musst", "müssen", "müsst", "musste", "mussten", "müsste", "müssten",
    "soll", "sollst", "sollen", "sollt", "sollte", "sollten",
    "darf nicht", "darfst nicht", "dürfen nicht",
    "zwingen", "zwingt", "gezwungen", "zwang", "notgedrungen", "pflicht",
}


# ---------------------------------------------------------------------------
# 6. Hecken und Vagheit
# ---------------------------------------------------------------------------

HECKEN = {
    "irgendwie", "irgendwas", "irgendwo", "irgendwann", "irgendein", "irgendeine",
    "eigentlich", "sozusagen", "quasi", "gewissermassen", "gewissermaßen",
    "vielleicht", "eventuell", "möglicherweise", "womöglich", "wahrscheinlich",
    "schätze", "vermute", "denke mal", "glaube ich", "glaub ich", "ich glaube",
    "ich denke", "ich meine", "keine ahnung", "weiss nicht", "weiß nicht",
    "so eine art", "eine art", "so was wie", "sowas wie", "so ungefähr",
    "mehr oder weniger", "im prinzip", "im grunde", "in gewisser weise",
    "ein bisschen", "ein wenig", "so halb", "so in die richtung",
    "schwer zu sagen", "kann man so sagen", "wie soll ich sagen",
    "also ich weiss nicht", "nicht so richtig", "so irgendwie",
}


# ---------------------------------------------------------------------------
# 7. Kausalität und Einsicht
# ---------------------------------------------------------------------------

KAUSAL = {
    "weil", "denn", "deshalb", "deswegen", "darum", "daher", "folglich",
    "sodass", "so dass", "dadurch", "aufgrund", "wegen", "infolge", "weshalb",
    "zusammenhang", "zusammenhängt", "hängt zusammen", "führt dazu", "führte dazu",
    "liegt daran", "lag daran", "grund", "gründe", "ursache", "ursachen",
    "bewirkt", "verursacht", "resultiert", "kommt daher", "kommt davon",
    "hat damit zu tun", "hängt damit zusammen", "erklärt",
}

EINSICHT = {
    "verstehe", "verstanden", "verstehen", "begreife", "begriffen", "begreifen",
    "erkenne", "erkannt", "erkennen", "merke", "gemerkt", "bemerkt", "aufgefallen",
    "klar geworden", "wird mir klar", "ist mir klar", "bewusst geworden",
    "bewusst", "einsehen", "eingesehen", "einsicht", "realisiert", "realisiere",
    "durchschaue", "dämmert", "sehe jetzt", "weiss jetzt", "weiß jetzt",
    "neu für mich", "noch nie so gesehen", "fällt mir gerade auf",
    "jetzt wo ich das sage", "wenn ich so darüber nachdenke",
}


# ---------------------------------------------------------------------------
# 8. Zeitliche Orientierung
# ---------------------------------------------------------------------------

ZEIT_ADVERBIEN = {
    "vergangenheit": {
        "damals", "früher", "gestern", "vorgestern", "letztens", "neulich",
        "seinerzeit", "vorhin", "davor", "einst", "ehemals", "als kind",
        "letzte woche", "letzten monat", "letztes jahr", "vor jahren",
        "vor kurzem", "seit jeher", "schon immer", "rückblickend",
    },
    "gegenwart": {
        "jetzt", "gerade", "heute", "momentan", "aktuell", "zurzeit", "derzeit",
        "gegenwärtig", "im moment", "im augenblick", "heutzutage", "inzwischen",
        "mittlerweile", "grade",
    },
    "zukunft": {
        "morgen", "übermorgen", "bald", "künftig", "zukünftig", "demnächst",
        "später", "nächste woche", "nächsten monat", "nächstes jahr",
        "in zukunft", "irgendwann", "eines tages", "ab jetzt", "von nun an",
        "vorher nicht",
    },
}

# Für die Tempus-Heuristik in markers.py.
HILFSVERB_PERFEKT = {
    "habe", "hab", "hast", "hat", "haben", "habt",
    "bin", "bist", "ist", "sind", "seid",
}
HILFSVERB_PRAETERITUM_SEIN_HABEN = {
    "war", "warst", "waren", "wart", "hatte", "hattest", "hatten", "hattet",
}
FUTUR_HILFSVERB = {"werde", "wirst", "wird", "werden", "werdet"}


# ---------------------------------------------------------------------------
# 9. Negation
# ---------------------------------------------------------------------------

NEGATION = {
    "nicht", "nichts", "nie", "niemals", "niemand", "nirgends", "nirgendwo",
    "kein", "keine", "keiner", "keines", "keinem", "keinen", "keins",
    "weder", "noch nie", "ohne", "keinesfalls", "nein", "nee", "nö",
    "unmöglich", "nix", "gar nicht", "überhaupt nicht", "auf keinen fall",
}

# Verneinende Präfixe, mit Mindestlänge.
NEGATIV_PRAEFIXE = ("un", "miss", "nicht")
NEGATIV_SUFFIXE = ("los", "frei", "unfähig")


# ---------------------------------------------------------------------------
# 10. Passiv
# ---------------------------------------------------------------------------

PASSIV_HILFSVERB = {
    "wurde", "wurdest", "wurden", "wurdet", "wird", "werde", "wirst", "werden",
    "werdet", "worden", "würde", "würden",
}

# Partizip II ohne „ge-“.
UNTRENNBARE_PRAEFIXE = ("be", "ver", "er", "ent", "emp", "zer", "miss", "ge")

# Sieht aus wie Passiv, ist keins.
PASSIV_AUSNAHMEN = {"werden", "wird"}  # nur relevant ohne folgendes Partizip


# ---------------------------------------------------------------------------
# 11. Intensivierer (eigene Spur)
# ---------------------------------------------------------------------------

INTENSIVIERER = set(ABSOLUT_AUSGESCHLOSSEN) | {
    "sehr", "besonders", "äusserst", "äußerst", "höchst", "furchtbar",
    "unglaublich", "enorm", "massiv", "ungeheuer",
}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

WORTLISTEN = {
    "man": MAN_NOMINATIV,
    "man_ambig": MAN_OBLIQUE_AMBIG,
    "ich_nom": ICH_NOMINATIV,
    "ich_obl": ICH_OBLIQUE,
    "ich_poss": ICH_POSSESSIV,
    "du_generisch": DU_GENERISCH,
    "wir": WIR_FORMEN,
    "konjunktiv2": KONJUNKTIV2_EINDEUTIG,
    "konjunktiv2_ambig": KONJUNKTIV2_AMBIG,
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
