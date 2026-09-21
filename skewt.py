from herbie import HerbieLatest
import matplotlib.pyplot as plt
import numpy as np

from metpy.plots import SkewT
from metpy.units import units
import metpy.calc as mpcalc

plt.rcParams["font.family"] = "Hiragino Sans"

# 最新GFS F00
H = HerbieLatest(
    model="gfs",
    product="pgrb2.0p25",
    fxx=0
)

# 土浦
lat = 36.08
lon = 140.20

# 軽めにするため気圧面は絞る
levels = "1000|900|800|700|600|500|400|300|200|100"

# 必要最小限のデータ取得
temperature = H.xarray(
    f":TMP:({levels}) mb"
)

humidity = H.xarray(
    f":RH:({levels}) mb"
)

wind_u = H.xarray(
    f":UGRD:({levels}) mb"
)

wind_v = H.xarray(
    f":VGRD:({levels}) mb"
)

# 1地点だけ取得
temp_point = temperature["t"].sel(
    latitude=lat,
    longitude=lon,
    method="nearest"
)

rh_point = humidity["r"].sel(
    latitude=lat,
    longitude=lon,
    method="nearest"
)

u_point = wind_u["u"].sel(
    latitude=lat,
    longitude=lon,
    method="nearest"
)

v_point = wind_v["v"].sel(
    latitude=lat,
    longitude=lon,
    method="nearest"
)

# 配列
pressure = temp_point.isobaricInhPa.values * units.hPa
temperature_k = temp_point.values * units.kelvin
temperature_c = temperature_k.to(units.degC)

# RHは0〜100%の範囲に丸める
rh = np.clip(rh_point.values, 1, 100) / 100.0

# 露点温度
dewpoint = mpcalc.dewpoint_from_relative_humidity(
    temperature_k,
    rh
).to(units.degC)

# 風
u_wind = u_point.values * units("m/s")
v_wind = v_point.values * units("m/s")

# 描画
fig = plt.figure(figsize=(10, 7))
skew = SkewT(fig, rotation=45)

# 気温
skew.plot(
    pressure,
    temperature_c,
    color="black",
    linewidth=2,
    label="Temperature"
)

# 露点温度
skew.plot(
    pressure,
    dewpoint,
    color="blue",
    linewidth=2,
    label="Dew Point"
)

# 凡例
skew.ax.legend(
    loc="upper left"
)

# 風矢羽
skew.plot_barbs(
    pressure,
    u_wind,
    v_wind
)

# 補助線
skew.plot_dry_adiabats(
    color="black",
    linestyle="-",
    linewidth=0.8,
    alpha=0.35
)

skew.plot_moist_adiabats(
    color="blue",
    linestyle="--",
    linewidth=1.0,
    alpha=0.55
)

skew.plot_mixing_lines(
    color="orange",
    linestyle=":",
    linewidth=1.0,
    alpha=0.60
)

skew.ax.text(
    0.02,
    0.02,
    "Black solid = Dry Adiabats（乾燥断熱線）\n"
    "Blue dashed = Moist Adiabats（湿潤断熱線）\n"
    "Orange dotted = Mixing Ratio Lines（混合比線）",
    transform=skew.ax.transAxes,
    fontsize=9,
    verticalalignment="bottom"
)

# 軸設定
skew.ax.set_ylim(1000, 100)
skew.ax.set_xlim(-40, 40)
skew.ax.set_ylabel("Pressure [hPa]")

# タイトル
gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    "GFS Skew-T at Tsuchiura\n"
    f"{gfs_time}"
)
plt.savefig(
    "images/skewt_tsuchiura.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()