"""Interventionsmuster — die Therapeutenseite.

**Konfidenz C. Das steht so auch in der Oberfläche.**

Eine regelbasierte Klassifikation therapeutischer Interventionen ist ein
grober Stellvertreter für etwas, das eigentlich annotierte deutsche
Therapieäusserungen und einen trainierten Klassifikator bräuchte. Das ist
echte Arbeit und sie wird hier nicht simuliert.

Was diese Muster trotzdem können: Verhältnisse *zwischen Klienten* zeigen.
Der absolute Anteil "Deutungen" ist nicht belastbar. Der Befund "bei A dreimal
so viele Deutungstreffer wie bei B" ist es eher — derselbe systematische
Fehler liegt auf beiden Seiten und kürzt sich im Vergleich weitgehend heraus.
Genau so ist die Mirror-Ansicht gebaut.

Muster sind reguläre Ausdrücke gegen den kleingeschriebenen Turn-Text.
Reihenfolge zählt: der erste Treffer in KATEGORIEN_REIHENFOLGE gewinnt, damit
ein Turn genau ein Label bekommt.
"""

from __future__ import annotations

# Reihenfolge = Priorität bei Mehrfachtreffern. Spezifisches zuerst.
KATEGORIEN_REIHENFOLGE = [
    "strukturierung",
    "selbstoffenbarung",
    "psychoedukation",
    "deutung",
    "validierung",
    "spiegelung",
    "frage_offen",
    "frage_geschlossen",
    "rueckkanal",
]

# Anzeigenamen in der Oberfläche. Die Oberfläche ist englisch, die Muster
# darüber und das Material darunter sind deutsch — die Schlüssel bleiben
# deshalb deutsch und werden nur hier für die Anzeige übersetzt.
ANZEIGE_NAMEN = {
    "spiegelung": "Reflection",
    "deutung": "Interpretation",
    "frage_offen": "Open question",
    "frage_geschlossen": "Closed question",
    "validierung": "Validation",
    "psychoedukation": "Psychoeducation",
    "selbstoffenbarung": "Self-disclosure",
    "strukturierung": "Structuring",
    "rueckkanal": "Backchannel",
    "sonstiges": "Unclassified",
}

MUSTER: dict[str, list[str]] = {
    # ------------------------------------------------------------------
    "spiegelung": [
        r"\bsie sagen\b", r"\bsie sagten\b", r"\bsie meinen\b", r"\bsie beschreiben\b",
        r"\bwenn ich sie richtig verstehe\b", r"\bhabe ich sie richtig verstanden\b",
        r"\bdas klingt (nach|als|so)\b", r"\bes klingt\b", r"\bich höre (da|heraus)\b",
        r"\bsie fühlen sich\b", r"\bsie erleben\b", r"\bsie spüren\b",
        r"\balso war da\b", r"\bda war (also )?\b.{0,30}\bgefühl\b",
        r"\bsie haben gerade\b", r"\bich fasse (das )?(mal )?zusammen\b",
        r"\bmit anderen worten\b", r"\bin ihren worten\b",
        r"\bsie nennen das\b", r"\bsie sprechen von\b",
    ],
    # ------------------------------------------------------------------
    "deutung": [
        r"\bkönnte es sein,? dass\b", r"\bvielleicht hat das (auch )?(damit )?(etwas |was )?zu tun\b",
        r"\bich frage mich,? ob\b", r"\bdas erinnert (mich )?an\b",
        r"\bhängt (das )?(womöglich|vielleicht) (damit )?zusammen\b",
        r"\bals (ob|wäre|wenn)\b.{0,40}\b(früher|damals|kind|mutter|vater)\b",
        r"\bda(s)? scheint\b", r"\bmein eindruck ist\b", r"\bich habe den eindruck\b",
        r"\bvielleicht ist das (ja )?(auch )?ein\b", r"\bmöglicherweise\b.{0,40}\bmuster\b",
        r"\bdas könnte (ein|eine|damit)\b", r"\bkennen sie das (aus|von)\b",
        r"\bwie damals\b", r"\bwie bei ihr(em|er)\b",
        r"\bda wiederholt sich\b", r"\bein muster\b", r"\bdas gleiche muster\b",
        r"\bschutz\b.{0,30}\bfunktion\b", r"\bwozu\b.{0,20}\bgut\b",
    ],
    # ------------------------------------------------------------------
    "validierung": [
        r"\bdas ist (sehr )?(gut )?(verständlich|nachvollziehbar|menschlich)\b",
        r"\bkann ich (gut )?(gut )?(nachvollziehen|verstehen)\b",
        r"\bkein wunder\b", r"\bdas darf (auch )?(so )?sein\b",
        r"\bda(s)? ist völlig in ordnung\b", r"\bdas ist okay\b",
        r"\bjede(r|s)? würde\b", r"\bdas (ist|war) viel\b",
        r"\bsie dürfen\b", r"\bsie müssen (das )?nicht\b",
        r"\bdas haben sie (gut|mutig)\b", r"\bdas ist mutig\b",
        r"\bich finde es bemerkenswert\b", r"\brespekt\b",
        r"\bdanke,? dass sie (das )?(mir )?(erzählen|sagen|teilen)\b",
    ],
    # ------------------------------------------------------------------
    "psychoedukation": [
        r"\bdas nennt man\b", r"\bman nennt das\b", r"\bdafür gibt es einen (begriff|namen)\b",
        r"\bviele menschen\b", r"\bdas (ist|kommt) (sehr )?häufig\b",
        r"\btypisch (für|bei)\b", r"\bin (der )?(forschung|studien)\b",
        r"\bman weiss (heute|inzwischen)\b", r"\bman weiß (heute|inzwischen)\b",
        r"\bunser (gehirn|nervensystem|körper)\b", r"\bdas vegetative nervensystem\b",
        r"\bstressreaktion\b", r"\bkampf oder flucht\b",
        r"\bwas dabei passiert,? ist\b", r"\bich erkläre (ihnen )?(kurz|mal)\b",
        r"\bdas funktioniert so\b",
    ],
    # ------------------------------------------------------------------
    "selbstoffenbarung": [
        r"\bich selbst\b", r"\bbei mir (ist|war|geht)\b", r"\bmir geht es\b",
        r"\bich merke bei mir\b", r"\bich spüre (gerade|jetzt|bei mir)\b",
        r"\bich bin (gerade )?(berührt|bewegt|irritiert|ratlos)\b",
        r"\bmir fällt (gerade )?auf,? dass ich\b", r"\bich kenne das\b",
        r"\bals ich\b.{0,30}\bwar,? (habe|hatte) ich\b",
        r"\bich muss zugeben\b", r"\behrlich gesagt\b.{0,20}\bich\b",
    ],
    # ------------------------------------------------------------------
    "strukturierung": [
        r"\blassen sie uns\b", r"\bwir haben noch\b", r"\bunsere zeit\b",
        r"\bwir sind (gleich )?(am ende|fertig)\b", r"\bzum schluss\b",
        r"\bfür heute\b", r"\bnächste(s)? mal\b", r"\bbeim (letzten|nächsten) mal\b",
        r"\bletzte woche hatten wir\b", r"\bwo waren wir\b",
        r"\bich möchte (ihnen )?vorschlagen\b", r"\bich schlage vor\b",
        r"\bwollen wir\b", r"\bdürfen wir (da )?(noch )?bleiben\b",
        r"\bbevor wir weitergehen\b", r"\bich unterbreche sie\b",
        r"\bkommen wir (nochmal )?zurück\b", r"\bhausaufgabe\b",
        r"\bbis (zum )?nächsten (mal|termin)\b", r"\btermin\b",
    ],
    # ------------------------------------------------------------------
    # Offene Fragen: W-Frage oder ausdrückliche Einladung.
    # "warum" steht bewusst dabei, obwohl es klinisch oft als geschlossene
    # Rechtfertigungsfrage wirkt — die Unterscheidung trifft der Therapeut,
    # nicht das Werkzeug.
    "frage_offen": [
        r"(^|[.?!]\s*)(wie|was|wann|wo|warum|wieso|weshalb|wer|wodurch|inwiefern|woran|wobei|wovon|womit)\b[^?]*\?",
        r"\berzählen sie\b", r"\bbeschreiben sie\b", r"\bmögen sie (mir )?erzählen\b",
        r"\bwas fällt ihnen\b", r"\bwas geht (ihnen )?(gerade )?(durch den kopf|vor)\b",
        r"\bwie ist das für sie\b", r"\bwas macht das mit ihnen\b",
        r"\bwo (spüren|merken) sie das\b", r"\bwie war das\b",
        r"\bmehr dazu\b\?", r"\bund dann\?",
    ],
    # ------------------------------------------------------------------
    # Geschlossene Fragen: Verberstfrage, Tag-Frage, Ja/Nein-Einladung.
    "frage_geschlossen": [
        r"(^|[.?!]\s*)(ist|sind|war|waren|haben|hat|hatten|können|könnten|wollen|wollten|würden|werden|dürfen|darf|soll|sollen|muss|müssen|gibt|geht|kommt|stimmt|finden|glauben|denken|meinen|kennen|fühlen)\s+(sie|es|das|der|die|ihr|ihnen|man)\b[^?]*\?",
        r"\b(oder)\?\s*$", r"\bnicht wahr\?", r"\brichtig\?\s*$", r"\bstimmt('s| das)?\?",
        r"\bja\?\s*$", r"\bja oder nein\b",
        r"\bhaben sie\b[^?]*\?", r"\bwaren sie\b[^?]*\?",
    ],
    # ------------------------------------------------------------------
    "rueckkanal": [
        r"^(mhm|hm+|aha|ach so|achso|ja|jaja|ja ja|genau|okay|ok|verstehe|klar|gut|richtig|stimmt)[.!,\s]*$",
        r"^(mhm[,.\s]*){1,3}$",
    ],
}

# Merkmale, die für die Idiolekt-Analyse (§5.7, "sagt er allen dasselbe?")
# ausgeschlossen werden — reine Höflichkeitsformeln sind keine Formeln im
# interessanten Sinn.
IDIOLEKT_AUSSCHLUSS = {
    "guten tag", "guten morgen", "auf wiedersehen", "schönen tag",
    "bis nächste woche", "bitte sehr", "gern geschehen", "kommen sie rein",
    "nehmen sie platz", "wie geht es ihnen", "wie geht es ihnen heute",
}

# Untergrenzen für die Idiolekt-Auswertung.
IDIOLEKT_MIN_NGRAMM = 3
IDIOLEKT_MAX_NGRAMM = 6
IDIOLEKT_MIN_KLIENTEN = 2   # Phrase muss bei mindestens so vielen Klienten fallen
IDIOLEKT_MIN_HAEUFIGKEIT = 3
