import os
import pandas as pd
import requests

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
CSV_FILE = "weather_exam_glossary_master_55_65.csv"

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


def get_random_terms():
    df = pd.read_csv(CSV_FILE)

    selected = df.sample(n=10)

    messages = []

    for _, row in selected.iterrows():
        message = (
            f"【{row['用語']}】\n"
            f"科目：{row['科目']}\n"
            f"{row['解説']}\n"
            f"\u200b\n"
        )

        messages.append(message)

    return messages


def main():
    messages = get_random_terms()

    for message in messages:
        send_discord(message)

    send_discord("──────────")

    print("Discordへの送信が完了しました")


if __name__ == "__main__":
    main()
