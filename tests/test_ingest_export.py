"""Transkripte, wie Dokumentations-Assistenten sie herausgeben."""

from __future__ import annotations

from therapy.ingest import KLIENT, THERAPEUT, erkenne_format, lies


def lies_eine(*args, **kwargs):
    sitzungen = lies(*args, **kwargs)
    assert len(sitzungen) == 1, f"unerwartet {len(sitzungen)} Sitzungen"
    return sitzungen[0]


# --- Sprecher auf eigener Zeile -------------------------------------------

BLOCK = """\
Therapeut
Wie war die Woche?

Patientin
Schwierig. Ich habe viel nachgedacht.
Vor allem nachts.

Therapeut
Mhm.

Patientin
Aber es geht schon.
"""


def test_sprecher_auf_eigener_zeile_wird_erkannt():
    s = lies_eine("via.txt", BLOCK)
    assert [t.sprecher for t in s.turns] == [THERAPEUT, KLIENT, THERAPEUT, KLIENT]
    assert s.befund.sprecher_quelle == "labels"
    # Der Name selbst darf nicht im gesprochenen.
    assert s.turns[0].text == "Wie war die Woche?"
    assert "nachts" in s.turns[1].text


def test_sprecher_auf_eigener_zeile_auch_ohne_leerzeile():
    eng = ("Therapeut\nWie war die Woche?\n"
           "Patientin\nSchwierig.\n"
           "Therapeut\nMhm.\n")
    s = lies_eine("eng.txt", eng)
    assert [t.sprecher for t in s.turns] == [THERAPEUT, KLIENT, THERAPEUT]


def test_sprecher_zeile_mit_doppelpunkt_und_zeitstempel():
    text = ("[00:00:12] Therapeut:\nWie war die Woche?\n\n"
            "[00:00:20] Patientin:\nSchwierig.\n")
    s = lies_eine("zeit.txt", text)
    assert [t.sprecher for t in s.turns] == [THERAPEUT, KLIENT]
    assert s.turns[0].start_sek == 12
    assert s.befund.zeitstempel


def test_anonyme_sprecher_auf_eigener_zeile_werden_geraten_und_gemeldet():
    # Wer diarisiert.
    text = ("Sprecher 1\nMhm.\n\n"
            "Sprecher 2\nEs war eine wirklich schwierige Woche für mich "
            "und ich habe sehr viel darüber nachgedacht.\n")
    s = lies_eine("diar.txt", text)
    assert s.befund.sprecher_quelle == "geraten"
    assert any("guessed" in w for w in s.befund.warnungen)
    # Wer weniger redet, gilt als Therapeut
    assert s.turns[0].sprecher == THERAPEUT
    assert s.turns[1].sprecher == KLIENT


# --- Der unstrukturierte Weg muss heil bleiben.

def test_fliesstext_bekommt_keine_erfundenen_sprecher():
    """Der eigentliche Prüfstein der neuen Regel."""
    text = ("Ich weiss nicht.\n"
            "Ja.\n"
            "Vielleicht.\n"
            "Es war schwierig, und ich habe lange darüber nachgedacht.\n"
            "Montag.\n"
            "Angst.\n")
    s = lies_eine("notiz.txt", text)
    assert s.befund.labels_gefunden == []
    assert s.befund.sprecher_quelle == "keine"
    assert "talk ratio" in s.befund.nicht_verfuegbar


def test_einzelbuchstabe_auf_eigener_zeile_ist_kein_sprecher():
    # "T" und "K" sind gültige Kürzel
    s = lies_eine("liste.txt", "T\nK\nP\nEs ging um die Woche davor.\n")
    assert s.befund.labels_gefunden == []


def test_doppelpunkt_form_funktioniert_unveraendert():
    text = "Therapeut: Wie war die Woche?\n\nKlientin: Schwierig.\n"
    s = lies_eine("klassisch.txt", text)
    assert [t.sprecher for t in s.turns] == [THERAPEUT, KLIENT]
    assert s.turns[0].text == "Wie war die Woche?"


# --- HTML -----------------------------------------------------------------

HTML = """<!DOCTYPE html>
<html><head><title>Transkript</title>
<style>p { color: #333 }</style></head>
<body>
<h1>Sitzung 4 &ndash; 14.03.2024</h1>
<p><strong>Therapeut:</strong> Wie war die Woche?</p>
<p><strong>Patientin:</strong> Schwierig &amp; anstrengend.</p>
<p><strong>Therapeut:</strong> Mhm.</p>
</body></html>
"""

HTML_BLOCK = """<div class="transkript">
<p><b>Therapeut</b><br>Wie war die Woche?</p>
<p><b>Patientin</b><br>Schwierig.</p>
</div>
"""


def test_html_wird_als_html_erkannt():
    assert erkenne_format("export.html", HTML) == "html"
    assert erkenne_format("export.htm", "<p>x</p>") == "html"
    # Ohne Endung genügt das Wurzel-Tag.
    assert erkenne_format("export", HTML) == "html"


def test_ein_p_im_text_macht_aus_einer_textdatei_kein_html():
    text = "Therapeut: Er sagte wörtlich <p> und lachte.\n\nKlientin: Ja.\n"
    assert erkenne_format("notiz.txt", text) == "txt"


def test_html_export_wird_gelesen():
    s = lies_eine("export.html", HTML)
    assert s.befund.format == "html"
    assert [t.sprecher for t in s.turns] == [THERAPEUT, KLIENT, THERAPEUT]
    # Tags stehen nicht im gesprochenen Text, Entitäten.
    assert s.turns[0].text == "Wie war die Woche?"
    assert s.turns[1].text == "Schwierig & anstrengend."
    assert not any("<" in t.text for t in s.turns)
    # Und das Stylesheet ist kein Redebeitrag geworden.
    assert not any("color" in t.text for t in s.turns)


def test_html_mit_sprecher_im_eigenen_absatz():
    s = lies_eine("block.html", HTML_BLOCK)
    assert [t.sprecher for t in s.turns] == [THERAPEUT, KLIENT]
    assert s.turns[0].text == "Wie war die Woche?"


def test_amp_wird_zuletzt_aufgeloest():
    # "&amp;lt;" ist ein geschriebenes "&lt;", kein Tag.
    s = lies_eine("esc.html", "<body><p>Therapeut: Er schrieb &amp;lt; an die Tafel.</p></body>")
    assert s.turns[0].text == "Er schrieb &lt; an die Tafel."


# --- Der Sprechertausch ---------------------------------------------------

def _abschnitt(nr: str, datum: str) -> str:
    # Mindestens MIN_TURNS_JE_ABSCHNITT Turns.
    return (
        f"--- Sitzung {nr} - {datum} ---\n"
        "Sprecher 1\nMhm.\n\n"
        "Sprecher 2\nEs war eine schwierige Woche und ich habe viel "
        "nachgedacht.\n\n"
        "Sprecher 1\nJa.\n\n"
        "Sprecher 2\nVor allem nachts ging mir das alles durch den Kopf.\n\n"
        "Sprecher 1\nMhm.\n\n"
        "Sprecher 2\nAber es geht schon wieder etwas besser als letzte Woche.\n\n"
    )


JAHR = _abschnitt("1", "2024-01-08") + _abschnitt("2", "2024-01-15")


def test_tausch_erreicht_alle_abschnitte_einer_datei():
    from therapy.report import Korpus
    korpus = Korpus()
    korpus.lade([{"name": "jahr.txt", "inhalt": JAHR}])
    assert len(korpus.sitzungen) == 2

    vorher = [[t.sprecher for t in s.turns] for s in korpus.sitzungen]
    # Die Befundzeile kennt nur den Dateinamen.
    korpus.sprecher_tauschen("jahr.txt")
    nachher = [[t.sprecher for t in s.turns] for s in korpus.sitzungen]

    tausch = {THERAPEUT: KLIENT, KLIENT: THERAPEUT}
    assert nachher == [[tausch.get(x, x) for x in zeile] for zeile in vorher]
    assert all(s.befund.sprecher_quelle == "manuell" for s in korpus.sitzungen)


def test_tausch_notiert_sich_genau_einmal():
    # Abschnitte teilen sich einen Befund.
    from therapy.report import Korpus
    korpus = Korpus()
    korpus.lade([{"name": "jahr.txt", "inhalt": JAHR}])
    korpus.sprecher_tauschen("jahr.txt")
    notizen = [w for w in korpus.sitzungen[0].befund.warnungen
               if "swapped by hand" in w]
    assert len(notizen) == 1


def test_sprache_setzen_erreicht_ebenfalls_alle_abschnitte():
    from therapy.report import Korpus
    korpus = Korpus()
    korpus.lade([{"name": "jahr.txt", "inhalt": JAHR}])
    korpus.sprache_setzen("jahr.txt", "en")
    assert all(s.sprache == "en" for s in korpus.sitzungen)
    assert korpus.sitzungen[0].befund.sprache_quelle == "manuell"


def test_befundzeile_steht_einmal_je_datei_nicht_je_abschnitt():
    """Was ``lade`` zurueckgibt und was ``befunde`` zurueckgibt."""
    import json

    import therapy

    therapy.leeren()
    zuerst = json.loads(therapy.lade(json.dumps(
        [{"name": "jahr.txt", "inhalt": JAHR}])))
    danach = json.loads(therapy.befunde())
    assert len(zuerst) == 1
    assert len(danach) == len(zuerst)

    # Und nach einem Tausch steht die Notiz.
    therapy.sprecher_tauschen("jahr.txt")
    nach_tausch = json.loads(therapy.befunde())
    assert len(nach_tausch) == 1
    notizen = [w for w in nach_tausch[0]["warnungen"] if "swapped by hand" in w]
    assert len(notizen) == 1
    therapy.leeren()
