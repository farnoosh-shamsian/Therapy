"""Korpuswerkzeuge: Keyness, Wortverlauf, Vokabelbewegung, Kollokationen, TTR."""

from __future__ import annotations

from therapy.ingest import KLIENT, lies
from therapy.lexical import Index, referenzfrequenzen


def _sitzungen(saetze_je_sitzung: list[str]):
    """Eine Sitzung je Eintrag, Klientenrede mit fester."""
    sitzungen = []
    for i, satz in enumerate(saetze_je_sitzung, start=1):
        text = (f"--- Session {i} ---\n"
                f"Therapeut: Wie war die Woche?\n"
                f"Klientin: {satz}\n"
                f"Therapeut: Erzählen Sie mehr davon.\n"
                f"Klientin: {satz}\n")
        sitzungen.extend(lies(f"s{i:02d}.txt", text))
    return sitzungen


# Zwölf Sitzungen:
STEIGT_UND_FAELLT = _sitzungen([
    "Ich habe Angst gehabt und wieder Angst und nur Angst vor allem.",
    "Ich habe Angst gehabt und wieder Angst vor dieser Sache.",
    "Ich habe Angst gehabt und Angst vor dem Gespräch gehabt.",
    "Ich habe Angst gehabt und Angst vor dem Abend gehabt.",
    "Ich habe etwas Wut gespürt, zum ersten Mal überhaupt.",
    "Ich habe Wut gespürt und Wut benannt, das war neu.",
    "Ich habe Wut gespürt und Wut benannt und Wut gezeigt.",
    "Ich habe Wut gespürt und Wut benannt und Wut ausgehalten.",
    "Ich habe Wut gespürt und Wut benannt und Wut verstanden.",
    "Ich habe Wut gespürt und Wut benannt und Wut angenommen.",
    "Ich habe Wut gespürt und Wut benannt und Wut behalten.",
    "Ich habe Wut gespürt und einen schweren Rucksack abgestellt.",
])


def _index():
    return Index(STEIGT_UND_FAELLT)


def _anzeigen(eintraege) -> set[str]:
    """Die angezeigten Wortformen einer Ergebnisliste."""
    return {e["anzeige"] for e in eintraege}


# ---------------------------------------------------------------------------
# Wortverlauf
# ---------------------------------------------------------------------------

def test_wortverlauf_findet_die_eingebaute_bewegung():
    idx = _index()
    angst = idx.wortverlauf("Angst", KLIENT)
    wut = idx.wortverlauf("Wut", KLIENT)

    assert len(angst["werte"]) == 12
    # Angst geht runter, Wut geht hoch
    assert angst["werte"][0] > angst["werte"][-1]
    assert wut["werte"][0] < wut["werte"][-1]
    assert angst["werte"][-1] == 0.0
    assert wut["werte"][0] == 0.0


def test_wortverlauf_ist_eine_rate_keine_rohzahl():
    # Sonst hat die längere Stunde automatisch mehr.
    idx = _index()
    verlauf = idx.wortverlauf("Wut", KLIENT)
    assert verlauf["roh"][-1] >= 1
    assert verlauf["werte"][-1] != verlauf["roh"][-1]
    assert verlauf["gesamt"] == sum(verlauf["roh"])


def test_wortverlauf_eines_unbekannten_wortes_ist_leer_aber_wohlgeformt():
    verlauf = _index().wortverlauf("Nilpferd", KLIENT)
    assert verlauf["gesamt"] == 0
    assert set(verlauf["werte"]) == {0.0}
    assert len(verlauf["nummern"]) == 12


# ---------------------------------------------------------------------------
# Vokabelbewegung
# ---------------------------------------------------------------------------

def test_vokabelbewegung_trennt_steigend_von_fallend():
    bewegung = _index().vokabelbewegung(KLIENT, min_frequenz=4)
    assert bewegung["genug"] is True
    steigend = _anzeigen(bewegung["steigend"])
    fallend = _anzeigen(bewegung["fallend"])
    assert "wut" in steigend
    assert "angst" in fallend
    # Ein Wort kann nicht beides sein.
    assert not steigend & fallend


def test_vokabelbewegung_meldet_was_frueh_aufhoert():
    bewegung = _index().vokabelbewegung(KLIENT, min_frequenz=4)
    assert "angst" in _anzeigen(bewegung["verschwunden"])


def test_vokabelbewegung_rechnet_unter_vier_sitzungen_nicht():
    # Eine Rangkorrelation über drei Punkte ist keine.
    kurz = Index(_sitzungen(["Ich habe Angst gehabt."] * 3))
    assert kurz.vokabelbewegung(KLIENT)["genug"] is False
    assert kurz.vokabelbewegung(KLIENT)["steigend"] == []


# ---------------------------------------------------------------------------
# Keyness ohne zweiten Klienten
# ---------------------------------------------------------------------------

def test_keyness_je_sitzung_findet_das_einmalige_wort():
    idx = _index()
    letzte = idx.sitzungen[-1]
    assert "rucksack" in _anzeigen(idx.keyness_sitzung(letzte, KLIENT, min_frequenz=2))


def test_keyness_je_sitzung_ist_bei_einer_einzigen_sitzung_leer():
    # Es gibt dann nichts, wogegen sich etwas.
    eine = Index(_sitzungen(["Ich habe Angst gehabt und viel nachgedacht."]))
    assert eine.keyness_sitzung(eine.sitzungen[0], KLIENT) == []


def test_keyness_phase_stellt_spaet_gegen_frueh():
    phase = _index().keyness_phase(KLIENT, min_frequenz=3)
    assert phase["genug"] is True
    assert "wut" in _anzeigen(phase["spaet"])
    assert "angst" in _anzeigen(phase["frueh"])


def test_keyness_phase_braucht_vier_sitzungen():
    kurz = Index(_sitzungen(["Ich habe Angst gehabt."] * 3))
    assert kurz.keyness_phase(KLIENT)["genug"] is False


def test_keyness_zeigt_nur_was_heraussticht():
    # Die Achsen "diese Sitzung" und "späte Hälfte".
    phase = _index().keyness_phase(KLIENT, min_frequenz=3)
    assert all(e["ll"] >= 0 for e in phase["spaet"])
    assert all(e["ll"] >= 0 for e in phase["frueh"])


def test_keyness_traegt_effektstaerke_neben_signifikanz():
    # G² wächst mit der Textmenge; ohne Log.
    phase = _index().keyness_phase(KLIENT, min_frequenz=3)
    assert phase["spaet"], "die späte Hälfte muss etwas hergeben"
    for eintrag in phase["spaet"]:
        assert "logRatio" in eintrag
        if eintrag["logRatio"] is not None:
            assert eintrag["logRatio"] > 0


# ---------------------------------------------------------------------------
# Keyness zwischen Klienten
# ---------------------------------------------------------------------------

def test_keyness_gegen_anderen_klienten():
    a = _index()
    b = Index(_sitzungen(["Ich denke oft an den Garten und die Blumen dort."] * 6))
    referenz, n = referenzfrequenzen([a, b], ausser=a)
    woerter = _anzeigen(a.keyness(referenz, n, KLIENT, min_frequenz=4))
    assert {"wut", "angst"} & woerter


# ---------------------------------------------------------------------------
# Anzeigeform
# ---------------------------------------------------------------------------

def test_anzeigeform_gibt_eine_gesprochene_form_zurueck():
    # Der Lemmatisierer ist grob; angezeigt wird, was.
    idx = _index()
    lemma = idx._lemma("gespürt")
    assert idx.anzeigeform(lemma) in {t.klein
                                      for toks in idx.tokens.values()
                                      for t in toks if t.ist_wort}


def test_anzeigeform_eines_unbekannten_lemmas_faellt_auf_sich_selbst_zurueck():
    assert _index().anzeigeform("nilpferd") == "nilpferd"


# ---------------------------------------------------------------------------
# Kollokationen, KWIC, TTR
# ---------------------------------------------------------------------------

def test_kollokationen_finden_den_nachbarn():
    idx = _index()
    nachbarn = {e["wort"] for e in idx.kollokationen("Wut", KLIENT)}
    assert nachbarn, "Kollokationen dürfen nicht leer sein"
    assert any(w.startswith("benann") or w.startswith("gesp") for w in nachbarn)


def test_kwic_fuehrt_zu_einer_adresse():
    zeilen = _index().kwic("Rucksack")
    assert zeilen
    z = zeilen[0]
    assert z["sid"] and z["turn"] is not None
    assert "rucksack" in (z["treffer"] + z["links"] + z["rechts"]).lower()


def test_ttr_meldet_ob_es_belastbar_ist():
    idx = _index()
    ttr = idx.ttr(idx.sitzungen[0], KLIENT)
    assert 0.0 <= ttr["sttr"] <= 1.0
    # Zwei kurze Beiträge sind unter dem 100-Token-Fenster.
    assert ttr["belastbar"] is False
