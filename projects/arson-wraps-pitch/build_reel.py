"""Build the arson-wraps-pitch reel: B-roll clips, plan, captions, ledger, SFX/mix, index.html.

Project-specific generator, kept as the worked example. For a new video, copy it into projects/<slug>/
and adapt SCENE_SPEC (layouts + anchor phrases), CLIPS (screen-recording intervals + crops), CHUNKS
(caption grouping + colours), and the three graphics. Run from the repo root:

usage: python3 projects/<slug>/build_reel.py projects/<slug> [--skip-clips] [--skip-audio]
"""
import hashlib
import html
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

proj = Path(sys.argv[1])
SKIP_CLIPS = "--skip-clips" in sys.argv
SKIP_AUDIO = "--skip-audio" in sys.argv
FPS = 30
SCREEN = proj / "raw/screen-recording.mov"

edl = json.loads((proj / "assets/edit-decisions.json").read_text())
tr = json.loads((proj / "assets/transcript.json").read_text())
WORDS = tr["words"]
DUR = round(round(edl["duration"] * FPS) / FPS, 6)


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


# ---------------------------------------------------------------- scenes
# (id, layout, kind, anchor phrase, holdReason)
SCENE_SPEC = [
    ("s00", "broll-split", "hero", "If these", None),
    ("s01", "broll-split", "hook-sweep", "change the color", None),
    ("s02", "punch", "why-before", "why not", "Conviction beat: the hook question lands on the speaker's face"),
    ("s03", "face", "thesis", "When it comes", "Thesis setup delivered to camera before the graphic"),
    ("s04", "split", "not-about", "it's not about colors", None),
    ("s05", "punch", "but-all", "but it's all", None),
    ("s06", "broll-split", "four-steps", "visualizing", "Real scroll lands on the site's four-step process, then holds with a push-in while 'visualizing the process of your business' plays out"),
    ("s07", "face", "yesterday", "So yesterday", "Personal story beat; the speaker's delivery carries it"),
    ("s08", "punch", "pitching", "pitching", None),
    ("s09", "broll-split", "shop-gallery", "and I came", "Continuous scroll through the shop's real recent-work gallery"),
    ("s10", "broll-split", "services", "protective film", None),
    ("s11", "broll-split", "upload-ui", "So I built", "Slow push-in on the real AI preview section while the full build sentence plays"),
    ("s12", "broll-split", "upload-photo", "When somebody", None),
    ("s13", "broll-split", "pick-lime", "they choose", "Real cursor moves to Lime Green and clicks 'Show my car'"),
    ("s14", "broll-split", "ai-loader", "and AI", None),
    ("s15", "broll-split", "reveal", "spits out", "One continuous real slider sweep from the white car to Lime Green"),
    ("s16", "face", "from-there", "And from there", None),
    ("s17", "broll-split", "quote-sent", "book a meeting", "Real page scroll past the sent quote request"),
    ("s18", "split", "funnel", "which could lead", "Chain builds node by node on the spoken words; holds follow the speaker's pacing"),
    ("s19", "face", "do-this", "So I do", None),
    ("s19b", "punch", "could-think", "I could think", None),
    ("s20", "split", "many-businesses", "millions", None),
    ("s21", "punch", "cta", "and if you", None),
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

# ---------------------------------------------------------------- B-roll clips (screen recording)
# kind: (src start, src end, crop x, y, w, h) in 2940x1912 source pixels. Panel = 1080x880.
CLIPS = {
    "hero": (93.35, 95.00, 60, 72, 2040, 1662, "Site hero 'CHANGE YOUR COLOUR. KEEP YOUR PAINT.' with nav logo"),
    "hook-sweep": (74.35, 75.45, 51, 477, 1410, 1149, "Before/after slider, second sweep (right to left): white GR86 -> Lime Green"),
    "four-steps": (57.30, 58.00, 60, 210, 1740, 1418, "'FOUR STEPS, PHOTO TO FINISH.' real scroll into the process section at 0.6x, then a held frame with push-in (ends before the FAQ section)"),
    "shop-gallery": (56.35, 56.62, 60, 210, 2040, 1662, "'LATELY IN THE SHOP.' real scroll into the recent-work gallery at 0.6x, then a held frame with push-in"),
    "services": (52.10, 53.70, 840, 210, 2040, 1662, "Services: vehicle wraps, partial wraps, paint protection film"),
    "upload-ui": (2.00, 3.75, 1440, 510, 1440, 1173, "'AI WRAP PREVIEW / UPLOAD YOUR CAR. SEE IT WRAPPED.' section"),
    "upload-photo": (8.75, 10.55, 51, 384, 1410, 1149, "Photo of the white GR86 drops into the upload panel"),
    "pick-lime": (10.90, 12.90, 1470, 735, 1410, 1149, "Cursor picks Lime Green and clicks 'Show my car in Lime Green'"),
    "ai-loader": (13.00, 15.00, 51, 420, 1410, 1149, "'Wrapping your car...' loader on the uploaded photo"),
    "reveal": (70.75, 73.95, 51, 477, 1410, 1149, "Loader resolves into the before/after slider; first sweep to Lime Green"),
    "quote-sent": (91.40, 92.60, 1410, 216, 1470, 1198, "'Thanks! Arson Wraps has your photos and will get back to you.'"),
}


HOLD_SPEED = {"shop-gallery": 0.6, "four-steps": 0.6}  # play at this speed, then hold the last frame for the rest of the scene


def render_clip(kind, dur):
    a, b, x, y, w, h, _ = CLIPS[kind]
    n = round(dur * FPS) + 2
    factor = dur / (b - a) if kind not in HOLD_SPEED else 1 / HOLD_SPEED[kind]
    out = proj / f"assets/{kind}.mp4"
    vf = (f"crop={w}:{h}:{x}:{y},setpts={factor:.6f}*(PTS-STARTPTS),fps={FPS},"
          f"scale=1080:880:flags=lanczos,format=yuv420p" + (f",tpad=stop_mode=clone:stop_duration={dur + 1:.3f}" if kind in HOLD_SPEED else ""))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a + (0.0 if kind in HOLD_SPEED else 0.2):.3f}", "-i", str(SCREEN),
                    "-vf", vf, "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                    "-g", "15", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    str(out)], check=True)
    return out


ledger = []
for s in scenes:
    if s["layout"] != "broll-split":
        continue
    dur = s["end"] - s["start"]
    a, b, x, y, w, h, desc = CLIPS[s["kind"]]
    out = proj / f"assets/{s['kind']}.mp4"
    if not SKIP_CLIPS or not out.exists():
        render_clip(s["kind"], dur)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    ledger.append({
        "scene": s["id"], "sourceSceneId": f"site-{s['kind']}", "asset": f"assets/{s['kind']}.mp4", "sha256": sha,
        "sourceStart": 0.0, "sourceEnd": round(dur, 3),
        "upstream": {"file": "raw/screen-recording.mov", "sourceStart": a, "sourceEnd": b,
                     "crop": {"x": x, "y": y, "w": w, "h": h},
                     "speed": HOLD_SPEED.get(s["kind"], round((b - a) / dur, 3)),
                     **({"heldFrame": True} if s["kind"] in HOLD_SPEED else {}),
                     "provenance": "Saagii's screen recording of the live Arson Wraps site (2026-10-15)"},
        "description": desc,
        "framing": {"9x16": "Top panel 1080x880; crop keeps the full UI action and its result visible"},
    })

# ---------------------------------------------------------------- captions
# Chunks in spoken order: (words, color) with color in '', 'm', 'l', 'o'.
CHUNKS = [
    ("If these people", ""), ("are going in", ""), ("to change", ""), ("the color", "m"), ("of their car,", ""),
    ("why not", ""), ("do it", ""), ("before they", "l"), ("come in?", "l"),
    ("When it comes", ""), ("to businesses", ""), ("having a website,", ""),
    ("it's not about", ""), ("colors,", "o"), ("it's not about", ""), ("how the website", ""), ("looks,", "o"),
    ("it's not about", ""), ("how website", ""), ("feels,", "o"),
    ("but it's", ""), ("all about", ""), ("visualizing", "m"), ("the process", "m"), ("of your business.", ""),
    ("So yesterday", ""), ("I was", ""), ("cold calling", "m"), ("and pitching", ""), ("my ideas,", ""),
    ("and I came", ""), ("across this", ""), ("car wrapping,", "m"), ("protective film", ""), ("installing business.", ""),
    ("So I built", ""), ("this custom", ""), ("AI component", "m"), ("into their", ""), ("website.", ""),
    ("When somebody", ""), ("uploads the photo", ""), ("of their car,", ""), ("they choose", ""), ("the color", "m"),
    ("and see", ""), ("the end result,", "l"),
    ("and AI", ""), ("does its magic", "m"), ("and spits out", ""), ("an image", ""), ("of the car", ""),
    ("being wrapped", ""), ("in that color.", "l"),
    ("And from there,", ""), ("they could just", ""), ("book a meeting", "l"), ("or get", ""), ("a quote", "l"),
    ("for the businesses,", ""),
    ("which could", ""), ("lead to", ""), ("more traffic", "l"), ("coming into", ""), ("the business,", ""),
    ("which means", ""), ("more money,", "l"), ("which means", ""), ("overall better", ""), ("business, right?", "l"),
    ("So I do", ""), ("this all", ""), ("the time.", ""),
    ("I could think", ""), ("of millions", "m"), ("of different ways", ""), ("this thought process", "m"),
    ("could be applied", ""), ("to many", ""), ("different businesses,", "m"),
    ("and if you", ""), ("want the same", "l"), ("for your", ""), ("business, then", ""), ("hit me up.", "l"),
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
    # Show 2 frames early, but never before the previous chunk's last word has finished.
    c["start"] = round(max(0.0, c["words"][0]["start"] - LEAD, prev_last), 3)
    prev_last = c["words"][-1]["end"]
for i, c in enumerate(caps):
    last_end = c["words"][-1]["end"]
    nxt = caps[i + 1]["start"] if i + 1 < len(caps) else DUR
    # Hold until the next chunk; after a real pause, clear 0.35 s after the last word.
    c["end"] = round(min(nxt, last_end + 0.35) if nxt - last_end > 0.6 else nxt, 3)

colored = sum(1 for c in caps if c["color"]) / len(caps)

# ---------------------------------------------------------------- events + SFX cues
def edited_time_of_clip(kind, src_t):
    s = next(s for s in scenes if s["kind"] == kind)
    a, b = CLIPS[kind][0], CLIPS[kind][1]
    return round(s["start"] + (src_t - a) * (s["end"] - s["start"]) / (b - a), 3)


def wt(phrase_word_index):
    return WORDS[phrase_word_index]["start"]


def word_time(phrase, after_scene):
    _cursor[0] = S[after_scene]["anchorWord"]
    return WORDS[find(phrase)]["start"]


events, sfx = [], []
for s in scenes:
    events.append({"time": s["start"], "type": "cut", "visual": s["id"], "anchor": s["anchor"]})

# not-about strikes
t_colors = word_time("colors,", "s04")
t_looks = word_time("looks,", "s04")
t_feels = word_time("feels,", "s04")
for t, nm in ((t_colors, "colors"), (t_looks, "looks"), (t_feels, "feels")):
    events.append({"time": round(t - LEAD, 3), "type": "word-card", "visual": "s04", "anchor": nm})
    events.append({"time": round(t + 0.30, 3), "type": "strike", "visual": "s04", "anchor": nm})
sfx += [("stop", t_colors + 0.30, -20.0), ("stop2", t_looks + 0.30, -21.0), ("stop3", t_feels + 0.30, -20.5)]

# hook sweep + reveal + UI clicks (times measured on the screen recording)
sfx.append(("whoosh", S["s01"]["start"] + 0.02, -24.0))
t_pop = edited_time_of_clip("upload-photo", 8.92)
sfx.append(("tap", t_pop, -22.0))
events.append({"time": t_pop, "type": "photo-drop", "visual": "s12", "anchor": "uploads"})
t_pick = edited_time_of_clip("pick-lime", 11.55)
t_click = edited_time_of_clip("pick-lime", 12.38)
sfx += [("click", t_pick, -23.0), ("click2", t_click, -22.0)]
events += [{"time": t_pick, "type": "ui-select", "visual": "s13", "anchor": "choose"},
           {"time": t_click, "type": "ui-click", "visual": "s13", "anchor": "the color"}]
t_slider = edited_time_of_clip("reveal", 71.08)
t_green = edited_time_of_clip("reveal", 73.30)
sfx.append(("whoosh2", t_slider, -25.0))
events += [{"time": t_slider, "type": "reveal", "visual": "s15", "anchor": "spits out"},
           {"time": t_green, "type": "result", "visual": "s15", "anchor": "wrapped"}]

# funnel nodes
t_traffic = word_time("more traffic", "s18")
t_money = word_time("more money,", "s18")
t_better = word_time("better", "s18")
t_right = word_time("right?", "s18")
for t, nm, snd in ((t_traffic, "traffic", "tap2"), (t_money, "money", "tap3"), (t_better, "better", "tap")):
    events.append({"time": round(t - LEAD, 3), "type": "node", "visual": "s18", "anchor": nm})
    sfx.append((snd, t - LEAD + 0.05, -23.0))
events.append({"time": round(t_right, 3), "type": "pulse", "visual": "s18", "anchor": "right?"})

# many businesses
t_process = word_time("thought process", "s20")
t_applied = word_time("applied", "s20")
t_many = word_time("many", "s20")
events += [{"time": round(S["s20"]["start"] + 0.10, 3), "type": "process-row", "visual": "s20", "anchor": "millions"},
           {"time": round(t_process - LEAD, 3), "type": "process-pulse", "visual": "s20", "anchor": "thought process"},
           {"time": round(t_applied - LEAD, 3), "type": "chips", "visual": "s20", "anchor": "applied"},
           {"time": round(t_many, 3), "type": "chips-lit", "visual": "s20", "anchor": "many"}]
sfx.append(("tick", t_applied, -26.0))

t_hit = word_time("hit", "s21")
events.append({"time": round(t_hit - LEAD, 3), "type": "cta", "visual": "s21", "anchor": "hit me up"})
sfx.append(("tap3", t_hit, -24.0))

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
    if name.startswith("whoosh"):
        n = int(0.55 * SR)
        x = bandnoise(n, 300, 3800 if name == "whoosh" else 3000, 7 if name == "whoosh" else 8)
        t = np.linspace(0, 1, n)
        e = np.sin(np.pi * np.clip(t * 1.15, 0, 1)) ** 2.2
        return x * e
    if name.startswith("click"):
        n = int(0.05 * SR)
        f0 = 2300 if name == "click" else 1700
        t = np.arange(n) / SR
        x = 0.7 * np.sin(2 * np.pi * f0 * t) * env_exp(n, 0.006) + 0.5 * bandnoise(n, 1500, 7000, 11) * env_exp(n, 0.003)
        return x
    if name.startswith("tap") or name == "tick":
        n = int(0.16 * SR)
        f0 = {"tap": 190, "tap2": 230, "tap3": 160, "tick": 900}[name]
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * f0 * t) * env_exp(n, 0.035 if name != "tick" else 0.01)
        x += 0.35 * bandnoise(n, 200, 2500, 13) * env_exp(n, 0.008)
        return x
    if name.startswith("stop"):
        n = int(0.14 * SR)
        f0 = {"stop": 120, "stop2": 105, "stop3": 135}[name]
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * f0 * t * (1 - 0.25 * t / t[-1])) * env_exp(n, 0.045)
        x += 0.6 * bandnoise(n, 400, 4000, 17 + len(name)) * env_exp(n, 0.012)
        return x
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
    # Clean + level the voice: rumble cut, gentle compression, two-pass loudness to -16 LUFS / -1.5 dBTP.
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
    if peak > 0.84:  # keep sample peaks under about -1.5 dBFS
        mix *= 0.84 / peak
    write_wav(proj / "assets/mix.wav", mix)
    (proj / "assets/sfx-cues.json").write_text(json.dumps(cues, indent=1))

# ---------------------------------------------------------------- index.html
def esc(t):
    return html.escape(t)


SPLIT_Y, FACE_Y, PUNCH_Y = 880, 1180, 1250
parts_media, parts_graphics, parts_caps, tl = [], [], [], []

# Layout state at each cut.
for s in scenes:
    t = s["start"]
    if s["layout"] in ("split", "broll-split"):
        tl.append(f"tl.set('#top',{{opacity:1}},{t});tl.set('#spk-wrap',{{y:780,scale:1}},{t});tl.set('#cap-layer',{{y:{SPLIT_Y - 880}}},{t});")
    elif s["layout"] == "face":
        tl.append(f"tl.set('#top',{{opacity:0}},{t});tl.set('#spk-wrap',{{y:0,scale:1}},{t});tl.set('#cap-layer',{{y:{FACE_Y - 880}}},{t});")
    elif s["layout"] == "punch":
        tl.append(f"tl.set('#top',{{opacity:0}},{t});tl.set('#spk-wrap',{{y:0,scale:1.28}},{t});tl.set('#cap-layer',{{y:{PUNCH_Y - 880}}},{t});")

for s in scenes:
    d = round(s["end"] - s["start"], 6)
    if s["layout"] == "broll-split":
        parts_media.append(
            f'<div class="bw" id="bw-{s["id"]}"><video id="v-{s["id"]}" src="assets/{s["kind"]}.mp4" muted playsinline '
            f'data-start="{s["start"]}" data-duration="{d}" data-track-index="1"></video></div>')
        tl.append(f"tl.fromTo('#bw-{s['id']}',{{scale:1}},{{scale:1.045,duration:{d},ease:'none'}},{s['start']});")

# Graphic: not-about
g = S["s04"]
gd = round(g["end"] - g["start"], 6)
swatches = "".join(f'<i style="background:{c}"></i>' for c in ("#E41395", "#35D430", "#FF4D1A", "#2F5BD8", "#8C8C94", "#4B5320"))
parts_graphics.append(f'''<div id="g-notabout" class="clip g gpanel" data-start="{g['start']}" data-duration="{gd}" data-track-index="2">
 <div class="na-wrap">
  <div class="eyebrow" id="na-eb">IT'S NOT ABOUT</div>
  <div class="na-row" id="na-colors"><span class="na-word">COLORS<b class="strike"></b></span><span class="sw">{swatches}</span></div>
  <div class="na-row" id="na-looks"><span class="na-word">LOOKS<b class="strike"></b></span></div>
  <div class="na-row" id="na-feels"><span class="na-word">FEELS<b class="strike"></b></span></div>
 </div></div>''')
tl.append(f"tl.from('#na-eb',{{opacity:0,y:16,duration:.4,ease:'power2.out'}},{g['start'] + 0.08});")
for rid, t, ease in (("colors", t_colors, "power3.out"), ("looks", t_looks, "expo.out"), ("feels", t_feels, "back.out(1.6)")):
    tl.append(f"tl.from('#na-{rid}',{{opacity:0,y:46,duration:.34,ease:'{ease}'}},{round(t - LEAD, 3)});")
    if rid == "colors":
        tl.append(f"tl.from('#na-colors .sw i',{{scale:0,duration:.22,stagger:.04,ease:'back.out(2)'}},{round(t - LEAD + 0.08, 3)});")
    tl.append(f"tl.fromTo('#na-{rid} .strike',{{scaleX:0}},{{scaleX:1,duration:.22,ease:'power2.in'}},{round(t + 0.12, 3)});")
    tl.append(f"tl.to('#na-{rid} .na-word',{{color:'#6E6E78',duration:.2,ease:'none'}},{round(t + 0.30, 3)});")

# Graphic: funnel
g = S["s18"]
gd = round(g["end"] - g["start"], 6)
parts_graphics.append(f'''<div id="g-funnel" class="clip g gpanel" data-start="{g['start']}" data-duration="{gd}" data-track-index="2">
 <div class="fn-wrap">
  <div class="node n-quote" id="fn-quote"><em>&#10003;</em>QUOTE REQUEST</div>
  <b class="link" id="fl-1"></b>
  <div class="node" id="fn-traffic">MORE TRAFFIC</div>
  <b class="link" id="fl-2"></b>
  <div class="node" id="fn-money">MORE MONEY</div>
  <b class="link" id="fl-3"></b>
  <div class="node n-win" id="fn-better">BETTER BUSINESS</div>
 </div></div>''')
tl.append(f"tl.from('#fn-quote',{{opacity:0,x:-60,duration:.4,ease:'power3.out'}},{g['start'] + 0.1});")
for k, (nid, t, ease) in enumerate((("traffic", t_traffic, "expo.out"), ("money", t_money, "power3.out"), ("better", t_better, "back.out(1.4)")), 1):
    tl.append(f"tl.fromTo('#fl-{k}',{{scaleY:0}},{{scaleY:1,duration:.28,ease:'power2.inOut'}},{round(t - LEAD - 0.30, 3)});")
    tl.append(f"tl.from('#fn-{nid}',{{opacity:0,y:30,scale:.92,duration:.36,ease:'{ease}'}},{round(t - LEAD, 3)});")
tl.append(f"tl.to('#fn-better',{{scale:1.06,duration:.18,ease:'power2.out',yoyo:true,repeat:1}},{round(t_right, 3)});")

# Graphic: many businesses
g = S["s20"]
gd = round(g["end"] - g["start"], 6)
chips = ["SALONS", "DENTISTS", "GYMS", "LANDSCAPERS", "RENOVATIONS", "TATTOO STUDIOS", "DETAILERS", "PAINTERS"]
chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
parts_graphics.append(f'''<div id="g-many" class="clip g gpanel" data-start="{g['start']}" data-duration="{gd}" data-track-index="2">
 <div class="mb-wrap">
  <div class="mb-row" id="mb-row"><span class="step">PHOTO</span><i>&#8594;</i><span class="step">PREVIEW</span><i>&#8594;</i><span class="step s-hot">QUOTE</span></div>
  <div class="mb-eg" id="mb-eg">FOR EXAMPLE</div>
  <div class="mb-chips" id="mb-chips">{chip_html}</div>
 </div></div>''')
tl.append(f"tl.from('#mb-row .step',{{opacity:0,y:28,duration:.3,stagger:.14,ease:'power3.out'}},{g['start'] + 0.10});")
tl.append(f"tl.from('#mb-row i',{{opacity:0,duration:.2,stagger:.14,ease:'none'}},{g['start'] + 0.22});")
tl.append(f"tl.fromTo('#mb-row',{{boxShadow:'0 0 0 0 rgba(228,19,149,0)'}},{{boxShadow:'0 0 0 6px rgba(228,19,149,.9)',duration:.25,ease:'power2.out'}},{round(t_process - LEAD, 3)});")
tl.append(f"tl.from('#mb-eg',{{opacity:0,duration:.25,ease:'none'}},{round(t_applied - LEAD, 3)});")
tl.append(f"tl.from('#mb-chips .chip',{{opacity:0,scale:.85,y:20,duration:.26,stagger:.09,ease:'back.out(1.7)'}},{round(t_applied - LEAD + 0.05, 3)});")
tl.append(f"tl.to('#mb-chips .chip',{{borderColor:'#35D430',color:'#F5F5F7',duration:.2,stagger:.05,ease:'none'}},{round(t_many, 3)});")

# Captions
for i, c in enumerate(caps):
    d = round(c["end"] - c["start"], 3)
    cls = "cap" + (f" {c['color']}" if c["color"] else "")
    parts_caps.append(f'<div id="c{i:03d}" class="clip {cls}" data-start="{c["start"]}" data-duration="{d}" data-track-index="3"><span>{esc(c["text"].upper())}</span></div>')

CSS = """
@font-face{font-family:'Anton';src:url(assets/fonts/anton-latin.woff2) format('woff2');font-weight:400;font-style:normal}
@font-face{font-family:'Inter';src:url(assets/fonts/inter-latin-var.woff2) format('woff2');font-weight:100 900;font-style:normal}
:root{--asphalt:#0B0B0D;--gun:#1A1A1F;--mag:#E41395;--lime:#35D430;--orange:#FF4D1A;--smoke:#F5F5F7;--ash:#9A9AA5}
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#0B0B0D}
#reel{position:relative;width:1080px;height:1920px;overflow:hidden;background:var(--asphalt)}
#spk-wrap{position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:540px 700px;z-index:1}
#spk{width:1080px;height:1920px;display:block}
#top{position:absolute;left:0;top:0;width:1080px;height:880px;overflow:hidden;z-index:2;background:var(--asphalt)}
#seam{position:absolute;left:0;bottom:0;width:100%;height:4px;background:var(--mag);z-index:4}
.bw{position:absolute;left:0;top:0;width:1080px;height:880px;transform-origin:50% 50%}
.bw video{width:1080px;height:880px;display:block}
.g{position:absolute;left:0;top:0;width:1080px;height:880px;z-index:3}
.gpanel{background:radial-gradient(ellipse at 85% 0%,rgba(228,19,149,.16),transparent 60%),var(--asphalt)}
.eyebrow{font:700 34px/1 'Inter',sans-serif;letter-spacing:8px;color:var(--ash)}
.na-wrap{display:flex;flex-direction:column;justify-content:center;gap:26px;width:100%;height:100%;padding:90px 110px;box-sizing:border-box}
.na-row{position:relative;display:flex;align-items:center;gap:34px;height:170px}
.na-word{position:relative;font:400 168px/1 'Anton',sans-serif;color:var(--smoke);letter-spacing:1px}
.sw{display:flex;gap:14px}.sw i{display:block;width:44px;height:44px;border-radius:50%;box-shadow:0 0 0 2px rgba(245,245,247,.15)}
.strike{position:absolute;left:-16px;right:-16px;top:50%;height:14px;margin-top:-7px;background:var(--orange);border-radius:7px;transform-origin:0 50%}
.fn-wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;height:100%;padding:70px 90px;box-sizing:border-box}
.node{font:400 86px/1 'Anton',sans-serif;color:var(--smoke);background:var(--gun);border:2px solid rgba(245,245,247,.16);border-radius:22px;padding:22px 44px 16px;letter-spacing:1px;white-space:nowrap}
.n-quote{font-size:60px;color:var(--ash);display:flex;align-items:center;gap:18px}.n-quote em{font-style:normal;color:var(--lime)}
.n-win{color:var(--asphalt);background:var(--lime);border-color:var(--lime);box-shadow:0 0 60px rgba(53,212,48,.35)}
.link{display:block;width:6px;height:48px;background:var(--mag);border-radius:3px;transform-origin:50% 0}
.mb-wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;width:100%;height:100%;padding:70px 70px;box-sizing:border-box}
.mb-row{display:flex;align-items:center;gap:18px;padding:22px 30px;border-radius:24px;background:var(--gun)}
.mb-row .step{font:400 76px/1 'Anton',sans-serif;color:var(--smoke)}.mb-row .s-hot{color:var(--mag)}
.mb-row i{font:700 54px/1 'Inter',sans-serif;color:var(--ash);font-style:normal}
.mb-eg{font:700 28px/1 'Inter',sans-serif;letter-spacing:8px;color:var(--ash)}
.mb-chips{display:flex;flex-wrap:wrap;justify-content:center;gap:16px;max-width:900px}
.chip{font:800 34px/1 'Inter',sans-serif;letter-spacing:2px;color:var(--ash);border:2px solid rgba(245,245,247,.18);background:var(--gun);border-radius:999px;padding:16px 26px}
#cap-layer{position:absolute;left:0;top:880px;width:1080px;height:0;z-index:6}
.cap{position:absolute;left:0;top:0;width:1080px;text-align:center;transform:translateY(-50%)}
.cap span{display:inline-block;font:400 82px/1 'Anton',sans-serif;letter-spacing:1px;color:var(--smoke);background:rgba(11,11,13,.9);border:2px solid rgba(245,245,247,.26);border-radius:16px;padding:16px 28px 12px;white-space:nowrap}
.cap.m span{color:#F0359F}.cap.l span{color:var(--lime)}.cap.o span{color:var(--orange)}
"""

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Arson Wraps pitch reel</title>
<script src="assets/gsap.min.js"></script>
<style>{CSS}</style></head><body>
<div id="reel" data-composition-id="reel" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
<div id="spk-wrap"><video id="spk" src="assets/aroll.mp4" muted playsinline data-start="0" data-duration="{DUR}" data-track-index="0"></video></div>
<div id="top">
{chr(10).join(parts_media)}
{chr(10).join(parts_graphics)}
<div id="seam"></div>
</div>
<div id="cap-layer">
{chr(10).join(parts_caps)}
</div>
<audio id="mix" src="assets/mix.wav" data-start="0" data-duration="{DUR}" data-track-index="4" data-volume="1"></audio>
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{chr(10).join(tl)}
window.__timelines['reel']=tl;
</script>
</body></html>
"""
(proj / "index.html").write_text(HTML)
(proj / "meta.json").write_text(json.dumps({"id": "reel", "name": "arson-wraps-pitch", "width": 1080, "height": 1920, "fps": FPS}, indent=1))

print(f"duration {DUR}s, scenes {len(scenes)}, captions {len(caps)} ({colored:.0%} coloured), events {len(events)}, sfx {len(sfx)}")
for s in scenes:
    print(f"  {s['id']:5s} {s['start']:6.2f}-{s['end']:6.2f} ({s['end'] - s['start']:4.2f}) {s['layout']:11s} {s['kind']:15s} anchor@{s['anchorTime']:.2f}")
