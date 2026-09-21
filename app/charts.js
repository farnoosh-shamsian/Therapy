/* Hand-rolled SVG. No chart library. */

const NS = 'http://www.w3.org/2000/svg';

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function zahl(n, stellen = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '–';
  return Number(n).toLocaleString('en-GB', {
    minimumFractionDigits: 0, maximumFractionDigits: stellen,
  });
}

export function prozent(n, stellen = 0) {
  if (n === null || n === undefined || Number.isNaN(n)) return '–';
  return (n * 100).toLocaleString('en-GB', {
    minimumFractionDigits: stellen, maximumFractionDigits: stellen,
  }) + '%';
}

export { zahl };

/* ------------------------------------------------------------------ */
/* Line chart across sessions. */
/* ------------------------------------------------------------------ */

/* @param {number[]} werte @param {number[]} nummern session numbers for the x axis @param {object} opt { hoehe, breite, wechselpunkte, glatt, klickbar } */
export function verlauf(werte, nummern, opt = {}) {
  const B = opt.breite ?? 560;
  const H = opt.hoehe ?? 150;
  const pad = { l: 42, r: 12, o: 14, u: 26 };
  if (!werte || werte.length === 0) return leer(B, H, 'No data');

  const min = Math.min(...werte);
  const max = Math.max(...werte);
  const spanne = (max - min) || 1;
  // Air above and below the extremes.
  const y0 = min - spanne * 0.12;
  const y1 = max + spanne * 0.12;

  const px = (i) => pad.l + (i * (B - pad.l - pad.r)) / Math.max(1, werte.length - 1);
  const py = (v) => H - pad.u - ((v - y0) / (y1 - y0)) * (H - pad.o - pad.u);

  const punkte = werte.map((v, i) => `${px(i)},${py(v)}`).join(' ');
  const flaeche = `${pad.l},${H - pad.u} ${punkte} ${px(werte.length - 1)},${H - pad.u}`;

  let teile = [`<svg class="chart" viewBox="0 0 ${B} ${H}" role="img" aria-label="Trajectory across sessions">`];

  // Grid behind the line.
  for (const v of [min, max]) {
    teile.push(`<line class="gitter" x1="${pad.l}" y1="${py(v)}" x2="${B - pad.r}" y2="${py(v)}"/>`);
    teile.push(`<text class="achse" x="${pad.l - 6}" y="${py(v) + 3}" text-anchor="end">${esc(zahl(v, 2))}</text>`);
  }

  // Changepoints behind the line, as rules.
  for (const wp of opt.wechselpunkte ?? []) {
    const i = wp.position;
    if (i < 0 || i >= werte.length) continue;
    const x = px(i);
    teile.push(`<line class="wechsel" x1="${x}" y1="${pad.o}" x2="${x}" y2="${H - pad.u}"/>`);
    teile.push(`<text class="wechsel-text" x="${x + 4}" y="${pad.o + 10}">S${esc(wp.sitzung ?? i + 1)}</text>`);
  }

  teile.push(`<polygon class="verlauf-flaeche" points="${flaeche}"/>`);
  if (opt.glatt && opt.glatt.length === werte.length) {
    const g = opt.glatt.map((v, i) => `${px(i)},${py(v)}`).join(' ');
    teile.push(`<polyline class="verlauf-glatt" points="${g}"/>`);
  }
  teile.push(`<polyline class="verlauf-linie" points="${punkte}"/>`);

  werte.forEach((v, i) => {
    const attrs = opt.klickbar
      ? ` class="punkt klickbar" tabindex="0" role="button" data-sitzung="${esc(nummern[i] ?? i + 1)}" data-index="${i}"`
      : ' class="punkt"';
    teile.push(`<circle${attrs} cx="${px(i)}" cy="${py(v)}" r="3.5"><title>Session ${esc(nummern[i] ?? i + 1)}: ${esc(zahl(v, 3))}</title></circle>`);
  });

  // x axis: session numbers.
  const schritt = Math.max(1, Math.ceil(werte.length / 8));
  nummern.forEach((nr, i) => {
    if (i % schritt !== 0 && i !== werte.length - 1) return;
    teile.push(`<text class="achse" x="${px(i)}" y="${H - 8}" text-anchor="middle">${esc(nr)}</text>`);
  });

  teile.push('</svg>');
  return teile.join('');
}

/* ------------------------------------------------------------------ */
/* Sparkline. */
/* ------------------------------------------------------------------ */

export function sparkline(werte, opt = {}) {
  const B = opt.breite ?? 120, H = opt.hoehe ?? 28;
  if (!werte || werte.length < 2) return leer(B, H, '');
  const min = Math.min(...werte), max = Math.max(...werte);
  const spanne = (max - min) || 1;
  const px = (i) => (i * (B - 4)) / (werte.length - 1) + 2;
  const py = (v) => H - 3 - ((v - min) / spanne) * (H - 6);
  const punkte = werte.map((v, i) => `${px(i)},${py(v)}`).join(' ');
  const letzte = werte[werte.length - 1];
  return `<svg class="spark" viewBox="0 0 ${B} ${H}" aria-hidden="true">
    <polyline class="spark-linie" points="${punkte}"/>
    <circle class="spark-ende" cx="${px(werte.length - 1)}" cy="${py(letzte)}" r="2.5"/>
  </svg>`;
}

/* ------------------------------------------------------------------ */
/* Bars. */
/* ------------------------------------------------------------------ */

/* @param {{label:string, wert:number, zusatz?:string, schluessel?:string}[]} zeilen */
export function balken(zeilen, opt = {}) {
  if (!zeilen.length) return '<p class="leer">Nothing to show.</p>';
  const max = opt.max ?? Math.max(...zeilen.map((z) => Math.abs(z.wert)), 1e-9);
  const formatiere = opt.format ?? ((v) => zahl(v, 2));
  return `<div class="balken">${zeilen.map((z) => {
    const anteil = Math.abs(z.wert) / max;
    const klick = z.schluessel
      ? ` class="balken-zeile klickbar" tabindex="0" role="button" data-marker="${esc(z.schluessel)}"`
      : ' class="balken-zeile"';
    return `<div${klick}>
      <span class="balken-label">${esc(z.label)}</span>
      <span class="balken-spur"><span class="balken-fuell" style="width:${(anteil * 100).toFixed(1)}%"></span></span>
      <span class="balken-wert">${esc(formatiere(z.wert))}${z.zusatz ? ` <em>${esc(z.zusatz)}</em>` : ''}</span>
    </div>`;
  }).join('')}</div>`;
}

/* ------------------------------------------------------------------ */
/* Share bar (two or more parts). */
/* ------------------------------------------------------------------ */

export function anteile(teile, opt = {}) {
  const summe = teile.reduce((a, t) => a + t.wert, 0) || 1;
  const B = opt.breite ?? 560, H = opt.hoehe ?? 22;
  let x = 0;
  const stuecke = teile.map((t, i) => {
    const w = (t.wert / summe) * B;
    const rect = `<rect class="anteil f${i % 8}" x="${x}" y="0" width="${Math.max(0, w - 1)}" height="${H}" rx="2">
      <title>${esc(t.label)}: ${esc(prozent(t.wert / summe, 1))}</title></rect>`;
    x += w;
    return rect;
  }).join('');
  const legende = teile.map((t, i) =>
    `<span class="legende-eintrag"><i class="punkt-f f${i % 8}"></i>${esc(t.label)} <b>${esc(prozent(t.wert / summe))}</b></span>`
  ).join('');
  return `<svg class="anteilsbalken" viewBox="0 0 ${B} ${H}" preserveAspectRatio="none">${stuecke}</svg>
          <div class="legende">${legende}</div>`;
}

/* ------------------------------------------------------------------ */
/* Affect through one session. */
/* ------------------------------------------------------------------ */

/* @param {[number,number,number][]} punkte [turnIndex, words, affectRate] */
export function sitzungsverlauf(punkte, opt = {}) {
  const B = opt.breite ?? 560, H = opt.hoehe ?? 120;
  const pad = { l: 34, r: 10, o: 12, u: 22 };
  if (!punkte.length) return leer(B, H, 'Too little client speech to plot');
  const maxTurn = Math.max(...punkte.map((p) => p[0])) || 1;
  const maxRate = Math.max(...punkte.map((p) => p[2]), 1);
  const maxW = Math.max(...punkte.map((p) => p[1]), 1);
  const px = (t) => pad.l + (t / maxTurn) * (B - pad.l - pad.r);
  const py = (r) => H - pad.u - (r / maxRate) * (H - pad.o - pad.u);

  const kreise = punkte.map(([t, w, r]) =>
    `<circle class="punkt klickbar" tabindex="0" role="button" data-turn="${t}"
       cx="${px(t).toFixed(1)}" cy="${py(r).toFixed(1)}"
       r="${(2 + 5 * Math.sqrt(w / maxW)).toFixed(1)}">
       <title>Turn ${t}: ${w} words, ${zahl(r, 1)} feeling words per 1000</title></circle>`).join('');

  return `<svg class="chart" viewBox="0 0 ${B} ${H}" role="img" aria-label="Affect through the session">
    <line class="gitter" x1="${pad.l}" y1="${H - pad.u}" x2="${B - pad.r}" y2="${H - pad.u}"/>
    <text class="achse" x="${pad.l - 6}" y="${pad.o + 8}" text-anchor="end">${esc(zahl(maxRate, 0))}</text>
    ${kreise}
    <text class="achse" x="${pad.l}" y="${H - 6}">start</text>
    <text class="achse" x="${B - pad.r}" y="${H - 6}" text-anchor="end">end</text>
  </svg>`;
}

/* ------------------------------------------------------------------ */
/* Sociogram. */
/* ------------------------------------------------------------------ */

/* Force-directed layout, deterministic. */
export function soziogramm(knoten, kanten, opt = {}) {
  const B = opt.breite ?? 560, H = opt.hoehe ?? 360;
  if (!knoten.length) return leer(B, H, 'No people detected');

  const n = knoten.length;
  const maxN = Math.max(...knoten.map((k) => k.nennungen), 1);
  const pos = knoten.map((k, i) => ({
    x: B / 2 + Math.cos((2 * Math.PI * i) / n) * (B / 3.4),
    y: H / 2 + Math.sin((2 * Math.PI * i) / n) * (H / 3.2),
    r: 6 + 14 * Math.sqrt(k.nennungen / maxN),
    k,
  }));
  const index = new Map(knoten.map((k, i) => [k.name, i]));

  for (let runde = 0; runde < 120; runde++) {
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = pos[j].x - pos[i].x, dy = pos[j].y - pos[i].y;
        const d = Math.hypot(dx, dy) || 0.01;
        const abstossung = 2600 / (d * d);
        pos[i].x -= (dx / d) * abstossung; pos[i].y -= (dy / d) * abstossung;
        pos[j].x += (dx / d) * abstossung; pos[j].y += (dy / d) * abstossung;
      }
    }
    for (const kante of kanten) {
      const a = index.get(kante.a), b = index.get(kante.b);
      if (a === undefined || b === undefined) continue;
      const dx = pos[b].x - pos[a].x, dy = pos[b].y - pos[a].y;
      const d = Math.hypot(dx, dy) || 0.01;
      const zug = (d - 90) * 0.012 * Math.min(1, kante.gewicht / 6);
      pos[a].x += (dx / d) * zug; pos[a].y += (dy / d) * zug;
      pos[b].x -= (dx / d) * zug; pos[b].y -= (dy / d) * zug;
    }
    for (const p of pos) {
      p.x = Math.max(p.r + 40, Math.min(B - p.r - 40, p.x));
      p.y = Math.max(p.r + 12, Math.min(H - p.r - 12, p.y));
    }
  }

  const maxG = Math.max(...kanten.map((k) => k.gewicht), 1);
  const linien = kanten.map((kante) => {
    const a = index.get(kante.a), b = index.get(kante.b);
    if (a === undefined || b === undefined) return '';
    return `<line class="sozio-kante" x1="${pos[a].x.toFixed(1)}" y1="${pos[a].y.toFixed(1)}"
      x2="${pos[b].x.toFixed(1)}" y2="${pos[b].y.toFixed(1)}"
      stroke-width="${(0.6 + 2.6 * (kante.gewicht / maxG)).toFixed(2)}">
      <title>${esc(kante.a)} – ${esc(kante.b)}: named together in ${kante.gewicht} turns</title></line>`;
  }).join('');

  const kreise = pos.map((p) => `
    <g class="sozio-knoten klickbar" tabindex="0" role="button" data-person="${esc(p.k.name)}">
      <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${p.r.toFixed(1)}"
        style="fill:${temperaturfarbe(p.k.temperatur)}"/>
      <text x="${p.x.toFixed(1)}" y="${(p.y + p.r + 12).toFixed(1)}" text-anchor="middle">${esc(p.k.name)}</text>
      <title>${esc(p.k.name)} — ${p.k.nennungen} mentions, temperature ${zahl(p.k.temperatur, 2)}</title>
    </g>`).join('');

  return `<svg class="chart sozio" viewBox="0 0 ${B} ${H}" role="img" aria-label="Sociogram">${linien}${kreise}</svg>`;
}

function temperaturfarbe(t) {
  // -1 cold, 0 neutral, +1 warm.
  const v = Math.max(-1, Math.min(1, t || 0));
  if (v < 0) return `color-mix(in oklab, var(--kalt) ${Math.round(-v * 80)}%, var(--neutral))`;
  return `color-mix(in oklab, var(--warm) ${Math.round(v * 80)}%, var(--neutral))`;
}

/* ------------------------------------------------------------------ */
/* People over time (who arrives, who fades). */
/* ------------------------------------------------------------------ */

export function personenverlauf(reihen, nummern, opt = {}) {
  if (!reihen.length) return '<p class="leer">No people detected.</p>';
  const B = opt.breite ?? 560;
  const zeilenhoehe = 22;
  const H = reihen.length * zeilenhoehe + 24;
  const labelBreite = 118;
  const zellBreite = (B - labelBreite - 8) / Math.max(1, nummern.length);
  const max = Math.max(...reihen.flatMap((r) => r.werte), 1);

  const zeilen = reihen.map((r, zi) => {
    const y = zi * zeilenhoehe + 16;
    const zellen = r.werte.map((w, i) => w
      ? `<rect class="heat" x="${labelBreite + i * zellBreite}" y="${y - 10}"
           width="${Math.max(2, zellBreite - 2)}" height="14" rx="2"
           style="opacity:${(0.22 + 0.78 * (w / max)).toFixed(2)}">
           <title>${esc(r.name)}, session ${esc(nummern[i])}: ${w}×</title></rect>`
      : '').join('');
    return `<text class="heat-label" x="0" y="${y}">${esc(r.name)}</text>${zellen}`;
  }).join('');

  const achse = nummern.map((nr, i) => (i % Math.max(1, Math.ceil(nummern.length / 10)) === 0)
    ? `<text class="achse" x="${labelBreite + i * zellBreite + zellBreite / 2}" y="${H - 4}" text-anchor="middle">${esc(nr)}</text>`
    : '').join('');

  return `<svg class="chart" viewBox="0 0 ${B} ${H}" role="img" aria-label="People across sessions">${zeilen}${achse}</svg>`;
}

/* ------------------------------------------------------------------ */

function leer(B, H, text) {
  return `<svg class="chart leer-chart" viewBox="0 0 ${B} ${H}" aria-hidden="true">
    <text class="leer-text" x="${B / 2}" y="${H / 2}" text-anchor="middle">${esc(text)}</text></svg>`;
}
