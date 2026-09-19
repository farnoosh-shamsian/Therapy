"""Handgeprüfte englische Sätze, ein Block pro Marker.

Das Gegenstück zu ``test_marker.py`` und mit demselben Anspruch: diese Datei
ist die eigentliche Dokumentation der englischen Marker. Jeder Satz hier wurde
von Hand daraufhin angesehen, ob der Marker treffen *soll* — und mindestens
ein Gegenbeispiel pro Marker steht dabei, weil eine Liste, die nur Treffer
enthält, nichts beweist.

Wo die englische Fassung schwächer ist als die deutsche, steht das als Test
und nicht als Fussnote: die Gegenbeispiele beim generischen "you" und beim
be-Passiv sind hier die wichtigsten Zeilen der Datei, weil genau dort die
beiden Zahlen kippen würden.
"""

from __future__ import annotations

import pytest

from therapy.ingest import KLIENT, Sitzung, Turn
from therapy.markers import analysiere_sitzung, kennzahlen


def _sitzung(*saetze: str) -> Sitzung:
    turns = [Turn(idx=i, sprecher=KLIENT, text=text) for i, text in enumerate(saetze)]
    return Sitzung(sid="t", dateiname="t.txt", turns=turns, nummer=1, sprache="en")


def zaehle(marker: str, *saetze: str) -> int:
    sm = analysiere_sitzung(_sitzung(*saetze))[KLIENT]
    return sm.zaehler.get(marker, 0)


def werte(*saetze: str) -> dict:
    return kennzahlen(analysiere_sitzung(_sitzung(*saetze))[KLIENT])


# ---------------------------------------------------------------------------
# Generisches "you" gegen "I"
# ---------------------------------------------------------------------------
#
# Der schwierigste Marker des englischen Pakets. Deutsch hat mit "man" ein
# eigenes Pronomen; Englisch benutzt dasselbe "you", mit dem der Therapeut
# angesprochen wird. Die drei Gegenbeispiele unten sind der Filter.

def test_generisches_you_wird_gezaehlt():
    assert zaehle("generisch", "You just feel awful and there is nothing you can do.") == 2


def test_you_in_einer_frage_ist_anrede():
    # Ein "you" in einer Frage ist fast immer das Gegenüber.
    assert zaehle("generisch", "Do you think that is what happened?") == 0


def test_you_know_ist_diskursmarker_keine_referenz():
    # "You know" ist eine Hecke und steht dort, nicht hier.
    assert zaehle("generisch", "You know, I told her about it.") == 0
    assert zaehle("hecken", "You know, I told her about it.") == 1


def test_they_ist_bewusst_ausgeschlossen():
    # "They" ist in einem Transkript fast immer konkrete Referenz auf Menschen
    # in der Erzählung — die zählt das Soziogramm, nicht dieser Marker.
    assert zaehle("generisch", "They never listened to me at all.") == 0


def test_one_und_people_zaehlen():
    assert zaehle("generisch", "People just carry on and one never says anything.") == 2


def test_generisch_quote_gegen_ich():
    w = werte("You just carry on.", "I carry on.")
    assert w["generisch_quote"] == pytest.approx(0.5)


def test_ich_kasus_unterscheidet_subjekt_und_erlebenden():
    assert werte("I told him that.")["ich_nominativ_anteil"] == 1.0
    assert werte("It just happened to me.")["ich_nominativ_anteil"] == 0.0


# ---------------------------------------------------------------------------
# Irrealis
# ---------------------------------------------------------------------------

def test_irrealis_eindeutige_periphrastische_formen():
    assert zaehle("irrealis", "I should have said something.") >= 1
    assert zaehle("irrealis", "If I were braver I would have stayed.") >= 2


def test_irrealis_ambige_formen_getrennt():
    # Blosses "could" ist Fähigkeit in der Vergangenheit, nicht Irrealis, und
    # darf die Hauptzahl nicht aufblähen. Derselbe Schnitt wie bei "sollte"
    # auf der deutschen Seite.
    sm = analysiere_sitzung(_sitzung("I could swim back then."))[KLIENT]
    assert sm.zaehler.get("irrealis", 0) == 0
    assert sm.zaehler.get("irrealis_ambig", 0) == 1


def test_indikativ_ist_kein_irrealis():
    assert zaehle("irrealis", "I did that and it was fine.") == 0


# ---------------------------------------------------------------------------
# Bedauern
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("satz", [
    "If only I had left earlier.",
    "I should have said something that day.",
    "I wish I had told her the truth.",
    "Looking back, that was a mistake.",
    "I regret it to this day.",
    "Why didn't I say anything?",
])
def test_bedauern_trifft(satz):
    assert zaehle("bedauern", satz) >= 1


def test_bedauern_kein_fehlalarm():
    assert zaehle("bedauern", "I went shopping yesterday and cooked dinner.") == 0


# ---------------------------------------------------------------------------
# Absolutismen
# ---------------------------------------------------------------------------

def test_absolutismen_stufe_eins():
    assert zaehle("absolut1", "It is always like this and it never changes.") == 2


def test_umgangssprachliche_verstaerker_sind_ausgeschlossen():
    # Der wichtigste Einzeltest dieser Datei, und der einzige Punkt, an dem
    # das Werkzeug seiner eigenen Vorlage widerspricht: Al-Mosaiwi &
    # Johnstone zählen "totally"/"completely"/"absolutely" als absolutistisch.
    # Das Instrument wurde an geschriebenen Forenbeiträgen validiert; in
    # gesprochener Therapiesprache sind das Intensivierer.
    satz = "I was totally fine, completely normal, absolutely literally fine."
    sm = analysiere_sitzung(_sitzung(satz))[KLIENT]
    assert sm.zaehler.get("absolut1", 0) == 0
    assert sm.zaehler.get("absolut2", 0) == 0
    assert sm.zaehler.get("intensivierer", 0) >= 4


def test_zwang_ist_kein_absolutismus():
    satz = "I have to do it, I am supposed to function, I gotta keep going."
    sm = analysiere_sitzung(_sitzung(satz))[KLIENT]
    assert sm.zaehler.get("zwang", 0) == 3
    assert sm.zaehler.get("absolut1", 0) == 0


# ---------------------------------------------------------------------------
# Abtönung
# ---------------------------------------------------------------------------

def test_resignative_abtoenung():
    assert zaehle("partikel_resignativ", "Anyway, it is what it is.") == 2


def test_minimierende_abtoenung():
    assert zaehle("partikel_minimierend", "It was just a bit much.") == 2


def test_right_am_satzanfang_ist_keine_abtoenung():
    # "Right." als Antwort ist Rückkanal, "…, right?" ist Abtönung.
    # Derselbe Positionsfilter wie beim deutschen "ja".
    assert zaehle("partikel_abtönend", "Right. Okay.") == 0
    assert zaehle("partikel_abtönend", "That is how it went, right?") == 1


# ---------------------------------------------------------------------------
# Affekt und Granularität
# ---------------------------------------------------------------------------

def test_granularitaet_unterscheidet_benannt_und_vage():
    vage = werte("It was kind of bad and weird.")
    benannt = werte("I felt slighted and wistful.")
    assert benannt["granularitaet"] > vage["granularitaet"]


def test_distinkte_lemmata_zaehlen_verschiedenheit_nicht_menge():
    einmal = analysiere_sitzung(_sitzung("I felt fear, grief and shame."))[KLIENT]
    oft = analysiere_sitzung(_sitzung("Fear, fear, fear, fear."))[KLIENT]
    assert len(einmal.emo_lemmata) > len(oft.emo_lemmata)


def test_verneinter_affekt_wird_getrennt_gefuehrt():
    # Das Negationsfenster ist hier eine Position breiter als im Deutschen:
    # englische Negation hängt am Hilfsverb und steht damit weiter vom
    # verneinten Wort entfernt.
    sm = analysiere_sitzung(_sitzung("I am not sad about it."))[KLIENT]
    assert sm.emo_verneint.get("trauer", 0) == 1
    assert sm.emo_familien.get("trauer", 0) == 0


def test_verneinter_affekt_ueber_hilfsverb():
    sm = analysiere_sitzung(_sitzung("I don't really feel angry."))[KLIENT]
    assert sm.emo_verneint.get("wut", 0) == 1


def test_koerperaffekt_eigene_spur():
    sm = analysiere_sitzung(
        _sitzung("There was a lump in my throat and pressure in my stomach."))[KLIENT]
    assert sm.zaehler.get("emo_koerper", 0) >= 3


# ---------------------------------------------------------------------------
# Hecken, Kausalität, Einsicht
# ---------------------------------------------------------------------------

def test_hecken():
    assert zaehle("hecken", "I kind of, I guess, I don't know, it was sort of hard.") >= 3


def test_like_ist_bewusst_keine_hecke():
    # "like" ist als Diskursmarker eine Hecke, als Verb und als Präposition
    # keine, und die Lesarten sind etwa gleich häufig. Lieber der verpasste
    # Treffer als die verdorbene Zahl.
    assert zaehle("hecken", "I like my sister, she is like my mother.") == 0


def test_kausal_und_einsicht():
    # Das Gegenstück zum deutschen Test mit „weil“ + „Zusammenhang“.
    sm = analysiere_sitzung(_sitzung(
        "Because I noticed that, the connection makes sense to me now."))[KLIENT]
    assert sm.zaehler.get("kausal", 0) >= 2
    assert sm.zaehler.get("einsicht", 0) >= 2


def test_blosses_why_ist_nicht_kausal():
    # „why“ allein ist überwiegend Frage und nicht Begründung; gezählt werden
    # nur die Konstruktionen („that's why“, „which is why“). Dieselbe
    # Zurückhaltung wie bei „like“ in den Hecken.
    assert zaehle("kausal", "Why did you ask me that?") == 0
    assert zaehle("kausal", "That's why I stopped calling her.") == 1


# ---------------------------------------------------------------------------
# Passiv und Tempus
# ---------------------------------------------------------------------------

def test_passiv_be_plus_partizip():
    assert zaehle("passiv", "I was told to pull myself together.") == 1


def test_praedikatives_adjektiv_ist_kein_passiv():
    # Der wichtigste Ausschluss des englischen Pakets: ohne ihn misst der
    # Marker Befinden statt Agens — und Befinden wird nebenan schon gemessen.
    assert zaehle("passiv", "I was tired and worried the whole week.") == 0


def test_get_passiv_wird_mitgezaehlt():
    # Im gesprochenen Englisch häufiger als das be-Passiv, und im Deutschen
    # ohne direktes Gegenstück.
    assert zaehle("passiv", "I got left behind again.") == 1


def test_futur_ist_kein_passiv():
    sm = analysiere_sitzung(_sitzung("I will call her tomorrow."))[KLIENT]
    assert sm.zaehler.get("passiv", 0) == 0
    assert sm.zaehler.get("tempus_futur", 0) == 1


def test_perfekt_und_praeteritum_werden_getrennt():
    # Englisch teilt die Vergangenheit zweifach, wo das gesprochene Deutsch
    # fast nur das Perfekt benutzt. Deshalb sind die beiden Anteile zwischen
    # den Sprachen nicht vergleichbar, nur ihre Summe.
    assert zaehle("tempus_perfekt", "I have done that already.") == 1
    assert zaehle("tempus_praeteritum", "I called her yesterday.") == 1


# ---------------------------------------------------------------------------
# Negationsmorphologie
# ---------------------------------------------------------------------------

def test_negationsmorphologie():
    assert zaehle("negation_morph", "I felt worthless and unable to move.") == 2


def test_negationsmorphologie_kein_fehlalarm():
    # "un-", "in-", "mis-" sind im Englischen kurz und stehen zufällig am
    # Anfang vieler gewöhnlicher Wörter. Ohne die Ausnahmeliste wäre jedes
    # zweite Wort hier eine Verneinung.
    satz = "I did not understand the interest into that minute."
    assert zaehle("negation_morph", satz) == 0


def test_kontraktionen_zaehlen_als_negation():
    # "don't" ist in gesprochenem Englisch die Normalform und "do not" die
    # Ausnahme. Eine Liste, die nur "not" kennt, zählt an der Sprache vorbei.
    assert zaehle("negation", "I don't know and I can't say.") == 2


# ---------------------------------------------------------------------------
# Metaphern
# ---------------------------------------------------------------------------

def test_metapher_braucht_mentalen_bezug():
    ohne = analysiere_sitzung(_sitzung("On Tuesday there was thunder and rain."))[KLIENT]
    assert sum(ohne.metapher_domaenen.values()) == 0
    mit = analysiere_sitzung(_sitzung("I feel like I am under a grey cloud."))[KLIENT]
    assert mit.metapher_domaenen.get("wetter", 0) >= 1


# ---------------------------------------------------------------------------
# Keine Kompositazerlegung
# ---------------------------------------------------------------------------

def test_keine_komposita_im_englischen():
    # Englische Komposita sind offen geschrieben ("fear of loss") und damit
    # bereits zerlegt. Der Schritt entfällt, statt leer zu laufen.
    sm = analysiere_sitzung(_sitzung("The fear of loss was overwhelming."))[KLIENT]
    assert not sm.komposita
    assert sm.zaehler.get("kompositum", 0) == 0


# ---------------------------------------------------------------------------
# Raten sind wortzahlnormiert
# ---------------------------------------------------------------------------

def test_raten_sind_pro_tausend_woerter():
    kurz = werte("You carry on.")
    lang = werte("You carry on. " + "This is a neutral sentence with no markers. " * 20)
    assert kurz["generisch_rate"] > lang["generisch_rate"]
    assert kurz["generisch_quote"] == lang["generisch_quote"] == 1.0
