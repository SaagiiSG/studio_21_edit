# VERIFY — arson-wraps-pitch draft v4

**Status: draft for review, not final.**

- Rendered master: `renders/draft-v4.mp4` (HyperFrames 0.7.109, standard quality, 138.2 MB)
- Share copy: `arson-wraps-pitch-draft-v4.mp4` (H.264 2-pass 5 Mb/s, AAC copied from master, 39.0 MB)
  sha256 `11145465ad8acd471476b60cbbb613fd330c514938a3f9a659a8406d2f1bef66`
- 1080x1920, 30 fps, 1798 frames, 59.933 s

## Edit
- Source: IMG_4780 + IMG_4781 joined into `assets/source.mov` (HLG HDR tone-mapped to BT.709, mobius).
- 39 kept ranges, one-pass frame-exact render (`tools/build_edl.py`). Cuts only inside measured silence
  (ffmpeg silencedetect −38 dB). 29 pauses trimmed to 0.18–0.26 s.
- Reviewed removals (see `assets/edit-decisions.json`): false starts "so when, when it comes to"; retake
  "photo of their website … when somebody uploads their"; "and the AI does this math" restart; repeated
  "of their car"; false start "you could"; long pauses. The hook line (raw 0:36) was moved to the front.

## Checks run on the delivered share file
- Plan validator: True (196 words, 23 scenes, every word maps to one kept range).
- Footage validator: True (11 B-roll rows, unique scenes, hashes match).
- HyperFrames lint: 0 errors, 1 warning (85 caption clips on one track — readability of the HTML only).
- Kit preflight flags root `data-start` + inline video as a blocker; the installed HyperFrames lint exempts the
  root composition from that rule, and the render plays all videos (verified below), so this is a stale check.
- Loudness: −16.3 LUFS integrated, LRA 3.6 LU, true peak −1.5 dBTP (measured on the share file).
- Lip sync: rendered speaker frames matched the cut A-roll at offset 0 at 8 points (5.7 s – 51.2 s).

  frame  170 ( 5.67s): best offset +0
  frame  230 ( 7.67s): best offset +0
  frame  540 (18.00s): best offset +0
  frame  590 (19.67s): best offset +0
  frame 1180 (39.33s): best offset +0
  frame 1215 (40.50s): best offset +0
  frame 1490 (49.67s): best offset +0
  frame 1535 (51.17s): best offset +0
- Flash / black-frame scan of all 1798 frames: none.
- Captions: 85 chunks, 29% coloured, shown 2 frames before the first word, never before the previous
  chunk's last word ends; positioned on the seam (split) or chest (face/punch) — mouth/chin never covered
  in inspected frames, including the first 2.5 s frame by frame.
- Fresh ASR (local faster-whisper large-v3) of the final audio — every line present:
```
[  0.00 ->   5.04] if these people are going in to change the color of their car why not do it before they come in
[  5.60 ->  11.00] when it comes to businesses having a website it's not about colors it's not about how the website
[ 11.00 ->  17.50] looks it's not about how website feels but it's all about visualizing the process of your business
[ 17.50 ->  23.50] so yesterday i was cold calling and pitching my ideas and i came across this car wrapping
[ 23.50 ->  28.94] protective film installing business so i built this custom ai component into their website
[ 28.94 ->  33.78] When somebody uploads the photo of their car, they choose the color and see the end result.
[ 34.00 ->  39.12] And AI does its magic and spits out an image of their car being wrapped in that color.
[ 39.28 ->  43.18] And from there, they could just book a meeting or get a quote for the businesses,
[ 43.30 ->  49.48] which could lead into more traffic coming into the business, which means more money, which means overall better business, right?
[ 49.60 ->  51.50] So I do this all the time.
[ 51.56 ->  56.80] I could think of millions of different ways this process could be applied to many different businesses.
[ 56.80 ->  59.56] And if you want to sing for your business, then hit me up.
wrote work/qa/final.asr.json: 195 words
```
  ASR differences vs. the reviewed script ("lead into", "want to sing", missing "thought") occur at points
  with no cut nearby; they are recognition errors on quiet speech, not edit damage. Captions use the script.

## Time split
- Site footage (split, top panel): 26.4 s · Brand graphics (split): 15.8 s · Speaker full/punch: 17.7 s
- Speaker on screen: 100 % (split layouts keep him visible below).
- Two shots use a real scroll then a held frame with push-in (shop gallery, four steps) — the real scroll
  through those sections lasts < 0.7 s. Marked `heldFrame` in `assets/footage-ledger.json`.

## Sound
- Voice: high-pass 80 Hz, light compression, two-pass loudnorm. 13 synthesized SFX (`assets/sfx-cues.json`),
  peaks −20 to −26 dBFS, on visible actions only. **No music bed** (no licensed track available).

## Limits — be honest about these
- I could not *listen* to the result; audio checks are measurement + ASR, not ears. Listen to the joins.
- No uninterrupted real-time viewing either; review was frame sheets, cut strips and per-frame scans.
- Only concept 2 of the three openings was built (see DESIGN.md).
- The business-type chips in the "many businesses" graphic are illustrative examples (labelled "FOR EXAMPLE"),
  not businesses Saagii named.
