"""Deutsche Marker-Lexika.

Konventionen für dieses Modul:

* Alle Einträge sind **kleingeschrieben**. Der Abgleich passiert gegen die
  kleingeschriebene Wortform (nicht gegen das Lemma), ausser es steht anders
  dabei. Deutsche Funktionswörter flektieren wenig genug, dass Vollformen-
  listen hier ehrlicher sind als ein Lemmatisierer, dem man ansieht, dass er
  geraten hat.
* Mehrwortausdrücke stehen mit einfachem Leerzeichen und werden gegen den
  normalisierten Turn-Text gematcht.
* Jede Liste, die aus einem englischsprachigen Instrument adaptiert wurde,
  sagt das dazu — mitsamt dem, was bewusst *nicht* drin ist.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. man / ich — der grammatische Notausgang aus der ersten Person
# ---------------------------------------------------------------------------
#
# "Man fühlt sich dann halt schlecht" statt "ich fühle mich schlecht".
# Das ist im Deutschen der sauberste Distanzierungsmarker, den es gibt, und er
# hat im Englischen kein Gegenstück ("one" ist im gesprochenen Englisch tot).
#
# Vorsicht bei den obliquen Formen: "einem" und "einen" sind als Indefinit-
# pronomen von "man" nicht vom unbestimmten Artikel zu trennen, ohne zu parsen.
# Sie werden deshalb getrennt gezählt und gehen nicht in die Hauptquote ein.

MAN_NOMINATIV = {"man"}
MAN_OBLIQUE_AMBIG = {"einem", "einen"}  # gezählt, aber nicht in der Quote

ICH_NOMINATIV = {"ich"}
ICH_OBLIQUE = {"mir", "mich"}
ICH_POSSESSIV = {
    "mein", "meine", "meiner", "meines", "meinem", "meinen", "meins",
}

# Die zweite Person tauchte in Klientenrede als Distanzierung auf
# ("du denkst dann, das geht nie vorbei") — generisches "du".
DU_GENERISCH = {"du", "dir", "dich", "dein", "deine", "deinem", "deinen"}

WIR_FORMEN = {"wir", "uns", "unser", "unsere", "unserem", "unseren", "unserer"}


# ---------------------------------------------------------------------------
# 2. Konjunktiv II
# ---------------------------------------------------------------------------
#
# Irrealis. Im Deutschen morphologisch fast geschenkt: die Umlautformen der
# starken Verben sind eindeutig. Die schwachen Verben sind es nicht — bei
# "sollte", "wollte", "machte" ist Präteritum und Konjunktiv II formgleich.
# Die werden separat gezählt und in der UI separat ausgewiesen, statt sie
# stillschweigend in die Hauptzahl zu mischen.

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

# Formgleich mit dem Präteritum. Nicht entscheidbar ohne Kontextanalyse.
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
#
# Die wertvollsten Einzeltreffer im ganzen Werkzeug. Als Muster, nicht als
# Wortliste — die Konstruktion trägt die Bedeutung, nicht das Einzelwort.
# Syntax hier: einfache Platzhalter-Sprache, die in markers.py in echte
# reguläre Ausdrücke übersetzt wird.
#   *   = beliebig viel Text (max. ~40 Zeichen, damit es im Satz bleibt)
#   |   = Alternative innerhalb einer Gruppe (…)

REGRET_MUSTER = [
    # "hätte ich nur früher …", "wenn ich doch bloß …"
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
#
# Das Deutsche trägt hier, was das Englische in den Tonfall legt. "Das ist halt
# so" ist Resignation in drei Wörtern, und keine Übersetzung rettet das.
#
# Bekannte Schwäche, offen benannt: alle diese Wörter haben eine nicht-
# partikelhafte Lesart ("nur" als Fokuspartikel, "ja" als Antwort, "eben" als
# Zeitadverb). Ohne Parser ist das nicht sauber zu trennen. Die Zahlen sind
# deshalb als *Profil über die Zeit* zu lesen, nicht als absolute Häufigkeit —
# der systematische Fehler ist über Sitzungen hinweg konstant und kürzt sich
# in der Trajektorie heraus.

PARTIKEL_GRUPPEN = {
    "resignativ": ["halt", "eben", "nun mal", "nunmal", "sowieso", "ohnehin", "eh"],
    "insistierend": ["doch", "ja", "wohl", "schon", "durchaus", "sehr wohl"],
    "minimierend": ["nur", "bloß", "blos", "lediglich", "gerade mal", "grade mal",
                    "bisschen", "kurz mal"],
    "abtönend": ["einfach", "mal", "denn", "etwa", "auch", "ruhig"],
}

# "ja" als Antwortpartikel am Turn-Anfang ist keine Modalpartikel.
PARTIKEL_POSITION_AUSNAHMEN = {"ja", "doch", "schon", "eben"}


# ---------------------------------------------------------------------------
# 5. Absolutismen
# ---------------------------------------------------------------------------
#
# Adaptiert nach Al-Mosaiwi & Johnstone (2018), "In an Absolute State".
# Das Original ist ein englisches Instrument. Zwei Dinge daran übersetzen sich
# nicht, und beide sind hier korrigiert:
#
#   (a) Die englische Liste enthält Intensivierer ("totally", "completely"),
#       die im gesprochenen Deutsch reine Umgangssprache sind. "Total nett",
#       "voll gut", "ganz okay" sind kein absolutistisches Denken, sondern
#       Jugendsprache und Norddeutsch. Sie stehen unten in AUSGESCHLOSSEN und
#       werden bewusst NICHT gezählt.
#   (b) Deontische Modalität ("muss", "sollte") ist im Deutschen viel häufiger
#       grammatikalisiert als im Englischen. Sie bekommt eine eigene Gruppe
#       (ZWANG) statt in die Absolutismen zu wandern.
#
# Stufe 1 = quantifizierend/temporal absolut, der belastbare Kern.
# Stufe 2 = graduell absolut, schwächer, separat ausgewiesen.

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

# Bewusst ausgeschlossen. Diese Liste ist Teil der Methode, nicht ein Rest.
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
#
# Steigt unter Bedrohung, in der Nähe von Brüchen und rund um Vermiedenes.
# Das ist der Marker, der sich am ehesten *innerhalb* einer Sitzung lohnt.

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
#
# Der Anstieg dieser beiden über eine Therapie hinweg gehört zu den besser
# replizierten sprachlichen Befunden überhaupt (Pennebaker-Linie).

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
#
# Grübeln lebt in der Vergangenheit, Angst in der Zukunft. Die Tempusverteilung
# kommt aus markers.py (Hilfsverb-Heuristik), die Adverbien von hier.

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

# Präfixe, die eine Eigenschaft verneinen ("unfähig", "wertlos", "sinnlos").
# Nur mit Mindestlänge, sonst fängt man "Unterschied" und "Losung" mit ein.
NEGATIV_PRAEFIXE = ("un", "miss", "nicht")
NEGATIV_SUFFIXE = ("los", "frei", "unfähig")


# ---------------------------------------------------------------------------
# 10. Passiv
# ---------------------------------------------------------------------------
#
# "Da wurde mir gesagt", "das ist mir angetan worden". Dinge, die dem Selbst
# geschehen. Erkennung über werden-Hilfsverb + Partizip-II-Morphologie.

PASSIV_HILFSVERB = {
    "wurde", "wurdest", "wurden", "wurdet", "wird", "werde", "wirst", "werden",
    "werdet", "worden", "würde", "würden",
}

# Untrennbare Präfixe: Partizip II ohne "ge-" ("verloren", "bekommen").
UNTRENNBARE_PRAEFIXE = ("be", "ver", "er", "ent", "emp", "zer", "miss", "ge")

# Formen, die wie Passiv aussehen, aber Futur oder Vollverb sind.
PASSIV_AUSNAHMEN = {"werden", "wird"}  # nur relevant ohne folgendes Partizip


# ---------------------------------------------------------------------------
# 11. Intensivierer (eigene Spur, nicht Absolutismus)
# ---------------------------------------------------------------------------

INTENSIVIERER = set(ABSOLUT_AUSGESCHLOSSEN) | {
    "sehr", "besonders", "äusserst", "äußerst", "höchst", "furchtbar",
    "unglaublich", "enorm", "massiv", "ungeheuer",
}


# ---------------------------------------------------------------------------
# Register — was markers.py abläuft
# ---------------------------------------------------------------------------
#
# Jeder Eintrag: (schlüssel, anzeige, art, quelle, konfidenz)
# art: "wort" = Vollformabgleich, "phrase" = n-Gramm im Turn-Text,
#      "muster" = regulärer Ausdruck, "morph" = eigene Funktion in markers.py

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
