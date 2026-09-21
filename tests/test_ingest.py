"""Einlesen: Formate, Parsen, Sprecher."""

from __future__ import annotations

import json

from therapy.ingest import (KLIENT, THERAPEUT, erkenne_format, lies,
                             metadaten_aus_name, sortiere_sitzungen)


def lies_eine(*args, **kwargs):
    """Liest einen Text, der genau eine Sitzung."""
    sitzungen = lies(*args, **kwargs)
    assert len(sitzungen) == 1, f"unerwartet {len(sitzungen)} Sitzungen"
    return sitzungen[0]

TXT = """\
Therapeut: Wie geht es Ihnen heute?

Klientin: Es war eine schwierige Woche.
Ich habe viel nachgedacht.

Therapeut: Mhm.

Klientin: Aber es geht schon.
"""

VTT = """WEBVTT

00:00:01.000 --> 00:00:04.000
<v Therapeut>Wie geht es Ihnen heute?

00:00:06.500 --> 00:00:09.000
<v Klientin>Es war eine schwierige Woche.

00:00:09.100 --> 00:00:11.000
<v Klientin>Ich habe viel nachgedacht.
"""

SRT = """1
00:00:01,000 --> 00:00:04,000
T: Wie geht es Ihnen?

2
00:00:05,000 --> 00:00:08,000
K: Ganz gut, danke.
"""

CSV = """sprecher;text;start
Therapeut;"Wie geht es Ihnen heute?";00:00:01
Klientin;"Es war schwierig.";00:00:06
"""

WHISPER = json.dumps({
    "segments": [
        {"start": 1.0, "end": 4.0, "speaker": "SPEAKER_00", "text": "Wie geht es Ihnen?"},
        {"start": 5.0, "end": 12.0, "speaker": "SPEAKER_01",
         "text": "Es war eine wirklich schwierige Woche für mich gewesen, ehrlich gesagt."},
        {"start": 12.2, "end": 18.0, "speaker": "SPEAKER_01",
         "text": "Ich habe kaum geschlafen und mich schlecht gefühlt."},
    ]
})


# ---------------------------------------------------------------------------
# Formaterkennung
# ---------------------------------------------------------------------------

def test_formate_werden_erkannt():
    assert erkenne_format("a.txt", TXT) == "txt"
    assert erkenne_format("a.vtt", VTT) == "vtt"
    assert erkenne_format("a.srt", SRT) == "srt"
    assert erkenne_format("a.csv", CSV) == "csv"
    assert erkenne_format("a.json", WHISPER) == "json"


def test_format_wird_auch_ohne_endung_erkannt():
    assert erkenne_format("ohne_endung", VTT) == "vtt"
    assert erkenne_format("ohne_endung", WHISPER) == "json"


# ---------------------------------------------------------------------------
# Parsen
# ---------------------------------------------------------------------------

def test_txt_mit_labels():
    s = lies_eine("sitzung-01.txt", TXT)
    assert len(s.turns) == 4
    assert s.turns[0].sprecher == THERAPEUT
    assert s.turns[1].sprecher == KLIENT
    # Fortsetzungszeile gehört zum selben Beitrag.
    assert "nachgedacht" in s.turns[1].text
    assert s.befund.sprecher_quelle == "labels"


def test_vtt_fasst_untertitelzeilen_zusammen():
    # Ohne Zusammenfassung zählt man Untertitel statt Redebeiträge.
    s = lies_eine("sitzung-04.vtt", VTT)
    assert len(s.turns) == 2
    assert "nachgedacht" in s.turns[1].text
    assert s.hat_zeitstempel


def test_srt_und_csv():
    assert len(lies_eine("a.srt", SRT).turns) == 2
    s = lies_eine("a.csv", CSV)
    assert len(s.turns) == 2
    assert s.turns[0].sprecher == THERAPEUT


def test_whisper_diarisierung_wird_geraten_und_gemeldet():
    s = lies_eine("a.json", WHISPER)
    # Anonyme Labels:
    assert s.turns[0].sprecher == THERAPEUT
    assert s.turns[1].sprecher == KLIENT
    # … und genau das muss als Vermutung.
    assert s.befund.sprecher_quelle == "geraten"
    assert any("guessed" in w.lower() for w in s.befund.warnungen)


# ---------------------------------------------------------------------------
# Ehrlicher Befund
# ---------------------------------------------------------------------------

def test_ohne_labels_werden_kennzahlen_als_nicht_verfuegbar_gemeldet():
    s = lies_eine("roh.txt", "Es war eine schwierige Woche.\n\nIch habe nachgedacht.\n")
    assert not s.hat_sprecher
    assert "talk ratio" in s.befund.nicht_verfuegbar
    assert "dropped threads" in s.befund.nicht_verfuegbar


def test_zeitstempel_werden_erkannt_oder_eben_nicht():
    # Zeitkennzahlen selbst gibt es nicht mehr; ob.
    assert not lies_eine("a.txt", TXT).befund.zeitstempel
    assert lies_eine("a.vtt", VTT).befund.zeitstempel


def test_fliesstext_ohne_sprecher_wird_nicht_zerhackt():
    # Ein Doppelpunkt im Fliesstext darf keinen Sprecherwechsel.
    text = "Ich dachte mir nur: das kann doch nicht wahr sein.\n"
    s = lies_eine("a.txt", text)
    assert len(s.turns) == 1


# ---------------------------------------------------------------------------
# Metadaten und Reihenfolge
# ---------------------------------------------------------------------------

def test_metadaten_aus_dateinamen():
    nr, datum, klient = metadaten_aus_name("klient-anna_sitzung-07_2024-03-14.txt")
    assert nr == 7
    assert datum == "2024-03-14"
    assert klient == "anna"


def test_sortierung_nach_datum():
    a = lies_eine("klient-x_sitzung-02_2024-02-01.txt", TXT)
    b = lies_eine("klient-x_sitzung-01_2024-01-01.txt", TXT)
    geordnet = sortiere_sitzungen([a, b])
    assert [s.nummer for s in geordnet] == [1, 2]


# ---------------------------------------------------------------------------
# Ein langer Text, mehrere Sitzungen
# ---------------------------------------------------------------------------

def _jahr(marke):
    """Drei Sitzungen, getrennt durch die übergebene Markenzeile."""
    block = ("Therapeut: Wie war die Woche?\n"
             "Klientin: Schwierig. Ich habe viel darüber nachgedacht.\n"
             "Therapeut: Erzählen Sie mehr davon.\n"
             "Klientin: Es ging mir damit nicht besonders gut.\n")
    return "\n".join((marke % i) + "\n" + block for i in (1, 2, 3))


def test_sitzungsmarken_trennen_einen_langen_text():
    sitzungen = lies("jahr.txt", _jahr("--- Session %d ---"))
    assert len(sitzungen) == 3
    assert [s.nummer for s in sitzungen] == [1, 2, 3]
    assert all(len(s.turns) == 4 for s in sitzungen)
    assert sitzungen[0].befund.teilung == "separator"


def test_marke_gibt_nummer_und_datum_her():
    sitzungen = lies("jahr.txt",
                     "--- Session 7 — 2024-03-14 ---\n"
                     "Therapeut: Wie war die Woche?\n"
                     "Klientin: Schwierig, ich habe viel nachgedacht.\n"
                     "Therapeut: Erzählen Sie.\n"
                     "Klientin: Es war eine lange Woche für mich.\n"
                     "\n### Sitzung 8\n"
                     "Therapeut: Und heute?\n"
                     "Klientin: Heute geht es mir etwas besser damit.\n"
                     "Therapeut: Das freut mich zu hören.\n"
                     "Klientin: Mich eigentlich auch, ja.\n")
    assert [s.nummer for s in sitzungen] == [7, 8]
    assert sitzungen[0].datum == "2024-03-14"


def test_datumszeile_allein_ist_eine_marke():
    sitzungen = lies("jahr.txt", _jahr("2024-01-0%d"))
    assert len(sitzungen) == 3
    assert [s.datum for s in sitzungen] == ["2024-01-01", "2024-01-02", "2024-01-03"]


def test_sitzungskopf_wird_nicht_mehr_als_rede_verschluckt():
    # Vorher fiel "Session 3:" durch die Labelprüfung.
    sitzungen = lies("jahr.txt", _jahr("Session %d:"))
    assert len(sitzungen) == 3
    assert not any("Session" in t.text for s in sitzungen for t in s.turns)


def test_eine_einzelne_marke_trennt_nicht():
    # Eine Marke ist ein Kopf, keine Trennung.
    text = ("--- Session 1 ---\n"
            "Therapeut: Wie war die Woche?\n"
            "Klientin: Schwierig, ich habe viel nachgedacht darüber.\n")
    assert len(lies("a.txt", text)) == 1


def test_turn_indizes_beginnen_je_sitzung_neu():
    # Belegstellen, KWIC und Fäden lesen den Index.
    sitzungen = lies("jahr.txt", _jahr("--- Session %d ---"))
    for s in sitzungen:
        assert [t.idx for t in s.turns] == [0, 1, 2, 3]


def test_zwoelf_benannte_dateien_werden_nicht_noch_einmal_zerschnitten():
    # Wer seine Stunden ordentlich ablegt, bekommt sie.
    from therapy.report import Korpus
    korpus = Korpus()
    korpus.lade([{"name": f"klient-a_sitzung-{i:02d}_2024-01-{i:02d}.txt",
                  "inhalt": TXT} for i in range(1, 13)])
    assert len(korpus.sitzungen) == 12
    assert not any(s.ist_segment for s in korpus.sitzungen)


def test_langer_text_ohne_marken_wird_segmentiert():
    from therapy.ingest import SEGMENT_MIN_WOERTER
    from therapy.report import Korpus

    paar = ("Therapeut: Wie war denn diese Woche für Sie bisher gewesen?\n"
            "Klientin: Es war eine wirklich schwierige Woche und ich habe sehr "
            "viel über alles nachgedacht was zuletzt passiert ist.\n")
    text = paar * 400
    assert len(text.split()) > SEGMENT_MIN_WOERTER

    korpus = Korpus()
    korpus.lade([{"name": "jahr.txt", "inhalt": text}])
    assert len(korpus.sitzungen) > 1
    assert all(s.ist_segment for s in korpus.sitzungen)
    assert korpus.sitzungen[0].titel.startswith("Segment")
    assert korpus.sitzungen[0].befund.teilung == "segmente"
    # Und es steht als Warnung im Befund.
    assert any("equal segments" in w for w in korpus.sitzungen[0].befund.warnungen)


def test_kurzer_text_ohne_marken_bleibt_eine_sitzung():
    from therapy.report import Korpus
    korpus = Korpus()
    korpus.lade([{"name": "eine.txt", "inhalt": TXT}])
    assert len(korpus.sitzungen) == 1
    assert not korpus.sitzungen[0].ist_segment
