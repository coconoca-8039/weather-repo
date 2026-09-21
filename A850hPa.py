from herbie import HerbieLatest
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# 最新GFS F00
H = HerbieLatest(
    model="gfs",
    product="pgrb2.0p25",
    fxx=0
)

# 850 hPaデータ取得
height = H.xarray(":HGT:850 mb")
temp = H.xarray(":TMP:850 mb")
wind_u = H.xarray(":UGRD:850 mb")
wind_v = H.xarray(":VGRD:850 mb")

# 日本周辺を切り出し
height_japan = height["gh"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

temp_japan = temp["t"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
) - 273.15  # K → ℃

u_japan = wind_u["u"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

v_japan = wind_v["v"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

# 描画
fig = plt.figure(figsize=(10, 7))

ax = fig.add_subplot(
    1, 1, 1,
    projection=ccrs.PlateCarree()
)

ax.set_extent([100, 160, 15, 60])

# 850 hPa気温
ax.contourf(
    temp_japan.longitude.values,
    temp_japan.latitude.values,
    temp_japan.values,
    levels=range(-30, 37, 3),
    cmap="viridis",
    extend="both",
    transform=ccrs.PlateCarree()
)

# 850 hPaジオポテンシャル高度
cs = ax.contour(
    height_japan.longitude.values,
    height_japan.latitude.values,
    height_japan.values,
    levels=range(900, 1801, 30),
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

# 850 hPa風
# 0.25度格子をそのまま描くと多すぎるので間引く
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

gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    "GFS 850 hPa Temperature + Geopotential Height + Wind\n"
    f"{gfs_time}"
)

plt.savefig(
    "images/850hPa.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()