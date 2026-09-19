"""Einlesen: Formaterkennung, Sprecherzuordnung, und vor allem der Befund.

Der Befund ist hier wichtiger als das Parsen. Ein Parser, der danebenliegt und
es meldet, ist brauchbar. Einer, der danebenliegt und schweigt, ist gefährlich —
deshalb prüfen die Tests unten fast durchgehend, ob die *Warnung* kommt.
"""

from __future__ import annotations

import json

from therapy.ingest import (KLIENT, THERAPEUT, erkenne_format, lies,
                             metadaten_aus_name, sortiere_sitzungen)

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
    s = lies("sitzung-01.txt", TXT)
    assert len(s.turns) == 4
    assert s.turns[0].sprecher == THERAPEUT
    assert s.turns[1].sprecher == KLIENT
    # Fortsetzungszeile gehört zum selben Beitrag.
    assert "nachgedacht" in s.turns[1].text
    assert s.befund.sprecher_quelle == "labels"


def test_vtt_fasst_untertitelzeilen_zusammen():
    # Ohne Zusammenfassung zählt man Untertitel statt Redebeiträge, und jede
    # Turn-Längen-Statistik ist Unsinn.
    s = lies("sitzung-04.vtt", VTT)
    assert len(s.turns) == 2
    assert "nachgedacht" in s.turns[1].text
    assert s.hat_zeitstempel


def test_srt_und_csv():
    assert len(lies("a.srt", SRT).turns) == 2
    s = lies("a.csv", CSV)
    assert len(s.turns) == 2
    assert s.turns[0].sprecher == THERAPEUT


def test_whisper_diarisierung_wird_geraten_und_gemeldet():
    s = lies("a.json", WHISPER)
    # Anonyme Labels: wer weniger redet, wird als Therapeut angenommen …
    assert s.turns[0].sprecher == THERAPEUT
    assert s.turns[1].sprecher == KLIENT
    # … und genau das muss als Vermutung im Befund stehen.
    assert s.befund.sprecher_quelle == "geraten"
    assert any("guessed" in w.lower() for w in s.befund.warnungen)


# ---------------------------------------------------------------------------
# Ehrlicher Befund
# ---------------------------------------------------------------------------

def test_ohne_labels_werden_kennzahlen_als_nicht_verfuegbar_gemeldet():
    s = lies("roh.txt", "Es war eine schwierige Woche.\n\nIch habe nachgedacht.\n")
    assert not s.hat_sprecher
    assert "talk ratio" in s.befund.nicht_verfuegbar
    assert "dropped threads" in s.befund.nicht_verfuegbar


def test_ohne_zeitstempel_fehlen_zeitkennzahlen():
    s = lies("a.txt", TXT)
    assert not s.befund.zeitstempel
    assert "response latency" in s.befund.nicht_verfuegbar


def test_zeitstempel_machen_zeitkennzahlen_verfuegbar():
    s = lies("a.vtt", VTT)
    assert s.befund.zeitstempel
    assert "response latency" not in s.befund.nicht_verfuegbar


def test_fliesstext_ohne_sprecher_wird_nicht_zerhackt():
    # Ein Doppelpunkt im Fliesstext darf keinen Sprecherwechsel erzeugen.
    text = "Ich dachte mir nur: das kann doch nicht wahr sein.\n"
    s = lies("a.txt", text)
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
    a = lies("klient-x_sitzung-02_2024-02-01.txt", TXT)
    b = lies("klient-x_sitzung-01_2024-01-01.txt", TXT)
    geordnet = sortiere_sitzungen([a, b])
    assert [s.nummer for s in geordnet] == [1, 2]
