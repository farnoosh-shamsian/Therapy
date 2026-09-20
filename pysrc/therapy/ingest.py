"""Einlesen: Formaterkennung, Parsen, Sprecherzuordnung — und ein ehrlicher Befund.

Leitsatz dieses Moduls: **lieber melden als raten.** Das Transkriptformat ist
unbekannt, und jede Heuristik hier kann danebenliegen. Was sie nicht darf, ist
danebenliegen und so tun, als sei alles in Ordnung. Deshalb gibt jeder
Einlesevorgang einen :class:`Befund` zurück, der sagt, was gefunden wurde, was
geraten wurde und welche Kennzahlen deshalb *nicht* zur Verfügung stehen.

Unterstützte Formate: ``.txt`` ``.vtt`` ``.srt`` ``.json`` (Whisper) ``.csv``
``.tsv`` ``.docx`` ``.html`` ``.md``.

``.docx`` und ``.html`` sind die Formate, in denen die verbreiteten
Dokumentations-Assistenten (VIA u.a.) ein Transkript herausgeben. Sie setzen
den Sprecher gern auf eine *eigene* Zeile statt vor einen Doppelpunkt —
deshalb kennt der Textparser beide Schreibweisen.

Seit das Werkzeug zweisprachig ist, gehört die **Sprache** zu genau diesen
geratenen Dingen. Sie wird pro Sitzung erkannt, steht im Befund, und wenn die
Erkennung unsicher ist oder eine Sitzung die Sprache wechselt, steht auch das
dort — vor den Kurven und nicht hinter ihnen.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from dataclasses import dataclass, field

from . import sprachen
from .tokenize import normalisiere

THERAPEUT = "T"
KLIENT = "K"
UNBEKANNT = "?"


# ---------------------------------------------------------------------------
# Datenmodell
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Turn:
    """Ein Redebeitrag."""

    idx: int
    sprecher: str                 # "T" | "K" | "?"
    text: str
    start_sek: float | None = None
    ende_sek: float | None = None
    roh_label: str = ""

    @property
    def dauer(self) -> float | None:
        if self.start_sek is None or self.ende_sek is None:
            return None
        return max(0.0, self.ende_sek - self.start_sek)


@dataclass(slots=True)
class Sitzung:
    """Eine Sitzung: geordnete Turns plus alles, was wir über die Datei wissen."""

    sid: str
    dateiname: str
    turns: list[Turn] = field(default_factory=list)
    nummer: int | None = None
    datum: str | None = None
    klient_id: str = "unbekannt"
    format: str = "?"
    sprache: str = sprachen.STANDARD
    befund: "Befund | None" = None
    # Position in der Quelldatei — hält aufgeteilte Sitzungen ohne Datum in der
    # Reihenfolge, in der sie im Text standen.
    quelle_idx: int = 0
    # True, wenn das hier keine echte Sitzung ist, sondern ein gleich grosses
    # Stück eines Textes ohne Sitzungsmarken. Die Oberfläche sagt das dazu.
    ist_segment: bool = False

    @property
    def titel(self) -> str:
        teile = []
        if self.nummer is not None:
            wort = "Segment" if self.ist_segment else "Session"
            teile.append(f"{wort} {self.nummer:02d}")
        if self.datum:
            teile.append(self.datum)
        return " · ".join(teile) if teile else self.dateiname

    @property
    def hat_zeitstempel(self) -> bool:
        return any(t.start_sek is not None for t in self.turns)

    @property
    def hat_sprecher(self) -> bool:
        return any(t.sprecher in (THERAPEUT, KLIENT) for t in self.turns)

    def turns_von(self, sprecher: str) -> list[Turn]:
        return [t for t in self.turns if t.sprecher == sprecher]

    def volltext(self) -> str:
        return "\n".join(t.text for t in self.turns)


@dataclass(slots=True)
class Befund:
    """Was das Einlesen gefunden hat — und was es dadurch nicht kann.

    Wird in der Oberfläche als Erstes angezeigt. Wenn hier etwas fehlt, fehlt
    es später auch, und das soll man sehen, bevor man Kurven anschaut.
    """

    dateiname: str
    format: str
    turns: int = 0
    woerter: int = 0
    labels_gefunden: list[str] = field(default_factory=list)
    sprecher_quelle: str = "keine"      # "labels" | "geraten" | "manuell" | "keine"
    zeitstempel: bool = False
    warnungen: list[str] = field(default_factory=list)
    nicht_verfuegbar: list[str] = field(default_factory=list)
    anteil_unbekannt: float = 0.0
    sprache: str = sprachen.STANDARD
    sprache_quelle: str = "erkannt"     # "erkannt" | "dateiname" | "manuell" | "standard"
    sprache_sicherheit: float = 0.0
    anteil_fremdsprache: float = 0.0
    # Wie die Datei in Sitzungen zerfiel: "keine" (eine Datei = eine Sitzung),
    # "separator" (Sitzungsmarken im Text gefunden) oder "segmente" (keine
    # Marken, in gleich grosse Stücke geschnitten).
    teilung: str = "keine"
    sitzungen_info: list[dict] = field(default_factory=list)
    # Roh-Fundstellen der Sitzungsmarken, (Turn-Index, Kopfdaten). Intern.
    abschnitt_marken: list[dict] = field(default_factory=list)

    def als_dict(self) -> dict:
        return {
            "dateiname": self.dateiname,
            "format": self.format,
            "turns": self.turns,
            "woerter": self.woerter,
            "labels": self.labels_gefunden,
            "sprecherQuelle": self.sprecher_quelle,
            "zeitstempel": self.zeitstempel,
            "warnungen": self.warnungen,
            "nichtVerfuegbar": self.nicht_verfuegbar,
            "anteilUnbekannt": round(self.anteil_unbekannt, 3),
            "sprache": self.sprache,
            "spracheName": sprachen.name(self.sprache),
            "spracheQuelle": self.sprache_quelle,
            "spracheSicherheit": round(self.sprache_sicherheit, 3),
            "anteilFremdsprache": round(self.anteil_fremdsprache, 3),
            "teilung": self.teilung,
            "sitzungen": self.sitzungen_info,
        }


# ---------------------------------------------------------------------------
# Sprecherlabels
# ---------------------------------------------------------------------------
#
# Zuordnung über Wortanfänge, nicht über Teilstrings: "Patient" soll treffen,
# "Therapeutin" auch, aber ein Eigenname wie "Petra" darf nicht über das "P"
# zum Patienten werden. Einzelbuchstaben werden deshalb gesondert behandelt.

_THERAPEUT_MUSTER = re.compile(
    r"^(therapeut(in)?|thera|ther|therapist|behandler(in)?|psycholog(e|in|ist)?|"
    r"psychotherapeut(in)?|psychotherapist|arzt|ärztin|doktor|dr|beraterin|berater|"
    r"counsell?or|clinician|analyst|psychiatrist|interviewer(in)?|t|th|b)$", re.I)

_KLIENT_MUSTER = re.compile(
    r"^(klient(in)?|patient(in)?|pat|pt|kl|k|p|c|cl|client|proband(in)?|"
    r"befragte(r)?|interviewte(r)?|interviewee|ratsuchende(r)?|service user)$", re.I)

# "Sprecher 1" / "SPEAKER_00" aus Diarisierungs-Werkzeugen.
_ANONYM_MUSTER = re.compile(r"^(sprecher|speaker|spk|s)[\s_-]*(\d+)$", re.I)

# Zeile mit Sprecherlabel: "T: …", "Therapeutin: …", "[00:12:03] K: …",
# "(12:03) Patient – …"
_LABEL_ZEILE = re.compile(
    r"""^\s*
        (?:[\[\(]?\s*(?P<zeit>\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)\s*[\]\)]?\s*)?
        (?P<label>[A-Za-zÄÖÜäöüß][\wÄÖÜäöüß .\-]{0,28}?)
        \s*(?::|\s[–—-]\s)\s+
        (?P<text>\S.*)$
    """,
    re.VERBOSE,
)

# Sprecher auf einer *eigenen* Zeile, Text darunter:
#
#     Therapeut
#     Wie war die Woche?
#
# So setzen Word- und HTML-Exporte den Sprecherwechsel — der Name steht fett
# in einem eigenen Absatz, ohne Doppelpunkt. Bis hierher fiel diese Zeile
# durch und wurde als gesprochener Satz gezählt.
_NUR_LABEL_ZEILE = re.compile(
    r"""^\s*
        (?:[\[\(]?\s*(?P<zeit>\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)\s*[\]\)]?\s*)?
        (?P<label>[A-Za-zÄÖÜäöüß][\wÄÖÜäöüß .\-]{0,28}?)
        \s*:?\s*$
    """,
    re.VERBOSE,
)

_ZEIT_VTT = re.compile(
    r"(\d{1,2}:)?(\d{1,2}):(\d{2})[.,](\d{1,3})\s*-->\s*(\d{1,2}:)?(\d{1,2}):(\d{2})[.,](\d{1,3})"
)
_VTT_STIMME = re.compile(r"<v\s+([^>]+?)\s*>(.*?)(?:</v>)?$", re.S)
_TAGS = re.compile(r"<[^>]+>")

# HTML-Export: Skript und Stil fliegen ganz raus, Blockenden werden zu
# Zeilenumbrüchen. Mehr braucht es nicht — was danach übrig bleibt, ist Text
# mit Sprecherzeilen, und dafür gibt es schon einen Parser.
_HTML_WEG = re.compile(r"<(script|style)\b.*?</\s*\1\s*>", re.I | re.S)
_HTML_BLOCK = re.compile(
    r"</\s*(?:p|div|li|tr|h[1-6]|blockquote|section|article|td|th)\s*>"
    r"|<\s*br\s*/?\s*>",
    re.I,
)

_ENTITAETEN = {
    "&nbsp;": " ", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'",
    "&ndash;": "–", "&mdash;": "—", "&hellip;": "…", "&shy;": "",
    "&auml;": "ä", "&ouml;": "ö", "&uuml;": "ü", "&szlig;": "ß",
    "&Auml;": "Ä", "&Ouml;": "Ö", "&Uuml;": "Ü",
}


def _entitaeten(text: str) -> str:
    """Löst HTML-Entitäten auf — ``&amp;`` als Letztes.

    Die Reihenfolge ist keine Kosmetik: wer ``&amp;`` zuerst ersetzt, macht
    aus dem geschriebenen ``&amp;lt;`` ein ``<`` und erfindet damit ein Tag,
    das im Transkript nie stand.
    """
    for roh, zeichen in _ENTITAETEN.items():
        text = text.replace(roh, zeichen)
    text = re.sub(r"&#(\d{1,6});",
                  lambda m: chr(int(m.group(1))) if int(m.group(1)) < 0x110000 else "",
                  text)
    return text.replace("&amp;", "&")


def _zeit_zu_sekunden(text: str) -> float | None:
    if not text:
        return None
    text = text.strip().replace(",", ".")
    teile = text.split(":")
    try:
        werte = [float(p) for p in teile]
    except ValueError:
        return None
    sek = 0.0
    for wert in werte:
        sek = sek * 60 + wert
    return sek


# ---------------------------------------------------------------------------
# Formaterkennung
# ---------------------------------------------------------------------------

def erkenne_format(dateiname: str, inhalt: str | bytes) -> str:
    name = dateiname.lower()
    if isinstance(inhalt, bytes):
        if inhalt[:2] == b"PK":
            return "docx"
        try:
            inhalt = inhalt.decode("utf-8")
        except UnicodeDecodeError:
            inhalt = inhalt.decode("latin-1", errors="replace")
    kopf = inhalt.lstrip()[:400]

    if name.endswith(".docx") or kopf.startswith("PK"):
        return "docx"
    # Bewusst eng: nur die Wurzel-Tags eines echten Dokuments. Ein Transkript,
    # in dem einmal "<p>" als gesprochenes Zeichen vorkommt, ist kein HTML.
    if (name.endswith((".html", ".htm"))
            or re.search(r"<\s*(?:!doctype\s+html|html|head|body)\b", kopf, re.I)):
        return "html"
    if kopf.upper().startswith("WEBVTT") or name.endswith(".vtt"):
        return "vtt"
    if name.endswith(".srt") or re.match(r"^\d+\s*\n\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->", kopf):
        return "srt"
    if name.endswith(".json") or kopf.startswith(("{", "[")):
        return "json"
    if name.endswith((".csv", ".tsv")):
        return "csv"
    # CSV ohne Endung: erste Zeile hat Trenner und plausible Spaltennamen
    erste = kopf.split("\n", 1)[0]
    if erste.count(";") >= 1 or erste.count(",") >= 2 or erste.count("\t") >= 1:
        if re.search(r"sprecher|speaker|text|inhalt|redner|rolle", erste, re.I):
            return "csv"
    return "txt"


# ---------------------------------------------------------------------------
# Parser je Format
# ---------------------------------------------------------------------------

def _parse_txt(text: str, befund: Befund) -> list[Turn]:
    """Zeilenbasiert mit Sprecherlabels; ohne Labels ein Turn pro Absatz."""
    turns: list[Turn] = []
    labels: dict[str, int] = {}
    aktuell: Turn | None = None

    for rohzeile in text.split("\n"):
        zeile = rohzeile.strip()
        if not zeile:
            aktuell = None      # Leerzeile beendet den Turn
            continue
        kopf = sitzungskopf(zeile)
        if kopf is not None:
            # Die Marke steht *vor* dem naechsten Turn — der Index, den wir uns
            # merken, ist deshalb die Laenge der bisherigen Turnliste.
            kopf["turn"] = len(turns)
            befund.abschnitt_marken.append(kopf)
            aktuell = None
            continue
        if _ist_metazeile(zeile):
            continue
        m = _LABEL_ZEILE.match(zeile)
        if m and _plausibles_label(m.group("label")):
            label = m.group("label").strip()
            labels[label] = labels.get(label, 0) + 1
            aktuell = Turn(
                idx=len(turns),
                sprecher=UNBEKANNT,
                text=m.group("text").strip(),
                start_sek=_zeit_zu_sekunden(m.group("zeit") or ""),
                roh_label=label,
            )
            turns.append(aktuell)
            continue

        # Sprecher allein auf der Zeile, Text folgt darunter. Der Turn wird
        # leer angelegt und von den nächsten Zeilen gefüllt; bleibt er leer,
        # wirft ``lies`` ihn ohnehin weg.
        nur = _reines_label(zeile)
        if nur is not None:
            label, zeit = nur
            labels[label] = labels.get(label, 0) + 1
            aktuell = Turn(
                idx=len(turns),
                sprecher=UNBEKANNT,
                text="",
                start_sek=_zeit_zu_sekunden(zeit),
                roh_label=label,
            )
            turns.append(aktuell)
        elif aktuell is not None:
            aktuell.text += " " + zeile
        else:
            aktuell = Turn(idx=len(turns), sprecher=UNBEKANNT, text=zeile)
            turns.append(aktuell)

    befund.labels_gefunden = sorted(labels, key=lambda k: -labels[k])
    return turns


# ---------------------------------------------------------------------------
# Sitzungsmarken in einem langen Text
# ---------------------------------------------------------------------------
#
# Ein Jahr Therapie liegt oft in *einer* Datei. Bis hierher war eine Datei
# immer genau eine Sitzung, und ein zusammengeklebtes Jahr wurde damit zu
# einem einzigen Punkt — der Verlauf, also der ganze Zweck des Werkzeugs,
# fiel lautlos aus.
#
# Zwei Klassen von Marken, bewusst getrennt:
#
# *stark*  — die Zeile sagt selbst, dass hier eine Sitzung beginnt: sie nennt
#            "Sitzung"/"Session" mit einer Zahl, oder sie ist nichts als ein
#            Datum. Zwei davon genügen zum Teilen.
# *schwach* — eine blosse Trennlinie (``---``, ``===``). Ohne weitere Angabe
#            ist das ein Hinweis, keine Aussage; sie wird nur benutzt, wenn
#            keine starke Marke da ist und die entstehenden Stücke tragfähig
#            sind.
#
# Was eine Marke *nicht* tut: sie verschwindet nicht mehr stillschweigend.
# Vorher fiel "Session 3:" durch ``_plausibles_label`` und landete als
# gesprochener Text im vorigen Turn.

_KOPF_DATUM = re.compile(
    r"^[\s#\-=*_\[\(]*"
    r"(\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[-./]\d{1,2}[-./]\d{4})"
    r"[\s#\-=*_\]\).,:]*$")

_KOPF_SITZUNG = re.compile(
    r"^[\s#\-=*_\[\(]*"
    r"(sitzung|session|termin|stunde|hour|meeting)\b.{0,70}$", re.I)

_KOPF_REGEL = re.compile(r"^\s*([-=*_])\1{2,}\s*$")

# Ein Abschnitt unter dieser Turn-Zahl ist kein Abschnitt, sondern ein
# Streuner — er wird an den vorigen angehängt statt eigene Sitzung zu werden.
MIN_TURNS_JE_ABSCHNITT = 4

# Rueckfallebene: ein langer Text ganz ohne Marken wird in gleich grosse
# Stuecke geschnitten. Unter SEGMENT_MIN_WOERTER lohnt das nicht — da ist der
# Text schlicht eine Sitzung.
SEGMENT_MIN_WOERTER = 4000
SEGMENT_ZIEL = 12
SEGMENT_MIN = 6
SEGMENT_MAX = 20


def sitzungskopf(zeile: str) -> dict | None:
    """Erkennt eine Sitzungsmarke und liest Nummer und Datum aus ihr heraus.

    Nummer und Datum kommen aus denselben Mustern, die ``metadaten_aus_name``
    auf Dateinamen anwendet — was im Dateinamen gilt, gilt auch in der Zeile.
    """
    zeile = zeile.strip()
    if not zeile or len(zeile) > 120:
        return None

    if _KOPF_DATUM.match(zeile):
        # Das Leerzeichen schuetzt "14.03.2024" davor, dass ".2024" als
        # Dateiendung abgeschnitten wird.
        _, datum, _ = metadaten_aus_name(zeile + " ")
        return {"art": "stark", "nummer": None, "datum": datum, "zeile": zeile}

    if _KOPF_SITZUNG.match(zeile) and re.search(r"\d", zeile):
        nummer, datum, _ = metadaten_aus_name(zeile + " ")
        return {"art": "stark", "nummer": nummer, "datum": datum, "zeile": zeile}

    if _KOPF_REGEL.match(zeile):
        return {"art": "schwach", "nummer": None, "datum": None, "zeile": zeile}

    return None


_META_MUSTER = re.compile(
    r"^\s*[\[\(#]?\s*(transkript|transcript|datei|file|datum|date|dauer|duration|"
    r"sitzung\s*nr|session\s*(no|nr|number)|aufnahme|recording|seite \d+|page \d+|"
    r"anonymisiert|anonymised|anonymized|de-?identified|--+|==+)\b", re.I)


def _ist_metazeile(zeile: str) -> bool:
    # Eine mit "#" beginnende Zeile ist in jedem Transkriptformat, das wir
    # gesehen haben, ein Kommentar oder Kopf — und nie Gesprochenes.
    return zeile.startswith("#") or bool(_META_MUSTER.match(zeile))


def _plausibles_label(label: str) -> bool:
    """Verhindert, dass jeder Doppelpunkt im Fliesstext ein Sprecherwechsel wird."""
    label = label.strip()
    if not label or len(label) > 28:
        return False
    if len(label.split()) > 3:
        return False
    if _THERAPEUT_MUSTER.match(label) or _KLIENT_MUSTER.match(label):
        return True
    if _ANONYM_MUSTER.match(label):
        return True
    # Ein einzelnes grossgeschriebenes Wort oder "Vorname N." gilt als Name.
    return bool(re.match(r"^[A-ZÄÖÜ][\wÄÖÜäöüß.\-]*(\s+[A-ZÄÖÜ][\wÄÖÜäöüß.\-]*)?$", label))


def _reines_label(zeile: str) -> tuple[str, str] | None:
    """Eine Zeile, die aus nichts als einem Sprechernamen besteht.

    Deutlich strenger als :func:`_plausibles_label`, und zwar aus einem
    handfesten Grund: dort bürgt der Doppelpunkt dafür, dass jemand einen
    Sprecher gemeint hat. Hier bürgt nichts. Ein kurzer Satz auf einer eigenen
    Zeile — "Ja." — sähe sonst aus wie ein Sprecher und würde die Redeanteile
    still verfälschen.

    Deshalb zählt hier nur, was aus sich heraus ein Sprecher ist: eine
    benannte Rolle (``Therapeut``, ``Patientin``, ``Client``) oder ein
    Diarisierungs-Name (``Sprecher 1``, ``SPEAKER_00``). Ein blosser Eigenname
    reicht nicht.
    """
    m = _NUR_LABEL_ZEILE.match(zeile)
    if not m:
        return None
    label = m.group("label").strip()
    kern = label.rstrip(".").strip()
    # Einzelbuchstaben nicht: "T" und "K" sind gültige Sprecherkürzel, aber
    # ohne Doppelpunkt stehen sie in einem eingefügten Text mit grösserer
    # Wahrscheinlichkeit für irgendetwas anderes. Blocklayout schreibt die
    # Rolle ohnehin aus.
    if len(kern) < 2:
        return None
    if (_THERAPEUT_MUSTER.match(kern) or _KLIENT_MUSTER.match(kern)
            or _ANONYM_MUSTER.match(kern)):
        return label, m.group("zeit") or ""
    return None


def _parse_vtt(text: str, befund: Befund) -> list[Turn]:
    turns: list[Turn] = []
    labels: dict[str, int] = {}
    bloecke = re.split(r"\n\s*\n", text)
    for block in bloecke:
        zeilen = [z for z in block.split("\n") if z.strip()]
        if not zeilen or zeilen[0].upper().startswith("WEBVTT"):
            continue
        zeit = next((z for z in zeilen if "-->" in z), None)
        if zeit is None:
            continue
        m = _ZEIT_VTT.search(zeit)
        start = ende = None
        if m:
            start = _zeit_zu_sekunden(
                f"{(m.group(1) or '0:').rstrip(':')}:{m.group(2)}:{m.group(3)}.{m.group(4)}")
            ende = _zeit_zu_sekunden(
                f"{(m.group(5) or '0:').rstrip(':')}:{m.group(6)}:{m.group(7)}.{m.group(8)}")
        inhalt = " ".join(zeilen[zeilen.index(zeit) + 1:]).strip()
        if not inhalt:
            continue
        label = ""
        v = _VTT_STIMME.match(inhalt)
        if v:
            label, inhalt = v.group(1).strip(), v.group(2).strip()
        else:
            m2 = _LABEL_ZEILE.match(inhalt)
            if m2 and _plausibles_label(m2.group("label")):
                label, inhalt = m2.group("label").strip(), m2.group("text").strip()
        inhalt = _TAGS.sub("", inhalt).strip()
        if not inhalt:
            continue
        if label:
            labels[label] = labels.get(label, 0) + 1
        turns.append(Turn(len(turns), UNBEKANNT, inhalt, start, ende, label))
    befund.labels_gefunden = sorted(labels, key=lambda k: -labels[k])
    return _fasse_gleiche_sprecher_zusammen(turns)


def _parse_srt(text: str, befund: Befund) -> list[Turn]:
    # Dieselbe Blockstruktur wie VTT, nur mit laufender Nummer davor.
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.M)
    return _parse_vtt(text, befund)


def _parse_json(text: str, befund: Befund) -> list[Turn]:
    daten = json.loads(text)
    segmente = None
    if isinstance(daten, dict):
        for schluessel in ("segments", "segmente", "turns", "utterances",
                           "results", "transcript", "items"):
            if isinstance(daten.get(schluessel), list):
                segmente = daten[schluessel]
                break
        if segmente is None and isinstance(daten.get("text"), str):
            befund.warnungen.append(
                "The JSON holds one continuous text without segments — speaker "
                "labels were searched for inside that text instead.")
            return _parse_txt(daten["text"], befund)
    elif isinstance(daten, list):
        segmente = daten
    if segmente is None:
        raise ValueError("JSON without a recognisable list of segments.")

    turns: list[Turn] = []
    labels: dict[str, int] = {}
    for seg in segmente:
        if not isinstance(seg, dict):
            continue
        inhalt = str(seg.get("text") or seg.get("content") or
                     seg.get("transcript") or "").strip()
        if not inhalt:
            continue
        label = str(seg.get("speaker") or seg.get("sprecher") or
                    seg.get("speaker_label") or seg.get("rolle") or "").strip()
        start = seg.get("start", seg.get("start_time"))
        ende = seg.get("end", seg.get("end_time"))
        start = float(start) if isinstance(start, (int, float)) else _zeit_zu_sekunden(str(start or ""))
        ende = float(ende) if isinstance(ende, (int, float)) else _zeit_zu_sekunden(str(ende or ""))
        if label:
            labels[label] = labels.get(label, 0) + 1
        turns.append(Turn(len(turns), UNBEKANNT, inhalt, start, ende, label))
    befund.labels_gefunden = sorted(labels, key=lambda k: -labels[k])
    return _fasse_gleiche_sprecher_zusammen(turns)


def _parse_csv(text: str, befund: Befund) -> list[Turn]:
    probe = text[:2000]
    try:
        dialekt = csv.Sniffer().sniff(probe, delimiters=",;\t|")
    except csv.Error:
        dialekt = csv.excel
        dialekt.delimiter = ";" if probe.count(";") > probe.count(",") else ","
    leser = csv.reader(io.StringIO(text), dialekt)
    zeilen = [z for z in leser if any(f.strip() for f in z)]
    if not zeilen:
        return []

    kopf = [f.strip().lower() for f in zeilen[0]]
    def finde(*namen: str) -> int | None:
        for i, feld in enumerate(kopf):
            if any(n in feld for n in namen):
                return i
        return None

    i_sprecher = finde("sprecher", "speaker", "rolle", "role", "wer", "name")
    i_text = finde("text", "inhalt", "content", "aussage", "utterance", "transkript")
    i_start = finde("start", "beginn", "zeit", "time", "timestamp")
    i_ende = finde("ende", "end", "stop")
    hat_kopf = i_text is not None or i_sprecher is not None
    if not hat_kopf:
        # Kein Kopf: heuristisch Spalte 0 = Sprecher, letzte = Text.
        i_sprecher, i_text = 0, len(zeilen[0]) - 1
        befund.warnungen.append(
            "CSV without a recognisable header row — column 1 read as the "
            "speaker, the last column as the text.")
    datenzeilen = zeilen[1:] if hat_kopf else zeilen

    turns: list[Turn] = []
    labels: dict[str, int] = {}
    for zeile in datenzeilen:
        def feld(i):
            return zeile[i].strip() if i is not None and i < len(zeile) else ""
        inhalt = feld(i_text)
        if not inhalt:
            continue
        label = feld(i_sprecher)
        if label:
            labels[label] = labels.get(label, 0) + 1
        turns.append(Turn(len(turns), UNBEKANNT, inhalt,
                          _zeit_zu_sekunden(feld(i_start)),
                          _zeit_zu_sekunden(feld(i_ende)), label))
    befund.labels_gefunden = sorted(labels, key=lambda k: -labels[k])
    return _fasse_gleiche_sprecher_zusammen(turns)


def _parse_docx(rohdaten: bytes, befund: Befund) -> list[Turn]:
    """docx ist ein ZIP mit XML darin. Reicht für Absätze, mehr brauchen wir nicht."""
    with zipfile.ZipFile(io.BytesIO(rohdaten)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    text = _TAGS.sub("", xml)
    return _parse_txt(_entitaeten(text), befund)


def _parse_html(text: str, befund: Befund) -> list[Turn]:
    """HTML-Export: Blockenden werden zu Zeilenumbrüchen, dann wie Text.

    Der Grund, dass es das gibt: die Dokumentations-Assistenten geben ein
    Transkript als Word *oder* HTML heraus. Ohne diesen Weg fiel eine
    HTML-Datei in den Textparser, und jedes ``<p>`` stand als gesprochenes
    Wort in der Auswertung.
    """
    text = _HTML_WEG.sub(" ", text)
    text = _HTML_BLOCK.sub("\n", text)
    return _parse_txt(_entitaeten(_TAGS.sub("", text)), befund)


def _fasse_gleiche_sprecher_zusammen(turns: list[Turn]) -> list[Turn]:
    """VTT/SRT/Whisper zerhacken einen Redebeitrag in Untertitelzeilen.

    Für Turn-Längen und Redeanteile ist das fatal — man zählt sonst
    Untertitel statt Beiträge. Aufeinanderfolgende Segmente desselben
    Sprechers werden deshalb zusammengefasst.
    """
    if not turns:
        return turns
    zusammen: list[Turn] = []
    for t in turns:
        if zusammen and zusammen[-1].roh_label == t.roh_label and t.roh_label != "":
            letzter = zusammen[-1]
            letzter.text = (letzter.text.rstrip() + " " + t.text.lstrip()).strip()
            letzter.ende_sek = t.ende_sek if t.ende_sek is not None else letzter.ende_sek
        elif zusammen and not t.roh_label and not zusammen[-1].roh_label:
            letzter = zusammen[-1]
            # Ohne Labels: nur zusammenfassen, wenn die Lücke klein ist.
            luecke = None
            if letzter.ende_sek is not None and t.start_sek is not None:
                luecke = t.start_sek - letzter.ende_sek
            if luecke is not None and luecke < 1.5:
                letzter.text = (letzter.text.rstrip() + " " + t.text.lstrip()).strip()
                letzter.ende_sek = t.ende_sek
            else:
                zusammen.append(t)
        else:
            zusammen.append(t)
    for i, t in enumerate(zusammen):
        t.idx = i
    return zusammen


# ---------------------------------------------------------------------------
# Sprecherzuordnung
# ---------------------------------------------------------------------------

def ordne_sprecher_zu(
    turns: list[Turn],
    befund: Befund,
    manuell: dict[str, str] | None = None,
) -> None:
    """Weist jedem Turn ``T``/``K``/``?`` zu und trägt die Quelle im Befund ein.

    Drei Wege, in dieser Reihenfolge:

    1. **Manuell.** Was der Therapeut in der Oberfläche zugeordnet hat, gilt.
    2. **Sprechende Labels.** "Therapeutin:", "Pat:", "T:" — eindeutig.
    3. **Geraten.** Nur bei genau zwei anonymen Labels ("Sprecher 1/2"), und
       nur nach einem Kriterium, das benannt wird: wer weniger redet, ist der
       Therapeut. Das stimmt in der Einzeltherapie meistens und ist trotzdem
       eine Vermutung — sie steht als Warnung im Befund und ist in der
       Oberfläche mit einem Klick umkehrbar.
    """
    manuell = {k.strip().lower(): v for k, v in (manuell or {}).items()}
    labels = {t.roh_label for t in turns if t.roh_label}

    if not labels:
        for t in turns:
            t.sprecher = UNBEKANNT
        befund.sprecher_quelle = "keine"
        befund.warnungen.append(
            "No speaker labels found. The text is read as a single voice.")
        befund.nicht_verfuegbar += [
            "talk ratio", "turn lengths", "question types", "lexical uptake",
            "style matching", "dropped threads",
        ]
        return

    zuordnung: dict[str, str] = {}
    quelle = "labels"
    for label in labels:
        schluessel = label.strip().lower()
        if schluessel in manuell:
            zuordnung[label] = manuell[schluessel]
        elif _THERAPEUT_MUSTER.match(label.strip().rstrip(".")):
            zuordnung[label] = THERAPEUT
        elif _KLIENT_MUSTER.match(label.strip().rstrip(".")):
            zuordnung[label] = KLIENT
        else:
            zuordnung[label] = UNBEKANNT

    if manuell:
        quelle = "manuell"

    offen = [l for l, s in zuordnung.items() if s == UNBEKANNT]
    zugeordnet = {s for s in zuordnung.values() if s != UNBEKANNT}

    if len(offen) == 2 and not zugeordnet:
        worte = {l: sum(len(t.text.split()) for t in turns if t.roh_label == l)
                 for l in offen}
        wenig, viel = sorted(offen, key=lambda l: worte[l])
        zuordnung[wenig], zuordnung[viel] = THERAPEUT, KLIENT
        quelle = "geraten"
        befund.warnungen.append(
            f"Speakers guessed: “{wenig}” = therapist (talks less), "
            f"“{viel}” = client. Please check, and swap them if that is wrong.")
    elif len(offen) == 1 and len(zugeordnet) == 1:
        fehlend = KLIENT if THERAPEUT in zugeordnet else THERAPEUT
        zuordnung[offen[0]] = fehlend
        rolle = "therapist" if fehlend == THERAPEUT else "client"
        befund.warnungen.append(
            f"“{offen[0]}” was filled in as {rolle}, because the other side was "
            "unambiguous.")
    elif offen:
        befund.warnungen.append(
            "More than two speakers in this transcript: "
            + ", ".join(f"“{l}”" for l in sorted(offen))
            + ". Unassigned turns are left out of the analysis.")

    for t in turns:
        t.sprecher = zuordnung.get(t.roh_label, UNBEKANNT)

    befund.sprecher_quelle = quelle
    unbekannt = sum(1 for t in turns if t.sprecher == UNBEKANNT)
    befund.anteil_unbekannt = unbekannt / len(turns) if turns else 0.0
    if befund.anteil_unbekannt > 0.25:
        befund.warnungen.append(
            f"{befund.anteil_unbekannt:.0%} of turns could not be assigned to a "
            "speaker. The dialogue figures are correspondingly shaky.")


# ---------------------------------------------------------------------------
# Metadaten aus dem Dateinamen
# ---------------------------------------------------------------------------

_NUMMER_MUSTER = [
    re.compile(r"sitzung[\s_-]*(\d{1,3})", re.I),
    re.compile(r"session[\s_-]*(\d{1,3})", re.I),
    re.compile(r"\bs(\d{1,3})\b", re.I),
    re.compile(r"(?:^|[^\d])(\d{1,3})(?:[^\d]|$)"),
]
_DATUM_MUSTER = [
    (re.compile(r"(\d{4})[-_.](\d{2})[-_.](\d{2})"), (1, 2, 3)),
    (re.compile(r"(\d{2})[-_.](\d{2})[-_.](\d{4})"), (3, 2, 1)),
]
_KLIENT_MUSTER_DATEI = re.compile(
    r"(?:klient|client|kl|pat|patient)[\s_-]*([A-Za-zÄÖÜäöüß0-9]{1,20})", re.I)

# Eine Sprachangabe im Dateinamen schlägt die Erkennung. Wer seine Dateien
# "..._en.txt" nennt, hat die Frage schon beantwortet, und geraten wird nur
# da, wo niemand etwas gesagt hat.
_SPRACHE_MUSTER_DATEI = re.compile(
    r"(?:^|[\s_.\-])(de|deu|ger|german|deutsch|en|eng|english|englisch)"
    r"(?:[\s_.\-]|$)", re.I)

_SPRACHE_ALIAS = {
    "de": "de", "deu": "de", "ger": "de", "german": "de", "deutsch": "de",
    "en": "en", "eng": "en", "english": "en", "englisch": "en",
}


def sprache_aus_name(dateiname: str) -> str | None:
    """Sprachcode aus dem Dateinamen, falls einer drinsteht."""
    basis = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", dateiname)
    basis = basis.replace("\\", "/").split("/")[-1]
    treffer = _SPRACHE_MUSTER_DATEI.search(basis)
    return _SPRACHE_ALIAS.get(treffer.group(1).lower()) if treffer else None


def metadaten_aus_name(dateiname: str) -> tuple[int | None, str | None, str | None]:
    """(Sitzungsnummer, ISO-Datum, Klientenkennung) aus dem Dateinamen."""
    basis = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", dateiname)
    basis = basis.replace("\\", "/").split("/")[-1]

    datum = None
    for muster, (j, m, t) in _DATUM_MUSTER:
        tr = muster.search(basis)
        if tr:
            datum = f"{tr.group(j)}-{tr.group(m)}-{tr.group(t)}"
            basis = basis.replace(tr.group(0), " ")
            break

    nummer = None
    for muster in _NUMMER_MUSTER:
        tr = muster.search(basis)
        if tr:
            try:
                nummer = int(tr.group(1))
            except ValueError:
                nummer = None
            break

    klient = None
    tr = _KLIENT_MUSTER_DATEI.search(basis)
    if tr:
        klient = tr.group(1).lower()
    return nummer, datum, klient


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def bestimme_sprache(turns: list[Turn], dateiname: str, befund: Befund,
                     vorgabe: str | None = None) -> str:
    """Legt die Sprache einer Sitzung fest und schreibt den Vorgang in den Befund.

    Reihenfolge, wie bei der Sprecherzuordnung: was jemand gesagt hat, gilt;
    dann, was im Dateinamen steht; dann geraten; und wenn zu wenig Material da
    ist, wird nicht geraten, sondern die Standardsprache genommen und das als
    Warnung vermerkt.
    """
    texte = [t.text for t in turns]
    code, sicherheit, details = sprachen.erkenne_je_turn(texte)
    befund.sprache_sicherheit = sicherheit
    befund.anteil_fremdsprache = details.get("anteilFremdsprache", 0.0)

    aus_name = sprache_aus_name(dateiname)

    if vorgabe in sprachen.CODES:
        befund.sprache, befund.sprache_quelle = vorgabe, "manuell"
        if details["woerter"] >= sprachen.MIN_WOERTER and code != vorgabe:
            befund.warnungen.append(
                f"This file was set to {sprachen.name(vorgabe)} by hand, but it "
                f"reads as {sprachen.name(code)}. The chosen language is used.")
        return befund.sprache

    if aus_name:
        befund.sprache, befund.sprache_quelle = aus_name, "dateiname"
        if details["woerter"] >= sprachen.MIN_WOERTER and code != aus_name:
            befund.warnungen.append(
                f"The filename says {sprachen.name(aus_name)}, the text reads as "
                f"{sprachen.name(code)}. The filename wins — rename the file if "
                "that is wrong.")
        return befund.sprache

    if details["woerter"] < sprachen.MIN_WOERTER:
        befund.sprache, befund.sprache_quelle = sprachen.STANDARD, "standard"
        befund.warnungen.append(
            f"Too little text to tell the language from ({details['woerter']} "
            f"words). Read as {sprachen.name(sprachen.STANDARD)} — put “_en” or "
            "“_de” in the filename if that is wrong.")
        return befund.sprache

    befund.sprache, befund.sprache_quelle = code, "erkannt"
    if sicherheit < 0.25:
        befund.warnungen.append(
            f"The language was hard to tell apart; read as "
            f"{sprachen.name(code)}. Put “_en” or “_de” in the filename to "
            "settle it.")
    if befund.anteil_fremdsprache >= sprachen.GEMISCHT_AB:
        befund.warnungen.append(
            f"{befund.anteil_fremdsprache:.0%} of the substantial turns are in "
            f"the other language. The whole file is analysed as "
            f"{sprachen.name(code)}, so those turns are counted with the wrong "
            "word lists. Splitting the file by language is the honest fix.")
    return befund.sprache


def lies(
    dateiname: str,
    inhalt: str | bytes,
    klient_id: str | None = None,
    manuelle_sprecher: dict[str, str] | None = None,
    sprache: str | None = None,
) -> list[Sitzung]:
    """Liest eine Datei zu einer oder mehreren :class:`Sitzung` mit :class:`Befund`.

    Eine Datei war lange genau eine Sitzung. Das stimmt, solange jemand seine
    Stunden einzeln ablegt, und es stimmt nicht mehr, sobald er ein Jahr in ein
    Dokument schreibt — genau der Fall, für den dieses Werkzeug gemacht ist.
    Trägt der Text Sitzungsmarken, wird an ihnen getrennt; trägt er keine,
    bleibt es bei einer Sitzung, und ``Korpus.lade`` entscheidet dann mit Blick
    auf den ganzen Bestand, ob gleichmässig segmentiert wird.
    """
    fmt = erkenne_format(dateiname, inhalt)
    befund = Befund(dateiname=dateiname, format=fmt)

    if fmt == "docx":
        rohdaten = inhalt if isinstance(inhalt, bytes) else inhalt.encode("latin-1", "replace")
        turns = _parse_docx(rohdaten, befund)
    else:
        text = inhalt.decode("utf-8", errors="replace") if isinstance(inhalt, bytes) else inhalt
        text = normalisiere(text)
        try:
            turns = {
                "vtt": _parse_vtt, "srt": _parse_srt, "json": _parse_json,
                "csv": _parse_csv, "html": _parse_html, "txt": _parse_txt,
            }[fmt](text, befund)
        except Exception as fehler:                      # noqa: BLE001
            befund.warnungen.append(
                f"Could not be read as {fmt.upper()} ({fehler}); read as plain text.")
            befund.format = fmt = "txt"
            turns = _parse_txt(text, befund)

    turns = [t for t in turns if t.text.strip()]
    for i, t in enumerate(turns):
        t.idx = i
        t.text = re.sub(r"\s+", " ", t.text).strip()

    # Die Sprache wird vor der Sprecherzuordnung bestimmt, weil die Warnungen
    # im Befund in der Reihenfolge stehen sollen, in der die Entscheidungen
    # gefallen sind: erst welche Sprache, dann wer spricht.
    sprache_code = bestimme_sprache(turns, dateiname, befund, sprache)

    # Die Sprecherzuordnung läuft über die *ganze* Datei und nicht je Abschnitt.
    # Die Rateregel ("wer weniger redet, ist der Therapeut") wird mit mehr Text
    # nicht schlechter, und ein Sprecher, der in Sitzung 3 anders heisst als in
    # Sitzung 4, wäre schlimmer als eine unsichere Zuordnung.
    ordne_sprecher_zu(turns, befund, manuelle_sprecher)

    befund.turns = len(turns)
    befund.woerter = sum(len(t.text.split()) for t in turns)
    befund.zeitstempel = any(t.start_sek is not None for t in turns)
    if befund.turns < 6:
        befund.warnungen.append(
            "Very few turns detected. The format was probably misread — worth a "
            "look at the raw view.")

    nummer, datum, klient_aus_name = metadaten_aus_name(dateiname)
    ganz = Sitzung(
        sid=dateiname,
        dateiname=dateiname,
        turns=turns,
        nummer=nummer,
        datum=datum,
        klient_id=(klient_id or klient_aus_name or "unbekannt"),
        format=fmt,
        sprache=sprache_code,
        befund=befund,
    )

    abschnitte = _abschnitte_aus_marken(befund.abschnitt_marken, len(turns))
    if not abschnitte:
        befund.sitzungen_info = [_sitzung_info(ganz)]
        return [ganz]

    sitzungen = [
        _teilsitzung(ganz, a["start"], a["ende"], i,
                     nummer=a["nummer"], datum=a["datum"], ist_segment=False)
        for i, a in enumerate(abschnitte)
    ]
    # Nummern nur dann erfinden, wenn der Text selbst keine genannt hat.
    if all(t.nummer is None for t in sitzungen):
        for i, t in enumerate(sitzungen, start=1):
            t.nummer = i
    _sprache_je_abschnitt(sitzungen, befund, sprache)

    befund.teilung = "separator"
    befund.sitzungen_info = [_sitzung_info(t) for t in sitzungen]
    return sitzungen


def _sprache_je_abschnitt(sitzungen: list[Sitzung], befund: Befund,
                          manuell: str | None) -> None:
    """Bestimmt die Sprache je Abschnitt neu, ohne den Befund vollzuschreiben.

    Ein Klient, der mitten in der Behandlung die Sprache wechselt, soll nicht
    ein Jahr lang mit einem gemittelten Urteil analysiert werden. Eine Vorgabe
    von aussen oder aus dem Dateinamen bleibt unangetastet: die hat jemand
    absichtlich gesetzt.
    """
    if manuell or befund.sprache_quelle in ("manuell", "dateiname"):
        return
    abweichend = 0
    for s in sitzungen:
        text = " ".join(t.text for t in s.turns)
        code, sicherheit, _ = sprachen.erkenne(text)
        # erkenne() verweigert unter 25 Wörtern und gibt dann Sicherheit 0
        # zurück — dann bleibt es beim Urteil über die ganze Datei.
        if sicherheit > 0:
            s.sprache = code
            if code != befund.sprache:
                abweichend += 1
    if abweichend:
        befund.warnungen.append(
            f"{abweichend} of {len(sitzungen)} sections were detected as the "
            "other language and are analysed with that language’s word lists. "
            "Levels do not compare across the language line.")


# ---------------------------------------------------------------------------
# Aufteilen
# ---------------------------------------------------------------------------

def _abschnitte_aus_marken(marken: list[dict], n_turns: int) -> list[dict]:
    """Waehlt die brauchbaren Marken aus und macht Abschnittsgrenzen daraus.

    Starke Marken schlagen schwache: wer "Sitzung 7" schreibt, meint es, wer
    eine Linie zieht, vielleicht auch nur Zierde. Schwache Marken kommen nur
    zum Zug, wenn keine starke da ist.
    """
    for art in ("stark", "schwach"):
        kandidaten = [m for m in marken if m["art"] == art and 0 <= m["turn"] <= n_turns]
        if len(kandidaten) < 2:
            continue

        # Grenzen sind die Turn-Indizes der Marken; eine Marke bei 0 ist der
        # Kopf des ersten Abschnitts, keine Trennung.
        grenzen: list[dict] = []
        for m in kandidaten:
            if grenzen and m["turn"] == grenzen[-1]["turn"]:
                continue        # zwei Marken hintereinander, etwa Linie + Datum
            grenzen.append(m)

        abschnitte = []
        for i, m in enumerate(grenzen):
            start = m["turn"]
            ende = grenzen[i + 1]["turn"] if i + 1 < len(grenzen) else n_turns
            abschnitte.append({"start": start, "ende": ende,
                               "nummer": m["nummer"], "datum": m["datum"]})
        if abschnitte and abschnitte[0]["start"] > 0:
            # Text vor der ersten Marke gehoert zum ersten Abschnitt.
            abschnitte[0]["start"] = 0

        # Streuner anhaengen statt als Sitzung zaehlen.
        verdichtet: list[dict] = []
        for a in abschnitte:
            if verdichtet and (a["ende"] - a["start"]) < MIN_TURNS_JE_ABSCHNITT:
                verdichtet[-1]["ende"] = a["ende"]
            else:
                verdichtet.append(a)
        if len(verdichtet) >= 2:
            return verdichtet
    return []


def segmentiere(sitzung: "Sitzung", anzahl: int | None = None) -> list["Sitzung"]:
    """Schneidet eine Sitzung in gleich grosse Stuecke.

    Die Rueckfallebene fuer einen langen Text ohne jede Sitzungsmarke. Die
    Stuecke heissen "Segment", nicht "Session", und der Befund sagt, dass hier
    geschnitten und nicht gelesen wurde — ein Segmentwechsel ist eine Stelle im
    Text, keine Stelle in der Behandlung.
    """
    turns = sitzung.turns
    if anzahl is None:
        anzahl = SEGMENT_ZIEL
    anzahl = max(SEGMENT_MIN, min(SEGMENT_MAX, anzahl))
    if len(turns) < anzahl * MIN_TURNS_JE_ABSCHNITT:
        anzahl = len(turns) // MIN_TURNS_JE_ABSCHNITT
    if anzahl < 2:
        return [sitzung]

    gross, rest = divmod(len(turns), anzahl)
    stuecke: list[Sitzung] = []
    pos = 0
    for i in range(anzahl):
        laenge = gross + (1 if i < rest else 0)
        stuecke.append(_teilsitzung(sitzung, pos, pos + laenge, i, nummer=i + 1,
                                    datum=None, ist_segment=True))
        pos += laenge

    if sitzung.befund is not None:
        sitzung.befund.teilung = "segmente"
        sitzung.befund.warnungen.append(
            f"No session markers found in this text, so it was cut into {anzahl} "
            "equal segments. The trend is a trend *within* the text, not between "
            "sessions. Put a line like \u201c--- Session 7 \u2014 2024-03-14 ---\u201d "
            "between your sessions and it will be read as written.")
        sitzung.befund.sitzungen_info = [_sitzung_info(t) for t in stuecke]
    return stuecke


def _teilsitzung(quelle: "Sitzung", start: int, ende: int, idx: int,
                 nummer: int | None, datum: str | None,
                 ist_segment: bool) -> "Sitzung":
    # Turn-Indizes werden je Sitzung neu vergeben, weil alles Spaetere
    # (Belegstellen, KWIC, Faeden) sie als Adresse innerhalb der Sitzung liest.
    turns = quelle.turns[start:ende]
    for i, t in enumerate(turns):
        t.idx = i
    return Sitzung(
        sid=f"{quelle.sid}#{idx + 1}",
        dateiname=quelle.dateiname,
        turns=turns,
        nummer=nummer,
        datum=datum or quelle.datum,
        klient_id=quelle.klient_id,
        format=quelle.format,
        sprache=quelle.sprache,
        befund=quelle.befund,
        quelle_idx=idx,
        ist_segment=ist_segment,
    )


def _sitzung_info(s: "Sitzung") -> dict:
    return {
        "nr": s.nummer,
        "datum": s.datum,
        "turns": len(s.turns),
        "woerter": sum(len(t.text.split()) for t in s.turns),
        "sprache": s.sprache,
        "istSegment": s.ist_segment,
    }


def sortiere_sitzungen(sitzungen: list[Sitzung]) -> list[Sitzung]:
    """Chronologisch: Datum vor Nummer vor Dateiname. Nummern werden
    anschliessend lückenlos neu vergeben, damit die Arc-Achse stimmt."""
    def schluessel(s: Sitzung):
        # ``quelle_idx`` hält aus einer Datei geschnittene Sitzungen in der
        # Reihenfolge, in der sie im Text standen — auch wenn keine von ihnen
        # ein Datum trägt und der Dateiname für alle derselbe ist.
        return (s.datum or "9999-99-99",
                s.nummer if s.nummer is not None else 9999,
                s.dateiname,
                s.quelle_idx)
    geordnet = sorted(sitzungen, key=schluessel)
    for i, s in enumerate(geordnet, start=1):
        if s.nummer is None:
            s.nummer = i
    return geordnet
