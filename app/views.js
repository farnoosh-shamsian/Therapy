/* Thera.py — views.
 *
 * Four views (session card, arc, mirror, concordance) plus the ingest report.
 * Every function here returns HTML as a string; wiring up the clicks is
 * main.js's job.
 *
 * Note on language: the interface is English; the material is German or
 * English, per session. Marker names are translated, but every example inside
 * them is quoted in the language it was spoken in and left untranslated —
 * "man fühlt sich dann halt schlecht" has no English equivalent, and that is
 * exactly why this tool analyses each session in its own language rather than
 * a translation of it.
 *
 * Nothing in this file knows which markers exist. Which tiles a session card
 * shows, which series the arc draws, and what every label and caveat says
 * comes from `beschriftung` in the report, keyed by the session's language.
 * That is deliberate: a view with a hard-coded list of German keys shows an
 * English session ten empty tiles.
 *
 * Three rules that hold in every view:
 *
 *  1. **Every number carries its confidence and its caveat.** A number without
 *     a statement of what it can bear is not information here, it is a claim.
 *  2. **Every number is clickable** and opens the lines that produced it.
 *     Without that, Thera.py becomes a dashboard he watches instead of a
 *     person he listens to.
 *  3. **Wherever two languages meet, the view says so.** Rates computed with
 *     different word lists are not comparable, and a chart that quietly puts
 *     them on one axis is worse than no chart.
 */

import * as C from './charts.js';

const esc = C.esc;

/* ------------------------------------------------------------------ */
/* Building blocks                                                     */
/* ------------------------------------------------------------------ */

export function konfidenz(stufe) {
  const titel = {
    A: 'A — well grounded and robustly computable',
    'A*': 'A* — well grounded, but only when the transcript has timestamps',
    B: 'B — sound reasoning, heuristic implementation',
    C: 'C — exploratory; interesting to look at, not to conclude from',
  }[stufe] ?? stufe;
  return `<span class="konf konf-${esc(String(stufe).replace('*', 'stern'))}" title="${esc(titel)}">${esc(stufe)}</span>`;
}

/**
 * One metric tile. `marker` makes it clickable and names the hit list to open.
 */
export function kachel({ label, wert, konf, hinweis, marker, sprecher, spark, klient }) {
  const klickbar = marker ? ' klickbar' : '';
  // The drawer needs the tile's own label and caveat: the marker key ("man")
  // is not the same key as the metric ("man_quote"), so looking the label up
  // again from the marker key would come back empty.
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

/** Format names used by `beschriftung.kacheln`, which comes from Python. */
const FORMATE = {
  prozent: (v) => C.prozent(v),
  zahl0: (v) => C.zahl(v, 0),
  zahl1: (v) => C.zahl(v, 1),
  zahl2: (v) => C.zahl(v, 2),
};

/**
 * Pulls the label tables for one language out of the report.
 * Falls back to the first language present rather than to German, so a
 * purely English corpus never renders a German caveat.
 */
export function fuerSprache(beschriftung, sprache) {
  const waehle = (tabelle) => tabelle?.[sprache]
    ?? tabelle?.[Object.keys(tabelle ?? {})[0]] ?? {};
  return {
    marker: waehle(beschriftung.marker),
    dialog: waehle(beschriftung.dialog),
    interventionen: waehle(beschriftung.interventionen),
    kacheln: waehle(beschriftung.kacheln) ?? [],
    arcReihen: waehle(beschriftung.arcReihen) ?? [],
  };
}

export function sprachhinweis(text) {
  if (!text) return '';
  return `<div class="warnkasten sanft"><p>⚑ ${esc(text)}</p></div>`;
}

export function abschnitt(titel, inhalt, hinweis) {
  return `<section class="block">
    <h3>${esc(titel)}</h3>
    ${hinweis ? `<p class="block-hinweis">${esc(hinweis)}</p>` : ''}
    ${inhalt}
  </section>`;
}

/* ------------------------------------------------------------------ */
/* Ingest report                                                       */
/* ------------------------------------------------------------------ */

export function befundAnsicht(befunde, sprachhinweisText) {
  if (!befunde.length) return '';
  const quelle = {
    labels: 'from labels', geraten: 'guessed', manuell: 'set by hand', keine: 'none',
  };
  const sprachQuelle = {
    erkannt: 'detected', dateiname: 'from filename', manuell: 'set by hand',
    standard: 'defaulted',
  };
  const SPALTEN = 8;

  // The language select is the counterpart to the speaker swap: detection is a
  // heuristic, so it gets a control that corrects it in one click rather than a
  // paragraph explaining that it might be wrong.
  const sprachWahl = (b) => `
    <select class="sprachwahl" data-sid="${esc(b.dateiname)}"
            title="Analyse this file with this language's word lists">
      <option value="de" ${b.sprache === 'de' ? 'selected' : ''}>German</option>
      <option value="en" ${b.sprache === 'en' ? 'selected' : ''}>English</option>
    </select>
    <span class="sprach-quelle">${esc(sprachQuelle[b.spracheQuelle] ?? b.spracheQuelle)}</span>`;

  const zeilen = befunde.map((b) => `
    <tr class="${b.warnungen.length ? 'warn' : ''}">
      <td class="mono">${esc(b.dateiname)}</td>
      <td><span class="tag">${esc(b.format)}</span></td>
      <td>${sprachWahl(b)}</td>
      <td class="num">${esc(b.turns)}</td>
      <td class="num">${esc(b.woerter)}</td>
      <td>${b.labels.length ? b.labels.map((l) => `<span class="tag">${esc(l)}</span>`).join(' ') : '<em>none</em>'}</td>
      <td>${esc(quelle[b.sprecherQuelle] ?? b.sprecherQuelle)}</td>
      <td>${b.zeitstempel ? 'yes' : 'no'}</td>
    </tr>
    ${b.warnungen.map((w) => `<tr class="warnzeile"><td colspan="${SPALTEN}">⚠ ${esc(w)}</td></tr>`).join('')}
    ${b.nichtVerfuegbar.length ? `<tr class="infozeile"><td colspan="${SPALTEN}">Unavailable for this file: ${esc(b.nichtVerfuegbar.join(', '))}</td></tr>` : ''}
  `).join('');

  return abschnitt('What was read', `
    <table class="tabelle">
      <thead><tr><th>File</th><th>Format</th><th>Language</th><th>Turns</th><th>Words</th>
        <th>Labels</th><th>Speakers</th><th>Time</th></tr></thead>
      <tbody>${zeilen}</tbody>
    </table>
    ${sprachhinweis(sprachhinweisText)}`,
    'This is an honest report of the ingest, not a result. Whatever is missing '
    + 'here will be missing later too — which is why it comes before the '
    + 'numbers rather than after them. The language is detected per file; '
    + 'change it here if it is wrong, and the analysis is recomputed.');
}

/* ------------------------------------------------------------------ */
/* Session card                                                        */
/* ------------------------------------------------------------------ */

export function sitzungskarte(klient, sitzung, beschriftung, hinweise, serien) {
  const k = sitzung.marker.K?.kennzahlen ?? {};
  const dia = sitzung.dialog ?? {};
  const L = fuerSprache(beschriftung, sitzung.sprache);
  const B = L.marker;
  const D = L.dialog;
  const spark = (schluessel) => (serien && serien[schluessel])
    ? C.sparkline(serien[schluessel]) : '';

  // Which tiles, in which order, and which hit list a click opens: all of it
  // comes from the language pack via the report. See the note at the top.
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
    dia.zeitstempel
      ? kachel({
          label: 'Response latency (median)',
          wert: dia.latenzMedian !== null ? `${C.zahl(dia.latenzMedian, 1)} s` : '–',
          konf: 'A*', hinweis: D.latenzMedian?.hinweis,
        })
      : kachel({
          label: 'Response latency',
          wert: 'unavailable',
          konf: 'A*',
          hinweis: 'This transcript has no timestamps. The number is left out '
            + 'rather than estimated.',
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
    `All rates are hits per 1000 words spoken by the client, counted with the `
    + `${sitzung.spracheName} word lists. Click any tile to open the lines that `
    + `produced it.`)}

  ${abschnitt('Affect through the hour',
    C.sitzungsverlauf(sitzung.affektverlauf ?? []),
    'Each circle is one client turn; size is its length, height is the density '
    + 'of named feelings. Unsmoothed — the shape of an hour is more honest raw.')}

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
    `Content words that appear in no earlier session with this client. Click `
    + `one to look it up in the concordance.`
    + (klient.spracheGemischt
      ? ' This client’s sessions are not all in one language, so the first'
        + ' session after a switch is almost entirely “new” — that is arithmetic,'
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
/* Arc (one client across all sessions)                                */
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

  // The order comes from the language pack. Series that do not exist in this
  // client's language — or that dropped out because the client switched
  // language mid-course — are simply absent, and the spliced `vgl_*` series
  // take their place at the end, carrying their own caveat.
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
    <h2>Arc — ${esc(klient.id)}</h2>
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

  ${abschnitt('What makes this client distinctive',
    klient.keynessHinweis
      ? `<p class="leer">${esc(klient.keynessHinweis)}</p>`
      : keynessListe(klient.keyness ?? []),
    'Log-likelihood against the rest of your caseload rather than against a '
    + 'general corpus, and only against clients seen in the same language. '
    + 'With fewer than two such clients loaded this list stays empty.')}

  ${(klient.komposita ?? []).length ? abschnitt('Compounds',
    kompositaListe(klient.komposita),
    'German compounds, split open. “Verlustangst” appears once and vanishes '
    + 'into the tail unless it is decomposed — and that is exactly where the '
    + 'emotionally loaded vocabulary hides. English writes its compounds open '
    + '(“fear of loss”), so they are already split and this block does not '
    + 'appear for English sessions.') : ''}

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
  if (!eintraege.length) return '<p class="leer">No reference corpus available.</p>';
  return C.balken(eintraege.slice(0, 25).map((e) => ({
    label: e.wort, wert: e.ll,
    zusatz: `${e.hier}× here, ${e.referenz}× elsewhere`,
    schluessel: null,
  })), { format: (v) => C.zahl(v, 1) })
    + `<p class="block-hinweis">Click a word to open the concordance.</p>`;
}

function kompositaListe(eintraege) {
  if (!eintraege.length) return '<p class="leer">No decomposable compounds found.</p>';
  return `<p class="wortwolke">${eintraege.map((e) =>
    `<button class="wort klickbar" data-suche="${esc(e.wort)}">
      ${esc(e.wort)} <span class="teile">${esc(e.teile.join(' + '))}</span>
      <span class="anzahl">${esc(e.anzahl)}×</span></button>`).join(' ')}</p>`;
}

/* ------------------------------------------------------------------ */
/* Mirror                                                              */
/* ------------------------------------------------------------------ */

export function spiegel(daten, beschriftung, hinweise = {}) {
  if (!daten.profile.length) return '<p class="leer">Nothing loaded yet.</p>';

  // The mirror is the one view that puts clients of different languages side by
  // side, so it is the one view that has to name the seam. Rows that cross it
  // are marked rather than dropped — dropped, a bilingual practice would lose
  // half the table.
  const ueberGrenze = daten.vergleich.some((z) => z.sprachgrenze);
  const namenFuer = (klientId) => {
    const profil = daten.profile.find((p) => p.klient === klientId);
    return fuerSprache(beschriftung, profil?.sprachen?.[0]).interventionen;
  };

  const vergleich = daten.vergleich.length
    ? `<ul class="vergleich">${daten.vergleich.map((z) => `
        <li class="${z.sprachgrenze ? 'ueber-sprachgrenze' : ''}">
          <span class="vergleich-satz">${esc(z.satz)}${z.sprachgrenze
            ? ' <span class="grenze-marke" title="These two clients were seen in different languages — part of this gap is the tool, not you.">⚑ across languages</span>'
            : ''}</span>
          <span class="vergleich-zahl">${esc(C.zahl(z.verhaeltnis, 1))}×</span></li>`).join('')}</ul>`
    : `<p class="leer">${daten.genugKlienten
        ? 'No striking differences between clients.'
        : 'The comparison needs at least two clients. This is the view the whole '
          + 'exercise is worth — load a second case.'}</p>`;

  const profile = daten.profile.map((p) => {
    const namen = namenFuer(p.klient);
    const kategorien = Object.entries(p.anteile)
      .filter(([kat]) => kat !== 'rueckkanal')
      .sort((a, b) => b[1] - a[1]);
    return `<article class="profil">
      <h4>${esc(p.klient)} <span class="tag">${esc(p.spracheName)}</span></h4>
      <p class="unter">${esc(p.sitzungen)} sessions · talk ratio ${esc(C.prozent(p.redeanteil))}
        · open questions ${esc(p.frageQuote !== null ? C.prozent(p.frageQuote) : '–')}
        · uptake ${esc(C.prozent(p.aufnahme))}</p>
      ${C.anteile(kategorien.map(([kat, wert]) => ({ label: namen[kat] ?? kat, wert })))}
      ${C.balken(kategorien.map(([kat, wert]) => ({
        label: namen[kat] ?? kat, wert,
        zusatz: `${p.interventionen[kat]}×`,
        schluessel: `intervention:${p.klient}:${kat}`,
      })), { format: (v) => C.prozent(v, 1) })}
    </article>`;
  }).join('');

  const idiolekt = daten.idiolekt.length
    ? `<ol class="idiolekt">${daten.idiolekt.map((e) => `
        <li><span class="phrase">“${esc(e.phrase)}”</span>
          <span class="anzahl">${esc(e.anzahl)}×</span>
          <span class="bei">with ${esc(e.klienten.join(', '))}</span></li>`).join('')}</ol>`
    : '<p class="leer">No phrase recurs across more than one client.</p>';

  return `
  <header class="ansicht-kopf">
    <h2>Mirror</h2>
    <p class="unter">Across your whole caseload — about you.</p>
  </header>

  <div class="warnkasten sanft"><p>${esc(daten.hinweis)}</p></div>
  ${ueberGrenze ? sprachhinweis(hinweise.spiegelSprachgrenze) : ''}

  ${abschnitt('The comparison', vergleich,
    'The line in this view that carries the most weight. Absolute shares carry '
    + 'little; ratios between clients carry more, because the same measurement '
    + 'error sits on both sides.')}

  ${abschnitt('Intervention profile per client', `<div class="profile">${profile}</div>`,
    'Assigned by rule, confidence C. Click a category to see example turns — '
    + 'read a few before believing the distribution.')}

  ${abschnitt('Your idiolect', idiolekt,
    'Your own formulaic phrases, counted across every client. Only phrases that '
    + 'occur with more than one person: otherwise it is not idiolect, it is that '
    + 'one case. Phrases are counted within a language, so a habit you have in '
    + 'both will show up as two entries rather than one.')}
  `;
}

/* ------------------------------------------------------------------ */
/* Concordance and evidence                                            */
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
/* Turn view (the jump back into the text)                             */
/* ------------------------------------------------------------------ */

export function turnAnsicht(turns, fokus) {
  return `<ol class="turns">${turns.map((t) => `
    <li class="turn ${t.idx === fokus ? 'fokus' : ''} sprecher-${esc(t.sprecher)}" id="turn-${esc(t.idx)}">
      <span class="turn-ort">${esc(t.idx)}<i class="sprecher s-${esc(t.sprecher)}">${esc(t.sprecher)}</i></span>
      <p>${esc(t.text)}</p>
    </li>`).join('')}</ol>`;
}

/* ------------------------------------------------------------------ */
/* Validity notes                                                      */
/* ------------------------------------------------------------------ */

export function geltung(hinweise) {
  return `<div class="geltung">${hinweise.map((h) => `
    <div class="geltung-punkt"><h4>${esc(h.titel)}</h4><p>${esc(h.text)}</p></div>`).join('')}</div>`;
}
