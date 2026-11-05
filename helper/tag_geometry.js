// ---------- tag geometry ----------
const TAG = { w: 49.7, h: 13.7, base: 0.6, top: 1.0, textMaxW: 44, capMax: 7.0, capMin: 4.0 };
let FONT = null;
function font() {
  if (FONT || !globalThis.opentype) return FONT;
  const bin = atob(TAG_FONT_B64), buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  FONT = opentype.parse(buf.buffer); return FONT;
}
function layout(text) {
  const f = font(); if (!f || !text) return null;
  const capU = (f.tables.os2 && f.tables.os2.sCapHeight) || 0.73 * f.unitsPerEm;
  let size = TAG.capMax * f.unitsPerEm / capU;
  const width = f.getAdvanceWidth(text, size, { kerning: true });
  if (width > TAG.textMaxW) size *= TAG.textMaxW / width;
  const cap = size * capU / f.unitsPerEm;
  const w = f.getAdvanceWidth(text, size, { kerning: true });
  const path = f.getPath(text, -w / 2, cap / 2, size, { kerning: true }); // y-down, centred on the cap height
  return { path, cap, w, size, tooSmall: cap < TAG.capMin };
}
// flatten a y-down opentype path into closed y-up contours
function contours(path) {
  const out = []; let cur = [], x = 0, y = 0;
  const push = (px, py) => cur.push([px, -py]);
  for (const c of path.commands) {
    if (c.type === "M") { if (cur.length > 2) out.push(cur); cur = []; push(c.x, c.y); x = c.x; y = c.y; }
    else if (c.type === "L") { push(c.x, c.y); x = c.x; y = c.y; }
    else if (c.type === "Q") { for (let i = 1; i <= 6; i++) { const t = i / 6, u = 1 - t; push(u * u * x + 2 * u * t * c.x1 + t * t * c.x, u * u * y + 2 * u * t * c.y1 + t * t * c.y); } x = c.x; y = c.y; }
    else if (c.type === "C") { for (let i = 1; i <= 8; i++) { const t = i / 8, u = 1 - t; push(u*u*u*x + 3*u*u*t*c.x1 + 3*u*t*t*c.x2 + t*t*t*c.x, u*u*u*y + 3*u*u*t*c.y1 + 3*u*t*t*c.y2 + t*t*t*c.y); } x = c.x; y = c.y; }
    else if (c.type === "Z") { if (cur.length > 2) out.push(cur); cur = []; }
  }
  if (cur.length > 2) out.push(cur);
  return out.map(pts => {
    const q = [];
    for (const p of pts) { const l = q[q.length - 1]; if (!l || Math.hypot(l[0] - p[0], l[1] - p[1]) > 1e-4) q.push(p); }
    if (q.length > 2 && Math.hypot(q[0][0] - q[q.length - 1][0], q[0][1] - q[q.length - 1][1]) < 1e-4) q.pop();
    return q;
  }).filter(q => q.length > 2);
}
const area = pts => { let a = 0; for (let i = 0; i < pts.length; i++) { const [x1, y1] = pts[i], [x2, y2] = pts[(i + 1) % pts.length]; a += x1 * y2 - x2 * y1; } return a / 2; };
function inside(pt, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
}
// extrude text outlines from z0 to z1 -> flat array of triangles [[x,y,z]x3]
function textTriangles(text, z0, z1) {
  const L = layout(text); if (!L) return [];
  const cs = contours(L.path);
  const depth = cs.map((c, i) => cs.reduce((d, o, j) => d + (j !== i && Math.abs(area(o)) > Math.abs(area(c)) && inside(c[0], o) ? 1 : 0), 0));
  const tris = [];
  cs.forEach((c, i) => {
    if (depth[i] % 2) return;
    const outer = area(c) > 0 ? c : c.slice().reverse();
    const holes = cs.filter((h, j) => depth[j] === depth[i] + 1 && inside(h[0], c)).map(h => area(h) < 0 ? h : h.slice().reverse());
    const flat = [], holeIdx = [];
    outer.forEach(p => flat.push(p[0], p[1]));
    for (const h of holes) { holeIdx.push(flat.length / 2); h.forEach(p => flat.push(p[0], p[1])); }
    const idx = earcut(flat, holeIdx);
    const P2 = k => [flat[2 * k], flat[2 * k + 1]];
    for (let t = 0; t < idx.length; t += 3) {
      let a = P2(idx[t]), b = P2(idx[t + 1]), d = P2(idx[t + 2]);
      if (area([a, b, d]) < 0) [b, d] = [d, b];
      tris.push([[...a, z1], [...b, z1], [...d, z1]]);
      tris.push([[...a, z0], [...d, z0], [...b, z0]]);
    }
    for (const ring of [outer, ...holes]) {
      for (let k = 0; k < ring.length; k++) {
        const a = ring[k], b = ring[(k + 1) % ring.length];
        tris.push([[...a, z0], [...b, z0], [...b, z1]]);
        tris.push([[...a, z0], [...b, z1], [...a, z1]]);
      }
    }
  });
  return tris;
}
function baseTriangles(blank) {
  const m = TAG_MESH[blank ? "blank" : "base"];
  return m.f.map(f => f.map(i => m.v[i]));
}
function tagTriangles(text, dx = 0, dy = 0) {
  const t = text ? [...baseTriangles(false), ...textTriangles(text, TAG.base - 0.05, TAG.top)] : baseTriangles(true);
  return (dx || dy) ? t.map(tr => tr.map(([x, y, z]) => [x + dx, y + dy, z])) : t;
}
function stl(tris, name) {
  const buf = new ArrayBuffer(84 + tris.length * 50), dv = new DataView(buf);
  const head = (name || "hutch tag").slice(0, 79); for (let i = 0; i < head.length; i++) dv.setUint8(i, head.charCodeAt(i) & 127);
  dv.setUint32(80, tris.length, true);
  let o = 84;
  for (const [a, b, c] of tris) {
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    let n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const l = Math.hypot(...n) || 1; n = n.map(x => x / l);
    for (const x of [...n, ...a, ...b, ...c]) { dv.setFloat32(o, x, true); o += 4; }
    dv.setUint16(o, 0, true); o += 2;
  }
  return buf;
}
function plateTriangles(texts) {
  const cols = 4, px = 54, py = 18, rows = Math.ceil(texts.length / cols);
  const out = [];
  texts.forEach((t, i) => {
    const c = i % cols, r = Math.floor(i / cols);
    out.push(...tagTriangles(t, (c - (Math.min(cols, texts.length) - 1) / 2) * px, ((rows - 1) / 2 - r) * py));
  });
  return out;
}

