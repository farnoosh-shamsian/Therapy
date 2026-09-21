"""Wer im Raum ist — das Soziogramm."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import sprachen
from .ingest import KLIENT, Sitzung
from .tokenize import tokenisiere

FENSTER = 8          # Tokens links und rechts für die Temperaturmessung
MIN_NENNUNGEN = 2    # darunter ist es Rauschen


@dataclass
class Person:
    name: str
    art: str                      # "person" | "beziehung"
    nennungen: int = 0
    pro_sitzung: dict[int, int] = field(default_factory=dict)
    familien: Counter = field(default_factory=Counter)
    valenz_summe: float = 0.0
    valenz_n: int = 0
    belege: list[list] = field(default_factory=list)

    @property
    def temperatur(self) -> float:
        """Mittlere Valenz des Affektumfelds, -1 bis +1."""
        return self.valenz_summe / self.valenz_n if self.valenz_n else 0.0

    def als_dict(self) -> dict:
        return {
            "name": self.name,
            "art": self.art,
            "nennungen": self.nennungen,
            "proSitzung": self.pro_sitzung,
            "familien": dict(self.familien.most_common(5)),
            "temperatur": round(self.temperatur, 3),
            "belegZahl": self.valenz_n,
            "belege": self.belege[:5],
        }


def soziogramm(sitzungen: list[Sitzung], platzhalter: list[str],
               nur_sprecher: str = KLIENT) -> dict:
    """Baut Knoten und Kanten über alle Sitzungen."""
    # Beziehungsbegriffe aus *allen* vorkommenden Sprachen.
    gesucht: dict[str, str] = {}
    codes = {getattr(s, "sprache", sprachen.STANDARD) for s in sitzungen}
    for code in codes or {sprachen.STANDARD}:
        for b in sprachen.paket(code).emotion.BEZIEHUNGS_BEGRIFFE:
            gesucht[b] = "beziehung"
    for p in platzhalter:
        gesucht[p.lower()] = "person"

    personen: dict[str, Person] = {}
    kanten: Counter = Counter()
    sitzungsnummern: list[int] = []

    for sitzung in sitzungen:
        nr = sitzung.nummer or 0
        sitzungsnummern.append(nr)
        emo = sprachen.paket(getattr(sitzung, "sprache", sprachen.STANDARD)).emotion
        code = getattr(sitzung, "sprache", sprachen.STANDARD)
        for turn in sitzung.turns:
            if turn.sprecher != nur_sprecher:
                continue
            toks = [t for t in tokenisiere(turn.text, code) if t.ist_wort]
            formen = [t.klein for t in toks]
            im_turn: set[str] = set()

            for i, form in enumerate(formen):
                # Platzhalter sind mehrteilig („Person A“)
                name = None
                if i + 1 < len(formen) and f"{form} {formen[i+1]}" in gesucht:
                    name = f"{form} {formen[i+1]}"
                elif form in gesucht:
                    name = form
                if name is None:
                    continue

                art = gesucht[name]
                anzeige = name.title() if art == "person" else name.capitalize()
                person = personen.setdefault(anzeige, Person(anzeige, art))
                person.nennungen += 1
                person.pro_sitzung[nr] = person.pro_sitzung.get(nr, 0) + 1
                im_turn.add(anzeige)

                a, b = max(0, i - FENSTER), min(len(formen), i + FENSTER + 1)
                for j in range(a, b):
                    if j == i:
                        continue
                    familien = emo.WORT_ZU_FAMILIE.get(formen[j])
                    if not familien:
                        continue
                    for fam in familien:
                        person.familien[fam] += 1
                        person.valenz_summe += emo.VALENZ.get(fam, 0)
                        person.valenz_n += 1
                    if len(person.belege) < 5:
                        person.belege.append(
                            [sitzung.sid, turn.idx, toks[i].start, toks[i].end,
                             formen[j]])

            for a_name in im_turn:
                for b_name in im_turn:
                    if a_name < b_name:
                        kanten[(a_name, b_name)] += 1

    knoten = [p.als_dict() for p in personen.values() if p.nennungen >= MIN_NENNUNGEN]
    knoten.sort(key=lambda k: -k["nennungen"])
    behalten = {k["name"] for k in knoten}
    kantenliste = [
        {"a": a, "b": b, "gewicht": w}
        for (a, b), w in kanten.items()
        if a in behalten and b in behalten and w >= MIN_NENNUNGEN
    ]
    kantenliste.sort(key=lambda k: -k["gewicht"])

    return {
        "knoten": knoten,
        "kanten": kantenliste,
        "sitzungen": sorted(set(sitzungsnummern)),
        "hinweis": (
            "Temperature is the mean valence of the feeling words surrounding each "
            "mention, not a judgement about the relationship. Someone spoken of "
            "with worry reads as cold — worry is negatively valenced and often a "
            "sign of closeness."
        ),
    }


def verlauf(personen: list[dict], sitzungen: list[int]) -> list[dict]:
    """Nennungen pro Person und Sitzung als Reihe."""
    reihen = []
    for p in personen:
        pro = p.get("proSitzung", {})
        reihen.append({
            "name": p["name"],
            "art": p["art"],
            "werte": [pro.get(nr, pro.get(str(nr), 0)) for nr in sitzungen],
        })
    return reihen


def eintritte_und_abgaenge(reihen: list[dict], sitzungen: list[int]) -> dict:
    """Wann taucht jemand zum ersten Mal auf."""
    eintritt, abgang = [], []
    for reihe in reihen:
        werte = reihe["werte"]
        nicht_null = [i for i, w in enumerate(werte) if w]
        if not nicht_null:
            continue
        erste, letzte = nicht_null[0], nicht_null[-1]
        if erste > 0:
            eintritt.append({"name": reihe["name"], "sitzung": sitzungen[erste]})
        if letzte < len(werte) - 2:
            abgang.append({"name": reihe["name"], "sitzung": sitzungen[letzte]})
    return {"eintritte": eintritt, "abgaenge": abgang}
