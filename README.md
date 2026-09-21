# Thera-py

**A distant reading of therapy session transcriptions.**

Thera-py counts the things in a transcript of therapy sessions that are too small to hear one at a time, plots them
across the whole course, and makes every number clickable back to the lines that
produced it.

Sessions are German or English, mixed freely in one caseload.

_This started as a conversation with a friend about whether distant reading —
the corpus methods literary scholars use on a few hundred novels — has anything
to say about a year of therapy transcripts. This is that question, made
runnable._

---

## Nothing leaves your machine

Open the page, wait for the version number, **switch off your Wi-Fi**, then drop
your transcripts on it. Everything still works. An application that sent data
anywhere could not do that.

The analysis is a Python runtime executing _inside_ your browser tab. There is
no code in this repository that transmits transcript content — no `fetch` of
anything but its own files, no storage, no cookies, no analytics — and a
Content-Security-Policy in `index.html` blocks it at the browser level as a
second line of defence.

**The flip side:** results live only in that tab. Reload and you start over.
Anything you want to keep, you export yourself. In exchange, Thera-py cannot be
subpoenaed, breached, or quietly changed under you.

**The export** writes a JSON file to your machine. It never contains transcript
lines, filenames or the case name. Names you confirmed are gone too — they
became "Person A" before anything was counted. It does contain single words
taken from the text (keyword and emotion-vocabulary lists), so a name you
declined to confirm was never replaced and can appear there.
`tests/test_export_datenschutz.py` holds that as a test.

That is the default. If you switch name replacement off — because the data
protection is already settled outside this tool — real names stay in the text
and can reach those word lists. The export says which mode produced it, in its
own `export.hinweis` field.

---

## Getting transcripts in

**Paste everything into the box** — a year in one document, sessions in order.
Mark where each starts with a line of its own; any of these works, and the
number and date are read out of it:

```
--- Session 7 — 2024-03-14 ---
### Sitzung 7
2024-03-14
```

Without any such line, a long text is cut into equal _Segments_ instead — never
called sessions, and the report says the trend runs _within_ the text.

**Or drop files**, one per session: `.txt` `.md` `.vtt` `.srt` `.json` (Whisper)
`.csv` `.tsv` `.docx` `.html`. Anything marking who speaks works best —
`Therapeut:`, `Client:`, `T:`, `Sprecher 1:`, `SPEAKER_00`, or the speaker on
its own line, as Word and HTML exports set it.

Put session number, date and client in the filename and everything sorts and
groups itself: `client-jane_session-07_2024-03-14.txt`. Language is detected per
file; `_de` or `_en` in the name overrides it, and a dropdown in _What was read_
corrects it in one click.

### From a documentation assistant (VIA and its like)

Word and HTML drop straight on; for PDF, copy the text and paste it. Three
things to know:

- **Export the transcript, not the generated notes.** Notes have no turns and no
  speakers, so everything on the dialogue side goes dark.
- **Check who is who.** `Sprecher 1`/`Sprecher 2` means the voices were
  separated without knowing which is which. Thera-py guesses — whoever talks
  less is the therapist — and says so. There is a _swap_ button next to the
  guess. It is the single judgement everything about _you_ rests on.
- **Save the same day.** These assistants delete session data within the day by
  design. A year only exists if you exported each hour as it happened.

---

## The five views

|                   |                                                                                                                                                                                             |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **What was read** | What each file contained, in which language, how it was split, and which figures are therefore _unavailable_. Look at this first.                                                           |
| **Session**       | One page per hour: language markers, affect through the session, talk ratio, question types, new vocabulary, dropped threads.                                                               |
| **Trends**        | The year at once — every marker as a trajectory, changepoints marked, who enters and leaves the narrative.                                                                                  |
| **Keywords**      | What is distinctive about one session, what separates late sessions from early ones, which vocabulary is rising or fading, compounds split open, any word you name plotted across the year. |
| **Concordance**   | The way back. Every number in the tool opens the lines that produced it — without that, this would be a dashboard you watch instead of a person you listen to.                              |

No diagnoses, no scores, no severity ratings, no "insights" written in
sentences. It counts things and shows you where each number came from. The
interpretation is your work and stays your work.

---

## What you need to know about the numbers

Every figure carries a confidence grade in the interface:

|       |                                                                  |
| ----- | ---------------------------------------------------------------- |
| **A** | well grounded, robustly computable                               |
| **B** | sound reasoning, heuristic implementation, useful as a trajectory |
| **C** | exploratory. Interesting to look at, not to conclude from.       |

The same marker can carry different grades in the two languages, and where it
does, the panel says why. German `man` is grade A because it is a dedicated
pronoun that cannot be anything else; the English equivalent, generic _you_, is
grade B because the same word is usually how the therapist is addressed.

And, without softening:

- **One session is noise.** Below roughly ten sessions most markers mean
  nothing.
- **A transcript is not a session.** Tone, pause, body and silence are gone.
  Thera-py reads the shadow of the hour, not the hour.
- **Speech-recognition errors are not random.** They fall hardest on exactly
  the low-frequency emotional vocabulary the granularity measure most wants to
  count.
- **The lexicons are adapted, not validated.** Which direction the adaptation
  runs differs per marker, and it is not always the German side that is
  borrowing: the absolutist list is an English instrument in German clothes,
  while style matching and the causal/insight lists are English originals that
  the German side had to translate. Colloquial intensifiers are deliberately
  _excluded_ — "total", "voll", "ganz" on the German side, "totally",
  "completely", "literally" on the English one — because they mark emphasis
  rather than absolutist thinking. Both lists are `ABSOLUT_AUSGESCHLOSSEN` in
  `pysrc/therapy/lexika/marker.py` and `pysrc/therapy/lexika_en/marker.py`.
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

|                     | German                                      | English                                                  |
| ------------------- | ------------------------------------------- | -------------------------------------------------------- |
| Distancing from "I" | `man` (grade A)                             | generic _you_, _one_, _people_ (grade B)                  |
| Counterfactual      | Konjunktiv II, unambiguous umlaut forms (A) | _would have_, _if I were_, _I wish_ (B)                   |
| Attitude marking    | modal particles: _halt_, _eben_, _doch_, _nur_ | downtoners: _anyway_, _really_, _just_, _I suppose_    |
| Obligation          | _muss_, _soll_, _darf nicht_                | _have to_, _supposed to_, _gotta_, _should_               |
| Passive             | _werden_ + participle                       | _be_/_get_ + participle, minus predicative adjectives     |
| Past                | mostly perfect in speech                    | perfect and simple past, counted separately               |

Two things exist on one side only, and they are simply absent on the other
rather than faked:

- **Compound splitting** is German-only. "Verlustangst" has to be prised open
  or it vanishes into the tail; English writes its compounds open ("fear of
  loss"), so they arrive already split and the Keywords view drops the block.
- **Honorific forms** (`Sie`/`Ihnen`) are German-only. English has no
  T–V distinction, so the tile does not appear rather than showing a zero.

Two places where English is the better-off side, said plainly because the rest
of this section runs the other way: **name detection** is more reliable, because
a capitalised word mid-sentence is a proper-name signal in English and merely a
noun signal in German; and **style matching** is at home, having been developed
on English function words, so the German figure is the adapted one.

If a client's sessions are not all in the same language, markers that exist in
only one of them are left out of the charts entirely rather than padded with
zeros, and a spliced "across languages" series is drawn for the constructs that
have a counterpart on both sides — to be read for its shape within each stretch,
not for the step between them.

---

## Names

Before anything is analysed, Thera-py finds likely personal names and puts them
in front of you once. What you confirm becomes a stable placeholder — "Person A"
is the same person across all twelve sessions, otherwise the sociogram would be
worthless. The mapping stays in the tab, is never stored, and is not exported.

It is a heuristic with a confirmation step rather than named-entity recognition
on purpose: you know who these people are, the machine does not.

**Replacing them is a choice, not a law.** The checkbox above the drop panel —
_Replace names with placeholders_ — is ticked by default and can be switched
off before you load anything, for the case where consent and data protection are
already settled outside this tool, or the transcripts arrive de-identified
anyway. Switched off, the names stay exactly as they were spoken: in the
concordance, in the word lists, in the sociogram and in anything you export.

The confirmation step stays either way, because it is the step that decides
_who is a person_. That is what the sociogram is built from; without it "Mark"
is just a word that happens to be capitalised. Confirming a name with
replacement off therefore changes nothing in the text and everything in the
social map.

The choice is read when you load the transcripts, and it is not remembered
between visits — nothing about you is. On the command line it is
`--keine-pseudonyme`, which now keeps the real names rather than skipping
detection.

---

_"Thera-py" is the name everywhere it is read: the repository, the page, the
command, the distribution. Python import names cannot contain a hyphen, so the
importable package alone stays `therapy` — `import therapy`._

This all has been build with the assistance of Claude Opus 5.
