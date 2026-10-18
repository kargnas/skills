#!/usr/bin/env bash
# Self-check for start-server.sh and stop-server.sh: a session boots under the
# project's .agents/ai-tasks/ui-buffet/ path, publishes server-info, and
# stops cleanly. Never pass --open here; CI has no browser to launch.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d)
SESSION_DIR=""
cleanup() {
  [ -n "$SESSION_DIR" ] && bash "$SCRIPT_DIR/stop-server.sh" "$SESSION_DIR" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT

assert_contains() { case "$1" in *"$2"*) ;; *) printf 'missing: %s\nin:\n%s\n' "$2" "$1" >&2; exit 1 ;; esac; }

# --background forces the path Claude Code users get even when CODEX_CI is set.
started=$(bash "$SCRIPT_DIR/start-server.sh" --project-dir "$TMP" --background) \
  || { printf 'start failed: %s\n' "$started" >&2; exit 1; }
assert_contains "$started" 'server-started'
assert_contains "$started" "$TMP/.agents/ai-tasks/ui-buffet/"
SESSION_DIR=$(node -e 'process.stdout.write(require("path").dirname(JSON.parse(process.argv[1]).state_dir))' "$started")
[ -f "$SESSION_DIR/state/server-info" ]

# Auth gate and dotfile refusal, the behaviour the skill relies on.
key=$(node -e 'process.stdout.write(new URL(JSON.parse(process.argv[1]).url).searchParams.get("key"))' "$started")
base=$(node -e 'process.stdout.write(new URL(JSON.parse(process.argv[1]).url).origin)' "$started")
code() { curl -s -o /dev/null -w '%{http_code}' "$1"; }
[ "$(code "$base/")" = 403 ]
[ "$(code "$base/?key=$key")" = 200 ]
[ "$(code "$base/files/.last-token?key=$key")" = 404 ]
# The bootstrap page mirrors the key into a cookie; a cookie-only request must pass.
jar="$TMP/cookies"
curl -s -o /dev/null -c "$jar" "$base/?key=$key"
[ "$(curl -s -o /dev/null -w '%{http_code}' -b "$jar" "$base/")" = 200 ]
pid=$(cat "$SESSION_DIR/state/server.pid")
kill -0 "$pid"

stopped=$(bash "$SCRIPT_DIR/stop-server.sh" "$SESSION_DIR")
SESSION_DIR=""
assert_contains "$stopped" '"status": "stopped"'
if kill -0 "$pid" 2>/dev/null; then echo "server $pid still alive after stop" >&2; exit 1; fi
echo "preview-server.test.sh: ok"
