// Read-only use_figma script: compact fingerprint of the colors a frame uses. Set ROOT to the frame's node id.
// Returns {page, frame, nodes, colors, hash, list}; list is sorted unique hex (with @opacity%), gradient stops and IMAGE.
const ROOT = '0:0';
let node = await figma.getNodeByIdAsync(ROOT);
if (!node) return { error: 'node not found' };
let page = node; while (page && page.type !== 'PAGE') page = page.parent;
if (page && page !== figma.currentPage) { await figma.setCurrentPageAsync(page); node = await figma.getNodeByIdAsync(ROOT); }
const h2 = v => Math.round(v * 255).toString(16).padStart(2, '0').toUpperCase();
const hex = (c, a) => '#' + h2(c.r) + h2(c.g) + h2(c.b) + (a !== undefined && a < 0.999 ? '@' + Math.round(a * 100) : '');
const counts = {};
const add = k => { counts[k] = (counts[k] || 0) + 1; };
const take = paints => {
  if (!Array.isArray(paints)) return;
  for (const p of paints) {
    if (p.visible === false) continue;
    if (p.type === 'SOLID') add(hex(p.color, p.opacity));
    else if (p.type && p.type.startsWith('GRADIENT')) for (const s of p.gradientStops) add(hex(s.color, s.color.a * (p.opacity ?? 1)));
    else if (p.type === 'IMAGE') add('IMAGE');
  }
};
const nodes = [node, ...node.findAll(n => n.visible !== false)];
for (const n of nodes) { if ('fills' in n && n.fills !== figma.mixed) take(n.fills); if ('strokes' in n) take(n.strokes); }
const list = Object.keys(counts).sort();
let h = 5381; const s = list.map(k => k + ':' + counts[k]).join('|');
for (let i = 0; i < s.length; i++) h = ((h * 33) ^ s.charCodeAt(i)) >>> 0;
return { page: page.name, frame: node.name, nodes: nodes.length, colors: list.length, hash: h.toString(16), list };
