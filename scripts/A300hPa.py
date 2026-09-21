from herbie import HerbieLatest
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

# 最新GFS F00
H = HerbieLatest(
    model="gfs",
    product="pgrb2.0p25",
    fxx=0
)

# 300 hPaデータ取得
height = H.xarray(":HGT:300 mb")
wind_u = H.xarray(":UGRD:300 mb")
wind_v = H.xarray(":VGRD:300 mb")

# 日本周辺を切り出し
height_japan = height["gh"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

u_japan = wind_u["u"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

v_japan = wind_v["v"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

# 風速を計算 [m/s]
wind_speed = np.sqrt(
    u_japan.values ** 2 +
    v_japan.values ** 2
)

# 描画
fig = plt.figure(figsize=(10, 7))

ax = fig.add_subplot(
    1, 1, 1,
    projection=ccrs.PlateCarree()
)

ax.set_extent([100, 160, 15, 60])

# 300 hPa風速
ax.contourf(
    u_japan.longitude.values,
    u_japan.latitude.values,
    wind_speed,
    levels=range(10, 71, 1),
    cmap="viridis",
    extend="max",
    transform=ccrs.PlateCarree()
)

# 300 hPaジオポテンシャル高度
cs = ax.contour(
    height_japan.longitude.values,
    height_japan.latitude.values,
    height_japan.values,
    levels=range(8400, 10201, 60),
    colors="yellow",
    linewidths=1.0,
    transform=ccrs.PlateCarree()
)

# 高度値
ax.clabel(
    cs,
    inline=True,
    fontsize=8,
    fmt="%d",
    colors="yellow"
)

# 風
skip = 12

ax.barbs(
    u_japan.longitude.values[::skip],
    u_japan.latitude.values[::skip],
    u_japan.values[::skip, ::skip],
    v_japan.values[::skip, ::skip],
    length=5,
    color="black",
    transform=ccrs.PlateCarree()
)

# 海岸線・国境
ax.coastlines(
    linewidth=0.8
)

ax.add_feature(
    cfeature.BORDERS,
    linewidth=0.5
)

# GFS時刻
gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    "GFS 300 hPa Geopotential Height + Wind Speed + Wind\n"
    f"{gfs_time}"
)

# 画像保存
plt.savefig(
    "images/300hPa.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()