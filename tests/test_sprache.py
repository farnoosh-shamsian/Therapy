"""Spracherkennung, Sprachwahl und das gemischte Korpus.

Der Befund ist hier wieder wichtiger als die Erkennung. Eine Erkennung, die
danebenliegt und es meldet, ist brauchbar; eine, die danebenliegt und
schweigt, zählt ein englisches Transkript mit deutschen Wortlisten aus und
liefert eine Kurve, die aussieht wie ein Befund und keiner ist. Die Tests
unten prüfen deshalb fast durchgehend, ob die *Warnung* kommt.
"""

from __future__ import annotations

from therapy import sprachen
from therapy.ingest import KLIENT, lies
from therapy.report import Korpus

DE = """\
Therapeut: Wie war die Woche?

Klientin: Es war schwierig. Ich habe die ganze Zeit nachgedacht und mich
eigentlich durchgehend schlecht gefühlt, weil das halt immer so ist und sich
nie etwas ändert. Man macht dann einfach weiter.

Therapeut: Mhm.

Klientin: Aber es geht schon irgendwie.
"""

EN = """\
Therapist: How was the week?

Client: It was hard. I kept thinking about it the whole time and I just felt
awful about all of it, because that is how it always goes and nothing ever
changes. You just carry on.

Therapist: Mhm.

Client: But I suppose I am getting through it somehow.
"""


# ---------------------------------------------------------------------------
# Erkennung
# ---------------------------------------------------------------------------

def test_erkennt_deutsch_und_englisch():
    code_de, sicher_de, _ = sprachen.erkenne(DE)
    code_en, sicher_en, _ = sprachen.erkenne(EN)
    assert code_de == "de" and sicher_de > 0.5
    assert code_en == "en" and sicher_en > 0.5


def test_zu_wenig_text_wird_nicht_geraten():
    # Unterhalb der Wortgrenze wird die Standardsprache genommen und das
    # gesagt — nicht geraten und geschwiegen.
    code, sicherheit, details = sprachen.erkenne("Mhm. Ja.")
    assert code == sprachen.STANDARD
    assert sicherheit == 0.0
    assert details["woerter"] < sprachen.MIN_WOERTER


def test_zu_wenig_text_erzeugt_eine_warnung_im_befund():
    sitzung = lies("kurz.txt", "T: Mhm.\n\nK: Ja.\n")
    assert sitzung.befund.sprache_quelle == "standard"
    assert any("language" in w.lower() for w in sitzung.befund.warnungen)


def test_dateiname_schlaegt_die_erkennung():
    sitzung = lies("client-jane_session-03_de.txt", EN)
    assert sitzung.sprache == "de"
    assert sitzung.befund.sprache_quelle == "dateiname"
    # …und der Widerspruch wird gemeldet, statt still übergangen zu werden.
    assert any("filename" in w.lower() for w in sitzung.befund.warnungen)


def test_vorgabe_schlaegt_den_dateinamen():
    sitzung = lies("client-jane_session-03_de.txt", EN, sprache="en")
    assert sitzung.sprache == "en"
    assert sitzung.befund.sprache_quelle == "manuell"


def test_erkannte_sprache_steht_im_befund():
    sitzung = lies("client-jane_session-01.txt", EN)
    befund = sitzung.befund.als_dict()
    assert befund["sprache"] == "en"
    assert befund["spracheName"] == "English"
    assert befund["spracheQuelle"] == "erkannt"


# ---------------------------------------------------------------------------
# Gemischte Sitzungen
# ---------------------------------------------------------------------------

def test_gemischte_sitzung_wird_gemeldet():
    # Eine Sitzung, die zur Hälfte in der anderen Sprache läuft, wird als
    # eine Sprache ausgewertet — mit einer Warnung, die sagt, was das kostet.
    sitzung = lies("gemischt.txt", EN + "\n" + DE)
    assert sitzung.befund.anteil_fremdsprache > 0
    assert any("other language" in w for w in sitzung.befund.warnungen)


def test_einzelnes_fremdsprachiges_zitat_ist_keine_mischung():
    text = EN + "\n\nClient: She kept saying “das ist halt so” and nothing else.\n"
    sitzung = lies("zitat.txt", text)
    assert sitzung.sprache == "en"
    assert sitzung.befund.anteil_fremdsprache < sprachen.GEMISCHT_AB


# ---------------------------------------------------------------------------
# Englische Sprecherlabels
# ---------------------------------------------------------------------------

def test_englische_sprecherlabels():
    sitzung = lies("client-jane_session-01.txt", EN)
    assert sitzung.befund.sprecher_quelle == "labels"
    assert sitzung.hat_sprecher
    assert any(t.sprecher == KLIENT for t in sitzung.turns)


def test_englische_rueckkanaele_zaehlen_nicht_als_beitrag():
    from therapy.dialogue import ist_rueckkanal
    from therapy.ingest import Turn

    for text in ("Mhm.", "Right.", "Yeah.", "Uh huh", "I see.", "Got it."):
        assert ist_rueckkanal(Turn(0, "T", text), "en"), text
    assert not ist_rueckkanal(Turn(0, "T", "Right, and what happened then?"), "en")


# ---------------------------------------------------------------------------
# Das gemischte Korpus im Bericht
# ---------------------------------------------------------------------------

def _korpus_mit_beiden_sprachen() -> Korpus:
    korpus = Korpus()
    korpus.lade([
        {"name": "klient-anna_sitzung-01_2024-01-11.txt", "inhalt": DE},
        {"name": "klient-anna_sitzung-02_2024-01-18.txt", "inhalt": DE},
        {"name": "client-jane_session-01_2024-01-12.txt", "inhalt": EN},
        {"name": "client-jane_session-02_2024-01-19.txt", "inhalt": EN},
    ])
    return korpus


def test_bericht_traegt_beide_sprachen():
    bericht = _korpus_mit_beiden_sprachen().bericht()
    assert bericht["sprachen"]["gemischt"] is True
    assert set(bericht["sprachen"]["codes"]) == {"de", "en"}


def test_beschriftung_ist_nach_sprache_geschachtelt():
    bericht = _korpus_mit_beiden_sprachen().bericht()
    marker = bericht["beschriftung"]["marker"]
    # Jede Sprache bringt ihren eigenen Distanzierungsmarker mit, und der der
    # anderen taucht bei ihr gar nicht auf.
    assert "man_quote" in marker["de"] and "man_quote" not in marker["en"]
    assert "generisch_quote" in marker["en"] and "generisch_quote" not in marker["de"]


def test_kacheln_kommen_aus_dem_bericht_nicht_aus_der_oberflaeche():
    bericht = _korpus_mit_beiden_sprachen().bericht()
    kacheln = bericht["beschriftung"]["kacheln"]
    assert kacheln["de"][0][0] == "man_quote"
    assert kacheln["en"][0][0] == "generisch_quote"


def test_jede_sitzung_traegt_ihre_sprache():
    bericht = _korpus_mit_beiden_sprachen().bericht()
    je_klient = {k["id"]: k for k in bericht["klienten"]}
    assert je_klient["anna"]["sprache"] == "de"
    assert je_klient["jane"]["sprache"] == "en"
    assert all(s["sprache"] == "de" for s in je_klient["anna"]["sitzungen"])
    assert all(s["sprache"] == "en" for s in je_klient["jane"]["sitzungen"])


def test_keyness_vergleicht_nicht_ueber_die_sprachgrenze():
    # Gegen eine anderssprachige Referenz misst Keyness den Sprachunterschied
    # und sonst nichts. Dann lieber eine leere Liste mit Begründung.
    bericht = _korpus_mit_beiden_sprachen().bericht()
    for klient in bericht["klienten"]:
        assert klient["keyness"] == []
        assert klient["keynessHinweis"] is not None


def test_spiegel_markiert_zeilen_ueber_die_sprachgrenze():
    from therapy.mirror import Klientenprofil, vergleich

    def profil(klient_id, sprache, deutungen, spiegelungen):
        p = Klientenprofil(klient_id=klient_id, sitzungen=10, sprachen=[sprache])
        p.interventionen.update({"deutung": deutungen, "spiegelung": spiegelungen})
        return p

    # Zwei Klienten derselben Sprache: gewöhnlicher Vergleich, keine Markierung.
    gleich = vergleich([profil("anna", "de", 30, 10), profil("bernd", "de", 10, 30)])
    assert gleich and not any(z["sprachgrenze"] for z in gleich)

    # Zwei Klienten verschiedener Sprachen: dieselbe Zeile, aber markiert.
    ueber = vergleich([profil("anna", "de", 30, 10), profil("jane", "en", 10, 30)])
    assert ueber and all(z["sprachgrenze"] for z in ueber)


def test_spiegel_hinweis_zur_sprachgrenze_steht_im_bericht():
    bericht = _korpus_mit_beiden_sprachen().bericht()
    hinweis = bericht["hinweise"]["spiegelSprachgrenze"]
    assert "style matching" in hinweis.lower()


def test_einsprachiges_korpus_hat_keine_sprachwarnung():
    korpus = Korpus()
    korpus.lade([
        {"name": "klient-anna_sitzung-01_2024-01-11.txt", "inhalt": DE},
        {"name": "klient-bernd_sitzung-01_2024-02-06.txt", "inhalt": DE},
    ])
    bericht = korpus.bericht()
    assert bericht["sprachen"]["gemischt"] is False
    for klient in bericht["klienten"]:
        assert klient["spracheGemischt"] is False
        assert klient["spracheWarnung"] is None


# ---------------------------------------------------------------------------
# Klient mit Sprachwechsel mitten in der Fallgeschichte
# ---------------------------------------------------------------------------

def test_sprachwechsel_beim_selben_klienten_wird_gemeldet():
    korpus = Korpus()
    korpus.lade([
        {"name": "klient-anna_sitzung-01_2024-01-11.txt", "inhalt": DE},
        {"name": "klient-anna_sitzung-02_2024-01-18.txt", "inhalt": EN},
    ])
    klient = korpus.bericht()["klienten"][0]
    assert klient["spracheGemischt"] is True
    assert "not all in the same language" in klient["spracheWarnung"]


def test_sprachwechsel_laesst_nur_vollstaendige_reihen_uebrig():
    korpus = Korpus()
    korpus.lade([
        {"name": "klient-anna_sitzung-01_2024-01-11.txt", "inhalt": DE},
        {"name": "klient-anna_sitzung-02_2024-01-18.txt", "inhalt": EN},
    ])
    serien = korpus.bericht()["klienten"][0]["arc"]["serien"]
    # Sprachspezifische Reihen fallen heraus, statt mit Nullen aufgefüllt zu
    # werden — eine Null wäre eine Behauptung über eine Sitzung, in der gar
    # nicht gemessen wurde.
    assert "man_quote" not in serien
    assert "generisch_quote" not in serien
    # Die zusammengesetzte Reihe geht durch, und die geteilten auch.
    assert len(serien["vgl_distanzierung"]) == 2
    assert len(serien["hecken_rate"]) == 2


def test_sprache_von_hand_setzen():
    korpus = Korpus()
    korpus.lade([{"name": "client-jane_session-01.txt", "inhalt": EN}])
    sid = korpus.sitzungen[0].sid
    korpus.sprache_setzen(sid, "de")
    assert korpus.sitzungen[0].sprache == "de"
    assert korpus.sitzungen[0].befund.sprache_quelle == "manuell"
    # Und die Analyse läuft danach in der gesetzten Sprache neu.
    assert korpus.bericht()["klienten"][0]["sprache"] == "de"


# ---------------------------------------------------------------------------
# Namenserkennung je Sprache
# ---------------------------------------------------------------------------

def test_namen_werden_je_sprache_gesucht():
    from therapy.pseudonym import finde_namen

    # „Rat“ ist im Deutschen ein gewöhnliches Substantiv und im Englischen
    # kein Lexikonwort — ein gemeinsamer Durchgang würde den Sprachen ihre
    # jeweiligen Substantive als Namen unterschieben.
    deutsch = finde_namen(["Ich habe meine Schwester Anna gefragt."], sprache="de")
    assert any(k.name == "Anna" for k in deutsch)

    englisch = finde_namen(["I asked my sister Sarah about it."], sprache="en")
    assert any(k.name == "Sarah" for k in englisch)
    assert not any(k.name == "Sister" for k in englisch)
