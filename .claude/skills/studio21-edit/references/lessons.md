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
- **Check the spoken language before transcribing.** `transcribe.py` and `chunk_asr.py` default to English; set
  `STUDIO21_LANG=mn` for Mongolian (Saagii's AI lessons). Whisper's Mongolian is weaker, so for a plain dead-space cut
  don't depend on words: use `tools/deadspace_cut.py` (VAD + loudness + screen motion).
- **Calibrate the silence threshold to the mic.** A -38 dB threshold suits noisy phone footage; the 2026-11-06 screen-recording
  audio had a floor of about -70 dBFS (measure it first). Total "silence" swung from 36% to 53% between -54 and -38 dB, so a loudness threshold alone is a guess.
  Require VAD "no speech" AND quiet before cutting.
- **Silent is not dead on a screen recording.** Drawing/writing in silence has lots of pixel change; typing a prompt has
  almost none but is still on-screen content. `deadspace_cut.py` keeps more of busy gaps and tells you the longest cuts
  (those are usually typing) so Saagii can ask for a speed-up instead.
- **Webcam bubble position changes between recordings** (bottom-left in the whiteboard lesson, top-left in the agent-chat
  one). Look at a full-size frame and pass `--webcam-box x0,y0,x1,y1` to `deadspace_cut.py`; otherwise face movement
  reads as screen activity and silent gaps are kept too long. Its "drawing" kind just means "screen busy": in a chat
  recording it is silent scrolling/clicking between threads, so read the stills before describing the cuts.
- Render the cut in **one ffmpeg pass** with frame-exact trims (`trim=start_frame/end_frame`). Never
  encode segments separately and concatenate; that drifts lip sync.

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
