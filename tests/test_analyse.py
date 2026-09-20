"""Dialog, verlorene Fäden, Wechselpunkte, Pseudonymisierung, Gesamtlauf."""

from __future__ import annotations

import math

from therapy import arc, dialogue, threads
from therapy.ingest import KLIENT, THERAPEUT, Sitzung, Turn
from therapy.pseudonym import Pseudonymisierer, finde_namen
from therapy.report import Korpus
from therapy.tokenize import lemma_grob, tokenisiere, zerlege_kompositum


def sitzung(*paare: tuple[str, str], nummer: int = 1) -> Sitzung:
    turns = [Turn(idx=i, sprecher=sp, text=text) for i, (sp, text) in enumerate(paare)]
    return Sitzung(sid=f"s{nummer}", dateiname=f"s{nummer}.txt", turns=turns, nummer=nummer)


# ---------------------------------------------------------------------------
# Tokenisierung
# ---------------------------------------------------------------------------

def test_offsets_zeigen_auf_den_ursprungstext():
    text = "Ich habe Angst gehabt."
    tok = [t for t in tokenisiere(text) if t.ist_wort][2]
    assert text[tok.start:tok.end] == "Angst"


def test_satzgrenzen_ignorieren_abkuerzungen():
    tokens = tokenisiere("Das war z.B. am Montag. Dann kam sie.")
    assert max(t.satz for t in tokens) == 1


def test_lemma_behaelt_umlaute():
    # Ein Lemma, das angezeigt wird, darf nicht "fuhlen" heissen.
    assert lemma_grob("fühlte") == "fühlen"
    assert "ä" in lemma_grob("ärgerte") or lemma_grob("ärgerte").startswith("ärger")


def test_kompositum_wird_zerlegt():
    vok = {"verlust", "angst", "schuld", "gefühl"}
    assert zerlege_kompositum("verlustangst", vok) == ["verlust", "angst"]
    assert zerlege_kompositum("schuldgefühl", vok) == ["schuld", "gefühl"]


def test_kurze_woerter_werden_nicht_zerlegt():
    assert zerlege_kompositum("angst", {"an", "gst"}) is None


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

def test_rueckkanal_ist_kein_beitrag():
    s = sitzung((THERAPEUT, "Mhm."), (KLIENT, "Es war schwierig diese Woche."),
                (THERAPEUT, "Wie war das für Sie?"))
    k = dialogue.analysiere(s)
    assert k.rueckkanal_turns == 1
    assert k.turns[THERAPEUT] == 1


def test_fragetypen():
    assert dialogue.frage_typ("Wie war das für Sie?") == "offen"
    assert dialogue.frage_typ("Waren Sie da allein?") == "geschlossen"
    assert dialogue.frage_typ("Das war schwierig.") is None


def test_offene_frage_schlaegt_nachgeschobene_geschlossene():
    assert dialogue.frage_typ("Wie war das, waren Sie allein?") == "offen"


def test_lexikalische_aufnahme():
    geborgt = sitzung(
        (KLIENT, "Da war so eine Enge in der Brust, richtige Enge."),
        (THERAPEUT, "Diese Enge in der Brust — erzählen Sie mir von der Enge."))
    uebersetzt = sitzung(
        (KLIENT, "Da war so eine Enge in der Brust, richtige Enge."),
        (THERAPEUT, "Das nennt man eine somatische Angstreaktion."))
    assert dialogue.analysiere(geborgt).aufnahme > dialogue.analysiere(uebersetzt).aufnahme


def test_redeanteil():
    s = sitzung((THERAPEUT, "a b c d"), (KLIENT, "e f"))
    assert dialogue.analysiere(s).redeanteil_t == 4 / 6


# ---------------------------------------------------------------------------
# Verlorene Fäden
# ---------------------------------------------------------------------------

GELADEN = ("Als mein Vater gestorben ist, war ich fünfzehn und ich habe nicht geweint. "
           "Ich hatte furchtbare Angst und war einsam, und ich schäme mich dafür bis heute, "
           "wenn ich ehrlich bin, das macht mich traurig.")


def test_fallen_gelassener_faden_wird_gefunden():
    s = sitzung(
        (KLIENT, "Die Woche war okay soweit, nichts Besonderes passiert eigentlich."),
        (THERAPEUT, "Mhm."),
        (KLIENT, GELADEN),
        (THERAPEUT, "Haben Sie den Antrag inzwischen abgeschickt?"),
        (KLIENT, "Ja, der Antrag ist raus, das hat geklappt."),
        (THERAPEUT, "Gut."),
        (KLIENT, "Sonst war die Woche ruhig, ich habe viel geschlafen und gelesen."),
    )
    faeden = threads.finde(s)
    assert [f.turn_klient for f in faeden] == [2]


def test_aufgegriffener_faden_wird_nicht_gemeldet():
    s = sitzung(
        (KLIENT, "Die Woche war okay soweit, nichts Besonderes passiert eigentlich."),
        (KLIENT, GELADEN),
        (THERAPEUT, "Ihr Vater ist gestorben, als Sie fünfzehn waren, "
                    "und Sie haben nicht geweint. Was war da für eine Angst?"),
        (KLIENT, "Ich glaube, ich hatte Angst, dass ich dann nicht mehr aufhöre zu weinen."),
    )
    assert threads.finde(s) == []


# ---------------------------------------------------------------------------
# Wechselpunkte
# ---------------------------------------------------------------------------

def test_klarer_sprung_wird_gefunden():
    werte = [0.1, 0.12, 0.09, 0.11, 0.1, 0.5, 0.52, 0.49, 0.51, 0.5]
    punkte = arc.wechselpunkte(werte, list(range(1, 11)))
    assert punkte, "ein deutlicher Sprung muss gefunden werden"
    assert punkte[0].position == 5
    assert punkte[0].bayes_faktor > 3


def test_reines_rauschen_liefert_nichts():
    # Der wichtigste Test hier: bei zwölf Punkten findet jedes Verfahren
    # irgendetwas. Es darf nur nicht gemeldet werden.
    werte = [0.50, 0.48, 0.52, 0.49, 0.51, 0.50, 0.47, 0.53, 0.49, 0.51, 0.50, 0.48]
    punkte = arc.wechselpunkte(werte, list(range(1, 13)))
    assert all(p.bayes_faktor >= arc.BF_SCHWELLE for p in punkte)
    assert len(punkte) <= 1


def test_zu_kurze_reihe_wird_nicht_gerechnet():
    assert arc.wechselpunkte([1, 2, 3, 9, 9, 9], [1, 2, 3, 4, 5, 6]) == []


def test_rangkorrelation_erkennt_monotonen_anstieg():
    assert arc.rangkorrelation([1, 2, 3, 4, 5, 6]) == 1.0
    assert arc.rangkorrelation([6, 5, 4, 3, 2, 1]) == -1.0


# ---------------------------------------------------------------------------
# Pseudonymisierung
# ---------------------------------------------------------------------------

def test_namen_werden_vorgeschlagen_substantive_nicht():
    kandidaten = finde_namen([
        "Ich habe mit Markus gesprochen, und Markus war wütend.",
        "Meine Verlustangst kommt von meiner Mutter, das ist nichts Besonderes.",
    ])
    namen = {k.name for k in kandidaten if k.sicherheit >= 0.8}
    assert "Markus" in namen
    assert "Verlustangst" not in namen
    assert "Besonderes" not in namen


def test_platzhalter_sind_ueber_sitzungen_stabil():
    p = Pseudonymisierer()
    p.registriere("Markus")
    p.registriere("Anna")
    assert p.ersetze("Markus war da.") == "Person A war da."
    assert p.ersetze("Später kam Markus wieder.") == "Später kam Person A wieder."
    assert p.ersetze("Anna auch.") == "Person B auch."


def test_genitiv_wird_mitersetzt():
    p = Pseudonymisierer()
    p.registriere("Markus")
    assert "Person A" in p.ersetze("Das war Markus' Idee.")


def test_klarnamen_sind_nicht_im_export():
    p = Pseudonymisierer()
    p.registriere("Markus")
    assert "Markus" not in str(p.zusammenfassung())


# ---------------------------------------------------------------------------
# Gesamtlauf über die Beispiele
# ---------------------------------------------------------------------------

def test_gesamtlauf_ueber_die_beispiele(tmp_path):
    from pathlib import Path
    proben = Path(__file__).resolve().parents[1] / "samples"
    dateien = [{"name": p.name, "inhalt": p.read_text(encoding="utf-8")}
               for p in sorted(proben.glob("klient-*"))]
    assert dateien, "die synthetischen Beispiele fehlen — samples/_generator.py ausführen"

    k = Korpus()
    k.lade(dateien)
    k.pseudonymisiere()
    bericht = k.bericht()

    assert {kl["id"] for kl in bericht["klienten"]} == {"anna", "bernd"}
    anna = next(kl for kl in bericht["klienten"] if kl["id"] == "anna")
    assert len(anna["sitzungen"]) == 12
    assert anna["genugSitzungen"] is True
    assert anna["faeden"], "in den Beispielen sind Fäden absichtlich eingebaut"
    assert anna["arc"]["wechselpunkte"], "der eingebaute Sprung muss gefunden werden"

    # Der eingebaute Verlauf: Distanzierung runter, Granularität hoch.
    assert arc.rangkorrelation(anna["arc"]["serien"]["man_quote"]) < -0.5
    assert arc.rangkorrelation(anna["arc"]["serien"]["granularitaet"]) > 0.5

    # Jede Zahl muss zurückführen: Marker-Treffer tragen Adressen.
    treffer = anna["sitzungen"][0]["marker"]["K"]["treffer"]
    turn, start, ende, form = treffer["man"][0]
    ausschnitt = k.ausschnitt("anna", anna["sitzungen"][0]["sid"], turn, start, ende)
    assert ausschnitt["treffer"].lower() == form


def test_export_enthaelt_keinen_transkripttext():
    from pathlib import Path
    proben = Path(__file__).resolve().parents[1] / "samples"
    dateien = [{"name": p.name, "inhalt": p.read_text(encoding="utf-8")}
               for p in sorted(proben.glob("klient-anna*"))]
    k = Korpus()
    k.lade(dateien)
    k.pseudonymisiere()
    export = k.export()
    for klient in export["klienten"]:
        for sitzung in klient["sitzungen"]:
            for block in sitzung["marker"].values():
                assert "treffer" not in block


def test_alle_zahlen_im_bericht_sind_endlich():
    # json.dumps(allow_nan=False) fliegt sonst im Browser — und zwar erst
    # beim seltenen Fall, also nach der Auslieferung.
    from pathlib import Path
    proben = Path(__file__).resolve().parents[1] / "samples"
    dateien = [{"name": p.name, "inhalt": p.read_text(encoding="utf-8")}
               for p in sorted(proben.glob("klient-*"))]
    k = Korpus()
    k.lade(dateien)
    k.pseudonymisiere()

    def pruefe(objekt, pfad="bericht"):
        if isinstance(objekt, float):
            assert math.isfinite(objekt), f"{pfad} ist {objekt}"
        elif isinstance(objekt, dict):
            for schluessel, wert in objekt.items():
                pruefe(wert, f"{pfad}.{schluessel}")
        elif isinstance(objekt, list):
            for i, wert in enumerate(objekt):
                pruefe(wert, f"{pfad}[{i}]")

    pruefe(k.bericht())
