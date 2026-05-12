#!/usr/bin/env bash
# Apply all venv patches after a pip install or venv rebuild.
# Run from the repo root: bash patches/apply.sh

set -e

VENV="${VENV:-/opt/egyptian/venv}"
SITE_PACKAGES="$VENV/lib/python3.11/site-packages"

apply() {
    local patch_file="$1"
    local target="$2"
    echo "Applying $patch_file → $target"
    if patch --dry-run -p1 -d "$SITE_PACKAGES" < "$patch_file" > /dev/null 2>&1; then
        patch -p1 -d "$SITE_PACKAGES" < "$patch_file"
        echo "  OK"
    else
        echo "  Already applied or conflict — skipping"
    fi
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# gnupg: handle BrokenPipeError when GPG exits early on non-PGP files
# Symptom: document upload fails silently (size/mimetype stay NULL) for PNG
# files whose header bytes are misidentified as OpenPGP packets.
apply "$SCRIPT_DIR/gnupg_broken_pipe.patch" "gnupg.py"

echo "Done."
