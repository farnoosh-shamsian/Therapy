"""Erzeugt die synthetischen Beispieltranskripte in ``samples/``."""

from __future__ import annotations

import random
from pathlib import Path

HIER = Path(__file__).parent

# ---------------------------------------------------------------------------
# Satzbausteine
# ---------------------------------------------------------------------------

KLIENT_FRUEH = [
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

KLIENT_MITTE = [
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

KLIENT_SPAET = [
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

# Beiträge, die absichtlich einen Faden legen.
KLIENT_GELADEN = [
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

THERAPEUT_SPIEGELUNG = [
    "If I understand you, there was a feeling you couldn't name.",
    "You say it was just strange. That sounds like more than strange.",
    "You're describing a tightness. Where exactly do you feel it?",
    "So there was anger, and something else behind it.",
    "I hear a tiredness in that which is older than this week.",
    "You talk about a rucksack. What's in it?",
    "You call that functioning. What would the opposite be?",
]

THERAPEUT_OFFEN = [
    "What was that like for you?",
    "What went through your mind in that moment?",
    "Tell me more about that.",
    "What does it do to you to say that here, now?",
    "Where in your body do you feel that?",
    "When did you first have this feeling?",
    "What would you have needed in that moment?",
    "How is it to say it out loud?",
]

THERAPEUT_GESCHLOSSEN = [
    "Was that on Tuesday?",
    "Did you talk to him about it?",
    "Is it often like that?",
    "Were you on your own?",
    "Did she really say it like that?",
    "Can you bear that at the moment?",
]

THERAPEUT_DEUTUNG = [
    "Could it be that this has something to do with your mother?",
    "I wonder whether an old pattern is repeating there.",
    "That reminds me of what you said about your father.",
    "Perhaps that functioning had a protective purpose too.",
    "My sense is that you protect yourself by making yourself invisible.",
]

THERAPEUT_VALIDIERUNG = [
    "That makes complete sense.",
    "No wonder you're tired.",
    "That's brave, saying it here.",
    "Thank you for telling me that.",
    "That's allowed to hurt.",
]

THERAPEUT_STRUKTUR = [
    "Let's stay with that a moment longer.",
    "We have another twenty minutes today.",
    "Last time we stopped at your mother.",
    "I'd like to suggest something for the coming week.",
    "We'll have to finish there for today.",
]

THERAPEUT_PSYCHOEDUKATION = [
    "What you're describing is called dissociation; it's a protective response.",
    "A lot of people experience exactly that after an experience like this.",
    "Our nervous system doesn't distinguish between then and now.",
]

# Themenwechsel des Therapeuten.
THERAPEUT_WECHSEL = [
    "How was the rest of the week, work-wise?",
    "Let's come back to sleep for a moment. How is that going?",
    "Last time we talked about your appointments. Did that work out?",
    "It occurs to me — have you sent off the application yet?",
]

THERAPEUT_RUECKKANAL = ["Mhm.", "Yeah.", "Right.", "Mhm, yes.", "I see."]

ERSTE_BEITRAEGE = [
    "Good afternoon. How are you today?",
    "Good to see you. Where would you like to start?",
    "Come on in. What's on your mind this week?",
]

FADEN_ANTWORT = "Yeah. Um. Sleep is okay, I think."
ABSCHLUSS_T = "Let's stop there for today. See you next week."
ABSCHLUSS_K = "Yes. Thank you. See you next week."
KOPF = "# Synthetic transcript — session {nr}, {datum}"
CSV_KOPF = "speaker;text"


# ---------------------------------------------------------------------------
# Der Fall
# ---------------------------------------------------------------------------

KLIENT = "claire"
SITZUNGEN = 12
SPRUNG_AB = 9            # ab hier der eingebaute, absichtlich abrupte Sprung
LABELS = ("Therapist", "Client")
START = (2024, 1, 9)
PRAEFIX = "client"
EINHEIT = "session"

# Gewichtete Pools für den Therapeuten.
THERAPEUTENPOOL = [
    (THERAPEUT_OFFEN, 0.30), (THERAPEUT_SPIEGELUNG, 0.26),
    (THERAPEUT_VALIDIERUNG, 0.14), (THERAPEUT_DEUTUNG, 0.10),
    (THERAPEUT_GESCHLOSSEN, 0.10), (THERAPEUT_STRUKTUR, 0.06),
    (THERAPEUT_PSYCHOEDUKATION, 0.04),
]


# ---------------------------------------------------------------------------
# Aufbau einer Sitzung
# ---------------------------------------------------------------------------

def _phase(nummer: int, gesamt: int) -> str:
    # Absichtlich flach geschnitten:
    if nummer <= max(5, gesamt // 2):
        return "frueh"
    if nummer <= max(7, 2 * gesamt // 3):
        return "mitte"
    return "spaet"


def _klientenpool(phase: str, nummer: int, sprung_ab: int) -> list[str]:
    """Mischung der Pools."""
    if nummer >= sprung_ab:
        return KLIENT_SPAET * 3 + KLIENT_MITTE
    if phase == "frueh":
        return KLIENT_FRUEH * 4 + KLIENT_MITTE
    if phase == "mitte":
        return KLIENT_FRUEH * 2 + KLIENT_MITTE * 2
    return KLIENT_MITTE * 2 + KLIENT_SPAET


def _waehle(pools, rng: random.Random) -> str:
    wurf = rng.random()
    summe = 0.0
    for pool, gewicht in pools:
        summe += gewicht
        if wurf <= summe:
            return rng.choice(pool)
    return rng.choice(pools[0][0])


def sitzung(nummer: int, gesamt: int, rng: random.Random,
            sprung_ab: int = SPRUNG_AB,
            labels: tuple[str, str] = LABELS) -> list[tuple[str, str]]:
    t_label, k_label = labels
    phase = _phase(nummer, gesamt)
    k_pool = _klientenpool(phase, nummer, sprung_ab)

    zeilen: list[tuple[str, str]] = [(t_label, rng.choice(ERSTE_BEITRAEGE))]
    anzahl = rng.randint(18, 26)
    faden_gelegt = False

    for i in range(anzahl):
        # Klientenbeitrag: ein bis drei Sätze.
        saetze = rng.sample(k_pool, k=min(len(k_pool), rng.choice([1, 1, 2, 2, 3])))
        zeilen.append((k_label, " ".join(saetze)))

        # Ein bis zwei geladene Beiträge pro Sitzung.
        if not faden_gelegt and 4 <= i <= anzahl - 4 and rng.random() < 0.55:
            zeilen.append((k_label, rng.choice(KLIENT_GELADEN)))
            zeilen.append((t_label, rng.choice(THERAPEUT_WECHSEL)))
            zeilen.append((k_label, FADEN_ANTWORT))
            faden_gelegt = True
            continue

        if rng.random() < 0.18:
            zeilen.append((t_label, rng.choice(THERAPEUT_RUECKKANAL)))
            continue
        zeilen.append((t_label, _waehle(THERAPEUTENPOOL, rng)))

    zeilen.append((t_label, ABSCHLUSS_T))
    zeilen.append((k_label, ABSCHLUSS_K))
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
    """Eine Datei im Untertitelformat."""
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

def _datum(start: tuple[int, int, int], woche: int) -> str:
    import datetime
    d = datetime.date(*start) + datetime.timedelta(weeks=woche)
    return d.isoformat()


def main() -> None:
    rng = random.Random(20240911)
    HIER.mkdir(exist_ok=True)
    geschrieben = []

    for nr in range(1, SITZUNGEN + 1):
        zeilen = sitzung(nr, SITZUNGEN, rng)
        datum = _datum(START, nr - 1)
        name = f"{PRAEFIX}-{KLIENT}_{EINHEIT}-{nr:02d}_{datum}"

        # Sitzung 4 als VTT, Sitzung 5 als.
        if nr == 4:
            pfad = HIER / f"{name}.vtt"
            pfad.write_text(als_vtt(zeilen), encoding="utf-8")
        elif nr == 5:
            pfad = HIER / f"{name}.csv"
            pfad.write_text(als_csv(zeilen, CSV_KOPF), encoding="utf-8")
        else:
            pfad = HIER / f"{name}.txt"
            pfad.write_text(als_txt(zeilen, KOPF.format(nr=nr, datum=datum)),
                            encoding="utf-8")
        geschrieben.append(pfad.name)

    (HIER / "MANIFEST.json").write_text(
        __import__("json").dumps(sorted(geschrieben), ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"{len(geschrieben)} synthetische Transkripte geschrieben (en).")


if __name__ == "__main__":
    main()
