#!/usr/bin/env bash
# Offline tests of bin/dsh-romeo against a fake ROMEO (tests/fake-romeo): fake ssh, romeollmtool,
# squeue and gateway, and a fake dsh that records how it was started. No network, no GPU.
#
#   tests/run.sh
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
FAKE=$HERE/fake-romeo/bin
T=$(mktemp -d "${TMPDIR:-/tmp}/dsh-romeo-test.XXXXXX")
REAL_DSH=$(command -v dsh || true)   # before the fake dsh comes first in PATH
PORT=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')

export FAKE_ROMEO_STATE=$T/state FAKE_ROMEO_HOME=$T/romeo-home FAKE_GATEWAY_PORT=$PORT FAKE_LOAD_SECONDS=2
export PATH=$FAKE:$PATH ROMEOLLMTOOL=$FAKE/romeollmtool DSH_ROMEO_DSH=$FAKE/dsh DSH_ROMEO_POLL=1
export DSH_ROMEO_CONFIG_DIR=$T/config DSH_ROMEO_SOCKET=$T/ctl DSH_ROMEO_PORT=$PORT
export ROMEO_SSH_HOST=romeo ROMEO_PROJECT=r000000
unset DSH_ROMEO_FICHE DSH_ROMEO_SEARXNG_URL DSH_ROMEO_EFFORT DSH_ROMEO_TIME
mkdir -p "$FAKE_ROMEO_STATE" "$FAKE_ROMEO_HOME"

python3 "$FAKE/gateway.py" "$PORT" &
gateway=$!
trap 'kill $gateway 2>/dev/null; rm -rf "$T"' EXIT
for _ in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.1; done

pass=0 fail=0
check() {  # check "name" condition...
  local name=$1; shift
  if "$@"; then pass=$((pass + 1)); printf '  ok    %s\n' "$name"
  else fail=$((fail + 1)); printf '  FAIL  %s\n' "$name"; printf '%s\n' "$out" | sed 's/^/        | /'; fi
}
has() { grep -q -- "$1" <<<"$out"; }
run() { out=$("$ROOT/bin/dsh-romeo" "$@" 2>&1); code=$?; }

echo "dsh-romeo offline tests"

run --version
check "--version" has "dsh-romeo 0."

run --status
check "status: gateway stopped, no job, tunnel closed" has "gateway stopped"
check "status: no model job" has "no model job of dsh-deepseek-v4.1-flash-1m"

run
check "start before --setup: fiche missing" has "not found on ROMEO. Run: dsh-romeo --setup"
check "start before --setup: exit 1" test "$code" = 1
check "start starts the gateway" test -e "$FAKE_ROMEO_STATE/gateway"

run --setup
check "--setup copies the fiche" test -f "$FAKE_ROMEO_HOME/.romeollmtool/configs/dsh-deepseek-v4.1-flash-1m.yaml"

run
check "start without a job: says --launch" has "Start one with: dsh-romeo --launch"
check "start without a job: exit 1" test "$code" = 1

ROMEO_PROJECT='' run --launch
check "--launch without a project: says so" has "no project code"

run --launch 9
check "--launch 9: refused" has "--launch takes 1 to 8 jobs"

run --launch
check "--launch: job submitted" has "model job 900001 submitted"
check "--launch: waits, then ready" has "ready"
check "--launch: dsh web with the overlay" grep -q "args: web --patch $DSH_ROMEO_CONFIG_DIR/dsh.patch.yml" "$FAKE_ROMEO_STATE/dsh-call"
check "--launch: dsh gets the gateway key" grep -q "key: test-key" "$FAKE_ROMEO_STATE/dsh-call"
overlay=$DSH_ROMEO_CONFIG_DIR/dsh.patch.yml
check "overlay: served model of the fiche" grep -q "model: dsh-deepseek-v4.1-flash-1m" "$overlay"
check "overlay: 1M context from the fiche" grep -q "contextWindow: 1048576" "$overlay"
check "overlay: output limit from the fiche" grep -q "maxTokens: 262144" "$overlay"
check "overlay: tunnel port" grep -q "baseURL: http://127.0.0.1:$PORT/v1" "$overlay"
check "overlay: no key written" bash -c "! grep -q test-key '$overlay'"
check "overlay: no web search by default" bash -c "! grep -q searxng '$overlay'"

run headless "fix the tests"
check "job running: straight to dsh" bash -c "! grep -q submitted <<<'$out'"
check "headless and its task pass through" grep -q "args: headless --patch .* fix the tests" "$FAKE_ROMEO_STATE/dsh-call"

DSH_ROMEO_SEARXNG_URL=http://127.0.0.1:8888 run
check "overlay: SearXNG when configured" grep -q 'baseURL: "http://127.0.0.1:8888"' "$overlay"
check "overlay: SearXNG plugin path" grep -q "name: $ROOT/share/web-search-searxng.mjs" "$overlay"

run --status
check "status: job listed" has "model job 900001 running"

run --stop
check "--stop: job stopped" has "model job 900001 stopped"
check "--stop: no job left" bash -c "! grep -q . '$FAKE_ROMEO_STATE/jobs'"

DSH_ROMEO_FICHE=no-such-fiche run
check "unknown fiche: clear error" has "fiche 'no-such-fiche' not found"

FAKE_ROMEO_UNREACHABLE=1 DSH_ROMEO_SOCKET=$T/ctl2 run --status
check "ROMEO unreachable: clear error" has "cannot connect to 'romeo' over SSH"

if [ -n "$REAL_DSH" ]; then
  # The overlay must compose with the real dsh (fresh DSH_HOME, no network needed).
  DSH_ROMEO_SEARXNG_URL=http://127.0.0.1:8888 run
  composed=$(cd "$T" && DSH_HOME=$T/dsh-home "$REAL_DSH" --profile headless --patch "$overlay" --dump-config 2>&1)
  out=$composed
  check "real dsh: romeo is the default provider" has "provider: romeo"
  check "real dsh: SearXNG plugin inserted" has "id: dsh-romeo-searxng"
fi

for f in "$ROOT/bin/dsh-romeo" "$ROOT/install.sh" "$HERE/run.sh"; do
  out=$(bash -n "$f" 2>&1); check "syntax: $(basename "$f")" test -z "$out"
done
if command -v shellcheck >/dev/null; then
  out=$(shellcheck -S warning "$ROOT/bin/dsh-romeo" "$ROOT/install.sh" 2>&1); check "shellcheck" test -z "$out"
fi

echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
