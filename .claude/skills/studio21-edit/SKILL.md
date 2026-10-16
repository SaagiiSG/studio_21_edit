---
name: studio21-edit
description: Edit Saagii's raw talking-head recordings from Google Drive (studio_21/raw) into finished 9:16 reels with captions, site/screen-recording motion graphics and SFX, and deliver to studio_21/edited. Use for any request to edit, cut, caption, or make a reel/Short/pitch video from his footage, or to apply his brand guidelines or scripted templates to a video.
---

# Studio 21 edit

End-to-end: Drive raw folder → reviewed cut → HyperFrames composition → verified draft → Drive edited folder.
Read `references/lessons.md` first. It holds the rules that cost time to learn. The engine is
`$STUDIO21_KIT` (herk-edit-kit); its own skills live in `$STUDIO21_KIT/.claude/skills/`. Read
`hyperframes/SKILL.md` and `short-form-edit/SKILL.md` there before building a composition, plus
`$STUDIO21_KIT/docs/EDITING-PLAYBOOK.md` for the house reel style.

Work in `projects/<slug>/` (slug = short kebab-case name). Layout:

```
projects/<slug>/
  raw/            downloaded footage (gitignored)
  work/           wavs, ASR, QA images (gitignored)
  renders/        HyperFrames output (gitignored)
  assets/         clips/media (gitignored) + *.json plans (committed)
  edl-plan.json   reviewed segments + removal reasons (committed)
  script.txt      exactly what is said, in edited order (committed)
  DESIGN.md  VERIFY.md  OPEN-LOOPS.json  index.html  build_reel.py (committed)
```

## 0. Brief and inputs

1. `tools/drive.sh check`. List the raw folder with the Google Drive connector
   (`search_files` with `parentId = '<raw folder id>'`) to get file ids, sizes, and names.
2. Ask only what you can't infer: which clips are A-roll vs B-roll/screen recordings, the format,
   and which brand/template applies. Default brand = `brand/BRAND.md`; template = the one named.
3. Fetch: `tools/drive.sh fetch <id> projects/<slug>/raw/<name>`. In parallel is fine. Check that byte sizes
   match Drive.

## 1. Inspect

- `ffprobe` every file: duration, fps, rotation, audio, and **color_transfer**. iPhone footage is usually
  HLG HDR (arib-std-b67), and `make_master.py` tone-maps it.
- Contact sheets (`ffmpeg ... fps=1/3,scale=270:-1,drawtext=pts,tile=7x3`) of every clip, and per-second
  sheets of screen recordings. Write down usable intervals per shot, and anything that must not appear
  (personal data, file pickers, OS menu bars, overlays).

## 2. Master, transcribe, review

```bash
python3 tools/make_master.py projects/<slug> projects/<slug>/raw/takeA.MOV projects/<slug>/raw/takeB.MOV
python3 tools/transcribe.py projects/<slug>/work/source.16k.wav projects/<slug>/assets/source.transcript.json <duration>
```

- Read every line. Whisper word times stretch across pauses, so **find real pauses with silencedetect /
  loudness envelopes, not word gaps.** Check unclear spots with
  `python3 tools/chunk_asr.py <wav> a-b c-d` (short windows give truer words).
- Write `edl-plan.json` (see `tools/build_edl.py` docstring): story segments in edited order, every removal
  with a reason. Keep the last clean take. Cut only between phrases. Moving a line to the front as a hook
  is fine if the meaning holds; record it.

## 3. Cut, then re-verify the cut

```bash
python3 tools/build_edl.py projects/<slug> --render
python3 tools/transcribe.py projects/<slug>/work/aroll.16k.wav projects/<slug>/work/aroll.asr.json 0
```

- **Re-transcribe the cut.** It exposes stumbles the first pass smoothed over ("the AI does this math",
  repeated "of their car"). Chunk-ASR suspicious joins, fix `edl-plan.json`, and re-render.
  ASR on quiet speech varies between runs: a word that differs where there is **no cut nearby** is a
  recognition error, not edit damage.
- Write `script.txt` (reviewed words, edited order; fix mishearings like "cold cuddling" → "cold calling").
  Then `python3 tools/align_words.py projects/<slug>`.

## 4. Design and build

- `DESIGN.md`: brief, palette/type from `brand/` (or the client's brand), caption rules, layouts, three
  opening concepts with the chosen one and why, the open loop, sound plan, and what NOT to do.
- Copy `projects/arson-wraps-pitch/build_reel.py` as the starting point. It renders B-roll clips with exact
  crops and speeds, writes plan/captions/footage ledger, synthesizes SFX, mixes voice, and generates
  `index.html`. Adapt SCENE_SPEC, CLIPS, CHUNKS, and the graphics for the new video.
  Copy `$STUDIO21_KIT/node_modules/gsap/dist/gsap.min.js` into `assets/`, and the brand fonts (woff2)
  into `assets/fonts/`.
- Validate: `node $STUDIO21_KIT/.claude/skills/short-form-edit/scripts/validate-plan.mjs projects/<slug>`,
  the same with `validate-footage.mjs`, and `$STUDIO21_KIT/node_modules/.bin/hyperframes lint` inside the
  project dir. Ignore the kit's `scripts/preflight.mjs` "root data-start" blocker; see lessons.

## 5. Render, QA, deliver

```bash
(cd projects/<slug> && "$STUDIO21_KIT/node_modules/.bin/hyperframes" render --quality standard --output renders/draft-vN.mp4)
tools/encode_share.sh projects/<slug>/renders/draft-vN.mp4 projects/<slug>/renders/<slug>-draft-vN.mp4
python3 tools/qa_checks.py projects/<slug> projects/<slug>/renders/<slug>-draft-vN.mp4
```

- Look at a frame per scene (contact sheet), the first 2.5 s frame by frame, and strips across cuts.
  Re-ASR the delivered audio. Fix, re-render, and re-check what changed.
- `VERIFY.md`: hash, measurements, checks run, revisions, and **limits** (you can't listen or watch in
  real time; say so).
- Deliver: `tools/drive.sh upload <share mp4>` → `studio_21/edited`. Without the token, SendUserFile
  the share copy and tell Saagii it is not in Drive yet.
- Commit the project's text files and push. Tell Saagii what's in the video, what was cut, and what's
  unverified or open (music, handle, length).
