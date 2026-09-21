import os

import requests
import random

url = "https://ja.wikipedia.org/w/api.php"

discord_webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

categories = [
    "Category:大気力学",
    "Category:大気熱力学",
    "Category:気候学",
    "Category:気象衛星"
]

headers = {
    "User-Agent": "weather-discord-bot/1.0"
}

message = "【今日の気象Wikipedia】\n\n"

for category in categories:
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmnamespace": 0,
        "cmlimit": 500,
        "format": "json"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    articles = data["query"]["categorymembers"]

    article = random.choice(articles)

    title = article["title"]
    page_url = "https://ja.wikipedia.org/wiki/" + requests.utils.quote(
        title.replace(" ", "_")
    )

    category_name = category.replace("Category:", "")

    message += f"【{category_name}】\n"
    message += f"{title}\n"
    message += f"{page_url}\n\n"


payload = {
    "content": message
}

response = requests.post(discord_webhook_url, json=payload)

if response.status_code == 204:
    print("Discord送信成功")
else:
    print("Discord送信失敗")
    print(response.status_code)
    print(response.text)

separator_response = requests.post(
    discord_webhook_url,
    json={
        "content": "──────────"
    },
    timeout=10
)
