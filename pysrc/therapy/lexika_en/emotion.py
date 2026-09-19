"""Englisches Emotionslexikon — auf Differenzierung ausgelegt, nicht auf Valenz.

Derselbe entscheidende Unterschied zu einem Sentiment-Lexikon wie im
deutschen Modul: hier wird nicht gemessen, *wie gut oder schlecht* es
jemandem geht, sondern *wie fein er es sagen kann*. Der Weg von "bad" und
"weird" zu "slighted", "wistful", "relieved" ist das therapeutische Ziel
selbst, und er ist zählbar.

Die Familien sind **dieselben vierzehn wie im deutschen Modul**, mit
denselben Schlüsseln und denselben Valenzen. Das ist der einzige Grund,
warum ein gemischtes Korpus überhaupt eine gemeinsame Affektkurve haben
kann, und es ist eine inhaltliche Setzung: die Familien sind hier als
klinische Kategorien gemeint und nicht als Eigenschaften der jeweiligen
Sprache.

Was dabei **nicht** behauptet wird: dass "Wut" und "anger" dieselbe
Wortfeldgrösse haben. Haben sie nicht, und deshalb sind die Affektraten
zwischen den Sprachen nicht vergleichbar. Vergleichbar ist der Verlauf
innerhalb einer Sprache. Die Oberfläche sagt das an jeder Kurve, die
Sitzungen beider Sprachen enthält.

Ein englischspezifischer Gewinn, der hier ausgenutzt wird: Englisch hat für
Affekt eine ungewöhnlich grosse Zahl von Ein-Wort-Adjektiven mittlerer
Frequenz ("miffed", "wistful", "smitten", "queasy"). Genau das ist das
Material, das die Granularitätsmessung sehen will.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Emotionsfamilien
# ---------------------------------------------------------------------------
#
# Familien statt einer flachen Liste, weil die klinisch interessante Frage
# selten "wie viel Affekt" ist, sondern "welcher Affekt, und seit wann".
# Ein Wort darf in mehreren Familien stehen (Scham/Schuld überlappen real).

FAMILIEN: dict[str, set[str]] = {
    "angst": {
        "afraid", "fear", "fears", "feared", "fearful", "scared", "scary",
        "frightened", "terrified", "terror", "panic", "panicked", "panicky",
        "anxious", "anxiety", "worried", "worry", "worries", "worrying",
        "nervous", "nerves", "uneasy", "unease", "apprehensive", "dread",
        "dreading", "jumpy", "on edge", "edgy", "tense", "restless",
        "insecure", "insecurity", "unsafe", "threatened", "vulnerable",
        "helpless", "powerless", "at their mercy", "phobia", "paranoid",
        "catastrophising", "catastrophizing", "worst case", "spiralling",
        "spiraling", "freaking out", "freaked out", "butterflies",
    },
    "trauer": {
        "sad", "sadness", "sorrow", "sorrowful", "grief", "grieving", "grieve",
        "mourning", "mourn", "down", "low", "blue", "heavy hearted",
        "downcast", "dejected", "despondent", "melancholy", "melancholic",
        "wistful", "heartbroken", "heartbreak", "devastated", "crushed",
        "despair", "desperate", "hopeless", "hopelessness", "bleak",
        "empty", "emptiness", "hollow", "numb", "crying", "cried", "tears",
        "tearful", "weeping", "sobbing", "loss", "lost her", "lost him",
        "miss", "missed", "missing him", "missing her", "longing", "yearning",
        "ache", "aching", "bereft", "resigned", "resignation",
    },
    "wut": {
        "angry", "anger", "mad", "furious", "fury", "rage", "raging", "enraged",
        "irate", "livid", "cross", "annoyed", "annoying", "annoyance",
        "irritated", "irritation", "irritable", "frustrated", "frustration",
        "aggravated", "exasperated", "indignant", "outraged", "outrage",
        "resentful", "resentment", "bitter", "bitterness", "grudge",
        "hate", "hated", "hatred", "loathe", "seething", "fuming", "fed up",
        "sick of", "pissed off", "wound up", "boiling", "snapped", "lash out",
        "lashed out", "miffed", "peeved", "vengeful", "revenge",
    },
    "scham": {
        "ashamed", "shame", "shameful", "embarrassed", "embarrassing",
        "embarrassment", "humiliated", "humiliating", "humiliation",
        "mortified", "cringe", "cringing", "self conscious", "exposed",
        "small", "worthless", "worthlessness", "inadequate", "inadequacy",
        "inferior", "inferiority", "not good enough", "not enough",
        "failure", "failed", "failing", "loser", "pathetic", "useless",
        "defective", "flawed", "broken", "unworthy", "undeserving",
        "hiding", "hide it", "found out", "seen through", "exposed as",
    },
    "schuld": {
        "guilt", "guilty", "guilt tripping", "conscience", "remorse",
        "remorseful", "blame", "blamed", "blaming", "blameworthy",
        "self blame", "my fault", "at fault", "responsible", "responsibility",
        "accountable", "let them down", "let him down", "let her down",
        "should have known", "owe", "owed", "make amends", "make it up",
        "apologise", "apologize", "apologised", "apologized", "sorry",
        "regret", "regretted", "did wrong", "in the wrong",
    },
    "freude": {
        "happy", "happiness", "glad", "gladness", "joy", "joyful", "joyous",
        "delighted", "delight", "pleased", "cheerful", "cheery", "merry",
        "elated", "elation", "thrilled", "excited", "excitement", "buzzing",
        "upbeat", "chuffed", "content", "contented", "contentment",
        "satisfied", "satisfaction", "grateful", "gratitude", "thankful",
        "proud", "pride", "enjoyed", "enjoying", "enjoyment", "laughed",
        "laughing", "laughter", "smiling", "light", "lightness", "alive",
        "playful", "fun",
    },
    "erleichterung": {
        "relieved", "relief", "unburdened", "lighter", "eased", "at ease",
        "freed", "freedom from", "liberated", "reassured", "reassurance",
        "calmed", "settled", "let go of", "off my chest", "weight lifted",
        "weight off", "breathe again", "breathing again", "finally quiet",
        "less pressure", "it passed", "it lifted",
    },
    "hoffnung": {
        "hope", "hopes", "hopeful", "hoping", "hoped", "optimism",
        "optimistic", "confidence", "confident", "faith", "trust", "trusting",
        "encouraged", "encouraging", "courage", "brave", "bravery", "daring",
        "prospect", "prospects", "possibility", "possibilities", "chance",
        "looking forward", "something to aim at", "a way out", "a way through",
    },
    "ekel": {
        "disgust", "disgusted", "disgusting", "revolted", "revolting",
        "repulsed", "repulsive", "repelled", "sickened", "sickening",
        "nauseated", "queasy", "gross", "vile", "contempt", "contemptuous",
        "scorn", "scornful", "distaste", "skin crawl", "skin crawling",
    },
    "überraschung": {
        "surprised", "surprise", "astonished", "astonishment", "amazed",
        "stunned", "startled", "taken aback", "caught off guard",
        "blindsided", "speechless", "didn't see it coming", "out of nowhere",
        "unexpected", "unexpectedly", "floored",
    },
    "zuneigung": {
        "love", "loved", "loving", "lovely", "affection", "affectionate",
        "fond", "fondness", "tender", "tenderness", "warm", "warmth",
        "close", "closeness", "intimate", "intimacy", "connected",
        "connection", "attached", "bonded", "safe with", "held", "cared for",
        "caring", "cherish", "cherished", "adore", "adored", "smitten",
        "at home with", "belonging", "belong",
    },
    "einsamkeit": {
        "lonely", "loneliness", "alone", "on my own", "by myself",
        "isolated", "isolation", "cut off", "shut out", "left out",
        "excluded", "abandoned", "abandonment", "rejected", "rejection",
        "unwanted", "unloved", "invisible", "unseen", "overlooked",
        "misunderstood", "nobody gets it", "no one understands",
        "no one to call", "outsider", "estranged", "distant from",
    },
    "neid": {
        "envy", "envious", "jealous", "jealousy", "resentful of", "begrudge",
        "comparing myself", "compare myself", "why them", "why not me",
        "unfair", "unfairness", "left behind", "everyone else has",
    },
    "überforderung": {
        "overwhelmed", "overwhelming", "swamped", "snowed under", "buried",
        "exhausted", "exhaustion", "drained", "depleted", "burned out",
        "burnt out", "burnout", "worn out", "wiped out", "running on empty",
        "no energy", "no capacity", "spent", "knackered", "shattered",
        "can't keep up", "too much", "stretched", "stretched thin",
        "pressure", "pressured", "stress", "stressed", "stressful",
        "under the pump", "juggling", "spread thin", "at my limit",
        "breaking point", "at capacity",
    },
    "ruhe": {
        "calm", "calmness", "peaceful", "peace", "at peace", "quiet inside",
        "still", "stillness", "steady", "steadier", "settled", "grounded",
        "centred", "centered", "balanced", "even", "stable", "secure",
        "safe", "safety", "clear", "clarity", "composed", "collected",
        "level headed", "in myself", "myself again",
    },
}

# Identisch zum deutschen Modul — die Valenzen gehören zur klinischen
# Kategorie, nicht zur Sprache.
VALENZ = {
    "angst": -1, "trauer": -1, "wut": -1, "scham": -1, "schuld": -1,
    "ekel": -1, "einsamkeit": -1, "neid": -1, "überforderung": -1,
    "freude": +1, "erleichterung": +1, "hoffnung": +1, "zuneigung": +1,
    "ruhe": +1,
    "überraschung": 0,
}

# Umgekehrter Index: Wort -> Familien.
WORT_ZU_FAMILIE: dict[str, list[str]] = {}
for _fam, _woerter in FAMILIEN.items():
    for _w in _woerter:
        WORT_ZU_FAMILIE.setdefault(_w, []).append(_fam)
del _fam, _woerter, _w

DIFFERENZIERT: set[str] = set(WORT_ZU_FAMILIE)


# ---------------------------------------------------------------------------
# Vager Affekt
# ---------------------------------------------------------------------------
#
# Der Gegenpol. Wörter, die einen Zustand melden, ohne ihn zu benennen.
# Nicht "schlechter" als differenzierter Affekt — nur undifferenzierter, und
# genau dieses Verhältnis ist die Messgrösse.
#
# Englisch hat hier eine Eigenheit, die die Zahl beeinflusst: "fine", "okay"
# und "alright" sind als Antwort auf "how are you" praktisch Grussformeln und
# tragen null Information. Sie stehen trotzdem drin, weil genau ihr *Anteil*
# an der gesamten Affektsprache die Messgrösse ist — jemand, der eine Stunde
# lang "fine" und "okay" sagt, ist der Befund.

VAGER_AFFEKT = {
    "bad", "good", "fine", "okay", "ok", "alright", "all right", "so so",
    "meh", "weird", "strange", "odd", "funny", "off", "not right",
    "not myself", "rubbish", "crap", "crappy", "rough", "tough", "hard",
    "difficult", "heavy", "horrible", "awful", "terrible", "dreadful",
    "great", "nice", "lovely", "wonderful", "amazing", "better", "worse",
    "uncomfortable", "comfortable", "unsettled", "unsettling", "wobbly",
    "all over the place", "up and down", "mixed", "conflicted", "confused",
    "muddled", "foggy", "flat", "blah", "numb", "nothing much", "neutral",
    "normal", "same as usual", "not great", "not good", "pretty bad",
}


# ---------------------------------------------------------------------------
# Körpernaher Affekt
# ---------------------------------------------------------------------------
#
# Manche Klienten sprechen konsequent im Körper statt im Gefühl. Das ist
# keine Schwäche und keine Alexithymie-Diagnose — es ist eine eigene Spur mit
# einer eigenen Trajektorie, und die Verschiebung zwischen Körper und Gefühl
# über die Sitzungen hinweg ist das Interessante daran.

KOERPER_AFFEKT = {
    # Orte
    "stomach", "belly", "gut", "chest", "ribs", "heart", "throat", "neck",
    "shoulders", "back", "head", "forehead", "jaw", "hands", "knees", "legs",
    "skin", "chest wall", "diaphragm", "solar plexus", "temples", "spine",
    # Empfindungen
    "tight", "tightness", "tightening", "pressure", "heavy", "heaviness",
    "lump", "knot", "knotted", "churning", "churn", "clenched", "clenching",
    "burning", "tingling", "numb", "numbness", "pins and needles", "queasy",
    "nauseous", "nausea", "dizzy", "dizziness", "lightheaded", "shaky",
    "shaking", "trembling", "sweating", "sweaty", "clammy", "racing heart",
    "heart racing", "pounding", "pulse", "breath", "breathing", "breathless",
    "can't breathe", "short of breath", "winded", "tense", "tension",
    "cramped", "cramping", "stiff", "rigid", "leaden", "hot", "cold",
    "ice cold", "fluttering", "flutter", "hollow", "empty inside",
    "closed up", "shut down", "frozen", "paralysed", "paralyzed",
    "disconnected from my body", "not in my body",
}


# ---------------------------------------------------------------------------
# Metaphern-Kandidaten
# ---------------------------------------------------------------------------
#
# Konfidenz C, und das steht auch in der UI. Was hier gezählt wird, sind
# Wörter aus Quelldomänen — ob sie im Satz *metaphorisch* gebraucht wurden,
# entscheidet das Werkzeug nicht. Der Nutzen liegt nicht in der Zahl, sondern
# darin, dass man sehen kann, wann ein Bild auftaucht, ob es mutiert und wann
# es verschwindet. Therapeuten leben von diesen Bildern.
#
# markers.py verlangt zusätzlich einen mentalen Bezug im selben Satz (ein
# Wort aus FAMILIEN, VAGER_AFFEKT oder eine Selbstreferenz), sonst zählt
# "weather" auch dann, wenn draussen wirklich Regen ist.
#
# Die Domänen sind dieselben zehn wie im deutschen Modul. Das ist keine
# Bequemlichkeit: die konzeptuellen Metaphern, um die es hier geht
# (LIFE IS A JOURNEY, EMOTIONS ARE CONTAINED SUBSTANCES), sind gerade die,
# von denen die Metapherntheorie behauptet, dass sie sprachübergreifend sind.

METAPHERN_DOMAENEN = {
    "bewegung": {
        "path", "way", "road", "step", "steps", "forward", "backward",
        "backwards", "stuck", "stalled", "standstill", "moving", "move on",
        "going round", "circles", "dead end", "crossroads", "detour",
        "direction", "running", "dragging", "drifting", "stumble",
        "stumbling", "tripping", "edge", "brink", "cliff", "ledge",
    },
    "behälter": {
        "full", "empty", "overflowing", "spill", "spilling", "burst",
        "bursting", "fill", "filled", "lid", "bottled", "bottling", "sealed",
        "shut", "open up", "opened up", "let in", "let out", "inside",
        "outside", "container", "vessel", "bucket", "tank", "reserves",
        "room for", "no room",
    },
    "raum": {
        "tight", "narrow", "wide", "space", "room", "air", "wall", "walls",
        "door", "doors", "window", "cage", "caged", "trapped", "prison",
        "locked in", "boxed in", "hole", "tunnel", "basement", "floor",
        "bottom", "deep", "high", "distance", "gap", "boundary",
        "boundaries", "close", "far",
    },
    "last": {
        "burden", "burdened", "weight", "weighed", "heavy", "shoulders",
        "carry", "carrying", "carried", "backpack", "baggage", "load",
        "loaded", "crushing", "crushed", "pressing", "put down", "set down",
        "unload", "shake off", "stone", "rock", "millstone", "anchor",
    },
    "wetter": {
        "cloud", "clouds", "cloudy", "grey", "gray", "fog", "foggy", "mist",
        "storm", "stormy", "thunder", "lightning", "rain", "raining",
        "pouring", "sun", "sunny", "clearing", "clear up", "brighten",
        "dark", "darker", "gloomy", "bleak", "light", "shadow", "shade",
        "cold", "frost", "ice", "thaw", "calm before",
    },
    "kampf": {
        "fight", "fighting", "fought", "battle", "war", "front line",
        "opponent", "enemy", "weapon", "shield", "armour", "armor",
        "defensive", "defend", "defending", "attack", "attacked", "guard",
        "guarded", "on guard", "win", "won", "lose", "lost", "defeat",
        "surrender", "give up", "protect", "protection", "cover", "retreat",
    },
    "bindung": {
        "thread", "threads", "string", "rope", "chain", "chains", "knot",
        "tied", "tie", "bound", "connected", "linked", "snapped", "broke off",
        "hold", "holding", "hold on", "let go", "cling", "clinging",
        "anchor", "roots", "bridge", "net", "safety net", "leash", "tether",
    },
    "wasser": {
        "wave", "waves", "flood", "flooded", "flooding", "drowning", "drown",
        "sinking", "sink", "surfacing", "come up for air", "current",
        "undertow", "pull", "depth", "deep end", "swimming", "treading water",
        "adrift", "shore", "island", "dry", "dried up", "drip", "trickle",
    },
    "maschine": {
        "function", "functioning", "working", "broken", "broke down",
        "breakdown", "fix", "fixing", "repair", "engine", "gears", "wheels",
        "switch", "switch off", "shut down", "turn off", "turn on",
        "autopilot", "automatic", "programmed", "wired", "battery",
        "recharge", "running on", "cog", "machine", "robot",
    },
    "dunkelheit_licht": {
        "dark", "darkness", "black", "blackness", "light", "lights", "bright",
        "glimmer", "spark", "flicker", "flickering", "gone out", "burned out",
        "blind", "blinded", "see", "seeing", "overlook", "dazzle", "dim",
        "shine", "shining", "tunnel vision",
    },
}

METAPHER_ZU_DOMAENE: dict[str, list[str]] = {}
for _dom, _woerter in METAPHERN_DOMAENEN.items():
    for _w in _woerter:
        METAPHER_ZU_DOMAENE.setdefault(_w, []).append(_dom)
del _dom, _woerter, _w


# ---------------------------------------------------------------------------
# Verneinter Affekt
# ---------------------------------------------------------------------------
#
# "I'm not sad" ist kein Trauer-Treffer im selben Sinn wie "I'm sad".
# markers.py prüft ein kurzes Fenster links auf Negation und zählt solche
# Treffer getrennt — verworfen werden sie nicht, denn ein Klient, der
# durchgehend verneinten Affekt produziert, ist selbst ein Befund.
#
# Das Fenster ist hier um eins grösser als im Deutschen: englische Negation
# steht am Hilfsverb ("I don't really feel angry"), deutsche näher am
# negierten Wort. Drei Tokens würden "don't ... angry" regelmässig verpassen.

NEGATIONS_FENSTER = 4  # Tokens rechts von der Negation


# ---------------------------------------------------------------------------
# Beziehungsbegriffe — Rohstoff für das Soziogramm
# ---------------------------------------------------------------------------

BEZIEHUNGS_BEGRIFFE = {
    "mother", "mum", "mom", "mummy", "mommy", "father", "dad", "daddy",
    "parents", "sister", "brother", "sibling", "siblings", "grandmother",
    "grandma", "granny", "nan", "grandfather", "grandad", "grandpa",
    "aunt", "auntie", "uncle", "cousin", "niece", "nephew",
    "wife", "husband", "partner", "boyfriend", "girlfriend", "friend",
    "friends", "best friend", "ex", "fiance", "fiancee", "spouse",
    "son", "daughter", "child", "children", "kid", "kids", "baby",
    "boss", "manager", "supervisor", "colleague", "colleagues", "coworker",
    "neighbour", "neighbor", "doctor", "gp", "teacher", "therapist",
    "counsellor", "counselor", "mother in law", "father in law",
    "stepfather", "stepmother", "stepdad", "stepmum", "stepmom",
    "sister in law", "brother in law", "flatmate", "roommate", "landlord",
}
