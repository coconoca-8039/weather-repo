# Weather Discord

NOAAの数値予報モデル GFS のデータを取得し、
日本周辺の気象図をPythonで生成してDiscordへ送信する個人用システム。

現在はMacBook上で実行。
将来的にはRaspberry Piでの定期自動実行を想定している。

---

## システム概要

処理の流れは以下。

1. Herbieを使用してGFSデータを取得
2. xarrayで必要な気象要素を抽出
3. Matplotlib / Cartopyで日本周辺を描画
4. PNGとして `images/` に保存
5. Discord Webhookを使用して5枚まとめて送信

GFSの完成済み天気図画像を取得しているのではなく、
GFSの数値データからPythonで独自に気象図を生成している。

---

## データ

使用モデル：

GFS (Global Forecast System)

米国NOAA/NCEPが運用する全球数値予報モデル。

Herbieでは以下を指定。

```python
model="gfs"
product="pgrb2.0p25"
```

`pgrb2.0p25` は0.25度格子のGRIB2データ。

実行時にはHerbieが利用可能な最新GFSサイクルを検索する。

ログ例：

```text
model=gfs
product=pgrb2.0p25
2026-Aug-22 06:00 UTC F00
GRIB2 @ aws
```

今回の取得では、NOAAがAWS Open Dataとして公開している
GFSデータが使用されている。

---

# 作成する気象図

対象範囲は概ね

- 経度：100°E ～ 160°E
- 緯度：15°N ～ 60°N

として、日本とその周辺を表示する。

## Surface

ファイル：

```text
ASurface.py
images/surface.png
```

表示内容：

- 海面更正気圧
- 6時間積算降水量

海面更正気圧を等圧線として表示する。
等圧線間隔は4 hPa。

降水量は背景色として表示。

気圧線および気圧値は、降水域との視認性を確保するため
シアン系の色を使用。

地上図のみ、最新GFSの初期値 F00 から
6時間後の F06 を使用している。

タイトル：

```text
GFS Surface Pressure + 6-hour Precipitation (F06)
```

---

## 850 hPa

ファイル：

```text
A850hPa.py
images/850hPa.png
```

表示内容：

- 850 hPa 気温
- 850 hPa ジオポテンシャル高度
- 850 hPa 風

気温を背景色として表示。

カラーマップは `viridis` を使用し、
他の高層図と色調をある程度統一している。

ジオポテンシャル高度はシアンの等高度線。

風は黒の矢羽根で表示。
GFSの0.25度格子をそのまま描くと密集するため、
格子を間引いて表示している。

タイトル：

```text
GFS 850 hPa Temperature + Geopotential Height + Wind
```

主な用途：

暖気・寒気の分布と、その移流を風と合わせて確認する。

---

## 700 hPa

ファイル：

```text
A700hPa.py
images/700hPa.png
```

表示内容：

- 700 hPa ジオポテンシャル高度
- 700 hPa 相対湿度
- 700 hPa 鉛直流

相対湿度を背景色として表示。

ジオポテンシャル高度をシアンの等高度線として表示。

鉛直流は黒の等値線として表示。
負の鉛直流を上昇流として見る。

タイトル：

```text
GFS 700 hPa Height + Relative Humidity + Vertical Velocity
```

主な用途：

中層の湿潤域と上昇流の位置関係を見る。

特に、

「湿っている領域」と「上昇流」

が重なっている場所を確認する。

※ 情報量が多く、現在の5枚の中では比較的複雑な図。

---

## 500 hPa

ファイル：

```text
A500hPa.py
images/500hPa.png
```

表示内容：

- 500 hPa ジオポテンシャル高度
- 500 hPa 絶対渦度

絶対渦度を背景色として表示。

ジオポテンシャル高度を等高度線として重ねる。

タイトル：

```text
GFS 500 hPa Geopotential Height + Absolute Vorticity
```

主な用途：

- トラフ
- リッジ
- 寒冷渦
- 上空の大規模な流れ

などの把握。

---

## 300 hPa

ファイル：

```text
A300hPa.py
images/300hPa.png
```

表示内容：

- 300 hPa ジオポテンシャル高度
- 300 hPa 風速
- 300 hPa 風

U成分とV成分から風速を計算。

```python
wind_speed = np.sqrt(u ** 2 + v ** 2)
```

風速を背景色として表示。

ジオポテンシャル高度はシアンの等高度線。

風向・風速は黒の矢羽根として表示。

タイトル：

```text
GFS 300 hPa Geopotential Height + Wind Speed + Wind
```

主な用途：

上層の偏西風およびジェット気流の位置・蛇行を確認する。

---

# 画像保存

生成画像は以下に保存。

```text
images/
    surface.png
    850hPa.png
    700hPa.png
    500hPa.png
    300hPa.png
```

ファイル名は固定。

実行するたびに前回の画像を上書きする。

過去画像は現在の仕様では保存しない。

Matplotlibでは概ね以下の形式で保存。

```python
plt.savefig(
    "images/500hPa.png",
    dpi=150,
    bbox_inches="tight"
)

plt.close()
```

自動実行時に画像ウィンドウが開いて処理が停止しないよう、
`plt.show()` は使用せず `plt.close()` を使用する。

---

# Discord送信

Discord Webhookを使用。

Botは使用していない。

Pythonの `requests` からWebhookへHTTP POSTし、
生成した5枚のPNGを一つのDiscordメッセージに添付する。

送信メッセージ：

```text
GFS Weather Charts
```

Webhook URLは外部へ公開しないこと。
Webhook URLを知っている第三者は投稿できるため、
認証情報として扱う。

---

# 一括実行

`run_all.sh` から各Pythonファイルを順番に実行する。

```bash
#!/bin/bash

cd "$(dirname "$0")" || exit 1

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

python3 discord_send.py
echo "Discord Send Fin"

echo "=== Weather charts complete ==="
```

macOSでは `python` ではなく `python3` を使用。

実行：

```bash
./run_all.sh
```

初回のみ実行権限を付与する。

```bash
chmod +x run_all.sh
```

---

# ディレクトリ構成

```text
weather_discord/
    README.md
    run_all.sh
    discord_send.py

    ASurface.py
    A850hPa.py
    A700hPa.py
    A500hPa.py
    A300hPa.py

    images/
        surface.png
        850hPa.png
        700hPa.png
        500hPa.png
        300hPa.png
```

---

# 主なPythonライブラリ

- Herbie
- xarray
- Matplotlib
- Cartopy
- NumPy
- requests

HerbieがGFSデータの検索・取得を担当。

xarrayでGRIB2から取得した気象データを扱い、
Matplotlib / Cartopyで地図として描画する。

requestsはDiscord Webhookへの送信に使用する。

---

# 現在の運用

現在はMacBookから手動実行。

出勤前などに、

```bash
./run_all.sh
```

を実行すると、

GFS取得
→ 5枚の気象図生成
→ PNG上書き
→ Discord送信

まで連続して実行される。

---

# 今後

最終目標はRaspberry Piへ移行して定期自動実行すること。

Macで自動化する場合はmacOS標準の `launchd` も利用可能。

前線については、GFSデータに完成済みの前線線がそのまま
格納されているわけではないため、現在は描画していない。

将来的には気温・相当温位・風などから前線候補を解析する処理を
追加する余地がある。