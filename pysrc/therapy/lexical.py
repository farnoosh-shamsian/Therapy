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
from .arc import rangkorrelation
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
        # Dasselbe noch einmal je Sitzung. Das ist die Grundlage für alles,
        # was ein Wort über die Zeit betrachtet: Verlauf, steigend/fallend,
        # und Keyness einer Sitzung gegen die übrigen. Ohne diese Zähler lässt
        # sich nur sagen, *dass* ein Wort oft fällt, nicht *wann*.
        self.lemma_je_sitzung: dict[str, dict[str, Counter]] = {}
        self.gesamt_je_sitzung: dict[str, dict[str, int]] = {}
        # Lemma -> die Wortformen, die darauf abgebildet wurden. Der Lemmatisierer
        # ist bewusst grob (kein Parser, keine Modelle), und das war unauffällig,
        # solange Keyness in einer Nebenansicht stand. Als Überschrift einer
        # Wortansicht ist „aufgefall“ schlicht falsch zu lesen — angezeigt wird
        # deshalb die häufigste tatsächlich gesprochene Form, gesucht weiter das
        # Lemma.
        self._formen_je_lemma: dict[str, Counter] = defaultdict(Counter)
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
            je_sitzung = {THERAPEUT: Counter(), KLIENT: Counter()}
            summe = {THERAPEUT: 0, KLIENT: 0}
            self.lemma_je_sitzung[sitzung.sid] = je_sitzung
            self.gesamt_je_sitzung[sitzung.sid] = summe
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
                    je_sitzung[turn.sprecher][lemma] += 1
                    summe[turn.sprecher] += 1
                    self._formen_je_lemma[lemma][tok.klein] += 1

    # -- Anzeige --------------------------------------------------------
    def anzeigeform(self, lemma: str) -> str:
        """Die häufigste gesprochene Form zu einem Lemma.

        Bei Gleichstand gewinnt die kürzere: der Stamm ist meist das, was der
        Lemmatisierer ohnehin gemeint hat.
        """
        formen = self._formen_je_lemma.get(lemma)
        if not formen:
            return lemma
        return min(formen.items(), key=lambda p: (-p[1], len(p[0])))[0]

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
                "wort": wort, "anzeige": self.anzeigeform(wort),
                "hier": f_ziel, "referenz": f_ref,
                "ll": round(ll * richtung, 2),
                "faktor": round(rel_ziel / rel_ref, 2) if rel_ref else None,
                "logRatio": _log_ratio(rel_ziel, rel_ref),
            })
        ergebnis.sort(key=lambda e: -e["ll"])
        return ergebnis[:grenze]

    # -- Keyness ohne zweiten Klienten ----------------------------------
    #
    # Die Referenz war lange die übrige Fallgeschichte. Wer genau einen Fall
    # lädt — und das ist der Normalfall, seit ein langer Text genügt — bekam
    # damit eine leere Liste. Die beiden folgenden Achsen brauchen keinen
    # zweiten Klienten: sie vergleichen den Text mit sich selbst.

    def _zaehler_ueber(self, sids: list[str], sprecher: str) -> tuple[Counter, int]:
        summe: Counter = Counter()
        n = 0
        for sid in sids:
            summe.update(self.lemma_je_sitzung.get(sid, {}).get(sprecher, Counter()))
            n += self.gesamt_je_sitzung.get(sid, {}).get(sprecher, 0)
        return summe, n

    def keyness_sitzung(self, sitzung: Sitzung, sprecher: str = KLIENT,
                        min_frequenz: int = 3, grenze: int = 25) -> list[dict]:
        """Was *diese* Stunde von den übrigen Stunden desselben Falls abhebt.

        Klinisch die interessanteste Keyness-Achse und bis jetzt die einzige,
        die es nicht gab: nicht „wie redet dieser Klient verglichen mit
        anderen“, sondern „wovon war an diesem Tag die Rede und sonst nicht“.
        """
        andere = [s.sid for s in self.sitzungen if s.sid != sitzung.sid]
        if not andere:
            return []
        referenz, referenz_n = self._zaehler_ueber(andere, sprecher)
        ziel = self.lemma_je_sitzung.get(sitzung.sid, {}).get(sprecher, Counter())
        ziel_n = self.gesamt_je_sitzung.get(sitzung.sid, {}).get(sprecher, 0)
        return self._keyness_roh(ziel, ziel_n, referenz, referenz_n,
                                 min_frequenz, grenze)

    def keyness_phase(self, sprecher: str = KLIENT, min_frequenz: int = 4,
                      grenze: int = 25) -> dict:
        """Späte Sitzungen gegen frühe — der Wortschatz der Veränderung.

        Bei ungerader Sitzungszahl fällt die mittlere Sitzung heraus statt
        einer Hälfte zugeschlagen zu werden; sie würde die Kante verwischen,
        die hier gerade interessiert.
        """
        sids = [s.sid for s in self.sitzungen]
        if len(sids) < 4:
            return {"spaet": [], "frueh": [], "genug": False}
        halb = len(sids) // 2
        frueh_ids, spaet_ids = sids[:halb], sids[-halb:]
        frueh, frueh_n = self._zaehler_ueber(frueh_ids, sprecher)
        spaet, spaet_n = self._zaehler_ueber(spaet_ids, sprecher)
        return {
            "spaet": self._keyness_roh(spaet, spaet_n, frueh, frueh_n,
                                       min_frequenz, grenze),
            "frueh": self._keyness_roh(frueh, frueh_n, spaet, spaet_n,
                                       min_frequenz, grenze),
            "genug": True,
            "sitzungenJeHaelfte": halb,
        }

    def _keyness_roh(self, ziel: Counter, ziel_n: int, referenz: Counter,
                     referenz_n: int, min_frequenz: int, grenze: int) -> list[dict]:
        ziel_n = ziel_n or 1
        referenz_n = referenz_n or 1
        ergebnis = []
        for wort, f_ziel in ziel.items():
            if f_ziel < min_frequenz or wort in self.stoppwoerter or len(wort) < 3:
                continue
            f_ref = referenz.get(wort, 0)
            ll = _log_likelihood(f_ziel, ziel_n, f_ziel + f_ref, ziel_n + referenz_n)
            rel_ziel = f_ziel / ziel_n
            rel_ref = f_ref / referenz_n
            if rel_ziel < rel_ref:
                continue        # hier interessiert nur, was *heraussticht*
            ergebnis.append({
                "wort": wort, "anzeige": self.anzeigeform(wort),
                "hier": f_ziel, "referenz": f_ref,
                "ll": round(ll, 2),
                "faktor": round(rel_ziel / rel_ref, 2) if rel_ref else None,
                "logRatio": _log_ratio(rel_ziel, rel_ref),
            })
        ergebnis.sort(key=lambda e: -e["ll"])
        return ergebnis[:grenze]

    # -- Ein Wort über die Zeit -----------------------------------------
    def wortverlauf(self, wort: str, sprecher: str = KLIENT) -> dict:
        """Ein Wort, Sitzung für Sitzung, als Rate je 1000 Wörter.

        Rate und nicht Rohzahl: eine lange Stunde hat sonst automatisch mehr
        von allem. Gesucht wird über das Lemma, damit „Ängste“ und „Angst“
        dieselbe Kurve sind.
        """
        lemma = self._lemma(wort.strip().lower())
        nummern, werte, roh = [], [], []
        for s in self.sitzungen:
            zaehler = self.lemma_je_sitzung.get(s.sid, {}).get(sprecher, Counter())
            n = self.gesamt_je_sitzung.get(s.sid, {}).get(sprecher, 0)
            treffer = zaehler.get(lemma, 0)
            nummern.append(s.nummer)
            roh.append(treffer)
            werte.append(round(1000.0 * treffer / n, 3) if n else 0.0)
        return {
            "wort": wort.strip(), "lemma": lemma, "sprecher": sprecher,
            "nummern": nummern, "werte": werte, "roh": roh,
            "gesamt": sum(roh),
        }

    # -- Was kommt, was geht --------------------------------------------
    def vokabelbewegung(self, sprecher: str = KLIENT, min_frequenz: int = 5,
                        min_sitzungen: int = 4, grenze: int = 20) -> dict:
        """Wortschatz, der steigt, fällt, auftaucht oder verschwindet.

        Steigen und Fallen über die Rangkorrelation der Rate gegen die
        Sitzungsfolge — dieselbe Rechnung, mit der ``arc`` seine Marker prüft,
        nur auf ein einzelnes Wort angewandt. Auftauchen und Verschwinden sind
        schlichter und oft aussagekräftiger: das erste und das letzte Mal.
        """
        sids = [s.sid for s in self.sitzungen]
        leer = {"steigend": [], "fallend": [], "neu": [], "verschwunden": [],
                "genug": False}
        if len(sids) < min_sitzungen:
            return leer

        raten: dict[str, list[float]] = {}
        gesamt = self.lemma_frequenz[sprecher]
        for wort, anzahl in gesamt.items():
            if anzahl < min_frequenz or wort in self.stoppwoerter or len(wort) < 3:
                continue
            reihe = []
            for sid in sids:
                n = self.gesamt_je_sitzung.get(sid, {}).get(sprecher, 0)
                treffer = self.lemma_je_sitzung.get(sid, {}).get(sprecher, Counter()).get(wort, 0)
                reihe.append(1000.0 * treffer / n if n else 0.0)
            raten[wort] = reihe

        bewegt = []
        for wort, reihe in raten.items():
            rho = rangkorrelation(reihe)
            bewegt.append({"wort": wort, "anzeige": self.anzeigeform(wort),
                           "anzahl": gesamt[wort], "rho": round(rho, 3),
                           "werte": [round(v, 3) for v in reihe]})

        steigend = sorted((e for e in bewegt if e["rho"] > 0.3), key=lambda e: -e["rho"])
        fallend = sorted((e for e in bewegt if e["rho"] < -0.3), key=lambda e: e["rho"])

        # Erst- und Letztauftritt. Die zweite Hälfte bzw. erste Hälfte als
        # Schwelle: ein Wort, das erst spät kommt, und eines, das früh aufhört.
        drittel = max(1, len(sids) // 3)
        neu, verschwunden = [], []
        for wort, reihe in raten.items():
            treffer_idx = [i for i, v in enumerate(reihe) if v > 0]
            if not treffer_idx:
                continue
            erst, letzt = treffer_idx[0], treffer_idx[-1]
            eintrag = {"wort": wort, "anzeige": self.anzeigeform(wort),
                       "anzahl": gesamt[wort],
                       "erst": self.sitzungen[erst].nummer,
                       "letzt": self.sitzungen[letzt].nummer}
            if erst >= len(sids) - drittel:
                neu.append(eintrag)
            if letzt < drittel:
                verschwunden.append(eintrag)

        return {
            "steigend": steigend[:grenze],
            "fallend": fallend[:grenze],
            "neu": sorted(neu, key=lambda e: -e["anzahl"])[:grenze],
            "verschwunden": sorted(verschwunden, key=lambda e: -e["anzahl"])[:grenze],
            "genug": True,
        }

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


def _log_ratio(rel_ziel: float, rel_ref: float) -> float | None:
    """Effektstärke neben dem Signifikanzwert.

    G² sagt, wie sicher ein Unterschied ist, und wird mit der Textmenge
    beliebig gross — bei einem Jahr Transkript steht am Ende fast alles oben.
    Log Ratio sagt, wie *gross* der Unterschied ist: +1 heisst doppelt so
    häufig, +2 viermal. Erst beide zusammen sind eine Aussage.
    """
    if rel_ziel <= 0 or rel_ref <= 0:
        return None
    return round(math.log2(rel_ziel / rel_ref), 2)


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
