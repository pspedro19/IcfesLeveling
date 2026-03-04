#!/usr/bin/env bash
# =============================================================================
# setup-release.sh — Pre-release verification for ICFES Leveling mobile app
#
# Checks all prerequisites needed before publishing to Google Play / App Store.
#
# Usage:
#   bash scripts/setup-release.sh
# =============================================================================
set -uo pipefail

MOBILE_DIR="apps/mobile"
ERRORS=0
WARNINGS=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass()    { echo -e "  ${GREEN}PASS${NC}  $*"; }
fail()    { echo -e "  ${RED}FAIL${NC}  $*"; ERRORS=$((ERRORS + 1)); }
warn_msg(){ echo -e "  ${YELLOW}WARN${NC}  $*"; WARNINGS=$((WARNINGS + 1)); }
section() { echo -e "\n${CYAN}[$1]${NC} $2"; }

echo "============================================================"
echo "  ICFES Leveling — Mobile Release Checklist"
echo "============================================================"

# ----- 1. Prerequisites -----
section "1/7" "Prerequisites"

if command -v flutter &>/dev/null; then
    FLUTTER_VER=$(flutter --version 2>/dev/null | head -1)
    pass "Flutter: $FLUTTER_VER"
else
    fail "Flutter SDK not found in PATH"
fi

if command -v keytool &>/dev/null; then
    pass "keytool available (Java JDK)"
else
    fail "keytool not found — install Java JDK"
fi

if command -v firebase &>/dev/null; then
    pass "Firebase CLI installed"
else
    warn_msg "Firebase CLI not installed (npm install -g firebase-tools)"
fi

if command -v flutterfire &>/dev/null; then
    pass "FlutterFire CLI installed"
else
    fail "FlutterFire CLI not installed (dart pub global activate flutterfire_cli)"
fi

# ----- 2. Keystore -----
section "2/7" "Android Keystore"

KEYSTORE_PATH="${MOBILE_DIR}/android/app/release-keystore.jks"
KEY_PROPS="${MOBILE_DIR}/android/key.properties"

if [ -f "$KEYSTORE_PATH" ]; then
    pass "Keystore found: $KEYSTORE_PATH"
else
    fail "Keystore missing: $KEYSTORE_PATH"
    echo "       Generate with:"
    echo "       keytool -genkey -v -keystore $KEYSTORE_PATH \\"
    echo "         -keyalg RSA -keysize 2048 -validity 10000 \\"
    echo "         -alias icfes-leveling"
fi

if [ -f "$KEY_PROPS" ]; then
    pass "key.properties found"
else
    fail "key.properties missing: $KEY_PROPS"
    echo "       Create with:"
    echo "       storePassword=<password>"
    echo "       keyPassword=<password>"
    echo "       keyAlias=icfes-leveling"
    echo "       storeFile=release-keystore.jks"
fi

# ----- 3. Firebase -----
section "3/7" "Firebase Configuration"

FIREBASE_OPTIONS="${MOBILE_DIR}/lib/firebase_options.dart"
GOOGLE_SERVICES="${MOBILE_DIR}/android/app/google-services.json"
GOOGLE_INFO="${MOBILE_DIR}/ios/Runner/GoogleService-Info.plist"

if [ -f "$FIREBASE_OPTIONS" ]; then
    pass "firebase_options.dart found"
else
    fail "firebase_options.dart missing — run: flutterfire configure"
fi

if [ -f "$GOOGLE_SERVICES" ]; then
    pass "google-services.json found (Android)"
else
    fail "google-services.json missing — run: flutterfire configure"
fi

if [ -f "$GOOGLE_INFO" ]; then
    pass "GoogleService-Info.plist found (iOS)"
else
    warn_msg "GoogleService-Info.plist missing (only needed for iOS)"
fi

# ----- 4. AdMob -----
section "4/7" "AdMob Configuration"

MANIFEST="${MOBILE_DIR}/android/app/src/main/AndroidManifest.xml"
ADMOB_SERVICE="${MOBILE_DIR}/lib/core/services/admob_service.dart"
TEST_ADMOB_APP_ID="ca-app-pub-3940256099942544"

if [ -f "$MANIFEST" ]; then
    if grep -q "$TEST_ADMOB_APP_ID" "$MANIFEST" 2>/dev/null; then
        warn_msg "AndroidManifest.xml still uses TEST AdMob App ID"
    else
        pass "AndroidManifest.xml uses production AdMob App ID"
    fi
else
    fail "AndroidManifest.xml not found"
fi

if [ -f "$ADMOB_SERVICE" ]; then
    if grep -q "$TEST_ADMOB_APP_ID" "$ADMOB_SERVICE" 2>/dev/null; then
        warn_msg "admob_service.dart still uses TEST ad unit IDs"
    else
        pass "admob_service.dart uses production ad unit IDs"
    fi
else
    warn_msg "admob_service.dart not found"
fi

# ----- 5. Sound Assets -----
section "5/7" "Sound Assets"

SOUNDS_DIR="${MOBILE_DIR}/assets/sounds"
EXPECTED_SOUNDS=(
    "correct.mp3"
    "wrong.mp3"
    "level_up.mp3"
    "battle_start.mp3"
    "battle_win.mp3"
    "battle_lose.mp3"
    "combo.mp3"
    "click.mp3"
    "notification.mp3"
)

if [ -d "$SOUNDS_DIR" ]; then
    FOUND_SOUNDS=0
    MISSING_SOUNDS=0
    for sound in "${EXPECTED_SOUNDS[@]}"; do
        if [ -f "${SOUNDS_DIR}/${sound}" ]; then
            FOUND_SOUNDS=$((FOUND_SOUNDS + 1))
        else
            MISSING_SOUNDS=$((MISSING_SOUNDS + 1))
        fi
    done
    if [ "$MISSING_SOUNDS" -eq 0 ]; then
        pass "All ${#EXPECTED_SOUNDS[@]} sound files present"
    else
        warn_msg "${MISSING_SOUNDS}/${#EXPECTED_SOUNDS[@]} sound files missing"
        echo "       Run: bash scripts/setup-sound-assets.sh"
    fi
else
    warn_msg "Sound assets directory missing: $SOUNDS_DIR"
fi

# ----- 6. App Icons -----
section "6/7" "App Icons"

ICONS_DIR="${MOBILE_DIR}/assets/icons"
ANDROID_ICON="${MOBILE_DIR}/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png"

if [ -d "$ICONS_DIR" ] && [ "$(ls -1 "$ICONS_DIR"/*.png 2>/dev/null | wc -l)" -gt 0 ]; then
    ICON_COUNT=$(ls -1 "$ICONS_DIR"/*.png 2>/dev/null | wc -l)
    pass "App icons found: ${ICON_COUNT} PNG files"
else
    warn_msg "App icons missing from $ICONS_DIR"
fi

if [ -f "$ANDROID_ICON" ]; then
    pass "Android launcher icon present"
else
    warn_msg "Android launcher icon missing (run flutter_launcher_icons)"
fi

# ----- 7. Environment Config -----
section "7/7" "Environment & Build"

PUBSPEC="${MOBILE_DIR}/pubspec.yaml"
if [ -f "$PUBSPEC" ]; then
    VERSION=$(grep "^version:" "$PUBSPEC" 2>/dev/null | head -1)
    pass "pubspec.yaml found — $VERSION"
else
    fail "pubspec.yaml not found"
fi

# Check .env is NOT committed
if [ -f ".env" ]; then
    if git ls-files --error-unmatch .env >/dev/null 2>&1; then
        warn_msg ".env is tracked by git — add to .gitignore"
    else
        pass ".env exists but is NOT tracked by git"
    fi
fi

# ----- Summary -----
echo ""
echo "============================================================"
echo "  Summary: ${ERRORS} ERRORS, ${WARNINGS} WARNINGS"
echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo -e "  Status: ${GREEN}READY FOR RELEASE${NC} (fix warnings if any)"
else
    echo -e "  Status: ${RED}NOT READY${NC} — fix ${ERRORS} error(s) first"
fi
echo "============================================================"

exit "$ERRORS"
