# tuition-ep02-ai-editor

45 s 9:16 reel, episode 2 of Saagii's series "making my tuition by January 15th". He gave himself one hour
to build an AI video editor; v1 took five hours; this video is edited by it. Motion graphics: Studio 21
brand colours and type pushed into a cyberpunk build-terminal look (neon Violet/Mint on Graphite-black),
per Saagii's note "more tech vibe like cyberpunk so the colors really pop through on the black background".

- **Raw (Drive `saagii_so/raw`, folder `1m3vESG_T9g2MrryfAJgnkhJSa_t9N0bX`):**
  `58E1AF89-9A9F-47FB-B00B-DCE134184D86.MP4` (Drive id `15b7quJnZxUanMgvsE2KI8GT3EvOdiHFh`, 120,627,748 bytes,
  1080x1920 HEVC SDR, 30 fps, 101.6 s). One take with several spoken "cut" retakes.
- **Brand:** Figma file `JycAnwdfFjAqWomz8LVIry` (Studio_21), page "Studio 21 Brand - neutral", node 209:49.
  Logos exported to `assets/brand/` (not used on screen; see DESIGN.md).
- **Delivered:** see VERIFY.md.

| File | What |
| --- | --- |
| `DESIGN.md` | Brief, brand mapping (and where the cyberpunk brief pushed on it), captions, layouts, openings, loop, sound, don'ts |
| `edl-plan.json` | Reviewed story segments and every removal with its reason |
| `script.txt` | Exactly what is said in the cut (caption text) |
| `assets/align-fixes.json` | Five word timings re-anchored by hand from the loudness envelope at joins (applied after `tools/align_words.py`) |
| `build_reel.py` | Generator: monitor PiP clips, plan, captions, ledger, SFX, mix, `index.html` |
| `index.html` | The HyperFrames composition as rendered |
| `assets/*.json` | plan, transcript (edited timeline), edit decisions, footage ledger, SFX cues, sources, raw ASR |
| `OPEN-LOOPS.json` | The timer loop (1 hour → 5 hours) and the pipeline loop |
| `VERIFY.md` | Measurements and checks on the delivered file, plus limits |

## Rebuild

```bash
tools/drive.sh fetch 15b7quJnZxUanMgvsE2KI8GT3EvOdiHFh projects/tuition-ep02-ai-editor/raw/58E1AF89-9A9F-47FB-B00B-DCE134184D86.MP4
python3 tools/make_master.py projects/tuition-ep02-ai-editor projects/tuition-ep02-ai-editor/raw/58E1AF89-9A9F-47FB-B00B-DCE134184D86.MP4
python3 tools/build_edl.py projects/tuition-ep02-ai-editor --render
python3 tools/transcribe.py projects/tuition-ep02-ai-editor/work/aroll.16k.wav projects/tuition-ep02-ai-editor/work/aroll.asr.json 0
python3 tools/align_words.py projects/tuition-ep02-ai-editor   # then re-apply assets/align-fixes.json (see VERIFY.md)
# fonts: Space Grotesk + Inter latin woff2 from Google Fonts -> assets/fonts/; gsap.min.js -> assets/
python3 projects/tuition-ep02-ai-editor/build_reel.py projects/tuition-ep02-ai-editor
(cd projects/tuition-ep02-ai-editor && "$STUDIO21_KIT/node_modules/.bin/hyperframes" render --quality standard --output renders/draft-v1.mp4)
```

Note: `assets/transcript.json` is committed, so step 4–5 are only needed if the EDL changes.
