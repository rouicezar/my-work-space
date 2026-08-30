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

if [ -e "$APP" ]; then
  echo "error: app destination already exists" >&2
  exit 2
fi

swift build --package-path "$SCRIPT_DIR" --configuration release --product MacAIWorkOSApp
BIN_DIRECTORY=$(swift build --package-path "$SCRIPT_DIR" --configuration release --show-bin-path)

mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
install -m 0755 "$BIN_DIRECTORY/MacAIWorkOSApp" "$APP/Contents/MacOS/MacAIWorkOSApp"
install -m 0644 "$SCRIPT_DIR/App-Info.plist" "$APP/Contents/Info.plist"
install -m 0644 "$REPOSITORY_ROOT/config/product-manifest.json" "$APP/Contents/Resources/product-manifest.json"
install -m 0644 "$REPOSITORY_ROOT/config/hardware-profiles.yaml" "$APP/Contents/Resources/hardware-profiles.json"
install -m 0644 "$REPOSITORY_ROOT/config/upstreams.json" "$APP/Contents/Resources/upstreams.json"
install -m 0644 "$REPOSITORY_ROOT/config/models.json" "$APP/Contents/Resources/models.json"
install -m 0644 "$REPOSITORY_ROOT/config/cloud-providers.json" "$APP/Contents/Resources/cloud-providers.json"
install -m 0644 "$REPOSITORY_ROOT/config/local-model-profiles.json" "$APP/Contents/Resources/local-model-profiles.json"
mkdir -p "$APP/Contents/Resources/evidence/runtime"
install -m 0644 "$REPOSITORY_ROOT/evidence/runtime/private-local-task-2026-08-30.md" "$APP/Contents/Resources/evidence/runtime/private-local-task-2026-08-30.md"
"$SCRIPT_DIR/build-supervisor.sh" "$APP/Contents/Helpers/Supervisor"

MEMORY_RUNTIME="$APP/Contents/Helpers/MemoryRuntime"
mkdir -p "$MEMORY_RUNTIME/mac_ai_work_os/adapters"
install -m 0644 "$REPOSITORY_ROOT/scripts/semantica_memory_runtime.py" "$MEMORY_RUNTIME/semantica_memory_runtime.py"
for SOURCE in __init__.py broker.py governed_memory.py memory_service.py omlx_embeddings.py semantica_backend.py semantica_runtime.py models.py; do
  install -m 0644 "$REPOSITORY_ROOT/mac_ai_work_os/$SOURCE" "$MEMORY_RUNTIME/mac_ai_work_os/$SOURCE"
done
install -m 0644 "$REPOSITORY_ROOT/mac_ai_work_os/adapters/__init__.py" "$MEMORY_RUNTIME/mac_ai_work_os/adapters/__init__.py"
install -m 0644 "$REPOSITORY_ROOT/mac_ai_work_os/adapters/semantica.py" "$MEMORY_RUNTIME/mac_ai_work_os/adapters/semantica.py"

codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"
echo "$APP"
