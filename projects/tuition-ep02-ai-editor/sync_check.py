"""Lip-sync check that models the layout transform at each frame (split shift, face/punch push-in)."""
import json, subprocess, sys
import numpy as np
from PIL import Image
proj, video = sys.argv[1], sys.argv[2]
plan = json.load(open(f"{proj}/assets/plan.json")); fps = plan["fps"]
def grabs(path, n0, count):
    # Seek just before frame n0 (first frame with pts >= t is n0), then decode `count` consecutive frames.
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{(n0 - 0.25) / fps:.4f}", "-i", path, "-frames:v", str(count),
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    return [Image.frombytes("L", (1080, 1920), raw[i * 1080 * 1920:(i + 1) * 1080 * 1920]) for i in range(count)]
def grab(path, n):
    return grabs(path, n, 1)[0]
def tf(img, scale, ty, ox=540, oy=800, inner=1.0, iox=540, ioy=820):
    # spk-push (inner scale around iox,ioy) inside spk-wrap (y=ty, scale around ox,oy)
    a = np.asarray(img).astype(float)
    ys, xs = np.mgrid[0:1920:4, 0:1080:4].astype(float)
    # invert wrap: page -> wrap local
    lx = (xs - ox) / scale + ox; ly = (ys - ty - oy) / scale + oy
    # invert push
    px = (lx - iox) / inner + iox; py = (ly - ioy) / inner + ioy
    px = np.clip(px, 0, 1079).astype(int); py = np.clip(py, 0, 1919).astype(int)
    return a[py, px]
res = []
for s in plan["scenes"]:
    lay = s["layout"]
    if lay not in ("face", "split", "broll-split", "punch"): continue
    for frac in (0.3, 0.7):
        n = round((s["start"] + (s["end"] - s["start"]) * frac) * fps)
        r = np.asarray(grab(video, n)).astype(float)[0:1920:4, 0:1080:4]
        if lay in ("split", "broll-split"):
            scale, ty, inner = 1.0, 540, 1.0; region = (slice(960//4, 1700//4), slice(200//4, 880//4))
        else:
            d = s["end"] - s["start"]; prog = (n / fps - s["start"]) / (d - 1/fps)
            scale = 1.3 if lay == "punch" else 1.0; ty = 0; inner = 1 + 0.035 * min(1, max(0, prog))
            region = (slice(400//4, 1150//4), slice(220//4, 860//4))
        errs = []
        cands = grabs(f"{proj}/assets/aroll.mp4", n - 3, 7)
        for k in range(-3, 4):
            a = tf(cands[k + 3], scale, ty, inner=inner)
            errs.append((float(np.abs(r[region] - a[region]).mean()), k))
        best = min(errs); res.append((s["id"], lay, n, best[1], round(best[0], 2), round(sorted(errs)[1][0] - best[0], 2)))
        print(f"{s['id']:4s} {lay:11s} frame {n:5d} ({n/fps:6.2f}s) best offset {best[1]:+d} err {best[0]:.2f} margin {sorted(errs)[1][0]-best[0]:.2f}", flush=True)
print("all zero:", all(r[3] == 0 for r in res))
