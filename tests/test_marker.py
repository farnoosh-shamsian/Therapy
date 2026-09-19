"""Handgeprüfte deutsche Sätze, ein Block pro Marker.

Diese Datei ist die eigentliche Dokumentation der Marker. Jeder Satz hier
wurde von Hand daraufhin angesehen, ob der Marker treffen *soll* — und
mindestens ein Gegenbeispiel pro Marker steht dabei, weil eine Liste, die nur
Treffer enthält, nichts beweist.

Wo ein Marker bewusst ungenau ist, steht das als Test mit ``xfail``-Kommentar
und nicht als stiller Fehler.
"""

from __future__ import annotations

import pytest

from therapy.ingest import KLIENT, Sitzung, Turn
from therapy.markers import analysiere_sitzung, kennzahlen


def _sitzung(*saetze: str) -> Sitzung:
    turns = [Turn(idx=i, sprecher=KLIENT, text=text) for i, text in enumerate(saetze)]
    return Sitzung(sid="t", dateiname="t.txt", turns=turns, nummer=1)


def zaehle(marker: str, *saetze: str) -> int:
    sm = analysiere_sitzung(_sitzung(*saetze))[KLIENT]
    return sm.zaehler.get(marker, 0)


def werte(*saetze: str) -> dict:
    return kennzahlen(analysiere_sitzung(_sitzung(*saetze))[KLIENT])


# ---------------------------------------------------------------------------
# man vs. ich
# ---------------------------------------------------------------------------

def test_man_wird_gezaehlt():
    assert zaehle("man", "Man fühlt sich dann halt schlecht.") == 1


def test_man_nicht_in_zusammensetzungen():
    # "manchmal" und "manche" dürfen nicht als "man" durchgehen.
    assert zaehle("man", "Manchmal ist das so, manche sagen das auch.") == 0


def test_man_quote_gegen_ich():
    w = werte("Man macht das halt.", "Ich mache das.")
    assert w["man_quote"] == pytest.approx(0.5)


def test_ich_kasus_unterscheidet_subjekt_und_erlebenden():
    w = werte("Ich habe ihm das gesagt.")
    assert w["ich_nominativ_anteil"] == 1.0
    w = werte("Mir ist das einfach passiert.")
    assert w["ich_nominativ_anteil"] == 0.0


# ---------------------------------------------------------------------------
# Konjunktiv II
# ---------------------------------------------------------------------------

def test_konjunktiv_eindeutige_umlautformen():
    assert zaehle("konjunktiv2", "Ich hätte das gekonnt, wenn ich wollte.") == 1
    assert zaehle("konjunktiv2", "Das wäre schön, und es könnte klappen.") == 2


def test_konjunktiv_ambige_formen_getrennt():
    # "sollte" ist formgleich mit dem Präteritum und darf die Hauptzahl nicht
    # aufblähen.
    sm = analysiere_sitzung(_sitzung("Ich sollte das machen."))[KLIENT]
    assert sm.zaehler.get("konjunktiv2", 0) == 0
    assert sm.zaehler.get("konjunktiv2_ambig", 0) == 1


def test_indikativ_ist_kein_konjunktiv():
    assert zaehle("konjunktiv2", "Ich habe das gemacht und es war gut.") == 0


# ---------------------------------------------------------------------------
# Bedauern
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("satz", [
    "Hätte ich nur früher etwas gesagt.",
    "Wenn ich doch damals gegangen wäre.",
    "Ich hätte das nicht sagen sollen.",
    "Im Nachhinein war das ein Fehler.",
    "Ich bereue das bis heute.",
])
def test_bedauern_trifft(satz):
    assert zaehle("bedauern", satz) >= 1


def test_bedauern_kein_fehlalarm():
    assert zaehle("bedauern", "Ich habe gestern eingekauft und gekocht.") == 0


# ---------------------------------------------------------------------------
# Absolutismen
# ---------------------------------------------------------------------------

def test_absolutismen_stufe_eins():
    assert zaehle("absolut1", "Das ist immer so und ändert sich nie.") == 2


def test_umgangssprachliche_verstaerker_sind_ausgeschlossen():
    # Der wichtigste Einzeltest dieser Datei: die englische Vorlage würde
    # "totally/completely" mitzählen, im gesprochenen Deutsch ist das
    # Umgangssprache und kein absolutistisches Denken.
    sm = analysiere_sitzung(_sitzung("Das war total nett und voll gut, echt ganz okay."))[KLIENT]
    assert sm.zaehler.get("absolut1", 0) == 0
    assert sm.zaehler.get("absolut2", 0) == 0
    assert sm.zaehler.get("intensivierer", 0) >= 4


def test_zwang_ist_kein_absolutismus():
    sm = analysiere_sitzung(_sitzung("Ich muss das machen, ich soll funktionieren."))[KLIENT]
    assert sm.zaehler.get("zwang", 0) == 2
    assert sm.zaehler.get("absolut1", 0) == 0


# ---------------------------------------------------------------------------
# Modalpartikeln
# ---------------------------------------------------------------------------

def test_resignative_partikel():
    assert zaehle("partikel_resignativ", "Das ist halt so, das ist eben so.") == 2


def test_ja_am_satzanfang_ist_keine_modalpartikel():
    # "Ja." als Antwort darf nicht als insistierende Partikel zählen.
    assert zaehle("partikel_insistierend", "Ja. Genau.") == 0
    assert zaehle("partikel_insistierend", "Das ist ja furchtbar.") == 1


# ---------------------------------------------------------------------------
# Affekt und Granularität
# ---------------------------------------------------------------------------

def test_granularitaet_unterscheidet_benannt_und_vage():
    vage = werte("Es war irgendwie schlecht und komisch.")
    benannt = werte("Ich war gekränkt und wehmütig.")
    assert benannt["granularitaet"] > vage["granularitaet"]


def test_distinkte_lemmata_zaehlen_verschiedenheit_nicht_menge():
    einmal = analysiere_sitzung(_sitzung("Ich hatte Angst, Trauer und Scham."))[KLIENT]
    oft = analysiere_sitzung(_sitzung("Angst, Angst, Angst, Angst."))[KLIENT]
    assert len(einmal.emo_lemmata) > len(oft.emo_lemmata)


def test_verneinter_affekt_wird_getrennt_gefuehrt():
    sm = analysiere_sitzung(_sitzung("Ich bin nicht traurig."))[KLIENT]
    assert sm.emo_verneint.get("trauer", 0) == 1
    assert sm.emo_familien.get("trauer", 0) == 0


def test_koerperaffekt_eigene_spur():
    sm = analysiere_sitzung(_sitzung("Ich hatte einen Kloß im Hals und Druck im Magen."))[KLIENT]
    assert sm.zaehler.get("emo_koerper", 0) >= 3


# ---------------------------------------------------------------------------
# Hecken, Kausalität, Einsicht
# ---------------------------------------------------------------------------

def test_hecken():
    assert zaehle("hecken", "Irgendwie war das eigentlich, keine Ahnung, schwierig.") >= 3


def test_kausal_und_einsicht():
    sm = analysiere_sitzung(_sitzung(
        "Weil ich das gemerkt habe, ist mir der Zusammenhang klar geworden."))[KLIENT]
    assert sm.zaehler.get("kausal", 0) >= 2
    assert sm.zaehler.get("einsicht", 0) >= 2


# ---------------------------------------------------------------------------
# Passiv und Tempus
# ---------------------------------------------------------------------------

def test_passiv_werden_plus_partizip():
    assert zaehle("passiv", "Mir wurde gesagt, ich soll mich nicht anstellen.") == 1


def test_futur_ist_kein_passiv():
    sm = analysiere_sitzung(_sitzung("Ich werde morgen anrufen."))[KLIENT]
    assert sm.zaehler.get("passiv", 0) == 0
    assert sm.zaehler.get("tempus_futur", 0) == 1


def test_perfekt_wird_als_vergangenheit_erkannt():
    assert zaehle("tempus_perfekt", "Ich habe das gemacht.") == 1


# ---------------------------------------------------------------------------
# Metaphern
# ---------------------------------------------------------------------------

def test_metapher_braucht_mentalen_bezug():
    # Ohne Affekt- oder Selbstbezug im Satz zählt Wettervokabular nicht.
    ohne = analysiere_sitzung(_sitzung("Am Dienstag war Gewitter und Regen."))[KLIENT]
    assert sum(ohne.metapher_domaenen.values()) == 0
    mit = analysiere_sitzung(_sitzung("Ich fühle mich wie unter einer grauen Wolke."))[KLIENT]
    assert mit.metapher_domaenen.get("wetter", 0) >= 1


# ---------------------------------------------------------------------------
# Raten sind wortzahlnormiert
# ---------------------------------------------------------------------------

def test_raten_sind_pro_tausend_woerter():
    kurz = werte("Man macht das.")
    lang = werte("Man macht das. " + "Das ist ein neutraler Satz ohne Marker. " * 20)
    assert kurz["man_rate"] > lang["man_rate"]
    assert kurz["man_quote"] == lang["man_quote"] == 1.0
