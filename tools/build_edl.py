"""Build the reviewed EDL from <project>/edl-plan.json and (optionally) render the clean A-roll.

All times are on the master timeline (assets/source.mov, see assets/sources.json).
Cuts land only inside measured silence (ffmpeg silencedetect on work/source.16k.wav).

edl-plan.json:
{
  "segments": [{"id": "s1-hook", "start": 35.98, "end": 41.36, "why": "..."}, ...],   # edited order
  "removed":  [{"start": 0.0, "end": 3.3, "reason": "false starts ..."}, ...],        # reasons for the record
  "params":   {"noise_db": -38, "min_silence": 0.18, "min_pause": 0.28,
               "keep_short": 0.18, "keep_long": 0.26, "long_pause": 0.9, "pre_share": 0.45}
}

Writes assets/edit-decisions.json; with --render also assets/aroll.mov (one-pass, frame-exact).
usage: python3 build_edl.py <project-dir> [--render]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

if len(sys.argv) < 2:
    raise SystemExit(__doc__)
proj = Path(sys.argv[1])
render = "--render" in sys.argv
plan = json.loads((proj / "edl-plan.json").read_text())
src = json.loads((proj / "assets/sources.json").read_text())
FPS = src["fps"]
P = {"noise_db": -38, "min_silence": 0.18, "min_pause": 0.28, "keep_short": 0.18, "keep_long": 0.26,
     "long_pause": 0.9, "pre_share": 0.45, **plan.get("params", {})}
# pre_share: share of the kept silence left after the previous word. The rest protects the next onset,
# because silencedetect reports silence_end ~60 ms after the real onset.


def silences(wav):
    out = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(wav), "-af",
         f"highpass=f=80,silencedetect=noise={P['noise_db']}dB:d={P['min_silence']}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    vals = [float(v) for v in re.findall(r"silence_(?:start|end): ([0-9.]+)", out)]
    merged = []
    for a, b in zip(vals[0::2], vals[1::2]):
        if merged and a - merged[-1][1] < 0.01:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def q(t):
    return round(round(t * FPS) / FPS, 6)


sil = silences(proj / "work/source.16k.wav")
keeps, pauses = [], []
for seg in plan["segments"]:
    sid, s, e = seg["id"], seg["start"], seg["end"]
    cur = s
    for a, b in sil:
        if a <= s + 0.05 or b >= e - 0.05 or b - a < P["min_pause"]:
            continue
        keep = P["keep_long"] if b - a >= P["long_pause"] else P["keep_short"]
        cut_a, cut_b = a + keep * P["pre_share"], b - keep * (1 - P["pre_share"])
        keeps.append((sid, cur, cut_a))
        pauses.append({"sourceStart": q(cut_a), "sourceEnd": q(cut_b), "segment": sid,
                       "reason": f"pause {b - a:.2f}s trimmed to {keep:.2f}s"})
        cur = cut_b
    keeps.append((sid, cur, e))

rows, t = [], 0.0
for sid, a, b in keeps:
    a, b = q(a), q(b)
    if b - a < 1.0 / FPS:
        continue
    d = round(b - a, 6)
    rows.append({"segment": sid, "sourceStart": a, "sourceEnd": b, "start": round(t, 6), "end": round(t + d, 6)})
    t += d

decisions = {
    "duration": round(t, 6), "fps": FPS,
    "source": "assets/source.mov (see assets/sources.json)",
    "keeps": rows,
    "removals": [{"sourceStart": r["start"], "sourceEnd": r["end"], "reason": r["reason"]} for r in plan.get("removed", [])] + pauses,
    "segments": [{"id": g["id"], "sourceStart": g["start"], "sourceEnd": g["end"], "why": g.get("why", "")} for g in plan["segments"]],
    "params": P,
}
(proj / "assets/edit-decisions.json").write_text(json.dumps(decisions, indent=1))
print(f"keeps={len(rows)} pauses_trimmed={len(pauses)} duration={t:.3f}s")
for g in plan["segments"]:
    r = [x for x in rows if x["segment"] == g["id"]]
    print(f"  {g['id']:14s} src {g['start']:7.2f}-{g['end']:7.2f} -> edit {r[0]['start']:6.2f}-{r[-1]['end']:6.2f}")

if render:
    n = len(rows)
    parts = [f"[0:v]split={n}" + "".join(f"[v{i}]" for i in range(n)) + ";",
             f"[0:a]asplit={n}" + "".join(f"[a{i}]" for i in range(n)) + ";"]
    for i, r in enumerate(rows):
        sf, ef = round(r["sourceStart"] * FPS), round(r["sourceEnd"] * FPS)
        parts.append(f"[v{i}]trim=start_frame={sf}:end_frame={ef},setpts=PTS-STARTPTS[w{i}];")
        parts.append(f"[a{i}]atrim=start={sf / FPS:.6f}:end={ef / FPS:.6f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.006,afade=t=out:st={(ef - sf) / FPS - 0.006:.6f}:d=0.006[b{i}];")
    parts.append("".join(f"[w{i}][b{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
    graph = proj / "work/cut-filter.txt"
    graph.write_text("\n".join(parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(proj / "assets/source.mov"),
                    "-filter_complex_script", str(graph), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-g", "15", "-pix_fmt", "yuv420p",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "pcm_s16le", str(proj / "assets/aroll.mov")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(proj / "assets/aroll.mov"), "-an", "-c:v", "copy",
                    "-movflags", "+faststart", str(proj / "assets/aroll.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(proj / "assets/aroll.mov"), "-vn", "-ac", "1",
                    "-ar", "16000", str(proj / "work/aroll.16k.wav")], check=True)
    print("rendered assets/aroll.mov, assets/aroll.mp4 (video only), work/aroll.16k.wav")
