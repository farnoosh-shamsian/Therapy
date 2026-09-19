"""Erzeugt die synthetischen Beispieltranskripte in ``samples/``.

**In diesem Ordner liegt niemals echtes Klientenmaterial.** Nicht anonymisiert,
nicht geschwärzt, nicht in einem Zweig. Alles hier ist maschinell aus
Satzbausteinen erzeugt und beschreibt keine existierende Person.

Zweck der Beispiele:

* Die Offline-Demonstration braucht Material, das mitgeliefert wird, damit die
  Seite ohne jede Datei des Nutzers etwas zeigen kann.
* Die Marker brauchen einen Verlauf, an dem man sieht, dass die Arc-Ansicht
  und die Wechselpunkterkennung tun, was sie sollen. Der Verlauf ist hier
  absichtlich eingebaut: Distanzierung und Vagheit gehen zurück, Granularität,
  Kausalität und Einsicht steigen, und zwar mit einem Sprung um Sitzung 9.
* Zwei Klienten mit unterschiedlich verhaltendem Therapeuten, damit die
  Spiegel-Ansicht überhaupt etwas zu vergleichen hat.
* **Ein dritter Fall auf Englisch**, damit die Zweisprachigkeit in der Demo
  nicht behauptet, sondern gezeigt wird — mitsamt allem, was daran unbequem
  ist: der Sprachspalte im Befund, der markierten Zeile im Spiegel und der
  leeren Keyness-Liste, weil es keinen zweiten englischen Fall gibt.

Die Satzbänke stehen je Sprache in :data:`BAENKE`. Sie sind **keine
Übersetzungen voneinander**, und das ist der Punkt: der englische Fall zeigt
generisches "you", "should have" und "just", wo der deutsche "man", Konjunktiv
II und "halt" zeigt. Eine übersetzte Bank würde englische Sätze mit deutscher
Statistik erzeugen und die Demo zu einer Lüge machen.

Aufruf:  ``python samples/_generator.py``
"""

from __future__ import annotations

import random
from pathlib import Path

HIER = Path(__file__).parent

# ---------------------------------------------------------------------------
# Satzbausteine, deutsch
# ---------------------------------------------------------------------------
# Drei Phasen. Der Unterschied zwischen ihnen ist das, was die Beispieldaten
# überhaupt nützlich macht — er ist deshalb grob und deutlich, nicht subtil.

DE_KLIENT_FRUEH = [
    "Also, es war irgendwie so eine komische Woche, schwer zu sagen.",
    "Man macht das dann halt einfach, da denkt man nicht drüber nach.",
    "Ich weiß nicht, es war eigentlich ganz okay, nur irgendwie blöd zwischendurch.",
    "Das ist halt so, da kann man nichts machen.",
    "Man funktioniert ja einfach weiter, irgendwie geht das schon.",
    "Es ging mir schlecht, aber frag mich nicht warum, keine Ahnung.",
    "Da wurde mir gesagt, ich soll mich nicht so anstellen.",
    "Ich hab dann halt nichts gesagt, wie immer.",
    "Bei der Arbeit ist immer dasselbe, das ändert sich nie.",
    "Man will ja niemandem zur Last fallen.",
    "Mein Chef hat wieder so einen Ton gehabt, aber gut, das ist normal.",
    "Meine Mutter hat angerufen, das war so wie immer, anstrengend halt.",
    "Ich hätte da eigentlich was sagen sollen, aber ich hab es nicht gemacht.",
    "So eine Art Druck, im Magen irgendwie, aber das ist nichts Besonderes.",
    "Es ist einfach zu viel, alles gleichzeitig, immer.",
    "Markus hat gemeint, ich soll mal Urlaub machen. Als ob das was bringt.",
    "Das war schon okay, nichts Schlimmes, nur eben so.",
    "Ich funktioniere, das reicht ja erst mal.",
    "Manchmal denkt man sich, wozu das alles.",
    "Ich bin dann einfach nach Hause und hab ferngesehen, den ganzen Abend.",
]

DE_KLIENT_MITTE = [
    "Ich habe diese Woche gemerkt, dass ich ziemlich wütend war, richtig sauer.",
    "Es ist mir aufgefallen, dass ich immer sofort nachgebe, wenn meine Mutter anruft.",
    "Da war so eine Enge in der Brust, und ich glaube, das war Angst.",
    "Ich war enttäuscht, weil ich gehofft hatte, dass Markus von selber fragt.",
    "Das hängt vielleicht damit zusammen, dass ich es früher auch schon so gemacht habe.",
    "Ich habe mich geschämt, als ich das gesagt habe, ziemlich sogar.",
    "Ich merke, dass ich mich dann klein mache. Das tue ich, nicht es passiert mir.",
    "Bei meinem Chef spüre ich diese alte Angst, irgendwas falsch zu machen.",
    "Es war traurig, aber auch erleichternd, als sie aufgelegt hat.",
    "Ich habe zum ersten Mal Nein gesagt, und danach ging es mir gut und schlecht gleichzeitig.",
    "Deshalb bin ich so müde, glaube ich. Weil ich ständig aufpasse.",
    "Ich hätte früher nie gedacht, dass ich das mal so klar sehen würde.",
    "Es ist wie ein Rucksack, den ich seit Jahren trage, und ich merke ihn erst jetzt.",
    "Frau Weber aus dem Nachbarbüro hat mich gefragt, wie es mir geht, und ich habe gelogen.",
    "Ich war eifersüchtig, das ist mir unangenehm zu sagen.",
    "Da kam so eine Wut hoch, und dahinter war eigentlich Kränkung.",
    "Ich habe gemerkt, dass ich Angst habe, verlassen zu werden.",
    "Diese Woche war schwer, aber ich weiß jetzt wenigstens, warum.",
]

DE_KLIENT_SPAET = [
    "Ich war wütend, und ich habe es ihm gesagt. Das war neu.",
    "Ich habe gemerkt, dass hinter der Wut meistens Kränkung liegt, und das erklärt einiges.",
    "Mir ist klar geworden, dass ich die Verlustangst von meiner Mutter übernommen habe.",
    "Ich bin traurig darüber, und gleichzeitig erleichtert, dass ich es benennen kann.",
    "Ich habe Markus erzählt, wie es mir wirklich geht. Ich war nervös, aber ich habe es gemacht.",
    "Das Schuldgefühl ist noch da, aber es bestimmt nicht mehr alles.",
    "Ich merke, dass ich mich weniger schäme, wenn ich darüber rede.",
    "Weil ich jetzt verstehe, woher das kommt, macht es mir weniger Angst.",
    "Ich habe meinem Chef widersprochen. Danach war mir schlecht, aber ich war auch stolz.",
    "Es fühlt sich an, als wäre der Rucksack leichter. Nicht weg, aber leichter.",
    "Ich bin dankbar, dass ich das hier sagen kann, ohne mich zu rechtfertigen.",
    "Ich bin einsam gewesen, jahrelang, und ich habe es nie so genannt.",
    "Diese Woche war gut. Nicht perfekt, aber gut, und ich kann das jetzt auch sagen.",
    "Ich spüre die Angst immer noch, aber ich glaube ihr nicht mehr alles.",
    "Ich habe mich geärgert und war zugleich zärtlich gestimmt, das ging beides.",
    "Mir ist aufgefallen, dass ich seit Wochen nicht mehr gesagt habe, es sei egal.",
]

# Beiträge, die absichtlich einen Faden legen, den der Therapeut fallen lässt.
DE_KLIENT_GELADEN = [
    "Als mein Vater gestorben ist, war ich fünfzehn, und ich habe nicht geweint. "
    "Ich habe einfach weiter funktioniert und alle haben gesagt, wie tapfer ich bin. "
    "Ich glaube, ich habe seitdem nie wieder richtig geweint, und das macht mir Angst, "
    "wenn ich ehrlich bin. Es ist, als wäre da eine Tür zu.",
    "Manchmal denke ich, dass ich nie gelernt habe, wie das geht, gemocht zu werden. "
    "Ich habe immer nur gelernt, wie man gebraucht wird. Das ist etwas anderes, und "
    "es macht mich furchtbar müde, und einsam, und ich schäme mich ein bisschen, "
    "dass ich das überhaupt sage.",
    "Es gab da eine Situation mit meiner Schwester, über die ich nie gesprochen habe. "
    "Ich habe sie im Stich gelassen, als sie mich gebraucht hätte, und ich bereue das "
    "bis heute. Wenn ich daran denke, wird mir eng im Hals und ich möchte am liebsten "
    "aufstehen und gehen.",
]

DE_THERAPEUT_SPIEGELUNG = [
    "Wenn ich Sie richtig verstehe, war da ein Gefühl, das Sie nicht benennen konnten.",
    "Sie sagen, es sei irgendwie komisch gewesen. Das klingt nach mehr als komisch.",
    "Sie beschreiben da eine Enge. Wo genau spüren Sie die?",
    "Also war da Ärger, und dahinter noch etwas anderes.",
    "Ich höre da eine Müdigkeit heraus, die älter ist als diese Woche.",
    "Sie sprechen von einem Rucksack. Was ist da drin?",
    "Sie nennen das funktionieren. Was wäre das Gegenteil davon?",
]

DE_THERAPEUT_OFFEN = [
    "Wie war das für Sie?",
    "Was ist Ihnen in dem Moment durch den Kopf gegangen?",
    "Erzählen Sie mir mehr davon.",
    "Was macht das mit Ihnen, wenn Sie das jetzt hier sagen?",
    "Wo im Körper spüren Sie das?",
    "Wann haben Sie dieses Gefühl zum ersten Mal gehabt?",
    "Was hätten Sie gebraucht in dem Moment?",
    "Wie ist es, das auszusprechen?",
]

DE_THERAPEUT_GESCHLOSSEN = [
    "War das am Dienstag?",
    "Haben Sie mit ihm darüber gesprochen?",
    "Ist das öfter so?",
    "Waren Sie da allein?",
    "Hat sie das wirklich so gesagt?",
    "Können Sie das im Moment aushalten?",
]

DE_THERAPEUT_DEUTUNG = [
    "Könnte es sein, dass das etwas mit Ihrer Mutter zu tun hat?",
    "Ich frage mich, ob sich da ein altes Muster wiederholt.",
    "Das erinnert mich an das, was Sie über Ihren Vater erzählt haben.",
    "Vielleicht hat dieses Funktionieren ja auch eine Schutzfunktion gehabt.",
    "Mein Eindruck ist, dass Sie sich schützen, indem Sie sich unsichtbar machen.",
]

DE_THERAPEUT_VALIDIERUNG = [
    "Das ist sehr verständlich.",
    "Kein Wunder, dass Sie müde sind.",
    "Das ist mutig, das hier zu sagen.",
    "Danke, dass Sie mir das erzählen.",
    "Das darf auch wehtun.",
]

DE_THERAPEUT_STRUKTUR = [
    "Lassen Sie uns da noch einen Moment bleiben.",
    "Wir haben heute noch zwanzig Minuten.",
    "Beim letzten Mal waren wir bei Ihrer Mutter stehen geblieben.",
    "Ich möchte Ihnen etwas vorschlagen für die kommende Woche.",
    "Für heute müssen wir leider zum Schluss kommen.",
]

DE_THERAPEUT_PSYCHOEDUKATION = [
    "Was Sie da beschreiben, nennt man Dissoziation, das ist eine Schutzreaktion.",
    "Viele Menschen erleben genau das nach so einer Erfahrung.",
    "Unser Nervensystem unterscheidet nicht zwischen damals und heute.",
]

# Themenwechsel des Therapeuten — erzeugt die verlorenen Fäden.
DE_THERAPEUT_WECHSEL = [
    "Wie war denn sonst die Woche, arbeitsmässig?",
    "Kommen wir noch einmal auf den Schlaf zurück. Wie sieht es damit aus?",
    "Wir haben beim letzten Mal über Ihre Termine gesprochen. Hat das geklappt?",
    "Mir fällt gerade ein: haben Sie den Antrag inzwischen abgeschickt?",
]

DE_THERAPEUT_RUECKKANAL = ["Mhm.", "Ja.", "Hm.", "Mhm, ja.", "Verstehe."]

DE_ERSTE_BEITRAEGE = [
    "Guten Tag. Wie geht es Ihnen heute?",
    "Schön, dass Sie da sind. Womit möchten Sie anfangen?",
    "Kommen Sie rein. Was beschäftigt Sie diese Woche?",
]


# ---------------------------------------------------------------------------
# Satzbausteine, englisch
# ---------------------------------------------------------------------------
#
# Keine Übersetzung der obigen. Dieselbe Bewegung über die Sitzungen hinweg —
# von unbenanntem, distanziertem Sprechen zu benanntem, angeeignetem — aber
# mit den Mitteln, die das Englische dafür hat: generisches "you" statt "man",
# "should have" statt Konjunktiv II, "just" und "anyway" statt "halt" und
# "eben". Wer hier übersetzt hätte, hätte englische Sätze mit deutscher
# Statistik gebaut.

EN_KLIENT_FRUEH = [
    "It was just a strange week, I guess, hard to say really.",
    "You just get on with it, you don't really think about it.",
    "I don't know, it was fine, kind of, just a bit off in places.",
    "It is what it is, there's nothing you can do about it anyway.",
    "You just keep functioning and somehow it works out.",
    "I felt bad, but don't ask me why, I have no idea.",
    "I was told to stop making such a fuss about it.",
    "So I just said nothing, like always.",
    "Work is always the same, it never changes.",
    "You don't want to be a burden to anyone.",
    "My boss had that tone again, but okay, that's normal.",
    "My mother called, it was the same as ever, exhausting really.",
    "I should have said something there, but I just didn't.",
    "Sort of a pressure, in my stomach somehow, but it's nothing much.",
    "It's just too much, all at once, constantly.",
    "Mark said I should take a holiday. As if that would fix anything.",
    "It was okay, nothing terrible, just how it goes.",
    "I function, and that's enough for now.",
    "Sometimes you think, what is all of this even for.",
    "So I just went home and watched telly the whole evening.",
]

EN_KLIENT_MITTE = [
    "I noticed this week that I was really angry, properly furious.",
    "It struck me that I give in immediately whenever my mother calls.",
    "There was this tightness in my chest, and I think that was fear.",
    "I was disappointed, because I'd hoped Mark would ask by himself.",
    "That probably has to do with the fact that I used to do it that way too.",
    "I was ashamed when I said it, quite badly actually.",
    "I notice that I make myself small. I do that, it doesn't happen to me.",
    "With my boss I feel this old fear of getting something wrong.",
    "It was sad, but also a relief, when she hung up.",
    "I said no for the first time, and afterwards I felt good and awful at once.",
    "That's why I'm so tired, I think. Because I'm always on guard.",
    "I would never have thought I'd see it this clearly.",
    "It's like a rucksack I've carried for years, and I only notice it now.",
    "Mrs Whitfield from the next office asked how I was and I lied.",
    "I was envious, which is uncomfortable to say.",
    "This anger came up, and behind it was really hurt.",
    "I realised that I'm afraid of being left.",
    "This week was hard, but at least now I know why.",
]

EN_KLIENT_SPAET = [
    "I was angry, and I told him so. That was new.",
    "I noticed that behind the anger there's usually hurt, and that explains a lot.",
    "It became clear to me that I took the fear of loss from my mother.",
    "I'm sad about it, and relieved at the same time that I can name it.",
    "I told Mark how I actually am. I was nervous, but I did it.",
    "The guilt is still there, but it doesn't decide everything any more.",
    "I notice I'm less ashamed when I talk about it.",
    "Because I understand where it comes from now, it frightens me less.",
    "I disagreed with my boss. Afterwards I felt sick, but I was proud too.",
    "It feels as if the rucksack is lighter. Not gone, but lighter.",
    "I'm grateful I can say this here without having to justify it.",
    "I've been lonely, for years, and I never once called it that.",
    "This week was good. Not perfect, but good, and I can say that now.",
    "I still feel the fear, but I don't believe all of it any more.",
    "I was irritated and tender at the same time, and both were allowed.",
    "It struck me that I haven't said “it doesn't matter” in weeks.",
]

EN_KLIENT_GELADEN = [
    "When my father died I was fifteen, and I didn't cry. I just kept functioning "
    "and everyone said how brave I was. I don't think I've cried properly since, "
    "and that frightens me, if I'm honest. It's as if there's a door shut somewhere.",
    "Sometimes I think I never learned how to be liked. I only ever learned how to "
    "be needed. That's a different thing, and it makes me terribly tired, and "
    "lonely, and I'm a bit ashamed that I'm even saying it.",
    "There was a situation with my sister that I've never talked about. I let her "
    "down when she needed me, and I regret it to this day. When I think about it "
    "my throat goes tight and I want to stand up and leave.",
]

EN_THERAPEUT_SPIEGELUNG = [
    "If I understand you, there was a feeling you couldn't name.",
    "You say it was just strange. That sounds like more than strange.",
    "You're describing a tightness. Where exactly do you feel it?",
    "So there was anger, and something else behind it.",
    "I hear a tiredness in that which is older than this week.",
    "You talk about a rucksack. What's in it?",
    "You call that functioning. What would the opposite be?",
]

EN_THERAPEUT_OFFEN = [
    "What was that like for you?",
    "What went through your mind in that moment?",
    "Tell me more about that.",
    "What does it do to you to say that here, now?",
    "Where in your body do you feel that?",
    "When did you first have this feeling?",
    "What would you have needed in that moment?",
    "How is it to say it out loud?",
]

EN_THERAPEUT_GESCHLOSSEN = [
    "Was that on Tuesday?",
    "Did you talk to him about it?",
    "Is it often like that?",
    "Were you on your own?",
    "Did she really say it like that?",
    "Can you bear that at the moment?",
]

EN_THERAPEUT_DEUTUNG = [
    "Could it be that this has something to do with your mother?",
    "I wonder whether an old pattern is repeating there.",
    "That reminds me of what you said about your father.",
    "Perhaps that functioning had a protective purpose too.",
    "My sense is that you protect yourself by making yourself invisible.",
]

EN_THERAPEUT_VALIDIERUNG = [
    "That makes complete sense.",
    "No wonder you're tired.",
    "That's brave, saying it here.",
    "Thank you for telling me that.",
    "That's allowed to hurt.",
]

EN_THERAPEUT_STRUKTUR = [
    "Let's stay with that a moment longer.",
    "We have another twenty minutes today.",
    "Last time we stopped at your mother.",
    "I'd like to suggest something for the coming week.",
    "We'll have to finish there for today.",
]

EN_THERAPEUT_PSYCHOEDUKATION = [
    "What you're describing is called dissociation; it's a protective response.",
    "A lot of people experience exactly that after an experience like this.",
    "Our nervous system doesn't distinguish between then and now.",
]

EN_THERAPEUT_WECHSEL = [
    "How was the rest of the week, work-wise?",
    "Let's come back to sleep for a moment. How is that going?",
    "Last time we talked about your appointments. Did that work out?",
    "It occurs to me — have you sent off the application yet?",
]

EN_THERAPEUT_RUECKKANAL = ["Mhm.", "Yeah.", "Right.", "Mhm, yes.", "I see."]

EN_ERSTE_BEITRAEGE = [
    "Good afternoon. How are you today?",
    "Good to see you. Where would you like to start?",
    "Come on in. What's on your mind this week?",
]


# ---------------------------------------------------------------------------
# Die Bänke, je Sprache
# ---------------------------------------------------------------------------

BAENKE = {
    "de": {
        "frueh": DE_KLIENT_FRUEH, "mitte": DE_KLIENT_MITTE, "spaet": DE_KLIENT_SPAET,
        "geladen": DE_KLIENT_GELADEN,
        "spiegelung": DE_THERAPEUT_SPIEGELUNG, "offen": DE_THERAPEUT_OFFEN,
        "geschlossen": DE_THERAPEUT_GESCHLOSSEN, "deutung": DE_THERAPEUT_DEUTUNG,
        "validierung": DE_THERAPEUT_VALIDIERUNG, "struktur": DE_THERAPEUT_STRUKTUR,
        "psychoedukation": DE_THERAPEUT_PSYCHOEDUKATION,
        "wechsel": DE_THERAPEUT_WECHSEL, "rueckkanal": DE_THERAPEUT_RUECKKANAL,
        "erste": DE_ERSTE_BEITRAEGE,
        "faden_antwort": "Ja. Ähm. Der Schlaf ist okay, glaube ich.",
        "abschluss_t": "Dann machen wir für heute Schluss. Bis nächste Woche.",
        "abschluss_k": "Ja. Danke. Bis nächste Woche.",
        "kopf": "# Synthetisches Transkript — Sitzung {nr}, {datum}",
        "csv_kopf": "sprecher;text",
    },
    "en": {
        "frueh": EN_KLIENT_FRUEH, "mitte": EN_KLIENT_MITTE, "spaet": EN_KLIENT_SPAET,
        "geladen": EN_KLIENT_GELADEN,
        "spiegelung": EN_THERAPEUT_SPIEGELUNG, "offen": EN_THERAPEUT_OFFEN,
        "geschlossen": EN_THERAPEUT_GESCHLOSSEN, "deutung": EN_THERAPEUT_DEUTUNG,
        "validierung": EN_THERAPEUT_VALIDIERUNG, "struktur": EN_THERAPEUT_STRUKTUR,
        "psychoedukation": EN_THERAPEUT_PSYCHOEDUKATION,
        "wechsel": EN_THERAPEUT_WECHSEL, "rueckkanal": EN_THERAPEUT_RUECKKANAL,
        "erste": EN_ERSTE_BEITRAEGE,
        "faden_antwort": "Yeah. Um. Sleep is okay, I think.",
        "abschluss_t": "Let's stop there for today. See you next week.",
        "abschluss_k": "Yes. Thank you. See you next week.",
        "kopf": "# Synthetic transcript — session {nr}, {datum}",
        "csv_kopf": "speaker;text",
    },
}


# ---------------------------------------------------------------------------
# Aufbau einer Sitzung
# ---------------------------------------------------------------------------

def _phase(nummer: int, gesamt: int) -> str:
    # Absichtlich flach geschnitten: der Verlauf soll *einen* deutlichen
    # Sprung haben (bei ``sprung_ab``), nicht drei. Sonst findet die
    # Wechselpunkterkennung in der Demo überall etwas und zeigt damit
    # genau das, wovor arc.HINWEIS warnt.
    if nummer <= max(5, gesamt // 2):
        return "frueh"
    if nummer <= max(7, 2 * gesamt // 3):
        return "mitte"
    return "spaet"


def _klientenpool(bank: dict, phase: str, nummer: int, sprung_ab: int) -> list[str]:
    """Mischung der Pools. Der Sprung ab ``sprung_ab`` ist absichtlich abrupt."""
    if nummer >= sprung_ab:
        return bank["spaet"] * 3 + bank["mitte"]
    if phase == "frueh":
        return bank["frueh"] * 4 + bank["mitte"]
    if phase == "mitte":
        return bank["frueh"] * 2 + bank["mitte"] * 2
    return bank["mitte"] * 2 + bank["spaet"]


def _therapeutenpool(bank: dict, stil: str) -> list[tuple[list[str], float]]:
    """Gewichtete Pools. ``stil`` unterscheidet die Fälle voneinander — ohne
    diesen Unterschied hätte die Spiegel-Ansicht nichts zu zeigen."""
    if stil == "deutend":
        return [(bank["deutung"], 0.28), (bank["geschlossen"], 0.22),
                (bank["spiegelung"], 0.15), (bank["offen"], 0.15),
                (bank["psychoedukation"], 0.10), (bank["validierung"], 0.05),
                (bank["struktur"], 0.05)]
    return [(bank["offen"], 0.30), (bank["spiegelung"], 0.26),
            (bank["validierung"], 0.14), (bank["deutung"], 0.10),
            (bank["geschlossen"], 0.10), (bank["struktur"], 0.06),
            (bank["psychoedukation"], 0.04)]


def _waehle(pools, rng: random.Random) -> str:
    wurf = rng.random()
    summe = 0.0
    for pool, gewicht in pools:
        summe += gewicht
        if wurf <= summe:
            return rng.choice(pool)
    return rng.choice(pools[0][0])


def sitzung(nummer: int, gesamt: int, rng: random.Random, stil: str,
            sprung_ab: int, labels: tuple[str, str],
            sprache: str = "de") -> list[tuple[str, str]]:
    t_label, k_label = labels
    bank = BAENKE[sprache]
    phase = _phase(nummer, gesamt)
    k_pool = _klientenpool(bank, phase, nummer, sprung_ab)
    t_pools = _therapeutenpool(bank, stil)

    zeilen: list[tuple[str, str]] = [(t_label, rng.choice(bank["erste"]))]
    anzahl = rng.randint(18, 26)
    faden_gelegt = False

    for i in range(anzahl):
        # Klientenbeitrag: ein bis drei Sätze.
        saetze = rng.sample(k_pool, k=min(len(k_pool), rng.choice([1, 1, 2, 2, 3])))
        zeilen.append((k_label, " ".join(saetze)))

        # Ein bis zwei geladene Beiträge pro Sitzung, deren Faden fallen gelassen
        # wird — damit threads.py in der Demo überhaupt etwas findet.
        if not faden_gelegt and 4 <= i <= anzahl - 4 and rng.random() < 0.55:
            zeilen.append((k_label, rng.choice(bank["geladen"])))
            zeilen.append((t_label, rng.choice(bank["wechsel"])))
            zeilen.append((k_label, bank["faden_antwort"]))
            faden_gelegt = True
            continue

        if rng.random() < 0.18:
            zeilen.append((t_label, rng.choice(bank["rueckkanal"])))
            continue
        zeilen.append((t_label, _waehle(t_pools, rng)))

    zeilen.append((t_label, bank["abschluss_t"]))
    zeilen.append((k_label, bank["abschluss_k"]))
    return zeilen


# ---------------------------------------------------------------------------
# Ausgabeformate
# ---------------------------------------------------------------------------

def als_txt(zeilen: list[tuple[str, str]], kopf: str) -> str:
    teile = [kopf, ""]
    for label, text in zeilen:
        teile.append(f"{label}: {text}")
        teile.append("")
    return "\n".join(teile)


def als_vtt(zeilen: list[tuple[str, str]]) -> str:
    """Eine Datei im Untertitelformat, damit die Formaterkennung und die
    zeitabhängigen Kennzahlen in der Demo nicht theoretisch bleiben."""
    teile = ["WEBVTT", ""]
    t = 0.0
    for label, text in zeilen:
        dauer = max(2.0, len(text.split()) / 2.6)
        pause = 0.4 + (2.6 if text.endswith("?") else 0.0)
        teile.append(f"{_zeit(t)} --> {_zeit(t + dauer)}")
        teile.append(f"<v {label}>{text}")
        teile.append("")
        t += dauer + pause
    return "\n".join(teile)


def als_csv(zeilen: list[tuple[str, str]], kopf: str) -> str:
    teile = [kopf]
    for label, text in zeilen:
        teile.append(f'{label};"{text}"')
    return "\n".join(teile)


def _zeit(sekunden: float) -> str:
    stunden = int(sekunden // 3600)
    minuten = int((sekunden % 3600) // 60)
    rest = sekunden % 60
    return f"{stunden:02d}:{minuten:02d}:{rest:06.3f}"


# ---------------------------------------------------------------------------
# Hauptlauf
# ---------------------------------------------------------------------------
#
# Der englische Fall trägt "client"/"session" im Dateinamen statt
# "klient"/"sitzung". Beides erkennt ``ingest.metadaten_aus_name``, und die
# Demo zeigt damit gleich mit, dass die Benennung nicht vorgeschrieben ist.
#
# Die Sprache steht **nicht** im Dateinamen. Das ist Absicht: die Erkennung
# soll in der Demo auch wirklich laufen und im Befund sichtbar werden, statt
# von einem Suffix übersprungen zu werden.

FAELLE = [
    {"klient": "anna", "sitzungen": 12, "stil": "spiegelnd", "sprung_ab": 9,
     "labels": ("Therapeut", "Klientin"), "start": (2024, 1, 11),
     "sprache": "de", "praefix": "klient", "einheit": "sitzung"},
    {"klient": "bernd", "sitzungen": 8, "stil": "deutend", "sprung_ab": 99,
     "labels": ("T", "K"), "start": (2024, 2, 6),
     "sprache": "de", "praefix": "klient", "einheit": "sitzung"},
    {"klient": "claire", "sitzungen": 12, "stil": "spiegelnd", "sprung_ab": 9,
     "labels": ("Therapist", "Client"), "start": (2024, 1, 9),
     "sprache": "en", "praefix": "client", "einheit": "session"},
]


def _datum(start: tuple[int, int, int], woche: int) -> str:
    import datetime
    d = datetime.date(*start) + datetime.timedelta(weeks=woche)
    return d.isoformat()


def main() -> None:
    rng = random.Random(20240911)
    HIER.mkdir(exist_ok=True)
    geschrieben = []

    for fall in FAELLE:
        bank = BAENKE[fall["sprache"]]
        for nr in range(1, fall["sitzungen"] + 1):
            zeilen = sitzung(nr, fall["sitzungen"], rng, fall["stil"],
                             fall["sprung_ab"], fall["labels"], fall["sprache"])
            datum = _datum(fall["start"], nr - 1)
            name = (f"{fall['praefix']}-{fall['klient']}"
                    f"_{fall['einheit']}-{nr:02d}_{datum}")

            # Sitzung 4 als VTT, Sitzung 5 als CSV — die Formatvielfalt gehört
            # zur Demo, weil das echte Material auch nicht einheitlich ist.
            if nr == 4:
                pfad = HIER / f"{name}.vtt"
                pfad.write_text(als_vtt(zeilen), encoding="utf-8")
            elif nr == 5:
                pfad = HIER / f"{name}.csv"
                pfad.write_text(als_csv(zeilen, bank["csv_kopf"]), encoding="utf-8")
            else:
                kopf = bank["kopf"].format(nr=nr, datum=datum)
                pfad = HIER / f"{name}.txt"
                pfad.write_text(als_txt(zeilen, kopf), encoding="utf-8")
            geschrieben.append(pfad.name)

    (HIER / "MANIFEST.json").write_text(
        __import__("json").dumps(sorted(geschrieben), ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"{len(geschrieben)} synthetische Transkripte geschrieben "
          f"({', '.join(sorted({f['sprache'] for f in FAELLE}))}).")


if __name__ == "__main__":
    main()
