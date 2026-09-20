# Thera.py

**Read a year of transcripts at once.**

> Present in every hour. Legible only across the year.

The transcripts are German or English, per session, mixed freely in one
caseload. The interface is always English. That split is deliberate: the
markers worth counting are properties of a language and do not survive
translation, but the person using the tool reads English.

Thera.py does two things a therapist cannot do unaided.

**See a year at once.** After twelve months you remember session 1, session 9
(the big one), and last week. Everything in between has collapsed into an
impression. Thera.py restores the middle.

**See yourself.** Therapists are trained on their own process but almost never
get quantitative feedback on it. That is the part that will be least
comfortable and most valuable.

---

## In three sentences

You open a web page, drag your transcripts onto it, and get trajectories,
lists and evidence. The files never leave your machine — the whole analysis
runs in the browser. You can load the page, switch off your Wi-Fi, and keep
working.

---

## The proof that nothing is transmitted

This is not a promise, it is a property of how the thing is built, and you can
check it yourself:

1. Open the page and wait until the header shows “v0.1.0”.
2. **Switch off Wi-Fi** or unplug the network cable.
3. Drop transcripts on the page and work normally.

Everything still works. An application that sent data anywhere could not do
that. It is worth more than any privacy statement.

The reason: the page is a set of files your browser downloads once. The
analysis itself is a Python runtime that executes *inside* your browser. There
is no place in this program that transmits transcript content — and the browser
additionally forbids it, via a Content-Security-Policy in `index.html`.

**The flip side, so that it is said:** results live only in that browser tab.
Reload the page and you start over. Anything you want to keep, you export with
the *Export* button to a file on your own machine. In exchange, Thera.py cannot
be subpoenaed, breached, or quietly changed under you.

### With no foreign server at all

On the very first visit the page downloads the Python runtime (Pyodide) from a
public CDN. That one request fetches program files and sends nothing of yours —
but if you want it gone too:

```bash
curl -L https://github.com/pyodide/pyodide/releases/download/0.26.4/pyodide-0.26.4.tar.bz2 -o pyodide.tar.bz2
tar xjf pyodide.tar.bz2
mkdir -p vendor && mv pyodide vendor/pyodide
```

If `vendor/pyodide/pyodide.js` exists, Thera.py uses that copy automatically.
The page then makes literally no foreign request. (You can then delete the two
`jsdelivr` entries from the Content-Security-Policy in `index.html`.)

---

## Getting your transcripts in

**The short way: paste everything into the box.** One long text with your
sessions one after another, in the order they happened. That is the normal
case — a year of therapy usually lives in one document, not in twelve neatly
named files.

**Mark where each session starts** with a line of its own:

```
--- Session 7 — 2024-03-14 ---
### Sitzung 7
2024-03-14
```

Any of those works, and the number and date are read out of the line. Two such
lines are enough to split the text; a single one is treated as a heading.

**Without any marker**, a long text is cut into equal segments instead. They
are called *Segment 1…N*, never *Session*, and the report says plainly that the
trend you are looking at runs *within* the text rather than between sessions.

**Or drop files** — that still works exactly as before, one file per session,
all formats:

`.txt` · `.md` · `.vtt` · `.srt` · `.json` (Whisper) · `.csv` · `.tsv` ·
`.docx` · `.html`

Anything that marks who is speaking works best:

```
Therapeut: Wie war die Woche?

Klientin: Schwierig. Ich habe viel nachgedacht.
```

```
Therapist: How was the week?

Client: Hard. I kept thinking about it.
```

The speaker may also stand on a line of its own, which is how a Word or HTML
export usually sets it:

```
Therapeut
Wie war die Woche?

Patientin
Schwierig. Ich habe viel nachgedacht.
```

Recognised labels include `Therapeut:`, `Therapist:`, `T:`, `Klientin:`,
`Client:`, `Pat:`, `Sprecher 1:`, `SPEAKER_00`, timestamps in brackets, and the
usual subtitle formats.

### If your transcript comes out of a documentation assistant

The AI assistants that record and transcribe sessions — VIA and its like —
export Word, PDF and HTML. Word and HTML drop straight onto this page; for PDF,
copy the text and paste it into the box. Three things are worth knowing before
you rely on it:

**Export the transcript, not the notes.** The generated session notes are a
summary in the assistant's own words. They have no turns and no speakers, so
everything on the dialogue side — talk ratio, turn lengths, question types,
uptake, style matching, dropped threads — goes dark. The ingest report says so
plainly, but it is a wasted export either way.

**Check who is who.** An exporter that writes `Sprecher 1` and `Sprecher 2` has
separated the voices without knowing which is which. Thera.py then guesses by a
rule it names — whoever talks less is the therapist — and says so in the ingest
report. That rule is wrong for any hour you spent explaining something. There is
a *swap* button next to the guess; it costs one click and it is the single
judgement everything about *you* rests on.

**Save the transcript the same day.** These assistants delete session data
within the day, by design — that is the point of them. Nothing is archived on
your behalf, so a year only exists if you exported each hour as it happened.

**Filenames help.** Put the session number, the date and the client in the
name and Thera.py sorts and groups everything by itself:

```
klient-anna_sitzung-07_2024-03-14.txt
client-jane_session-07_2024-03-14.txt
```

**Language is detected per file**, from the text. If you would rather not leave
it to a heuristic, put `_de` or `_en` in the name and that wins. Either way the
detected language is shown in *What was read*, where a dropdown corrects it
in one click.

**When something is not recognised, Thera.py tells you.** The first view after
loading is *What was read*: per file, what was found, how the text was split
into sessions, and which figures are therefore *unavailable*. Pasted text has
no filename and so arrives as one unnamed case; the name is a label you can
type in there, and it is neither analysed nor exported.

---

## The views

**What was read** — what was found, in which language, how the text was split,
and what is missing. Look at this first.

**Session** — one page per session: language markers, affect through the hour,
talk ratio, question types, new vocabulary, dropped threads.

**Trends** — the year at once. Every marker as a trajectory, changepoints
marked, and who enters and leaves the narrative.

**Keywords** — which words carry the case. What is distinctive about one
session against the others, what separates the late sessions from the early
ones, which vocabulary is rising and which is fading, compounds split open, and
any word you name plotted across the whole text.

**Concordance** is reachable from anywhere. Every number in the tool is
clickable and opens the lines that produced it. That is not a convenience, it
is the point: without the way back, Thera.py would become a dashboard you watch
instead of a person you listen to.

---

## What Thera.py does not do

No diagnoses. No scores. No severity ratings. No “insights” written in
sentences. It counts things, plots them over time, and shows you where every
number came from. The interpretation is your work and stays your work.

---

## What you need to know about the numbers

Every figure carries a confidence grade in the interface:

| | |
|---|---|
| **A** | well grounded, robustly computable |
| **B** | sound reasoning, heuristic implementation, useful as a trajectory |
| **C** | exploratory. Interesting to look at, not to conclude from. |

The same marker can carry different grades in the two languages, and where it
does, the panel says why. German `man` is grade A because it is a dedicated
pronoun that cannot be anything else; the English equivalent, generic *you*, is
grade B because the same word is usually how the therapist is addressed.

And, without softening:

- **One session is noise.** Below roughly ten sessions most markers mean
  nothing.
- **A transcript is not a session.** Tone, pause, body and silence are gone.
  Thera.py reads the shadow of the hour, not the hour.
- **Speech-recognition errors are not random.** They fall hardest on exactly
  the low-frequency emotional vocabulary the granularity measure most wants to
  count.
- **The lexicons are adapted, not validated.** Which direction the adaptation
  runs differs per marker, and it is not always the German side that is
  borrowing: the absolutist list is an English instrument in German clothes,
  while style matching and the causal/insight lists are English originals that
  the German side had to translate. What is deliberately *excluded* — “total”,
  “voll”, “ganz” and “totally”, “completely”, “literally” as colloquial
  intensifiers — is documented with reasons in `pysrc/therapy/lexika/marker.py`
  and `pysrc/therapy/lexika_en/marker.py`.
- **Numbers do not cross the language line.** Within German, or within English,
  the trajectories compare cleanly. Between the two they do not: the word lists
  are different sizes, so the levels sit differently for reasons that have
  nothing to do with the client. Wherever the tool puts the two side by side —
  a client who switched language mid-course — it marks the row and says what
  survives the crossing and what does not.
- **Keyness carries two numbers, and they answer different questions.** G²
  says how confident a difference is and grows with the amount of text — over a
  year almost everything ends up looking significant. Log ratio says how large
  it is. Read them together, and read the lines behind them before believing
  either.

### Consent

Your clients consented to being recorded. They almost certainly did not consent
to computational analysis of their language. That is your call to make — but it
should be made deliberately rather than by default, and it is worth raising
with your professional body.

---

## The two languages

Each session is analysed in the language it was spoken in, with that language's
own word lists. Nothing is ever translated — a translated lexicon measures the
translation.

Where the two languages do the same job with different machinery, the tool
measures the same construct under the same key and labels it honestly:

| | German | English |
|---|---|---|
| Distancing from “I” | `man` (grade A) | generic *you*, *one*, *people* (grade B) |
| Counterfactual | Konjunktiv II, unambiguous umlaut forms (A) | *would have*, *if I were*, *I wish* (B) |
| Attitude marking | modal particles: *halt*, *eben*, *doch*, *nur* | downtoners: *anyway*, *really*, *just*, *I suppose* |
| Obligation | *muss*, *soll*, *darf nicht* | *have to*, *supposed to*, *gotta*, *should* |
| Passive | *werden* + participle | *be*/*get* + participle, minus predicative adjectives |
| Past | mostly perfect in speech | perfect and simple past, counted separately |

Two things exist on one side only, and they are simply absent on the other
rather than faked:

- **Compound splitting** is German-only. “Verlustangst” has to be prised open
  or it vanishes into the tail; English writes its compounds open (“fear of
  loss”), so they arrive already split and the Keywords view drops the block.
- **Honorific forms** (`Sie`/`Ihnen`) are German-only. English has no
  T–V distinction, so the tile does not appear rather than showing a zero.

Two places where English is the better-off side, said plainly because the rest
of this section runs the other way: **name detection** is more reliable, because
a capitalised word mid-sentence is a proper-name signal in English and merely a
noun signal in German; and **style matching** is at home, having been developed
on English function words, so the German figure is the adapted one.

If a client's sessions are not all in the same language, markers that exist in
only one of them are left out of the charts entirely rather than padded with
zeros, and a spliced “across languages” series is drawn for the constructs that
have a counterpart on both sides — to be read for its shape within each stretch,
not for the step between them.

---

## Names

Before anything is analysed, Thera.py looks for personal names in the text and
puts them in front of you once for confirmation. What you confirm is replaced
with stable placeholders — “Person A” is the same person across all twelve
sessions, otherwise the sociogram would be worthless.

The mapping from placeholder to name stays in your browser, is never stored,
and is not part of the export. Reload the page and it is gone.

The detection is deliberately a heuristic with a confirmation step rather than
named-entity recognition: you know who these people are, the machine does not.

---

## Under the hood

### Layout

```
index.html            entry point (GitHub Pages)
app/
  main.js             Pyodide bootstrap, files, routing
  views.js            the four views
  charts.js           hand-rolled SVG, no chart library
  styles.css          light and dark
pysrc/therapy/       the actual work, pure Python
  ingest.py           format detection, parsing, speaker assignment, findings
  pseudonym.py        names → placeholders, before anything else
  tokenize.py         tokenisation, sentences, coarse lemmas, compounds
  markers.py          the marker pipeline — language-agnostic
  dialogue.py         talk ratio, questions, uptake, style matching
  lexical.py          concordance, collocations, keyness, type-token
  threads.py          dropped threads
  people.py           sociogram
  arc.py              series across sessions, Bayesian changepoints
  report.py           the JSON contract to the interface
  sprachen/           language detection and one pack per language
    de.py             German morphology, metrics, labels, tile order
    en.py             English, the same list, different machinery
  lexika/             the German word lists, with reasoning in the source
  lexika_en/          the English ones, same structure
samples/              synthetic transcripts — never real material
tests/                hand-checked sentences per marker, per language
```

**Where the languages live.** Everything that depends on the language sits in
exactly one place — a *language pack* under `sprachen/`. Everything else, from
the concordance to the changepoint detection to the interface, asks the pack for
what it needs and otherwise knows nothing about language. That is why adding
English did not fork the pipeline: `markers.py` still holds one procedure, and
the German numbers are unchanged after the rewrite, which is what
`tests/test_marker.py` is there to prove.

The interface has no hard-coded marker names at all. Which tiles a session card
shows, which series the Trends view draws, and every label and caveat come from the
report, keyed by the session's language.

No bundler, no npm, no build step. Editing a `.py` file and pushing updates the
live tool. That property is deliberate and worth protecting: it means this is
still maintainable in three years when neither of us remembers how it works.

**A note on the code's language.** The interface is English; the Python
identifiers are German (`konjunktiv2`, `partikel_resignativ`, `Sitzung`). That
is not an oversight. These names denote grammatical categories, and where the
category is German it keeps its German name — renaming `man_quote` to something
English would make the code read as if it were measuring something it is not.
The same rule gives the English-only metrics their own keys (`generisch_quote`,
`irrealis_rate`) rather than pretending they are the German ones. Keys are
shared between the two packs exactly when both languages measure the same
thing; `VERGLEICHBAR` in each pack records which pairs are *comparable*, and
that word means “measures the same construct”, never “is the same number”.
The translation to English happens in the label tables in `sprachen/de.py`,
`sprachen/en.py` and `dialogue.py`, and in the two `dialogmuster.py` files.

**Zero runtime dependencies.** No numpy, no pandas, no spaCy, no `micropip`.
Everything is standard library. That is not asceticism, it is what makes the
promise above possible: every additional dependency would be a network call at
startup.

What it costs, plainly: no dependency parsing, no named-entity recognition, no
transformer sentiment, and no language-identification library. Acceptable — the
markers that matter here are morphological and lexical, a transformer sentiment
score is the number a clinician should trust least anyway, and telling German
from English over a whole transcript is a job that a function-word profile does
well enough to hand back a confidence with it.

### Run it locally

```bash
python -m http.server 8765
```

Then open `http://localhost:8765`.

### Over a whole corpus, without a browser

```bash
pip install -e .
therapy befund ./transcripts
therapy auswerten ./transcripts --ausgabe report.json
therapy konkordanz ./transcripts "Angst" --sprecher K
therapy konkordanz ./transcripts "ashamed" --sprecher K
```

`befund` prints the detected language per file. `--sprache de|en` forces one
for the whole run if the detection gets it wrong.

Same code, same JSON contract as the interface.

### Tests

```bash
pip install -e ".[dev]"
pytest
```

`tests/test_marker.py` and `tests/test_marker_en.py` double as the substantive
documentation of the markers: each one has at least one hand-checked example
sentence in its own language and one counter-example. `tests/test_sprache.py`
covers detection, the manual override, and what a mixed caseload is and is not
allowed to compare.

### Sample data

`samples/` holds 12 synthetic transcripts of one invented English case,
generated from sentence banks (`python samples/_generator.py`). They
deliberately contain a trajectory with a step around session 9, so you can see
that the Trends view and the changepoint detection do what they claim.

One case is the deliberate minimum: it is enough to show a session card, a
trajectory and the dropped threads. What a single case cannot show is not
faked — with nothing to be distinctive *against*, Keywords says so and falls
back to comparing the text with itself, one session against the others and the
late sessions against the early ones. Language detection still runs on the
text rather than on the filename, so the language column in *What was read* is
doing real work even here.

**No real client material is ever committed to that folder.** Not
de-identified, not redacted, not in a branch.

---

## Deploying

GitHub Pages from `/` on `main`. The repository *is* the site.

---

*Name note: “Thera.py” is the display name and the repository name. Python
packages cannot contain a dot, so the importable package is `therapy` and the
distribution is `thera-py`. Both are common enough words that they may already
be taken on PyPI — check before you publish there. Nothing about the tool
depends on it: rename the distribution in `pyproject.toml` and everything else
keeps working.*
