"""Measured QA on a delivered reel: lip sync, one-frame flashes / black frames, loudness.

Lip sync compares rendered frames against assets/aroll.mp4 at the same frame index, using scenes whose
layout is "face" in assets/plan.json (speaker unscaled, untranslated). Best offset must be +0.

usage: python3 qa_checks.py <project-dir> <delivered.mp4>
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

if len(sys.argv) < 3:
    raise SystemExit(__doc__)
proj, video = Path(sys.argv[1]), sys.argv[2]
plan = json.loads((proj / "assets/plan.json").read_text())
fps = plan["fps"]


def frames(path, ns=None, w=270, h=480):
    vf = (f"select='{'+'.join(f'eq(n\\,{n})' for n in ns)}'," if ns else "") + f"scale={w}:{h}"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", vf, "-vsync", "0", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w).astype(float)


ok = True
face = [s for s in plan["scenes"] if s["layout"] == "face"]
print("== lip sync (face scenes vs assets/aroll.mp4; top 56% of frame, above captions)")
for s in face[:8]:
    n = round((s["start"] + s["end"]) / 2 * fps)
    r = frames(video, [n])[0][:270]
    cand = list(range(n - 3, n + 4))
    errs = [(float(np.abs(r - a[:270]).mean()), k - n) for a, k in zip(frames(proj / "assets/aroll.mp4", cand), cand)]
    best = min(errs)[1]
    ok &= best == 0
    print(f"  {s['id']:6s} frame {n:5d} ({n / fps:6.2f}s): best offset {best:+d}")

print("== flash / black-frame scan")
v = frames(video, None, 54, 96)
flags = []
for i in range(1, len(v) - 1):
    dp, dn, dpn = (np.abs(v[i] - v[i - 1]).mean(), np.abs(v[i] - v[i + 1]).mean(), np.abs(v[i - 1] - v[i + 1]).mean())
    if dp > 12 and dn > 12 and dpn < 6:
        flags.append((i, "one-frame outlier"))
    if v[i].mean() < 6:
        flags.append((i, "near-black frame"))
ok &= not flags
print(f"  {len(v)} frames; flags: {flags or 'none'}")

print("== loudness (target about -16 LUFS, true peak <= -1.0 dBTP)")
out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", out)[-1])
TP = float(re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", out)[-1])
ok &= -18 <= I <= -13 and TP <= -1.0
print(f"  integrated {I} LUFS, true peak {TP} dBTP")
print("RESULT:", "PASS" if ok else "CHECK FAILURES ABOVE")
sys.exit(0 if ok else 1)
