import os

import requests

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

images = [
    ("vertical_125E_temp_rh_u.png", "images/vertical_125E_temp_rh_u.png"),
    ("vertical_130E_temp_rh_u.png", "images/vertical_130E_temp_rh_u.png"),
    ("vertical_135E_temp_rh_u.png", "images/vertical_135E_temp_rh_u.png"),
    ("vertical_140E_temp_rh_u.png", "images/vertical_140E_temp_rh_u.png"),
    ("vertical_145E_temp_rh_u.png", "images/vertical_145E_temp_rh_u.png"),
    ("vertical_150E_temp_rh_u.png", "images/vertical_150E_temp_rh_u.png"),
    ("vertical_155E_temp_rh_u.png", "images/vertical_155E_temp_rh_u.png"),
]

files = {}

for i, (name, path) in enumerate(images):
    files[f"files[{i}]"] = (
        name,
        open(path, "rb"),
        "image/png"
    )

data = {
    "content": "GFS Weather Charts"
}

try:
    response = requests.post(
        WEBHOOK_URL,
        data=data,
        files=files
    )

    print("Discord status:", response.status_code)

finally:
    # 開いた画像ファイルをすべて閉じる
    for file_data in files.values():
        file_data[1].close()

separator_response = requests.post(
    WEBHOOK_URL,
    json={
        "content": "──────────"
    },
    timeout=10
)

separator_response.raise_for_status()

print(response.status_code)
