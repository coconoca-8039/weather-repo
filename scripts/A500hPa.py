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

# 500 hPa高度・絶対渦度
height = H.xarray(":HGT:500 mb")
vort = H.xarray(":ABSV:500 mb")

# 日本周辺
height_japan = height["gh"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

vort_japan = vort["absv"].sel(
    latitude=slice(60, 15),
    longitude=slice(100, 160)
)

# 描画
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

ax.set_extent([100, 160, 15, 60])

# 絶対渦度
cf = ax.contourf(
    vort_japan.longitude.values,
    vort_japan.latitude.values,
    (vort_japan.values * 1e5),
    levels=range(0, 41, 2),
    cmap="viridis",
    transform=ccrs.PlateCarree()
)

# 500 hPa高度
cs = ax.contour(
    height_japan.longitude.values,
    height_japan.latitude.values,
    height_japan.values,
    levels=range(4800, 6001, 60),
    colors="yellow",
    transform=ccrs.PlateCarree()
)

ax.clabel(cs, inline=True, fontsize=8, fmt="%d")

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linewidth=0.5)

gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    "GFS 500 hPa Geopotential Height + Absolute Vorticity\n"
    f"{gfs_time}"
)

plt.savefig(
    "images/500hPa.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()