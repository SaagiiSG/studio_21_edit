# create-new-bot: VERIFY (draft v1, dead-space cut)

Source: Drive `studio_21/Goat academy AI video lessons/create new bot with dr egg bot'.mp4`
(id `16Zp9vd32QxaODVHkxtfotv-mK8xtiXjR`, 433,753,712 bytes, downloaded and size-matched).
1660x1080, H.264 SDR (bt709), 30 fps CFR, AAC stereo 48 kHz, 529.967 s, about 6.5 Mb/s.
Screen recording of an AI-agent chat UI (dr eggbot, Content CCO, Script Smith, Carousel Smith) with a whiteboard
moment near 1:30. Webcam bubble is TOP-LEFT in this recording. Only 171.9 s (32%) is speech.
Language not transcribed (the cut uses VAD + loudness + screen motion, not words).

Delivered: `renders/create-new-bot-deadspace.mp4`, 292.1 s, 1660x1080, 88,660,039 bytes.
sha256 `70c157af9e84f08c2877b4b76d26c6a057920caadc0b7f09f4a490256a1fb95a`

## What was cut

Same rules and settings as goat-academy-lesson v1 (which Saagii has not reviewed yet): remove only where Silero VAD
says "no speech" AND silencedetect (-38 dB, >= 0.18 s) says quiet. Gaps <= 0.5 s untouched. Longer gaps shortened to
0.35 s (screen still) or 1.5 s (screen busy). Only change: `--webcam-box 0,0,0.27,0.40` so face movement in the
top-left bubble does not count as screen activity (the default mask is bottom-left).

| Gap type | Kept | Cuts | Removed |
| --- | --- | --- | --- |
| head before first word | 0.3 s | 1 | 1.4 s |
| screen still | 0.35 s | 32 | 80.3 s |
| screen busy (plan kind "drawing") | 1.5 s | 17 | 155.7 s |
| tail after last word | 0.5 s | 1 | 0.4 s |

529.97 s -> 292.10 s (-237.9 s, 45%).

**"drawing" is a mislabel here.** Nothing is drawn in this video. In the biggest cuts, stills show Saagii silently
clicking and scrolling between agent chats (frames differ every few seconds): 3:11-3:48 (37 s), 5:59-6:36 (37 s),
6:43-7:00 (18 s), 7:50-8:04 (13 s), 5:37-5:50 (13 s). The final video jumps from one chat state to the next in those
places. 4:31-4:46 (15 s, "static") is waiting on the same screen.
Gentler options, measured with `--plan-only` and not rendered: `--keep-active 3` -> 5m14s, `--keep-active 5` -> 5m35s.

## Measurements (`tools/deadspace_verify.py`, `work/verify.json`)

- Video frames 8,763 = planned (292.1 s x 30). Audio 292.094 s vs video 292.100 s (-6 ms, AAC padding).
- Speech (VAD) source 171.9 s -> output 176.0 s (+2.3%); 129 -> 127 segments. No removal overlaps detected speech (0.000 s).
- Level +-20 ms around the 50 joins: median -54.5 dBFS, max -38.8 dBFS. The one join above -40 dBFS (output 159.07 s,
  source 237.0-238.87) has no VAD speech within +-1.2 s; a short click (-12 dBFS, gone in about 100 ms) sits before it and a low
  sound after it; the cut lands in a faint -39 dBFS tail under a 6 ms fade, and the next sound is protected by 0.2 s of quiet.
- Loudness: output -16.6 LUFS / -4.4 dBTP; source identical. Level not changed (within 0.6 LU of the -16 house default).
- Contact sheet of the output every 10 s: layout matches the source (chat threads, whiteboard at 1:30-1:40, webcam
  top-left throughout); no black, corrupt or frozen frames in those samples.

## Not verified (limits)

- I cannot listen or watch in real time. Nothing here says how it sounds or looks: no word-level check, no perceived-pacing
  check, no lip-sync measurement (sync is by construction: one ffmpeg pass, identical frame-quantised intervals for video and audio).
- VAD can miss quiet or unusual speech; the -38 dB check protects against most of that, but a clipped consonant would not show here.
- No transcript, so no check for stumbles or retakes (not part of a dead-space cut).
- Personal data on screen (agent chats with business content) was only seen in contact sheets, not reviewed second by second.
- Not uploaded to Drive (no `GDRIVE_RCLONE_TOKEN`); delivered in chat.
