"""Der Bericht — ein einziger JSON-Vertrag zwischen Python und Oberfläche.

Alles, was die Oberfläche zeichnet, kommt aus :meth:`Korpus.bericht`. Alles,
was sie nachlädt (Konkordanz, Kollokationen, Ausschnitte), holt sie über die
Abfragemethoden weiter unten. Kein zweiter Weg, keine Sonderpfade — sonst
driftet der Vertrag und in zwei Jahren weiss niemand mehr, welche Zahl woher
kommt.

Deutsche Schlüssel in Python, kurze Schlüssel im JSON. Die Übersetzung passiert
genau hier und nirgendwo sonst.

**Zur Zweisprachigkeit.** Der Vertrag hat sich um genau drei Dinge erweitert:

* Jede Sitzung und jeder Klientenblock trägt seine ``sprache``.
* ``beschriftung`` ist nach Sprachcode geschachtelt, und dazu kommen
  ``kacheln`` und ``arcReihen`` — welche Zahlen die Oberfläche zeigt, ist
  jetzt eine sprachliche Entscheidung und steht deshalb hier und nicht im
  JavaScript.
* Wo ein gemischtes Korpus eine Zahl unbrauchbar macht, steht eine Warnung
  neben der Zahl statt in der Dokumentation.

Was sich **nicht** geändert hat: es gibt weiterhin genau einen Weg von den
Transkripten in die Oberfläche.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import arc, dialogue, lexical, markers, people, sprachen, threads
from .ingest import (KLIENT, SEGMENT_MIN_WOERTER, THERAPEUT, Befund, Sitzung,
                     lies, segmentiere, sortiere_sitzungen)
from .markers import SprecherMarker, kennzahlen
from .pseudonym import Namenskandidat, Pseudonymisierer, finde_namen, pseudonymisiere_sitzungen

VERSION = "0.1.0"
MAX_TREFFER_JE_MARKER = 400      # deckelt die JSON-Grösse, ohne die Klickbarkeit zu verlieren


@dataclass
class Korpus:
    """Der gesamte Zustand einer Sitzung im Browser.

    Lebt im Arbeitsspeicher und nirgends sonst. Wer die Seite neu lädt, fängt
    von vorn an — das ist kein Mangel, sondern die Eigenschaft, die die ganze
    Datenschutzarchitektur trägt.
    """

    sitzungen: list[Sitzung] = field(default_factory=list)
    pseudo: Pseudonymisierer = field(default_factory=Pseudonymisierer)
    indizes: dict[str, lexical.Index] = field(default_factory=dict)
    marker: dict[str, dict[str, SprecherMarker]] = field(default_factory=dict)
    dialoge: dict[str, dialogue.Dialogkennzahlen] = field(default_factory=dict)
    kandidaten: list[Namenskandidat] = field(default_factory=list)
    _analysiert: bool = False

    # -- Einlesen --------------------------------------------------------
    def lade(self, dateien: list[dict], klient_id: str | None = None,
             manuelle_sprecher: dict[str, str] | None = None,
             sprache: str | None = None) -> list[dict]:
        """Liest Dateien ein. ``dateien`` = ``[{"name": …, "inhalt": …}, …]``.

        Gibt die Befunde zurück — **bevor** irgendetwas analysiert wird, damit
        der Therapeut zuerst sieht, was überhaupt erkannt wurde. Die erkannte
        Sprache steht dort mit drin, aus demselben Grund wie die geratene
        Sprecherzuordnung: sie ist geraten, und wer sie erst hinter den Kurven
        erfährt, hat die Kurven schon geglaubt.
        """
        neue: list[Sitzung] = []
        befunde: list[Befund] = []
        for datei in dateien:
            gelesen = lies(datei["name"], datei["inhalt"],
                           klient_id=klient_id or datei.get("klient"),
                           manuelle_sprecher=manuelle_sprecher,
                           sprache=sprache or datei.get("sprache"))
            neue.extend(gelesen)
            if gelesen and gelesen[0].befund is not None:
                befunde.append(gelesen[0].befund)

        neue = self._notfalls_segmentieren(neue, datei_anzahl=len(dateien))
        self.sitzungen = sortiere_sitzungen(self.sitzungen + neue)
        self._analysiert = False
        return [b.als_dict() for b in befunde]

    def _notfalls_segmentieren(self, neue: list[Sitzung],
                               datei_anzahl: int) -> list[Sitzung]:
        """Schneidet einen langen Text ohne Sitzungsmarken in gleiche Stücke.

        Die Entscheidung fällt hier und nicht in ``lies``, weil sie vom ganzen
        Bestand abhängt: zwölf sauber benannte Dateien sind zwölf Sitzungen und
        dürfen nicht noch einmal zerschnitten werden. Nur wenn am Ende fast
        nichts dasteht — weniger als drei Sitzungen — und der Text trotzdem lang
        ist, war es offenbar ein zusammengeschriebenes Jahr ohne Marken.
        """
        bestand = self.sitzungen + neue
        if len(bestand) >= 3 or datei_anzahl > 2:
            return neue
        lang = [s for s in neue
                if sum(len(t.text.split()) for t in s.turns) >= SEGMENT_MIN_WOERTER]
        if not lang:
            return neue
        aufgeteilt: list[Sitzung] = []
        for s in neue:
            aufgeteilt.extend(segmentiere(s) if s in lang else [s])
        return aufgeteilt

    def klient_umbenennen(self, alt: str, neu: str) -> None:
        """Gibt einem Fall einen Namen.

        Die Fallkennung kam bisher ausschliesslich aus dem Dateinamen. Wer
        einen Text einfügt, hat keinen Dateinamen und bekam deshalb einen Fall
        namens „unbekannt“, den er nirgends ändern konnte. Der Name ist reine
        Beschriftung — er wird nicht analysiert und landet nicht im Export.
        """
        neu = (neu or "").strip()[:40] or "unbekannt"
        if neu == alt:
            return
        for sitzung in self.sitzungen:
            if sitzung.klient_id == alt:
                sitzung.klient_id = neu
        self._analysiert = False

    def leeren(self) -> None:
        self.sitzungen = []
        self.pseudo = Pseudonymisierer()
        self.indizes.clear()
        self.marker.clear()
        self.dialoge.clear()
        self.kandidaten = []
        self._analysiert = False

    # -- Pseudonymisierung ----------------------------------------------
    def namensvorschlaege(self) -> list[dict]:
        """Namenskandidaten zur einmaligen Bestätigung durch den Therapeuten.

        Je Sprache ein eigener Durchgang, danach zusammengeführt. Ein
        gemeinsamer Durchgang über ein gemischtes Korpus würde den Sprachen
        ihre jeweiligen Substantive gegenseitig als Personennamen
        unterschieben — „Rat“, „Gift“, „Hut“ und „Bald“ sind in der einen
        Sprache gewöhnliche Wörter und in der anderen nichts davon.

        Beim Zusammenführen gewinnt der höhere Sicherheitswert: ein Name, den
        der eine Durchgang sicher erkennt und der andere gar nicht, ist ein
        erkannter Name und kein strittiger.
        """
        texte_je_sprache: dict[str, list[str]] = defaultdict(list)
        for sitzung in self.sitzungen:
            code = getattr(sitzung, "sprache", sprachen.STANDARD)
            texte_je_sprache[code].extend(t.text for t in sitzung.turns)

        zusammen: dict[str, Namenskandidat] = {}
        for code, texte in texte_je_sprache.items():
            for kandidat in finde_namen(texte, sprache=code):
                vorhanden = zusammen.get(kandidat.name)
                if vorhanden is None:
                    zusammen[kandidat.name] = kandidat
                elif kandidat.sicherheit > vorhanden.sicherheit:
                    kandidat.haeufigkeit += vorhanden.haeufigkeit
                    zusammen[kandidat.name] = kandidat
                else:
                    vorhanden.haeufigkeit += kandidat.haeufigkeit

        self.kandidaten = sorted(zusammen.values(),
                                 key=lambda k: (-k.sicherheit, -k.haeufigkeit, k.name))
        return [k.als_dict() for k in self.kandidaten]

    def pseudonymisiere(self, bestaetigte: list[dict] | None = None) -> dict:
        """Ersetzt bestätigte Namen. Läuft vor jeder Analyse.

        ``bestaetigte`` = ``[{"name": "Anna", "rolle": "Schwester"}, …]``.
        Ohne Argument werden alle Kandidaten mit Sicherheit ≥ 0.8 genommen —
        die Bestätigung bleibt trotzdem der vorgesehene Weg.
        """
        if bestaetigte is None:
            if not self.kandidaten:
                self.namensvorschlaege()
            bestaetigte = [{"name": k.name, "rolle": k.beziehung}
                           for k in self.kandidaten if k.sicherheit >= 0.8]
        for eintrag in bestaetigte:
            self.pseudo.registriere(eintrag["name"], eintrag.get("rolle"))
        geaendert = pseudonymisiere_sitzungen(self.sitzungen, self.pseudo)
        self._analysiert = False
        return {"ersetzteTurns": geaendert, **self.pseudo.zusammenfassung()}

    def sprecher_tauschen(self, sid: str) -> None:
        """Dreht T und K in einer Sitzung um — für den geratenen Fall."""
        for sitzung in self.sitzungen:
            if sitzung.sid != sid:
                continue
            for turn in sitzung.turns:
                if turn.sprecher == THERAPEUT:
                    turn.sprecher = KLIENT
                elif turn.sprecher == KLIENT:
                    turn.sprecher = THERAPEUT
            if sitzung.befund:
                sitzung.befund.sprecher_quelle = "manuell"
                sitzung.befund.warnungen.append("Speakers were swapped by hand.")
        self._analysiert = False

    def sprache_setzen(self, sid: str, code: str) -> None:
        """Überschreibt die erkannte Sprache einer Sitzung von Hand.

        Das Gegenstück zu :meth:`sprecher_tauschen`: die Erkennung ist eine
        Heuristik, also braucht sie einen Knopf, der sie in einem Klick
        korrigiert. Die Analyse wird danach neu gerechnet.
        """
        if code not in sprachen.CODES:
            return
        for sitzung in self.sitzungen:
            if sitzung.sid != sid:
                continue
            sitzung.sprache = code
            if sitzung.befund:
                sitzung.befund.sprache = code
                sitzung.befund.sprache_quelle = "manuell"
                sitzung.befund.warnungen.append(
                    f"Language was set to {sprachen.name(code)} by hand.")
        self._analysiert = False

    # -- Gruppierung -----------------------------------------------------
    @property
    def klienten(self) -> dict[str, list[Sitzung]]:
        gruppen: dict[str, list[Sitzung]] = defaultdict(list)
        for sitzung in self.sitzungen:
            gruppen[sitzung.klient_id].append(sitzung)
        return {k: sortiere_sitzungen(v) for k, v in gruppen.items()}

    # -- Analyse ---------------------------------------------------------
    def analysiere(self) -> None:
        if self._analysiert:
            return
        self.indizes.clear()
        self.marker.clear()
        self.dialoge.clear()
        for klient_id, sitzungen in self.klienten.items():
            index = lexical.Index(sitzungen)
            self.indizes[klient_id] = index
            vokabular = index.vokabular()
            for sitzung in sitzungen:
                self.marker[sitzung.sid] = markers.analysiere_sitzung(sitzung, vokabular)
                self.dialoge[sitzung.sid] = dialogue.analysiere(sitzung)
        self._analysiert = True

    # -- Bericht ---------------------------------------------------------
    def bericht(self) -> dict:
        self.analysiere()
        klienten = self.klienten
        alle_indizes = list(self.indizes.values())

        klient_blocks = []
        for klient_id, sitzungen in klienten.items():
            index = self.indizes[klient_id]
            klient_blocks.append(self._klient_block(klient_id, sitzungen, index,
                                                    alle_indizes))

        return {
            "version": VERSION,
            "klienten": klient_blocks,
            "sprachen": self._sprachblock(),
            "beschriftung": self._beschriftung(),
            "hinweise": {
                "faeden": threads.RAHMUNG,
                "arc": arc.HINWEIS,
                "geltung": GELTUNGSHINWEISE,
                "sprache": SPRACHHINWEIS,
            },
        }

    # -- Sprachen --------------------------------------------------------
    def _sprachcodes(self) -> list[str]:
        codes = {getattr(s, "sprache", sprachen.STANDARD) for s in self.sitzungen}
        return sorted(codes) or [sprachen.STANDARD]

    def _sprachblock(self) -> dict:
        codes = self._sprachcodes()
        je_sprache: Counter = Counter()
        for sitzung in self.sitzungen:
            je_sprache[getattr(sitzung, "sprache", sprachen.STANDARD)] += 1
        return {
            "codes": codes,
            "namen": {c: sprachen.name(c) for c in codes},
            "sitzungen": dict(je_sprache),
            "gemischt": len(codes) > 1,
        }

    def _beschriftung(self) -> dict:
        """Beschriftung, Kacheln und Arc-Reihen — je Sprache.

        Die Oberfläche schlägt hier mit dem Sprachcode der Sitzung nach, die
        sie gerade zeichnet. Dass die Auswahl der Kacheln hier steht und nicht
        im JavaScript, ist der eigentliche Umbau: welche Zahlen ein deutscher
        und ein englischer Fall zeigen, ist nicht dieselbe Liste, und eine
        Ansicht, die das fest verdrahtet, zeigt in der anderen Sprache leere
        Kacheln.
        """
        marker: dict[str, dict] = {}
        dialog: dict[str, dict] = {}
        familien: dict[str, dict] = {}
        kacheln: dict[str, list] = {}
        arc_reihen: dict[str, list] = {}

        for code in self._sprachcodes():
            pak = sprachen.paket(code)
            marker[code] = {
                k: {"name": n, "konfidenz": c, "hinweis": h}
                for k, (n, c, h) in {**pak.BESCHRIFTUNG,
                                     **sprachen.VERGLEICHBAR_BESCHRIFTUNG}.items()
            }
            dialog[code] = {k: {"name": n, "konfidenz": c, "hinweis": h}
                            for k, (n, c, h) in dialogue.beschriftung(code).items()}
            familien[code] = {f: pak.emotion.VALENZ.get(f, 0)
                              for f in pak.emotion.FAMILIEN}
            kacheln[code] = [list(k) for k in pak.KACHELN]
            arc_reihen[code] = list(pak.ARC_REIHEN)

        return {
            "marker": marker, "dialog": dialog,
            "familien": familien,
            "kacheln": kacheln, "arcReihen": arc_reihen,
        }

    def _klient_block(self, klient_id: str, sitzungen: list[Sitzung],
                      index: lexical.Index, alle_indizes: list[lexical.Index]) -> dict:
        sitzungs_blocks = []
        marker_je_sitzung = []
        for sitzung in sitzungen:
            sm = self.marker[sitzung.sid]
            marker_je_sitzung.append(sm)
            sitzungs_blocks.append(self._sitzung_block(sitzung, sm, index))

        nummern = [s.nummer or i + 1 for i, s in enumerate(sitzungen)]
        serien = arc.reihen(marker_je_sitzung, KLIENT)
        serien_t = arc.reihen(marker_je_sitzung, THERAPEUT)
        serien["redeanteilT"] = [self.dialoge[s.sid].redeanteil_t for s in sitzungen]
        serien["aufnahme"] = [self.dialoge[s.sid].aufnahme for s in sitzungen]
        serien["lsm"] = [self.dialoge[s.sid].lsm for s in sitzungen]

        index_werte = arc.komposit(serien, index.sprache)
        punkte = arc.wechselpunkte(index_werte, nummern) if index_werte else []
        saetze = [arc.beschreibe(p, nummern) for p in punkte]

        # Keyness nur gegen Klienten derselben Sprache. Gegen eine Referenz in
        # einer anderen Sprache misst das Log-Likelihood den Sprachunterschied
        # und sonst nichts — jedes deutsche Wort wäre "distinktiv", weil es im
        # englischen Vergleichskorpus null mal vorkommt. Lieber eine leere
        # Liste mit Begründung als eine volle ohne Bedeutung.
        vergleichbare = [i for i in alle_indizes
                         if i is not index and i.sprache == index.sprache]
        referenz, referenz_n = lexical.referenzfrequenzen(
            vergleichbare + [index], ausser=index)
        keyness = index.keyness(referenz, referenz_n) if referenz_n else []
        # Der Hinweis hing vorher daran, dass es *mehrere* Indizes gibt — wer
        # genau einen Fall lud, bekam eine leere Liste und kein Wort dazu. Es
        # gibt jetzt immer eine Begründung, und für den Fall ohne zweiten
        # Klienten gibt es ausserdem zwei Achsen, die keinen brauchen.
        if referenz_n:
            keyness_hinweis = None
        elif len(alle_indizes) > 1:
            keyness_hinweis = (
                "No reference corpus in the same language. Keyness against your "
                "other clients would measure the language rather than the "
                "client here, so it is left out rather than filled with "
                "something that looks like a result. The two axes below do not "
                "need a second client.")
        else:
            keyness_hinweis = (
                "Only one case is loaded, so there is nothing to be distinctive "
                "*against*. The two axes below compare this text with itself "
                "instead: one session against the others, and the late sessions "
                "against the early ones.")

        sozio = people.soziogramm(sitzungen, self.pseudo.platzhalter)
        verlauf = people.verlauf(sozio["knoten"], sozio["sitzungen"])

        sprach_codes = sorted(index.sprachen)
        return {
            "id": klient_id,
            "sitzungen": sitzungs_blocks,
            "nummern": nummern,
            "genugSitzungen": len(sitzungen) >= 10,
            "sprache": index.sprache,
            "sprachen": sprach_codes,
            "spracheName": ", ".join(sprachen.name(c) for c in sprach_codes),
            "spracheGemischt": index.gemischt,
            "spracheWarnung": (
                "This client's sessions are not all in the same language "
                f"({', '.join(sprachen.name(c) for c in sprach_codes)}). Each "
                "session is analysed with its own word lists, which is right, "
                "but it means the rates on either side of the switch sit at "
                "different levels for reasons that have nothing to do with the "
                "client. Markers that exist in only one of the two languages "
                "are left out of the charts entirely; the ones marked “across "
                "languages” are spliced and should be read for their shape "
                "within each stretch, not for the step between them."
                if index.gemischt else None),
            "arc": {
                "nummern": nummern,
                "serien": {k: [round(v, 4) for v in werte]
                           for k, werte in serien.items()},
                "serienTherapeut": {k: [round(v, 4) for v in werte]
                                    for k, werte in serien_t.items()},
                "komposit": [round(v, 4) for v in index_werte],
                "kompositGeglaettet": [round(v, 4) for v in arc.glaetten(index_werte)],
                "wechselpunkte": [p.als_dict() for p in punkte],
                "saetze": saetze,
                "trend": {k: round(arc.rangkorrelation(werte), 3)
                          for k, werte in serien.items() if len(werte) >= 4},
                "hinweis": arc.HINWEIS,
            },
            "soziogramm": {**sozio, "verlauf": verlauf,
                           **people.eintritte_und_abgaenge(verlauf, sozio["sitzungen"])},
            "keyness": keyness,
            "keynessHinweis": keyness_hinweis,
            "schluesselwoerter": {
                "phase": index.keyness_phase(KLIENT),
                "bewegung": index.vokabelbewegung(KLIENT),
                "komposita": index.komposita(KLIENT),
                "teilfrequenzen": [
                    {"wort": w, "anzeige": index.anzeigeform(w), "anzahl": n}
                    for w, n in index.teil_frequenzen(KLIENT).most_common(40)
                ],
                "haeufig": [
                    {"wort": w, "anzeige": index.anzeigeform(w), "anzahl": n}
                    for w, n in _haeufigste(index, KLIENT, 40)
                ],
                "hinweis": SCHLUESSELWORT_HINWEIS,
            },
            "faeden": [f.als_dict() for f in threads.ueber_sitzungen(sitzungen)],
        }

    def _sitzung_block(self, sitzung: Sitzung, sm: dict[str, SprecherMarker],
                       index: lexical.Index) -> dict:
        dia = self.dialoge[sitzung.sid]
        return {
            "sid": sitzung.sid,
            "nr": sitzung.nummer,
            "titel": sitzung.titel,
            "datum": sitzung.datum,
            "dateiname": sitzung.dateiname,
            "format": sitzung.format,
            "sprache": getattr(sitzung, "sprache", sprachen.STANDARD),
            "spracheName": sprachen.name(getattr(sitzung, "sprache",
                                                 sprachen.STANDARD)),
            "befund": sitzung.befund.als_dict() if sitzung.befund else None,
            "turns": len(sitzung.turns),
            "dialog": dia.als_dict(),
            "marker": {
                sprecher: {
                    "kennzahlen": {k: round(v, 4) for k, v in kennzahlen(einzel).items()},
                    "zaehler": dict(einzel.zaehler),
                    "familien": dict(einzel.emo_familien),
                    "verneint": dict(einzel.emo_verneint),
                    "metaphern": dict(einzel.metapher_domaenen),
                    "lemmata": dict(Counter(einzel.emo_lemmata).most_common(40)),
                    "treffer": {
                        name: [t.als_liste() for t in liste[:MAX_TREFFER_JE_MARKER]]
                        for name, liste in einzel.treffer.items()
                    },
                }
                for sprecher, einzel in sm.items()
            },
            "ttr": {sprecher: index.ttr(sitzung, sprecher)
                    for sprecher in (KLIENT, THERAPEUT)},
            "neuesVokabular": index.neues_vokabular(sitzung, KLIENT),
            # Wovon war an diesem Tag die Rede und sonst nicht — die Keyness-
            # Achse, die keinen zweiten Klienten braucht.
            "keyness": index.keyness_sitzung(sitzung, KLIENT),
            "faeden": [f.als_dict() for f in threads.finde(sitzung)],
            "affektverlauf": self._affektverlauf(sitzung),
        }

    def _affektverlauf(self, sitzung: Sitzung) -> list[list]:
        """Affektdichte des Klienten über den Verlauf der Sitzung.

        Pro Beitrag, nicht geglättet. Die Sitzung hat typischerweise eine
        Form — Aufwärmen, Kern, Abkühlen — und sie ist im Rohbild sichtbarer
        als in einer Kurve, die man schöngerechnet hat.
        """
        code = getattr(sitzung, "sprache", sprachen.STANDARD)
        punkte: list[list] = []
        for turn in sitzung.turns:
            if turn.sprecher != KLIENT:
                continue
            woerter = turn.text.split()
            if len(woerter) < 5:
                continue
            treffer = threads.affektwoerter(turn.text, code)
            punkte.append([turn.idx, len(woerter),
                           round(1000.0 * len(treffer) / len(woerter), 1)])
        return punkte

    # -- Abfragen aus der Oberfläche -------------------------------------
    def kwic(self, begriff: str, klient: str | None = None,
             sprecher: str | None = None, grenze: int = 300) -> list[dict]:
        self.analysiere()
        ergebnis: list[dict] = []
        for klient_id, index in self.indizes.items():
            if klient and klient_id != klient:
                continue
            for zeile in index.kwic(begriff, sprecher=sprecher, grenze=grenze):
                ergebnis.append({**zeile, "klient": klient_id})
        return ergebnis[:grenze]

    def kollokationen(self, begriff: str, klient: str,
                      sprecher: str = KLIENT) -> list[dict]:
        self.analysiere()
        index = self.indizes.get(klient)
        return index.kollokationen(begriff, sprecher) if index else []

    def wortverlauf(self, wort: str, klient: str,
                    sprecher: str = KLIENT) -> dict:
        """Ein Wort über die Sitzungen. Wird bei jeder Eingabe neu gerechnet
        statt für jedes Wort im Bericht mitgeschickt — der Bericht wäre sonst
        um den ganzen Wortschatz grösser, für eine Kurve, die man meistens
        nicht anschaut."""
        self.analysiere()
        index = self.indizes.get(klient)
        return index.wortverlauf(wort, sprecher) if index else {}

    def ausschnitt(self, klient: str, sid: str, turn: int,
                   start: int, end: int) -> dict:
        self.analysiere()
        index = self.indizes.get(klient)
        return index.ausschnitt(sid, turn, start, end) if index else {}

    def belege(self, klient: str, marker: str, sprecher: str = KLIENT,
               sid: str | None = None, grenze: int = 120) -> list[dict]:
        """Alle Belegstellen eines Markers, fertig als Textausschnitte.

        Das ist der Weg von einer Zahl in der Oberfläche zurück zu den Zeilen,
        die sie erzeugt haben. Bewusst eine einzige Abfrage statt hundert
        Einzelaufrufen über die Sprachgrenze — sonst wird der Klick auf eine
        Kachel im Browser spürbar langsam, und dann klickt niemand mehr.
        """
        self.analysiere()
        index = self.indizes.get(klient)
        if index is None:
            return []
        ergebnis: list[dict] = []
        for sitzung in self.klienten.get(klient, []):
            if sid and sitzung.sid != sid:
                continue
            sm = self.marker.get(sitzung.sid, {}).get(sprecher)
            if sm is None:
                continue
            for treffer in sm.treffer.get(marker, []):
                ergebnis.append({
                    **index.ausschnitt(sitzung.sid, treffer.turn,
                                       treffer.start, treffer.end),
                    "nr": sitzung.nummer, "titel": sitzung.titel,
                    "form": treffer.form,
                })
                if len(ergebnis) >= grenze:
                    return ergebnis
        return ergebnis

    def turns(self, sid: str, von: int = 0, bis: int = 10_000) -> list[dict]:
        """Rohansicht eines Sitzungsausschnitts — für den Sprung aus einer Zahl."""
        for sitzung in self.sitzungen:
            if sitzung.sid != sid:
                continue
            return [
                {"idx": t.idx, "sprecher": t.sprecher, "text": t.text,
                 "start": t.start_sek, "label": t.roh_label}
                for t in sitzung.turns if von <= t.idx <= bis
            ]
        return []

    def namenstabelle(self) -> list[dict]:
        """Nur für die Anzeige im Browser des Therapeuten. Nie im Export."""
        return self.pseudo.tabelle_fuer_anzeige()

    def export(self) -> dict:
        """Was den Browser verlassen darf, wenn er es ausdrücklich anstösst.

        Ohne Klarnamen, ohne Volltext — Kennzahlen, Verläufe und Belegstellen
        als Koordinaten. Wer die Belege lesen will, braucht die Transkripte,
        und die hat nur er.
        """
        bericht = self.bericht()
        for klient in bericht["klienten"]:
            for sitzung in klient["sitzungen"]:
                for sprecher_block in sitzung["marker"].values():
                    sprecher_block.pop("treffer", None)
            klient["faeden"] = [{k: v for k, v in f.items() if k != "inhalt"}
                                for f in klient["faeden"]]
        bericht["export"] = {
            "hinweis": ("Contains no real names and no transcript text. The "
                        "placeholder-to-name mapping exists only in your browser "
                        "and is forgotten when the page reloads."),
            "pseudonyme": self.pseudo.zusammenfassung(),
            "sprachen": self._sprachblock(),
        }
        return bericht


# ---------------------------------------------------------------------------
# Geltungshinweise — gehören in die Oberfläche, nicht in ein Dokument
# ---------------------------------------------------------------------------

SCHLUESSELWORT_HINWEIS = (
    "Two numbers per word, and they answer different questions. G² says how "
    "confident the difference is and grows with the amount of text — over a "
    "year almost everything ends up looking significant. Log ratio says how "
    "large it is: +1 means twice as often, +2 four times. Read them together, "
    "and read the lines behind them before you believe either."
)


def _haeufigste(index, sprecher: str, grenze: int) -> list[tuple[str, int]]:
    """Häufigste Inhaltslemmata — der Einstieg in den Wortverlauf.

    Keyness zeigt das Besondere, aber man sucht auch das Naheliegende: wer
    „Mutter“ eingeben will, soll es anklicken können statt es zu tippen.
    """
    stopp = index.stoppwoerter
    return [(w, n) for w, n in index.lemma_frequenz[sprecher].most_common()
            if w not in stopp and len(w) >= 3][:grenze]


SPRACHHINWEIS = (
    "Each session is analysed in the language it was spoken in, with that "
    "language's own word lists — a translated lexicon would measure the "
    "translation. The language is detected per file and shown in the ingest "
    "report; you can override it there, or settle it in advance by putting "
    "“_de” or “_en” in the filename. Within one language the numbers compare "
    "cleanly. Across the two they do not, and anywhere they are put side by "
    "side the interface says so."
)

GELTUNGSHINWEISE = [
    {
        "titel": "One session is noise.",
        "text": ("Most markers mean nothing below roughly ten sessions. A single "
                 "striking number in a single session is almost always chance."),
    },
    {
        "titel": "A transcript is not a session.",
        "text": ("Tone, pause, body and silence are gone. Thera.py reads the "
                 "shadow of the hour, not the hour."),
    },
    {
        "titel": "Speech-recognition errors are not random.",
        "text": ("Automatic transcription mishears hardest on exactly the "
                 "low-frequency emotional vocabulary that the granularity "
                 "measure most wants to count."),
    },
    {
        "titel": "The lexicons are adapted, not validated.",
        "text": ("Each language runs on its own word lists, and neither set is "
                 "validated. Which way the adaptation runs differs per marker: "
                 "the absolutist list is an English instrument worn in German "
                 "clothes, while style matching and the causal/insight lists are "
                 "English originals that the German side had to translate. What "
                 "is deliberately excluded is documented in the source, in "
                 "lexika/marker.py and lexika_en/marker.py."),
    },
    {
        "titel": "Two languages, two rulers.",
        "text": ("German and English sessions are counted with different word "
                 "lists, because the markers are properties of a language and "
                 "not of a translation. That makes the trajectories within one "
                 "language sound, and the *levels* between the two languages "
                 "meaningless. Wherever a number crosses that line, it says so "
                 "next to the number."),
    },
    {
        "titel": "Consent.",
        "text": ("Your clients consented to being recorded. They almost "
                 "certainly did not consent to computational analysis of their "
                 "language. That is your call to make — but it should be made "
                 "deliberately rather than by default, and it is worth raising "
                 "with your professional body."),
    },
    {
        "titel": "The tool has no opinion.",
        "text": "It counts. The interpretation is your work and stays your work.",
    },
]
