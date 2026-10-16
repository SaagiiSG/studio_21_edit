# studio_21_edit

Saagii's video-editing studio for Claude Code cloud sessions. Attach this repo to a session, and Claude
already knows the workflow, the Drive folders, the brand, and every lesson from past edits.

```
Drive studio_21/raw  →  cut + captions + motion graphics (HyperFrames)  →  Drive studio_21/edited
```

## Each session

1. Start a Claude Code cloud session with **this repo** selected, using an environment that has full network
   access (or at least Drive + Hugging Face allowed).
2. The SessionStart hook installs everything (about 1 minute on a fresh container): Nate Herk's
   [herk-edit-kit](https://github.com/nateherkai/herk-edit-kit) at a pinned commit, its npm deps,
   faster-whisper, rclone, and the browser path.
3. Drop clips in Drive `studio_21/raw` (a subfolder per video is cleanest), then tell Claude what the video
   is: e.g. *"Edit the clips in raw/arson into a 9:16 reel with the studio brand, template hook-proof-cta."*

## One-time setup: let Claude upload to Drive

The Drive connector can read Drive but can't upload video. Give the environment your own Drive token:

1. On your computer: install rclone (`brew install rclone`), then run `rclone authorize "drive"`. Sign in
   with the Google account that owns `studio_21` and approve.
2. It prints a JSON token (`{"access_token":...,"refresh_token":...}`). Copy all of it.
3. In Claude Code: cloud environment menu (session title bar) → **Edit** → add an environment variable /
   secret named **`GDRIVE_RCLONE_TOKEN`** with that JSON as the value. Don't paste it into the chat.
4. New sessions pick it up. `tools/drive.sh check` confirms it works.

That token gives full access to your Drive. Revoke it any time at
[myaccount.google.com/permissions](https://myaccount.google.com/permissions) (rclone).
Without it, Claude still works: share raw files as "Anyone with the link can view", and Claude hands you
the finished video in the chat instead of putting it in `edited`.

## What's here

| Path | What |
| --- | --- |
| `CLAUDE.md` | Standing instructions every session reads |
| `.claude/skills/studio21-edit/` | The editing workflow + `references/lessons.md` (rules learned the hard way) |
| `.claude/hooks/session-start.sh` | Installs the toolchain in each cloud session |
| `tools/` | make_master, build_edl, transcribe, chunk_asr, align_words, qa_checks, encode_share, drive |
| `brand/` | Your brand guidelines (drop them here) |
| `templates/` | Your scripted video templates (drop them here) |
| `projects/` | One folder per video: plans and metadata only, no media |

## Credits

Editing engine: [herk-edit-kit](https://github.com/nateherkai/herk-edit-kit) by Nate Herk (MIT;
teaching-kit use permission in its `licenses/`). It's installed at runtime, not redistributed here.
Rendering by [HyperFrames](https://hyperframes.heygen.com); animation by GSAP. Transcription is local,
using faster-whisper (Whisper large-v3).
