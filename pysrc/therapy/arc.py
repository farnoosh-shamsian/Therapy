"""Der Bogen — alles über Sitzungen hinweg, plus Wechselpunkte.

Was der Therapeut am Ende wirklich will, sind nicht zwölf Liniendiagramme,
sondern einen Satz: *um Sitzung 9 herum hat sich etwas verschoben.* Danach
geht er selbst nachsehen, warum. Genau das rechnet dieses Modul.

Die Wechselpunkterkennung ist eine Bayes'sche Einzelwechselpunkt-Analyse mit
Normal-Inverse-Gamma-Prior, rekursiv angewandt (binäre Segmentierung). Sie
liefert nicht nur eine Position, sondern eine Posteriorverteilung darüber und
einen Bayes-Faktor gegen das Modell „kein Wechselpunkt“. Das ist wichtiger,
als es klingt: bei zwölf Datenpunkten *findet* jedes Verfahren einen
Wechselpunkt. Die Frage ist, ob er etwas bedeutet, und der Bayes-Faktor ist
die einzige Zahl hier, die darauf antwortet.

Reine Standardbibliothek, absichtlich. Kein numpy, kein scipy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import sprachen
from .ingest import KLIENT
from .markers import kennzahlen

# Prior. Schwach informativ, auf z-standardisierten Reihen.
_MU0, _KAPPA0, _ALPHA0, _BETA0 = 0.0, 1.0, 2.0, 1.0

MIN_SEGMENT = 3          # kürzere Segmente sind bei Sitzungsreihen Unsinn
BF_SCHWELLE = 3.0        # Bayes-Faktor, ab dem ein Wechselpunkt gemeldet wird
MIN_SITZUNGEN = 8        # darunter wird gar nicht erst gerechnet


@dataclass
class Wechselpunkt:
    position: int              # Index in der Reihe
    sitzung: int | None        # Sitzungsnummer
    bayes_faktor: float
    posterior: list[float] = field(default_factory=list)
    vorher: float = 0.0
    nachher: float = 0.0

    def als_dict(self) -> dict:
        return {
            "position": self.position,
            "sitzung": self.sitzung,
            "bayesFaktor": round(self.bayes_faktor, 2),
            "posterior": [round(p, 4) for p in self.posterior],
            "vorher": round(self.vorher, 3),
            "nachher": round(self.nachher, 3),
            "richtung": "hoch" if self.nachher > self.vorher else "runter",
        }


# ---------------------------------------------------------------------------
# Bayes'sche Wechselpunkte
# ---------------------------------------------------------------------------

def _log_marginal(werte: list[float]) -> float:
    """Log-Randlikelihood eines Segments unter Normal-Inverse-Gamma."""
    n = len(werte)
    if n == 0:
        return 0.0
    mittel = sum(werte) / n
    quadrate = sum((x - mittel) ** 2 for x in werte)
    kappa_n = _KAPPA0 + n
    alpha_n = _ALPHA0 + n / 2.0
    beta_n = (_BETA0 + 0.5 * quadrate
              + _KAPPA0 * n * (mittel - _MU0) ** 2 / (2.0 * kappa_n))
    return (math.lgamma(alpha_n) - math.lgamma(_ALPHA0)
            + _ALPHA0 * math.log(_BETA0) - alpha_n * math.log(beta_n)
            + 0.5 * (math.log(_KAPPA0) - math.log(kappa_n))
            - (n / 2.0) * math.log(math.pi * 2.0))


def _logsumexp(werte: list[float]) -> float:
    if not werte:
        return float("-inf")
    m = max(werte)
    if m == float("-inf"):
        return m
    return m + math.log(sum(math.exp(w - m) for w in werte))


def _standardisiere(werte: list[float]) -> list[float]:
    n = len(werte)
    if n < 2:
        return [0.0] * n
    mittel = sum(werte) / n
    varianz = sum((x - mittel) ** 2 for x in werte) / n
    sd = math.sqrt(varianz)
    if sd < 1e-9:
        return [0.0] * n
    return [(x - mittel) / sd for x in werte]


def einzelner_wechselpunkt(werte: list[float]) -> Wechselpunkt | None:
    """Bester Wechselpunkt einer Reihe mit Posterior und Bayes-Faktor."""
    n = len(werte)
    if n < 2 * MIN_SEGMENT:
        return None
    z = _standardisiere(werte)
    if all(abs(x) < 1e-9 for x in z):
        return None

    ohne = _log_marginal(z)
    positionen = list(range(MIN_SEGMENT, n - MIN_SEGMENT + 1))
    if not positionen:
        return None
    log_evidenz = [_log_marginal(z[:t]) + _log_marginal(z[t:]) for t in positionen]

    # Gleichverteilter Prior über die zulässigen Positionen.
    log_prior = -math.log(len(positionen))
    log_mit = _logsumexp([e + log_prior for e in log_evidenz])
    bf = math.exp(min(700.0, log_mit - ohne))

    norm = _logsumexp(log_evidenz)
    posterior_kurz = [math.exp(e - norm) for e in log_evidenz]
    beste = max(range(len(positionen)), key=lambda i: posterior_kurz[i])
    t = positionen[beste]

    posterior = [0.0] * n
    for i, pos in enumerate(positionen):
        posterior[pos] = posterior_kurz[i]

    return Wechselpunkt(
        position=t, sitzung=None, bayes_faktor=bf, posterior=posterior,
        vorher=sum(werte[:t]) / t,
        nachher=sum(werte[t:]) / (n - t),
    )


def wechselpunkte(werte: list[float], sitzungsnummern: list[int] | None = None,
                  max_punkte: int = 3) -> list[Wechselpunkt]:
    """Mehrere Wechselpunkte über binäre Segmentierung.

    Jedes Teilstück wird erneut geprüft; abgebrochen wird, sobald der
    Bayes-Faktor unter die Schwelle fällt. Kein Verfahren mit fester
    Punktzahl — wenn nichts da ist, kommt eine leere Liste zurück, und das
    ist ein gültiges Ergebnis.
    """
    if len(werte) < MIN_SITZUNGEN:
        return []
    gefunden: list[Wechselpunkt] = []
    segmente = [(0, len(werte))]
    while segmente and len(gefunden) < max_punkte:
        a, b = segmente.pop(0)
        wp = einzelner_wechselpunkt(werte[a:b])
        if wp is None or wp.bayes_faktor < BF_SCHWELLE:
            continue
        absolut = a + wp.position
        voll_posterior = [0.0] * len(werte)
        for i, p in enumerate(wp.posterior):
            voll_posterior[a + i] = p
        wp.position = absolut
        wp.posterior = voll_posterior
        if sitzungsnummern and 0 <= absolut < len(sitzungsnummern):
            wp.sitzung = sitzungsnummern[absolut]
        gefunden.append(wp)
        if absolut - a >= 2 * MIN_SEGMENT:
            segmente.append((a, absolut))
        if b - absolut >= 2 * MIN_SEGMENT:
            segmente.append((absolut, b))
    gefunden.sort(key=lambda w: -w.bayes_faktor)
    return gefunden


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

def rangkorrelation(werte: list[float]) -> float:
    """Spearman-Korrelation gegen die Sitzungsreihenfolge.

    Rangbasiert, weil ein einzelner Ausreisser bei zwölf Sitzungen eine
    Regressionsgerade sonst komplett dreht.
    """
    n = len(werte)
    if n < 4:
        return 0.0
    raenge = _raenge(werte)
    zeit = list(range(1, n + 1))
    mz = sum(zeit) / n
    mr = sum(raenge) / n
    zaehler = sum((zeit[i] - mz) * (raenge[i] - mr) for i in range(n))
    nenner = math.sqrt(sum((z - mz) ** 2 for z in zeit)
                       * sum((r - mr) ** 2 for r in raenge))
    return zaehler / nenner if nenner else 0.0


def _raenge(werte: list[float]) -> list[float]:
    geordnet = sorted(range(len(werte)), key=lambda i: werte[i])
    raenge = [0.0] * len(werte)
    i = 0
    while i < len(geordnet):
        j = i
        while j + 1 < len(geordnet) and werte[geordnet[j + 1]] == werte[geordnet[i]]:
            j += 1
        mittlerer_rang = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            raenge[geordnet[k]] = mittlerer_rang
        i = j + 1
    return raenge


def glaetten(werte: list[float], fenster: int = 3) -> list[float]:
    """Gleitender Mittelwert. Nur für die Darstellung, nie für die Rechnung."""
    if fenster <= 1 or len(werte) < fenster:
        return list(werte)
    rand = fenster // 2
    geglaettet = []
    for i in range(len(werte)):
        a, b = max(0, i - rand), min(len(werte), i + rand + 1)
        geglaettet.append(sum(werte[a:b]) / (b - a))
    return geglaettet


# ---------------------------------------------------------------------------
# Reihen über Sitzungen
# ---------------------------------------------------------------------------

def reihen(marker_je_sitzung: list[dict[str, "object"]],
           sprecher: str = KLIENT) -> dict[str, list[float]]:
    """Baut aus den Sitzungsmarkern eine Reihe pro Kennzahl.

    **Nur vollständige Reihen kommen zurück.** Wechselt ein Klient mitten in
    der Fallgeschichte die Sprache, gibt es Kennzahlen, die nur einen Teil der
    Sitzungen haben — ``man_quote`` für die deutschen, ``generisch_quote`` für
    die englischen. Eine Reihe, die für die halbe Achse keinen Wert hat, darf
    nicht gezeichnet werden: die Lücke mit Nullen zu füllen wäre eine
    Behauptung über eine Sitzung, in der gar nicht gemessen wurde.

    Stattdessen bekommt jeder Begriff aus ``VERGLEICHBAR`` zusätzlich eine
    zusammengesetzte Reihe unter ``vgl_<begriff>``. Sie ist über die
    Sprachgrenze hinweg durchgehend und trägt genau so viel, wie der
    Docstring von :mod:`therapy.sprachen` es zulässt: der Verlauf ist
    lesbar, die Höhe ist zwischen den Abschnitten nicht vergleichbar, und die
    Oberfläche schreibt das an die Kurve.
    """
    je_sitzung: list[dict[str, float]] = []
    for eintrag in marker_je_sitzung:
        sm = eintrag[sprecher]
        werte = dict(kennzahlen(sm))
        pak = sprachen.paket(getattr(sm, "sprache", sprachen.STANDARD))
        for begriff, schluessel in pak.VERGLEICHBAR.items():
            if schluessel in werte:
                werte["vgl_" + begriff] = werte[schluessel]
        je_sitzung.append(werte)

    if not je_sitzung:
        return {}
    gemeinsam = set(je_sitzung[0])
    for werte in je_sitzung[1:]:
        gemeinsam &= set(werte)
    return {schluessel: [float(w[schluessel]) for w in je_sitzung]
            for schluessel in gemeinsam}


def komposit(serien: dict[str, list[float]],
             sprache: str = sprachen.STANDARD) -> list[float]:
    """Gewichteter Index aus mehreren Markern, z-standardisiert.

    Einzelne Marker rauschen bei einer Sitzung pro Woche stark. Der Index
    bündelt die, die in dieselbe Richtung zeigen sollten (Aneignung,
    Differenzierung, Verarbeitung), und macht den Wechselpunkt dadurch
    überhaupt erst auffindbar. Das Vorzeichen jeder Komponente steht im
    Sprachpaket unter ``KOMPOSIT_INDEX`` und ist eine inhaltliche Setzung,
    keine statistische.

    Beide Sprachen benutzen dieselben zehn Komponenten mit denselben
    Gewichten. Da jede Komponente vor der Summierung z-standardisiert wird,
    rechnet der Index ohnehin in Standardabweichungen *dieses* Falles und
    nicht in Raten — deshalb ist er die eine Zahl in diesem Werkzeug, die eine
    Sprachgrenze verträgt.
    """
    laenge = max((len(v) for v in serien.values()), default=0)
    if not laenge:
        return []
    pak = sprachen.paket(sprache)
    # Rückwärtsabbildung: wenn der sprachspezifische Schlüssel fehlt, weil der
    # Klient die Sprache gewechselt hat, springt die zusammengesetzte Reihe
    # ein. Ohne das verlöre der Index bei gemischten Fällen ausgerechnet die
    # Distanzierung — die Komponente mit dem grössten Gewicht.
    ersatz = {schluessel: "vgl_" + begriff
              for begriff, schluessel in pak.VERGLEICHBAR.items()}
    summe = [0.0] * laenge
    gewicht_summe = 0.0
    for schluessel, gewicht in pak.KOMPOSIT_INDEX.items():
        werte = serien.get(schluessel)
        if not werte and schluessel in ersatz:
            werte = serien.get(ersatz[schluessel])
        if not werte or len(werte) != laenge:
            continue
        z = _standardisiere(werte)
        for i, x in enumerate(z):
            summe[i] += gewicht * x
        gewicht_summe += abs(gewicht)
    if not gewicht_summe:
        return []
    return [s / gewicht_summe for s in summe]


def beschreibe(wp: Wechselpunkt, sitzungsnummern: list[int]) -> str:
    """Der eine Satz, um den es geht."""
    nr = wp.sitzung or (sitzungsnummern[wp.position]
                        if wp.position < len(sitzungsnummern) else wp.position)
    richtung = "rises" if wp.nachher > wp.vorher else "falls"
    sicherheit = ("clearly" if wp.bayes_faktor > 10
                  else "noticeably" if wp.bayes_faktor > 3 else "weakly")
    return (f"Something shifts around session {nr}: the index {richtung} "
            f"{sicherheit} from there (Bayes factor {wp.bayes_faktor:.1f}).")


HINWEIS = (
    "Changepoints are places worth re-reading, not events. A year of weekly "
    "sessions is twelve to fifty data points, and on that many any method will "
    "find something. The Bayes factor says how much more the data favour a step "
    "over ordinary fluctuation; below 3 nothing is reported at all."
)
