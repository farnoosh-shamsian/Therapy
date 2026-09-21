/* The five views. Labels come from the report. */

import * as C from './charts.js';

const esc = C.esc;

/* ------------------------------------------------------------------ */
/* Building blocks. */
/* ------------------------------------------------------------------ */

export function konfidenz(stufe) {
  const titel = {
    A: 'A — well grounded and robustly computable',
    B: 'B — sound reasoning, heuristic implementation',
    C: 'C — exploratory; interesting to look at, not to conclude from',
  }[stufe] ?? stufe;
  return `<span class="konf konf-${esc(String(stufe).replace('*', 'stern'))}" title="${esc(titel)}">${esc(stufe)}</span>`;
}

/* One metric tile. */
export function kachel({ label, wert, konf, hinweis, marker, sprecher, spark, klient }) {
  const klickbar = marker ? ' klickbar' : '';
  // Drawer needs the tile's own label.
  const attrs = marker
    ? ` tabindex="0" role="button" data-belege="${esc(marker)}"`
      + ` data-sprecher="${esc(sprecher ?? 'K')}" data-klient="${esc(klient ?? '')}"`
      + ` data-titel="${esc(label)}" data-hinweis="${esc(hinweis ?? '')}"`
    : '';
  return `<div class="kachel${klickbar}"${attrs}>
    <div class="kachel-kopf"><span class="kachel-label">${esc(label)}</span>${konf ? konfidenz(konf) : ''}</div>
    <div class="kachel-wert">${esc(wert)}</div>
    ${spark ? `<div class="kachel-spark">${spark}</div>` : ''}
    ${hinweis ? `<p class="kachel-hinweis">${esc(hinweis)}</p>` : ''}
  </div>`;
}

/* Formats named by the language pack. */
const FORMATE = {
  prozent: (v) => C.prozent(v),
  zahl0: (v) => C.zahl(v, 0),
  zahl1: (v) => C.zahl(v, 1),
  zahl2: (v) => C.zahl(v, 2),
};

/* Pulls the label tables for one language. */
export function fuerSprache(beschriftung, sprache) {
  const waehle = (tabelle) => tabelle?.[sprache]
    ?? tabelle?.[Object.keys(tabelle ?? {})[0]] ?? {};
  return {
    marker: waehle(beschriftung.marker),
    dialog: waehle(beschriftung.dialog),
    kacheln: waehle(beschriftung.kacheln) ?? [],
    arcReihen: waehle(beschriftung.arcReihen) ?? [],
  };
}

export function sprachhinweis(text) {
  if (!text) return '';
  return `<div class="warnkasten sanft"><p>⚑ ${esc(text)}</p></div>`;
}

/* Steht über „What was read“, solange Klarnamen im Text stehen. */
export function namenshinweis(anonymisiert) {
  if (anonymisiert) return '';
  return `<div class="warnkasten">
    <p>⛑ <strong>Names were kept.</strong> You switched replacement off, so
      the real names stand in the concordance, in the word lists and in the
      sociogram — and in anything you export from here. Nothing leaves this tab
      on its own; an export you make yourself is personal data.</p>
  </div>`;
}

export function abschnitt(titel, inhalt, hinweis) {
  return `<section class="block">
    <h3>${esc(titel)}</h3>
    ${hinweis ? `<p class="block-hinweis">${esc(hinweis)}</p>` : ''}
    ${inhalt}
  </section>`;
}

/* ------------------------------------------------------------------ */
/* Ingest report. */
/* ------------------------------------------------------------------ */

export function befundAnsicht(befunde, sprachhinweisText, klienten = []) {
  if (!befunde.length) return '';
  const quelle = {
    labels: 'from labels', geraten: 'guessed', manuell: 'set by hand', keine: 'none',
  };
  const sprachQuelle = {
    erkannt: 'detected', dateiname: 'from filename', manuell: 'set by hand',
    standard: 'defaulted',
  };
  const SPALTEN = 8;

  // Counterpart to the speaker swap.
  const sprachWahl = (b) => `
    <select class="sprachwahl" data-sid="${esc(b.dateiname)}"
            title="Analyse this file with this language's word lists">
      <option value="de" ${b.sprache === 'de' ? 'selected' : ''}>German</option>
      <option value="en" ${b.sprache === 'en' ? 'selected' : ''}>English</option>
    </select>
    <span class="sprach-quelle">${esc(sprachQuelle[b.spracheQuelle] ?? b.spracheQuelle)}</span>`;

  // Name the roles, not the labels.
  const sprecherZelle = (b) => {
    const text = esc(quelle[b.sprecherQuelle] ?? b.sprecherQuelle);
    if (b.sprecherQuelle === 'keine') return text;
    return `${text}
      <button type="button" class="sprecher-tausch" data-sid="${esc(b.dateiname)}"
              title="Swap therapist and client throughout this file">swap</button>`;
  };

  const zeilen = befunde.map((b) => `
    <tr class="${b.warnungen.length ? 'warn' : ''}">
      <td class="mono">${esc(b.dateiname)}</td>
      <td><span class="tag">${esc(b.format)}</span></td>
      <td>${sprachWahl(b)}</td>
      <td class="num">${esc(b.turns)}</td>
      <td class="num">${esc(b.woerter)}</td>
      <td>${b.labels.length ? b.labels.map((l) => `<span class="tag">${esc(l)}</span>`).join(' ') : '<em>none</em>'}</td>
      <td>${sprecherZelle(b)}</td>
      <td>${b.zeitstempel ? 'yes' : 'no'}</td>
    </tr>
    ${teilungsZeile(b, SPALTEN)}
    ${b.warnungen.map((w) => `<tr class="warnzeile"><td colspan="${SPALTEN}">⚠ ${esc(w)}</td></tr>`).join('')}
    ${b.nichtVerfuegbar.length ? `<tr class="infozeile"><td colspan="${SPALTEN}">Unavailable for this file: ${esc(b.nichtVerfuegbar.join(', '))}</td></tr>` : ''}
  `).join('');

  return abschnitt('What was read', `
    <table class="tabelle">
      <thead><tr><th>File</th><th>Format</th><th>Language</th><th>Turns</th><th>Words</th>
        <th>Labels</th><th>Speakers</th><th>Time</th></tr></thead>
      <tbody>${zeilen}</tbody>
    </table>
    ${fallnamen(klienten)}
    ${sprachhinweis(sprachhinweisText)}`,
    'What the files actually contained, not a result. Anything missing here '
    + 'is missing later too. Correct a language or swap the speakers and '
    + 'everything is recomputed.');
}

/* Fallname: eintippbar, wenn kein Dateiname da ist. */
function fallnamen(klienten) {
  if (!klienten.length) return '';
  return `<div class="fallnamen">
    <h4>Cases</h4>
    <p class="block-hinweis">Grouped from the filenames. The name is a label
      only: not analysed, not exported.</p>
    ${klienten.map((k) => `
      <label class="fallname">
        <input type="text" class="fallname-feld" value="${esc(k.id)}"
               data-klient="${esc(k.id)}" maxlength="40"
               aria-label="Name for this case">
        <span class="anzahl">${esc(k.sitzungen.length)} sessions</span>
      </label>`).join('')}
  </div>`;
}

/* Wie eine Datei in Sitzungen zerfiel. */
function teilungsZeile(b, spalten) {
  const teile = b.sitzungen ?? [];
  if (b.teilung === 'keine' || teile.length < 2) return '';
  const segment = b.teilung === 'segmente';
  const marken = teile.map((s) => {
    const name = `${segment ? 'Seg' : 'S'}${s.nr ?? '?'}`;
    return `<span class="tag" title="${esc(s.turns)} turns, ${esc(s.woerter)} words">${esc(name)}${
      s.datum ? ` · ${esc(s.datum)}` : ''}</span>`;
  }).join(' ');
  return `<tr class="infozeile"><td colspan="${spalten}">
    ${segment
      ? `Cut into <b>${teile.length} equal segments</b> — no session markers were
         found. The trend is a trend <em>within</em> this text, not between sessions.`
      : `Split into <b>${teile.length} sessions</b> at the markers in the text.`}
    ${marken}</td></tr>`;
}

/* ------------------------------------------------------------------ */
/* Session card. */
/* ------------------------------------------------------------------ */

export function sitzungskarte(klient, sitzung, beschriftung, hinweise, serien) {
  const k = sitzung.marker.K?.kennzahlen ?? {};
  const dia = sitzung.dialog ?? {};
  const L = fuerSprache(beschriftung, sitzung.sprache);
  const B = L.marker;
  const D = L.dialog;
  const spark = (schluessel) => (serien && serien[schluessel])
    ? C.sparkline(serien[schluessel]) : '';

  // Tiles and captions come from the pack.
  const kacheln = L.kacheln.map(([schluessel, format, marker]) => {
    const meta = B[schluessel] ?? B[schluessel.replace('_anzahl', '_rate')] ?? {};
    const fmt = FORMATE[format] ?? FORMATE.zahl1;
    return kachel({
      label: meta.name ?? schluessel,
      wert: fmt(k[schluessel] ?? 0),
      konf: meta.konfidenz, hinweis: meta.hinweis,
      marker, sprecher: 'K', klient: klient.id,
      spark: spark(schluessel),
    });
  }).join('');

  const fragen = (dia.fragenGesamt ?? 0) > 0
    ? C.anteile([
        { label: 'open', wert: dia.fragenOffen },
        { label: 'closed', wert: dia.fragenGeschlossen },
      ])
    : '<p class="leer">No questions detected.</p>';

  const dialogKacheln = [
    kachel({
      label: D.redeanteilT?.name ?? 'Therapist talk ratio',
      wert: C.prozent(dia.redeanteilT ?? 0),
      konf: D.redeanteilT?.konfidenz, hinweis: D.redeanteilT?.hinweis,
      spark: spark('redeanteilT'),
    }),
    kachel({
      label: 'Turn length, client / therapist (median)',
      wert: `${C.zahl(dia.medianLaenge?.K ?? 0, 0)} / ${C.zahl(dia.medianLaenge?.T ?? 0, 0)}`,
      konf: 'A', hinweis: D.medianLaenge?.hinweis,
    }),
    kachel({
      label: D.aufnahme?.name ?? 'Lexical uptake',
      wert: C.prozent(dia.aufnahme ?? 0),
      konf: D.aufnahme?.konfidenz, hinweis: D.aufnahme?.hinweis,
      spark: spark('aufnahme'),
    }),
    kachel({
      label: D.lsm?.name ?? 'Style matching',
      wert: C.zahl(dia.lsm ?? 0, 2),
      konf: D.lsm?.konfidenz, hinweis: D.lsm?.hinweis,
      spark: spark('lsm'),
    }),
  ].join('');

  const ttr = sitzung.ttr ?? {};
  const vokabel = (sitzung.neuesVokabular ?? []).slice(0, 24);

  return `
  <header class="ansicht-kopf">
    <h2>${esc(sitzung.titel)}</h2>
    <p class="unter">${esc(sitzung.dateiname)} · ${esc(sitzung.turns)} turns ·
      ${esc(sitzung.format)} · <span class="tag">${esc(sitzung.spracheName)}</span></p>
  </header>

  ${klient.spracheGemischt ? sprachhinweis(klient.spracheWarnung) : ''}

  ${sitzung.befund?.warnungen?.length ? `<div class="warnkasten">${sitzung.befund.warnungen.map((w) => `<p>⚠ ${esc(w)}</p>`).join('')}</div>` : ''}

  ${abschnitt('The client’s language', `<div class="kacheln">${kacheln}</div>`,
    `Hits per 1000 client words, counted with the ${sitzung.spracheName} word `
    + `lists. Click a tile for the lines behind it.`)}

  ${abschnitt('Affect through the hour',
    C.sitzungsverlauf(sitzung.affektverlauf ?? []),
    'One circle per client turn: size is its length, height the density of '
    + 'named feelings. Unsmoothed.')}

  ${abschnitt('Dialogue', `<div class="kacheln">${dialogKacheln}</div>
    <h4>Question types</h4>${fragen}`)}

  ${abschnitt('Dropped threads', fadenListe(sitzung.faeden ?? [], klient.id), hinweise.faeden)}

  ${abschnitt('Vocabulary', `
    <div class="kacheln">
      ${kachel({ label: 'Type-token ratio (standardised), client', wert: C.zahl(ttr.K?.sttr ?? 0, 3), konf: 'B',
        hinweis: ttr.K?.belastbar ? 'Computed in windows of 100 words.'
          : 'Fewer than 100 words — this number does not carry weight.' })}
      ${kachel({ label: 'Words, client / therapist',
        wert: `${C.zahl(dia.woerter?.K ?? 0, 0)} / ${C.zahl(dia.woerter?.T ?? 0, 0)}`, konf: 'A' })}
    </div>
    <h4>First appearing in this session</h4>
    ${vokabel.length
      ? `<p class="wortwolke">${vokabel.map((w) => `<button class="wort klickbar" data-suche="${esc(w)}">${esc(w)}</button>`).join(' ')}</p>`
      : '<p class="leer">Nothing new — or this is the first session.</p>'}`,
    `Content words that appear in no earlier session with this client.`
    + (klient.spracheGemischt
      ? ' After a change of language almost everything is “new” — arithmetic,'
        + ' not a finding.'
      : ''))}
  `;
}

function fadenListe(faeden, klientId) {
  if (!faeden.length) return '<p class="leer">No candidates in this session.</p>';
  return `<ol class="faeden">${faeden.map((f) => `
    <li class="faden klickbar" tabindex="0" role="button"
        data-faden="${esc(f.sid)}" data-turn="${esc(f.turnKlient)}" data-klient="${esc(klientId)}">
      <div class="faden-kopf">
        <span class="faden-ort">Session ${esc(f.nr ?? '?')}, turn ${esc(f.turnKlient)}</span>
        <span class="faden-staerke" title="How loaded the moment was, and how completely it was left lying">${esc(C.zahl(f.staerke, 2))}</span>
      </div>
      <p class="faden-woerter">${f.affektWoerter.map((w) => `<span class="tag">${esc(w)}</span>`).join(' ')}</p>
      <p class="faden-meta">${esc(f.woerter)} words · uptake ${esc(C.prozent(f.aufnahme))} · return ${esc(C.prozent(f.rueckkehr))}</p>
    </li>`).join('')}</ol>`;
}

/* ------------------------------------------------------------------ */
/* Arc (one client across all sessions). */
/* ------------------------------------------------------------------ */

export function bogen(klient, beschriftung, hinweise) {
  const a = klient.arc;
  const L = fuerSprache(beschriftung, klient.sprache);
  const B = L.marker;
  const nummern = a.nummern;

  const saetze = a.saetze.length
    ? `<ul class="saetze">${a.saetze.map((s) => `<li>${esc(s)}</li>`).join('')}</ul>`
    : `<p class="leer">No changepoint above the reporting threshold. That is a
       valid result, not a failure.</p>`;

  // Order from the pack; spliced series last.
  const reihen = L.arcReihen
    .concat(Object.keys(a.serien).filter((s) => s.startsWith('vgl_')))
    .filter((s) => a.serien[s]);

  const kleinBilder = reihen.map((s) => {
    const meta = B[s] ?? L.dialog[s] ?? {};
    const trend = a.trend[s] ?? 0;
    const pfeil = trend > 0.45 ? '↗' : trend < -0.45 ? '↘' : '→';
    return `<figure class="klein-bild klickbar" tabindex="0" role="button" data-reihe="${esc(s)}">
      <figcaption>
        <span>${esc(meta.name ?? s)}</span>
        ${meta.konfidenz ? konfidenz(meta.konfidenz) : ''}
        <span class="trend" title="Rank correlation with session order: ${esc(C.zahl(trend, 2))}">${pfeil}</span>
      </figcaption>
      ${C.verlauf(a.serien[s], nummern, { hoehe: 96, breite: 300, wechselpunkte: a.wechselpunkte })}
    </figure>`;
  }).join('');

  const sozio = klient.soziogramm;

  return `
  <header class="ansicht-kopf">
    <h2>Trends — ${esc(klient.id)}</h2>
    <p class="unter">${esc(klient.sitzungen.length)} sessions ·
      <span class="tag">${esc(klient.spracheName)}</span></p>
  </header>

  ${klient.genugSitzungen ? '' : `<div class="warnkasten"><p>⚠ Fewer than ten
     sessions. Most markers mean nothing below that line — the curves below are
     here to try out, not to conclude from.</p></div>`}

  ${klient.spracheGemischt ? sprachhinweis(klient.spracheWarnung) : ''}

  ${abschnitt('The one sentence', saetze + `
    ${C.verlauf(a.komposit, nummern, {
      hoehe: 190, breite: 720, wechselpunkte: a.wechselpunkte,
      glatt: a.kompositGeglaettet, klickbar: true,
    })}`, hinweise.arc)}

  ${abschnitt('Every marker across the sessions', `<div class="klein-bilder">${kleinBilder}</div>`,
    'Click a chart to open it large. The arrow is the rank correlation with '
    + 'session order, not a significance test.')}

  ${abschnitt('Who is in the room',
    C.soziogramm(sozio.knoten ?? [], sozio.kanten ?? [])
    + C.personenverlauf(sozio.verlauf ?? [], sozio.sitzungen ?? [])
    + eintritte(sozio), sozio.hinweis)}

  ${abschnitt('Dropped threads across all sessions',
    fadenListe(klient.faeden ?? [], klient.id), hinweise.faeden)}
  `;
}

function eintritte(sozio) {
  const e = sozio.eintritte ?? [], ab = sozio.abgaenge ?? [];
  if (!e.length && !ab.length) return '';
  return `<div class="kommen-gehen">
    ${e.length ? `<p><b>Enters the narrative:</b> ${e.map((x) => `${esc(x.name)} (from session ${esc(x.sitzung)})`).join(', ')}</p>` : ''}
    ${ab.length ? `<p><b>Fades out:</b> ${ab.map((x) => `${esc(x.name)} (last in session ${esc(x.sitzung)})`).join(', ')}</p>` : ''}
  </div>`;
}

function keynessListe(eintraege) {
  if (!eintraege?.length) return '<p class="leer">Nothing stands out here.</p>';
  return C.balken(eintraege.slice(0, 25).map((e) => ({
    label: e.anzeige ?? e.wort, wert: e.ll,
    // G² sorts; log ratio sizes.
    zusatz: `${e.hier}× here, ${e.referenz}× elsewhere`
      + (e.logRatio !== null && e.logRatio !== undefined ? ` · ${C.zahl(e.logRatio, 1)}×log₂` : ''),
    schluessel: null,
  })), { format: (v) => C.zahl(v, 1) })
    + `<p class="block-hinweis">Click a word to open the concordance.</p>`;
}

/* Frequenzen *nach* der Zerlegung. */
function teilfrequenzListe(eintraege) {
  if (!eintraege.length) return '';
  return `<h4 class="unter-titel">Counted after splitting</h4>
    <p class="wortwolke">${eintraege.slice(0, 30).map((e) =>
    `<button class="wort klickbar" data-wortverlauf="${esc(e.anzeige ?? e.wort)}">
      ${esc(e.anzeige ?? e.wort)} <span class="anzahl">${esc(e.anzahl)}×</span></button>`).join(' ')}</p>`;
}

function kompositaListe(eintraege) {
  if (!eintraege.length) return '<p class="leer">No decomposable compounds found.</p>';
  return `<p class="wortwolke">${eintraege.map((e) =>
    `<button class="wort klickbar" data-suche="${esc(e.wort)}">
      ${esc(e.wort)} <span class="teile">${esc(e.teile.join(' + '))}</span>
      <span class="anzahl">${esc(e.anzahl)}×</span></button>`).join(' ')}</p>`;
}

/* ------------------------------------------------------------------ */
/* Keywords. */
/* ------------------------------------------------------------------ */
/* Keyness sits up top now. */

export function woerter(klient, hinweise = {}) {
  const sw = klient.schluesselwoerter ?? {};
  const phase = sw.phase ?? {};
  const bewegung = sw.bewegung ?? {};
  const komposita = sw.komposita ?? [];

  const einstiege = (sw.haeufig ?? []).slice(0, 30).map((e) =>
    `<button class="wort klickbar" data-wortverlauf="${esc(e.anzeige ?? e.wort)}">
      ${esc(e.anzeige ?? e.wort)} <span class="anzahl">${esc(e.anzahl)}×</span></button>`).join(' ');

  return `
  <header class="ansicht-kopf">
    <h2>Keywords — ${esc(klient.id)}</h2>
    <p class="unter">${esc(klient.sitzungen.length)} sessions ·
      <span class="tag">${esc(klient.spracheName)}</span></p>
  </header>

  ${klient.spracheGemischt ? sprachhinweis(klient.spracheWarnung) : ''}

  ${abschnitt('One word across the sessions', `
    <form id="wort-form" class="suchzeile" autocomplete="off">
      <input type="search" id="wort-eingabe" placeholder="A word — Angst, Mutter, Arbeit …"
             aria-label="Word to plot across the sessions">
      <button type="submit" class="knopf">Plot it</button>
    </form>
    <div id="wort-verlauf"></div>
    <p class="wortwolke">${einstiege}</p>`,
    'Rate per 1000 words, not raw counts, and searched by lemma — “Ängste” '
    + 'and “Angst” are one curve. Click a point to open the session.')}

  ${abschnitt('Late sessions against early ones',
    phase.genug
      ? `<div class="wort-spalten">
           <div><h4>More in the late half</h4>${keynessListe(phase.spaet ?? [])}</div>
           <div><h4>More in the early half</h4>${keynessListe(phase.frueh ?? [])}</div>
         </div>`
      : `<p class="leer">Fewer than four sessions — there is no early and late
         half to compare yet.</p>`,
    sw.hinweis)}

  ${abschnitt('What comes and what goes',
    bewegung.genug
      ? `<div class="wort-spalten">
           ${wortSpalte('Rising', bewegung.steigend, (e) => `ρ ${C.zahl(e.rho, 2)}`)}
           ${wortSpalte('Fading', bewegung.fallend, (e) => `ρ ${C.zahl(e.rho, 2)}`)}
           ${wortSpalte('Appears late', bewegung.neu, (e) => `from session ${esc(e.erst)}`)}
           ${wortSpalte('Stops early', bewegung.verschwunden, (e) => `last in session ${esc(e.letzt)}`)}
         </div>`
      : `<p class="leer">Fewer than four sessions — a rank correlation over
         three points is not an answer.</p>`,
    'Rising and fading are the rank correlation of a word’s rate against '
    + 'session order. Appearing and stopping are simpler and often say more.')}

  ${komposita.length ? abschnitt('Compounds, split open',
    kompositaListe(komposita)
    + teilfrequenzListe(sw.teilfrequenzen ?? []),
    '“Verlustangst” vanishes into the tail unless it is split — and that is '
    + 'where the loaded vocabulary hides. English writes its compounds open, so '
    + 'this block is German only.') : ''}

  ${abschnitt('Against your other clients',
    klient.keynessHinweis
      ? `<p class="leer">${esc(klient.keynessHinweis)}</p>`
      : keynessListe(klient.keyness ?? []),
    'Log-likelihood against the rest of your caseload, and only against '
    + 'clients seen in the same language.')}
  `;
}

function wortSpalte(titel, eintraege, zusatz) {
  const liste = eintraege ?? [];
  if (!liste.length) return `<div><h4>${esc(titel)}</h4><p class="leer">Nothing here.</p></div>`;
  return `<div><h4>${esc(titel)}</h4>
    <ul class="wortliste">${liste.slice(0, 12).map((e) => `
      <li><button class="wort klickbar" data-wortverlauf="${esc(e.anzeige ?? e.wort)}">${esc(e.anzeige ?? e.wort)}</button>
        <span class="anzahl">${esc(e.anzahl)}×</span>
        <span class="zusatz">${esc(zusatz(e))}</span></li>`).join('')}</ul></div>`;
}

/* ------------------------------------------------------------------ */
/* Concordance and evidence. */
/* ------------------------------------------------------------------ */

export function kwicListe(zeilen, begriff) {
  if (!zeilen.length) {
    return `<p class="leer">No occurrence of “${esc(begriff)}”.</p>`;
  }
  return `<p class="treffer-zahl">${zeilen.length} occurrences of “${esc(begriff)}”</p>
  <ol class="kwic">${zeilen.map((z) => `
    <li class="kwic-zeile klickbar" tabindex="0" role="button"
        data-sid="${esc(z.sid)}" data-turn="${esc(z.turn)}" data-klient="${esc(z.klient ?? '')}">
      <span class="kwic-ort">S${esc(z.nr ?? '?')}·${esc(z.turn)}<i class="sprecher s-${esc(z.sprecher)}">${esc(z.sprecher)}</i></span>
      <span class="kwic-links">${esc(z.links)}</span><span class="kwic-treffer">${esc(z.treffer)}</span><span class="kwic-rechts">${esc(z.rechts)}</span>
    </li>`).join('')}</ol>`;
}

export function belegListe(zeilen, titel) {
  if (!zeilen.length) return '<p class="leer">No occurrences.</p>';
  return `<p class="treffer-zahl">${zeilen.length} occurrences — ${esc(titel)}</p>
  <ol class="kwic">${zeilen.map((z) => `
    <li class="kwic-zeile klickbar" tabindex="0" role="button"
        data-sid="${esc(z.sid)}" data-turn="${esc(z.turn)}">
      <span class="kwic-ort">S${esc(z.nr ?? '?')}·${esc(z.turn)}<i class="sprecher s-${esc(z.sprecher)}">${esc(z.sprecher)}</i></span>
      <span class="kwic-links">${esc(z.links)}</span><span class="kwic-treffer">${esc(z.treffer)}</span><span class="kwic-rechts">${esc(z.rechts)}</span>
    </li>`).join('')}</ol>`;
}

export function kollokationsListe(eintraege, begriff) {
  if (!eintraege.length) return '<p class="leer">Too few hits for collocations.</p>';
  return `<h4>What clusters around “${esc(begriff)}”</h4>`
    + C.balken(eintraege.map((e) => ({
      label: e.wort, wert: e.ll, zusatz: `${e.gemeinsam}× nearby, ${e.gesamt}× total`,
    })), { format: (v) => C.zahl(v, 1) })
    + '<p class="block-hinweis">Log-likelihood, not raw frequency: this shows '
    + 'what stands nearby <em>more often than expected</em>.</p>';
}

/* ------------------------------------------------------------------ */
/* Turn view: the jump back. */
/* ------------------------------------------------------------------ */

export function turnAnsicht(turns, fokus) {
  return `<ol class="turns">${turns.map((t) => `
    <li class="turn ${t.idx === fokus ? 'fokus' : ''} sprecher-${esc(t.sprecher)}" id="turn-${esc(t.idx)}">
      <span class="turn-ort">${esc(t.idx)}<i class="sprecher s-${esc(t.sprecher)}">${esc(t.sprecher)}</i></span>
      <p>${esc(t.text)}</p>
    </li>`).join('')}</ol>`;
}

/* ------------------------------------------------------------------ */
/* Validity notes. */
/* ------------------------------------------------------------------ */

/* Vorbehalte: zugeklappt, aber vorhanden. */
export function geltung(hinweise) {
  if (!hinweise?.length) return '';
  return `<details class="geltung-block">
    <summary>What these numbers can and cannot carry</summary>
    <div class="geltung">${hinweise.map((h) => `
      <div class="geltung-punkt"><h4>${esc(h.titel)}</h4><p>${esc(h.text)}</p></div>`).join('')}</div>
  </details>`;
}
