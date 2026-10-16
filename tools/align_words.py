"""Align the reviewed script to ASR word timings on the edited timeline.

Text comes from <project>/script.txt (exactly what is said, in edited order, corrected by a human/agent).
Timing comes from ASR of the rendered A-roll (work/aroll.asr.json, from tools/transcribe.py).
Each word is clamped into the keep range holding its midpoint, so no word crosses a cut.

Writes assets/transcript.json (herk-edit-kit format: text/start/end/sourceStart/sourceEnd per word).
usage: python3 align_words.py <project-dir>
"""
import difflib
import json
import re
import sys
from pathlib import Path

if len(sys.argv) < 2:
    raise SystemExit(__doc__)
proj = Path(sys.argv[1])
SCRIPT = " ".join((proj / "script.txt").read_text().split())
asr = json.loads((proj / "work/aroll.asr.json").read_text())["words"]
edl = json.loads((proj / "assets/edit-decisions.json").read_text())
keeps = edl["keeps"]


def norm(t):
    return re.sub(r"[^a-z0-9']", "", t.lower())


script_words = SCRIPT.split()
a = [norm(w) for w in script_words]
b = [norm(w["text"]) for w in asr]
timing = [None] * len(script_words)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1):
            timing[i1 + k] = (asr[j1 + k]["start"], asr[j1 + k]["end"])
        continue
    if i2 > i1 and j2 > j1:  # replace: spread the ASR span over the script words
        s, e = asr[j1]["start"], asr[j2 - 1]["end"]
        step = (e - s) / (i2 - i1)
        for k in range(i2 - i1):
            timing[i1 + k] = (s + k * step, s + (k + 1) * step)
    print(f"  {tag}: script {' '.join(script_words[i1:i2])!r} <- asr {' '.join(w['text'] for w in asr[j1:j2])!r}")

for i, t in enumerate(timing):  # words the ASR dropped: squeeze between neighbours
    if t is None:
        prev_end = timing[i - 1][1] if i and timing[i - 1] else 0.0
        j = i
        while j < len(timing) and timing[j] is None:
            j += 1
        nxt = timing[j][0] if j < len(timing) else prev_end + 0.3
        step = max((nxt - prev_end) / (j - i), 0.04)
        for k in range(j - i):
            timing[i + k] = (prev_end + k * step, prev_end + (k + 1) * step)

words = []
for text, (s, e) in zip(script_words, timing):
    mid = (s + e) / 2
    k = next((k for k in keeps if k["start"] - 1e-6 <= mid < k["end"] + 1e-6), None) or \
        min(keeps, key=lambda k: min(abs(k["start"] - mid), abs(k["end"] - mid)))
    s, e = max(s, k["start"]), min(e, k["end"])
    if e - s < 0.04:
        e = min(s + 0.04, k["end"])
        s = min(s, e - 0.04)
    words.append({"text": text, "start": round(s, 3), "end": round(e, 3),
                  "sourceStart": round(k["sourceStart"] + (s - k["start"]), 3),
                  "sourceEnd": round(k["sourceStart"] + (e - k["start"]), 3), "type": "word"})

(proj / "assets/transcript.json").write_text(json.dumps({
    "text": SCRIPT, "audio_duration_secs": edl["duration"], "timeline": "edited (assets/aroll.mov)",
    "provider": "faster-whisper (local) on the rendered A-roll; text from script.txt", "words": words}, indent=1))
print(f"wrote {len(words)} words to assets/transcript.json")
