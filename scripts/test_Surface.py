from herbie import HerbieLatest
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from scipy.ndimage import maximum_filter, minimum_filter

# 最新GFS F00
H = HerbieLatest(
    model="gfs",
    product="pgrb2.0p25",
    fxx=0
)

# 海面更正気圧
surface = H.xarray(":PRMSL:mean sea level")

# 10m風
wind_u = H.xarray(":UGRD:10 m above ground")
wind_v = H.xarray(":VGRD:10 m above ground")

# 日本周辺
mslp = surface["prmsl"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
) / 100

# 高気圧・低気圧の中心を検出
pressure = mslp.values
local_max = pressure == maximum_filter(
    pressure,
    size=50
)
local_min = pressure == minimum_filter(
    pressure,
    size=25
)

# 描画
fig = plt.figure(figsize=(10, 7))

ax = fig.add_subplot(
    1, 1, 1,
    projection=ccrs.PlateCarree()
)

ax.set_extent([100, 160, 15, 60])

# 海面更正気圧
cs = ax.contour(
    mslp.longitude.values,
    mslp.latitude.values,
    mslp.values,
    levels=range(960, 1049, 4),
    colors="red",
    linewidths=1.0,
    transform=ccrs.PlateCarree()
)

u10 = wind_u["u10"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

v10 = wind_v["v10"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

# 気圧値
ax.clabel(
    cs,
    inline=True,
    fontsize=9,
    fmt="%d",
    colors="tomato"
)

# H・Lを表示
lats = mslp.latitude.values
lons = mslp.longitude.values

# 高気圧 H
for y, x in zip(*np.where(local_max)):
    lat = lats[y]
    lon = lons[x]

    # 地図の端で誤検出されたHを除外
    if lon < 108 or lon > 157 or lat < 18 or lat > 57:
        continue

    ax.text(
        lon,
        lat,
        "H",
        fontsize=16,
        fontweight="bold",
        color="darkblue",
        ha="center",
        va="center",
        transform=ccrs.PlateCarree()
    )

# 低気圧 L
for y, x in zip(*np.where(local_min)):
    lat = lats[y]
    lon = lons[x]

    # 地図の端で誤検出されたLを除外
    if lon < 108 or lon > 157 or lat < 18 or lat > 57:
        continue

    ax.text(
        lon,
        lat,
        "L",
        fontsize=16,
        fontweight="bold",
        color="red",
        ha="center",
        va="center",
        transform=ccrs.PlateCarree()
    )

# 海岸線・国境
ax.coastlines(linewidth=0.8)
ax.add_feature(
    cfeature.BORDERS,
    linewidth=0.5
)

# 10m風
skip = 16

ax.barbs(
    u10.longitude.values[::skip],
    u10.latitude.values[::skip],
    u10.values[::skip, ::skip],
    v10.values[::skip, ::skip],
    length=5,
    color="tomato",
    transform=ccrs.PlateCarree()
)

# F00の時刻
valid_time = H.valid_date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    f"GFS Surface Pressure\n"
    f"{valid_time}"
)

plt.savefig(
    "images/surface.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()