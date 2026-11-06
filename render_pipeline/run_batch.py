"""Render a batch of images, one Blender process each, and keep a restart-safe log.

  python render_pipeline/run_batch.py --only 1-20 --test 1
  python render_pipeline/run_batch.py --only 41-60 --test 3 --resume
  python render_pipeline/run_batch.py --only 10,53,120 --quality preview

Images with an entry in test_plan.json (that isn't "path": "full") use the
cached base scenes (render_cached.py); every other image is built from its
template by render.py using tools/question_images/manifest.json + sign_map.json
+ spec_overrides.json. Images listed in skips.json (or with "skip" in
test_plan.json) are not rendered.

Writes render_pipeline/out/<n>.png, out/timings.json (per image: checks,
GPU render time, wall time, or the error), out/contact_sheet_test<N>.png and
one line per finished test in out/status.log. --resume skips images already
rendered successfully in this round (ROUND), so an interrupted batch restarts
where it stopped. Never installs anything into the app.
Set BLENDER to the blender executable (default: the portable 5.2.3 install).
"""
import argparse
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.environ.get("BLENDER", r"C:\Users\parsa\Apps\blender-5.2.3-windows-x64\blender.exe")
ROUND = "2026-11-06"          # bump when a new full re-render round starts


def parse_only(s):
    want = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            want += [str(i) for i in range(int(a), int(b) + 1)]
        else:
            want.append(part)
    return want


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    line = next((l for l in p.stdout.splitlines() if l.startswith("RESULT ")), None)
    if line:
        return json.loads(line[7:]), None
    tail = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()]
    err = next((l for l in reversed(tail) if "Error" in l or l.startswith(("framing", "bare pole", "image ", "sign post",
                                                                               "overhead mounting", "square_to"))), None)
    return None, (err or "\n".join(tail[-6:]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", required=True)
    ap.add_argument("--test", default=None, help="test number, names the contact sheet and the status line")
    ap.add_argument("--quality", default="final")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    plan = {e["image"]: e for e in json.load(open(os.path.join(HERE, "test_plan.json"), encoding="utf-8"))["images"]}
    sp = os.path.join(HERE, "skips.json")
    skips = {k: v for k, v in json.load(open(sp, encoding="utf-8")).items() if not k.startswith("_")} if os.path.exists(sp) else {}
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    tpath = os.path.join(out_dir, "timings.json")
    results = json.load(open(tpath)) if os.path.exists(tpath) else {}
    todo = parse_only(args.only)
    t_batch = time.time()
    for n in todo:
        e = plan.get(n, {})
        reason = skips.get(n) or e.get("skip")
        if reason:
            results[n] = {"image": n, "round": ROUND, "skipped": reason}
            print(f"#{n}: SKIPPED - {reason}", flush=True)
            json.dump(results, open(tpath, "w"), indent=1)
            continue
        prev = results.get(n, {})
        if args.resume and prev.get("round") == ROUND and prev.get("quality") == "final" and "render_s" in prev and os.path.exists(os.path.join(out_dir, f"{n}.png")):
            print(f"#{n}: already rendered this round, skipping (resume)", flush=True)
            continue
        if e and e.get("path") != "full":
            cmd = [BLENDER, "-b", os.path.join(HERE, "scenes", e["base"] + ".blend"), "-P",
                   os.path.join(HERE, "render_cached.py"), "--", "--image", n, "--quality", args.quality]
        else:
            cmd = [BLENDER, "-b", "--factory-startup", "-P", os.path.join(HERE, "render.py"), "--",
                   "--only", n, "--quality", args.quality]
        t0 = time.time()
        r, err = run(cmd)
        wall = round(time.time() - t0, 1)
        if r is None:
            results[n] = {"image": n, "round": ROUND, "error": err, "wall_s": wall}
            print(f"#{n}: FAILED ({wall}s) - {err}", flush=True)
        else:
            r.update(round=ROUND, quality=args.quality, wall_s=wall)
            results[n] = r
            fr = r.get("framing") or {}
            print(f"#{n}: {r['base']}/{r['weather']} sign {r['sign_fraction'] or 0:.1%} centre {fr.get('centre_x', '-')} "
                  f"GPU render {r.get('gpu_render_s')}s wall {wall}s", flush=True)
        json.dump(results, open(tpath, "w"), indent=1)
    label = f"test{args.test}" if args.test else "batch"
    sheet = os.path.join(out_dir, f"contact_sheet_{label}.png")
    subprocess.run([BLENDER, "-b", "--factory-startup", "-P", os.path.join(HERE, "contact_sheet.py"), "--",
                    out_dir, ",".join(todo), sheet], capture_output=True)
    mine = [results.get(n, {}) for n in todo]
    ok = [r for r in mine if "render_s" in r and r.get("round") == ROUND and r.get("quality") == args.quality]
    gpu = sum(r.get("gpu_render_s") or 0 for r in ok)
    line = (f"{time.strftime('%Y-%m-%d %H:%M')} {label} ({args.only}): {len(ok)} rendered, "
            f"{sum(1 for r in mine if 'skipped' in r)} skipped, {sum(1 for r in mine if 'error' in r)} failed, "
            f"GPU render {gpu / 60:.1f} min, batch wall {(time.time() - t_batch) / 60:.1f} min -> {os.path.basename(sheet)}")
    with open(os.path.join(out_dir, "status.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


main()
