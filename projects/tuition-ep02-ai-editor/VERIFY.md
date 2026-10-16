# VERIFY: tuition-ep02-ai-editor draft v2

**Status: draft for Saagii's review, not final.**

- Rendered master: `renders/draft-v2.mp4` (HyperFrames 0.7.109, standard quality, 74.7 MB, 6 m 30 s render)
- Share copy: `tuition-ep02-ai-editor-draft-v2.mp4` (H.264 2-pass 5 Mb/s, AAC copied from master, 29.4 MB)
  sha256 `c2435eee726f83cd9fd2b138e219d0301386cb1fc5042d1a78792c41b9ab8f23`
- 1080x1920, 30 fps, 1353 frames, 45.100 s
- Delivered to Saagii in chat. **Not in Drive `studio_21/edited`:** no `GDRIVE_RCLONE_TOKEN` in this environment.

## Edit

- Source: one take, `58E1AF89-….MP4` (SDR BT.709, no tone-mapping needed) → `assets/source.mov`, 101.6 s.
- 26 kept ranges, one-pass frame-exact render (`tools/build_edl.py`). 101.6 s → 45.1 s; 249 raw words → 163.
- Reviewed removals (`edl-plan.json`, `assets/edit-decisions.json`): hook takes 1 and 3 (take 2 kept: the only
  one that says "AI"); four abandoned "because…" restarts, including the spoken "cut" markers and a swear;
  the first "so I spent quite a amount of time…" take; a "quite a, quite a" stumble (found only by re-ASR of
  the cut); "Yeah."; the "the video ste—" stumble; dead air. 18 pauses trimmed to 0.18–0.26 s; one 0.5 s gap
  after the opening "I" trimmed by hand (two sub-threshold silences).
- Joins checked with short-window ASR on the cut: "editor. Because…", "not good. But it took quite a lot of
  time…", "the video. But the basic thing…", "Post it. And it took me five hours…", "something, [and] the
  video you're watching…". All read clean.
- Five word timings at joins re-anchored from the loudness envelope (`assets/align-fixes.json`).

## Checks run on the delivered share file

- Plan validator: ok (163 words, 15 scenes, 51 visual events, max event gap 2.27 s with a hold reason).
- Footage validator: ok (2 picture-in-picture rows: raw take 8.4–18.6 s, the cut's own opening 0–4.3 s).
- HyperFrames lint: 0 errors, 3 warnings (file length / track density: readability of the HTML only).
- Loudness: −16.1 LUFS integrated, LRA 2.8 LU, true peak −1.3 dBTP (ebur128 on the share file).
- Flash / black-frame scan of all 1353 frames: none.
- **Lip sync:** the stock `tools/qa_checks.py` reports −1/+1 on two face shots. Those shots have a slow push-in
  (scale 1 → 1.035) that the stock check doesn't model. `sync_check.py` (this folder) models each layout's
  transform (split: +540 px shift; face/punch: push-in; punch: 1.3×) and compares 30 points, two per scene,
  against `assets/aroll.mp4` at offsets −3…+3: **best offset 0 at all 30**:
  At frame 370, the stock checker's −1, frames 369 and 370 are nearly identical (Saagii is still), so that
  single point can't separate 0 from −1. Frame 991 resolves clearly to 0 once the push is modelled.
  Seek accuracy of the checker was verified against select-by-index (identical frames).

```
s00  split       frame    24 (  0.80s) best offset +0 err 5.44 margin 2.81
s00  split       frame    57 (  1.90s) best offset +0 err 5.88 margin 3.70
s01  face        frame    91 (  3.03s) best offset +0 err 2.70 margin 1.69
s01  face        frame   103 (  3.43s) best offset +0 err 3.10 margin 3.02
s02  split       frame   144 (  4.80s) best offset +0 err 5.47 margin 1.27
s02  split       frame   186 (  6.20s) best offset +0 err 5.97 margin 3.42
s03  punch       frame   231 (  7.70s) best offset +0 err 3.05 margin 0.63
s03  punch       frame   251 (  8.37s) best offset +0 err 2.57 margin 4.51
s04  split       frame   286 (  9.53s) best offset +0 err 5.43 margin 1.23
s04  split       frame   315 ( 10.50s) best offset +0 err 5.51 margin 0.88
s05  face        frame   356 ( 11.87s) best offset +0 err 2.84 margin 0.89
s05  face        frame   384 ( 12.80s) best offset +0 err 2.83 margin 1.79
s06  broll-split frame   496 ( 16.53s) best offset +0 err 5.72 margin 0.83
s06  broll-split frame   619 ( 20.63s) best offset +0 err 6.18 margin 3.20
s07  punch       frame   721 ( 24.03s) best offset +0 err 2.67 margin 1.52
s07  punch       frame   735 ( 24.50s) best offset +0 err 2.69 margin 2.60
s08  broll-split frame   783 ( 26.10s) best offset +0 err 6.02 margin 0.64
s08  broll-split frame   835 ( 27.83s) best offset +0 err 6.03 margin 1.37
s09  split       frame   899 ( 29.97s) best offset +0 err 5.30 margin 3.02
s09  split       frame   934 ( 31.13s) best offset +0 err 5.42 margin 1.34
s10  face        frame   979 ( 32.63s) best offset +0 err 3.19 margin 3.47
s10  face        frame  1003 ( 33.43s) best offset +0 err 2.81 margin 2.96
s11  punch       frame  1036 ( 34.53s) best offset +0 err 2.62 margin 1.84
s11  punch       frame  1056 ( 35.20s) best offset +0 err 2.74 margin 4.24
s12  face        frame  1098 ( 36.60s) best offset +0 err 3.07 margin 1.39
s12  face        frame  1135 ( 37.83s) best offset +0 err 2.87 margin 2.43
s13  punch       frame  1183 ( 39.43s) best offset +0 err 2.54 margin 2.48
s13  punch       frame  1210 ( 40.33s) best offset +0 err 2.40 margin 1.67
s14  split       frame  1267 ( 42.23s) best offset +0 err 5.71 margin 2.01
s14  split       frame  1316 ( 43.87s) best offset +0 err 5.59 margin 3.00
all zero: True
```

- Fresh ASR (faster-whisper large-v3) of the delivered audio (`assets/delivered.asr.json`): all 163 words present in order. Differences
  from `script.txt`: "dead" heard as "data" (mishearing, consistent across passes), "B-roll" tokenised as
  "b roll", and **the "and" before "the video you're watching" (35.25 s) is not recognised.** The envelope
  shows it inside the kept range (raw 87.72–87.92 s, −31 to −35 dB), but ASR misses it in every pass on the
  cut. Possibly a swallowed "an'". Unverified by ear.
- Decoded audio of v1 and v2 is identical (MD5 `66a23b8859f65b82689404189b6b4df5`), so the ASR and loudness
  results carry over.

## Visual inspection (frames from the encoded file)

- First 2.5 s frame by frame (75 frames): frame 0 shows the dim `1:00:00` timer and the first caption on the
  seam; the timer flickers on at frames 28–31 ("one hour"), counts down from frame 43, and the target chip
  lands at ~56. Nothing over the mouth.
- One frame per scene (15) at full size; strips across the three glitch transitions (8.83 s, 29.10 s,
  35.67 s): glitch bars last 4 frames, never full-frame; no bar crosses the mouth on the face-shot glitch.
- Captions: 66 chunks, 29 % Mint. On the seam (split), chest (face) or lower chest (punch), never over the
  mouth/chin in the inspected frames.
- Brand: only sheet colours (plus the darker Graphite edge), only Space Grotesk + Inter, Mint text only on
  Graphite/black. No code rain, circuit boards, robots or brains. No Studio 21 logo on screen (open question).
- Every number on screen is spoken or measured from this edit: 1:00:00 limit, 30–60 min, 5:00:00, 5×,
  1:41.6 → 0:45.1, 249 → 163 words, 1 → 26 clips, the 26-block cut strip.

## Revisions

- v1 → v2: the monitor PiP showed for one frame over the payoff glitch (clip ended exactly on the cut);
  now ends a frame early. "RESULT: WIN" was on screen ~5 frames; the punch-in now holds through "and this
  was" (cut moved to "episode"), so the badge holds ~0.85 s.
- Before v1 (snapshots): empty first-frame panel (timer now visible dim from frame 0); scramble digits
  read as plausible times ("1:04:02"), now mostly symbols; mini B-roll panel parked visibly above the
  monitor, now clipped; mini caption under the panel; readouts colliding with a label; export bar hidden by
  a same-frame `tl.set` ordering bug; episode panel empty for 0.6 s.

## Limits (what was not verified)

- I can't listen or watch in real time. Audio claims are measurements (loudness, envelopes, ASR), not
  listening. Motion was judged from frames and strips, not playback.
- No uninterrupted entertainment review; no audience data. The opening choice is editorial judgment.
- SFX (30 cues, 15 synthesized sounds, peaks −19 to −29 dBFS) are placed on visible actions; their feel is
  unheard.
- No music: none supplied. He says "put some background music on it" while the EQ graphic plays silently.
- The Studio 21 brand sheet is labelled "draft for approval".
