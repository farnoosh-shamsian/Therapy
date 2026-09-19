"""Englische Interventionsmuster — die Therapeutenseite.

**Konfidenz C. Das steht so auch in der Oberfläche.**

Wie im deutschen Modul: eine regelbasierte Klassifikation therapeutischer
Interventionen ist ein grober Stellvertreter für etwas, das annotierte
Äusserungen und einen trainierten Klassifikator bräuchte. Das ist echte
Arbeit und sie wird hier nicht simuliert.

Was diese Muster trotzdem können: Verhältnisse *zwischen Klienten* zeigen.
Der absolute Anteil "Deutungen" ist nicht belastbar. Der Befund "bei A
dreimal so viele Deutungstreffer wie bei B" ist es eher.

**Eine Einschränkung, die nur die englische Seite betrifft**, und die in der
Spiegel-Ansicht ausdrücklich steht: Deutsch siezt, Englisch nicht. Die
deutschen Muster können sich an "Sie"/"Ihnen" festhalten und damit
zuverlässig erkennen, dass der Therapeut über den Klienten spricht. Hier
muss dieselbe Unterscheidung über "you" laufen, das auch generisch und auch
rhetorisch sein kann. Die englische Klassifikation ist deshalb um eine
Nuance unschärfer als die deutsche, obwohl beide Konfidenz C tragen — und
ein Vergleich der Interventionsprofile zwischen einem deutschen und einem
englischen Fall trägt diese Unschärfe zusätzlich.

Muster sind reguläre Ausdrücke gegen den kleingeschriebenen Turn-Text.
Reihenfolge zählt: der erste Treffer in KATEGORIEN_REIHENFOLGE gewinnt,
damit ein Turn genau ein Label bekommt.
"""

from __future__ import annotations

# Reihenfolge = Priorität bei Mehrfachtreffern. Spezifisches zuerst.
# Identisch zur deutschen Reihenfolge, damit die Spiegel-Ansicht bei einem
# gemischten Korpus dieselben Zeilen in derselben Ordnung zeigt.
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

# Anzeigenamen in der Oberfläche. Die Schlüssel bleiben deutsch, weil sie der
# Berichtsvertrag sind und weil dieselbe Kategorie in beiden Sprachen
# dieselbe Zeile füllen muss.
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
        r"\byou say\b", r"\byou said\b", r"\byou mean\b", r"\byou describe\b",
        r"\byou're describing\b", r"\bif i understand you\b",
        r"\bhave i got that right\b", r"\bdid i get that right\b",
        r"\bthat sounds (like|as if|really)\b", r"\bit sounds (like|as if)\b",
        r"\bwhat i('m| am) hearing\b", r"\bi hear (you|that)\b",
        r"\byou feel\b", r"\byou felt\b", r"\byou're feeling\b",
        r"\byou experience\b", r"\byou notice\b",
        r"\bso there was\b", r"\blet me (just )?(reflect|play) (that|it) back\b",
        r"\bin other words\b", r"\bin your words\b", r"\bto put it back\b",
        r"\byou call (it|that)\b", r"\byou talk about\b", r"\bso what you're\b",
        r"\blet me summarise\b", r"\blet me summarize\b",
    ],
    # ------------------------------------------------------------------
    "deutung": [
        r"\bcould it be that\b", r"\bmight (it|that) be\b",
        r"\bi wonder (if|whether)\b", r"\bthat reminds me of\b",
        r"\bdoes (that|this) (perhaps |maybe )?(have (something|anything) to do with|connect)\b",
        r"\bas (if|though)\b.{0,40}\b(back then|childhood|mother|father|a child)\b",
        r"\bthat seems\b", r"\bmy sense is\b", r"\bi have a sense that\b",
        r"\bmy impression is\b", r"\bi get the impression\b",
        r"\bperhaps (this|that) is\b", r"\bmaybe\b.{0,40}\bpattern\b",
        r"\bthat could be (a|an|the)\b", r"\bdo you know (that|this) from\b",
        r"\blike back then\b", r"\blike with your\b",
        r"\bthat repeats\b", r"\b(the|a|that) same pattern\b", r"\ba pattern\b",
        r"\bprotect(s|ed|ing)? you from\b", r"\bwhat (is|was) it for\b",
        r"\bwhat purpose\b", r"\bthere may be a reason\b",
    ],
    # ------------------------------------------------------------------
    "validierung": [
        r"\bthat (makes|made) (complete |perfect |a lot of )?sense\b",
        r"\bthat'?s (very |completely |entirely )?(understandable|human|fair)\b",
        r"\bi can (really |completely )?(understand|see) (that|why)\b",
        r"\bno wonder\b", r"\bof course you\b", r"\bthat'?s allowed\b",
        r"\bthat'?s (completely |perfectly )?(okay|ok|alright|fine)\b",
        r"\banyone would\b", r"\bthat (is|was) a lot\b",
        r"\byou'?re allowed to\b", r"\byou don'?t have to\b",
        r"\bthat (took|takes) (courage|guts)\b", r"\bthat'?s brave\b",
        r"\bi think (that'?s|it'?s) remarkable\b",
        r"\bthank you for (telling|sharing|saying)\b",
        r"\bi'?m glad you (said|told|brought)\b",
    ],
    # ------------------------------------------------------------------
    "psychoedukation": [
        r"\bthere'?s a name for\b", r"\bwe call (that|this)\b",
        r"\bthat'?s called\b", r"\bit'?s called\b",
        r"\ba lot of people\b", r"\bmany people\b", r"\bmost people\b",
        r"\bthat'?s (very |quite )?(common|normal|typical)\b",
        r"\btypical (of|for|in)\b", r"\bin (the )?(research|studies)\b",
        r"\bwe know (now|these days)\b", r"\bwhat we know is\b",
        r"\byour (brain|nervous system|body)\b", r"\bthe nervous system\b",
        r"\bfight or flight\b", r"\bstress response\b",
        r"\bwhat happens (there|then) is\b", r"\blet me explain\b",
        r"\bthe way (this|that) works\b",
    ],
    # ------------------------------------------------------------------
    "selbstoffenbarung": [
        r"\bi myself\b", r"\bfor me (it|that) (is|was)\b",
        r"\bi notice in myself\b", r"\bi('m| am) noticing (in myself|right now)\b",
        r"\bi feel (moved|touched|stuck|at a loss|irritated)\b",
        r"\bi'?m (moved|touched|struck|at a loss)\b",
        r"\bwhat strikes me (is|about)\b",
        r"\bi know (that|this) (feeling|myself)\b", r"\bi'?ve been there\b",
        r"\bwhen i was\b.{0,30}\bi (had|felt|used to)\b",
        r"\bi have to admit\b", r"\bhonestly,? i\b", r"\bto be honest,? i\b",
    ],
    # ------------------------------------------------------------------
    "strukturierung": [
        r"\blet'?s\b", r"\bwe have (about |another |still )?\b.{0,12}\bminutes\b",
        r"\bour time\b", r"\bwe'?re (nearly |almost )?(out of time|done)\b",
        r"\bbefore we (finish|end|stop)\b", r"\bto close\b",
        r"\bfor today\b", r"\bnext time\b", r"\blast (time|week) we\b",
        r"\bwhere were we\b", r"\bwhere did we (get to|leave)\b",
        r"\bi('d like| want) to suggest\b", r"\bcan i suggest\b",
        r"\bshall we\b", r"\bcould we stay (with|there)\b",
        r"\bbefore we move on\b", r"\bcan i (just )?(stop|interrupt) you\b",
        r"\blet'?s come back to\b", r"\bhomework\b",
        r"\buntil next (week|time|session)\b", r"\bappointment\b",
        r"\bsame time next\b",
    ],
    # ------------------------------------------------------------------
    # Offene Fragen: W-Frage oder ausdrückliche Einladung.
    # "why" steht bewusst dabei, obwohl es klinisch oft als geschlossene
    # Rechtfertigungsfrage wirkt — die Unterscheidung trifft der Therapeut,
    # nicht das Werkzeug. Dieselbe Entscheidung wie beim deutschen "warum".
    "frage_offen": [
        r"(^|[.?!]\s*)(what|how|when|where|why|who|which|in what way|to what extent)\b[^?]*\?",
        r"\btell me (about|more|what)\b", r"\bdescribe\b",
        r"\bwould you (tell|say) (me )?more\b", r"\bsay more\b",
        r"\bwhat comes (to mind|up)\b", r"\bwhat'?s going through your\b",
        r"\bwhat'?s that like (for you)?\b", r"\bhow is that for you\b",
        r"\bwhat does that do to you\b", r"\bwhere do you feel (that|it)\b",
        r"\bwhat was that like\b", r"\band then\?", r"\bgo on\b",
    ],
    # ------------------------------------------------------------------
    # Geschlossene Fragen: Verberstfrage, Tag-Frage, Ja/Nein-Einladung.
    "frage_geschlossen": [
        r"(^|[.?!]\s*)(is|are|was|were|do|does|did|have|has|had|can|could|will|would|shall|should|may|might|must)\s+(you|it|that|this|he|she|they|we|there)\b[^?]*\?",
        r"\b(or)\?\s*$", r"\bisn'?t it\?", r"\bdidn'?t (you|it|they)\?",
        r"\bright\?\s*$", r"\bdon'?t you\?", r"\bwasn'?t it\?",
        r"\byeah\?\s*$", r"\byes or no\b", r"\bcorrect\?\s*$",
        r"\bdo you\b[^?]*\?", r"\bwere you\b[^?]*\?", r"\bhave you\b[^?]*\?",
    ],
    # ------------------------------------------------------------------
    "rueckkanal": [
        r"^(mhm+|mm+|hm+|uh[- ]?huh|aha|ah|oh|yeah|yep|yup|yes|right|okay|ok|sure|i see|got it|exactly|indeed|true|quite)[.!,\s]*$",
        r"^(mhm[,.\s]*){1,3}$",
        r"^(right[,.\s]*){1,3}$",
    ],
}

# Merkmale, die für die Idiolekt-Analyse ausgeschlossen werden — reine
# Höflichkeitsformeln sind keine Formeln im interessanten Sinn.
IDIOLEKT_AUSSCHLUSS = {
    "good morning", "good afternoon", "good evening", "see you next week",
    "see you then", "take care", "come on in", "have a seat", "do sit down",
    "how are you", "how are you today", "thanks for coming", "you're welcome",
    "no problem at all", "have a good week",
}

# Untergrenzen für die Idiolekt-Auswertung.
#
# Die n-Gramm-Fenster sind hier um eins grösser als im Deutschen. Englische
# Phrasen sind bei gleichem Inhalt wortreicher — "könnte es sein, dass" sind
# vier Tokens, "could it be that maybe" fünf bis sechs. Mit dem deutschen
# Fenster fiele die Hälfte der englischen Formeln unter den Tisch.
IDIOLEKT_MIN_NGRAMM = 4
IDIOLEKT_MAX_NGRAMM = 7
IDIOLEKT_MIN_KLIENTEN = 2   # Phrase muss bei mindestens so vielen Klienten fallen
IDIOLEKT_MIN_HAEUFIGKEIT = 3
