#!/bin/bash
set -euo pipefail

# =============================================================================
# Sound Asset Setup Script
# =============================================================================
# Downloads royalty-free sound effects for the ICFES Leveling mobile app.
#
# Required sounds (9 total):
#   ding.mp3    - Correct answer chime
#   wrong.mp3   - Incorrect answer buzz
#   fanfare.mp3 - Lesson complete celebration
#   tick.mp3    - XP counter tick
#   levelup.mp3 - Level up celebration
#   combo.mp3   - Combo milestone hit
#   coin.mp3    - Gold/currency earned
#   click.mp3   - Button press
#   whoosh.mp3  - Transition/swipe
#
# Option 1: Run this script to generate silent placeholders (app compiles, no audio)
# Option 2: Replace the files manually with real sounds from:
#   - https://freesound.org (CC0 license)
#   - https://opengameart.org (various open licenses)
#   - https://mixkit.co/free-sound-effects/ (free license)
# =============================================================================

SOUNDS_DIR="apps/mobile/assets/sounds"

echo "==> Setting up sound assets in ${SOUNDS_DIR}"

# Ensure directory exists
mkdir -p "${SOUNDS_DIR}"

# Check if ffmpeg is available for generating silent MP3s
if command -v ffmpeg &> /dev/null; then
    echo "==> ffmpeg found. Generating minimal silent MP3 placeholders..."

    SOUNDS=(ding wrong fanfare tick levelup combo coin click whoosh)

    for sound in "${SOUNDS[@]}"; do
        target="${SOUNDS_DIR}/${sound}.mp3"
        if [ -f "${target}" ] && [ "$(stat -c%s "${target}" 2>/dev/null || stat -f%z "${target}" 2>/dev/null)" -gt 100 ]; then
            echo "    [skip] ${sound}.mp3 already exists"
        else
            # Generate a 100ms silent MP3 (~2KB)
            ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 0.1 -codec:a libmp3lame -b:a 32k "${target}" 2>/dev/null
            echo "    [created] ${sound}.mp3 (silent placeholder)"
        fi
    done

    echo ""
    echo "==> Placeholders created. The app will compile and run without audio."
    echo "==> Replace these files with real sound effects before production release."
else
    echo "==> ffmpeg not found. Cannot generate placeholders automatically."
    echo ""
    echo "To set up sounds manually:"
    echo "  1. Download MP3 sound effects (see sources above)"
    echo "  2. Place them in: ${SOUNDS_DIR}/"
    echo "  3. Required filenames:"
    echo "     ding.mp3, wrong.mp3, fanfare.mp3, tick.mp3,"
    echo "     levelup.mp3, combo.mp3, coin.mp3, click.mp3, whoosh.mp3"
    echo ""
    echo "Or install ffmpeg and re-run this script for silent placeholders:"
    echo "  macOS:   brew install ffmpeg"
    echo "  Ubuntu:  sudo apt install ffmpeg"
    echo "  Windows: winget install ffmpeg"
fi

echo "==> Done."
