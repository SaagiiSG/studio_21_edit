#!/usr/bin/env python3
"""Measure a dead-space cut against its plan. Measurements only: this cannot tell you how it sounds or looks.

usage: python3 tools/deadspace_verify.py <project-dir> <rendered.mp4>

Checks (all printed, JSON written to <project>/work/verify.json):
  1. output duration / frame count vs the plan
  2. audio length vs video length (sync can only drift if these differ)
  3. speech seconds: VAD on the output vs VAD on the source (cuts must not eat speech)
  4. level around every join (+-20 ms): a join inside a word would show as a loud peak
  5. integrated loudness and true peak of source and output (ebur128)
"""
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from faster_whisper.vad import VadOptions, get_speech_timestamps

proj, out = Path(sys.argv[1]), Path(sys.argv[2])
plan = json.loads((proj / "deadspace-plan.json").read_text())
FPS = plan["fps"]
res = {}


def ffprobe(path, entries, stream):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", entries, "-of", "json",
                        str(path)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)["streams"][0]


# 1 + 2: lengths
v = ffprobe(out, "stream=duration,nb_frames,width,height,r_frame_rate", "v:0")
a = ffprobe(out, "stream=duration,sample_rate,channels", "a:0")
exp_frames = sum(k["srcEndFrame"] - k["srcStartFrame"] for k in plan["keeps"])
res["frames"] = {"expected": exp_frames, "actual": int(v["nb_frames"]), "size": f'{v["width"]}x{v["height"]}'}
res["duration"] = {"planned": plan["outputDuration"], "video": float(v["duration"]), "audio": float(a["duration"]),
                   "audioMinusVideo": round(float(a["duration"]) - float(v["duration"]), 4)}

# 3: speech preserved
wav = proj / "work" / (out.stem + ".16k.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                str(wav)], check=True)
with wave.open(str(wav)) as wf:
    pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
ts = get_speech_timestamps(pcm, VadOptions(threshold=0.5, min_speech_duration_ms=120, min_silence_duration_ms=100,
                                           speech_pad_ms=0))
sp_out = sum((t["end"] - t["start"]) / 16000 for t in ts)
sp_src = plan["counts"]["speechSeconds"]
res["speech"] = {"sourceSeconds": sp_src, "outputSeconds": round(sp_out, 2),
                 "diffPercent": round((sp_out - sp_src) / sp_src * 100, 2),
                 "sourceSegments": plan["counts"]["speechSegments"], "outputSegments": len(ts)}

# 4: level at every join
joins, t = [], 0.0
for k in plan["keeps"][:-1]:
    t += (k["srcEndFrame"] - k["srcStartFrame"]) / FPS
    joins.append(t)
peaks = []
for j in joins:
    seg = pcm[max(0, int((j - 0.02) * 16000)):int((j + 0.02) * 16000)]
    peaks.append(20 * np.log10(np.abs(seg).max() + 1e-9))
peaks = np.array(peaks)
loud = [(round(j, 2), round(float(p), 1)) for j, p in zip(joins, peaks) if p > -40]
res["joins"] = {"count": len(joins), "peakDbfsMedian": round(float(np.median(peaks)), 1),
                "peakDbfsMax": round(float(peaks.max()), 1), "joinsLouderThanMinus40": loud}


# 5: loudness
def lufs(path):
    log = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = log[log.rfind("Summary:"):]
    return {"integratedLUFS": float(re.search(r"I:\s+(-?[0-9.]+) LUFS", summary).group(1)),
            "truePeakDBTP": float(re.search(r"Peak:\s+(-?[0-9.]+) dBFS", summary).group(1))}


src_path = next((p for p in (proj / "raw").glob("*") if p.name.lower() == plan["source"].lower()), None)
res["loudness"] = {"output": lufs(out)}
if src_path:
    res["loudness"]["source"] = lufs(src_path)

(proj / "work/verify.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
