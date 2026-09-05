#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
OUTPUT_DIRECTORY=$1
APP="$OUTPUT_DIRECTORY/Forma AI.app"
APP_DIR="$SCRIPT_DIR/Sources/FormaAIApp"
APP_SOURCE="$APP_DIR/FormaAIApp.swift"

legacy_pattern() {
  pattern=$1
  message=$2
  if rg -q "$pattern" "$APP_DIR" --glob '*.swift'; then
    echo "error: $message" >&2
    rg -n "$pattern" "$APP_DIR" --glob '*.swift' >&2 || true
    exit 2
  fi
}

legacy_pattern 'ManifestOverview' 'deprecated ManifestOverview runtime shell is still referenced'
legacy_pattern 'NavigationSplitView' 'deprecated NavigationSplitView runtime shell is still referenced'
legacy_pattern 'WorkspaceSection' 'deprecated WorkspaceSection navigation is still referenced'
legacy_pattern 'dailyNavRow|dailySidebar|dailySupervisionRail' 'deprecated ManifestOverview sidebar helpers are still referenced'
legacy_pattern 'What would you like to work on\?' 'legacy English idle workbench copy is still referenced'
legacy_pattern 'struct DailyWorkbench: View' 'DailyWorkbench legacy runtime wrapper must not exist; use DailyWorkbenchShell(presentation: .production)'

if ! rg -q 'DailyWorkbenchShell\(presentation: \.production\)' "$APP_DIR/ProductRootView.swift"; then
  echo "error: ProductRootView must route to DailyWorkbenchShell(presentation: .production)" >&2
  exit 2
fi

if ! awk '
  /#else/ { in_release = 1 }
  in_release && /ProductRootView\(\)|DailyWorkbenchShell\(presentation: \.production\)/ { ok = 1 }
  /#endif/ { in_release = 0 }
  END { exit ok ? 0 : 1 }
' "$APP_SOURCE"; then
  echo "error: release branch must route through ProductRootView or DailyWorkbenchShell production presentation" >&2
  exit 2
fi


if ! rg -q 'LocalRuntimeControlPanel|ModelsProvidersControlPanel|DiagnosticsRecoveryControlPanel' "$APP_DIR/DailyWorkbenchShell.swift"; then
  echo "error: production shell must wire real settings control panels" >&2
  exit 2
fi

if ! rg -q 'download-model' "$REPOSITORY_ROOT/scripts/supervisor.py"; then
  echo "error: supervisor must expose download-model for first-run model preparation" >&2
  exit 2
fi

if ! rg -q 'DailyWorkbenchComposerSurface' "$APP_DIR/DailyWorkbenchShell.swift"; then
  echo "error: production shell must render DailyWorkbenchComposerSurface" >&2
  exit 2
fi

if ! rg -q 'settingsSectionRow\(\.memory' "$APP_DIR/DailyWorkbenchShell.swift"; then
  echo "error: production shell must use bilingual Daily Workbench settings surface" >&2
  exit 2
fi

if [ -e "$APP" ]; then
  echo "error: app destination already exists" >&2
  exit 2
fi

swift build --package-path "$SCRIPT_DIR" --configuration release --product FormaAIApp
BIN_DIRECTORY=$(swift build --package-path "$SCRIPT_DIR" --configuration release --show-bin-path)

mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
install -m 0755 "$BIN_DIRECTORY/FormaAIApp" "$APP/Contents/MacOS/FormaAIApp"
install -m 0644 "$SCRIPT_DIR/App-Info.plist" "$APP/Contents/Info.plist"
install -m 0644 "$SCRIPT_DIR/Resources/FormaAI.icns" "$APP/Contents/Resources/FormaAI.icns"
install -m 0644 "$REPOSITORY_ROOT/config/product-manifest.json" "$APP/Contents/Resources/product-manifest.json"
install -m 0644 "$REPOSITORY_ROOT/config/hardware-profiles.yaml" "$APP/Contents/Resources/hardware-profiles.json"
install -m 0644 "$REPOSITORY_ROOT/config/upstreams.json" "$APP/Contents/Resources/upstreams.json"
install -m 0644 "$REPOSITORY_ROOT/config/models.json" "$APP/Contents/Resources/models.json"
install -m 0644 "$REPOSITORY_ROOT/config/cloud-providers.json" "$APP/Contents/Resources/cloud-providers.json"
install -m 0644 "$REPOSITORY_ROOT/config/local-model-profiles.json" "$APP/Contents/Resources/local-model-profiles.json"
mkdir -p "$APP/Contents/Resources/evidence/runtime"
install -m 0644 "$REPOSITORY_ROOT/evidence/runtime/private-local-task-2026-08-30.md" "$APP/Contents/Resources/evidence/runtime/private-local-task-2026-08-30.md"
for EVIDENCE in private-local-agent-qwen3-4b-2026-09-05.md private-local-agent-qwen3-8b-2026-09-05.md; do
  install -m 0644 "$REPOSITORY_ROOT/evidence/runtime/$EVIDENCE" "$APP/Contents/Resources/evidence/runtime/$EVIDENCE"
done
mkdir -p "$APP/Contents/Resources/config" "$APP/Contents/Resources/scripts"
for CATALOG in upstreams.json models.json hardware-profiles.yaml cloud-providers.json local-model-profiles.json tool-routing.json; do
  install -m 0644 "$REPOSITORY_ROOT/config/$CATALOG" "$APP/Contents/Resources/config/$CATALOG"
done
install -m 0644 "$REPOSITORY_ROOT/scripts/qwen_governed_mcp.py" "$APP/Contents/Resources/scripts/qwen_governed_mcp.py"
"$SCRIPT_DIR/build-supervisor.sh" "$APP/Contents/Helpers/Supervisor"

MEMORY_RUNTIME="$APP/Contents/Helpers/MemoryRuntime"
mkdir -p "$MEMORY_RUNTIME/forma_ai/adapters"
install -m 0644 "$REPOSITORY_ROOT/scripts/semantica_memory_runtime.py" "$MEMORY_RUNTIME/semantica_memory_runtime.py"
for SOURCE in __init__.py broker.py governed_memory.py memory_service.py omlx_embeddings.py semantica_backend.py semantica_runtime.py models.py; do
  install -m 0644 "$REPOSITORY_ROOT/forma_ai/$SOURCE" "$MEMORY_RUNTIME/forma_ai/$SOURCE"
done
install -m 0644 "$REPOSITORY_ROOT/forma_ai/adapters/__init__.py" "$MEMORY_RUNTIME/forma_ai/adapters/__init__.py"
install -m 0644 "$REPOSITORY_ROOT/forma_ai/adapters/semantica.py" "$MEMORY_RUNTIME/forma_ai/adapters/semantica.py"

codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"
echo "$APP"
