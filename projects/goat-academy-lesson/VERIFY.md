# goat-academy-lesson: VERIFY (draft v1, dead-space cut)

Source: Drive `studio_21/Goat academy AI video lessons/Cap 2026-11-06 at 12.56.18.mp4`
(id `11KVsFl8LEndh1IpNd6b2n9r9hxxClvPe`, 452,882,175 bytes, downloaded and size-matched).
1660x1080, H.264 SDR (bt709), 30 fps CFR, AAC stereo 48 kHz, 962.733 s. Screen recording with a webcam bubble.
Language: Mongolian. Not transcribed: the cut uses VAD + loudness + screen motion, not words.

Delivered: `renders/goat-academy-lesson-deadspace.mp4`, 713.5 s, 1660x1080, 103,688,514 bytes.
sha256 `42b6929e016f79b6b2623b8f8ac92b42756489acbb120fbda560f8bd8297b33c`

## What was cut

Rule (`tools/deadspace_cut.py`, params in `deadspace-plan.json`): remove only where Silero VAD says "no speech"
AND silencedetect (-38 dB, >= 0.18 s) says quiet. Gaps <= 0.5 s are left alone. Longer gaps are shortened:

| Screen during the gap | Kept | Cuts | Removed |
| --- | --- | --- | --- |
| still (typing, waiting) | 0.35 s | 86 | 171.0 s |
| busy (drawing, writing; >= 20% of 10 fps frames change) | 1.5 s | 49 | 77.5 s |
| tail after last word | 0.5 s | 1 | 0.7 s |

962.7 s -> 713.5 s (-249.2 s, 136 joins). Biggest cuts, source time:
12:18-12:56 (37 s), 11:28-11:52 (24 s), 13:56-14:10 (14 s), 2:34-2:43 (9 s, drawing), 12:09-12:18 (9 s),
14:47-14:55 (9 s). From stills, the chat-window ones are Saagii silently typing a prompt into the message box;
the final prompt appears after the cut without the typing. The 2:34 one is a label being written on the whiteboard.

## Measurements (`tools/deadspace_verify.py`, `work/verify.json`)

- Video frames 21,405 = planned (713.5 s x 30). Audio 713.474 s vs video 713.500 s (-26 ms, AAC end padding).
- Speech (VAD) source 430.9 s -> output 438.2 s (+1.7%); 367 -> 366 segments. No removal overlaps detected speech (0.000 s).
- Level +-20 ms around the 136 joins: median -58.3 dBFS, max -39.2 dBFS. One join (output 154.47 s, source 188.83)
  has a faint -39 dBFS blip in the last 20 ms of the kept pause, under a 6 ms fade-out; next speech onset is protected
  by 0.22 s of quiet. Everything else sits at the noise floor.
- Loudness: output -18.1 LUFS / -4.4 dBTP; source -18.2 LUFS / -4.5 dBTP. Audio level was not changed
  (house default is -16 LUFS; a +2 dB gain would give about -16.1 LUFS / -2.4 dBTP).
- Contact sheet of the output every 20 s: whiteboard / chat structure matches the source; no black, corrupt or frozen frames
  in those samples.

## Not verified (limits)

- I cannot listen or watch in real time. Nothing here says how it sounds or looks: no word-level check, no
  perceived-pacing check, no lip-sync measurement (sync is by construction: one ffmpeg pass, identical frame-quantised
  intervals for video and audio).
- VAD can miss quiet or unusual speech onsets. The -38 dB check protects against most of that, but a clipped
  consonant would not show in these numbers.
- No transcript, so no check for stumbles or retakes (not part of a dead-space cut).
- Personal data on screen (chat window with business figures, Finder window) was only seen in contact sheets, not reviewed second by second.
- Not uploaded to Drive `studio_21/edited` (no `GDRIVE_RCLONE_TOKEN`); delivered in chat.
