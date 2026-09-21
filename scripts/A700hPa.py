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

# 700 hPaの各データを取得
height = H.xarray(":HGT:700 mb")
rh = H.xarray(":RH:700 mb")
omega = H.xarray(":VVEL:700 mb")

# 日本周辺を切り出し
height_japan = height["gh"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

rh_japan = rh["r"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

omega_japan = omega["w"].sel(
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

# 相対湿度
ax.contourf(
    rh_japan.longitude.values,
    rh_japan.latitude.values,
    rh_japan.values,
    levels=[40, 50, 60, 70, 80, 90, 100],
    transform=ccrs.PlateCarree()
)

# 700 hPa高度
cs_height = ax.contour(
    height_japan.longitude.values,
    height_japan.latitude.values,
    height_japan.values,
    levels=range(2400, 3301, 30),
    colors="cyan",
    linewidths=1.0,
    transform=ccrs.PlateCarree()
)

ax.clabel(
    cs_height,
    inline=True,
    fontsize=8,
    fmt="%d",
    colors="cyan"
)

# 鉛直流
cs_omega = ax.contour(
    omega_japan.longitude.values,
    omega_japan.latitude.values,
    omega_japan.values,
    levels=[-2.0, -1.5, -1.0, -0.5, -0.2],
    colors="black",
    linewidths=0.8,
    transform=ccrs.PlateCarree()
)

ax.clabel(
    cs_omega,
    inline=True,
    fontsize=7,
    fmt="%.1f",
    colors="black"
)

# 海岸線・国境
ax.coastlines(linewidth=0.8)
ax.add_feature(cfeature.BORDERS, linewidth=0.5)

gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    "GFS 700 hPa Height + Relative Humidity + Vertical Velocity\n"
    f"{gfs_time}"
)

plt.savefig(
    "images/700hPa.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()