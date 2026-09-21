from herbie import HerbieLatest
import matplotlib.pyplot as plt
import numpy as np
import os

# 保存先フォルダ
os.makedirs("images", exist_ok=True)

# 最新GFS F00
H = HerbieLatest(
    model="gfs",
    product="pgrb2.0p25",
    fxx=0
)

# 気圧面
levels = "1000|925|850|700|500|300|250|200|100"

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

# 描画する経度
longitudes = range(125, 160, 5)

# 時刻
gfs_time = H.date.strftime("%Y-%m-%d %H:%M UTC")

for lon in longitudes:
    # 東経lon度の鉛直断面
    temp_section = temperature["t"].sel(
        longitude=lon,
        method="nearest"
    ).sel(
        latitude=slice(90, 0)
    )

    rh_section = humidity["r"].sel(
        longitude=lon,
        method="nearest"
    ).sel(
        latitude=slice(90, 0)
    )

    u_section = wind_u["u"].sel(
        longitude=lon,
        method="nearest"
    ).sel(
        latitude=slice(90, 0)
    )

    # 気温を℃へ変換
    temp_c = temp_section - 273.15

    latitude = temp_section.latitude.values
    pressure = temp_section.isobaricInhPa.values

    # 描画
    fig = plt.figure(figsize=(10, 7))

    ax = fig.add_subplot(
        1, 1, 1
    )

    # 気温
    cf = ax.contourf(
        latitude,
        pressure,
        temp_c.values,
        levels=np.arange(-80, 41, 5),
        cmap="coolwarm",
        extend="both"
    )

    # 相対湿度
    cs_rh = ax.contour(
        latitude,
        pressure,
        rh_section.values,
        levels=[40, 60, 80, 90],
        colors="black",
        linewidths=0.8
    )

    ax.clabel(
        cs_rh,
        inline=True,
        fontsize=8,
        fmt="%d%%"
    )

    # 東西風
    cs_u = ax.contour(
        latitude,
        pressure,
        u_section.values,
        levels=[-40, -20, 0, 20, 40, 60],
        colors="white",
        linewidths=0.9
    )

    ax.clabel(
        cs_u,
        inline=True,
        fontsize=8,
        fmt="%d"
    )

    # 左が北極、右が赤道
    ax.set_xlim(
        90,
        0
    )

    # 上ほど低圧
    ax.set_yscale("log")

    ax.set_ylim(
        1000,
        100
    )

    ax.set_yticks(
        [1000, 925, 850, 700, 500, 300, 250, 200, 100]
    )

    ax.set_yticklabels(
        [1000, 925, 850, 700, 500, 300, 250, 200, 100]
    )

    ax.set_xticks(
        range(90, -1, -10)
    )

    ax.set_xticklabels(
        [f"{lat}°N" for lat in range(90, -1, -10)]
    )

    ax.set_xlabel("Latitude")
    ax.set_ylabel("Pressure [hPa]")

    ax.grid(
        linewidth=0.4,
        alpha=0.5
    )

    # カラーバー
    cbar = plt.colorbar(
        cf,
        ax=ax,
        pad=0.02
    )

    cbar.set_label("Temperature [°C]")

    plt.title(
        f"GFS Vertical Cross Section at {lon}°E\n"
        f"Temperature + Relative Humidity + Zonal Wind\n"
        f"{gfs_time}"
    )

    # 保存
    save_path = f"images/vertical_{lon}E_temp_rh_u.png"

    plt.savefig(
        save_path,
        dpi=150,
        bbox_inches="tight"
    )

    print(f"saved: {save_path}")

    plt.close()