#!/usr/bin/env python3
"""Dead-space cut for talking + screen-recording videos (language independent).

A gap is cut only where BOTH detectors agree there is no speech:
  - Silero VAD (shipped with faster-whisper) says "not speech", and
  - ffmpeg silencedetect says "quiet" (default -38 dB after a 80 Hz high-pass).
Each such gap longer than --min-gap is shortened, never deleted. How much is kept depends on the screen:
  - screen still (typing, waiting, reading)  -> keep --keep-static  (default 0.35 s)
  - screen busy (drawing, writing, scrolling) -> keep --keep-active (default 1.5 s)
The head is trimmed to --head s before the first word, the tail to --tail s after the last word.

usage: python3 tools/deadspace_cut.py <project-dir> <video.mp4> [options]
  --plan-only          analyse and write <project>/deadspace-plan.json, do not render
  --out PATH           output mp4 (default <project>/renders/<slug>-deadspace.mp4)
  --crf N              x264 CRF (default 20)
  --noise-db -38  --min-gap 0.5  --keep-static 0.35  --keep-active 1.5  --head 0.3  --tail 0.5
  --webcam-box x0,y0,x1,y1   screen fractions ignored by the motion detector (default 0,0.58,0.30,1)

Writes (inside the project): work/source.16k.wav, work/vad_speech.json, work/motion10fps.npy (caches),
deadspace-plan.json (keeps, removals with reasons, parameters), and the render. Cuts are frame-quantised and
rendered in ONE ffmpeg pass from the original file (6 ms audio fades at joins), so lip sync cannot drift.
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("video")
ap.add_argument("--plan-only", action="store_true")
ap.add_argument("--out")
ap.add_argument("--crf", type=int, default=20)
ap.add_argument("--noise-db", type=float, default=-38)
ap.add_argument("--min-gap", type=float, default=0.5)
ap.add_argument("--keep-static", type=float, default=0.35)
ap.add_argument("--keep-active", type=float, default=1.5)
ap.add_argument("--pre-share", type=float, default=0.4, help="share of the kept pause left after the previous word")
ap.add_argument("--head", type=float, default=0.3)
ap.add_argument("--tail", type=float, default=0.5)
ap.add_argument("--active-frac", type=float, default=0.20, help="share of 10 fps frames that must change for 'busy'")
ap.add_argument("--webcam-box", default="0,0.58,0.30,1")
a = ap.parse_args()

proj, video = Path(a.project), Path(a.video)
for d in ("work", "renders"):
    (proj / d).mkdir(parents=True, exist_ok=True)
slug = proj.name


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


# ---- probe -------------------------------------------------------------------------------------------
pr = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                     "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", str(video)]).stdout)
st, DUR = pr["streams"][0], float(pr["format"]["duration"])
num, den = (int(x) for x in st["r_frame_rate"].split("/"))
FPS = num / den
assert abs(FPS - round(FPS)) < 1e-6, f"variable/odd frame rate {st['r_frame_rate']}: make a CFR master first"
FPS = int(round(FPS))
NFRAMES = int(st["nb_frames"]) if st.get("nb_frames", "").isdigit() else int(DUR * FPS)
W0, H0 = st["width"], st["height"]

# ---- audio, silence, VAD -------------------------------------------------------------------------------
wav = proj / "work/source.16k.wav"
if not wav.exists():
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)])

log = subprocess.run(["ffmpeg", "-v", "info", "-i", str(wav), "-af",
                      f"highpass=f=80,silencedetect=noise={a.noise_db}dB:d=0.18", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
vals = [float(v) for v in re.findall(r"silence_(?:start|end): ([0-9.]+)", log)]
if len(vals) % 2:                       # file ends while still silent
    vals.append(DUR)
sil = list(zip(vals[0::2], vals[1::2]))

vad_path = proj / "work/vad_speech.json"
if vad_path.exists():
    speech = [tuple(x) for x in json.loads(vad_path.read_text())]
else:
    import wave
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    with wave.open(str(wav)) as wf:
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    ts = get_speech_timestamps(pcm, VadOptions(threshold=0.5, min_speech_duration_ms=120,
                                               min_silence_duration_ms=100, speech_pad_ms=0))
    speech = [(t["start"] / 16000, t["end"] / 16000) for t in ts]
    vad_path.write_text(json.dumps(speech))
assert speech, "VAD found no speech"

# ---- screen motion (10 fps, webcam bubble masked) --------------------------------------------------------
mot_path = proj / "work/motion10fps.npy"
if mot_path.exists():
    changed = np.load(mot_path)[:, 0]
else:
    MW = 332
    MH = int(round(MW * H0 / W0))
    x0, y0, x1, y1 = (float(v) for v in a.webcam_box.split(","))
    mask = np.ones((MH, MW), bool)
    mask[int(MH * y0):int(MH * y1), int(MW * x0):int(MW * x1)] = False
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-an", "-vf",
                          f"fps=10,scale={MW}:{MH},format=gray", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, bufsize=MW * MH * 50)
    prev, rows = None, []
    while True:
        b = p.stdout.read(MW * MH)
        if len(b) < MW * MH:
            break
        f = np.frombuffer(b, np.uint8).astype(np.int16).reshape(MH, MW)
        d = np.abs(f - prev)[mask] if prev is not None else np.zeros(1)
        rows.append(((d > 20).sum(), d.mean()))
        prev = f
    arr = np.array(rows)
    np.save(mot_path, arr)
    changed = arr[:, 0]


def busy(g0, g1):
    c = changed[int(g0 * 10):int(g1 * 10)]
    return bool(len(c)) and float((c > 40).mean()) >= a.active_frac


# ---- dead gaps = VAD non-speech ∩ quiet --------------------------------------------------------------------
vgaps = [(0.0, speech[0][0])] + [(speech[i][1], speech[i + 1][0]) for i in range(len(speech) - 1)] + [(speech[-1][1], DUR)]
dead = []
for g0, g1 in vgaps:
    for s0, s1 in sil:
        lo, hi = max(g0, s0), min(g1, s1)
        if hi - lo > 0:
            dead.append([lo, hi])
dead.sort()
merged = []
for g in dead:
    if merged and g[0] - merged[-1][1] < 0.02:
        merged[-1][1] = g[1]
    else:
        merged.append(g)

# ---- plan removals -----------------------------------------------------------------------------------------
removals = []


def add(r0, r1, kind, gap0, gap1, why):
    r0, r1 = math.ceil(r0 * FPS) / FPS, math.floor(r1 * FPS) / FPS      # shrink inward to whole frames
    if r1 - r0 >= 0.1:
        removals.append({"start": round(r0, 6), "end": round(r1, 6), "kind": kind,
                         "gap": [round(gap0, 3), round(gap1, 3)], "reason": why})


for g0, g1 in merged:
    L = g1 - g0
    if g0 < 0.01 and g1 >= speech[0][0] - 0.2:                                  # head
        add(g0, g1 - a.head, "head", g0, g1, f"head {L:.2f}s trimmed to {a.head:.2f}s before first word")
    elif g1 > DUR - 0.1 and g0 <= speech[-1][1] + 0.2:                          # tail
        add(g0 + a.tail, g1, "tail", g0, g1, f"tail {L:.2f}s trimmed to {a.tail:.2f}s after last word")
    elif L > a.min_gap:
        act = busy(g0, g1)
        k = a.keep_active if act else a.keep_static
        if L - k >= 0.1:
            add(g0 + k * a.pre_share, g1 - k * (1 - a.pre_share), "drawing" if act else "static", g0, g1,
                f"{'screen busy' if act else 'screen still'}: {L:.2f}s pause trimmed to {k:.2f}s")

keeps, cur = [], 0          # cur is a frame number: start of the next kept stretch
for r in removals:
    ef = round(r["start"] * FPS)
    if ef > cur:
        keeps.append((cur, ef))
    cur = round(r["end"] * FPS)
if cur < NFRAMES:
    keeps.append((cur, NFRAMES))
out_dur = sum(e - s for s, e in keeps) / FPS

# ---- safety check: no removal may touch speech --------------------------------------------------------------
touch = 0.0
for r in removals:
    for s0, s1 in speech:
        touch += max(0.0, min(r["end"], s1) - max(r["start"], s0))
by_kind = {}
for r in removals:
    k = by_kind.setdefault(r["kind"], [0, 0.0])
    k[0] += 1
    k[1] += r["end"] - r["start"]

plan = {
    "tool": "tools/deadspace_cut.py", "source": video.name, "fps": FPS, "sourceFrames": NFRAMES,
    "sourceDuration": round(NFRAMES / FPS, 3), "outputDuration": round(out_dur, 3),
    "params": {k: v for k, v in vars(a).items() if k not in ("project", "video", "out")},
    "counts": {"speechSegments": len(speech), "speechSeconds": round(sum(e - s for s, e in speech), 2),
               "deadGaps": len(merged), "removals": len(removals),
               "removedByKind": {k: {"n": v[0], "seconds": round(v[1], 2)} for k, v in by_kind.items()},
               "speechSecondsInsideRemovals": round(touch, 4)},
    "keeps": [{"id": f"k{i + 1}", "srcStartFrame": s, "srcEndFrame": e, "srcStart": round(s / FPS, 6),
               "srcEnd": round(e / FPS, 6)} for i, (s, e) in enumerate(keeps)],
    "removed": removals,
}
(proj / "deadspace-plan.json").write_text(json.dumps(plan, indent=1))
print(json.dumps({"sourceDuration": plan["sourceDuration"], "outputDuration": plan["outputDuration"],
                  "removedSeconds": round(NFRAMES / FPS - out_dur, 2), **plan["counts"]}, indent=1))
if touch > 0.02:
    sys.exit(f"ABORT: removals overlap {touch:.3f}s of detected speech")
if a.plan_only:
    sys.exit(0)

# ---- render: one pass, frame-exact video trims, sample-exact audio trims, 6 ms fades --------------------------
n = len(keeps)
parts = [f"[0:v]split={n}" + "".join(f"[v{i}]" for i in range(n)) + ";",
         f"[0:a]asplit={n}" + "".join(f"[a{i}]" for i in range(n)) + ";"]
for i, (sf, ef) in enumerate(keeps):
    d = (ef - sf) / FPS
    parts.append(f"[v{i}]trim=start_frame={sf}:end_frame={ef},setpts=PTS-STARTPTS[w{i}];")
    parts.append(f"[a{i}]atrim=start={sf / FPS:.6f}:end={ef / FPS:.6f},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d=0.006,afade=t=out:st={d - 0.006:.6f}:d=0.006[b{i}];")
parts.append("".join(f"[w{i}][b{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
graph = proj / "work/deadspace-filter.txt"
graph.write_text("\n".join(parts))
out = Path(a.out) if a.out else proj / f"renders/{slug}-deadspace.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-filter_complex_script", str(graph),
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
                "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(out)], check=True)
print(f"rendered {out}")
