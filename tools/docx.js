#!/usr/bin/env node
/* CV au format Word, mis en page aux couleurs du site, à partir de data/resume.<lang>.json.
   Usage : node tools/docx.js <fr|en> <sortie.docx>      Dépendance : npm i docx */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, AlignmentType, VerticalAlign, LevelFormat, Footer, ExternalHyperlink, TableLayoutType, LineRuleType,
} = require('docx');

const [lang, out] = process.argv.slice(2);
const r = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', `resume.${lang}.json`), 'utf8'));
const b = r.basics;

const C = { purple: '84488C', deep: '5A2A62', sun: 'FFC83D', turq: '0091A6', ink: '52565F', muted: '7A7E8B', band: 'F3E9F4', lav: 'E9D7ED', paper: 'F9F6FB', white: 'FFFFFF' };
const FONT = 'Calibri';
const L = {
  fr: { now: 'Actuellement', prac: 'Pratique', path: 'Parcours', skills: 'Compétences techniques', projects: 'Projets informatiques personnels',
        work: 'Expérience', volunteer: 'Bénévolat', edu: 'Formation', langs: 'Langues', interests: 'Centres d’intérêt',
        lvl: ['Pratique', 'Initiation', 'Notions'], keys: ['pratique', 'initiation', 'notions'], present: 'aujourd’hui',
        live: 'En cours', stop: 'Interrompu', online: 'CV en ligne', sep: ' : ', months: null },
  en: { now: 'Currently', prac: 'Hands-on', path: 'Background', skills: 'Technical skills', projects: 'Personal IT projects',
        work: 'Experience', volunteer: 'Volunteering', edu: 'Education', langs: 'Languages', interests: 'Interests',
        lvl: ['Hands-on', 'Beginner', 'Basic knowledge'], keys: ['hands-on', 'beginner', 'basic'], present: 'present',
        live: 'Ongoing', stop: 'On hold', online: 'Online resume', sep: ': ',
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'] },
}[lang];

// ---------- utilitaires ----------
const W = 11906 - 2 * 1021;                       // largeur utile A4 (marges 1,8 cm) en DXA
const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none };
const cellNone = { top: none, bottom: none, left: none, right: none };
const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 21, bold: o.bold, italics: o.italics,
  color: o.color || C.ink, shading: o.bg ? { type: ShadingType.CLEAR, color: 'auto', fill: o.bg } : undefined, characterSpacing: o.cs });
const para = (children, o = {}) => new Paragraph({ children: Array.isArray(children) ? children : [children],
  alignment: o.align || AlignmentType.JUSTIFIED, spacing: { before: o.before || 0, after: o.after ?? 60, line: o.line || 276, lineRule: LineRuleType.AUTO },
  keepNext: o.keepNext, numbering: o.bullet ? { reference: 'puce', level: 0 } : undefined, indent: o.indent, border: o.border });
const fmt = (d) => { if (!d) return L.present; const p = d.split('-'); if (p.length === 1) return p[0];
  return L.months ? `${L.months[+p[1] - 1]} ${p[0]}` : `${p[1]}/${p[0]}`; };
const period = (x) => `${fmt(x.startDate)} – ${fmt(x.endDate)}`;
const cell = (children, w, o = {}) => new TableCell({ children, width: { size: w, type: WidthType.DXA },
  borders: o.borders || cellNone, shading: o.fill ? { type: ShadingType.CLEAR, color: 'auto', fill: o.fill } : undefined,
  margins: o.margins || { top: 80, bottom: 80, left: 140, right: 140 }, verticalAlign: o.v || VerticalAlign.TOP });
const table = (rows, widths) => new Table({ rows, columnWidths: widths, width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA },
  borders: noBorders, layout: TableLayoutType.FIXED });
const heading = (text) => para(run(text, { size: 30, bold: true, color: C.purple }), { align: AlignmentType.LEFT, before: 220, after: 110, keepNext: true,
  border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: C.sun, space: 4 } } });
const bullets = (items) => items.map((t) => para(run(t), { bullet: true, after: 40 }));
const spacer = (after = 60) => para(run(''), { after });

// ---------- en-tête ----------
const [first, ...rest] = b.name.split(' ');
const contact = [`${b.location.city} – ${b.location.region}`, b.phone, b.email, b.profiles[0].url.replace('https://', '')];
const header = table([new TableRow({ children: [cell([
  para(run(first, { size: 56, bold: true, color: C.white }), { align: AlignmentType.LEFT, after: 0, line: 228 }),
  para(run(rest.join(' ').toUpperCase(), { size: 56, bold: true, color: C.white, cs: 20 }), { align: AlignmentType.LEFT, after: 200, line: 228 }),
  para(run(`  ${b.label}  `, { size: 24, bold: true, color: C.ink, bg: C.sun }), { align: AlignmentType.LEFT, after: 160 }),
  para(contact.map((t, i) => run((i ? '   ·   ' : '') + t, { size: 19, color: C.white })), { align: AlignmentType.LEFT, after: 40 }),
  para(new ExternalHyperlink({ link: b.url, children: [run(`${L.online} : ${b.url}`.replace(' :', lang === 'en' ? ':' : ' :'), { size: 19, color: C.sun, bold: true })] }),
    { align: AlignmentType.LEFT, after: 0 }),
], W, { fill: C.purple, margins: { top: 360, bottom: 300, left: 400, right: 400 } })] })], [W]);

// ---------- profil ----------
const sentences = b.summary.split(/(?<=\.)\s+/);
const lede = sentences[0], goal = sentences[sentences.length - 1], middle = sentences.slice(1, -1);
const cardTexts = [middle[0] || '', middle.slice(1).join(' '), ''];
const e0 = r.education[0];
const proj = `${e0.studyType}, ${e0.institution}${L.sep}${e0.area}. ` + r.projects.filter((p) => /\((en cours|ongoing)\)/i.test(p.description || '')).map((p) => p.name).join(' ; ') + '.';
const card = (tag, text, w) => cell([
  para(run(` ${tag} `, { size: 17, bold: true, bg: C.sun }), { align: AlignmentType.LEFT, after: 100 }),
  para(run(text, { size: 19 }), { align: AlignmentType.LEFT, after: 0 }),
], w, { fill: C.white, borders: { top: { style: BorderStyle.SINGLE, size: 24, color: C.turq }, bottom: { style: BorderStyle.SINGLE, size: 4, color: 'E6E1EC' },
  left: { style: BorderStyle.SINGLE, size: 4, color: 'E6E1EC' }, right: { style: BorderStyle.SINGLE, size: 4, color: 'E6E1EC' } },
  margins: { top: 140, bottom: 160, left: 160, right: 160 } });
const gap = 160, cw = Math.floor((W - 2 * gap) / 3);
const cards = table([new TableRow({ children: [
  card(L.now, proj, cw), cell([para(run(''))], gap, { margins: { top: 0, bottom: 0, left: 0, right: 0 } }),
  card(L.prac, cardTexts[0], cw), cell([para(run(''))], gap, { margins: { top: 0, bottom: 0, left: 0, right: 0 } }),
  card(L.path, cardTexts[1], W - 2 * cw - 2 * gap),
] })], [cw, gap, cw, gap, W - 2 * cw - 2 * gap]);
const goalBox = table([new TableRow({ children: [cell([para(run(goal, { size: 23, bold: true, color: C.white }), { align: AlignmentType.LEFT, after: 0 })], W,
  { fill: C.purple, borders: { ...cellNone, left: { style: BorderStyle.SINGLE, size: 48, color: C.sun } }, margins: { top: 180, bottom: 180, left: 260, right: 260 } })] })], [W]);

// ---------- compétences ----------
const level = (k) => { const m = k.match(/\(([^)]*)\)\s*$/); const lv = m ? m[1].toLowerCase() : '';
  let i = L.keys.findIndex((x) => lv.startsWith(x)); if (i < 0 && /^(bon|good)/.test(lv)) i = 0; return { name: m ? k.slice(0, m.index).trim() : k, i: i < 0 ? 2 : i }; };
const pill = (name, i) => i === 0 ? run(` ${name} `, { size: 19, bold: true, color: C.white, bg: C.purple })
  : i === 1 ? run(` ${name} `, { size: 19, bold: true, color: C.purple, bg: C.lav })
  : run(` ${name} `, { size: 19, italics: true, color: C.muted });
const legend = para(L.lvl.map((t, i) => [pill(t, i), run('   ')]).flat(), { align: AlignmentType.LEFT, after: 120 });
const kw = 2600;
const skillRows = r.skills.map((s) => new TableRow({ cantSplit: true, children: [
  cell([para(run(s.name, { size: 19, bold: true, color: C.ink }), { align: AlignmentType.LEFT, after: 0 })], kw, { fill: C.lav, v: VerticalAlign.CENTER }),
  cell([para(s.keywords.map(level).map((x, j) => [j ? run('  ') : null, pill(x.name, x.i)]).flat().filter(Boolean), { align: AlignmentType.LEFT, after: 0, line: 320 })],
    W - kw, { fill: C.band, v: VerticalAlign.CENTER }),
] }));
const skills = new Table({ rows: skillRows, columnWidths: [kw, W - kw], width: { size: W, type: WidthType.DXA }, layout: TableLayoutType.FIXED,
  borders: { ...noBorders, insideHorizontal: { style: BorderStyle.SINGLE, size: 24, color: C.white } } });

// ---------- blocs datés (projets, expérience, bénévolat, formation) ----------
const dw = 2000;
function dated(left, title, sub, items, accent) {
  return new TableRow({ cantSplit: true, children: [
    cell(left, dw, { borders: { ...cellNone, left: { style: BorderStyle.SINGLE, size: 24, color: accent || C.turq } }, margins: { top: 70, bottom: 70, left: 160, right: 100 } }),
    cell([
      para(run(title, { size: 22, bold: true, color: C.deep }), { align: AlignmentType.LEFT, after: sub ? 20 : 60, keepNext: true }),
      ...(sub ? [para(run(sub, { size: 19, italics: true, color: C.muted }), { align: AlignmentType.LEFT, after: 60 })] : []),
      ...bullets(items || []),
    ], W - dw, { margins: { top: 70, bottom: 70, left: 160, right: 60 } }),
  ] });
}
const dates = (a, bb) => [para(run(a, { size: 19, bold: true, color: C.purple }), { align: AlignmentType.LEFT, after: 0 }),
  ...(bb ? [para(run(bb, { size: 17, color: C.muted }), { align: AlignmentType.LEFT, after: 0 })] : [])];
const block = (rows) => new Table({ rows, columnWidths: [dw, W - dw], width: { size: W, type: WidthType.DXA }, layout: TableLayoutType.FIXED,
  borders: { ...noBorders, insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: 'E6E1EC' } } });

const projects = block(r.projects.map((p) => {
  const live = /\((en cours|ongoing)\)/i.test(p.description || '');
  const desc = (p.description || '').replace(/\s*\((en cours|ongoing|interrompu|on hold)\)\.?/i, '').replace(/\.$/, '');
  return dated([para(run(p.startDate, { size: 32, bold: true, color: C.deep }), { align: AlignmentType.LEFT, after: 60 }),
    para(run(` ${live ? L.live : L.stop} `, { size: 16, bold: true, color: live ? C.ink : C.muted, bg: live ? C.sun : C.band }), { align: AlignmentType.LEFT, after: 0 })],
  p.name, desc, p.highlights, live ? C.turq : C.muted);
}));
const isMinor = (w) => !w.highlights || !w.highlights.length;
const job = (w) => dated(dates(fmt(w.startDate), w.endDate ? fmt(w.endDate) : L.present),
  `${w.position}${lang === 'fr' ? ', ' : ', '}${w.name}${w.location ? ` (${w.location})` : ''}`, w.summary, w.highlights, C.purple);
const vol = r.volunteer.map((v) => dated(dates(fmt(v.startDate), v.endDate ? fmt(v.endDate) : L.present), `${v.position}, ${v.organization}`, null, v.highlights, 'E07A5F'));
const work = block([...vol, ...r.work.filter((w) => !isMinor(w) || w.summary).map(job)]);
const earlier = r.work.filter((w) => isMinor(w) && !w.summary).map((w) =>
  para([run(`${period(w)}   `, { size: 19, bold: true, color: C.purple }), run(`${w.position}, ${w.name}${w.location ? ` (${w.location})` : ''}`, { size: 19 })],
    { align: AlignmentType.LEFT, after: 40 }));
const edu = block(r.education.map((e) => dated(dates(e.endDate ? `${fmt(e.startDate)} – ${fmt(e.endDate)}` : fmt(e.startDate)),
  `${e.studyType} – ${e.area}`, e.institution, e.courses, C.sun)));

const langs = r.languages.map((l) => para([run(l.language, { bold: true, color: C.deep }), run(`${L.sep}${l.fluency}`)], { align: AlignmentType.LEFT, after: 40 }));
const interests = para([run(L.interests, { bold: true, color: C.deep }), run(`${L.sep}${r.interests.map((i) => i.name).join(', ')}`)], { align: AlignmentType.LEFT, after: 0 });

const doc = new Document({
  creator: b.name, title: `${b.name} – ${b.label}`, description: b.summary, lastModifiedBy: b.name,
  styles: { default: { document: { run: { font: FONT, size: 21, color: C.ink } } } },
  numbering: { config: [{ reference: 'puce', levels: [{ level: 0, format: LevelFormat.BULLET, text: '▸', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 300, hanging: 240 } }, run: { color: C.turq } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 900, bottom: 900, left: 1021, right: 1021, footer: 400 } } },
    footers: { default: new Footer({ children: [para(run(`${b.name} · ${b.email} · ${b.url}`, { size: 16, color: C.muted }), { align: AlignmentType.CENTER, after: 0 })] }) },
    children: [
      header, spacer(160),
      para(run(lede, { size: 30, bold: true, color: C.ink }), { align: AlignmentType.LEFT, after: 200, line: 260 }),
      cards, spacer(140), goalBox,
      heading(L.skills), legend, skills,
      heading(L.projects), projects,
      heading(L.work), work, ...(earlier.length ? [spacer(80), ...earlier] : []),
      heading(L.edu), edu,
      heading(L.langs), ...langs, interests,
    ],
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log('docx →', out); });
