#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUTPUT_DIRECTORY=$1
PACKAGE_ROOT="$OUTPUT_DIRECTORY/pkg-root"
PACKAGE="$OUTPUT_DIRECTORY/mac-ai-work-os-launcher.pkg"

swift build --package-path "$SCRIPT_DIR" --configuration release --product mac-ai-work-os-launcher
BIN_DIRECTORY=$(swift build --package-path "$SCRIPT_DIR" --configuration release --show-bin-path)

mkdir -p "$PACKAGE_ROOT/usr/local/bin"
install -m 0755 "$BIN_DIRECTORY/mac-ai-work-os-launcher" "$PACKAGE_ROOT/usr/local/bin/mac-ai-work-os-launcher"

pkgbuild \
  --root "$PACKAGE_ROOT" \
  --identifier dev.macaiworkos.launcher.prototype \
  --version 0.1.0 \
  --install-location / \
  "$PACKAGE"

pkgutil --check-signature "$PACKAGE" || true
echo "$PACKAGE"
