# Projects

One folder per video, named by a short slug. Only text is committed: plans, scripts, design notes,
verification records, and the composition HTML. Footage, renders, and audio stay out of git (`.gitignore`).
The raw clips live in Drive `studio_21/raw` and the finished videos in `studio_21/edited`.

To rebuild a project from scratch in a fresh session:

1. Fetch its raw clips from Drive into `projects/<slug>/raw/` (`tools/drive.sh fetch <id> <path>`).
2. `python3 tools/make_master.py projects/<slug> <takes in order>`
3. `python3 tools/build_edl.py projects/<slug> --render`, then re-ASR and `tools/align_words.py`
4. `python3 projects/<slug>/build_reel.py projects/<slug>` (needs the screen recording in `raw/`)
5. Render with HyperFrames (see the `studio21-edit` skill).

Validators and lint report missing media until steps 1–4 have run. That's expected for a fresh checkout.

| Project | Date | Delivered |
| --- | --- | --- |
| [arson-wraps-pitch](arson-wraps-pitch/) | 2026-10-16 | Draft v4: 60 s 9:16 pitch reel. Sent in chat; not yet in Drive `edited` (no upload token at the time) |
| [goat-academy-lesson](goat-academy-lesson/) | 2026-11-06 | Draft v1: 11m53s dead-space cut of a Mongolian whiteboard/chat screen recording, native 1660x1080. Sent in chat; not in Drive `edited` (no upload token) |
| [create-new-bot](create-new-bot/) | 2026-11-06 | Draft v1: 4m52s dead-space cut (from 8m50s) of an AI-agent chat screen recording, native 1660x1080, webcam top-left. Sent in chat; not in Drive `edited` (no upload token) |
