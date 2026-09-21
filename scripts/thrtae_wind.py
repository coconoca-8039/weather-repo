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

# 軽めの気圧面
levels = "1000|950|900|850|800|750|700|650|600|550|500|450|400"

# データ取得
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

u_section = wind_u["u"].sel(
    longitude=longitude,
    method="nearest"
).sel(
    latitude=slice(50, 20)
)

v_section = wind_v["v"].sel(
    longitude=longitude,
    method="nearest"
).sel(
    latitude=slice(50, 20)
)

# 座標
latitude = temp_section.latitude.values
pressure = temp_section.isobaricInhPa.values

# MetPy用単位
temperature_k = temp_section.values * units.kelvin
relative_humidity = np.clip(
    rh_section.values,
    1,
    100
) / 100.0

pressure_2d = (
    pressure[:, np.newaxis] *
    np.ones((1, len(latitude))) *
    units.hPa
)

# 露点温度
dewpoint = mpcalc.dewpoint_from_relative_humidity(
    temperature_k,
    relative_humidity
)

# 相当温位
theta_e = mpcalc.equivalent_potential_temperature(
    pressure_2d,
    temperature_k,
    dewpoint
).to("kelvin")

# 描画
fig = plt.figure(figsize=(10, 7))

ax = fig.add_subplot(
    1, 1, 1
)

# 相当温位
cf = ax.contourf(
    latitude,
    pressure,
    theta_e.magnitude,
    levels=np.arange(280, 391, 3),
    cmap="viridis",
    extend="both"
)

# 相当温位の等値線
cs = ax.contour(
    latitude,
    pressure,
    theta_e.magnitude,
    levels=np.arange(285, 391, 4),
    colors="black",
    linewidths=0.7
)

ax.clabel(
    cs,
    inline=True,
    fontsize=8,
    fmt="%d"
)

# 風矢羽
skip = 4

ax.barbs(
    latitude[::skip],
    pressure,
    u_section.values[:, ::skip],
    v_section.values[:, ::skip],
    length=5,
    linewidth=0.6
)

# 軸
ax.set_xlim(
    50,
    20
)

ax.set_yscale(
    "log"
)

ax.set_ylim(
    1000,
    400
)

ax.set_yticks(
    [1000, 925, 850, 700, 600, 500, 400]
)

ax.set_yticklabels(
    [1000, 925, 850, 700, 600, 500, 400]
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
    "Equivalent Potential Temperature [K]"
)

# 時刻
gfs_time = H.date.strftime(
    "%Y-%m-%d %H:%M UTC"
)

plt.title(
    "GFS Vertical Cross Section at 140°E\n"
    "Equivalent Potential Temperature + Wind\n"
    f"{gfs_time}"
)

plt.savefig(
    "images/thetae_wind_140E.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()