import os

import requests
from jma_forecast import get_forecast

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

def send_discord(message):
    payload = {
        "content": message
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=10
    )

    response.raise_for_status()


def main():
    message = get_forecast()

    send_discord(message)
    send_discord("──────────")

    print("Discordへの送信が完了しました")


if __name__ == "__main__":
    main()
