#!/usr/bin/env node
// Builds one Bambu Studio project (.3mf) holding every queued label tag, ready for a Bambu Lab A1
// without an AMS. Plates are grouped by the front the tags are for:
//   black fronts: black base, sage text     sage fronts: sage base, black text
// Each plate has a pause at 0.8 mm, the first text layer, so you can swap filament mid print.
//
// usage: node labels.js '<json>' <out.3mf>
//   json = {"tags":[{"text":"CABLES","colour":"black"}, ...]}
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const HERE = __dirname;

globalThis.opentype = require(path.join(HERE, "vendor/opentype.min.js"));
globalThis.earcut = require(path.join(HERE, "vendor/earcut.min.js"));
const JSZip = require(path.join(HERE, "vendor/jszip.min.js"));
if (typeof globalThis.atob !== "function") globalThis.atob = s => Buffer.from(s, "base64").toString("binary");
vm.runInThisContext(fs.readFileSync(path.join(HERE, "tagdata.js"), "utf8") + "\nglobalThis.TAG_MESH = TAG_MESH; globalThis.TAG_FONT_B64 = TAG_FONT_B64;");
vm.runInThisContext(fs.readFileSync(path.join(HERE, "tag_geometry.js"), "utf8") + "\nglobalThis.tagTriangles = tagTriangles; globalThis.layout = layout; globalThis.TAG = TAG;");

const BED = 256, STRIDE = BED * 1.2;          // A1 bed, and Bambu's gap between plates in a project
const COLS = 4, PX = 54, PY = 18, ROWS = 13;  // 52 tags per plate
const PER_PLATE = COLS * ROWS;
const PAUSE_Z = 0.8;                          // top of the first text layer at 0.2 mm layers
const SETTINGS = fs.readFileSync(path.join(HERE, "template/project_settings.config"), "utf8");

const clean = s => String(s || "").toUpperCase().replace(/[^A-Z0-9 &+\-./#]/g, "").replace(/\s+/g, " ").trim().slice(0, 12);
const colsFor = n => { const v = Math.sqrt(n), r = Math.round(v); return v > r ? r + 1 : r; };
const uuid = (a, b) => `${String(a).padStart(8, "0")}-61cb-4c03-9d28-${String(b).padStart(12, "0")}`;
const esc = s => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

function plateMesh(texts) {
  const rows = Math.ceil(texts.length / COLS), cols = Math.min(COLS, texts.length);
  const tris = [];
  texts.forEach((t, i) => {
    const c = i % COLS, r = Math.floor(i / COLS);
    for (const tr of tagTriangles(t, (c - (cols - 1) / 2) * PX, ((rows - 1) / 2 - r) * PY)) tris.push(tr);
  });
  const key = v => v.map(x => x.toFixed(4)).join(","), index = new Map(), verts = [], faces = [];
  for (const tr of tris) {
    const f = tr.map(v => { const k = key(v); let i = index.get(k); if (i === undefined) { i = verts.length; index.set(k, i); verts.push(v); } return i; });
    if (f[0] !== f[1] && f[1] !== f[2] && f[0] !== f[2]) faces.push(f);
  }
  return { verts, faces };
}

function objectModel(id, mesh) {
  const v = mesh.verts.map(([x, y, z]) => `     <vertex x="${+x.toFixed(5)}" y="${+y.toFixed(5)}" z="${+z.toFixed(5)}"/>`).join("\n");
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

async function build(tags, out) {
  const groups = { black: [], sage: [] };
  for (const t of tags) { const s = clean(t.text); if (s && groups[t.colour]) groups[t.colour].push(s); }
  const plates = [];
  for (const colour of ["black", "sage"]) {
    const list = groups[colour];
    for (let i = 0; i < list.length; i += PER_PLATE) plates.push({ colour, texts: list.slice(i, i + PER_PLATE) });
  }
  if (!plates.length) throw new Error("no tags");
  const cols = colsFor(plates.length);
  const zip = new JSZip();
  const items = [], resources = [], rels = [], objCfg = [], plateCfg = [], gcodes = [], cuts = [], seq = {};
  plates.forEach((p, i) => {
    const meshId = 2 * i + 1, objId = 2 * i + 2, file = `/3D/Objects/object_${i + 1}.model`;
    const mesh = plateMesh(p.texts);
    zip.file(file.slice(1), objectModel(meshId, mesh));
    const row = Math.floor(i / cols), col = i % cols;
    const x = col * STRIDE + BED / 2, y = -row * STRIDE + BED / 2;
    const swap = p.colour === "black" ? "sage" : "black";
    const name = `${p.colour === "black" ? "Black" : "Sage"} fronts, ${p.texts.length} tags`;
    resources.push(`  <object id="${objId}" p:UUID="${uuid(objId, 2)}" type="model">
   <components>
    <component p:path="${file}" objectid="${meshId}" p:UUID="${uuid(meshId, 3)}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
   </components>
  </object>`);
    items.push(`  <item objectid="${objId}" p:UUID="${uuid(objId, 4)}" transform="1 0 0 0 1 0 0 0 1 ${x} ${y} 0" printable="1"/>`);
    rels.push(` <Relationship Target="${file}" Id="rel-${i + 1}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>`);
    objCfg.push(`  <object id="${objId}">
    <metadata key="name" value="${esc(name)}"/>
    <metadata key="extruder" value="${p.colour === "black" ? 1 : 2}"/>
    <metadata face_count="${mesh.faces.length}"/>
    <part id="${meshId}" subtype="normal_part">
      <metadata key="name" value="${esc(name)}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <mesh_stat face_count="${mesh.faces.length}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>`);
    plateCfg.push(`  <plate>
    <metadata key="plater_id" value="${i + 1}"/>
    <metadata key="plater_name" value="${esc(`${p.colour === "black" ? "Black" : "Sage"} fronts: ${p.colour} base, swap to ${swap} at the pause`)}"/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="gcode_file" value=""/>
    <model_instance>
      <metadata key="object_id" value="${objId}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="${100 + i}"/>
    </model_instance>
  </plate>`);
    gcodes.push(`<plate>
<plate_info id="${i + 1}"/>
<layer top_z="${PAUSE_Z}" type="1" extruder="${p.colour === "black" ? 1 : 2}" color="" extra="" gcode="M400 U1"/>
<mode value="SingleExtruder"/>
</plate>`);
    cuts.push(` <object id="${objId}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>`);
    seq[`plate_${i + 1}`] = { nozzle_sequence: [], optimal_assignment: [], sequence: [] };
  });
  const today = new Date().toISOString().slice(0, 10);
  zip.file("3D/3dmodel.model", `<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">BambuStudio-02.08.02.61</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="CreationDate">${today}</metadata>
 <metadata name="ModificationDate">${today}</metadata>
 <metadata name="Title">Hutch drawer label tags</metadata>
 <resources>
${resources.join("\n")}
 </resources>
 <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">
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
  const buf = await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  fs.writeFileSync(out, buf);
  return plates.map(p => ({ colour: p.colour, count: p.texts.length }));
}

if (require.main === module) {
  const [json, out] = process.argv.slice(2);
  build(JSON.parse(json).tags || [], out)
    .then(p => { process.stdout.write(JSON.stringify({ ok: true, plates: p }) + "\n"); })
    .catch(e => { process.stdout.write(JSON.stringify({ ok: false, error: String(e.message || e) }) + "\n"); process.exit(1); });
}
module.exports = { build };
