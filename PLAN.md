# Thera.py

**Distant reading for German psychotherapy transcripts.**

> Present in every hour. Legible only across the year.

A browser-based tool that reads a year of session transcripts at once and
surfaces what no one can hold in their head: how a client's language moves
over months, and how the therapist's own behaviour differs from client to
client.

Python, running in the browser. Nothing is uploaded, ever.

---

## 1. The premise

Two things a therapist cannot do unaided, and this tool does both:

**Seeing a year at once.** After twelve months, a therapist remembers session
1, session 9 (the big one), and last week. Everything in between has collapsed
into impression. A corpus view restores the middle.

**Seeing yourself.** Therapists are trained on their own process but almost
never get quantitative feedback on it. This is the part that will be least
comfortable and most valuable.

Everything in the metric catalogue below serves one of those two. Anything
that serves neither gets cut.

**Explicit non-goal:** this tool produces no scores, no severity ratings, no
diagnostic suggestions, and no "insights" written in sentences. It counts
things, plots them over time, and makes every number clickable back to the
line of transcript that produced it. The interpretation is the clinician's
job and the tool never pretends otherwise.

---

## 2. Hard constraints

| Constraint | Consequence |
|---|---|
| Transcripts are German | No English lexicon survives translation unexamined; German-specific markers become the core, not an afterthought |
| User is non-technical | No terminal, no install, no config file. Open a URL, drop a file. |
| Data is `§ 203 StGB` material | Nothing leaves the browser. No server, no upload, no logs, no analytics, no CDN that sees a filename. |
| Hosted from a personal GitHub Pages site | Static files only. All computation client-side. |
| Transcript format unknown | Ingest must be tolerant and must report honestly what it found rather than silently guessing |

### The privacy architecture, stated plainly

The page is static. When a file is dropped on it, the browser reads it into
memory and Pyodide analyses it there. No `fetch`, no `XMLHttpRequest`, no form
POST carries transcript content. The only network traffic is the initial load
of Pyodide's own WASM runtime from a pinned CDN — and that can be vendored
into the repo to eliminate even that.

This is not a policy promise, it is an architectural fact, and it should be
verifiable by the user: **the README must tell him he can load the page,
disconnect from the internet, and the tool still works.** That demonstration
is worth more than any privacy statement.

Consequence worth telling his friend: this also means Thera.py cannot be
subpoenaed, breached, or quietly changed under him. The flip side is that
results live only in his browser tab until he exports them himself.

---

## 3. Architecture

```
    Browser (his laptop)
    ┌─────────────────────────────────────────────┐
    │  index.html  ─  static, from GitHub Pages   │
    │      │                                       │
    │      ├── app/main.js      file drop, views  │
    │      ├── app/charts.js    SVG, no libraries │
    │      │                                       │
    │      └── Pyodide (WASM)                      │
    │            └── therapy/   ← the real work  │
    │                                               │
    │  Transcript never leaves this box.            │
    └─────────────────────────────────────────────┘
```

**Why Pyodide and not a server:** it is the only way to satisfy "Python",
"public URL", and "no data transfer" simultaneously. The cost is losing
spaCy and transformer models — see §5.

**Why the Python is a proper package and not inline script:** so the exact
same code can be `pip install`ed and run locally over a whole corpus if the
browser ever becomes limiting, and so it can be unit-tested in CI.

### What Pyodide gives us

Verified against the current Pyodide package set:

| Package | Available | Used for |
|---|---|---|
| `numpy`, `pandas`, `scipy` | yes | everything numeric |
| `scikit-learn` | yes | topic modelling (NMF), clustering |
| `nltk`, `networkx`, `regex` | yes | collocations, sociogram graph |
| **`spacy`** | **no** | — |

`simplemma` and `HanTa` are pure-Python German lemmatiser/taggers installable
in-browser via `micropip`; they replace spaCy for lemmatisation and coarse POS.
Compound splitting via `CharSplit`, also pure Python.

**What we give up:** dependency parsing, NER, and transformer sentiment.
Assessment: acceptable. The markers that matter most here are morphological
and lexical, and a transformer sentiment score is the number a clinician
should trust least anyway. NER for the sociogram is replaced by a
capitalisation-plus-gazetteer heuristic with a manual confirmation step — which
is better, because the therapist knows who the names are and the machine
doesn't.

---

## 4. Repository layout

```
therapy/
├── index.html                 GitHub Pages entry point
├── app/
│   ├── main.js                Pyodide bootstrap, file handling, routing
│   ├── views.js               session / trends / keywords / concordance
│   ├── charts.js              hand-rolled SVG — no chart library
│   └── styles.css             German UI, light + dark
├── pysrc/therapy/
│   ├── __init__.py
│   ├── ingest.py              format detection, parsing, speaker assignment
│   ├── pseudonym.py           name → stable token, at ingest, before anything
│   ├── tokenize.py            German tokenisation, sentence splitting
│   ├── markers.py             the German marker set (§5.1)
│   ├── dialogue.py            turn-level metrics (§5.2)
│   ├── lexical.py             KWIC, collocations, keyness, TTR (§5.3)
│   ├── threads.py             dropped-thread detection (§5.4)
│   ├── people.py              sociogram (§5.5)
│   ├── arc.py                 cross-session series + changepoints (§5.6)
│   ├── report.py              assembles the JSON the UI renders
│   └── lexika/
│       ├── marker.py          ✅ written
│       ├── emotion.py         ✅ written
│       ├── funktion.py        stopwords, pronouns, function words
│       └── dialogmuster.py     question types and backchannels
├── samples/                   synthetic English transcripts (no real data, ever)
├── tests/                     hand-checked German sentences per marker
├── pyproject.toml             so the same package installs locally
└── README.md                  for him, in German
```

**Rule, enforced in review:** `samples/` contains only synthetic transcripts.
No real client material is ever committed, not even de-identified, not even
in a branch.

---

## 5. The metric catalogue

Confidence column is deliberate. It is an honest statement of how much weight
each number can bear, and it should be visible in the UI, not just here.

- **A** — well-grounded in the literature, robustly computable
- **B** — sound reasoning, heuristic implementation, directionally useful
- **C** — exploratory; interesting to look at, not to conclude from

### 5.1 German markers — client side

These are the heart of it, and the reason a German tool beats a translated one.

| Marker | What it catches | Conf. |
|---|---|---|
| **`man` vs `ich` ratio** | The German grammatical escape hatch out of first-person experience. *Man fühlt sich dann halt schlecht* instead of *ich fühle mich schlecht*. Probably the single best distancing measure available in the language, and it has no English equivalent. | A |
| **Case of self-reference** (`ich` nominative vs `mir`/`mich` oblique) | Agency proxy without a parser. *Ich habe ihm gesagt* vs *mir ist das passiert*. Subject-position self vs experiencer-position self. | B |
| **Konjunktiv II density** | Counterfactual and irrealis thinking. Cleanly detectable by umlaut morphology (`hätte`, `wäre`, `könnte`), with ambiguous forms (`sollte`, `wollte`) counted separately. | A |
| **Regret constructions** | *hätte ich nur*, *wenn ich doch*, *ich hätte … sollen*. Pattern-matched. The highest-value individual hits in the whole tool. | A |
| **Modal particle profile** | *halt, eben, doch, ja, einfach, nur*. German carries in these the pragmatic weight English puts in tone of voice. *Das ist halt so* is resignation in three words. Grouped into resignative / insistent / minimising / hedging. | B |
| **Absolutist density** | Adapted from Al-Mosaiwi & Johnstone, tiered to keep colloquial intensifiers (*total*, *voll*, *ganz*) out of the count. Exclusions documented in the lexicon file. | B |
| **Emotional granularity** | Not valence — *differentiation*. Distinct emotion lemmas used, and differentiated vs vague affect words. The move from *schlecht/komisch* to *gekränkt/wehmütig/erleichtert* is the therapeutic goal itself. | A |
| **Body-located affect** | Some clients speak consistently in the body rather than the feeling. Own category, own trajectory. | B |
| **Tense / temporal orientation** | Perfekt (spoken past), Präsens, Futur, plus temporal adverbs. Rumination lives in the past, anxiety in the future. | B |
| **Causal + insight words** | *weil, deshalb, Zusammenhang* / *verstehe, gemerkt, klar geworden*. Increase over therapy is one of the better-replicated language findings. | A |
| **Hedging and vagueness** | *irgendwie, eigentlich, keine Ahnung, so eine Art*. Rises under threat, near ruptures, and around avoided material. | B |
| **Negation density** | Defining the self by what it is not. | B |
| **Passive constructions** | *wurde … gemacht*. Things done to the self. | B |
| **Metaphor candidates** | Motion / container / space / burden / weather / combat vocabulary applied to mental states. Tracks whether a metaphor persists, mutates, or disappears. Therapists live off these images. | C |

### 5.2 Dialogue dynamics

| Marker | What it catches | Conf. |
|---|---|---|
| **Talk ratio** | Therapist's share of words, per session and across the arc. Does it decline as therapy progresses? With everyone equally? | A |
| **Turn length distribution** | Long therapist turns followed by short client turns is a recognisable pattern with a recognisable meaning. | A |
| **Question typing** | Open (W-question, invitation) vs closed (verb-first, tag). Everyone believes they ask open questions. | B |
| **Lexical uptake** | Does the therapist use the client's own words back, or translate into his own vocabulary? Good therapy borrows. Content-word overlap, turn to turn. | B |
| **Style matching (LSM)** | Function-word convergence across turns. Plotted within a session, dips mark candidate ruptures. | B |

### 5.3 Corpus tools — the bridge back to close reading

Non-negotiable: every aggregate number in the UI is clickable and opens the
lines that produced it. Without this, Thera.py becomes a dashboard he watches
instead of a person he listens to — which is the real clinical risk here.

- **KWIC concordance.** Every occurrence of a word in context, across all
  sessions, with session and turn reference.
- **Collocations.** What clusters around *Mutter*, around *Arbeit*, around
  *Angst*. Log-likelihood, not raw frequency.
- **Keyness, on three axes.** What makes language distinctive rather than
  merely frequent. The reference used to be the rest of the caseload, which
  left anyone with a single case looking at an empty list; two of the three
  axes now compare a text with itself.
  - *This session against the others* — what was talked about that day and not
    otherwise. Clinically the most interesting of the three.
  - *Late sessions against early ones* — the vocabulary of change.
  - *This client against the rest of the caseload*, where there is one, and
    only against clients seen in the same language.
  Each entry carries G² **and** log ratio: the first says how confident the
  difference is and grows with the amount of text, the second says how large it
  is. One without the other is misleading over a year of transcript.
- **A word across the sessions.** Any word, plotted as a rate per 1000 words
  against the session axis, clickable into the session it came from.
- **Vocabulary that moves.** Rising and fading by rank correlation against
  session order; appearing and disappearing by first and last occurrence.
- **Compound decomposition.** *Verlustangst*, *Schuldgefühle*, *Versagensangst*
  each appear once and vanish into the tail unless split. This is exactly where
  the emotionally loaded vocabulary hides.
- **Type-token ratio**, standardised, both speakers.

### 5.4 Dropped threads

The feature I'd build first if I could only build one.

Find moments where the client said something emotionally loaded and the thread
then died. Heuristic: a client turn with above-median length and high affect
density, followed by a therapist turn with near-zero lexical uptake and a topic
shift, followed by a client turn that does not return to the original content
words.

Presented as a list of moments to review, with the transcript excerpt — framed
as *doors that were open*, not as errors. The framing matters; get it wrong and
the tool becomes an accusation.

### 5.5 Who is in the room

Frequency of named people and relationship terms across sessions, weighted by
the affect vocabulary in their immediate context. Rendered as a graph: who
enters the narrative, who fades, who is spoken about with what temperature.

Names come from a heuristic pass that the therapist confirms once per client —
he knows who these people are and the machine doesn't. Confirmation also feeds
the pseudonymiser.

### 5.6 The arc

All of the above as time series across sessions, plus Bayesian changepoint
detection on composite indices. The output the therapist actually wants is not
twelve line charts but one sentence: *something shifted around session 9.* Then
he goes and finds out why.

### 5.7 The mirror — cut

*Removed.* The therapist-side view was built around comparisons across the
caseload — *you interpret three times more with A than with B* — and the
intervention classifier and idiolect detector existed only to serve it. All
three need at least two clients, and the input this tool is actually used with
is one long text: one case, no comparison, an empty panel.

What is lost is real: the comparative question was the sharpest thing here, and
it is gone with it. What survives is the therapist-side measurement that works
within a single case — talk ratio, lexical uptake, style matching and question
typing, in the session card and as the therapist series in Trends. The
classifier and its two lexicons are in the git history if a multi-client view
ever comes back.

---

## 6. The views

**What was read** — what was found per file, how the text was split into
sessions, and which figures are unavailable as a result. First on purpose.

**Session** — one page per session. Affect arc, talk ratio, question profile,
new vocabulary, candidate ruptures, dropped threads.

**Trends** — the year at once. Every marker as a trajectory, changepoints
marked, the sociogram, metaphors as they appear and mutate.

**Keywords** — which words carry the case: the three keyness axes, a word
plotted across the sessions, vocabulary that rises and fades, compounds split
open.

Plus **Concordance**, reachable from any number anywhere. Keywords answers
*which words*; the concordance shows *the lines*.

UI language: English. Every panel carries a plain note on what the number can
and cannot bear.

---

## 7. Build phases

### Phase 0 — Foundations
- [x] Repo scaffold, package layout
- [x] `lexika/marker.py` — absolutist tiers, particles, Konjunktiv II, hedges, causal/insight, temporal
- [x] `lexika/emotion.py` — emotion families, vague affect, body affect, metaphor candidates
- [ ] `lexika/funktion.py` — stopwords, pronoun paradigms, function words for LSM
- [ ] `tokenize.py` — German tokenisation and sentence splitting
- [ ] Synthetic German sample transcripts across ~12 sessions
- [ ] Test harness with hand-checked German sentences per marker

### Phase 1 — Ingest
- [ ] Format detection: `.txt`, `.vtt`, `.srt`, Whisper `.json`, `.csv`, `.docx`
- [ ] Speaker-label detection; guided assignment pass when labels are absent
- [ ] Honest capability report: *labels found / no labels → these metrics unavailable*
- [ ] Pseudonymisation before any analysis touches the text

### Phase 2 — Analysis core
- [ ] `markers.py`, `dialogue.py`, `lexical.py`
- [ ] `threads.py`, `people.py`, `arc.py`
- [ ] `report.py` → single JSON contract for the UI

### Phase 3 — Browser
- [ ] Pyodide bootstrap with a real loading state (first load is slow; say so)
- [ ] Paste box and file drop; session splitting and ordering
- [ ] Session, trends, keywords, concordance
- [ ] Hand-rolled SVG charts
- [ ] Offline demonstration path using `samples/`

### Phase 4 — Gift polish
- [ ] German README written for him, not for developers
- [ ] The disconnect-your-wifi demonstration, documented up front
- [ ] Export: his own results to a local file, on demand only
- [ ] Vendor Pyodide into the repo so the page makes zero network calls

**Minimum giftable version:** Phase 0 + 1 + the German markers + concordance +
trends + dropped threads. A therapist-side view across several clients is the
natural v2 — the intervention classifier it would need wants labelled German
therapy utterances, and that is real work that shouldn't be faked (see §5.7).

---

## 8. What I need from you

1. **The birthday date.** Decides how much of §7 is realistic.
2. **Any de-identified transcript**, even one, even heavily redacted — to tune
   the ingest heuristics against. Failing that I build against synthetic German
   and the format detection will need a round of fixing on his real files.
3. **Which single feature is the centrepiece** — my vote is dropped threads,
   second the sociogram.

---

## 9. Validity and ethics, stated in the tool itself

These belong in the UI, not in a document nobody reads:

- **One session is noise.** Most markers mean nothing below roughly ten sessions.
- **A transcript is not a session.** Tone, pause, body, and silence are gone.
  Thera.py reads the shadow of the hour, not the hour.
- **ASR errors are not random.** They fall hardest on exactly the low-frequency
  emotional vocabulary the granularity measure most wants to count.
- **The lexicons are adapted, not validated.** The absolutist list in particular
  is an English instrument with German clothes on. Exclusions are documented in
  the source.
- **Consent.** His clients consented to recording. They almost certainly did not
  consent to computational analysis. That is his call to make, but he should
  make it deliberately rather than by default — and it is worth him raising with
  his professional body.
- **The tool has no opinion.** It counts. The clinician interprets.

---

## 10. Deployment

GitHub Pages from `/` on `main`. The repo *is* the site. A link from your own
page points at `yoursite.com/thera.py` or the Pages subdomain.

No build step, no bundler, no npm. Editing a `.py` file and pushing updates the
live tool. That property is worth protecting — it means this thing is still
maintainable in three years when neither of us remembers how it works.

*Name note: “Thera.py” is the display name. Python packages cannot contain a
dot, so the importable package is `therapy` and the distribution is `thera-py`.
Check both on PyPI before publishing there; nothing else depends on the choice.*
