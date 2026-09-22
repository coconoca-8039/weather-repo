#!/bin/bash

# Weather chart generators run concurrently, while Discord senders keep their
# original order. This script is compatible with the Bash version bundled with
# macOS (it does not require `wait -n`).

set -u

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd) || exit 1

if [ -z "${DISCORD_WEBHOOK_URL:-}" ]; then
    SECRETS_FILE="$SCRIPT_DIR/../secrets.env"

    if [ ! -r "$SECRETS_FILE" ]; then
        echo "Secret file not found or unreadable: $SECRETS_FILE" >&2
        exit 1
    fi

    set -a
    # shellcheck source=/dev/null
    source "$SECRETS_FILE"
    set +a
fi

cd "$SCRIPT_DIR" || exit 1

START_TIME=$(date +%s)

print_elapsed_time() {
    status=$?
    end_time=$(date +%s)
    elapsed=$((end_time - START_TIME))
    hours=$((elapsed / 3600))
    minutes=$(((elapsed % 3600) / 60))
    seconds=$((elapsed % 60))

    printf 'Total processing time: %02d:%02d:%02d\n' \
        "$hours" "$minutes" "$seconds"

    return "$status"
}

trap print_elapsed_time EXIT

MAX_JOBS=3
PIDS=()
NAMES=()

run_chart() {
    script="$1"

    # Wait until a worker slot is available.
    while [ "$(jobs -pr | wc -l | tr -d ' ')" -ge "$MAX_JOBS" ]; do
        sleep 0.2
    done

    echo "[START] $script"
    (
        if python3 "$script"; then
            echo "[FINISH] $script"
        else
            status=$?
            echo "[ERROR] $script (exit $status)" >&2
            exit "$status"
        fi
    ) &

    PIDS+=("$!")
    NAMES+=("$script")
}

echo "=== Weather charts start (max $MAX_JOBS parallel jobs) ==="

run_chart "scripts/ASurface.py"
run_chart "scripts/A850hPa.py"
run_chart "scripts/A700hPa.py"
run_chart "scripts/A500hPa.py"
run_chart "scripts/A300hPa.py"
run_chart "scripts/cloud_cover.py"
run_chart "scripts/300hPa_pacific.py"
run_chart "scripts/vertical_temp_rh_u.py"
run_chart "scripts/skewt.py"
run_chart "scripts/thrtae_wind.py"
run_chart "scripts/dewpoint_upward.py"

chart_failed=0
i=0
while [ "$i" -lt "${#PIDS[@]}" ]; do
    if ! wait "${PIDS[$i]}"; then
        echo "Chart generation failed: ${NAMES[$i]}" >&2
        chart_failed=1
    fi
    i=$((i + 1))
done

if [ "$chart_failed" -ne 0 ]; then
    echo "Discord sending was skipped because one or more charts failed." >&2
    exit 1
fi

echo "=== Weather charts complete ==="

# Keep message order deterministic and avoid simultaneous webhook posts.
python3 scripts/discord_jma_send.py || exit 1
python3 scripts/discord_send.py || exit 1
python3 scripts/discord_send_vertical.py || exit 1
python3 scripts/wiki_weather.py || exit 1
# python3 scripts/discord_word_send.py || exit 1

echo "Finish"
