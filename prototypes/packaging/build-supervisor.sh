#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
OUTPUT_DIRECTORY=$1

case "$OUTPUT_DIRECTORY" in
  /*) ;;
  *) echo "error: output directory must be absolute" >&2; exit 2 ;;
esac

if [ -e "$OUTPUT_DIRECTORY" ]; then
  echo "error: output directory already exists" >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is required to build the frozen Supervisor" >&2
  exit 2
fi

BUILD_DIRECTORY=$(mktemp -d "${TMPDIR:-/tmp}/forma-ai-supervisor.XXXXXX")
trap 'rm -rf "$BUILD_DIRECTORY"' EXIT INT TERM

uv tool run --from pyinstaller==6.22.2 pyinstaller \
  --noconfirm \
  --clean \
  --onedir \
  --name forma-ai-supervisor \
  --paths "$REPOSITORY_ROOT" \
  --distpath "$BUILD_DIRECTORY/dist" \
  --workpath "$BUILD_DIRECTORY/work" \
  --specpath "$BUILD_DIRECTORY/spec" \
  "$REPOSITORY_ROOT/scripts/supervisor.py"

ditto "$BUILD_DIRECTORY/dist/forma-ai-supervisor" "$OUTPUT_DIRECTORY"

EXECUTABLE="$OUTPUT_DIRECTORY/forma-ai-supervisor"
file "$EXECUTABLE" | grep -q 'arm64'
codesign --verify --strict --verbose=2 "$EXECUTABLE"
echo "$OUTPUT_DIRECTORY"
