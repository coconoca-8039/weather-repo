import os

import requests

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

images = [
    ("surface.png", "images/surface.png"),
    ("850hPa.png", "images/850hPa.png"),
    ("700hPa.png", "images/700hPa.png"),
    ("500hPa.png", "images/500hPa.png"),
    ("300hPa.png", "images/300hPa.png"),
    ("cloud_cover.png", "images/cloud_cover.png"),
    ("300hPa_pacific.png", "images/300hPa_pacific.png"),
    ("skewt_tsuchiura.png","images/skewt_tsuchiura.png"),
    ("thetae_wind_140E.png", "images/thetae_wind_140E.png"),
    ("dewpoint_depression_upward_motion_140E.png", "images/dewpoint_depression_upward_motion_140E.png")
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
