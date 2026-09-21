"""Emotionsfamilien, Valenz, Metapherndomänen."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Emotionsfamilien
# ---------------------------------------------------------------------------

FAMILIEN: dict[str, set[str]] = {
    "angst": {
        "angst", "ängste", "ängstlich", "furcht", "fürchte", "fürchten", "gefürchtet",
        "panik", "panisch", "sorge", "sorgen", "besorgt", "beunruhigt", "unruhe",
        "nervös", "nervosität", "aufgeregt", "unsicher", "unsicherheit",
        "bedroht", "bedrohlich", "bedrohung", "erschrocken", "erschrecken",
        "schreck", "grauen", "entsetzt", "entsetzen", "beklommen", "beklommenheit",
        "mulmig", "bange", "zittrig", "alarmiert", "hilflos", "ausgeliefert",
        "verlustangst", "versagensangst", "zukunftsangst", "existenzangst",
        "prüfungsangst", "flugangst", "phobie", "katastrophisieren",
    },
    "trauer": {
        "traurig", "trauer", "trauern", "betrübt", "bedrückt", "niedergeschlagen",
        "schwermut", "wehmut", "wehmütig", "melancholisch", "melancholie",
        "verzweifelt", "verzweiflung", "hoffnungslos", "hoffnungslosigkeit",
        "resigniert", "resignation", "leer", "leere", "kummer", "gram",
        "weinen", "geweint", "tränen", "schluchzen", "erschüttert", "gebrochen",
        "verlust", "vermisse", "vermissen", "sehnsucht", "sehnsüchtig",
        "abschied", "endgültig", "unwiederbringlich",
    },
    "wut": {
        "wut", "wütend", "zorn", "zornig", "ärger", "ärgere", "ärgerlich", "geärgert",
        "sauer", "genervt", "gereizt", "aggression", "aggressiv", "aufgebracht",
        "empört", "empörung", "erbost", "rasend", "hass", "hasse", "gehasst",
        "groll", "verbittert", "bitterkeit", "frust", "frustriert", "frustration",
        "explodiert", "platzen", "kochen", "gift", "rachegedanken", "rache",
    },
    "scham": {
        "scham", "schäme", "schämen", "geschämt", "beschämt", "beschämend",
        "peinlich", "peinlichkeit", "blamiert", "blamage", "bloßgestellt",
        "blossgestellt", "gedemütigt", "demütigung", "erniedrigt", "erniedrigung",
        "minderwertig", "minderwertigkeit", "wertlos", "unwürdig", "klein",
        "versagen", "versager", "versagt", "unzulänglich", "ungenügend",
        "verstecken", "verbergen", "durchschaut",
    },
    "schuld": {
        "schuld", "schuldig", "schuldgefühl", "schuldgefühle", "verschuldet",
        "gewissen", "gewissensbisse", "vorwurf", "vorwürfe", "vorwerfen",
        "vorgeworfen", "selbstvorwürfe", "verantwortlich", "verantwortung",
        "reue", "bereue", "bereut", "büßen", "bussen", "wiedergutmachen",
        "falsch gemacht", "mein fehler",
    },
    "freude": {
        "freude", "freue", "freuen", "gefreut", "froh", "glücklich", "glück",
        "fröhlich", "heiter", "vergnügt", "begeistert", "begeisterung",
        "euphorisch", "beschwingt", "gelöst", "ausgelassen", "stolz", "stolzen",
        "zufrieden", "zufriedenheit", "dankbar", "dankbarkeit", "genossen",
        "genießen", "geniessen", "lachen", "gelacht", "leicht", "leichtigkeit",
        "lebendig", "lust",
    },
    "erleichterung": {
        "erleichtert", "erleichterung", "entlastet", "entlastung", "befreit",
        "befreiung", "beruhigt", "beruhigung", "entspannt", "entspannung",
        "aufatmen", "durchatmen", "last gefallen", "stein vom herzen",
        "geht besser", "endlich ruhe",
    },
    "hoffnung": {
        "hoffnung", "hoffe", "hoffen", "gehofft", "zuversicht", "zuversichtlich",
        "optimistisch", "vertrauen", "vertraue", "mut", "mutig", "ermutigt",
        "perspektive", "aussicht", "zukunft", "möglichkeit", "chance",
    },
    "ekel": {
        "ekel", "ekelt", "ekelhaft", "angewidert", "widerlich", "abscheu",
        "abstoßend", "abstossend", "übel", "würgen", "verachtung", "verächtlich",
    },
    "überraschung": {
        "überrascht", "überraschung", "erstaunt", "verblüfft", "verwundert",
        "fassungslos", "sprachlos", "damit nicht gerechnet", "unerwartet",
    },
    "zuneigung": {
        "liebe", "liebevoll", "geliebt", "lieb", "zuneigung", "zärtlich",
        "zärtlichkeit", "nähe", "geborgen", "geborgenheit", "verbunden",
        "verbundenheit", "vertraut", "vertrautheit", "wärme", "herzlich",
        "mögen", "gemocht", "gernhaben", "sehnen",
    },
    "einsamkeit": {
        "einsam", "einsamkeit", "allein", "alleine", "verlassen", "verlassenheit",
        "isoliert", "isolation", "ausgeschlossen", "abgeschnitten", "fremd",
        "niemand da", "keiner versteht", "unverstanden", "übersehen",
        "unsichtbar", "nicht gesehen",
    },
    "neid": {
        "neid", "neidisch", "eifersucht", "eifersüchtig", "missgunst",
        "ungerecht", "warum die", "vergleiche mich",
    },
    "überforderung": {
        "überfordert", "überforderung", "erschöpft", "erschöpfung", "müde",
        "müdigkeit", "ausgebrannt", "burnout", "kraftlos", "energielos",
        "ausgelaugt", "am ende", "zu viel", "schaffe nicht", "überlastet",
        "druck", "stress", "gestresst", "getrieben", "gehetzt", "keine kraft",
    },
    "ruhe": {
        "ruhig", "ruhe", "gelassen", "gelassenheit", "friedlich", "frieden",
        "ausgeglichen", "stabil", "sicher", "sicherheit", "klar", "geerdet",
        "bei mir", "in mir",
    },
}

VALENZ = {
    "angst": -1, "trauer": -1, "wut": -1, "scham": -1, "schuld": -1,
    "ekel": -1, "einsamkeit": -1, "neid": -1, "überforderung": -1,
    "freude": +1, "erleichterung": +1, "hoffnung": +1, "zuneigung": +1, "ruhe": +1,
    "überraschung": 0,
}

# Umgekehrter Index: Wort -> Familien.
WORT_ZU_FAMILIE: dict[str, list[str]] = {}
for _fam, _woerter in FAMILIEN.items():
    for _w in _woerter:
        WORT_ZU_FAMILIE.setdefault(_w, []).append(_fam)
del _fam, _woerter, _w

DIFFERENZIERT: set[str] = set(WORT_ZU_FAMILIE)


# ---------------------------------------------------------------------------
# Vager Affekt
# ---------------------------------------------------------------------------

VAGER_AFFEKT = {
    "schlecht", "gut", "komisch", "seltsam", "merkwürdig", "eigenartig",
    "blöd", "doof", "mies", "beschissen", "bescheiden", "okay", "ok",
    "unangenehm", "angenehm", "schwierig", "schwer", "hart", "anstrengend",
    "nicht so gut", "nicht gut", "ganz gut", "so lala", "geht so",
    "durchwachsen", "wechselhaft", "irgendwie schlecht", "nicht so toll",
    "schlimm", "furchtbar", "schrecklich", "grauenhaft", "toll", "schön",
    "wohl", "unwohl", "unruhig", "aufgewühlt", "durcheinander", "verwirrt",
    "neutral", "normal", "nichts besonderes",
}


# ---------------------------------------------------------------------------
# Körpernaher Affekt
# ---------------------------------------------------------------------------

KOERPER_AFFEKT = {
    # Orte
    "magen", "bauch", "brust", "brustkorb", "herz", "hals", "kehle", "nacken",
    "schultern", "rücken", "kopf", "stirn", "kiefer", "hände", "knie", "beine",
    "haut", "brustbein", "zwerchfell", "solarplexus",
    # Empfindungen
    "druck", "enge", "eng", "kloß", "kloss", "knoten", "stich", "ziehen",
    "brennen", "kribbeln", "taub", "taubheit", "flau", "übelkeit", "schwindel",
    "zittern", "zittere", "schwitzen", "geschwitzt", "herzrasen", "puls",
    "atem", "atmen", "atemlos", "luft", "keine luft", "schwer im magen",
    "kloß im hals", "kloss im hals", "verspannt", "verspannung", "verkrampft",
    "krampf", "steif", "schwer", "bleiern", "heiss", "kalt", "eiskalt",
    "flattern", "flattrig", "zusammengezogen", "eingeschnürt", "wie gelähmt",
    "kein gefühl", "wie betäubt", "wattig", "dumpf",
}


# ---------------------------------------------------------------------------
# Metaphern-Kandidaten
# ---------------------------------------------------------------------------

METAPHERN_DOMAENEN = {
    "bewegung": {
        "weg", "wege", "schritt", "schritte", "vorwärts", "rückwärts", "stehen",
        "stillstand", "feststecken", "festgefahren", "vorankommen", "weiterkommen",
        "kreis", "kreise", "sackgasse", "abzweigung", "umweg", "richtung",
        "laufen", "rennen", "schleppen", "treiben", "bewegen", "stolpern",
        "abgrund", "kante", "rand",
    },
    "behälter": {
        "voll", "leer", "überlaufen", "überläuft", "platzen", "füllen", "gefüllt",
        "deckel", "verschlossen", "zu", "aufmachen", "aufgemacht", "reinlassen",
        "rauslassen", "drin", "drinnen", "innen", "aussen", "außen", "gefäss",
        "gefäß", "fass", "eimer", "tank", "reserve", "reserven",
    },
    "raum": {
        "eng", "weit", "raum", "platz", "luft", "mauer", "wand", "wände", "tür",
        "türen", "fenster", "käfig", "gefängnis", "eingesperrt", "gefangen",
        "loch", "tunnel", "keller", "boden", "oben", "unten", "tief", "hoch",
        "abstand", "distanz", "nähe", "grenze", "grenzen",
    },
    "last": {
        "last", "lasten", "gewicht", "schwer", "schultern", "tragen", "getragen",
        "rucksack", "gepäck", "ballast", "bürde", "erdrückt", "erdrückend",
        "drückt", "abladen", "loswerden", "abwerfen", "stein", "felsen",
        "aufgebürdet", "schultert",
    },
    "wetter": {
        "wolke", "wolken", "grau", "nebel", "neblig", "sturm", "gewitter",
        "donner", "blitz", "regen", "regnet", "sonne", "sonnig", "aufklaren",
        "aufhellen", "dunkel", "düster", "finster", "licht", "schatten",
        "kalt", "frost", "eis", "tauwetter", "windstille", "flaute",
    },
    "kampf": {
        "kampf", "kämpfe", "kämpfen", "gekämpft", "schlacht", "krieg", "front",
        "gegner", "feind", "waffe", "schild", "rüstung", "panzer", "angriff",
        "angegriffen", "verteidigen", "verteidigung", "wehren", "gewehrt",
        "sieg", "niederlage", "verloren", "aufgeben", "kapitulieren",
        "schützen", "schutz", "deckung", "schlagen", "treffer",
    },
    "bindung": {
        "faden", "fäden", "band", "bänder", "seil", "kette", "ketten", "knoten",
        "verbunden", "verknüpft", "abgerissen", "gerissen", "halten", "halt",
        "loslassen", "festhalten", "klammern", "anker", "wurzeln", "brücke",
        "brücken", "netz", "gefesselt", "leine",
    },
    "wasser": {
        "welle", "wellen", "flut", "überflutet", "überschwemmt", "ertrinken",
        "untergehen", "auftauchen", "strom", "strömung", "sog", "tiefe",
        "schwimmen", "treiben", "ufer", "land", "insel", "sturzflut",
        "tropfen", "versickern", "austrocknen", "trocken",
    },
    "maschine": {
        "funktionieren", "funktioniert", "kaputt", "defekt", "reparieren",
        "motor", "getriebe", "rad", "räder", "schalter", "abschalten",
        "ausschalten", "einschalten", "automatisch", "programm", "programmiert",
        "batterie", "akku", "leerlauf", "rädchen", "maschine", "roboter",
    },
    "dunkelheit_licht": {
        "dunkel", "dunkelheit", "finsternis", "schwarz", "licht", "hell",
        "leuchtet", "schimmer", "funke", "glimmt", "erloschen", "ausgegangen",
        "blind", "sehen", "übersehen", "blendet",
    },
}

METAPHER_ZU_DOMAENE: dict[str, list[str]] = {}
for _dom, _woerter in METAPHERN_DOMAENEN.items():
    for _w in _woerter:
        METAPHER_ZU_DOMAENE.setdefault(_w, []).append(_dom)
del _dom, _woerter, _w


# ---------------------------------------------------------------------------
# Verneinter Affekt
# ---------------------------------------------------------------------------

NEGATIONS_FENSTER = 3  # Tokens links vom Treffer


# ---------------------------------------------------------------------------
# Beziehungsbegriffe
# ---------------------------------------------------------------------------

BEZIEHUNGS_BEGRIFFE = {
    "mutter", "mama", "mutti", "vater", "papa", "vati", "eltern",
    "schwester", "bruder", "geschwister", "oma", "opa", "grossmutter",
    "großmutter", "grossvater", "großvater", "tante", "onkel", "cousine",
    "cousin", "nichte", "neffe",
    "frau", "mann", "partner", "partnerin", "freund", "freundin", "freunde",
    "ehemann", "ehefrau", "ex", "verlobte", "verlobter",
    "sohn", "tochter", "kind", "kinder", "baby",
    "chef", "chefin", "vorgesetzter", "vorgesetzte", "kollege", "kollegin",
    "kollegen", "nachbar", "nachbarin", "arzt", "ärztin", "lehrer", "lehrerin",
    "therapeut", "therapeutin", "hausarzt", "schwiegermutter", "schwiegervater",
    "schwägerin", "schwager", "stiefvater", "stiefmutter",
}
