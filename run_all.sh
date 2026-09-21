#!/bin/bash

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd) || exit 1
SECRETS_FILE="$SCRIPT_DIR/../secrets.env"

if [ ! -r "$SECRETS_FILE" ]; then
    echo "Secret file not found or unreadable: $SECRETS_FILE" >&2
    exit 1
fi

set -a
# shellcheck source=/dev/null
source "$SECRETS_FILE"
set +a

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

echo "=== Weather charts start ==="

python3 ASurface.py
echo "Surface Fin"

python3 A850hPa.py
echo "850 hPa Fin"

python3 A700hPa.py
echo "700 hPa Fin"

python3 A500hPa.py
echo "500 hPa Fin"

python3 A300hPa.py
echo "300 hPa Fin"

python3 cloud_cover.py
echo "Cloud Cover Fin"

python3 300hPa_pacific.py

python3 vertical_temp_rh_u.py

python3 skewt.py

python3 thrtae_wind.py

python3 dewpoint_upward.py

echo "=== Weather charts complete ==="

python3 discord_jma_send.py

python3 discord_send.py

python3 discord_send_vertical.py

python3 wiki_weather.py

python3 discord_word_send.py

echo "Finish"
