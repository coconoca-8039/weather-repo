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

# 全雲量を取得
cloud = H.xarray(":TCDC:entire atmosphere")

# 日本周辺を切り出し
cloud_japan = cloud["tcc"].sel(
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

# 全雲量
# 0% = 黒、100% = 白
cf = ax.contourf(
    cloud_japan.longitude.values,
    cloud_japan.latitude.values,
    cloud_japan.values,
    levels=range(0, 101, 10),
    cmap="Greys_r",
    extend="neither",
    transform=ccrs.PlateCarree()
)

# 海岸線・国境
ax.coastlines(
    linewidth=0.8,
    color="orange"
)

ax.add_feature(
    cfeature.BORDERS,
    linewidth=0.5,
    edgecolor="orange"
)

# カラーバー
cbar = fig.colorbar(
    cf,
    ax=ax,
    pad=0.03,
    shrink=0.85
)

cbar.set_label(
    "Total Cloud Cover [%]"
)

gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

plt.title(
    "GFS Total Cloud Cover\n"
    f"{gfs_time}"
)

plt.savefig(
    "images/cloud_cover.png",
    dpi=150,
    bbox_inches="tight"
)

#plt.show()
plt.close()