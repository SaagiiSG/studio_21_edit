#!/bin/bash
# Studio 21 SessionStart hook: installs the editing toolchain in Claude Code cloud sessions.
# Idempotent and non-interactive. Each step warns instead of failing, so a blocked host never stops the
# session from starting; the summary at the end says what is missing.
set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
KIT="$ROOT/vendor/herk-edit-kit"
KIT_REPO="https://github.com/nateherkai/herk-edit-kit"
KIT_COMMIT="10511e5af86fc47756ea89803b397422e2d89284"   # herk-edit-kit v2.0.0, verified 2026-10-16
RCLONE_VERSION="v1.75.2"
missing=()
log() { echo "[studio21] $*" >&2; }

# 1. herk-edit-kit at the pinned commit (sparse: no showcase videos, no teaching projects).
if [ "$(git -C "$KIT" rev-parse HEAD 2>/dev/null)" != "$KIT_COMMIT" ]; then
  log "installing herk-edit-kit @ ${KIT_COMMIT:0:7}"
  rm -rf "$KIT" && mkdir -p "$KIT"
  if ( cd "$KIT" && git init -q && git remote add origin "$KIT_REPO" \
       && GIT_LFS_SKIP_SMUDGE=1 git fetch -q --depth 1 --filter=blob:none origin "$KIT_COMMIT" \
       && git sparse-checkout set --no-cone '/*' '!/examples/showcase/' '!/video-projects/' \
       && GIT_LFS_SKIP_SMUDGE=1 git checkout -q FETCH_HEAD ); then
    log "herk-edit-kit ready"
  else
    missing+=("herk-edit-kit (github.com blocked?)")
  fi
fi

# 2. Kit npm dependencies (HyperFrames, GSAP, Playwright library; browsers are preinstalled).
if [ -f "$KIT/package.json" ] && [ ! -x "$KIT/node_modules/.bin/hyperframes" ]; then
  log "npm install (kit)"
  ( cd "$KIT" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --no-audit --no-fund --loglevel=error ) \
    || missing+=("kit npm deps")
fi

# 3. Local transcription (the Whisper model itself downloads from Hugging Face on first use).
if ! python3 -c "import faster_whisper" 2>/dev/null; then
  log "pip install faster-whisper"
  pip install --quiet faster-whisper 2>/dev/null || pip install --quiet --break-system-packages faster-whisper \
    || missing+=("faster-whisper")
fi

# 4. rclone for Drive transfers (used only when the GDRIVE_RCLONE_TOKEN secret exists).
if ! command -v rclone >/dev/null 2>&1; then
  log "installing rclone $RCLONE_VERSION"
  tmp="$(mktemp -d)"
  if curl -sSfL -o "$tmp/rclone.zip" "https://downloads.rclone.org/$RCLONE_VERSION/rclone-$RCLONE_VERSION-linux-amd64.zip" \
     && unzip -q "$tmp/rclone.zip" -d "$tmp" && install -m 0755 "$tmp"/rclone-*/rclone /usr/local/bin/rclone; then
    log "rclone ready"
  else
    missing+=("rclone (downloads.rclone.org blocked?)")
  fi
  rm -rf "$tmp"
fi

# 5. Session environment.
browser="$(ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell 2>/dev/null | tail -1)"
[ -n "$browser" ] || missing+=("headless Chromium under /opt/pw-browsers")
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export STUDIO21_KIT=\"$KIT\""
    echo "export HYPERFRAMES_NO_TELEMETRY=1"
    [ -n "$browser" ] && echo "export HYPERFRAMES_BROWSER_PATH=\"$browser\""
  } >> "$CLAUDE_ENV_FILE"
fi

# 6. Summary.
for tool in ffmpeg ffprobe node; do command -v "$tool" >/dev/null 2>&1 || missing+=("$tool"); done
if [ ${#missing[@]} -eq 0 ]; then
  log "toolchain ready (kit ${KIT_COMMIT:0:7}, $(rclone version 2>/dev/null | head -1), browser ok)"
else
  log "toolchain INCOMPLETE: ${missing[*]}"
fi
[ -n "${GDRIVE_RCLONE_TOKEN:-}" ] && log "Drive upload: token present" || log "Drive upload: no GDRIVE_RCLONE_TOKEN (see README)"
exit 0
