#!/usr/bin/env node
// Builds one Bambu Studio project (.3mf) of plain Gridfinity bins for the hutch drawers, ready for a
// Bambu Lab A1 without an AMS. Bins are grouped onto plates by colour (black, sage), so each plate is
// a single-colour print.
//
// Bins follow the Gridfinity standard (42 mm grid, 7 mm height units, the 0.8/1.8/2.15 base profile)
// so they seat in the sockets moulded into every drawer floor. No stacking lip: nothing stacks in a
// drawer, and leaving it off gives the most room under the frame ceiling. Optional dividers split a
// bin into equal compartments.
//
// usage: node bins.js '<json>' <out.3mf>
//   json = {"bins":[{"name":"CABLES","drawer":"bay-L-1","w":2,"d":2,"u":8,"nx":1,"ny":3,"colour":"black"}, ...]}
//   w, d   footprint in grid units (42 mm)      u   height in 7 mm units (bin total height = 7u)
//   nx     compartments side to side            ny  compartments front to back
"use strict";
const fs = require("fs"), path = require("path"), { pathToFileURL } = require("url");
const HERE = __dirname;
const JSZip = require(path.join(HERE, "vendor/jszip.min.js"));

const GRID = 42, UNIT = 7, CLEAR = 0.5;            // grid pitch, height unit, total clearance per bin
const WALL = 1.2, FLOOR = 1.2, DIV = 1.2;          // wall, floor (above the base) and divider thickness
const BASE_H = 4.75, R_OUT = 3.75;                 // base profile height, outer corner radius
const BED = 256, STRIDE = BED * 1.2, MARGIN = 6, GAP = 4;
const SETTINGS = fs.readFileSync(path.join(HERE, "template/project_settings.config"), "utf8");

const uuid = (a, b) => `${String(a).padStart(8, "0")}-7b1e-4c03-9d28-${String(b).padStart(12, "0")}`;
const esc = s => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const int = (v, lo, hi, dflt) => { const n = Math.round(Number(v)); return Number.isFinite(n) ? Math.min(hi, Math.max(lo, n)) : dflt; };

let M = null;
async function manifold() {
  if (M) return M;
  const mod = await import(pathToFileURL(path.join(HERE, "vendor/manifold.js")).href);
  const wasm = await (mod.default || mod)({ locateFile: () => path.join(HERE, "vendor/manifold.wasm") });
  wasm.setup();
  M = wasm;
  return M;
}

// rounded rectangle cross-section, centred, w x d with corner radius r
function rr(w, d, r) {
  const { CrossSection } = M;
  r = Math.max(0.01, Math.min(r, w / 2 - 0.01, d / 2 - 0.01));
  return CrossSection.square([w - 2 * r, d - 2 * r], true).offset(r, "Round", 2, 32);
}
const slab = (w, d, r, z0, z1) => rr(w, d, r).extrude(z1 - z0).translate([0, 0, z0]);

function foot() {
  const { Manifold } = M, e = 0.01;
  // Gridfinity bin base: 35.6 at the bottom, +0.8 at 45 degrees, 1.8 straight, +2.15 at 45 degrees
  const lower = Manifold.hull([slab(35.6, 35.6, 0.8, 0, e), slab(37.2, 37.2, 1.6, 0.8 - e, 0.8)]);
  const mid = slab(37.2, 37.2, 1.6, 0.8 - e, 2.6 + e);
  const upper = Manifold.hull([slab(37.2, 37.2, 1.6, 2.6, 2.6 + e), slab(41.5, 41.5, R_OUT, BASE_H - e, BASE_H)]);
  return Manifold.union([lower, mid, upper]);
}

function bin(spec) {
  const { Manifold } = M;
  const w = spec.w, d = spec.d, H = spec.u * UNIT;
  const Wo = GRID * w - CLEAR, Do = GRID * d - CLEAR;
  const parts = [];
  const f = foot();
  for (let i = 0; i < w; i++) for (let j = 0; j < d; j++)
    parts.push(f.translate([(i - (w - 1) / 2) * GRID, (j - (d - 1) / 2) * GRID, 0]));
  const body = slab(Wo, Do, R_OUT, BASE_H - 0.01, H);
  const floorZ = BASE_H + FLOOR;
  const Wi = Wo - 2 * WALL, Di = Do - 2 * WALL;
  const cavity = slab(Wi, Di, R_OUT - WALL, floorZ, H + 1);
  let m = Manifold.union([...parts, body]).subtract(cavity);
  // dividers stop 1.5 mm below the rim so the bin still reads as one piece from above
  const top = H - 1.5, divs = [];
  for (let k = 1; k < spec.nx; k++) {
    const x = -Wi / 2 + (Wi * k) / spec.nx;
    divs.push(Manifold.cube([DIV, Di + 0.2, top - floorZ + 0.01]).translate([x - DIV / 2, -Di / 2 - 0.1, floorZ - 0.01]));
  }
  for (let k = 1; k < spec.ny; k++) {
    const y = -Di / 2 + (Di * k) / spec.ny;
    divs.push(Manifold.cube([Wi + 0.2, DIV, top - floorZ + 0.01]).translate([-Wi / 2 - 0.1, y - DIV / 2, floorZ - 0.01]));
  }
  if (divs.length) m = Manifold.union([m, ...divs]);
  return m;
}

function toMesh(man) {
  const mesh = man.getMesh();
  const n = mesh.numProp, vp = mesh.vertProperties, tv = mesh.triVerts;
  const verts = [], faces = [];
  for (let i = 0; i < vp.length; i += n) verts.push([vp[i], vp[i + 1], vp[i + 2]]);
  for (let i = 0; i < tv.length; i += 3) faces.push([tv[i], tv[i + 1], tv[i + 2]]);
  return { verts, faces };
}

function objectModel(id, mesh) {
  const v = mesh.verts.map(([x, y, z]) => `     <vertex x="${+x.toFixed(4)}" y="${+y.toFixed(4)}" z="${+z.toFixed(4)}"/>`).join("\n");
  const t = mesh.faces.map(([a, b, c]) => `     <triangle v1="${a}" v2="${b}" v3="${c}"/>`).join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
  <object id="${id}" p:UUID="${uuid(id, 1)}" type="model">
   <mesh>
    <vertices>
${v}
    </vertices>
    <triangles>
${t}
    </triangles>
   </mesh>
  </object>
 </resources>
 <build/>
</model>
`;
}

// Shelf packing onto 256 mm plates, tallest footprint first; bins may turn 90 degrees to fit.
function pack(items) {
  const usable = BED - 2 * MARGIN, plates = [];
  const sorted = [...items].sort((a, b) => Math.max(b.W, b.D) - Math.max(a.W, a.D));
  for (const it of sorted) {
    let placed = false;
    for (const pl of plates) if (place(pl, it)) { placed = true; break; }
    if (!placed) { const pl = { shelves: [], items: [] }; plates.push(pl); if (!place(pl, it)) throw new Error("bin too big for the bed"); }
  }
  return plates;
  function place(pl, it) {
    for (const [W, D, rot] of [[it.W, it.D, false], [it.D, it.W, true]]) {
      for (const sh of pl.shelves) if (D <= sh.h && sh.x + W <= usable) {
        pl.items.push({ ...it, x: sh.x + W / 2, y: sh.y + D / 2, rot }); sh.x += W + GAP; return true;
      }
      const yTop = pl.shelves.reduce((s, sh) => Math.max(s, sh.y + sh.h + GAP), 0);
      if (yTop + D <= usable && W <= usable) {
        pl.shelves.push({ y: yTop, h: D, x: W + GAP });
        pl.items.push({ ...it, x: W / 2, y: yTop + D / 2, rot }); return true;
      }
    }
    return false;
  }
}

function normalise(raw) {
  const out = [];
  for (const b of (raw || []).slice(0, 80)) {
    const w = int(b.w, 1, 4, 1), d = int(b.d, 1, 5, 1);
    out.push({
      name: String(b.name || "Bin").replace(/[^\w &+\-./#()]/g, "").slice(0, 40) || "Bin",
      drawer: String(b.drawer || "").replace(/[^\w\-]/g, "").slice(0, 20),
      w, d, u: int(b.u, 2, 17, 6),
      nx: int(b.nx, 1, Math.max(1, w * 4), 1), ny: int(b.ny, 1, Math.max(1, d * 4), 1),
      colour: b.colour === "sage" ? "sage" : "black",
    });
  }
  return out;
}

async function build(rawBins, out) {
  await manifold();
  const bins = normalise(rawBins);
  if (!bins.length) throw new Error("no bins");
  const plates = [];
  for (const colour of ["black", "sage"]) {
    const items = bins.filter(b => b.colour === colour).map(b => ({ ...b, W: GRID * b.w - CLEAR, D: GRID * b.d - CLEAR }));
    if (items.length) for (const p of pack(items)) plates.push({ colour, items: p.items });
  }
  const cols = Math.ceil(Math.sqrt(plates.length));
  const zip = new JSZip();
  const items = [], resources = [], rels = [], objCfg = [], plateCfg = [], gcodes = [], cuts = [], seq = {};
  let n = 0, faceTotal = 0;
  const meshCache = new Map();
  plates.forEach((pl, pi) => {
    const row = Math.floor(pi / cols), col = pi % cols;
    const ox = col * STRIDE, oy = -row * STRIDE;
    const inst = [];
    for (const b of pl.items) {
      n++;
      const meshId = 2 * n - 1, objId = 2 * n, file = `/3D/Objects/object_${n}.model`;
      const key = `${b.w}x${b.d}x${b.u}x${b.nx}x${b.ny}`;
      let mesh = meshCache.get(key);
      if (!mesh) { mesh = toMesh(bin(b)); meshCache.set(key, mesh); }
      faceTotal += mesh.faces.length;
      zip.file(file.slice(1), objectModel(meshId, mesh));
      const x = ox + MARGIN + b.x, y = oy + MARGIN + b.y;
      const m = b.rot ? "0 1 0 -1 0 0 0 0 1" : "1 0 0 0 1 0 0 0 1";
      const name = `${b.name} ${b.w}x${b.d}${b.drawer ? ` (${b.drawer})` : ""}`;
      resources.push(`  <object id="${objId}" p:UUID="${uuid(objId, 2)}" type="model">
   <components>
    <component p:path="${file}" objectid="${meshId}" p:UUID="${uuid(meshId, 3)}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
   </components>
  </object>`);
      items.push(`  <item objectid="${objId}" p:UUID="${uuid(objId, 4)}" transform="${m} ${x.toFixed(3)} ${y.toFixed(3)} 0" printable="1"/>`);
      rels.push(` <Relationship Target="${file}" Id="rel-${n}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>`);
      objCfg.push(`  <object id="${objId}">
    <metadata key="name" value="${esc(name)}"/>
    <metadata key="extruder" value="${pl.colour === "black" ? 1 : 2}"/>
    <metadata face_count="${mesh.faces.length}"/>
    <part id="${meshId}" subtype="normal_part">
      <metadata key="name" value="${esc(name)}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <mesh_stat face_count="${mesh.faces.length}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>`);
      inst.push(`    <model_instance>
      <metadata key="object_id" value="${objId}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="${100 + n}"/>
    </model_instance>`);
      cuts.push(` <object id="${objId}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>`);
    }
    plateCfg.push(`  <plate>
    <metadata key="plater_id" value="${pi + 1}"/>
    <metadata key="plater_name" value="${esc(`${pl.colour === "black" ? "Black" : "Sage"} bins, ${pl.items.length}`)}"/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="gcode_file" value=""/>
${inst.join("\n")}
  </plate>`);
    gcodes.push(`<plate>\n<plate_info id="${pi + 1}"/>\n<mode value="SingleExtruder"/>\n</plate>`);
    seq[`plate_${pi + 1}`] = { nozzle_sequence: [], optimal_assignment: [], sequence: [] };
  });
  const today = new Date().toISOString().slice(0, 10);
  zip.file("3D/3dmodel.model", `<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">BambuStudio-02.08.02.61</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="CreationDate">${today}</metadata>
 <metadata name="ModificationDate">${today}</metadata>
 <metadata name="Title">Hutch drawer Gridfinity bins</metadata>
 <resources>
${resources.join("\n")}
 </resources>
 <build p:UUID="3d8c27e9-33c6-4e95-9946-2087133fb47a">
${items.join("\n")}
 </build>
</model>
`);
  zip.file("3D/_rels/3dmodel.model.rels", `<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
${rels.join("\n")}
</Relationships>
`);
  zip.file("_rels/.rels", `<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
`);
  zip.file("[Content_Types].xml", `<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>
`);
  zip.file("Metadata/project_settings.config", SETTINGS);
  zip.file("Metadata/model_settings.config", `<?xml version="1.0" encoding="UTF-8"?>\n<config>\n${objCfg.join("\n")}\n${plateCfg.join("\n")}\n  <assemble>\n  </assemble>\n</config>\n`);
  zip.file("Metadata/custom_gcode_per_layer.xml", `<?xml version="1.0" encoding="utf-8"?>\n<custom_gcodes_per_layer>\n${gcodes.join("\n")}\n</custom_gcodes_per_layer>\n`);
  zip.file("Metadata/cut_information.xml", `<?xml version="1.0" encoding="utf-8"?>\n<objects>\n${cuts.join("\n")}\n</objects>\n`);
  zip.file("Metadata/filament_sequence.json", JSON.stringify(seq));
  zip.file("Metadata/slice_info.config", `<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n    <header_item key="X-BBL-Client-Type" value="slicer"/>\n    <header_item key="X-BBL-Client-Version" value="02.08.02.61"/>\n  </header>\n</config>\n`);
  fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  return { plates: plates.map(p => ({ colour: p.colour, count: p.items.length })), bins: bins.length, faces: faceTotal };
}

if (require.main === module) {
  const [json, out] = process.argv.slice(2);
  build(JSON.parse(json).bins || [], out)
    .then(r => { process.stdout.write(JSON.stringify({ ok: true, ...r }) + "\n"); })
    .catch(e => { process.stdout.write(JSON.stringify({ ok: false, error: String(e.message || e) }) + "\n"); process.exit(1); });
}
module.exports = { build, bin, manifold, toMesh, normalise, GRID, UNIT, CLEAR };
