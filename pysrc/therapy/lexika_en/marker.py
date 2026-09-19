"""Englische Marker-Lexika.

Dieselben Konventionen wie im deutschen Modul:

* Alle Einträge sind **kleingeschrieben** und werden gegen die
  kleingeschriebene Wortform abgeglichen, nicht gegen ein Lemma.
* Mehrwortausdrücke stehen mit einfachem Leerzeichen.
* Jede adaptierte Liste sagt dazu, woher sie kommt und was bewusst *nicht*
  drin ist.

Ein Unterschied zum Deutschen, der das ganze Modul prägt: das Englische
grammatikalisiert weniger und lexikalisiert mehr. Distanzierung, Irrealis und
Abtönung stehen hier nicht in der Verbmorphologie, sondern in Konstruktionen
und Adverbien. Deshalb sind die Listen hier länger, mehrwortiger und an
mehreren Stellen mehrdeutiger als die deutschen — das ist nicht die
schlechtere Umsetzung derselben Sache, sondern dieselbe Sache in einer
Sprache, die sie anders baut.

**Kontraktionen stehen als Vollformen drin** ("don't", "can't", "i'd"). Der
Tokenizer hält sie zusammen, und eine Liste von Vollformen ist ehrlicher als
eine Expansionsregel, der man ansieht, dass sie rät.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Generische Referenz statt "I"
# ---------------------------------------------------------------------------
#
# Das englische Gegenstück zum deutschen "man" — und die Stelle, an der die
# beiden Sprachen am weitesten auseinanderliegen.
#
# Deutsch hat mit "man" ein eigenes, unmissverständliches Pronomen. Englisch
# hat "one", aber das ist in der gesprochenen Sprache praktisch tot und klingt
# dort, wo es doch vorkommt, gestelzt. Die Arbeit macht stattdessen das
# generische "you": "you just feel awful and there's nothing you can do."
# Das ist exakt dieselbe Bewegung aus der ersten Person heraus — nur ohne
# eigene Form.
#
# Und genau daher kommt das Problem: dasselbe "you" ist in einer
# Therapiestunde meistens die *Anrede* des Gegenübers. Ohne Auflösung wäre die
# Zahl wertlos. Deshalb steht unten ein Filter (GENERISCH_AUSNAHMEN, angewandt
# in sprachen/en.py), der die offensichtlichen Anreden entfernt: Fragen,
# direkte Rückfragen an den Therapeuten und die erstarrte Diskursformel
# "you know".
#
# Das bleibt eine Heuristik, und sie ist in der Oberfläche als Konfidenz B
# ausgewiesen — eine Stufe unter dem deutschen "man", das dort A trägt. Die
# Zahl trägt als *Verlauf über Sitzungen*: der systematische Fehler ist über
# die Sitzungen konstant und kürzt sich in der Trajektorie heraus. Als
# absolute Häufigkeit trägt sie nicht.

GENERISCH_PRONOMEN = {
    "you", "one", "people", "everybody", "everyone", "folks",
}

# Bewusst ausgeschlossen, obwohl sie generisch gebraucht werden *können*.
# Diese Liste ist Teil der Methode, nicht ein Rest.
#
# "they", "someone", "anybody" sind in einem Therapietranskript weit
# überwiegend konkrete Referenz auf Menschen, die in der Erzählung vorkommen —
# und genau die zählt das Soziogramm schon, an der richtigen Stelle und mit
# der richtigen Bedeutung. Sie hier noch einmal als Distanzierung zu zählen,
# würde jeden Klienten, der viel von anderen erzählt, distanziert aussehen
# lassen. Das ist der englische Gegenpart zur deutschen Entscheidung, die
# obliquen man-Formen ("einem", "einen") aus der Hauptquote zu lassen.
GENERISCH_AUSGESCHLOSSEN = {
    "they", "them", "somebody", "someone", "anybody", "anyone",
}

# Erstarrte Formeln mit "you", die keine generische Referenz sind. "You know"
# ist ein Diskursmarker und steht unten in HECKEN, nicht hier.
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
#
# Deutsch macht das morphologisch (Konjunktiv II, Umlaut), Englisch
# periphrastisch. Die Trennung "eindeutig / formgleich" ist deshalb eine
# andere als im deutschen Modul, aber sie ist aus demselben Grund nötig:
#
#   eindeutig    "would have", "could have", "if I were", "I wish"
#                → kontrafaktisch, keine zweite Lesart
#   mehrdeutig   bloßes "would", "could", "might"
#                → Höflichkeit ("would you"), Gewohnheit in der Vergangenheit
#                  ("every summer we would drive down"), Fähigkeit ("I could
#                  swim back then"). Ohne Parser nicht auflösbar.
#
# Wie im Deutschen wandert die mehrdeutige Gruppe in eine eigene Zahl, statt
# die Hauptzahl stillschweigend aufzublähen.

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
#
# Wie im Deutschen: als Muster, nicht als Wortliste. Die Konstruktion trägt
# die Bedeutung. Englisch baut das mit "should have" und "wish", wo das
# Deutsche "hätte … sollen" und "wenn ich nur" hat — dieselbe Handvoll
# Konstruktionen, andere Bauteile.

REGRET_MUSTER = [
    # "I should have said something earlier"
    (r"\bi should(?:'ve| have)\b", "I should have"),
    (r"\bshould(?:'ve| have)\b.{0,30}?\b(said|done|gone|left|told|asked|stayed|known|seen)\b",
     "should have + verb"),
    (r"\bi shouldn'?t have\b|\bi should not have\b", "I shouldn't have"),
    (r"\bi could(?:'ve| have)\b", "I could have"),
    (r"\bi would(?:'ve| have)\b.{0,40}?\bif\b", "I would have … if"),
    # "if only I had", "if I had just"
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
# 4. Abtönung — was im Deutschen die Modalpartikeln tragen
# ---------------------------------------------------------------------------
#
# Hier steht die interessanteste Asymmetrie der beiden Lexika.
#
# Das Deutsche hat eine geschlossene Klasse von Modalpartikeln ("halt", "eben",
# "doch", "ja", "nur"), die im Mittelfeld sitzen und Haltung tragen. Das
# Englische hat diese Klasse nicht. Es macht dieselbe Arbeit mit Adverbien,
# Tags und ganzen Formeln — verteilter, wortreicher, aber funktional an
# derselben Stelle im Satz.
#
# Deshalb sind die Gruppen absichtlich **dieselben vier** wie im deutschen
# Modul: ein gemischtes Korpus zeigt damit dieselbe Zeile in derselben Kurve.
# Was jeweils gezählt wird, steht in der Oberfläche daneben und ist
# ausdrücklich nicht dasselbe Wortmaterial.
#
# Dieselbe bekannte Schwäche wie im Deutschen, offen benannt: "just", "really"
# und "anyway" haben alle eine nicht-abtönende Lesart. Ohne Parser ist das
# nicht sauber zu trennen; die Zahlen sind als Profil über die Zeit zu lesen,
# nicht als absolute Häufigkeit.

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

# "Right?" als Rückversicherung am Turn-Ende ist Abtönung. "Right." als
# Antwort ist es nicht — derselbe Positionsfilter wie im Deutschen bei "ja".
PARTIKEL_POSITION_AUSNAHMEN = {"right", "really", "actually", "just", "obviously"}


# ---------------------------------------------------------------------------
# 5. Absolutismen
# ---------------------------------------------------------------------------
#
# Hier ist das Instrument zu Hause: Al-Mosaiwi & Johnstone (2018), "In an
# Absolute State", ist eine englische Wortliste für englisches Material. Die
# deutsche Fassung in ``lexika/marker.py`` musste sie übersetzen und dabei
# zwei Dinge reparieren. Eines davon muss hier trotzdem repariert werden, und
# das ist eine Behauptung über die Vorlage, nicht über die Übersetzung:
#
#   Die Originalliste enthält Intensivierer ("totally", "completely",
#   "absolutely"). Sie wurde an *geschriebenen* Forenbeiträgen validiert. In
#   gesprochener Therapiesprache sind genau diese Wörter Umgangssprache —
#   "I was totally fine", "that's completely normal" — und kein
#   absolutistisches Denken. Sie stehen unten in AUSGESCHLOSSEN und werden als
#   Intensivierer geführt, symmetrisch zur deutschen Entscheidung.
#
#   Das ist der einzige Punkt, an dem dieses Werkzeug seiner Vorlage
#   widerspricht, und es tut es in beiden Sprachen auf dieselbe Weise.
#
# Deontische Modalität bekommt wie im Deutschen eine eigene Gruppe (ZWANG),
# statt die Absolutismen aufzublähen.
#
# Stufe 1 = quantifizierend/temporal absolut, der belastbare Kern.
# Stufe 2 = graduell absolut, schwächer, separat ausgewiesen.

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

# Bewusst ausgeschlossen. Diese Liste ist Teil der Methode, nicht ein Rest.
ABSOLUT_AUSGESCHLOSSEN = {
    "totally", "completely", "absolutely", "literally", "super", "way",
    "insanely", "crazy", "madly", "ridiculously", "massively", "hugely",
    "terribly", "awfully", "horribly", "dead", "pretty", "quite", "rather",
    "fairly", "real", "proper",
}

# Deontischer Zwang — eigene Kategorie, nicht Absolutismus.
#
# Anders als im Deutschen ist das hier überwiegend periphrastisch ("have to",
# "supposed to"), und "got to"/"gotta" ist in gesprochener Sprache die
# häufigste Form von allen. Eine Liste ohne sie würde am Material vorbeizählen.
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
#
# Steigt unter Bedrohung, in der Nähe von Brüchen und rund um Vermiedenes.
# Im Englischen fällt hier deutlich mehr Material an als im Deutschen, weil
# "you know", "I mean" und "I guess" als Diskursmarker extrem frequent sind.
# Das hebt das Niveau der Zahl gegenüber dem deutschen Gegenstück spürbar an
# — ein weiterer Grund, warum die Raten zwischen den Sprachen nicht direkt
# verglichen werden dürfen und die Oberfläche das auch sagt.
#
# "like" ist bewusst **nicht** drin: als Diskursmarker ("it was like, awful")
# ist es eine Hecke, als Verb ("I like her") und als Präposition ("like my
# mother") ist es keine, und die drei Lesarten sind ohne Parser etwa gleich
# häufig. Lieber der verpasste Treffer als die verdorbene Zahl. Dieselbe
# Entscheidung wie bei "ganz" auf der deutschen Seite.

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
#
# Auch das ein englisches Original (Pennebaker-Linie, LIWC-Kategorien "causal"
# und "insight"). Der Anstieg beider über eine Therapie hinweg gehört zu den
# besser replizierten sprachlichen Befunden überhaupt — und im Gegensatz zu
# fast allem anderen hier ist die *englische* Fassung dieser Listen die
# validierte und die deutsche die adaptierte. Das steht so auch in der
# Oberfläche.

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
#
# Grübeln lebt in der Vergangenheit, Angst in der Zukunft. Die
# Tempusverteilung kommt aus sprachen/en.py (Hilfsverb- und
# Partizip-Heuristik), die Adverbien von hier.

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
#
# Kontraktionen als Vollformen, weil der Tokenizer sie zusammenhält und weil
# "don't" in gesprochenem Englisch die Normalform ist und "do not" die
# Ausnahme. Eine Liste, die nur "not" kennt, zählt an der Sprache vorbei.

NEGATION = {
    "not", "no", "never", "none", "nobody", "no one", "nothing", "nowhere",
    "neither", "nor", "without",
    "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
    "can't", "cannot", "couldn't", "won't", "wouldn't", "shouldn't",
    "shan't", "mustn't", "haven't", "hasn't", "hadn't", "ain't", "nope",
    "not at all", "no way", "not really", "hardly", "barely", "scarcely",
}

# Präfixe und Suffixe, die eine Eigenschaft verneinen ("unable", "worthless",
# "disconnected"). Mindestlänge wie im Deutschen, sonst fängt man "under",
# "interest" und "mister" mit ein.
NEGATIV_PRAEFIXE = ("un", "dis", "im", "in", "ir", "non", "mis")
NEGATIV_SUFFIXE = ("less",)

# Wörter, die mit einem Negationspräfix *anfangen*, ohne eines zu haben.
# Ohne diese Bremse ist im Englischen jedes zweite Wort "negiert" — die
# Präfixe sind hier viel kürzer und viel häufiger zufällig als im Deutschen,
# und das ist der Grund, warum diese Liste existiert und die deutsche nicht.
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
#
# "I was told", "it was done to me", "I got left behind". Dinge, die dem
# Selbst geschehen.
#
# Zwei Dinge sind hier schwerer als im Deutschen, und beide stehen in der
# Oberfläche als Einschränkung:
#
#   (a) Das deutsche Passiv hat mit "werden" ein eigenes Hilfsverb. Das
#       englische benutzt "be", und "be + -ed" ist zwischen Passiv ("I was
#       told") und prädikativem Adjektiv ("I was tired") formgleich. Die Liste
#       PARTIZIP_ADJEKTIVISCH unten fängt die häufigsten Adjektive ab; sie ist
#       der wichtigste Einzelteil dieses Abschnitts und bewusst grosszügig.
#       Ohne sie misst die Zahl Befinden statt Agens — und Befinden wird
#       nebenan schon gemessen.
#
#   (b) Dafür hat das Englische das get-Passiv ("I got fired", "I got left"),
#       das in gesprochener Sprache häufiger ist als das be-Passiv und im
#       Deutschen kein direktes Gegenstück hat. Es wird mitgezählt.

PASSIV_HILFSVERB = {
    "was", "were", "is", "are", "am", "been", "being", "be",
    "get", "gets", "got", "gotten", "getting",
    "wasn't", "weren't", "isn't", "aren't",
}

# Unregelmässige Partizipien II. Ohne sie findet die -ed-Regel "I was told"
# und "I was given" nicht, und das sind die klinisch dichtesten Fälle.
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

# Formgleich mit dem Passiv, aber prädikatives Adjektiv. Der wichtigste
# Ausschluss dieses Moduls.
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
# 11. Intensivierer (eigene Spur, nicht Absolutismus)
# ---------------------------------------------------------------------------

INTENSIVIERER = set(ABSOLUT_AUSGESCHLOSSEN) | {
    "very", "so", "really", "extremely", "incredibly", "unbelievably",
    "enormously", "immensely", "deeply", "profoundly", "seriously",
    "genuinely", "downright", "damn", "bloody", "freaking", "so much",
    "such a", "a whole lot", "a hell of a",
}


# ---------------------------------------------------------------------------
# Register — was markers.py abläuft
# ---------------------------------------------------------------------------
#
# Die Schlüssel sind dort, wo beide Sprachen dasselbe messen, absichtlich
# **dieselben wie im deutschen Modul** — sonst hätte ein gemischtes Korpus
# zwei Kurvensätze, die dasselbe heissen und nicht übereinanderliegen.
#
# Wo eine Sprache etwas hat, das die andere nicht hat, bekommt es einen
# eigenen Schlüssel und taucht in der anderen Sprache gar nicht auf:
#
#   nur Deutsch    man, man_ambig, konjunktiv2, konjunktiv2_ambig
#   nur Englisch   generisch, irrealis, irrealis_ambig
#
# ``sprachen/*.py`` deklariert dazu eine Tabelle VERGLEICHBAR, die sagt,
# welches Paar von Schlüsseln denselben Begriff meint. Vergleichbar heisst
# dort ausdrücklich *nicht* gleich, und die Oberfläche sagt das auch.

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
