"""Was der Export *nicht* enthalten darf."""

from __future__ import annotations

import json

from therapy.ingest import KLIENT, THERAPEUT
from therapy.report import Korpus

# Sprecherlabels als blosse Vornamen
TEXT = """Claire: Wie war die Woche?

Anna: Schwierig. Ich habe viel an Markus gedacht und hätte gern etwas gesagt,
aber man traut sich ja nicht.

Claire: Was hätten Sie denn gern gesagt?

Anna: Dass ich Angst habe. Richtig Angst, seit Wochen schon.
"""


def geladener_korpus() -> Korpus:
    korpus = Korpus()
    korpus.lade([{"name": "klientin-anna-weber_sitzung-01_2024-03-14.txt",
                  "inhalt": TEXT}])
    korpus.pseudonymisiere()
    return korpus


def test_export_traegt_weder_fallnamen_noch_dateinamen():
    korpus = geladener_korpus()
    korpus.klient_umbenennen(korpus.bericht()["klienten"][0]["id"], "Anna Weber")
    roh = json.dumps(korpus.export(), ensure_ascii=False)

    assert "Anna Weber" not in roh
    assert "anna" not in roh.lower()
    assert "weber" not in roh.lower()
    assert "klientin-anna" not in roh.lower()
    assert ".txt" not in roh
    # Die Sprecherlabels aus dem Dokument.
    assert "claire" not in roh.lower()


def test_export_nennt_den_fall_stabil_und_neutral():
    export = geladener_korpus().export()
    assert export["klienten"][0]["id"] == "Case A"
    assert export["klienten"][0]["sitzungen"][0]["titel"] == "Session 1"


def test_export_traegt_keine_transkriptzeilen():
    korpus = geladener_korpus()
    export = korpus.export()
    roh = json.dumps(export, ensure_ascii=False)

    # Ein ganzer Satz aus dem Transkript
    assert "traut sich ja nicht" not in roh
    assert "Was hätten Sie denn gern gesagt" not in roh
    assert "Wie war die Woche" not in roh
    for klient in export["klienten"]:
        assert all("inhalt" not in f for f in klient["faeden"])
        for sitzung in klient["sitzungen"]:
            assert all("inhalt" not in f for f in sitzung["faeden"])
            assert "frageBelege" not in sitzung["dialog"]
            # Die Zahl bleibt
            assert "fragenOffen" in sitzung["dialog"]
            for block in sitzung["marker"].values():
                assert "treffer" not in block


def test_die_sitzungskennung_ist_nicht_mehr_der_dateiname():
    export = geladener_korpus().export()
    sid = export["klienten"][0]["sitzungen"][0]["sid"]
    assert sid == "Case A · session 1"


def test_die_befundwarnung_behaelt_die_rolle_und_verliert_den_namen():
    befund = geladener_korpus().export()["klienten"][0]["sitzungen"][0]["befund"]
    geraten = [w for w in befund["warnungen"] if "therapist" in w.lower()]
    assert geraten, "ohne Rate-Warnung prüft dieser Test nichts"
    assert all("Claire" not in w and "Anna" not in w for w in geraten)
    assert befund["labels"] == []


def test_bericht_traegt_die_belege_weiterhin():
    # Gegenprobe über ein ganzes Korpus.
    bericht = geladener_korpus().bericht()
    sitzung = bericht["klienten"][0]["sitzungen"][0]
    assert any("treffer" in block for block in sitzung["marker"].values())
    assert sitzung["dateiname"].endswith(".txt")


def test_namenstabelle_ist_nie_teil_des_exports():
    korpus = geladener_korpus()
    tabelle = korpus.namenstabelle()
    assert tabelle, "ohne erkannte Namen prüft dieser Test nichts"
    roh = json.dumps(korpus.export(), ensure_ascii=False)
    for zeile in tabelle:
        for wert in zeile.values():
            if isinstance(wert, str) and len(wert) > 3 and " " not in wert:
                continue
        assert json.dumps(zeile, ensure_ascii=False) not in roh
    # Die Zusammenfassung darf mit.
    zus = korpus.export()["export"]["pseudonyme"]
    assert set(zus) == {"ersetzt", "praefix", "modus"}
    assert zus["modus"] == "pseudonyme"


def test_speicher_wird_beim_verwerfen_wirklich_leer():
    # Discard muss dasselbe leisten wie ein Reload.
    korpus = geladener_korpus()
    korpus.bericht()
    korpus.leeren()
    assert korpus.sitzungen == []
    assert korpus.namenstabelle() == []
    assert korpus.bericht()["klienten"] == []


# ---------------------------------------------------------------------------
# Die Gegenprobe über ein ganzes Korpus
# ---------------------------------------------------------------------------

import re
from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def beispiel_korpus() -> Korpus:
    dateien = [{"name": p.name, "inhalt": p.read_text(encoding="utf-8")}
               for p in sorted(SAMPLES.glob("client-claire_session-*"))]
    assert len(dateien) == 12, "die Beispielsitzungen fehlen"
    korpus = Korpus()
    korpus.lade(dateien)
    korpus.pseudonymisiere()
    return korpus


def test_kein_satz_aus_zwoelf_sitzungen_ueberlebt_den_export():
    korpus = beispiel_korpus()
    roh = json.dumps(korpus.export(), ensure_ascii=False)
    quelle = " ".join(p.read_text(encoding="utf-8")
                      for p in sorted(SAMPLES.glob("client-claire_session-*")))
    woerter = re.findall(r"[A-Za-z']+", quelle)
    durchgekommen = {" ".join(woerter[i:i + 5]) for i in range(len(woerter) - 5)}
    durchgekommen = sorted(g for g in durchgekommen if g in roh)
    assert not durchgekommen, f"wörtlich im Export: {durchgekommen[:5]}"


def test_kein_dateiname_ueberlebt_den_export():
    roh = json.dumps(beispiel_korpus().export(), ensure_ascii=False).lower()
    for p in sorted(SAMPLES.glob("client-claire_session-*")):
        assert p.name.lower() not in roh
        assert p.stem.lower() not in roh
    for endung in (".txt", ".csv", ".vtt", ".srt", ".json", ".docx"):
        assert endung not in roh


def test_klarnamen_modus_verschweigt_sich_nicht():
    """Ohne Ersetzung darf der Export nicht so tun, als sei ersetzt worden."""
    korpus = Korpus()
    korpus.lade([{"name": "klientin-anna-weber_sitzung-01_2024-03-14.txt",
                  "inhalt": TEXT}])
    korpus.pseudonymisiere(ersetzen=False)
    export = korpus.export()

    assert export["export"]["pseudonyme"]["modus"] == "klarnamen"
    assert export["export"]["pseudonyme"]["ersetzt"] == 0
    # Der Hinweis muss den Modus benennen, sonst liest jemand die Zusicherung
    # des Normalfalls in eine Datei, für die sie nicht gilt.
    assert "kept" in export["export"]["hinweis"].lower()

    # Dateiname, Fallname und Sitzungskennung bleiben auch hier neutral.
    roh = json.dumps(export, ensure_ascii=False)
    assert ".txt" not in roh
    assert export["klienten"][0]["id"] == "Case A"


def klarnamen_korpus() -> Korpus:
    korpus = Korpus()
    korpus.lade([{"name": "klientin-anna-weber_sitzung-01_2024-03-14.txt",
                  "inhalt": TEXT}])
    korpus.pseudonymisiere(ersetzen=False)
    return korpus


def test_klarnamen_lassen_den_text_unangetastet():
    text = " ".join(t.text for s in klarnamen_korpus().sitzungen for t in s.turns)
    assert "Markus" in text
    assert "Person A" not in text


def test_klarnamen_erkennen_trotzdem_wer_eine_person_ist():
    # Das Soziogramm hängt daran: ohne Personenliste keine Knoten.
    tabelle = klarnamen_korpus().namenstabelle()
    assert tabelle, "auch ohne Ersetzung müssen Namen erkannt werden"
    assert all(zeile["platzhalter"] == zeile["name"] for zeile in tabelle)


def test_der_schalter_laesst_sich_umlegen():
    korpus = klarnamen_korpus()
    korpus.pseudonymisiere(ersetzen=True)
    text = " ".join(t.text for s in korpus.sitzungen for t in s.turns)
    assert "Markus" not in text
    assert "Person" in text
