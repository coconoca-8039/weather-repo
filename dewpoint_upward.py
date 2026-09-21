from herbie import HerbieLatest
import matplotlib.pyplot as plt
import numpy as np

import metpy.calc as mpcalc
from metpy.units import units

# 最新GFS F00
H = HerbieLatest(
    model="gfs",
    product="pgrb2.0p25",
    fxx=0
)

# 東経140度
longitude = 140

# 気圧面
levels = "1000|950|900|850|800|750|700|650|600|550|500|450|400"

# データ取得
temperature = H.xarray(
    f":TMP:({levels}) mb"
)

humidity = H.xarray(
    f":RH:({levels}) mb"
)

vertical_velocity = H.xarray(
    f":VVEL:({levels}) mb"
)

# 東経140度・北緯50～20度
temp_section = temperature["t"].sel(
    longitude=longitude,
    method="nearest"
).sel(
    latitude=slice(50, 20)
)

rh_section = humidity["r"].sel(
    longitude=longitude,
    method="nearest"
).sel(
    latitude=slice(50, 20)
)

omega_section = vertical_velocity["w"].sel(
    longitude=longitude,
    method="nearest"
).sel(
    latitude=slice(50, 20)
)

# 座標
latitude = temp_section.latitude.values
pressure = temp_section.isobaricInhPa.values

# 気温
temperature_k = temp_section.values * units.kelvin
temperature_c = temperature_k.to("degC")

# 相対湿度
relative_humidity = np.clip(
    rh_section.values,
    1,
    100
) / 100.0

# 露点温度
dewpoint = mpcalc.dewpoint_from_relative_humidity(
    temperature_k,
    relative_humidity
).to("degC")

# 湿数
dewpoint_depression = (
    temperature_c - dewpoint
).magnitude

# 鉛直p速度
omega = omega_section.values

# 上昇流だけ残す
# ω < 0 が上昇流
upward_motion = np.where(
    omega < 0,
    -omega,
    np.nan
)

# 描画
fig = plt.figure(
    figsize=(10, 7)
)

ax = fig.add_subplot(
    1, 1, 1
)

# 上昇流を背景色にする
cf = ax.contourf(
    latitude,
    pressure,
    upward_motion,
    levels=[0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2],
    cmap="Blues",
    extend="max"
)

# 湿数
cs_td = ax.contour(
    latitude,
    pressure,
    dewpoint_depression,
    levels=[3, 6, 9, 12, 15],
    colors="black",
    linewidths=0.9
)

ax.clabel(
    cs_td,
    inline=True,
    fontsize=8,
    fmt="%d°C"
)

# 左が北、右が南
ax.set_xlim(
    50,
    20
)

# 上ほど低圧
ax.set_yscale(
    "log"
)

ax.set_ylim(
    1000,
    400
)

ax.set_yticks(
    [1000, 900, 800, 700, 600, 500, 400]
)

ax.set_yticklabels(
    [1000, 900, 800, 700, 600, 500, 400]
)

ax.set_xticks(
    [50, 45, 40, 35, 30, 25, 20]
)

ax.set_xticklabels(
    [
        "50°N",
        "45°N",
        "40°N",
        "35°N",
        "30°N",
        "25°N",
        "20°N"
    ]
)

ax.set_xlabel(
    "Latitude"
)

ax.set_ylabel(
    "Pressure [hPa]"
)

ax.grid(
    linewidth=0.4,
    alpha=0.4
)

# カラーバー
cbar = plt.colorbar(
    cf,
    ax=ax,
    pad=0.02
)

cbar.set_label(
    "Upward Motion [-ω, Pa/s]"
)

# 時刻
gfs_time = H.date.strftime(
    "%Y-%m-%d %H:%M UTC"
)

plt.title(
    "GFS Vertical Cross Section at 140°E\n"
    "Dew Point Depression + Upward Motion\n"
    f"{gfs_time}"
)

plt.savefig(
    "images/dewpoint_depression_upward_motion_140E.png",
    dpi=150,
    bbox_inches="tight"
)

plt.close()