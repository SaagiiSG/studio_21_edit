# Lessons (each one cost time; follow them)

Add to this file whenever Saagii gives a note or a step goes wrong. Format: rule, then why.

## Footage

- **iPhone clips are HLG HDR (10-bit, bt2020, arib-std-b67).** Tone-map before anything else, or the reel
  comes out washed out. `make_master.py` uses zscale + `tonemap=mobius:param=0.3`, which looks natural on
  skin. A plain transfer conversion blows out faces.
- iPhone video is very slightly VFR (29.998). Force `fps=30` and trim to whole frames so take offsets are exact.
- Rotation comes from the display matrix (rotation=90). ffmpeg auto-rotates on decode, giving 1080x1920.
- Screen recordings from a Retina Mac are 2940x1912 @ 60 fps. Crop in source pixels at panel ratio
  (1080x880 → 1.2273). The macOS menu bar takes the top ~66 px at times; crop it out.
- Fast scrolls through a section can last < 0.5 s. Don't slow them past ~0.6x (60 fps source starts to
  judder). Play the real scroll at 0.6x, then hold the frame where the section fills the panel, with a
  push-in. Mark `heldFrame` in the footage ledger.
- Check every second of a screen recording for personal data (names, phones, emails in forms), file
  pickers, desktop sidebars, and unrelated sections (an FAQ sliding in at the end of a shot).

## Transcription and cutting

- Local transcription works well: faster-whisper large-v3, int8, CPU. About 2–3 min for a minute of audio on 4 cores.
  The model (~3 GB) comes from Hugging Face on first use.
- The PyAV version installed alongside faster-whisper breaks `decode_audio` (`metadata_errors` TypeError).
  `tools/transcribe.py` reads 16 kHz WAV with `wave` and passes a numpy array instead.
- **Whisper word timestamps absorb pauses** (one word can span 2.5 s). Never pick cut points from word
  gaps. Use silencedetect (−38 dB, ≥0.18 s) and loudness envelopes.
- silencedetect reports silence_end ~60 ms after the real onset. Leave more of the kept pause before the
  next word (`pre_share` 0.45), or plosive onsets get tight.
- Trimmed pauses keep 0.18 s (0.26 s after a ≥0.9 s pause). Tails like a fading "s" can still sit at −48 dB
  past the detected silence start; extend the segment end there.
- **Always re-transcribe the rendered cut.** The first pass smoothed over "and the AI does this math… and
  AI does its magic" and a repeated "of their car". Only the re-ASR of the cut showed them.
- Quiet speech gives run-to-run ASR differences ("want the same" → "want to sing"). If there's no cut within
  ~1 s, it's ASR, not damage. Captions come from the reviewed `script.txt`, never raw ASR.
- Render the cut in **one ffmpeg pass** with frame-exact trims (`trim=start_frame/end_frame`). Never
  encode segments separately and concatenate; that drifts lip sync.
- Saagii marks retakes by saying **"cut"** out loud. Search the raw ASR for "cut" and treat each one as the
  end of an abandoned take; keep the take after the last "cut" for that line.
- Two silences split by a 20 ms blip can each fall under `min_pause` and leave a 0.5 s gap untrimmed
  ("I … gave myself"). Look for adjacent sub-threshold silences and split the segment by hand.
- `tools/align_words.py` clamps each word into the keep holding its midpoint. A short word right after a
  join can land in the keep *before* the cut ("the" before "video you're watching"), and a short word before
  a join can collapse to 40 ms. Check the words on both sides of every join and re-anchor them from the
  loudness envelope (`assets/align-fixes.json`, applied by the project's build script).
- Whisper's first pass on a fresh model download prints nothing for minutes (download, then the first 30 s
  window). It isn't stuck; check CPU time before restarting it.

## HyperFrames composition

- Browser: `HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell`
  (the hook exports it). `npx hyperframes browser ensure` isn't needed.
- Keep `data-start="0"` on the root composition. The kit's `scripts/preflight.mjs` calls that a blocker when
  videos have data-start, but HyperFrames 0.7.109 lint exempts the root and renders play fine (verified).
- Videos must sit in **non-timed** wrappers. Animate the wrapper (push-ins, layout moves), never the video.
- Captions: each chunk starts 2 frames before its first word, **but never before the previous chunk's last
  word ends**. Otherwise same-track clips overlap and lint fails.
- A strike-through bar: put it inside the word's span with `left/right` insets. A `:not(#id)` rule outranked
  the id rule and gave two strikes zero width.
- One long speaker `<video>` plus GSAP `tl.set` layout changes at cut times (split / face / punch-in) keeps
  lip sync exact. Measured offset 0 frames at 8 points.
- A 60 s 1080x1920 reel renders in ~4.5 min at standard quality (138 MB). Deliver a 2-pass 5 Mb/s share copy
  (~39 MB) with the audio copied.
- A `<video>` clip whose `data-duration` ends exactly on a cut still shows on the cut frame. End inset
  (picture-in-picture) clips one frame early, or the old clip flashes over the next scene for a frame.
- Two `tl.set` calls meant for "the same" frame can run in the wrong order when one time is rounded
  (24.833) and the other isn't (24.833333): the hide lands after the show and the element never appears.
  Put the show at `max(start + 0.02, t)` or use one rounding everywhere.
- `tl.fromTo` / `tl.from` render their start state immediately at build time. For anything visible on
  frame 0 with a CSS initial state (e.g. a dim timer), pass `immediateRender:false`.
- Live text (countdowns, counters, scrambles) works with a proxy tween + `onUpdate` writing `textContent`,
  seeded by frame index for scrambles. Deterministic and renders correctly (verified frame by frame).
- `tools/qa_checks.py` lip sync compares unscaled frames, so a push-in on face shots reports a false ±1.
  Either keep face shots static or check with the layout transform modelled (split shift, push scale);
  that check gave offset 0 everywhere on tuition-ep02.
- Use `hyperframes snapshot --at t1,t2,… --no-end` for a quick look at graphics before a full render
  (~1 min for 30 frames vs ~6 min to render).

## Sound

- Voice chain: highpass 80 Hz, light compression, two-pass loudnorm to −16 LUFS / −1.5 dBTP. Measure on the
  delivered file.
- SFX only on visible actions (slider sweep, photo drop, UI clicks, strikes, nodes landing), peaks −20 to
  −26 dBFS, with varied sounds. No whoosh on every cut.
- Music: only tracks Saagii supplies or approves. Music files inside other kit projects belong to those projects.

## Delivery and environment

- The Drive connector can list, read, and create folders and small text files. It **cannot upload video**: the
  content has to be inline in the tool call. Use `tools/drive.sh upload` with the `GDRIVE_RCLONE_TOKEN`
  secret, or SendUserFile.
- Downloading Drive files without a token needs "Anyone with the link can view" plus network access to
  `drive.usercontent.google.com`.
- The session's GitHub integration can't create new repositories. Saagii creates them on github.com, then
  `add_repo` with push access.
