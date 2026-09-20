/* Thera.py — bootstrap, files, routing.
 *
 * What does NOT happen in this file is the whole point of it:
 * there is no fetch(), no XMLHttpRequest, no sendBeacon and no form that
 * carries transcript content anywhere. Files are read with FileReader, handed
 * to Pyodide, and stay in this tab's memory. The only network calls the whole
 * application makes are:
 *
 *   – loading its own static files (HTML, JS, CSS, .py)
 *   – loading the Pyodide runtime
 *   – loading the synthetic samples from samples/, and only on a click
 *
 * All three fetch files; none of them ever sends one. If Pyodide is vendored
 * into vendor/pyodide/, the second one disappears too and the page needs no
 * foreign server at all.
 *
 * The interface is English. The material is German or English, decided per
 * session; everything quoted back out of a transcript stays in the language it
 * was spoken in, because translating an example would destroy the marker it
 * illustrates. Which markers exist, what they are called and what caveat they
 * carry all come from the report, keyed by that language — this file never
 * names a marker.
 */

import * as V from './views.js';
import * as C from './charts.js';

const PYODIDE_VERSION = 'v0.26.4';
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/${PYODIDE_VERSION}/full/`;
const PYODIDE_LOKAL = 'vendor/pyodide/';

/* Order matters only in that every file must exist before the package is
 * imported; Python resolves the rest itself. Both language packs are written
 * into the runtime, but `sprachen.paket()` imports one only when a session in
 * that language actually turns up. */
const PY_DATEIEN = [
  'therapy/__init__.py',
  'therapy/tokenize.py',
  'therapy/ingest.py',
  'therapy/pseudonym.py',
  'therapy/markers.py',
  'therapy/dialogue.py',
  'therapy/lexical.py',
  'therapy/threads.py',
  'therapy/people.py',
  'therapy/arc.py',
  'therapy/report.py',
  'therapy/lexika/__init__.py',
  'therapy/lexika/marker.py',
  'therapy/lexika/emotion.py',
  'therapy/lexika/funktion.py',
  'therapy/lexika/dialogmuster.py',
  'therapy/lexika_en/__init__.py',
  'therapy/lexika_en/marker.py',
  'therapy/lexika_en/emotion.py',
  'therapy/lexika_en/funktion.py',
  'therapy/lexika_en/dialogmuster.py',
  'therapy/sprachen/__init__.py',
  'therapy/sprachen/de.py',
  'therapy/sprachen/en.py',
];

const App = {
  py: null,
  ot: null,
  bericht: null,
  befunde: [],
  ansicht: 'befund',
  klientId: null,
  sitzungIdx: 0,
  // Das zuletzt geplottete Wort, damit die Kurve einen Ansichtswechsel
  // übersteht. Der Bericht trägt sie nicht mit: er wäre sonst um den ganzen
  // Wortschatz grösser, für eine Kurve, die man meistens nicht anschaut.
  wort: null,
  bereit: false,
};

const $ = (s, wurzel = document) => wurzel.querySelector(s);
const $$ = (s, wurzel = document) => [...wurzel.querySelectorAll(s)];

/* ------------------------------------------------------------------ */
/* Loading state                                                       */
/* ------------------------------------------------------------------ */

function status(text, fortschritt) {
  const box = $('#ladezustand');
  box.hidden = false;
  $('#lade-text').textContent = text;
  const balken = $('#lade-balken');
  if (fortschritt === undefined) {
    balken.removeAttribute('value');
  } else {
    balken.value = fortschritt;
  }
}

function statusFertig() {
  $('#ladezustand').hidden = true;
}

async function existiert(url) {
  try {
    const antwort = await fetch(url, { method: 'HEAD' });
    return antwort.ok;
  } catch {
    return false;
  }
}

async function ladePyodide() {
  // The first start is slow (~10 MB of WebAssembly). Saying so plainly beats a
  // spinner that pretends things are about to happen.
  const lokal = await existiert(PYODIDE_LOKAL + 'pyodide.js');
  const basis = lokal ? PYODIDE_LOKAL : PYODIDE_CDN;
  status(lokal
    ? 'Loading the Python runtime (from this repository — no foreign server) …'
    : 'Loading the Python runtime — the first time this takes 10 to 30 seconds. '
      + 'After that it sits in your browser cache and the page starts instantly, '
      + 'with or without a network connection.');

  await new Promise((fertig, fehler) => {
    const skript = document.createElement('script');
    skript.src = basis + 'pyodide.js';
    skript.onload = fertig;
    skript.onerror = () => fehler(new Error('Pyodide could not be loaded.'));
    document.head.appendChild(skript);
  });

  App.py = await globalThis.loadPyodide({ indexURL: basis });

  status('Writing Thera.py into the runtime …', 0.7);
  App.py.FS.mkdirTree('/pkg/therapy/lexika');
  App.py.FS.mkdirTree('/pkg/therapy/lexika_en');
  App.py.FS.mkdirTree('/pkg/therapy/sprachen');
  let geladen = 0;
  for (const pfad of PY_DATEIEN) {
    const antwort = await fetch('pysrc/' + pfad);
    if (!antwort.ok) throw new Error(`Missing file: pysrc/${pfad}`);
    App.py.FS.writeFile('/pkg/' + pfad, await antwort.text(), { encoding: 'utf8' });
    geladen += 1;
    status('Writing Thera.py into the runtime …', 0.7 + 0.25 * (geladen / PY_DATEIEN.length));
  }
  App.py.runPython("import sys; sys.path.insert(0, '/pkg')");
  App.ot = App.py.pyimport('therapy');
  App.bereit = true;
  statusFertig();
  $('#version').textContent = 'v' + App.ot.VERSION;
}

/* Lässt den Browser einmal zeichnen, bevor der Hauptthread blockiert wird.
 * Ein Timer und kein requestAnimationFrame: in einem Hintergrundtab feuert rAF
 * nicht, und die Auswertung stünde dann still, bis jemand hinschaut. */
function atemzug() {
  return new Promise((fertig) => setTimeout(fertig, 0));
}

/* The bridge: every Python function returns a JSON string. */
function py(name, ...args) {
  return JSON.parse(App.ot[name](...args));
}

/* ------------------------------------------------------------------ */
/* Files                                                               */
/* ------------------------------------------------------------------ */

function liesDatei(datei) {
  return new Promise((fertig, fehler) => {
    const leser = new FileReader();
    leser.onerror = () => fehler(leser.error);
    leser.onload = () => fertig({ name: datei.name, inhalt: leser.result });
    // .docx is a ZIP and has to be read as bytes; it is passed through as a
    // latin-1 string so the Python side gets the bytes back unchanged.
    if (datei.name.toLowerCase().endsWith('.docx')) {
      leser.readAsBinaryString(datei);
    } else {
      leser.readAsText(datei, 'utf-8');
    }
  });
}

async function verarbeite(dateien) {
  if (!App.bereit) {
    alert('The Python runtime is still loading. One moment.');
    return;
  }
  status(`Reading ${dateien.length} file(s) …`);
  const inhalte = [];
  for (const datei of dateien) inhalte.push(await liesDatei(datei));

  App.befunde = py('lade', JSON.stringify(inhalte));
  status('Looking for names …');
  const kandidaten = py('namensvorschlaege');
  statusFertig();

  zeigeBefund();
  if (kandidaten.length) {
    zeigeNamensdialog(kandidaten);
  } else {
    await analysiere([]);
  }
}

/* Eingefügter Text geht denselben Weg wie eine Datei — er *ist* eine Datei,
 * nur ohne Dateisystem. Zwei Pfade nebeneinander wären zwei Pfade, die
 * auseinanderlaufen. Der Dateiname ist frei erfunden und dient nur dazu, dass
 * der Befund eine Zeile bekommt, die man lesen kann. */
async function verarbeiteEingefuegtes() {
  const feld = $('#einfuegen');
  const text = feld.value.trim();
  if (!text) {
    feld.focus();
    return;
  }
  await verarbeite([new File([text], 'pasted-text.txt', { type: 'text/plain' })]);
}

async function analysiere(bestaetigte) {
  status('Replacing names …');
  py('pseudonymisiere', JSON.stringify(bestaetigte));
  status('Analysing — a year of transcripts takes a moment …');
  // Breathing room so the loading state is actually painted before Pyodide
  // blocks the main thread for a few seconds. Deliberately a timer and not
  // requestAnimationFrame: rAF does not fire in a hidden tab, so switching
  // away right after confirming the names stalled the analysis until you
  // came back and looked at it.
  await atemzug();
  App.bericht = py('bericht');
  statusFertig();

  App.klientId = App.bericht.klienten[0]?.id ?? null;
  App.sitzungIdx = 0;
  $('#leer-zustand').hidden = true;
  $('#kopfleiste').hidden = false;
  bauKlientenwahl();
  geheZu('sitzung');
}

/* ------------------------------------------------------------------ */
/* Name confirmation                                                   */
/* ------------------------------------------------------------------ */

function zeigeNamensdialog(kandidaten) {
  const dialog = $('#namensdialog');
  $('#namensliste').innerHTML = kandidaten.map((k) => `
    <li>
      <label>
        <input type="checkbox" data-name="${C.esc(k.name)}" ${k.sicherheit >= 0.8 ? 'checked' : ''}>
        <span class="name">${C.esc(k.name)}</span>
        <span class="name-meta">${C.esc(k.haeufigkeit)}× · ${C.esc(k.grund)}
          ${k.beziehung ? `· near “${C.esc(k.beziehung)}”` : ''}</span>
      </label>
      ${k.belege.length ? `<p class="name-beleg">${C.esc(k.belege[0])}</p>` : ''}
    </li>`).join('');
  dialog.showModal();
}

/* ------------------------------------------------------------------ */
/* Navigation                                                          */
/* ------------------------------------------------------------------ */

function bauKlientenwahl() {
  const wahl = $('#klientenwahl');
  wahl.innerHTML = App.bericht.klienten.map((k) =>
    `<option value="${C.esc(k.id)}">${C.esc(k.id)} (${k.sitzungen.length})</option>`).join('');
  wahl.value = App.klientId;
  wahl.hidden = App.bericht.klienten.length < 2;
  bauSitzungswahl();
}

function bauSitzungswahl() {
  const klient = aktiverKlient();
  if (!klient) return;
  $('#sitzungswahl').innerHTML = klient.sitzungen.map((s, i) =>
    `<option value="${i}">${C.esc(s.titel)}</option>`).join('');
  $('#sitzungswahl').value = String(App.sitzungIdx);
}

function aktiverKlient() {
  return App.bericht?.klienten.find((k) => k.id === App.klientId) ?? null;
}

function geheZu(ansicht) {
  App.ansicht = ansicht;
  $$('.nav-knopf').forEach((b) => b.setAttribute('aria-current', String(b.dataset.ansicht === ansicht)));
  $('#sitzungswahl').hidden = ansicht !== 'sitzung';
  zeichne();
}

function zeichne() {
  const ziel = $('#ansicht');
  const klient = aktiverKlient();
  if (!App.bericht) return;

  if (App.ansicht === 'befund') {
    ziel.innerHTML = V.befundAnsicht(App.befunde, App.bericht.hinweise?.sprache,
      App.bericht.klienten)
      + V.geltung(App.bericht.hinweise?.geltung ?? []);
  } else if (App.ansicht === 'sitzung' && klient) {
    const sitzung = klient.sitzungen[App.sitzungIdx];
    ziel.innerHTML = V.sitzungskarte(klient, sitzung, App.bericht.beschriftung,
      App.bericht.hinweise, klient.arc.serien);
  } else if (App.ansicht === 'bogen' && klient) {
    ziel.innerHTML = V.bogen(klient, App.bericht.beschriftung, App.bericht.hinweise);
  } else if (App.ansicht === 'woerter' && klient) {
    ziel.innerHTML = V.woerter(klient, App.bericht.hinweise);
    $('#wort-form')?.addEventListener('submit', (ev) => {
      ev.preventDefault();
      zeichneWortverlauf($('#wort-eingabe').value);
    });
    if (App.wort) zeichneWortverlauf(App.wort, { behalten: true });
  } else if (App.ansicht === 'konkordanz') {
    ziel.innerHTML = konkordanzAnsicht();
    $('#kwic-eingabe')?.focus();
  }
  ziel.scrollTop = 0;
}

/* The ingest report goes up before the analysis — that is the entire point of
 * it. Whoever sees curves first and only then learns that the speakers were
 * guessed has already believed the curves. */
function zeigeBefund() {
  $('#leer-zustand').hidden = true;
  $('#ansicht').innerHTML = V.befundAnsicht(App.befunde);
}

/* The language select in the ingest report. Detection is a heuristic, so it
 * needs a one-click correction rather than a paragraph of hedging — the same
 * reasoning as the speaker swap. Changing it re-runs the whole analysis,
 * because every word list downstream depends on it. */
/* Der Fallname ist Beschriftung, keine Messung — deshalb wird nach dem
 * Umbenennen zwar neu gerechnet (die Gruppierung hängt daran), aber nichts
 * gefragt und nichts gewarnt. */
async function benenneKlient(alt, neu) {
  if (!neu.trim() || neu.trim() === alt) return;
  py('klient_umbenennen', alt, neu);
  status('Renaming …');
  await atemzug();
  App.bericht = py('bericht');
  statusFertig();
  if (App.klientId === alt) App.klientId = neu.trim().slice(0, 40);
  bauKlientenwahl();
  zeichne();
}

async function setzeSprache(sid, code) {
  py('sprache_setzen', sid, code);
  App.befunde = py('befunde');
  if (App.bericht) {
    status('Re-analysing in the chosen language …');
    await atemzug();
    App.bericht = py('bericht');
    statusFertig();
    bauKlientenwahl();
  }
  zeichne();
}

function konkordanzAnsicht() {
  // The placeholder follows the client on screen: whoever is looking at an
  // English case is about to type an English word, and a German example there
  // would just be noise.
  const sprache = aktiverKlient()?.sprache ?? App.bericht?.sprachen?.codes?.[0] ?? 'de';
  const beispiel = sprache === 'en'
    ? 'An English word or phrase, e.g. ashamed or “I don’t know”'
    : 'A German word or phrase, e.g. Angst or “keine Ahnung”';
  return `
  <header class="ansicht-kopf">
    <h2>Concordance</h2>
    <p class="unter">Every number in this tool leads back here.
      ${App.bericht?.sprachen?.gemischt
        ? 'Your corpus holds both languages — a search runs over the selected client only.'
        : ''}</p>
  </header>
  <form id="kwic-form" class="suchzeile">
    <input id="kwic-eingabe" type="search" placeholder="${C.esc(beispiel)}"
           autocomplete="off" spellcheck="false">
    <select id="kwic-sprecher">
      <option value="">both speakers</option>
      <option value="K">client only</option>
      <option value="T">therapist only</option>
    </select>
    <button type="submit">Search</button>
  </form>
  <div id="kwic-ergebnis"></div>
  <div id="kollokationen"></div>`;
}

/* ------------------------------------------------------------------ */
/* Evidence drawer                                                     */
/* ------------------------------------------------------------------ */

function oeffneSchublade(titel, inhalt) {
  $('#schublade-titel').textContent = titel;
  $('#schublade-inhalt').innerHTML = inhalt;
  $('#schublade').hidden = false;
  $('#schublade').scrollTop = 0;
}

function schliesseSchublade() {
  $('#schublade').hidden = true;
}

function zeigeBelege(marker, sprecher, klientId, titel, hinweis) {
  const klient = klientId || App.klientId;
  // On the session card, restrict the evidence to the session on screen. In
  // every other view, show it across the whole case.
  const sid = App.ansicht === 'sitzung'
    ? aktiverKlient()?.sitzungen[App.sitzungIdx]?.sid ?? ''
    : '';
  const zeilen = py('belege', klient, marker, sprecher, sid);
  const name = titel || marker;
  oeffneSchublade(name,
    (hinweis ? `<p class="block-hinweis">${C.esc(hinweis)}</p>` : '')
    + V.belegListe(zeilen, name));
}

function zeigeTurns(sid, fokus) {
  const turns = py('turns', sid, Math.max(0, fokus - 4), fokus + 6);
  oeffneSchublade(`Transcript · turn ${fokus}`, V.turnAnsicht(turns, fokus));
  const el = $(`#turn-${fokus}`, $('#schublade-inhalt'));
  el?.scrollIntoView({ block: 'center' });
}

function suche(begriff, sprecher = '') {
  geheZu('konkordanz');
  $('#kwic-eingabe').value = begriff;
  $('#kwic-sprecher').value = sprecher;
  fuehreSucheAus();
}

/* Der Wortverlauf wird bei jeder Eingabe frisch gerechnet statt im Bericht
 * mitgeliefert — siehe App.wort. Gezeichnet wird mit demselben verlauf(), das
 * die Marker benutzen, damit eine Wortkurve und eine Markerkurve dasselbe
 * bedeuten und dieselben Klicks vertragen. */
function zeichneWortverlauf(begriff, { behalten = false } = {}) {
  const wort = String(begriff ?? '').trim();
  const klient = aktiverKlient();
  const ziel = $('#wort-verlauf');
  if (!wort || !klient || !ziel) return;

  if (!behalten) App.wort = wort;
  const daten = py('wortverlauf', wort, klient.id);
  const feld = $('#wort-eingabe');
  if (feld) feld.value = wort;

  if (!daten.gesamt) {
    ziel.innerHTML = `<p class="leer">“${C.esc(wort)}” does not occur in this
      client's sessions.</p>`;
    return;
  }
  ziel.innerHTML = `
    <p class="treffer-zahl">${daten.gesamt} occurrences of “${C.esc(daten.wort)}”</p>
    ${C.verlauf(daten.werte, daten.nummern, { hoehe: 200, breite: 720, klickbar: true })}
    <p class="block-hinweis">Per 1000 words.
      <button class="wort klickbar" data-suche="${C.esc(daten.wort)}">See the lines</button></p>`;
}

function fuehreSucheAus() {
  const begriff = $('#kwic-eingabe').value.trim();
  if (!begriff) return;
  const sprecher = $('#kwic-sprecher').value;
  $('#kwic-ergebnis').innerHTML = V.kwicListe(py('kwic', begriff, App.klientId ?? '', sprecher), begriff);
  $('#kollokationen').innerHTML = V.kollokationsListe(
    py('kollokationen', begriff, App.klientId ?? '', sprecher || 'K'), begriff);
}

/* ------------------------------------------------------------------ */
/* Samples and export                                                  */
/* ------------------------------------------------------------------ */

async function ladeBeispiele() {
  status('Loading the synthetic samples …');
  const antwort = await fetch('samples/MANIFEST.json');
  const namen = await antwort.json();
  const dateien = [];
  for (const name of namen) {
    const r = await fetch('samples/' + name);
    dateien.push(new File([await r.blob()], name));
  }
  await verarbeite(dateien);
}

function exportiere() {
  const daten = py('export');
  const blob = new Blob([JSON.stringify(daten, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `therapy-analysis-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ------------------------------------------------------------------ */
/* Events                                                              */
/* ------------------------------------------------------------------ */

function verdrahte() {
  const zone = $('#ablage');
  ['dragenter', 'dragover'].forEach((e) => zone.addEventListener(e, (ev) => {
    ev.preventDefault(); zone.classList.add('aktiv');
  }));
  ['dragleave', 'drop'].forEach((e) => zone.addEventListener(e, (ev) => {
    ev.preventDefault(); zone.classList.remove('aktiv');
  }));
  zone.addEventListener('drop', (ev) => verarbeite([...ev.dataTransfer.files]));
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => e.preventDefault());

  $('#dateiwahl').addEventListener('change', (ev) => verarbeite([...ev.target.files]));
  $('#einfuegen-los').addEventListener('click', verarbeiteEingefuegtes);
  $('#beispiele').addEventListener('click', ladeBeispiele);
  $('#export').addEventListener('click', exportiere);
  $('#neu').addEventListener('click', () => {
    if (!confirm('Discard all loaded transcripts and the name mapping?')) return;
    py('leeren');
    App.bericht = null; App.befunde = [];
    $('#leer-zustand').hidden = false;
    $('#kopfleiste').hidden = true;
    $('#ansicht').innerHTML = '';
  });

  $$('.nav-knopf').forEach((b) => b.addEventListener('click', () => geheZu(b.dataset.ansicht)));
  $('#klientenwahl').addEventListener('change', (ev) => {
    App.klientId = ev.target.value; App.sitzungIdx = 0; bauSitzungswahl(); zeichne();
  });
  $('#sitzungswahl').addEventListener('change', (ev) => {
    App.sitzungIdx = Number(ev.target.value); zeichne();
  });

  document.addEventListener('change', (ev) => {
    if (ev.target.matches?.('.sprachwahl')) {
      setzeSprache(ev.target.dataset.sid, ev.target.value);
    } else if (ev.target.matches?.('.fallname-feld')) {
      benenneKlient(ev.target.dataset.klient, ev.target.value);
    }
  });

  $('#schublade-zu').addEventListener('click', schliesseSchublade);
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') schliesseSchublade();
  });

  $('#namen-uebernehmen').addEventListener('click', async () => {
    const gewaehlt = $$('#namensliste input:checked').map((i) => ({ name: i.dataset.name }));
    $('#namensdialog').close();
    await analysiere(gewaehlt);
  });
  $('#namen-ueberspringen').addEventListener('click', async () => {
    $('#namensdialog').close();
    await analysiere([]);
  });

  // One delegate for everything clickable. The views produce their HTML as
  // strings; hanging individual listeners on them would be bookkeeping with no
  // benefit.
  document.addEventListener('click', behandleKlick);
  document.addEventListener('keydown', (ev) => {
    if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.matches?.('.klickbar')) {
      ev.preventDefault();
      behandleKlick(ev);
    }
  });

  document.addEventListener('submit', (ev) => {
    if (ev.target.id === 'kwic-form') { ev.preventDefault(); fuehreSucheAus(); }
  });
}

function behandleKlick(ev) {
  const ziel = ev.target.closest?.('.klickbar');
  if (!ziel) return;

  if (ziel.dataset.belege) {
    zeigeBelege(ziel.dataset.belege, ziel.dataset.sprecher || 'K',
                ziel.dataset.klient, ziel.dataset.titel, ziel.dataset.hinweis);
  } else if (ziel.dataset.suche) {
    suche(ziel.dataset.suche);
  } else if (ziel.dataset.person) {
    suche(ziel.dataset.person);
  } else if (ziel.dataset.wortverlauf) {
    zeichneWortverlauf(ziel.dataset.wortverlauf);
  } else if (ziel.dataset.faden) {
    zeigeTurns(ziel.dataset.faden, Number(ziel.dataset.turn));
  } else if (ziel.dataset.sid) {
    zeigeTurns(ziel.dataset.sid, Number(ziel.dataset.turn));
  } else if (ziel.dataset.turn && App.ansicht === 'sitzung') {
    const sitzung = aktiverKlient()?.sitzungen[App.sitzungIdx];
    if (sitzung) zeigeTurns(sitzung.sid, Number(ziel.dataset.turn));
  } else if (ziel.dataset.sitzung) {
    const klient = aktiverKlient();
    const idx = klient?.sitzungen.findIndex((s) => String(s.nr) === ziel.dataset.sitzung);
    if (idx >= 0) { App.sitzungIdx = idx; bauSitzungswahl(); geheZu('sitzung'); }
  } else if (ziel.dataset.reihe) {
    const klient = aktiverKlient();
    const s = ziel.dataset.reihe;
    const L = V.fuerSprache(App.bericht.beschriftung, klient?.sprache);
    const meta = L.marker[s] ?? L.dialog[s] ?? {};
    oeffneSchublade(meta.name ?? s,
      (meta.hinweis ? `<p class="block-hinweis">${C.esc(meta.hinweis)}</p>` : '')
      + C.verlauf(klient.arc.serien[s], klient.arc.nummern, {
        hoehe: 260, breite: 760, wechselpunkte: klient.arc.wechselpunkte, klickbar: true,
      }));
  } else if (ziel.classList.contains('balken-zeile')) {
    const wort = ziel.querySelector('.balken-label')?.textContent?.trim();
    if (wort) suche(wort);
  }
}

/* ------------------------------------------------------------------ */

async function start() {
  verdrahte();
  try {
    await ladePyodide();
  } catch (fehler) {
    status(`The Python runtime could not be loaded: ${fehler.message}. `
      + 'That only fails on the very first visit without a network connection — '
      + 'after that it works offline.');
    console.error(fehler);
  }
}

start();
