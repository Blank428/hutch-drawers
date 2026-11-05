"""Build every Bambu Studio project (.3mf) for the hutch drawers with Bambu Studio's own CLI,
then re-open and slice each one to verify it and record Bambu's grams and print time.

Output: /home/claude/hutch-drawers/projects/... and manifest.json
"""
import json, os, shutil, subprocess, sys, tempfile
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(__file__))
import profiles as pr

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/claude/hutch-drawers"
RUN = "/tmp/claude-0/-home-claude/20827e43-d651-539b-a417-716e5ce789ba/scratchpad/bs/run.sh"
V2 = "/home/claude/deliver/hutch_drawers_v2"
V3 = "/home/claude/deliver/hutch_drawers_v3_update"
CFG = os.path.join(HERE, "cfg"); os.makedirs(CFG, exist_ok=True)
WORK = os.path.join(HERE, "work"); os.makedirs(WORK, exist_ok=True)

BED = "Textured PEI Plate"
# ---------------------------------------------------------------- presets
def preset(kind, sysname, fname, **over):
    d = pr.flat(kind, sysname); d.update(over)
    d["name"] = sysname; d["from"] = "system" if kind == "machine" else "User"
    if kind != "machine": d["inherits"] = sysname
    p = os.path.join(CFG, fname); json.dump(d, open(p, "w"), indent=1); return p

MACHINE = preset("machine", "Bambu Lab A1 0.4 nozzle", "machine.json")
PROC = {
    "std": preset("process", "0.20mm Standard @BBL A1", "proc_std.json", wall_loops="3", curr_bed_type=BED),
    "tall": preset("process", "0.20mm Standard @BBL A1", "proc_tall.json", wall_loops="3", brim_type="outer_only", brim_width="5", curr_bed_type=BED),
    "latch": preset("process", "0.20mm Standard @BBL A1", "proc_latch.json", wall_loops="3", brim_type="outer_only", brim_width="3", curr_bed_type=BED),
    "tpu": preset("process", "0.20mm Standard @BBL A1", "proc_tpu.json", curr_bed_type=BED),
}
FIL = {
    "black": preset("filament", "Bambu PLA Basic @BBL A1", "pla_black.json", filament_colour=["#1F2120"]),
    "sage": preset("filament", "Bambu PLA Basic @BBL A1", "pla_sage.json", filament_colour=["#8FA382"]),
    "petg": preset("filament", "Bambu PETG HF @BBL A1", "petg.json", filament_colour=["#2B2D2C"]),
    "tpu": preset("filament", "Bambu TPU 95A HF @BBL A1", "tpu.json", filament_colour=["#2B2D2C"]),
}

# ---------------------------------------------------------------- jobs
def stl_rotated(src, deg):
    """Copy of an STL turned about Z (frames: long side front to back on the A1's moving bed)."""
    if not deg: return src
    out = os.path.join(WORK, f"rot{deg}_" + os.path.basename(src))
    m = trimesh.load(src, force="mesh", process=False)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(deg), [0, 0, 1]))
    m.export(out); return out

FS, FP, LA, TP, FT = f"{V2}/2_full_set", f"{V3}/2_faceplates_v3", f"{V3}/1_latches", f"{V2}/3_tpu_parts", f"{V2}/1_fit_test_print_first"
H = [("128", "128mm"), ("66", "66mm"), ("74", "74mm"), ("71", "71mm"), ("89-5", "89.5mm")]
FACES = {"128": [("black", 2)], "66": [("black", 2), ("sage", 2)], "74": [("black", 6)], "71": [("sage", 4)], "89-5": [("sage", 2)]}

jobs = []  # (key, project path, [stl, ...], proc, filament, rotate, title)
def job(key, path, stl, n, proc, fil, rot=0, title=""):
    jobs.append(dict(key=key, path=path, stls=[stl] * n, proc=proc, fil=fil, rot=rot, title=title or key))

job("fit_frame", "fit-test/fit_frame.3mf", f"{FT}/fit_frame_x1_black.stl", 1, "tall", "black", 90, "Fit-test frame")
job("fit_drawer", "fit-test/fit_drawer.3mf", f"{FT}/fit_drawer_x1_black.stl", 1, "std", "black", 0, "Fit-test drawer")
job("fit_face_black", "fit-test/fit_faceplate_black.3mf", f"{FP}/fit_test_faceplate_x1.stl", 1, "std", "black", 0, "Fit-test faceplate, black")
job("fit_face_sage", "fit-test/fit_faceplate_sage.3mf", f"{FP}/fit_test_faceplate_x1.stl", 1, "std", "sage", 0, "Fit-test faceplate, sage")
for name, fn in (("test_row_right", "latch_v3_test_row_x4_right"), ("test_row_left", "latch_v3_test_row_x4_left"),
                 ("row_right", "latch_v3_row_x19_right"), ("row_left", "latch_v3_row_x19_left"),
                 ("soft_test_row_right", "latch_v3_soft_test_row_x4_right"), ("soft_test_row_left", "latch_v3_soft_test_row_x4_left"),
                 ("firm_test_row_right", "latch_v3_firm_test_row_x4_right"), ("firm_test_row_left", "latch_v3_firm_test_row_x4_left")):
    job(f"latch_{name}", f"latches/latch_{name}.3mf", f"{LA}/{fn}.stl", 1, "latch", "petg", 0, "Latch " + name.replace("_", " "))
import glob
for hk, hs in H:
    fr = glob.glob(f"{FS}/{hs}_frame_x*_black.stl")[0]; dr = glob.glob(f"{FS}/{hs}_drawer_x*_black.stl")[0]
    job(f"frame_{hk}", f"modules-{hk}mm/frame_{hk}mm.3mf", fr, 1, "tall", "black", 90, f"{hs} frame")
    job(f"drawer_{hk}", f"modules-{hk}mm/drawer_{hk}mm.3mf", dr, 1, "std", "black", 0, f"{hs} drawer")
    for colour, qty in FACES[hk]:
        f = glob.glob(f"{FP}/{hs}_faceplate_x*_{colour}.stl")[0]
        job(f"face_{hk}_{colour}_x1", f"modules-{hk}mm/faceplate_{hk}mm_{colour}_x1.3mf", f, 1, "std", colour, 0, f"{hs} faceplate, {colour}, 1 per plate")
        n = min(qty, 3)
        if n > 1:
            job(f"face_{hk}_{colour}_x{n}", f"modules-{hk}mm/faceplate_{hk}mm_{colour}_x{n}.3mf", f, n, "std", colour, 0, f"{hs} faceplate, {colour}, {n} per plate")
job("pads", "tpu/foot_pads_x32.3mf", f"{TP}/foot_pad_x32_tpu.stl", 32, "tpu", "tpu", 0, "Foot pads, 32")
job("sp30", "tpu/top_spacers_3-0mm_x24.3mf", f"{TP}/top_spacer_3.0mm_x24_tpu.stl", 24, "tpu", "tpu", 0, "Top spacers 3.0 mm, 24")
job("sp35", "tpu/top_spacers_3-5mm_x8.3mf", f"{TP}/top_spacer_3.5mm_x8_tpu.stl", 8, "tpu", "tpu", 0, "Top spacers 3.5 mm, 8")

# ---------------------------------------------------------------- run
def bs(args, log):
    cmd = [RUN, "env", "LC_ALL=C.UTF-8", "/app/bin/bambu-studio", "--debug", "1"] + args
    r = subprocess.run(cmd, stdout=open(log, "w"), stderr=subprocess.STDOUT, timeout=900)
    return r.returncode

manifest = {}
only = set(sys.argv[1:])
for j in jobs:
    if only and j["key"] not in only: continue
    out = os.path.join(REPO, "projects", j["path"]); os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = tempfile.mkdtemp(dir=WORK)
    stls = [stl_rotated(s, j["rot"]) for s in j["stls"]]
    rc = bs(["--load-settings", f"{MACHINE};{PROC[j['proc']]}", "--load-filaments", FIL[j["fil"]],
             "--arrange", "1", "--orient", "0", "--export-3mf", "project.3mf", "--outputdir", tmp] + stls, os.path.join(tmp, "export.log"))
    if rc != 0 or not os.path.exists(f"{tmp}/project.3mf"):
        print("EXPORT FAILED", j["key"], rc, open(f"{tmp}/export.log").read()[-800:]); continue
    shutil.copy(f"{tmp}/project.3mf", out)
    # verify: reopen the saved project on its own and slice it
    rc = bs(["--slice", "0", "--outputdir", f"{tmp}/slice", out], os.path.join(tmp, "slice.log"))
    res = json.load(open(f"{tmp}/slice/result.json"))
    if res.get("return_code") != 0:
        print("SLICE FAILED", j["key"], res.get("error_string")); continue
    plates = res["sliced_plates"]
    g = sum(f["main_used_g"] for p in plates for f in p["filaments"]); t = sum(p["total_predication"] for p in plates)
    objs = sum(len(p["objects"]) for p in plates)
    manifest[j["key"]] = dict(path=f"projects/{j['path']}", title=j["title"], plates=len(plates), objects=objs, grams=round(g, 1), minutes=round(t / 60, 1),
                              filament=j["fil"], warning=" ".join(p.get("warning_message", "") for p in plates).strip())
    print(f"{j['key']:28s} plates {len(plates)} objects {objs:2d}  {g:7.1f} g  {t/3600:5.2f} h  {manifest[j['key']]['warning']}")
    shutil.rmtree(tmp, ignore_errors=True)

mpath = os.path.join(REPO, "manifest.json")
old = json.load(open(mpath)) if os.path.exists(mpath) else {}
old.update(manifest); json.dump(old, open(mpath, "w"), indent=1)
print("projects:", len(old))
