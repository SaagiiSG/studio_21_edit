# arson-wraps-pitch

60 s 9:16 pitch reel. Saagii explains how he cold-called Arson Wraps (Calgary vinyl wraps, PPF and tint)
and built an AI "upload your car, see it wrapped" feature into their site. The motion graphics come from his
screen recording of the live site.

- **Raw (Drive `studio_21/raw`):** `IMG_4780.MOV` (take 1, 63.4 s), `IMG_4781.MOV` (take 2, 47.0 s),
  `Screen Recording 2026-10-15 at 8.40.27 PM.mov` (site demo, 95 s, no audio). Saved locally as
  `raw/IMG_4780.MOV`, `raw/IMG_4781.MOV`, `raw/screen-recording.mov`.
- **Delivered:** draft v4, `arson-wraps-pitch-draft-v4.mp4`
  (sha256 `11145465ad8acd471476b60cbbb613fd330c514938a3f9a659a8406d2f1bef66`). Sent to Saagii in chat.
  Upload it to `studio_21/edited` once the Drive token exists.
- **Status:** Saagii approved the draft ("that turned out sick"). Open items: music, @handle on the CTA,
  optional 45 s cut.

| File | What |
| --- | --- |
| `DESIGN.md` | Brief, Arson Wraps palette/type, captions, layouts, three hook concepts, sound, don'ts |
| `edl-plan.json` | Reviewed story segments (edited order) and every removal with its reason |
| `script.txt` | Exactly what is said in the cut (caption text) |
| `build_reel.py` | Generator: B-roll crops/speeds, plan, captions, ledger, SFX, mix, `index.html` |
| `index.html` | The HyperFrames composition as rendered |
| `assets/*.json` | plan, transcript (edited timeline), edit decisions, footage ledger, SFX cues, sources, raw ASR |
| `VERIFY.md` | Measurements and checks on the delivered file, plus the limits of what was verified |
| `OPEN-LOOPS.json` | The hook's question and where the video answers it |

Note: the cut was originally built with per-take WAVs. Re-running the generalized `tools/build_edl.py` on
the joined master reproduces the identical 39 keep ranges (regression-checked 2026-10-16).
