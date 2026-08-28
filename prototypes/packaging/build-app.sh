#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
OUTPUT_DIRECTORY=$1
APP="$OUTPUT_DIRECTORY/Mac AI Work OS.app"

swift build --package-path "$SCRIPT_DIR" --configuration release --product MacAIWorkOSApp
BIN_DIRECTORY=$(swift build --package-path "$SCRIPT_DIR" --configuration release --show-bin-path)

mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
install -m 0755 "$BIN_DIRECTORY/MacAIWorkOSApp" "$APP/Contents/MacOS/MacAIWorkOSApp"
install -m 0644 "$SCRIPT_DIR/App-Info.plist" "$APP/Contents/Info.plist"
install -m 0644 "$REPOSITORY_ROOT/config/product-manifest.json" "$APP/Contents/Resources/product-manifest.json"

codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"
echo "$APP"
