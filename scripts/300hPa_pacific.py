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

# 北太平洋周辺を切り出し
height_pacific = height["gh"].sel(
    latitude=slice(80, 25),
    longitude=slice(100, 260)
)

u_pacific = wind_u["u"].sel(
    latitude=slice(80, 25),
    longitude=slice(100, 260)
)

v_pacific = wind_v["v"].sel(
    latitude=slice(80, 25),
    longitude=slice(100, 260)
)

# 描画用に0.5度相当まで間引く
height_pacific = height_pacific.isel(
    latitude=slice(None, None, 2),
    longitude=slice(None, None, 2)
)

u_pacific = u_pacific.isel(
    latitude=slice(None, None, 2),
    longitude=slice(None, None, 2)
)

v_pacific = v_pacific.isel(
    latitude=slice(None, None, 2),
    longitude=slice(None, None, 2)
)

# 風速を計算 [m/s]
wind_speed = np.sqrt(
    u_pacific.values ** 2 +
    v_pacific.values ** 2
)

# 描画
fig = plt.figure(figsize=(10, 7))

ax = fig.add_subplot(
    1, 1, 1,
    projection=ccrs.PlateCarree(
        central_longitude=180
    )
)

# 北太平洋
ax.set_extent(
    [100, 260, 25, 80],
    crs=ccrs.PlateCarree()
)

# 既存図と同じ縦横の地図枠を使う
ax.set_aspect("auto")

# 灰色下地
ax.add_feature(
    cfeature.LAND,
    facecolor="0.70",
    zorder=0
)

ax.add_feature(
    cfeature.OCEAN,
    facecolor="0.78",
    zorder=0
)

# 300 hPa風速
ax.contourf(
    u_pacific.longitude.values,
    u_pacific.latitude.values,
    wind_speed,
    levels=range(0, 81, 2),
    cmap="viridis",
    extend="max",
    alpha=0.68,
    transform=ccrs.PlateCarree(),
    zorder=1
)

# 300 hPaジオポテンシャル高度
cs = ax.contour(
    height_pacific.longitude.values,
    height_pacific.latitude.values,
    height_pacific.values,
    levels=range(8400, 10201, 60),
    colors="yellow",
    linewidths=1.0,
    transform=ccrs.PlateCarree(),
    zorder=3
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
skip = 9

ax.barbs(
    u_pacific.longitude.values[::skip],
    u_pacific.latitude.values[::skip],
    u_pacific.values[::skip, ::skip],
    v_pacific.values[::skip, ::skip],
    length=5,
    color="black",
    transform=ccrs.PlateCarree(),
    zorder=4
)

# 海岸線・国境
ax.coastlines(
    linewidth=0.8,
    zorder=5
)

ax.add_feature(
    cfeature.BORDERS,
    linewidth=0.5,
    zorder=5
)

# GFS時刻
gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    "GFS North Pacific 300 hPa Geopotential Height + Wind Speed + Wind\n"
    f"{gfs_time}"
)

# 画像保存
plt.savefig(
    "images/300hPa_pacific.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()