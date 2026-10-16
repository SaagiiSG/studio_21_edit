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
| [tuition-ep02-ai-editor](tuition-ep02-ai-editor/) | 2026-10-16 | Draft v2: 45 s 9:16, cyberpunk take on the Studio 21 brand. Sent in chat; not yet in Drive `edited` (no upload token) |
