import requests


URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/080000.json"


def get_forecast():

    response = requests.get(URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    forecast = data[0]

    # 天気・風
    weather_series = forecast["timeSeries"][0]

    area_index = None

    for i, area in enumerate(weather_series["areas"]):
        if area["area"]["name"] == "南部":
            area_index = i
            break

    if area_index is None:
        raise ValueError("茨城県南部の予報が見つかりませんでした")

    area_weather = weather_series["areas"][area_index]

    weather = area_weather["weathers"][0]
    wind = area_weather["winds"][0]


    # 降水確率
    pop_series = forecast["timeSeries"][1]

    pop_area_index = None

    for i, area in enumerate(pop_series["areas"]):
        if area["area"]["name"] == "南部":
            pop_area_index = i
            break

    if pop_area_index is None:
        raise ValueError("茨城県南部の降水確率が見つかりませんでした")

    pop_area = pop_series["areas"][pop_area_index]

    pops = pop_area["pops"]
    pop_times = pop_series["timeDefines"]


    # 気温
    temp_series = forecast["timeSeries"][2]

    temp_area = None

    for area in temp_series["areas"]:
        if area["area"]["name"] == "土浦":
            temp_area = area
            break

    if temp_area is None:
        raise ValueError("土浦の気温予報が見つかりませんでした")

    temps = temp_area["temps"]
    temp_times = temp_series["timeDefines"]

    print("気温データ確認")
    for time, temp in zip(temp_times, temps):
        print(time, temp)

    # Discord用文字列
    message = "【茨城県南部 今日の天気】\n\n"
    message += f"天気：{weather}\n"
    message += f"風：{wind}\n"

    if len(temps) >= 2:
        message += f"最低気温：{temps[0]} ℃\n"
        message += f"最高気温：{temps[1]} ℃\n"

    message += "\n降水確率\n"

    for time, pop in zip(pop_times, pops):
        hour = time[11:16]
        message += f"{hour}～：{pop} %\n"

    return message


if __name__ == "__main__":
    print(get_forecast())