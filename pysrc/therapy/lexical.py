"""Korpuswerkzeuge — die Brücke zurück zum nahen Lesen.

Ohne dieses Modul wäre Thera.py ein Dashboard. Mit ihm ist jede Zahl eine
Adresse: Konkordanz, Kollokationen, Keyness, Komposita, Type-Token.

Nicht verhandelbar und deshalb hier an einer Stelle gebündelt: **jede
aggregierte Zahl muss zu den Zeilen zurückführen, die sie erzeugt haben.**

**Zur Zweisprachigkeit.** Ein Index gehört zu einem Klienten, und ein Klient
kann seine Sitzungen in beiden Sprachen haben — ein Umzug, ein Wechsel der
Behandlungssprache, eine Vertretung. Deshalb wird jede Sitzung mit *ihrer*
Sprache tokenisiert und lemmatisiert, und der Index merkt sich, welche
Sprachen in ihm vorkommen.

Zwei Folgen daraus, die beide sichtbar sind statt still:

* Gefiltert wird gegen die **Vereinigung** der Stoppwortlisten aller
  vorkommenden Sprachen. Sonst stünde in der Keyness-Liste eines englischen
  Klienten „und“ ganz oben, nur weil die deutsche Referenz es kennt und die
  englische Filterliste es nicht.
* **Keyness zwischen Klienten verschiedener Sprachen ist wertlos.** Sie
  misst dann den Sprachunterschied und sonst nichts. ``report.py`` rechnet
  sie deshalb nur gegen Klienten derselben Sprache.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from . import sprachen
from .ingest import KLIENT, THERAPEUT, Sitzung
from .lexika import emotion as lex_emo
from .tokenize import Token, tokenisiere, typ_token_verhaeltnis, zerlege_kompositum


# Grundwortschatz für die Kompositazerlegung. Ohne ihn findet die Zerlegung
# „Verlustangst“ nur dann, wenn „Verlust“ im selben Korpus auch einmal allein
# vorkommt — und genau das tut es bei den interessanten Wörtern fast nie.
_LEXIKON_VOKABULAR: set[str] = set(lex_emo.KOERPER_AFFEKT) | set(lex_emo.VAGER_AFFEKT)
for _menge in lex_emo.FAMILIEN.values():
    _LEXIKON_VOKABULAR |= set(_menge)
for _menge in lex_emo.METAPHERN_DOMAENEN.values():
    _LEXIKON_VOKABULAR |= set(_menge)
_LEXIKON_VOKABULAR |= set(lex_emo.BEZIEHUNGS_BEGRIFFE)
_LEXIKON_VOKABULAR |= {
    # Häufige Zweitglieder deutscher Affektkomposita, die in keinem der
    # Marker-Lexika als Einzelwort stehen.
    "gefühl", "gefühle", "zustand", "gedanke", "gedanken", "erlebnis", "reaktion",
    "verhalten", "situation", "moment", "problem", "thema", "muster", "seite",
    "bild", "wort", "worte", "satz", "raum", "zeit", "leben", "alltag", "arbeit",
    "beziehung", "familie", "kindheit", "jugend", "vergangenheit", "zukunft",
    "körper", "kopf", "sache", "stelle", "punkt", "frage", "antwort", "grund",
}
_LEXIKON_VOKABULAR = {w for w in _LEXIKON_VOKABULAR if w.isalpha() and len(w) >= 4}


@dataclass(slots=True)
class Stelle:
    """Eine Fundstelle im Korpus, so genau wie das Werkzeug es kann."""

    sid: str
    sitzung_nr: int | None
    turn: int
    sprecher: str
    start: int
    end: int

    def als_dict(self) -> dict:
        return {"sid": self.sid, "nr": self.sitzung_nr, "turn": self.turn,
                "sprecher": self.sprecher, "start": self.start, "end": self.end}


class Index:
    """Der durchsuchbare Korpus eines Klienten (oder der ganzen Praxis).

    Wird einmal gebaut und danach für Konkordanz, Kollokationen und Keyness
    wiederverwendet. Die Turn-Texte bleiben im Speicher — das ist der Preis
    dafür, dass jede Zahl anklickbar ist, und er ist es wert.
    """

    def __init__(self, sitzungen: list[Sitzung]) -> None:
        self.sitzungen = sitzungen
        # Welche Sprachen kommen vor, und welche überwiegt. Die überwiegende
        # ist die, in der Suchbegriffe aus der Oberfläche lemmatisiert werden:
        # wer „Angst“ eintippt, meint die deutschen Sitzungen.
        self.sprachen: set[str] = {getattr(s, "sprache", sprachen.STANDARD)
                                   for s in sitzungen} or {sprachen.STANDARD}
        self.sprache: str = _ueberwiegende_sprache(sitzungen)
        self.gemischt: bool = len(self.sprachen) > 1
        self._stoppwoerter: set[str] | None = None
        self.texte: dict[tuple[str, int], str] = {}
        self.tokens: dict[tuple[str, int], list[Token]] = {}
        self.sprecher: dict[tuple[str, int], str] = {}
        self.sitzung_nr: dict[str, int | None] = {}
        # Wortform -> Fundstellen
        self._form_index: dict[str, list[Stelle]] = defaultdict(list)
        self._lemma_index: dict[str, list[Stelle]] = defaultdict(list)
        self.frequenz: dict[str, Counter] = {THERAPEUT: Counter(), KLIENT: Counter()}
        self.lemma_frequenz: dict[str, Counter] = {THERAPEUT: Counter(), KLIENT: Counter()}
        self.gesamt: dict[str, int] = {THERAPEUT: 0, KLIENT: 0}
        # Wortformen, die mindestens einmal gross geschrieben vorkamen.
        # Im Deutschen ist das der einzige verfügbare Substantiv-Hinweis
        # ohne Parser — und Komposita zerlegt man nur bei Substantiven,
        # sonst wird aus „vielleicht“ ein „viel+leicht“.
        self.substantivverdacht: set[str] = set()
        self._baue()

    # -- Aufbau ---------------------------------------------------------
    def _baue(self) -> None:
        for sitzung in self.sitzungen:
            self.sitzung_nr[sitzung.sid] = sitzung.nummer
            pak = sprachen.paket(getattr(sitzung, "sprache", sprachen.STANDARD))
            for turn in sitzung.turns:
                schluessel = (sitzung.sid, turn.idx)
                toks = tokenisiere(turn.text, pak.CODE)
                self.texte[schluessel] = turn.text
                self.tokens[schluessel] = toks
                self.sprecher[schluessel] = turn.sprecher
                if turn.sprecher not in self.frequenz:
                    continue
                for tok in toks:
                    if not tok.ist_wort:
                        continue
                    if (pak.GROSSSCHREIBUNG_IST_SUBSTANTIV
                            and tok.gross_geschrieben and tok.satz_position > 0):
                        self.substantivverdacht.add(tok.klein)
                    stelle = Stelle(sitzung.sid, sitzung.nummer, turn.idx,
                                    turn.sprecher, tok.start, tok.end)
                    self._form_index[tok.klein].append(stelle)
                    lemma = pak.lemma(tok.klein)
                    if lemma != tok.klein:
                        self._lemma_index[lemma].append(stelle)
                    self.frequenz[turn.sprecher][tok.klein] += 1
                    self.lemma_frequenz[turn.sprecher][lemma] += 1
                    self.gesamt[turn.sprecher] += 1

    # -- Sprache --------------------------------------------------------
    def _lemma(self, wort: str) -> str:
        """Lemmatisiert einen Suchbegriff in der überwiegenden Sprache."""
        return sprachen.paket(self.sprache).lemma(wort)

    @property
    def stoppwoerter(self) -> set[str]:
        """Vereinigung der Stoppwortlisten aller im Index vorkommenden Sprachen.

        Die Vereinigung und nicht die der überwiegenden Sprache: bei einem
        gemischten Klienten würde sonst die Frequenzliste der Minderheits-
        sprache von deren Funktionswörtern angeführt.
        """
        if self._stoppwoerter is None:
            menge: set[str] = set()
            for code in self.sprachen:
                menge |= sprachen.paket(code).funktion.STOPPWOERTER
            self._stoppwoerter = menge
        return self._stoppwoerter

    # -- Vokabular ------------------------------------------------------
    def vokabular(self, min_frequenz: int = 1) -> set[str]:
        """Bekannte Wortformen und Lemmata — Grundlage der Kompositazerlegung.

        Der mitgelieferte Grundwortschatz ist deutsch, weil nur das Deutsche
        zerlegt wird. Bei einem rein englischen Index wird die Zerlegung gar
        nicht erst angeworfen, und die Menge bleibt ungenutzt.
        """
        vok: set[str] = set(_LEXIKON_VOKABULAR)
        for counter in list(self.frequenz.values()) + list(self.lemma_frequenz.values()):
            vok |= {w for w, n in counter.items() if n >= min_frequenz and w.isalpha()}
        return vok

    # -- Konkordanz -----------------------------------------------------
    def kwic(self, begriff: str, sprecher: str | None = None,
             breite: int = 55, grenze: int = 300, lemma: bool = True) -> list[dict]:
        """Keyword in Context über alle Sitzungen.

        Sucht erst die Wortform, dann — wenn ``lemma`` — auch flektierte
        Formen mit demselben groben Lemma. Die Trefferliste sagt dazu, welche
        Form gefunden wurde, damit man der Lemmatisierung nicht blind
        vertrauen muss.
        """
        begriff = begriff.strip().lower()
        if not begriff:
            return []
        stellen: list[Stelle] = list(self._form_index.get(begriff, []))
        if lemma:
            gesehen = {(s.sid, s.turn, s.start) for s in stellen}
            for s in self._lemma_index.get(self._lemma(begriff), []):
                if (s.sid, s.turn, s.start) not in gesehen:
                    stellen.append(s)
        if " " in begriff:
            stellen = self._phrasensuche(begriff)

        stellen = [s for s in stellen if sprecher is None or s.sprecher == sprecher]
        stellen.sort(key=lambda s: (s.sitzung_nr or 0, s.turn, s.start))

        zeilen: list[dict] = []
        for s in stellen[:grenze]:
            text = self.texte[(s.sid, s.turn)]
            links = text[max(0, s.start - breite): s.start]
            rechts = text[s.end: s.end + breite]
            zeilen.append({
                **s.als_dict(),
                "links": ("…" if s.start - breite > 0 else "") + links,
                "treffer": text[s.start:s.end],
                "rechts": rechts + ("…" if s.end + breite < len(text) else ""),
            })
        return zeilen

    def _phrasensuche(self, phrase: str) -> list[Stelle]:
        muster = re.compile(r"\b" + re.escape(phrase) + r"\b")
        gefunden: list[Stelle] = []
        for (sid, turn), text in self.texte.items():
            for m in muster.finditer(text.lower()):
                gefunden.append(Stelle(sid, self.sitzung_nr.get(sid), turn,
                                       self.sprecher[(sid, turn)], m.start(), m.end()))
        return gefunden

    def turn_text(self, sid: str, turn: int) -> str:
        return self.texte.get((sid, turn), "")

    def ausschnitt(self, sid: str, turn: int, start: int, end: int,
                   breite: int = 90) -> dict:
        """Textausschnitt um eine Stelle — für den Sprung aus einer Zahl heraus."""
        text = self.texte.get((sid, turn), "")
        a, b = max(0, start - breite), min(len(text), end + breite)
        return {
            "sid": sid, "turn": turn, "sprecher": self.sprecher.get((sid, turn), "?"),
            "links": ("…" if a > 0 else "") + text[a:start],
            "treffer": text[start:end],
            "rechts": text[end:b] + ("…" if b < len(text) else ""),
            "voll": text,
        }

    # -- Kollokationen --------------------------------------------------
    def kollokationen(self, begriff: str, sprecher: str = KLIENT,
                      fenster: int = 5, min_gemeinsam: int = 3,
                      grenze: int = 30) -> list[dict]:
        """Was sich um ein Wort herum ballt — Log-Likelihood, nicht Rohfrequenz.

        Rohfrequenz liefert bei jedem Suchwort dieselbe Antwort („und“, „die“,
        „ich“). Log-Likelihood beantwortet die eigentliche Frage: welche
        Wörter stehen *häufiger als erwartbar* in der Nähe.
        """
        begriff = begriff.strip().lower()
        ziel_lemma = self._lemma(begriff)
        umfeld: Counter = Counter()
        treffer_anzahl = 0

        pak = sprachen.paket(self.sprache)
        stopp = self.stoppwoerter
        for (sid, turn), toks in self.tokens.items():
            if self.sprecher.get((sid, turn)) != sprecher:
                continue
            worte = [t for t in toks if t.ist_wort]
            formen = [t.klein for t in worte]
            lemmata = [pak.lemma(f) for f in formen]
            for i, form in enumerate(formen):
                if form != begriff and lemmata[i] != ziel_lemma:
                    continue
                treffer_anzahl += 1
                a, b = max(0, i - fenster), min(len(formen), i + fenster + 1)
                for j in range(a, b):
                    if j == i:
                        continue
                    kandidat = formen[j]
                    if kandidat in stopp or len(kandidat) < 3:
                        continue
                    umfeld[kandidat] += 1

        if not treffer_anzahl:
            return []
        gesamt = self.gesamt[sprecher] or 1
        fenster_gesamt = treffer_anzahl * fenster * 2
        ergebnis = []
        for wort, gemeinsam in umfeld.items():
            if gemeinsam < min_gemeinsam:
                continue
            f_wort = self.frequenz[sprecher].get(wort, gemeinsam)
            ll = _log_likelihood(gemeinsam, fenster_gesamt, f_wort, gesamt)
            ergebnis.append({"wort": wort, "gemeinsam": gemeinsam,
                             "gesamt": f_wort, "ll": round(ll, 2)})
        ergebnis.sort(key=lambda e: -e["ll"])
        return ergebnis[:grenze]

    # -- Keyness --------------------------------------------------------
    def keyness(self, referenz: Counter, referenz_gesamt: int,
                sprecher: str = KLIENT, min_frequenz: int = 4,
                grenze: int = 40) -> list[dict]:
        """Was diesen Klienten sprachlich *unterscheidet*, nicht was häufig ist.

        Ohne Referenz ist eine Frequenzliste bei jedem Klienten fast dieselbe.
        Gegen die übrige Fallgeschichte gerechnet wird sie erst interessant.
        """
        ziel = self.lemma_frequenz[sprecher]
        ziel_gesamt = sum(ziel.values()) or 1
        referenz_gesamt = referenz_gesamt or 1
        ergebnis = []
        for wort, f_ziel in ziel.items():
            if f_ziel < min_frequenz or wort in self.stoppwoerter or len(wort) < 3:
                continue
            f_ref = referenz.get(wort, 0)
            ll = _log_likelihood(f_ziel, ziel_gesamt, f_ziel + f_ref,
                                 ziel_gesamt + referenz_gesamt)
            rel_ziel = f_ziel / ziel_gesamt
            rel_ref = f_ref / referenz_gesamt
            richtung = 1 if rel_ziel >= rel_ref else -1
            ergebnis.append({
                "wort": wort, "hier": f_ziel, "referenz": f_ref,
                "ll": round(ll * richtung, 2),
                "faktor": round(rel_ziel / rel_ref, 2) if rel_ref else None,
            })
        ergebnis.sort(key=lambda e: -e["ll"])
        return ergebnis[:grenze]

    # -- Komposita ------------------------------------------------------
    def komposita(self, sprecher: str = KLIENT, grenze: int = 60) -> list[dict]:
        """Zerlegte Komposita mit ihren Teilen.

        „Verlustangst“, „Schuldgefühle“, „Versagensangst“ erscheinen je einmal
        und verschwinden im Langschwanz, wenn man sie nicht aufmacht. Genau
        dort versteckt sich das emotional geladene Vokabular.
        """
        if not any(sprachen.paket(c).KOMPOSITA for c in self.sprachen):
            return []
        vok = self.vokabular(min_frequenz=1)
        ergebnis = []
        for wort, anzahl in self.frequenz[sprecher].items():
            if not self._zerlegbar(wort):
                continue
            teile = zerlege_kompositum(wort, vok)
            if not teile:
                continue
            ergebnis.append({"wort": wort, "anzahl": anzahl, "teile": teile})
        ergebnis.sort(key=lambda e: (-e["anzahl"], e["wort"]))
        return ergebnis[:grenze]

    def _zerlegbar(self, wort: str) -> bool:
        """Nur echte Substantivkandidaten werden zerlegt.

        Ohne diese Bremse liefert die Zerlegung „viel+leicht“ und
        „zwischen+durch“ — formal korrekte Splits, die inhaltlich nichts
        bedeuten und die Liste unbrauchbar machen.
        """
        return (len(wort) >= 9
                and wort in self.substantivverdacht
                and wort not in self.stoppwoerter)

    def teil_frequenzen(self, sprecher: str = KLIENT) -> Counter:
        """Frequenzen *nach* Kompositazerlegung — der eigentliche Zweck der Übung."""
        vok = self.vokabular(min_frequenz=1)
        zerlegen = any(sprachen.paket(c).KOMPOSITA for c in self.sprachen)
        stopp = self.stoppwoerter
        zaehler: Counter = Counter()
        for wort, anzahl in self.frequenz[sprecher].items():
            if wort in stopp or len(wort) < 3:
                continue
            teile = (zerlege_kompositum(wort, vok)
                     if zerlegen and self._zerlegbar(wort) else None)
            if teile:
                for teil in teile:
                    zaehler[teil] += anzahl
            else:
                zaehler[self._lemma(wort)] += anzahl
        return zaehler

    # -- Type-Token -----------------------------------------------------
    def ttr(self, sitzung: Sitzung, sprecher: str, fenster: int = 100) -> dict:
        formen = [
            t.klein
            for turn in sitzung.turns if turn.sprecher == sprecher
            for t in self.tokens.get((sitzung.sid, turn.idx), []) if t.ist_wort
        ]
        return {
            "sttr": round(typ_token_verhaeltnis(formen, fenster), 4),
            "tokens": len(formen),
            "types": len(set(formen)),
            "belastbar": len(formen) >= fenster,
        }

    # -- Neues Vokabular ------------------------------------------------
    def neues_vokabular(self, sitzung: Sitzung, sprecher: str = KLIENT,
                        grenze: int = 40) -> list[str]:
        """Inhaltswörter, die in dieser Sitzung zum ersten Mal auftauchen.

        Bei einem Klienten, dessen Sitzungen die Sprache wechseln, ist die
        erste Sitzung in der neuen Sprache fast vollständig "neues Vokabular".
        Das ist rechnerisch richtig und inhaltlich nichtssagend; ``report.py``
        hängt für diesen Fall eine Warnung an die Sitzungskarte.
        """
        pak = sprachen.paket(getattr(sitzung, "sprache", sprachen.STANDARD))
        vorher: set[str] = set()
        for s in self.sitzungen:
            if s.sid == sitzung.sid:
                break
            vor_pak = sprachen.paket(getattr(s, "sprache", sprachen.STANDARD))
            for turn in s.turns:
                if turn.sprecher != sprecher:
                    continue
                for t in self.tokens.get((s.sid, turn.idx), []):
                    if t.ist_wort:
                        vorher.add(vor_pak.lemma(t.klein))
        neu: Counter = Counter()
        for turn in sitzung.turns:
            if turn.sprecher != sprecher:
                continue
            for t in self.tokens.get((sitzung.sid, turn.idx), []):
                if not t.ist_wort or len(t.text) < 4:
                    continue
                lemma = pak.lemma(t.klein)
                if lemma in vorher or lemma in self.stoppwoerter:
                    continue
                neu[lemma] += 1
        return [w for w, _ in neu.most_common(grenze)]


# ---------------------------------------------------------------------------
# Statistik
# ---------------------------------------------------------------------------

def _log_likelihood(a: int, a_gesamt: int, b: int, b_gesamt: int) -> float:
    """G² für eine 2×2-Tafel (Dunning 1993).

    ``a`` Treffer in Korpus A von ``a_gesamt``, ``b`` in B von ``b_gesamt``.
    Der übliche Kollokations- und Keyness-Test; robuster bei kleinen
    Häufigkeiten als χ², und genau die hat man bei einzelnen Klienten.
    """
    a = max(a, 0)
    b = max(b - a, 0) if b >= a else 0
    n1, n2 = max(a_gesamt, 1), max(b_gesamt - a_gesamt, 1)
    e1 = n1 * (a + b) / (n1 + n2)
    e2 = n2 * (a + b) / (n1 + n2)
    wert = 0.0
    if a > 0 and e1 > 0:
        wert += a * math.log(a / e1)
    if b > 0 and e2 > 0:
        wert += b * math.log(b / e2)
    return 2.0 * wert


def referenzfrequenzen(indizes: list[Index], ausser: Index | None = None,
                       sprecher: str = KLIENT) -> tuple[Counter, int]:
    """Summiert die Lemmafrequenzen aller anderen Klienten — Referenz für Keyness."""
    gesamt: Counter = Counter()
    n = 0
    for idx in indizes:
        if ausser is not None and idx is ausser:
            continue
        gesamt.update(idx.lemma_frequenz[sprecher])
        n += idx.gesamt[sprecher]
    return gesamt, n


def _ueberwiegende_sprache(sitzungen: list[Sitzung]) -> str:
    """Die Sprache, in der die meisten Wörter dieses Klienten gesprochen wurden.

    Nach Wörtern und nicht nach Sitzungen: eine einzelne lange Sitzung wiegt
    mehr als drei kurze, und für die Frage "in welcher Sprache tippt jemand
    hier einen Suchbegriff ein" ist die Textmasse der bessere Anhaltspunkt.
    """
    gewicht: Counter = Counter()
    for sitzung in sitzungen:
        code = getattr(sitzung, "sprache", sprachen.STANDARD)
        gewicht[code] += sum(len(t.text.split()) for t in sitzung.turns)
    if not gewicht:
        return sprachen.STANDARD
    return gewicht.most_common(1)[0][0]
