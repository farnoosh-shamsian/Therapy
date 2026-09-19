"""Pseudonymisierung — vor allem anderen.

Die Reihenfolge ist keine Geschmacksfrage: Namen werden ersetzt, *bevor*
irgendeine Analyse den Text anfasst. Alles, was danach gezählt, indiziert oder
exportiert wird, enthält dann nur noch stabile Platzhalter.

Die Zuordnungstabelle (Name → Platzhalter) bleibt ausschliesslich im
Arbeitsspeicher des Browsers. Sie wird nicht exportiert, nicht gespeichert und
nicht in den Bericht geschrieben. Wer die Seite neu lädt, hat sie verloren —
das ist gewollt.

Die Namenserkennung ist bewusst eine *Heuristik mit Bestätigungsschritt*. Eine
NER wäre hier schlechter, nicht besser: der Therapeut weiss, wer diese Menschen
sind, die Maschine nicht. Sie schlägt vor, er bestätigt einmal pro Klient.

**Zur Zweisprachigkeit — und das ist die eine Stelle, an der Englisch klar im
Vorteil ist.** Die deutsche Erkennung kämpft damit, dass alle Substantive
gross geschrieben sind: Grossschreibung mitten im Satz sagt nur "Substantiv"
und nicht "Name", und der halbe Aufwand im deutschen Zweig geht dafür drauf,
gewöhnliche Substantive wieder auszusortieren (Nomenendungen, Artikelprobe,
Kompositumsprobe). Im Englischen ist Grossschreibung mitten im Satz ein
Eigennamenhinweis und sonst fast nichts — die Erkennung wird dadurch
zuverlässiger und die Ausschlusslisten kürzer. Der Bestätigungsschritt bleibt
trotzdem, aus demselben Grund wie vorher.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import sprachen
from .lexika import emotion as lex_emo
from .lexika import funktion as lex_f
from .lexika import marker as lex_m
from .lexika.emotion import BEZIEHUNGS_BEGRIFFE
from .lexika_en import emotion as lex_emo_en
from .lexika_en import funktion as lex_f_en
from .lexika_en import marker as lex_m_en
from .tokenize import Token, tokenisiere

# Alles, was in irgendeinem Lexikon steht, ist ein deutsches Wort und damit
# kein Personenname. Ohne diesen Ausschluss schlägt die Heuristik „kommt nie
# kleingeschrieben vor“ bei jedem Substantiv an, das zufällig immer am
# Satzanfang oder als Nomen steht — „Angst“, „Verlustangst“, „Nachbarbüro“.
_LEXIKONWOERTER: set[str] = set()
for _menge in lex_m.WORTLISTEN.values():
    _LEXIKONWOERTER |= set(_menge)
for _menge in lex_emo.FAMILIEN.values():
    _LEXIKONWOERTER |= set(_menge)
for _menge in lex_emo.METAPHERN_DOMAENEN.values():
    _LEXIKONWOERTER |= set(_menge)
_LEXIKONWOERTER |= (lex_emo.VAGER_AFFEKT | lex_emo.KOERPER_AFFEKT
                    | lex_emo.BEZIEHUNGS_BEGRIFFE | lex_f.STOPPWOERTER
                    | lex_f.FUNKTIONSWOERTER | lex_f.RUECKKANAL)
for _paradigma in lex_f.PRONOMEN.values():
    _LEXIKONWOERTER |= {w.lower() for w in _paradigma}

# Dasselbe für Englisch, in einer eigenen Menge. Getrennt und nicht vereinigt:
# "Bald", "Gift", "Rat", "Hut", "Bad" und "Mist" sind in der einen Sprache
# gewöhnliche Wörter und in der anderen nichts davon. Eine gemeinsame Menge
# würde in beiden Richtungen Namen verschlucken, die die jeweils andere
# Sprache gar nicht kennt.
_LEXIKONWOERTER_EN: set[str] = set()
for _menge in lex_m_en.WORTLISTEN.values():
    _LEXIKONWOERTER_EN |= set(_menge)
for _menge in lex_emo_en.FAMILIEN.values():
    _LEXIKONWOERTER_EN |= set(_menge)
for _menge in lex_emo_en.METAPHERN_DOMAENEN.values():
    _LEXIKONWOERTER_EN |= set(_menge)
_LEXIKONWOERTER_EN |= (lex_emo_en.VAGER_AFFEKT | lex_emo_en.KOERPER_AFFEKT
                       | lex_emo_en.BEZIEHUNGS_BEGRIFFE | lex_f_en.STOPPWOERTER
                       | lex_f_en.FUNKTIONSWOERTER | lex_f_en.RUECKKANAL)
for _paradigma in lex_f_en.PRONOMEN.values():
    _LEXIKONWOERTER_EN |= {w.lower() for w in _paradigma}
del _menge, _paradigma

# ---------------------------------------------------------------------------
# Gazetteer
# ---------------------------------------------------------------------------
#
# Kein Anspruch auf Vollständigkeit — das ist ein Wahrscheinlichkeitsschub für
# die Erkennung, kein Namenslexikon. Fehlende Namen werden über die
# Grossschreibungs-Heuristik trotzdem gefunden.

VORNAMEN = {
    # weiblich
    "anna", "maria", "julia", "sarah", "sara", "laura", "lena", "lisa", "marie",
    "sophie", "sofia", "hannah", "emma", "mia", "lea", "leonie", "katharina",
    "christina", "stefanie", "sabine", "susanne", "petra", "monika", "andrea",
    "claudia", "nicole", "melanie", "jessica", "vanessa", "tanja", "silke",
    "birgit", "gabriele", "ursula", "renate", "helga", "ingrid", "brigitte",
    "elisabeth", "barbara", "martina", "kerstin", "heike", "anja", "nadine",
    "franziska", "carolin", "karin", "bettina", "daniela", "jana", "marion",
    "ute", "eva", "ruth", "hanna", "greta", "mara", "nina", "lara", "clara",
    "charlotte", "johanna", "amelie", "paula", "frieda", "ida", "luisa",
    "annika", "verena", "simone", "beate", "doris", "gisela", "hildegard",
    # männlich
    "michael", "thomas", "andreas", "peter", "stefan", "christian", "markus",
    "matthias", "daniel", "sebastian", "martin", "frank", "jan", "tobias",
    "florian", "alexander", "maximilian", "felix", "jonas", "leon", "paul",
    "lukas", "luca", "elias", "noah", "ben", "finn", "david", "simon", "philipp",
    "johannes", "niklas", "tim", "jens", "kai", "sven", "dirk", "uwe", "klaus",
    "wolfgang", "jürgen", "hans", "werner", "günther", "gerhard", "manfred",
    "helmut", "heinz", "rainer", "norbert", "bernd", "ralf", "holger", "olaf",
    "torsten", "carsten", "marco", "mario", "oliver", "robert", "richard",
    "erik", "lars", "nils", "moritz", "julian", "vincent", "theo", "emil",
    "anton", "oskar", "karl", "otto", "walter", "ernst", "fritz", "georg",
    "joachim", "rolf", "detlef", "axel", "arne", "bastian", "dominik",
}

# Grossgeschriebenes, das sicher kein Personenname ist.
NICHT_NAMEN = {
    "montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag",
    "sonnabend", "sonntag", "januar", "februar", "märz", "april", "mai",
    "juni", "juli", "august", "september", "oktober", "november", "dezember",
    "weihnachten", "ostern", "silvester", "pfingsten",
    "deutschland", "österreich", "schweiz", "berlin", "hamburg", "münchen",
    "köln", "frankfurt", "stuttgart", "leipzig", "dresden", "hannover",
    "europa", "amerika", "usa",
    "gott", "internet", "whatsapp", "instagram", "facebook", "google",
    "corona", "covid", "krankenkasse", "jobcenter", "praxis", "klinik",
    "reha", "therapie", "sitzung", "woche", "wochenende", "abend", "morgen",
    "nacht", "tag", "jahr", "monat", "zeit", "leben", "mensch", "menschen",
    "frage", "antwort", "gefühl", "gefühle", "gedanke", "gedanken",
    "herr", "frau", "familie", "arbeit", "beruf", "job", "schule", "uni",
}

# Typische deutsche Substantivendungen. Wer so endet, ist kein Vorname.
_NOMEN_ENDUNGEN = (
    "ung", "heit", "keit", "schaft", "tion", "sion", "ismus", "nis", "tum",
    "ling", "chen", "lein", "ei", "ur", "anz", "enz", "ität", "ment",
)

_HERR_FRAU = re.compile(r"\b(herr|frau|hr\.|fr\.)\s+([A-ZÄÖÜ][a-zäöüß]{2,})", re.I)

# ---------------------------------------------------------------------------
# Gazetteer und Ausschluesse, englisch
# ---------------------------------------------------------------------------

VORNAMEN_EN = {
    # weiblich
    "mary", "patricia", "jennifer", "linda", "elizabeth", "barbara", "susan",
    "jessica", "sarah", "karen", "nancy", "lisa", "margaret", "betty",
    "sandra", "ashley", "dorothy", "kimberly", "emily", "donna", "michelle",
    "carol", "amanda", "melissa", "deborah", "stephanie", "rebecca", "laura",
    "sharon", "cynthia", "kathleen", "helen", "amy", "shirley", "angela",
    "anna", "ruth", "brenda", "pamela", "nicole", "katherine", "samantha",
    "christine", "catherine", "virginia", "rachel", "janet", "emma", "olivia",
    "sophia", "isabella", "charlotte", "amelia", "mia", "harper", "evelyn",
    "abigail", "ella", "grace", "chloe", "lily", "hannah", "zoe", "megan",
    "claire", "louise", "jane", "alice", "rose", "eleanor", "beth", "kate",
    "holly", "gemma", "chelsea", "leanne", "siobhan", "niamh", "aoife",
    # maennlich
    "james", "robert", "john", "michael", "david", "william", "richard",
    "joseph", "thomas", "charles", "christopher", "daniel", "matthew",
    "anthony", "mark", "donald", "steven", "paul", "andrew", "joshua",
    "kenneth", "kevin", "brian", "george", "timothy", "ronald", "edward",
    "jason", "jeffrey", "ryan", "jacob", "gary", "nicholas", "eric",
    "jonathan", "stephen", "justin", "scott", "brandon", "benjamin",
    "samuel", "gregory", "alexander", "patrick", "jack", "dennis",
    "henry", "oliver", "harry", "noah", "leo", "arthur", "oscar",
    "archie", "theo", "freddie", "alfie", "liam", "ethan", "mason", "logan",
    "nathan", "aaron", "adam", "simon", "craig", "gareth", "rhys", "declan",
    "sean", "shane", "cian", "conor", "eoin",
}

# Grossgeschriebenes, das sicher kein Personenname ist.
#
# Deutlich kuerzer als die deutsche Liste, und das ist der Punkt: im
# Englischen ist ein grossgeschriebenes Wort mitten im Satz fast immer ein
# Eigenname. Was hier stehen muss, sind die Eigennamen, die keine *Personen*
# sind - Wochentage, Monate, Orte, Marken, Institutionen.
NICHT_NAMEN_EN = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "christmas", "easter", "halloween", "thanksgiving",
    "england", "scotland", "wales", "ireland", "britain", "america",
    "london", "manchester", "birmingham", "glasgow", "dublin", "leeds",
    "bristol", "liverpool", "edinburgh", "york", "europe", "usa", "uk",
    "god", "internet", "whatsapp", "instagram", "facebook", "google",
    "zoom", "netflix", "youtube", "twitter", "covid", "corona", "nhs",
    "university", "college", "school", "work", "office", "hospital",
    "clinic", "therapy", "session",
    # Wortformen, die die Heuristik sonst durchlaesst
    "i", "i'm", "i've", "i'd", "i'll", "ok", "okay", "mr", "mrs", "ms", "dr",
}

# "Mr Smith", "Mrs. Jones", "Dr Patel" - dieselbe Rolle wie _HERR_FRAU.
_MR_MRS = re.compile(r"\b(mr|mrs|ms|miss|dr|prof)\.?\s+([A-Z][a-z]{2,})")

# Ein grossgeschriebenes Wort direkt hinter einem Determinierer ist auch im
# Englischen meist kein Personenname. Der Fall ist seltener als im Deutschen,
# weil englische Substantive klein geschrieben werden - er kommt aber vor,
# etwa bei betont grossgeschriebenen Woertern im Transkript.
_DETERMINIERER_EN = {
    "the", "a", "an", "this", "that", "these", "those", "my", "your", "his",
    "her", "its", "our", "their", "some", "any", "no", "every", "each",
    "another", "such",
}



# Ein grossgeschriebenes Wort direkt hinter einem Determinierer oder Quantor
# ist ein gewöhnliches Substantiv: „nichts Besonderes“, „so eine Art“, „das
# Schlimmste“. Personennamen stehen im Deutschen normalerweise ohne Artikel.
# Der süddeutsche Fall („die Anna“) kostet uns dabei einen Treffer — billiger
# als zwanzig Substantive in der Vorschlagsliste.
_DETERMINIERER = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem",
    "einer", "eines", "kein", "keine", "keinen", "keinem", "keiner", "keines",
    "mein", "meine", "meinen", "meinem", "meiner", "dein", "deine", "sein",
    "seine", "ihr", "ihre", "ihren", "ihrem", "unser", "unsere", "euer", "eure",
    "dieser", "diese", "dieses", "diesem", "diesen", "jeder", "jede", "jedes",
    "alle", "allem", "viel", "viele", "wenig", "etwas", "nichts", "manche",
    "solche", "welche", "irgendein", "irgendeine", "im", "am", "zum", "zur",
    "beim", "ins", "vom", "aufs", "nach", "ganzen", "ganze",
}


@dataclass(slots=True)
class Namenskandidat:
    name: str
    haeufigkeit: int = 0
    belege: list[str] = field(default_factory=list)   # kurze Kontextausschnitte
    grund: str = ""
    sicherheit: float = 0.0
    beziehung: str | None = None     # "Mutter", "Chef", … falls im Umfeld genannt

    def als_dict(self) -> dict:
        return {
            "name": self.name,
            "haeufigkeit": self.haeufigkeit,
            "belege": self.belege[:3],
            "grund": self.grund,
            "sicherheit": round(self.sicherheit, 2),
            "beziehung": self.beziehung,
        }


# ---------------------------------------------------------------------------
# Erkennung
# ---------------------------------------------------------------------------

def finde_namen(texte: list[str], min_haeufigkeit: int = 1,
                sprache: str = sprachen.STANDARD) -> list[Namenskandidat]:
    """Sucht Personennamen-Kandidaten über mehrere Texte hinweg.

    Rückgabe ist nach Sicherheit sortiert und dafür gedacht, dem Therapeuten
    zur Bestätigung vorgelegt zu werden — nicht dafür, ungeprüft angewandt zu
    werden.

    ``sprache`` steuert, welcher der beiden Zweige gilt. Für ein gemischtes
    Korpus ruft ``report.py`` die Funktion je Sprache einmal auf und führt die
    Vorschläge zusammen: ein gemeinsamer Durchgang über beide Sprachen würde
    den Sprachen ihre jeweiligen Substantive gegenseitig als Namen
    unterschieben — "Rat", "Gift", "Bald" und "Hut" sind in der einen Sprache
    gewöhnliche Wörter und in der anderen nichts davon.
    """
    englisch = sprache == "en"
    vornamen = VORNAMEN_EN if englisch else VORNAMEN
    nicht_namen = NICHT_NAMEN_EN if englisch else NICHT_NAMEN
    determinierer = _DETERMINIERER_EN if englisch else _DETERMINIERER
    lexikonwoerter = _LEXIKONWOERTER_EN if englisch else _LEXIKONWOERTER
    anrede_muster = _MR_MRS if englisch else _HERR_FRAU
    beziehungsbegriffe = (lex_emo_en.BEZIEHUNGS_BEGRIFFE if englisch
                          else BEZIEHUNGS_BEGRIFFE)

    gross: dict[str, int] = {}
    klein_gesehen: set[str] = set()
    belege: dict[str, list[str]] = {}
    beziehung: dict[str, str] = {}
    nach_anrede: set[str] = set()
    mit_artikel: set[str] = set()

    for text in texte:
        for treffer in anrede_muster.finditer(text):
            nach_anrede.add(treffer.group(2).lower())
        tokens = tokenisiere(text, sprache)
        wort_tokens = [t for t in tokens if t.ist_wort]
        for i, tok in enumerate(wort_tokens):
            if not tok.gross_geschrieben or len(tok.text) < 3:
                if tok.ist_wort and not tok.gross_geschrieben:
                    klein_gesehen.add(tok.klein)
                continue
            satz_anfang = _ist_satzanfang(wort_tokens, i, tokens)
            schluessel = tok.klein
            if satz_anfang and schluessel not in vornamen:
                # Am Satzanfang ist Grossschreibung uninformativ.
                continue
            if i > 0 and wort_tokens[i - 1].klein in determinierer:
                mit_artikel.add(schluessel)
            gross[schluessel] = gross.get(schluessel, 0) + 1
            if len(belege.setdefault(schluessel, [])) < 3:
                belege[schluessel].append(_ausschnitt(text, tok))
            bez = _beziehung_im_umfeld(wort_tokens, i, beziehungsbegriffe)
            if bez and schluessel not in beziehung:
                beziehung[schluessel] = bez

    kandidaten: list[Namenskandidat] = []
    for wort, anzahl in gross.items():
        if anzahl < min_haeufigkeit:
            continue
        if wort in nicht_namen or wort in beziehungsbegriffe:
            continue
        if not englisch and wort.endswith(_NOMEN_ENDUNGEN):
            continue
        sicherheit, grund = 0.0, ""
        if wort in vornamen:
            sicherheit, grund = 0.9, ("known English first name" if englisch
                                      else "known German first name")
        elif wort in nach_anrede:
            sicherheit, grund = 0.85, (
                "follows an honorific (Mr/Mrs/Dr)" if englisch
                else "follows an honorific (Herr/Frau)")
        elif wort in mit_artikel:
            # Stand mindestens einmal hinter einem Artikel → Substantiv.
            continue
        elif wort in lexikonwoerter or (not englisch
                                        and _ist_bekanntes_kompositum(wort)):
            # Steht in einem Lexikon oder enthält ein Lexikonwort als
            # Kompositumsteil: gewöhnliches Substantiv, kein Name.
            continue
        elif englisch:
            # Hier zahlt sich die englische Kleinschreibung der Substantive
            # aus: ein unbekanntes, mitten im Satz grossgeschriebenes Wort ist
            # im Englischen ein Eigennamenhinweis und nicht bloss ein
            # Substantivhinweis. Deshalb 0.6 statt der 0.4, mit denen dasselbe
            # Signal auf der deutschen Seite bewertet wird.
            sicherheit, grund = 0.6, "capitalised mid-sentence, not a known word"
        elif wort not in klein_gesehen:
            # Kommt nie kleingeschrieben vor → kein gewöhnliches Substantiv?
            # Schwaches Signal, deshalb niedrige Sicherheit.
            sicherheit, grund = 0.4, "always capitalised, not a known word"
        else:
            continue
        if wort in beziehung:
            sicherheit = min(1.0, sicherheit + 0.1)
        if anzahl >= 3:
            sicherheit = min(1.0, sicherheit + 0.05)
        kandidaten.append(Namenskandidat(
            name=wort.capitalize(), haeufigkeit=anzahl, belege=belege.get(wort, []),
            grund=grund, sicherheit=sicherheit, beziehung=beziehung.get(wort),
        ))
    kandidaten.sort(key=lambda k: (-k.sicherheit, -k.haeufigkeit, k.name))
    return kandidaten


def _ist_bekanntes_kompositum(wort: str) -> bool:
    """„Verlustangst“, „Nachbarbüro“ — endet auf ein bekanntes deutsches Wort.

    Der Rechtskopf entscheidet im Deutschen über die Wortart. Wenn er ein
    Lexikonwort ist, ist das Ganze ein Substantiv und kein Nachname.
    """
    if len(wort) < 8:
        return False
    return any(len(kopf) >= 4 and wort.endswith(kopf) and wort != kopf
               for kopf in _LEXIKONWOERTER)


def _ist_satzanfang(wort_tokens: list[Token], i: int, alle: list[Token]) -> bool:
    if i == 0:
        return True
    return wort_tokens[i].satz != wort_tokens[i - 1].satz


def _ausschnitt(text: str, tok: Token, breite: int = 45) -> str:
    a = max(0, tok.start - breite)
    b = min(len(text), tok.end + breite)
    return ("…" if a > 0 else "") + text[a:b].strip() + ("…" if b < len(text) else "")


def _beziehung_im_umfeld(wort_tokens: list[Token], i: int,
                         begriffe: set[str] | None = None,
                         fenster: int = 4) -> str | None:
    """„meine Schwester Anna", „my sister Anna" — Rolle mitnehmen."""
    begriffe = BEZIEHUNGS_BEGRIFFE if begriffe is None else begriffe
    for j in range(max(0, i - fenster), min(len(wort_tokens), i + fenster + 1)):
        if j == i:
            continue
        if wort_tokens[j].klein in begriffe:
            return wort_tokens[j].text
    return None


# ---------------------------------------------------------------------------
# Ersetzung
# ---------------------------------------------------------------------------

_PLATZHALTER_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Pseudonymisierer:
    """Stabile Name→Platzhalter-Abbildung über eine ganze Fallgeschichte.

    Stabil heisst: derselbe Name bekommt in Sitzung 1 und Sitzung 12 denselben
    Platzhalter, sonst wäre das Soziogramm wertlos. Die Reihenfolge der
    Vergabe richtet sich nach der ersten Nennung.
    """

    def __init__(self, praefix: str = "Person") -> None:
        self.praefix = praefix
        self._zu_platzhalter: dict[str, str] = {}
        self._zu_name: dict[str, str] = {}
        self._zaehler = 0
        self.rollen: dict[str, str] = {}      # Platzhalter → bestätigte Rolle

    # -- Aufbau ----------------------------------------------------------
    def registriere(self, name: str, rolle: str | None = None) -> str:
        schluessel = name.strip().lower()
        if not schluessel:
            return name
        if schluessel not in self._zu_platzhalter:
            platz = f"{self.praefix} {self._buchstabe(self._zaehler)}"
            self._zaehler += 1
            self._zu_platzhalter[schluessel] = platz
            self._zu_name[platz] = name.strip()
        platz = self._zu_platzhalter[schluessel]
        if rolle:
            self.rollen[platz] = rolle
        return platz

    def registriere_alle(self, kandidaten: list[Namenskandidat]) -> None:
        for k in sorted(kandidaten, key=lambda k: (-k.sicherheit, k.name)):
            self.registriere(k.name, k.beziehung)

    def _buchstabe(self, n: int) -> str:
        if n < 26:
            return _PLATZHALTER_ALPHABET[n]
        return _PLATZHALTER_ALPHABET[n // 26 - 1] + _PLATZHALTER_ALPHABET[n % 26]

    # -- Anwendung -------------------------------------------------------
    def ersetze(self, text: str) -> str:
        """Ersetzt alle registrierten Namen im Text, inkl. Genitiv-s."""
        if not self._zu_platzhalter:
            return text
        muster = self._muster()
        if muster is None:
            return text

        def tausche(m: re.Match) -> str:
            gefunden = m.group(0)
            basis = gefunden.rstrip("'s").rstrip("s") if gefunden.lower() not in self._zu_platzhalter else gefunden
            platz = (self._zu_platzhalter.get(gefunden.lower())
                     or self._zu_platzhalter.get(basis.lower()))
            return platz or gefunden

        return muster.sub(tausche, text)

    def _muster(self) -> re.Pattern | None:
        namen = sorted(self._zu_platzhalter, key=len, reverse=True)
        if not namen:
            return None
        teile = "|".join(re.escape(n) for n in namen)
        return re.compile(rf"\b({teile})(?:'?s)?\b", re.IGNORECASE)

    # -- Auskunft --------------------------------------------------------
    @property
    def platzhalter(self) -> list[str]:
        return list(self._zu_name)

    def klarname(self, platzhalter: str) -> str | None:
        """Nur für die Anzeige im Browser des Therapeuten. Nie im Export."""
        return self._zu_name.get(platzhalter)

    def tabelle_fuer_anzeige(self) -> list[dict]:
        return [{"platzhalter": p, "name": n, "rolle": self.rollen.get(p)}
                for p, n in self._zu_name.items()]

    def zusammenfassung(self) -> dict:
        """Was in den Bericht darf: Anzahl, keine Namen."""
        return {"ersetzt": len(self._zu_name), "praefix": self.praefix}


def pseudonymisiere_sitzungen(sitzungen, pseudo: Pseudonymisierer) -> int:
    """Wendet die Ersetzung auf alle Turns an. Gibt die Zahl der Änderungen zurück."""
    geaendert = 0
    for sitzung in sitzungen:
        for turn in sitzung.turns:
            neu = pseudo.ersetze(turn.text)
            if neu != turn.text:
                turn.text = neu
                geaendert += 1
    return geaendert
