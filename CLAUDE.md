# Studio 21 edit — standing instructions

This repo is Saagii's video-editing studio for Claude Code cloud sessions. It turns raw recordings in
Google Drive into finished short-form videos. Read this file, then load the `studio21-edit` skill for any
editing request.

## Who you work for

- Saagii (Saran-Ochir). Values honesty over everything: no sugarcoating, no bluffing. Say plainly what was
  verified, what wasn't, and what you couldn't do. Never claim you listened to or watched something you
  only measured.
- Messages are often dictated (voice-to-text): expect mis-transcriptions ("69 by 16" = 9:16, "rap" = wrap,
  "Wispr Flow" usually means Whisper). Ask only when the meaning really changes the work.

## Where things live

| What | Where |
| --- | --- |
| Raw footage | Google Drive `studio_21/raw` — folder id `1Vma5Tf48OGztnKLu4HjT2QjncqHLZv3D` |
| Finished videos | Google Drive `studio_21/edited` — folder id `1sklHMi4CL5ii8GHffBFTmW_T-dBra4XQ` |
| Drive root folder | `studio_21` — folder id `1QBHn0kA-S6eG4cd4_AVoBtn6mwQOGp90` (in Saagii's My Drive) |
| Editing engine | `vendor/herk-edit-kit` (Nate Herk's kit, MIT, pinned commit; installed by the SessionStart hook, not committed) |
| Our tools | `tools/` (master, EDL, ASR, alignment, QA, share encode, Drive transfer) |
| Brand guidelines | `brand/` — read `brand/BRAND.md` (if present) before any design work |
| Scripted templates | `templates/` — use the one Saagii names, or the closest fit |
| One folder per video | `projects/<slug>/` — plans and metadata committed; media never committed |
| Hard-won rules | `.claude/skills/studio21-edit/references/lessons.md` — read before editing |

## Session environment

- The SessionStart hook (`.claude/hooks/session-start.sh`) installs the kit, npm deps, faster-whisper and
  rclone, and exports `HYPERFRAMES_BROWSER_PATH`, `HYPERFRAMES_NO_TELEMETRY=1`, `STUDIO21_KIT`. If a tool is
  missing, re-run the hook: `CLAUDE_CODE_REMOTE=true .claude/hooks/session-start.sh`.
- Network: the environment needs Drive (`drive.google.com`, `drive.usercontent.google.com`) and Hugging Face
  (`huggingface.co` + its CDN) for the Whisper model. Full network access is simplest. If a host is blocked,
  say which one and how to allow it; don't fake the missing step.
- Drive transfers: run `tools/drive.sh check` first.
  - With the `GDRIVE_RCLONE_TOKEN` environment secret: fetch folders and upload finished videos straight to
    `studio_21/edited`.
  - Without it: list files with the Google Drive connector, download only link-shared files, and hand the
    finished video to Saagii with SendUserFile. The Drive connector cannot upload video (it takes file
    content inline). Never ask Saagii to paste a token into chat.
- The container is wiped when the session ends. Anything worth keeping goes into this repo (text) or Drive
  (media) before you finish.

## Commit rules

- Commit `projects/<slug>/` plans: DESIGN.md, VERIFY.md, edl-plan.json, script.txt, index.html, assets/*.json,
  and the project's build script. Never commit footage, renders, audio, or personal data.
- When Saagii gives a note on a draft, fix the edit, then offer to write the note into
  `references/lessons.md` (or the skill) as a rule, so the next video starts from it.
- Push to the branch the session tells you to; this repo's default branch is `main`.

## Defaults when Saagii gives no direction

- 1080x1920, 30 fps, −16 LUFS, true peak ≤ −1.5 dBTP.
- Hook in the first 3 seconds with a visible change by second 3; every shot moves; captions in one boxed
  style, 1–3 words, never over the mouth.
- No music unless Saagii supplies or approves a track he has rights to. No paid generation (Kie.ai,
  ElevenLabs, Higgsfield) without asking first and stating the cost.
