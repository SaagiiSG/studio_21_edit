#!/bin/bash
# Google Drive transfers for Studio 21.
#
#   tools/drive.sh fetch <file-id> <dest-path>     download one file
#   tools/drive.sh fetch-folder <folder-id> <dir>  download every file in a folder (needs token)
#   tools/drive.sh upload <local-file> [folder-id] upload into studio_21/edited (default) or a given folder
#   tools/drive.sh check                           report which transfer modes are available
#
# Upload needs the environment secret GDRIVE_RCLONE_TOKEN (the JSON printed by `rclone authorize "drive"`).
# Without it, fetch falls back to the public download URL, which only works for files shared as
# "Anyone with the link can view", and upload is impossible (the Drive connector cannot carry video).
set -euo pipefail

EDITED_FOLDER_ID="1sklHMi4CL5ii8GHffBFTmW_T-dBra4XQ"   # studio_21/edited

have_token() { [ -n "${GDRIVE_RCLONE_TOKEN:-}" ] && command -v rclone >/dev/null 2>&1; }

rc() {
  RCLONE_CONFIG_GD_TYPE=drive RCLONE_CONFIG_GD_SCOPE=drive RCLONE_CONFIG_GD_TOKEN="$GDRIVE_RCLONE_TOKEN" \
    rclone --config /dev/null "$@"
}

cmd="${1:-check}"; shift || true
case "$cmd" in
  check)
    if have_token; then echo "Drive: rclone token present (fetch + upload available)"; rc lsd gd: --max-depth 1 >/dev/null && echo "Drive: token works";
    else echo "Drive: no GDRIVE_RCLONE_TOKEN (fetch needs link-sharing; upload unavailable)"; fi ;;
  fetch)
    id="$1"; dest="$2"; mkdir -p "$(dirname "$dest")"
    if have_token; then rc backend copyid gd: "$id" "$dest";
    else curl -sSL --fail --retry 4 --retry-delay 2 -o "$dest" "https://drive.usercontent.google.com/download?id=${id}&export=download&confirm=t"; fi
    ls -la "$dest" ;;
  fetch-folder)
    have_token || { echo "fetch-folder needs GDRIVE_RCLONE_TOKEN; list the folder with the Drive connector and fetch by id instead" >&2; exit 2; }
    rc copy gd: "$2" --drive-root-folder-id "$1" --progress ;;
  upload)
    have_token || { echo "upload needs GDRIVE_RCLONE_TOKEN (see README: one-time setup)" >&2; exit 2; }
    file="$1"; folder="${2:-$EDITED_FOLDER_ID}"
    rc copy "$file" gd: --drive-root-folder-id "$folder" --progress
    rc lsl gd: --drive-root-folder-id "$folder" --include "$(basename "$file")" ;;
  *) echo "unknown command: $cmd" >&2; exit 2 ;;
esac
