"""Build tuition-ep02-ai-editor: monitor clips, plan, captions, ledger, SFX/mix, index.html.

Cyberpunk build-terminal look on Studio 21 brand colours (see DESIGN.md). Adapted from
projects/arson-wraps-pitch/build_reel.py. Run from the repo root:

usage: python3 projects/tuition-ep02-ai-editor/build_reel.py projects/tuition-ep02-ai-editor [--skip-clips] [--skip-audio]
"""
import hashlib
import html
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

proj = Path(sys.argv[1])
SKIP_CLIPS = "--skip-clips" in sys.argv
SKIP_AUDIO = "--skip-audio" in sys.argv
FPS = 30

edl = json.loads((proj / "assets/edit-decisions.json").read_text())
tr = json.loads((proj / "assets/transcript.json").read_text())
WORDS = tr["words"]

# Word timings re-anchored by hand at joins (loudness envelope), applied on top of tools/align_words.py.
# Idempotent: {word index: [sourceStart, sourceEnd]} -> edited-timeline start/end via the keep that holds it.
_fix_path = proj / "assets/align-fixes.json"
if _fix_path.exists():
    for _i, (_a, _b) in json.loads(_fix_path.read_text()).items():
        _k = next(k for k in edl["keeps"] if k["sourceStart"] - 1e-6 <= _a and _b <= k["sourceEnd"] + 1e-6)
        WORDS[int(_i)].update(sourceStart=_a, sourceEnd=_b, start=round(_k["start"] + _a - _k["sourceStart"], 3),
                              end=round(_k["start"] + _b - _k["sourceStart"], 3))
    (proj / "assets/transcript.json").write_text(json.dumps(tr, indent=1))
DUR = round(round(edl["duration"] * FPS) / FPS, 6)
RAW_DUR = json.loads((proj / "assets/sources.json").read_text())["duration"]
RAW_WORDS = len(json.loads((proj / "assets/source.transcript.json").read_text())["words"])
N_KEEPS = len(edl["keeps"])


def fr(t):
    return round(round(t * FPS) / FPS, 6)


def norm(t):
    return "".join(c for c in t.lower() if c.isalnum() or c == "'")


_cursor = [0]


def find(phrase):
    """Index of the first word of `phrase` at/after the cursor; advances the cursor."""
    toks = [norm(t) for t in phrase.split()]
    for i in range(_cursor[0], len(WORDS) - len(toks) + 1):
        if all(norm(WORDS[i + k]["text"]) == toks[k] for k in range(len(toks))):
            _cursor[0] = i + 1
            return i
    raise SystemExit(f"anchor not found: {phrase!r} after word {_cursor[0]}")


def mmss(t, dec=1):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:0{3 + dec}.{dec}f}"


# Onsets measured on the cut's loudness envelope where Whisper's word start is late (seconds, edited timeline).
ONSET = {"two": 41.26, "edited": 37.48, "five": 29.86, "AI@pipe": 16.74, "Post": 28.49}

# ---------------------------------------------------------------- scenes
# (id, layout, kind, anchor phrase, holdReason)
SCENE_SPEC = [
    ("s00", "split", "hook-timer", "I gave", None),
    ("s01", "face", "because", "because it was", None),
    ("s02", "split", "manual", "30 minutes", "Problem stat builds number by number on the spoken words, then strikes on 'not good'"),
    ("s03", "punch", "quite-a-lot", "But it took", None),
    ("s04", "split", "redacted", "which I will", "Encrypted timer scrambles continuously while the promise 'I'll tell you at the end' plays out"),
    ("s05", "face", "basic", "But the basic", "Speaker sets up the list ('the basic thing goes like this') to camera before the pipeline starts"),
    ("s06", "broll-split", "mon-a", "you put in", "One continuous pipeline: each step lights up on its own spoken noun (raw video, AI analyzes, cuts, caption, B-roll)"),
    ("s07", "punch", "all-i-do", "and all I", None),
    ("s08", "broll-split", "mon-b", "export it", "Pipeline continues: export bar, music EQ, done, post, each on its spoken word"),
    ("s09", "split", "payoff", "And it took", "Loop closes: scramble resolves to 5:00:00, limit strikes, overtime bar fills, v1.0 chip"),
    ("s10", "face", "vision", "and this is far", "Conviction beat: 'far from the vision I had' carried by the speaker's delivery"),
    ("s11", "punch", "something", "but it's something", None),
    ("s12", "face", "meta-hud", "the video you're", "Full-frame HUD: this video's real cut list with a live playhead while the meta line plays"),
    ("s13", "punch", "win", "so I would", None),
    ("s14", "split", "episode", "episode", "Series card: episode odometer rolls to 02, then 'making my tuition by January 15th' builds word by word"),
]

scenes = []
for sid, layout, kind, phrase, hold in SCENE_SPEC:
    i = find(phrase)
    w = WORDS[i]
    start = 0.0 if not scenes else fr(w["start"] - 0.06)
    scenes.append({"id": sid, "start": start, "layout": layout, "kind": kind, "anchor": phrase,
                   "anchorTime": w["start"], "anchorWord": i, **({"holdReason": hold} if hold else {})})
for a, b in zip(scenes, scenes[1:]):
    a["end"] = b["start"]
scenes[-1]["end"] = DUR
S = {s["id"]: s for s in scenes}


def word_time(phrase, after_scene):
    _cursor[0] = S[after_scene]["anchorWord"]
    return WORDS[find(phrase)]["start"]


# ---------------------------------------------------------------- monitor clips (picture-in-picture inside the pipeline)
MON_W, MON_H = 330, 586
CLIPS = {
    "mon-a": ("assets/source.mov", 8.40, "Raw take (unedited master), take 3 of the hook + an abandoned restart with the spoken 'cut' marker. Muted."),
    "mon-b": ("assets/aroll.mp4", 0.00, "The clean cut (A-roll) of this video's own opening: the editor's output. Muted."),
}


def render_monitor(kind, dur):
    src, a, _ = CLIPS[kind]
    out = proj / f"assets/{kind}.mp4"
    n = round(dur * FPS) + 2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", str(proj / src),
                    "-vf", f"fps={FPS},scale={MON_W}:{MON_H}:flags=lanczos,eq=contrast=1.04:saturation=0.92,format=yuv420p",
                    "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-g", "15",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)], check=True)
    return out


ledger = []
for sid, kind in (("s06", "mon-a"), ("s08", "mon-b")):
    s = S[sid]
    dur = s["end"] - s["start"]
    out = proj / f"assets/{kind}.mp4"
    if not SKIP_CLIPS or not out.exists():
        render_monitor(kind, dur)
    src, a, desc = CLIPS[kind]
    ledger.append({
        "scene": sid, "sourceSceneId": f"{'raw-take' if kind == 'mon-a' else 'aroll-opening'}-{a:.1f}", "asset": f"assets/{kind}.mp4",
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "sourceStart": 0.0, "sourceEnd": round(dur, 3),
        "upstream": {"file": src, "sourceStart": a, "sourceEnd": round(a + dur, 3), "speed": 1.0,
                     "provenance": "Saagii's own recording (Drive saagii_so/raw, 2026-10-16)"},
        "description": desc,
        "framing": {"9x16": f"Full source frame scaled into a {MON_W}x{MON_H} monitor window inside the graphics panel"},
    })

# ---------------------------------------------------------------- waveform data (real raw audio, real keep ranges)
NB = 112
with wave.open(str(proj / "work/source.16k.wav")) as wf:
    pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
edges = np.linspace(0, RAW_DUR, NB + 1)
keeps_src = [(k["sourceStart"], k["sourceEnd"]) for k in edl["keeps"]]
bars = []
for a, b in zip(edges, edges[1:]):
    seg = pcm[int(a * 16000):int(b * 16000)]
    db = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
    kept = sum(max(0.0, min(b, kb) - max(a, ka)) for ka, kb in keeps_src) / (b - a)
    bars.append({"h": float(np.clip((db + 62) / 44, 0.06, 1.0)), "keep": kept >= 0.5})

# ---------------------------------------------------------------- captions
# Chunks in spoken order: (words, colour) with colour '' or 'm' (mint).
CHUNKS = [
    ("I gave myself", ""), ("one hour", "m"), ("to build an", ""), ("AI video editor,", "m"),
    ("because it was", ""), ("taking 30 minutes", ""), ("to one hour", ""), ("to edit", ""), ("a single video,", ""),
    ("which was", ""), ("not good.", ""),
    ("But it took", ""), ("quite a lot", ""), ("of time,", "m"), ("which I will", ""), ("tell you in", ""),
    ("the end", "m"), ("of the video.", ""),
    ("But the basic", ""), ("thing goes", ""), ("like this:", ""),
    ("you put in", ""), ("your video,", ""), ("raw video,", "m"), ("then AI", "m"), ("analyzes it,", ""),
    ("and it cuts", ""), ("the dead spaces,", "m"), ("and it adds", ""), ("in the caption,", "m"),
    ("and it adds", ""), ("B-roll", "m"), ("on top of it,", ""),
    ("and all I", ""), ("have to do", ""), ("is export it,", ""), ("put some", ""), ("background music", "m"),
    ("on it,", ""), ("then it's done.", ""), ("Post it.", "m"),
    ("And it", ""), ("took me", ""), ("five hours", "m"), ("to build the", ""), ("version one", "m"), ("of it,", ""),
    ("and this is", ""), ("far from", ""), ("the vision", ""), ("I had,", ""), ("but it's", ""), ("something,", ""),
    ("and the video", ""), ("you're watching", ""), ("right now", ""), ("is edited", "m"), ("by this editor,", "m"),
    ("so I would", ""), ("say this", ""), ("is a win,", "m"),
    ("and this was", ""), ("episode two", "m"), ("of making", ""), ("my tuition", "m"), ("by January 15th.", "m"),
]
caps, wi = [], 0
for text, color in CHUNKS:
    toks = text.split()
    ws = WORDS[wi:wi + len(toks)]
    if [w["text"] for w in ws] != toks:
        raise SystemExit(f"caption chunk mismatch at word {wi}: {text!r} vs {[w['text'] for w in ws]}")
    caps.append({"text": text, "color": color, "words": ws})
    wi += len(toks)
if wi != len(WORDS):
    raise SystemExit(f"captions cover {wi} of {len(WORDS)} words")

LEAD = 2 / FPS
prev_last = 0.0
for c in caps:
    c["start"] = round(max(0.0, c["words"][0]["start"] - LEAD, prev_last), 3)
    prev_last = c["words"][-1]["end"]
for i, c in enumerate(caps):
    last_end = c["words"][-1]["end"]
    nxt = caps[i + 1]["start"] if i + 1 < len(caps) else DUR
    c["end"] = round(min(nxt, last_end + 0.35) if nxt - last_end > 0.6 else nxt, 3)
colored = sum(1 for c in caps if c["color"]) / len(caps)

# ---------------------------------------------------------------- anchor times for graphics
T = {}
T["one_hour"] = word_time("one hour", "s00")
T["ai_editor"] = word_time("AI video", "s00")
T["thirty"] = word_time("30", "s02")
T["one_hour2"] = word_time("one hour", "s02")
T["single"] = word_time("single video,", "s02")
T["not_good"] = word_time("not good.", "s02")
T["redact_end"] = word_time("the end", "s04")
T["you_put"] = word_time("you put", "s06")
T["raw"] = word_time("raw video,", "s06")
T["ai"] = ONSET["AI@pipe"]
T["analyzes"] = word_time("analyzes", "s06")
T["cuts"] = word_time("cuts", "s06")
T["dead"] = word_time("dead", "s06")
T["adds_cap"] = word_time("adds in", "s06")
T["caption"] = word_time("caption,", "s06")
T["broll"] = word_time("B-roll", "s06")
T["export"] = word_time("export", "s08")
T["background"] = word_time("background", "s08")
T["done"] = word_time("done.", "s08")
T["post"] = ONSET["Post"]
T["five"] = ONSET["five"]
T["hours"] = word_time("hours", "s09")
T["version"] = word_time("version", "s09")
T["meta"] = S["s12"]["start"]
T["edited"] = ONSET["edited"]
T["win"] = word_time("win,", "s13")
T["episode"] = word_time("episode", "s14")
T["two"] = ONSET["two"]
T["making"] = word_time("making", "s14")
T["tuition"] = word_time("tuition", "s14")
T["january"] = word_time("January", "s14")
T = {k: round(v, 3) for k, v in T.items()}

GLITCH_AT = [S["s04"]["start"], S["s09"]["start"], S["s12"]["start"]]

# ---------------------------------------------------------------- events + SFX cues
events, sfx = [], []
for s in scenes:
    events.append({"time": s["start"], "type": "cut", "visual": s["id"], "anchor": s["anchor"]})


def ev(t, typ, vis, anchor):
    events.append({"time": round(t, 3), "type": typ, "visual": vis, "anchor": anchor})


ev(T["one_hour"] - LEAD, "timer-on", "s00", "one hour"); sfx.append(("tick", T["one_hour"] - LEAD, -24.0))
ev(T["one_hour"] + 0.45, "timer-run", "s00", "one hour")
ev(T["ai_editor"] - LEAD, "target-chip", "s00", "AI video editor"); sfx.append(("click", T["ai_editor"] - LEAD + 0.03, -24.0))
ev(T["thirty"] - LEAD, "stat-30", "s02", "30"); sfx.append(("tap", T["thirty"] - LEAD, -24.0))
ev(T["one_hour2"] - LEAD, "stat-60", "s02", "one hour"); sfx.append(("tap2", T["one_hour2"] - LEAD, -25.0))
ev(T["single"] - LEAD, "stat-sub", "s02", "single video")
ev(T["not_good"] + 0.10, "strike", "s02", "not good"); sfx.append(("stop", T["not_good"] + 0.10, -21.0))
ev(S["s04"]["start"], "glitch", "s04", "which I will"); sfx.append(("glitch", S["s04"]["start"], -26.0))
ev(T["redact_end"] - LEAD, "reveal-tag", "s04", "the end"); sfx.append(("click2", T["redact_end"] - LEAD + 0.03, -25.0))
ev(T["you_put"] - LEAD, "step-raw", "s06", "you put in"); sfx.append(("click", T["you_put"] - LEAD + 0.02, -24.0))
ev(T["raw"] - LEAD, "raw-tag", "s06", "raw video")
ev(T["ai"] - LEAD, "step-analyze", "s06", "AI"); sfx.append(("click3", T["ai"] - LEAD + 0.02, -24.0)); sfx.append(("air", T["ai"] + 0.05, -29.0))
ev(T["analyzes"], "face-lock", "s06", "analyzes")
ev(T["cuts"] - LEAD, "step-cut", "s06", "cuts"); sfx.append(("click2", T["cuts"] - LEAD + 0.02, -24.0))
ev(T["dead"] + 0.05, "wave-collapse", "s06", "dead spaces"); sfx.append(("air2", T["dead"] + 0.08, -28.0))
ev(T["adds_cap"] - LEAD, "step-caption", "s06", "adds in the caption"); sfx.append(("click", T["adds_cap"] - LEAD + 0.02, -25.0))
ev(T["caption"] - LEAD, "caption-on", "s06", "caption"); sfx.append(("tap2", T["caption"] - LEAD + 0.04, -26.0))
ev(T["broll"] - LEAD, "step-broll", "s06", "B-roll"); sfx.append(("tap", T["broll"] + 0.10, -25.0))
ev(T["export"] - LEAD, "step-export", "s08", "export"); sfx.append(("click3", T["export"] - LEAD + 0.02, -24.0))
ev(T["export"] + 0.85, "export-done", "s08", "export it"); sfx.append(("tick", T["export"] + 0.85, -26.0))
ev(T["background"] - LEAD, "step-music", "s08", "background music"); sfx.append(("click2", T["background"] - LEAD + 0.02, -25.0))
ev(T["done"] - LEAD, "step-done", "s08", "done"); sfx.append(("tone", T["done"], -26.0))
ev(T["post"] - LEAD, "post-press", "s08", "Post it"); sfx.append(("click", T["post"] - LEAD + 0.04, -23.0)); sfx.append(("tone2", T["post"] + 0.18, -25.0))
ev(S["s09"]["start"], "glitch", "s09", "And it took"); sfx.append(("glitch2", S["s09"]["start"], -26.0))
ev(T["five"] - LEAD, "timer-lock", "s09", "five hours"); sfx.append(("thump", T["five"] - LEAD, -19.0))
ev(T["hours"] + 0.08, "limit-strike", "s09", "hours"); sfx.append(("stop2", T["hours"] + 0.08, -23.0))
ev(T["hours"] + 0.25, "overtime-bar", "s09", "hours")
ev(T["version"] - LEAD, "v1-chip", "s09", "version one"); sfx.append(("tap", T["version"] - LEAD + 0.03, -25.0))
ev(T["meta"], "glitch", "s12", "the video you're"); sfx.append(("glitch", T["meta"], -28.0))
ev(T["meta"] + 0.10, "hud-frame", "s12", "the video you're watching")
ev(T["edited"] - LEAD, "hud-edited", "s12", "edited by this editor"); sfx.append(("tick", T["edited"] - LEAD, -26.0))
ev(T["win"] - LEAD, "win-badge", "s13", "win"); sfx.append(("tone", T["win"] - LEAD + 0.03, -25.0))
ev(S["s14"]["start"] + 0.05, "ep-card", "s14", "episode")
ev(T["two"] - LEAD, "ep-roll", "s14", "two"); sfx.append(("tick", T["two"] - LEAD + 0.05, -25.0))
ev(T["making"] - LEAD, "series-title", "s14", "making my tuition")
ev(T["january"] - LEAD, "deadline-chip", "s14", "January 15th"); sfx.append(("tap2", T["january"] - LEAD + 0.03, -24.0))
events.sort(key=lambda e: e["time"])

# ---------------------------------------------------------------- plan.json / ledger
plan = {
    "duration": DUR, "fps": FPS, "width": 1080, "height": 1920,
    "scenes": [{k: v for k, v in s.items() if k != "anchorWord"} for s in scenes],
    "events": events,
    "captions": [{"start": c["start"], "end": c["end"], "color": c["color"], "words": c["words"]} for c in caps],
}
(proj / "assets/plan.json").write_text(json.dumps(plan, indent=1))
(proj / "assets/footage-ledger.json").write_text(json.dumps(ledger, indent=1))

# ---------------------------------------------------------------- SFX synthesis + mix
SR = 48000


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def bandnoise(n, lo, hi, seed):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, n)


def synth(name):
    t_ = lambda n: np.arange(n) / SR
    if name.startswith("click"):
        n = int(0.05 * SR)
        f0 = {"click": 2300, "click2": 1750, "click3": 2850}[name]
        return 0.7 * np.sin(2 * np.pi * f0 * t_(n)) * env_exp(n, 0.006) + 0.5 * bandnoise(n, 1500, 7000, 11 + len(name)) * env_exp(n, 0.003)
    if name == "tick":
        n = int(0.06 * SR)
        return np.sin(2 * np.pi * 3200 * t_(n)) * env_exp(n, 0.004) + 0.3 * bandnoise(n, 3000, 9000, 5) * env_exp(n, 0.002)
    if name.startswith("tap"):
        n = int(0.16 * SR)
        f0 = {"tap": 190, "tap2": 240}[name]
        return np.sin(2 * np.pi * f0 * t_(n)) * env_exp(n, 0.035) + 0.35 * bandnoise(n, 200, 2500, 13) * env_exp(n, 0.008)
    if name.startswith("stop"):
        n = int(0.14 * SR)
        f0 = {"stop": 120, "stop2": 105}[name]
        t = t_(n)
        return np.sin(2 * np.pi * f0 * t * (1 - 0.25 * t / t[-1])) * env_exp(n, 0.045) + 0.6 * bandnoise(n, 400, 4000, 17 + len(name)) * env_exp(n, 0.012)
    if name.startswith("air"):
        n = int(0.42 * SR)
        x = bandnoise(n, 500, 4200 if name == "air" else 3200, 7 if name == "air" else 8)
        t = np.linspace(0, 1, n)
        return x * np.sin(np.pi * np.clip(t * 1.1, 0, 1)) ** 2.4
    if name.startswith("glitch"):
        # Short filtered noise with sample-and-hold steps, gated into three stutters (no pitch sweep, no laser).
        n = int(0.13 * SR)
        x = bandnoise(n, 700, 6000, 21 if name == "glitch" else 22)
        hold = 40
        x = np.repeat(x[::hold], hold)[:n]
        gate = np.zeros(n)
        for a, b in ((0, 0.035), (0.05, 0.08), (0.095, 0.125)):
            gate[int(a * SR):int(b * SR)] = 1
        return x * gate * env_exp(n, 0.08)
    if name == "thump":
        n = int(0.32 * SR)
        t = t_(n)
        return np.sin(2 * np.pi * (78 - 26 * t / t[-1]) * t) * env_exp(n, 0.09) + 0.25 * bandnoise(n, 150, 1800, 31) * env_exp(n, 0.015)
    if name.startswith("tone"):
        # Two short warm notes (a 'done' / 'posted' confirmation), soft attack.
        f1, f2 = (659.3, 987.8) if name == "tone" else (587.3, 880.0)
        n1, n2 = int(0.09 * SR), int(0.22 * SR)
        a = np.sin(2 * np.pi * f1 * t_(n1)) * env_exp(n1, 0.05)
        b = np.sin(2 * np.pi * f2 * t_(n2)) * env_exp(n2, 0.07)
        x = np.concatenate([a, b])
        att = np.minimum(1, np.arange(len(x)) / (0.004 * SR))
        return x * att
    raise ValueError(name)


def write_wav(path, x):
    y = np.clip(x, -1, 1)
    data = (y * 32767).astype(np.int16)
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())


if not SKIP_AUDIO:
    voice = proj / "work/voice-processed.wav"
    pre = "highpass=f=80,lowpass=f=15000,acompressor=threshold=-24dB:ratio=2.5:attack=8:release=150:makeup=2"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(proj / "assets/aroll.mov"), "-af",
                        pre + ",loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    ln = (f"loudnorm=I=-16:TP=-1.5:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(proj / "assets/aroll.mov"), "-af", pre + "," + ln,
                    "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", str(voice)], check=True)
    with wave.open(str(voice)) as wf:
        v = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768
    total = int(round(DUR * SR))
    mix = np.zeros((total, 2), dtype=np.float32)
    mix[:min(total, len(v))] = v[:total]
    sfx_dir = proj / "assets/sfx"
    sfx_dir.mkdir(exist_ok=True)
    cues = []
    for name, t, db in sfx:
        x = synth(name)
        x = x / (np.max(np.abs(x)) + 1e-9) * (10 ** (db / 20))
        write_wav(sfx_dir / f"{name}.wav", x)
        i0 = int(round(t * SR))
        seg = x[:max(0, min(len(x), total - i0))]
        mix[i0:i0 + len(seg)] += seg[:, None]
        cues.append({"name": name, "time": round(t, 3), "peak_dbfs": db})
    peak = float(np.max(np.abs(mix)))
    if peak > 0.84:
        mix *= 0.84 / peak
    write_wav(proj / "assets/mix.wav", mix)
    (proj / "assets/sfx-cues.json").write_text(json.dumps(cues, indent=1))

# ---------------------------------------------------------------- index.html
esc = html.escape
SPLIT_Y, FACE_Y, PUNCH_Y = 880, 1330, 1420
SPK_SPLIT_Y = 540
media, gfx, over, caps_html, tl = [], [], [], [], []


def d_(sid):
    return round(S[sid]["end"] - S[sid]["start"], 6)


def st(sid):
    return S[sid]["start"]


# Layout state at each cut.
for s in scenes:
    t = s["start"]
    if s["layout"] in ("split", "broll-split"):
        tl.append(f"tl.set('#top,#seam',{{opacity:1}},{t});tl.set('#spk-wrap',{{y:{SPK_SPLIT_Y},scale:1}},{t});"
                  f"tl.set('#brk',{{opacity:0}},{t});tl.set('#cap-layer',{{y:{SPLIT_Y - 880}}},{t});")
    elif s["layout"] == "face":
        tl.append(f"tl.set('#top,#seam',{{opacity:0}},{t});tl.set('#spk-wrap',{{y:0,scale:1}},{t});"
                  f"tl.set('#brk',{{opacity:{0 if s['kind'] == 'meta-hud' else 1}}},{t});tl.set('#cap-layer',{{y:{FACE_Y - 880}}},{t});")
    elif s["layout"] == "punch":
        tl.append(f"tl.set('#top,#seam',{{opacity:0}},{t});tl.set('#spk-wrap',{{y:0,scale:1.3}},{t});"
                  f"tl.set('#brk',{{opacity:1}},{t});tl.set('#cap-layer',{{y:{PUNCH_Y - 880}}},{t});")

# Ambient motion: the grid floor scrolls for the whole reel; the speaker gets a slow push inside each face/punch shot.
tl.append(f"tl.fromTo('#grid',{{backgroundPosition:'0px 0px'}},{{backgroundPosition:'0px 1260px',duration:{DUR},ease:'none'}},0);")
for s in scenes:
    if s["layout"] in ("face", "punch"):
        tl.append(f"tl.fromTo('#spk-push',{{scale:1}},{{scale:1.035,duration:{round(d_(s['id']) - 1 / FPS, 4)},ease:'none'}},{s['start']});")
    else:
        tl.append(f"tl.set('#spk-push',{{scale:1}},{s['start']});")


def flick(sel, t, frm=0):
    """Neon flicker-on: three quick opacity steps (deterministic)."""
    return (f"tl.fromTo('{sel}',{{opacity:{frm}}},{{opacity:1,duration:.04,ease:'none',immediateRender:false}},{round(t, 3)});"
            f"tl.to('{sel}',{{opacity:.25,duration:.03,ease:'none'}},{round(t + 0.05, 3)});"
            f"tl.to('{sel}',{{opacity:1,duration:.04,ease:'none'}},{round(t + 0.09, 3)});")


# ---- s00 hook timer
s = "s00"
gfx.append(f'''<div id="g-hook" class="clip g" data-start="{st(s)}" data-duration="{d_(s)}" data-track-index="2">
 <div class="lab l" id="hk-l">// EP.02 · BUILD CHALLENGE</div><div class="lab r dim" id="hk-r">TIME LIMIT</div>
 <div class="timer chroma" id="hk-t" style="opacity:.28">1:00:00</div>
 <div class="drain" id="hk-dr"><i id="hk-fill"></i></div>
 <div class="tgt" id="hk-tg"><span class="lab">TARGET</span><span class="chip" id="hk-chip">AI VIDEO EDITOR</span></div>
</div>''')
tl.append(f"tl.from('#hk-l',{{opacity:0,x:-30,duration:.35,ease:'power3.out'}},{0.12});")
tl.append(f"tl.from('#hk-r',{{opacity:0,duration:.3,ease:'none'}},{0.25});")
tl.append(flick("#hk-t", T["one_hour"] - LEAD, 0.28))
tl.append(f"tl.fromTo('#hk-t',{{scale:1.18}},{{scale:1,duration:.32,ease:'expo.out',immediateRender:false}},{round(T['one_hour'] - LEAD, 3)});")
tl.append(f"tl.from('#hk-dr',{{scaleX:0,duration:.3,ease:'power2.out'}},{round(T['one_hour'] + 0.05, 3)});")
run0, run1 = round(T["one_hour"] + 0.45, 3), round(S["s00"]["end"], 3)
tl.append(f"countdown('#hk-t',3600,12,{run0},{round(run1 - run0, 3)});")
tl.append(f"tl.fromTo('#hk-fill',{{scaleX:1}},{{scaleX:{round(1 - 12 * (run1 - run0) / 3600, 4)},duration:{round(run1 - run0, 3)},ease:'none'}},{run0});")
tl.append(f"tl.from('#hk-tg .lab',{{opacity:0,duration:.2,ease:'none'}},{round(T['ai_editor'] - LEAD - 0.1, 3)});")
tl.append(f"tl.from('#hk-chip',{{opacity:0,y:26,scale:.9,duration:.34,ease:'back.out(1.7)'}},{round(T['ai_editor'] - LEAD, 3)});")

# ---- s02 manual editing stat
s = "s02"
gfx.append(f'''<div id="g-manual" class="clip g" data-start="{st(s)}" data-duration="{d_(s)}" data-track-index="2">
 <div class="lab l">// THE PROBLEM</div><div class="lab r dim">EDITING BY HAND</div>
 <div class="mn-row" id="mn-row"><span class="big chroma" id="mn-30">30</span><span class="big chroma" id="mn-60">–60</span><span class="unit" id="mn-u">MIN</span><b class="strike" id="mn-strike"></b></div>
 <div class="mn-sub" id="mn-sub">PER VIDEO</div>
 <div class="tlm" id="mn-tl"><div class="trk"><i style="left:0;width:21%"></i><i style="left:23%;width:12%"></i><i style="left:37%;width:30%"></i><i style="left:69%;width:18%"></i></div>
  <div class="trk t2"><i style="left:6%;width:15%"></i><i style="left:40%;width:22%"></i><i style="left:66%;width:26%"></i></div><b class="ph" id="mn-ph"></b></div>
</div>''')
tl.append(f"tl.from('#g-manual .lab',{{opacity:0,duration:.25,ease:'none',stagger:.08}},{st(s) + 0.05});")
tl.append(flick("#mn-30", T["thirty"] - LEAD))
tl.append(f"tl.from('#mn-30',{{y:40,duration:.3,ease:'power3.out'}},{round(T['thirty'] - LEAD, 3)});")
tl.append(f"tl.set('#mn-60,#mn-u',{{opacity:0}},{st(s)});tl.to('#mn-60,#mn-u',{{opacity:1,duration:.05,ease:'none'}},{round(T['one_hour2'] - LEAD, 3)});")
tl.append(f"tl.from('#mn-60,#mn-u',{{x:-50,duration:.32,ease:'expo.out'}},{round(T['one_hour2'] - LEAD, 3)});")
tl.append(f"tl.from('#mn-sub',{{opacity:0,y:20,duration:.3,ease:'power2.out'}},{round(T['single'] - LEAD, 3)});")
tl.append(f"tl.from('#mn-tl',{{opacity:0,y:30,duration:.4,ease:'power3.out'}},{st(s) + 0.15});")
tl.append(f"tl.fromTo('#mn-ph',{{x:0}},{{x:150,duration:{d_(s)},ease:'none'}},{st(s)});")
tl.append(f"tl.fromTo('#mn-strike',{{scaleX:0}},{{scaleX:1,duration:.2,ease:'power2.in'}},{round(T['not_good'] + 0.02, 3)});")
tl.append(f"tl.to('#mn-30,#mn-60,#mn-u',{{color:'#4B5262',textShadow:'0 0 0 rgba(0,0,0,0)',duration:.18,ease:'none'}},{round(T['not_good'] + 0.18, 3)});")

# ---- s04 redacted timer
s = "s04"
gfx.append(f'''<div id="g-redact" class="clip g" data-start="{st(s)}" data-duration="{d_(s)}" data-track-index="2">
 <div class="lab l">// ACTUAL BUILD TIME</div><div class="lab r dim" id="rd-st">STATUS: ENCRYPTED</div>
 <div class="lockbox" id="rd-box"><div class="timer chroma" id="rd-t">#:##:##</div></div>
 <div class="tgt" id="rd-tag"><span class="chip">REVEALED AT THE END</span></div>
</div>''')
tl.append(f"tl.from('#rd-box',{{scaleY:.2,opacity:0,duration:.25,ease:'expo.out'}},{st(s) + 0.04});")
tl.append(f"scramble('#rd-t','#:##:##',{st(s)},{d_(s)},0);")
tl.append(f"tl.to('#rd-st',{{opacity:.25,duration:.12,ease:'none',yoyo:true,repeat:{int(d_(s) / 0.24) - 1}}},{st(s) + 0.1});")
tl.append(f"tl.from('#rd-tag',{{opacity:0,y:24,duration:.3,ease:'back.out(1.6)'}},{round(T['redact_end'] - LEAD, 3)});")

# ---- s06 / s08 pipeline
STEPS = ["RAW VIDEO", "AI ANALYZE", "CUT", "CAPTIONS", "B-ROLL", "EXPORT", "MUSIC", "POST"]


def steps_html(pfx):
    return "".join(f'<div class="stp" id="{pfx}-st{i}"><em>{i + 1:02d}</em><span>{n}</span></div>' for i, n in enumerate(STEPS))


def wave_html(pfx):
    return "".join(f'<i id="{pfx}-b{k}" class="{"kp" if b["keep"] else "rm"}" style="left:{k * 8.4:.1f}px;height:{max(4, round(b["h"] * 62))}px"></i>'
                   for k, b in enumerate(bars))


def step_on(pfx, i, t):
    """Step i becomes active at t; the previous step turns done."""
    out = [f"tl.set('#{pfx}-st{i}',{{className:'stp on'}},{round(t, 3)});"]
    if i > 0:
        out.append(f"tl.set('#{pfx}-st{i - 1}',{{className:'stp done'}},{round(t, 3)});")
    return "".join(out)


kept_n = sum(1 for b in bars if b["keep"])
kx0 = (940 - kept_n * 8.4) / 2  # compacted waveform is centred
for pfx, sid, kind in (("pa", "s06", "mon-a"), ("pb", "s08", "mon-b")):
    first = pfx == "pa"
    media.append(f'<div class="mon-wrap" id="mw-{pfx}"><div class="mon-in" id="mi-{pfx}"><video id="v-{pfx}" src="assets/{kind}.mp4" muted playsinline '
                 f'data-start="{st(sid)}" data-duration="{round(d_(sid) - 1 / FPS, 4)}" data-track-index="1"></video></div></div>')
    dur_txt = mmss(RAW_DUR) if first else mmss(DUR)
    words_txt = "&#8212;" if first else str(len(WORDS))
    clips_txt = "1" if first else str(N_KEEPS)
    gfx.append(f'''<div id="g-{pfx}" class="clip g" data-start="{st(sid)}" data-duration="{d_(sid)}" data-track-index="2">
 <div class="lab l">// PIPELINE</div><div class="lab r dim">AI EDITOR · V1</div>
 <div class="steps">{steps_html(pfx)}</div>
 <div class="mon-frame" id="{pfx}-mf"><div class="mon-lab" id="{pfx}-ml">{"RAW_TAKE.MOV" if first else "EDIT_V1.MP4"}</div></div>
 <div class="ro">
  <div class="ro-i"><span class="lab dim">DURATION</span><b id="{pfx}-dur">{dur_txt}</b></div>
  <div class="ro-i"><span class="lab dim">WORDS</span><b id="{pfx}-wds">{words_txt}</b></div>
  <div class="ro-i"><span class="lab dim">CLIPS</span><b id="{pfx}-clp">{clips_txt}</b></div>
 </div>
 <div class="wave" id="{pfx}-wave">{wave_html(pfx)}</div>
</div>''')
    tl.append(f"tl.from('#g-{pfx} .lab.l,#g-{pfx} .lab.r',{{opacity:0,duration:.2,ease:'none'}},{st(sid) + 0.03});")
    if first:
        tl.append(f"tl.from('#pa-st0,#pa-st1,#pa-st2,#pa-st3,#pa-st4,#pa-st5,#pa-st6,#pa-st7',{{opacity:0,x:-24,duration:.26,stagger:.04,ease:'power3.out'}},{st(sid) + 0.05});")
        tl.append(f"tl.from('#pa-mf',{{scale:.6,opacity:0,duration:.34,ease:'expo.out'}},{round(T['you_put'] - LEAD, 3)});")
        tl.append(f"tl.from('#mw-pa',{{scale:.6,opacity:0,duration:.34,ease:'expo.out'}},{round(T['you_put'] - LEAD, 3)});")
        tl.append(f"tl.from('#g-pa .ro-i',{{opacity:0,x:30,duration:.3,stagger:.07,ease:'power2.out'}},{round(T['you_put'] + 0.1, 3)});")
        tl.append(f"tl.from('#pa-wave i',{{scaleY:0,duration:.25,stagger:{{each:.006,from:'start'}},ease:'power2.out'}},{round(T['raw'] - LEAD, 3)});")
        tl.append(step_on("pa", 0, T["you_put"] - LEAD))
        tl.append(step_on("pa", 1, T["ai"] - LEAD))
        tl.append(f"count('#pa-wds',0,{RAW_WORDS},{round(T['ai'] + 0.1, 3)},1.1,0);")
        tl.append(step_on("pa", 2, T["cuts"] - LEAD))
        # Removed bars dim and drop, then the kept bars close the gaps (real keep ranges of this edit).
        tl.append(f"tl.to('#pa-wave i.rm',{{backgroundColor:'#4B5262',boxShadow:'0 0 0 rgba(0,0,0,0)',duration:.12,ease:'none'}},{round(T['cuts'], 3)});")
        tl.append(f"tl.to('#pa-wave i.rm',{{scaleY:0,duration:.3,ease:'power2.in',stagger:{{each:.004}}}},{round(T['dead'] - 0.05, 3)});")
        kk = 0
        for k, b in enumerate(bars):
            if b["keep"]:
                tl.append(f"tl.to('#pa-b{k}',{{x:{round(kx0 + kk * 8.4 - k * 8.4, 1)},duration:.42,ease:'power3.inOut'}},{round(T['dead'] + 0.28, 3)});")
                kk += 1
        tl.append(f"countClock('#pa-dur',{RAW_DUR},{DUR},{round(T['dead'] + 0.28, 3)},.5);")
        tl.append(f"count('#pa-wds',{RAW_WORDS},{len(WORDS)},{round(T['dead'] + 0.28, 3)},.5,0);count('#pa-clp',1,{N_KEEPS},{round(T['dead'] + 0.28, 3)},.5,0);")
        tl.append(f"tl.set('#pa-ml',{{textContent:'EDIT_V1.MP4'}},{round(T['dead'] + 0.7, 3)});")
        tl.append(step_on("pa", 3, T["adds_cap"] - LEAD))
        tl.append(step_on("pa", 4, T["broll"] - LEAD))
    else:
        for i in range(5):
            tl.append(f"tl.set('#pb-st{i}',{{className:'stp done'}},{st(sid)});")
        kk = 0
        for k, b in enumerate(bars):
            if b["keep"]:
                tl.append(f"tl.set('#pb-b{k}',{{x:{round(kx0 + kk * 8.4 - k * 8.4, 1)}}},{st(sid)});")
                kk += 1
            else:
                tl.append(f"tl.set('#pb-b{k}',{{scaleY:0}},{st(sid)});")
        tl.append(step_on("pb", 5, T["export"] - LEAD))
        tl.append(step_on("pb", 6, T["background"] - LEAD))
        tl.append(step_on("pb", 7, T["done"] - LEAD))
        tl.append(f"tl.set('#pb-st7',{{className:'stp done'}},{round(T['post'] + 0.18, 3)});")

# Monitor overlays (above the monitor video): scan, face lock, mini caption, mini B-roll, export bar, EQ, posted.
MON_X, MON_Y = 375, 112
MINI_DROP = round(SPK_SPLIT_Y * MON_W / 1080)
MINI_CAP_FACE, MINI_CAP_SPLIT = 388, 236 - 24
over.append(f'''<div id="o-pa" class="clip o" data-start="{st('s06')}" data-duration="{d_('s06')}" data-track-index="5">
 <div class="mov">
  <b class="scanbar" id="pa-scan"></b>
  <div class="facebox" id="pa-fb"><i class="c1"></i><i class="c2"></i><i class="c3"></i><i class="c4"></i><span>FACE · SPEECH</span></div>
  <div class="raw-tag" id="pa-rt">RAW</div>
  <div class="mbroll" id="pa-br"><div class="mb-grid"></div><div class="mb-t">1:00:00</div></div>
  <div class="mcap" id="pa-cap"><span>ONE HOUR</span></div>
 </div>
</div>''')
over.append(f'''<div id="o-pb" class="clip o" data-start="{st('s08')}" data-duration="{d_('s08')}" data-track-index="5">
 <div class="mov">
  <div class="mbroll" id="pb-br"><div class="mb-grid"></div><div class="mb-t">1:00:00</div></div>
  <div class="mcap" id="pb-cap"><span>ONE HOUR</span></div>
  <div class="xbar" id="pb-x"><i id="pb-xf"></i><span id="pb-xp">EXPORT 0%</span></div>
  <div class="posted" id="pb-done"><div class="pbtn" id="pb-btn">POST</div></div>
 </div>
 <div class="eq" id="pb-eq">{"".join(f'<i id="pb-q{k}"></i>' for k in range(14))}</div>
</div>''')
tl.append(f"tl.from('#pa-rt',{{opacity:0,scale:.7,duration:.22,ease:'back.out(2)'}},{round(T['raw'] - LEAD, 3)});")
tl.append(f"tl.to('#pa-rt',{{opacity:0,duration:.15,ease:'none'}},{round(T['ai'] - LEAD, 3)});")
tl.append(f"tl.set('#pa-scan',{{opacity:0}},{st('s06')});tl.set('#pa-scan',{{opacity:1}},{round(T['ai'] - LEAD, 3)});")
tl.append(f"tl.fromTo('#pa-scan',{{y:0}},{{y:{MON_H - 6},duration:.55,ease:'sine.inOut',yoyo:true,repeat:2}},{round(T['ai'] - LEAD, 3)});")
tl.append(f"tl.set('#pa-scan',{{opacity:0}},{round(T['ai'] - LEAD + 1.65, 3)});")
tl.append(f"tl.set('#pa-fb',{{opacity:0}},{st('s06')});")
tl.append(flick("#pa-fb", T["analyzes"]))
tl.append(f"tl.from('#pa-fb',{{scale:1.5,duration:.35,ease:'expo.out'}},{round(T['analyzes'], 3)});")
tl.append(f"tl.to('#pa-fb',{{opacity:0,duration:.15,ease:'none'}},{round(T['cuts'] - LEAD, 3)});")
tl.append(f"tl.set('#pa-cap',{{opacity:0}},{st('s06')});tl.set('#pa-cap',{{opacity:1}},{round(T['caption'] - LEAD, 3)});")
tl.append(f"tl.from('#pa-cap span',{{scale:1.4,duration:.22,ease:'expo.out'}},{round(T['caption'] - LEAD, 3)});")
tl.append(f"tl.fromTo('#pa-br',{{yPercent:-100}},{{yPercent:0,duration:.38,ease:'power3.out'}},{round(T['broll'] - LEAD, 3)});")
# The mini monitor mimics the real split: face drops by 540 px x 0.3056, caption moves up to the mini seam.
tl.append(f"tl.to('#mi-pa',{{y:{MINI_DROP},duration:.38,ease:'power3.out'}},{round(T['broll'] - LEAD, 3)});")
tl.append(f"tl.to('#pa-cap',{{y:{MINI_CAP_SPLIT - MINI_CAP_FACE},duration:.38,ease:'power3.out'}},{round(T['broll'] - LEAD, 3)});")
tl.append(f"tl.set('#mi-pb',{{y:{MINI_DROP}}},{st('s08')});tl.set('#pb-cap',{{y:{MINI_CAP_SPLIT - MINI_CAP_FACE}}},{st('s08')});")
tl.append(f"tl.fromTo('#pb-xf',{{scaleX:0}},{{scaleX:1,duration:.85,ease:'power1.inOut'}},{round(T['export'], 3)});")
tl.append(f"tl.set('#pb-x',{{opacity:0}},{st('s08')});tl.set('#pb-x',{{opacity:1}},{round(max(st('s08') + 0.02, T['export'] - LEAD), 3)});")
tl.append(f"pct('#pb-xp','EXPORT ',{round(T['export'], 3)},.85);")
tl.append(f"tl.set('#pb-eq',{{opacity:0}},{st('s08')});tl.set('#pb-eq',{{opacity:1}},{round(T['background'] - LEAD, 3)});")
eq_t0 = round(T["background"] - LEAD, 3)
eq_dur = round(T["done"] - LEAD - eq_t0, 3)
tl.append(f"eqbars('#pb-q',14,{eq_t0},{eq_dur});")
tl.append(f"tl.set('#pb-done',{{opacity:0}},{st('s08')});")
tl.append(flick("#pb-done", T["done"] - LEAD))
tl.append(f"tl.to('#pb-btn',{{scale:.88,duration:.08,ease:'power2.in',yoyo:true,repeat:1}},{round(T['post'] - LEAD, 3)});")
tl.append(f"tl.set('#pb-btn',{{textContent:'POSTED',className:'pbtn ok'}},{round(T['post'] + 0.12, 3)});")
tl.append(f"tl.from('#pb-btn',{{scale:1.2,duration:.3,ease:'back.out(2)',immediateRender:false}},{round(T['post'] + 0.12, 3)});")

# ---- s09 payoff
s = "s09"
gfx.append(f'''<div id="g-payoff" class="clip g" data-start="{st(s)}" data-duration="{d_(s)}" data-track-index="2">
 <div class="lab l">// ACTUAL BUILD TIME</div><div class="lab r dim" id="po-st">STATUS: ENCRYPTED</div>
 <div class="timer chroma" id="po-t">#:##:##</div>
 <div class="po-lim" id="po-lim"><span>LIMIT 1:00:00</span><b class="strike" id="po-strike"></b></div>
 <div class="ot" id="po-ot"><div class="ot-trk"><i id="po-fill"></i><b class="ot-mk"><span>1 HR</span></b></div><div class="ot-l"><span class="lab">5&#215; THE LIMIT</span></div></div>
 <div class="tgt" id="po-v1"><span class="chip">BUILD V1.0</span></div>
</div>''')
tl.append(f"scramble('#po-t','5:00:00',{st(s)},{round(T['five'] - LEAD - st(s), 3)},1);")
tl.append(f"tl.from('#po-t',{{scale:1.3,duration:.4,ease:'expo.out',immediateRender:false}},{round(T['five'] - LEAD, 3)});")
tl.append(f"tl.fromTo('#po-t',{{textShadow:'-4px 0 0 rgba(84,64,240,.95),4px 0 0 rgba(63,217,178,.6),0 0 90px rgba(84,64,240,1)'}},"
          f"{{textShadow:'-4px 0 0 rgba(84,64,240,.9),4px 0 0 rgba(63,217,178,.5),0 0 34px rgba(84,64,240,.55)',duration:.6,ease:'power2.out',immediateRender:false}},{round(T['five'] - LEAD, 3)});")
tl.append(f"tl.set('#po-st',{{textContent:'STATUS: DECRYPTED'}},{round(T['five'] - LEAD, 3)});")
tl.append(f"tl.from('#po-lim',{{opacity:0,y:20,duration:.25,ease:'power2.out'}},{round(T['five'] + 0.05, 3)});")
tl.append(f"tl.fromTo('#po-strike',{{scaleX:0}},{{scaleX:1,duration:.2,ease:'power2.in'}},{round(T['hours'] + 0.0, 3)});")
tl.append(f"tl.to('#po-lim span',{{color:'#4B5262',duration:.15,ease:'none'}},{round(T['hours'] + 0.15, 3)});")
tl.append(f"tl.from('#po-ot',{{opacity:0,duration:.2,ease:'none'}},{round(T['hours'] + 0.12, 3)});")
tl.append(f"tl.fromTo('#po-fill',{{scaleX:0}},{{scaleX:1,duration:.75,ease:'power2.out'}},{round(T['hours'] + 0.25, 3)});")
tl.append(f"tl.from('#po-ot .ot-l',{{opacity:0,x:20,duration:.25,ease:'power2.out'}},{round(T['hours'] + 0.85, 3)});")
tl.append(f"tl.from('#po-v1',{{opacity:0,y:26,scale:.9,duration:.34,ease:'back.out(1.7)'}},{round(T['version'] - LEAD, 3)});")

# ---- s12 meta HUD (full frame over the speaker)
s = "s12"
blocks, x = [], 0.0
for k in edl["keeps"]:
    w = (k["end"] - k["start"]) / DUR * (900 - 3 * (N_KEEPS - 1))
    blocks.append(f'<i style="left:{x:.1f}px;width:{max(2.0, w):.1f}px"></i>')
    x += w + 3
over.append(f'''<div id="o-meta" class="clip o full" data-start="{st(s)}" data-duration="{d_(s)}" data-track-index="6">
 <i class="fb tl"></i><i class="fb tr"></i><i class="fb bl"></i><i class="fb br"></i>
 <div class="mt-l" id="mt-l"><b class="dot"></b>THIS VIDEO · EDITED BY <span id="mt-ed">THIS EDITOR</span></div>
 <div class="strip" id="mt-strip">{"".join(blocks)}<b class="phd" id="mt-ph"></b></div>
 <div class="mt-s" id="mt-s"><span>RAW {mmss(RAW_DUR)}</span><span>{N_KEEPS} CLIPS</span><span>FINAL {mmss(DUR)}</span></div>
</div>''')
tl.append(f"tl.from('#o-meta .fb',{{opacity:0,scale:1.25,duration:.3,ease:'expo.out'}},{st(s) + 0.1});")
tl.append(f"tl.from('#mt-l',{{opacity:0,y:-16,duration:.3,ease:'power3.out'}},{st(s) + 0.12});")
tl.append(f"tl.from('#mt-strip i',{{scaleY:0,duration:.22,stagger:.012,ease:'power2.out'}},{st(s) + 0.18});")
tl.append(f"tl.from('#mt-s',{{opacity:0,duration:.25,ease:'none'}},{st(s) + 0.45});")
tl.append(f"tl.fromTo('#mt-ph',{{x:{round(st(s) / DUR * 900, 1)}}},{{x:{round(S[s]['end'] / DUR * 900, 1)},duration:{d_(s)},ease:'none'}},{st(s)});")
tl.append(f"tl.to('#mt-ed',{{color:'#3FD9B2',textShadow:'0 0 14px rgba(63,217,178,.8)',duration:.15,ease:'none'}},{round(T['edited'] - LEAD, 3)});")
tl.append(f"tl.to('#mt-ph',{{boxShadow:'0 0 26px 6px rgba(63,217,178,.95)',duration:.12,ease:'none',yoyo:true,repeat:1}},{round(T['edited'] - LEAD, 3)});")

# ---- s13 win badge
s = "s13"
over.append(f'''<div id="o-win" class="clip o full" data-start="{st(s)}" data-duration="{d_(s)}" data-track-index="6">
 <div class="win" id="win"><b class="chk"></b><span>RESULT: WIN</span></div>
</div>''')
tl.append(f"tl.set('#win',{{opacity:0}},{st(s)});")
tl.append(flick("#win", T["win"] - LEAD))
tl.append(f"tl.from('#win',{{scale:1.35,duration:.35,ease:'back.out(2)'}},{round(T['win'] - LEAD, 3)});")
tl.append(f"tl.fromTo('#win .chk',{{scale:0}},{{scale:1,duration:.25,ease:'back.out(3)'}},{round(T['win'] - LEAD + 0.08, 3)});")

# ---- s14 episode card
s = "s14"
gfx.append(f'''<div id="g-ep" class="clip g" data-start="{st(s)}" data-duration="{d_(s)}" data-track-index="2">
 <div class="lab l">// SERIES</div><div class="lab r dim">EPISODE</div>
 <div class="ep chroma" id="ep"><span>EP.0</span><span class="odo"><span class="odo-s" id="ep-odo"><b>1</b><b>2</b></span></span></div>
 <div class="ep-t" id="ep-t">MAKING MY TUITION</div>
 <div class="tgt" id="ep-dl"><span class="chip">BY JANUARY 15</span></div>
</div>''')
tl.append(f"tl.set('#ep',{{opacity:0}},{st(s)});")
tl.append(flick("#ep", st(s) + 0.05))
tl.append(f"tl.from('#ep',{{y:40,duration:.35,ease:'power3.out',immediateRender:false}},{round(st(s) + 0.05, 3)});")
tl.append(f"tl.fromTo('#ep-odo',{{yPercent:0}},{{yPercent:-50,duration:.32,ease:'back.out(1.4)'}},{round(T['two'] - LEAD, 3)});")
tl.append(f"tl.from('#ep-t',{{opacity:0,y:24,duration:.32,ease:'expo.out'}},{round(T['making'] - LEAD, 3)});")
tl.append(f"tl.from('#ep-dl',{{opacity:0,y:26,scale:.9,duration:.34,ease:'back.out(1.7)'}},{round(T['january'] - LEAD, 3)});")

# ---- glitch slices at the three big beat changes (4 frames, partial-frame bars, never a full-frame flash)
GL_BARS = [(110, 34, -60, "v"), (290, 70, 40, "i"), (470, 22, -30, "m"), (610, 54, 90, "v"), (760, 18, -80, "m"), (1180, 40, 50, "i")]
for gi, t in enumerate(GLITCH_AT):
    bars_html = "".join(f'<i class="gb {c}" style="top:{y}px;height:{h}px"></i>' for y, h, _, c in GL_BARS)
    over.append(f'<div id="gl{gi}" class="clip gl" data-start="{round(t, 3)}" data-duration="{round(4 / FPS, 4)}" data-track-index="{7 + gi}">{bars_html}</div>')
    for k, (y, h, dx, c) in enumerate(GL_BARS):
        tl.append(f"tl.set('#gl{gi} .gb:nth-child({k + 1})',{{x:{dx}}},{round(t, 3)});tl.set('#gl{gi} .gb:nth-child({k + 1})',{{x:{-dx // 2},y:{(k % 3 - 1) * 26}}},{round(t + 2 / FPS, 3)});")
    tl.append(f"tl.set('#top',{{x:14}},{round(t, 3)});tl.set('#top',{{x:-8}},{round(t + 1 / FPS, 3)});tl.set('#top',{{x:0}},{round(t + 3 / FPS, 3)});")

# ---- captions
for i, c in enumerate(caps):
    d = round(c["end"] - c["start"], 3)
    cls = "cap" + (f" {c['color']}" if c["color"] else "")
    caps_html.append(f'<div id="c{i:03d}" class="clip {cls}" data-start="{c["start"]}" data-duration="{d}" data-track-index="4"><span>{esc(c["text"].upper())}</span></div>')

CSS = """
@font-face{font-family:'Space Grotesk';src:url(assets/fonts/space-grotesk-latin-var.woff2) format('woff2');font-weight:300 700;font-style:normal}
@font-face{font-family:'Inter';src:url(assets/fonts/inter-latin-var.woff2) format('woff2');font-weight:100 900;font-style:normal}
:root{--graphite:#15171C;--ink:#0A0B0E;--slate:#4B5262;--mist:#E4E7EE;--cloud:#F5F6F8;--white:#FFFFFF;--violet:#5440F0;--lilac:#DDD8FF;--mint:#3FD9B2}
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0A0B0E}
#reel{position:relative;width:1080px;height:1920px;overflow:hidden;background:var(--ink)}
#spk-wrap{position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:540px 800px;z-index:1}
#spk-push{width:1080px;height:1920px;transform-origin:540px 820px}
#spk{width:1080px;height:1920px;display:block}
#fx{position:absolute;inset:0;z-index:2;pointer-events:none}
#fx .scan{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.03) 0 2px,transparent 2px 6px)}
#fx .vig{position:absolute;inset:0;background:radial-gradient(ellipse 80% 62% at 50% 44%,transparent 58%,rgba(10,11,14,.5) 100%)}
#brk{position:absolute;inset:0;z-index:2}
.bk{position:absolute;width:70px;height:70px;border:4px solid var(--mint);filter:drop-shadow(0 0 10px rgba(63,217,178,.8))}
.bk.a{left:56px;top:190px;border-right:0;border-bottom:0}.bk.b{right:56px;top:190px;border-left:0;border-bottom:0}
.bk.c{left:56px;bottom:300px;border-right:0;border-top:0}.bk.d{right:56px;bottom:300px;border-left:0;border-top:0}
#top{position:absolute;left:0;top:0;width:1080px;height:880px;overflow:hidden;z-index:3;
 background:radial-gradient(ellipse 85% 75% at 50% 40%,#1d2029 0%,#15171C 46%,#0A0B0E 100%)}
#grid{position:absolute;left:-50%;width:200%;bottom:-60px;height:560px;transform:perspective(520px) rotateX(64deg);transform-origin:50% 100%;
 background-image:linear-gradient(rgba(84,64,240,.5) 2px,transparent 2px),linear-gradient(90deg,rgba(84,64,240,.5) 2px,transparent 2px);background-size:90px 90px;
 -webkit-mask-image:linear-gradient(to top,rgba(0,0,0,.95) 0%,rgba(0,0,0,.55) 40%,transparent 88%);mask-image:linear-gradient(to top,rgba(0,0,0,.95) 0%,rgba(0,0,0,.55) 40%,transparent 88%)}
#tscan{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 2px,transparent 2px 5px);z-index:9;pointer-events:none}
.tb{position:absolute;width:48px;height:48px;border:3px solid var(--mint);opacity:.85;filter:drop-shadow(0 0 7px rgba(63,217,178,.8));z-index:8}
.tb.a{left:40px;top:40px;border-right:0;border-bottom:0}.tb.b{right:40px;top:40px;border-left:0;border-bottom:0}
.tb.c{left:40px;bottom:40px;border-right:0;border-top:0}.tb.d{right:40px;bottom:40px;border-left:0;border-top:0}
#seam{position:absolute;left:0;top:877px;width:1080px;height:5px;background:var(--violet);z-index:4;
 box-shadow:0 0 14px 3px rgba(84,64,240,.95),0 0 46px 12px rgba(84,64,240,.45)}
.g{position:absolute;left:0;top:0;width:1080px;height:880px;z-index:3}
.o{position:absolute;left:0;top:0;width:1080px;height:880px;z-index:5;pointer-events:none}
.o.full{height:1920px;z-index:6}
.lab{font:600 28px/1 'Inter',sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--mint);text-shadow:0 0 12px rgba(63,217,178,.55);white-space:nowrap}
.lab.dim{color:var(--mist);opacity:.7;text-shadow:none}
.g>.lab.l{position:absolute;left:104px;top:112px}.g>.lab.r{position:absolute;right:104px;top:112px}
.chroma{text-shadow:-4px 0 0 rgba(84,64,240,.9),4px 0 0 rgba(63,217,178,.5),0 0 34px rgba(84,64,240,.55)}
.timer{position:absolute;left:0;right:0;top:200px;text-align:center;font:700 196px/1 'Space Grotesk',sans-serif;letter-spacing:-.03em;color:var(--cloud);font-variant-numeric:tabular-nums}
.drain{position:absolute;left:104px;right:104px;top:450px;height:10px;border-radius:5px;background:rgba(75,82,98,.55);transform-origin:0 50%}
.drain i{display:block;height:100%;border-radius:5px;background:var(--violet);box-shadow:0 0 16px 2px rgba(84,64,240,.9);transform-origin:0 50%}
.tgt{position:absolute;left:0;right:0;top:530px;display:flex;flex-direction:column;align-items:center;gap:18px}
.chip{display:inline-block;font:700 54px/1 'Space Grotesk',sans-serif;letter-spacing:-.01em;color:var(--white);background:var(--violet);
 padding:20px 34px 18px;border-radius:26px 26px 26px 6px;box-shadow:0 0 30px rgba(84,64,240,.85),0 0 90px rgba(84,64,240,.35);text-shadow:none;white-space:nowrap}
.mn-row{position:absolute;left:0;right:0;top:190px;display:flex;justify-content:center;align-items:baseline}
.big{font:700 210px/1 'Space Grotesk',sans-serif;letter-spacing:-.04em;color:var(--cloud)}
.unit{font:700 84px/1 'Space Grotesk',sans-serif;color:var(--mist);margin-left:22px}
.strike{position:absolute;left:120px;right:120px;top:52%;height:14px;margin-top:-7px;background:var(--mist);border-radius:7px;transform-origin:0 50%;box-shadow:0 0 18px rgba(228,231,238,.5)}
.mn-sub{position:absolute;left:0;right:0;top:430px;text-align:center;font:500 54px/1 'Space Grotesk',sans-serif;color:var(--mist);letter-spacing:.02em}
.tlm{position:absolute;left:104px;right:104px;top:540px;height:150px;border:2px solid rgba(221,216,255,.22);border-radius:16px;background:rgba(10,11,14,.55);padding:22px 20px}
.trk{position:relative;height:44px;margin-bottom:16px}.trk i{position:absolute;top:0;height:44px;border-radius:8px;border:2px solid rgba(84,64,240,.9);background:rgba(84,64,240,.22)}
.trk.t2 i{border-color:rgba(221,216,255,.5);background:rgba(221,216,255,.1)}
.ph{position:absolute;left:30px;top:10px;width:4px;height:130px;background:var(--mint);box-shadow:0 0 12px rgba(63,217,178,.9)}
.lockbox{position:absolute;left:104px;right:104px;top:150px;height:330px;border:2px solid rgba(84,64,240,.85);border-radius:22px;box-shadow:0 0 28px rgba(84,64,240,.5),inset 0 0 40px rgba(84,64,240,.2)}
.lockbox .timer{top:66px}
.steps{position:absolute;left:96px;top:150px;width:270px;display:flex;flex-direction:column;gap:12px}
.stp{display:flex;align-items:center;gap:14px;height:54px;padding:0 14px;border-radius:12px;font:600 26px/1 'Inter',sans-serif;letter-spacing:.06em;color:rgba(228,231,238,.45);white-space:nowrap}
.stp em{font:700 24px/1 'Space Grotesk',sans-serif;font-style:normal;color:rgba(228,231,238,.35)}
.stp.on{color:var(--mint);background:rgba(84,64,240,.28);box-shadow:inset 3px 0 0 var(--violet),0 0 22px rgba(84,64,240,.35);text-shadow:0 0 12px rgba(63,217,178,.6)}
.stp.on em{color:var(--mint)}
.stp.done{color:var(--mist)}.stp.done em{color:var(--mint)}
.mon-frame{position:absolute;left:371px;top:108px;width:338px;height:594px;border:2px solid rgba(221,216,255,.5);border-radius:14px;box-shadow:0 0 0 1px rgba(84,64,240,.7),0 0 34px rgba(84,64,240,.55)}
.mon-lab{position:absolute;left:0;top:-36px;font:600 22px/1 'Inter',sans-serif;letter-spacing:.08em;color:var(--mist);opacity:.8}
.mon-wrap{position:absolute;left:375px;top:112px;width:330px;height:586px;border-radius:10px;overflow:hidden;z-index:4}
.mon-in{width:330px;height:586px}
.mon-wrap video{width:330px;height:586px;display:block}
.ro{position:absolute;left:744px;top:196px;width:250px;display:flex;flex-direction:column;gap:34px}
.ro-i{display:flex;flex-direction:column;gap:10px}.ro-i .lab{font-size:24px}
.ro-i b{font:700 58px/1 'Space Grotesk',sans-serif;color:var(--cloud);font-variant-numeric:tabular-nums;letter-spacing:-.02em;text-shadow:0 0 22px rgba(84,64,240,.6)}
.wave{position:absolute;left:70px;top:738px;width:940px;height:64px}
.wave i{position:absolute;bottom:0;width:5px;border-radius:2px;background:var(--violet);box-shadow:0 0 8px rgba(84,64,240,.85);transform-origin:50% 100%}
.mov{position:absolute;left:375px;top:112px;width:330px;height:586px;overflow:hidden;border-radius:10px}
.scanbar{position:absolute;left:0;top:0;width:330px;height:6px;background:var(--mint);box-shadow:0 0 18px 4px rgba(63,217,178,.85)}
.facebox{position:absolute;left:{FB_X}px;top:{FB_Y}px;width:190px;height:230px}
.facebox i{position:absolute;width:34px;height:34px;border:4px solid var(--mint);filter:drop-shadow(0 0 6px rgba(63,217,178,.9))}
.facebox .c1{left:0;top:0;border-right:0;border-bottom:0}.facebox .c2{right:0;top:0;border-left:0;border-bottom:0}
.facebox .c3{left:0;bottom:0;border-right:0;border-top:0}.facebox .c4{right:0;bottom:0;border-left:0;border-top:0}
.facebox span{position:absolute;left:0;top:-30px;font:600 18px/1 'Inter',sans-serif;letter-spacing:.08em;color:var(--mint);white-space:nowrap;background:rgba(10,11,14,.8);padding:4px 6px}
.raw-tag{position:absolute;left:16px;top:16px;font:700 26px/1 'Space Grotesk',sans-serif;color:var(--white);background:var(--violet);padding:8px 14px 6px;border-radius:12px 12px 12px 3px}
.mcap{position:absolute;left:0;top:388px;width:330px;text-align:center}
.mcap span{display:inline-block;font:700 30px/1 'Space Grotesk',sans-serif;color:var(--mint);background:rgba(10,11,14,.92);border:2px solid rgba(221,216,255,.55);border-radius:10px 10px 10px 3px;padding:8px 12px 6px;box-shadow:0 0 14px rgba(84,64,240,.6)}
.mbroll{position:absolute;left:0;top:0;width:330px;height:236px;overflow:hidden;background:radial-gradient(ellipse at 50% 40%,#1d2029,#0A0B0E);border-bottom:3px solid var(--violet);box-shadow:0 6px 18px rgba(84,64,240,.6)}
.mb-grid{position:absolute;left:-50%;width:200%;bottom:-20px;height:150px;transform:perspective(200px) rotateX(62deg);transform-origin:50% 100%;
 background-image:linear-gradient(rgba(84,64,240,.6) 2px,transparent 2px),linear-gradient(90deg,rgba(84,64,240,.6) 2px,transparent 2px);background-size:30px 30px}
.mb-t{position:absolute;left:0;right:0;top:66px;text-align:center;font:700 64px/1 'Space Grotesk',sans-serif;color:var(--cloud);text-shadow:-2px 0 0 rgba(84,64,240,.9),2px 0 0 rgba(63,217,178,.5)}
.xbar{position:absolute;left:20px;top:530px;width:290px;height:40px;border-radius:10px;background:rgba(10,11,14,.9);border:2px solid rgba(221,216,255,.4);overflow:hidden}
.xbar i{position:absolute;left:0;top:0;bottom:0;width:100%;background:var(--violet);box-shadow:0 0 14px rgba(84,64,240,.9);transform-origin:0 50%}
.xbar span{position:absolute;left:0;right:0;top:9px;text-align:center;font:700 22px/1 'Space Grotesk',sans-serif;color:var(--white);letter-spacing:.04em}
.eq{position:absolute;left:748px;top:560px;width:250px;height:130px;display:flex;align-items:flex-end;gap:5px}
.eq i{flex:1;height:100%;background:var(--mint);box-shadow:0 0 10px rgba(63,217,178,.8);transform-origin:50% 100%;border-radius:3px}
.posted{position:absolute;left:0;top:0;width:330px;height:586px;background:rgba(10,11,14,.72);display:flex;align-items:center;justify-content:center}
.pbtn{font:700 46px/1 'Space Grotesk',sans-serif;color:var(--white);background:var(--violet);padding:22px 40px 20px;border-radius:24px 24px 24px 6px;box-shadow:0 0 30px rgba(84,64,240,.9)}
.pbtn.ok{color:var(--graphite);background:var(--mint);box-shadow:0 0 34px rgba(63,217,178,.85)}
.po-lim{position:absolute;left:0;right:0;top:420px;text-align:center;font:500 56px/1 'Space Grotesk',sans-serif;color:var(--mist)}
.po-lim .strike{left:300px;right:300px;top:50%;height:8px;margin-top:-4px}
.ot{position:absolute;left:104px;right:104px;top:528px}
.ot-trk{position:relative;height:18px;border-radius:9px;background:rgba(75,82,98,.55)}
.ot-trk i{position:absolute;left:0;top:0;bottom:0;width:100%;border-radius:9px;background:linear-gradient(90deg,var(--violet),#7a6af5);box-shadow:0 0 18px 3px rgba(84,64,240,.85);transform-origin:0 50%}
.ot-mk{position:absolute;left:20%;top:-14px;width:4px;height:46px;background:var(--cloud)}
.ot-mk span{position:absolute;left:-30px;top:54px;font:600 24px/1 'Inter',sans-serif;letter-spacing:.08em;color:var(--mist);white-space:nowrap}
.ot-l{position:absolute;right:0;top:40px}
#po-v1{top:650px}
.fb{position:absolute;width:90px;height:90px;border:5px solid var(--mint);filter:drop-shadow(0 0 10px rgba(63,217,178,.85))}
.fb.tl{left:44px;top:170px;border-right:0;border-bottom:0}.fb.tr{right:44px;top:170px;border-left:0;border-bottom:0}
.fb.bl{left:44px;bottom:280px;border-right:0;border-top:0}.fb.br{right:44px;bottom:280px;border-left:0;border-top:0}
.mt-l{position:absolute;left:90px;top:206px;font:600 30px/1 'Inter',sans-serif;letter-spacing:.07em;color:var(--cloud);white-space:nowrap;
 background:rgba(10,11,14,.82);padding:12px 16px;border-radius:10px;border:1px solid rgba(221,216,255,.3)}
.mt-l .dot{display:inline-block;width:16px;height:16px;border-radius:50%;background:var(--mint);box-shadow:0 0 12px var(--mint);margin-right:14px;vertical-align:1px}
.strip{position:absolute;left:90px;top:286px;width:900px;height:54px;background:rgba(10,11,14,.82);border-radius:8px}
.strip i{position:absolute;top:8px;height:38px;border-radius:4px;background:var(--violet);box-shadow:0 0 10px rgba(84,64,240,.85);transform-origin:50% 100%}
.phd{position:absolute;left:-2px;top:-12px;width:5px;height:78px;background:var(--mint);box-shadow:0 0 14px 3px rgba(63,217,178,.8)}
.mt-s{position:absolute;left:90px;top:356px;width:900px;display:flex;justify-content:space-between;font:600 24px/1 'Inter',sans-serif;letter-spacing:.08em;color:var(--mist)}
.mt-s span{background:rgba(10,11,14,.82);padding:8px 10px;border-radius:6px}
.win{position:absolute;left:0;right:0;top:210px;margin:auto;width:520px;display:flex;align-items:center;justify-content:center;gap:22px;
 font:700 54px/1 'Space Grotesk',sans-serif;color:var(--mint);background:rgba(10,11,14,.88);border:3px solid var(--mint);border-radius:28px 28px 28px 6px;padding:22px 30px;
 box-shadow:0 0 30px rgba(63,217,178,.6);text-shadow:0 0 14px rgba(63,217,178,.6)}
.chk{display:block;width:26px;height:46px;border:solid var(--mint);border-width:0 9px 9px 0;transform:rotate(42deg);margin:-10px 6px 0 4px}
.ep{position:absolute;left:0;right:0;top:150px;display:flex;justify-content:center;font:700 250px/1 'Space Grotesk',sans-serif;letter-spacing:-.04em;color:var(--cloud)}
.odo{display:inline-block;height:250px;overflow:hidden}
.odo-s{display:flex;flex-direction:column}.odo-s b{display:block;height:250px;font-weight:700}
.ep-t{position:absolute;left:0;right:0;top:450px;text-align:center;font:700 74px/1 'Space Grotesk',sans-serif;letter-spacing:-.02em;color:var(--cloud)}
#ep-dl{top:575px}
.gl{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:9;pointer-events:none}
.gb{position:absolute;left:-40px;width:1160px;mix-blend-mode:screen}
.gb.v{background:rgba(84,64,240,.85)}.gb.m{background:rgba(63,217,178,.6)}.gb.i{background:rgba(10,11,14,.85);mix-blend-mode:normal}
#cap-layer{position:absolute;left:0;top:880px;width:1080px;height:0;z-index:7}
.cap{position:absolute;left:0;top:0;width:1080px;text-align:center;transform:translateY(-50%)}
.cap span{display:inline-block;font:700 76px/1 'Space Grotesk',sans-serif;letter-spacing:-.01em;color:var(--cloud);background:rgba(10,11,14,.92);
 border:2px solid rgba(221,216,255,.55);border-radius:20px 20px 20px 5px;padding:18px 30px 16px;white-space:nowrap;
 box-shadow:0 0 0 1px rgba(84,64,240,.55),0 0 26px rgba(84,64,240,.5)}
.cap.m span{color:var(--mint);text-shadow:0 0 16px rgba(63,217,178,.5)}
"""
# Face box over the raw monitor: the face in the 330x586 window sits at about x 105-265, y 145-370 (source face
# x 345-870, y 420-1125 scaled by 0.3056) -> page coords offset by the monitor origin.
CSS = CSS.replace("{FB_X}", "72").replace("{FB_Y}", "160")

JS_HELPERS = """
function fmtHMS(s){s=Math.max(0,Math.floor(s));const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;return h+':'+String(m).padStart(2,'0')+':'+String(x).padStart(2,'0');}
function fmtMS(s){const m=Math.floor(s/60),x=s-m*60;return m+':'+x.toFixed(1).padStart(4,'0');}
function hsh(n){n=Math.imul(n^0x5bd1e995,0x27d4eb2d);n^=n>>>15;n=Math.imul(n,0x85ebca6b);n^=n>>>13;return n>>>0;}
function countdown(sel,from,speed,t0,dur){const el=document.querySelector(sel),o={v:0};
 tl.to(o,{v:dur,duration:dur,ease:'none',onUpdate:()=>{el.textContent=fmtHMS(from-o.v*speed);}},t0);}
function scramble(sel,final,t0,dur,lock){const el=document.querySelector(sel),G='#%&?$@*#%&?$@*0189',o={v:0};
 tl.to(o,{v:1,duration:dur,ease:'none',onUpdate:()=>{const f=Math.floor(o.v*dur*15);let s='';
  for(let i=0;i<final.length;i++){const ch=final[i];s+=(ch===':')?':':G[hsh(f*31+i*7+11)%G.length];}
  el.textContent=(lock&&o.v>=1)?final:s;}},t0);
 if(lock)tl.set(el,{textContent:final},t0+dur);}
function count(sel,a,b,t0,dur,dec){const el=document.querySelector(sel),o={v:a};
 tl.to(o,{v:b,duration:dur,ease:'power2.out',onUpdate:()=>{el.textContent=o.v.toFixed(dec);}},t0);}
function countClock(sel,a,b,t0,dur){const el=document.querySelector(sel),o={v:a};
 tl.to(o,{v:b,duration:dur,ease:'power2.out',onUpdate:()=>{el.textContent=fmtMS(o.v);}},t0);}
function pct(sel,pre,t0,dur){const el=document.querySelector(sel),o={v:0};
 tl.to(o,{v:100,duration:dur,ease:'power1.inOut',onUpdate:()=>{el.textContent=pre+Math.round(o.v)+'%';}},t0);}
function eqbars(pfx,n,t0,dur){const steps=Math.floor(dur/0.1);
 for(let k=0;k<n;k++){tl.set(pfx+k,{scaleY:.1},t0);
  for(let s=0;s<steps;s++){const h=.15+.85*((hsh(k*97+s*13+5)%1000)/1000)*(.55+.45*Math.sin((k+1)*.7+s*.9)**2);
   tl.to(pfx+k,{scaleY:h,duration:.1,ease:'sine.inOut'},t0+s*.1);}}}
"""

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Tuition ep.02 AI video editor</title>
<script src="assets/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="reel" data-composition-id="reel" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
<div id="spk-wrap"><div id="spk-push"><video id="spk" src="assets/aroll.mp4" muted playsinline data-start="0" data-duration="{DUR}" data-track-index="0"></video></div></div>
<div id="fx"><div class="vig"></div><div class="scan"></div></div>
<div id="brk"><i class="bk a"></i><i class="bk b"></i><i class="bk c"></i><i class="bk d"></i></div>
<div id="top">
<div id="grid"></div>
{chr(10).join(gfx)}
{chr(10).join(media)}
<div id="tscan"></div>
<i class="tb a"></i><i class="tb b"></i><i class="tb c"></i><i class="tb d"></i>
</div>
<div id="seam"></div>
{chr(10).join(over)}
<div id="cap-layer">
{chr(10).join(caps_html)}
</div>
<audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{DUR}" data-track-index="20" data-volume="1"></audio>
</div>
<script>
window.__timelines=window.__timelines||{{}};
gsap.set('#brk',{{opacity:0}});gsap.set('#spk-wrap',{{y:{SPK_SPLIT_Y},scale:1}});
const tl=gsap.timeline({{paused:true}});
{JS_HELPERS}
{chr(10).join(tl)}
window.__timelines['reel']=tl;
</script>
</body></html>
"""
(proj / "index.html").write_text(HTML)
(proj / "meta.json").write_text(json.dumps({"id": "reel", "name": "tuition-ep02-ai-editor", "width": 1080, "height": 1920, "fps": FPS}, indent=1))

print(f"duration {DUR}s, scenes {len(scenes)}, captions {len(caps)} ({colored:.0%} mint), events {len(events)}, sfx {len(sfx)}, kept bars {kept_n}/{NB}")
for s in scenes:
    print(f"  {s['id']:4s} {s['start']:6.2f}-{s['end']:6.2f} ({s['end'] - s['start']:4.2f}) {s['layout']:6s} {s['kind']:12s} anchor@{s['anchorTime']:.2f}")
print(json.dumps(T))
