from herbie import Herbie, HerbieLatest
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import time

from PIL import Image
from pathlib import Path
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed


HISTORY_HOURS = 168
INTERVAL_HOURS = 3
INTERPOLATION_MINUTES = 60
IMAGE_DPI = 100

FRAME_DIR = Path("frames/surface")
GIF_PATH = Path("images/surface_7days_smooth.gif")

GIF_DURATION_MS = 100
MAX_WORKERS = 5

MAP_LON_MIN = 115
MAP_LON_MAX = 155
MAP_LAT_MIN = 20
MAP_LAT_MAX = 50

DATA_LON_MIN = 100
DATA_LON_MAX = 160
DATA_LAT_MIN = 15
DATA_LAT_MAX = 60


def get_latest_run():
    H = HerbieLatest(
        model="gfs",
        product="pgrb2.0p25",
        fxx=0
    )

    return H.date


def get_run_and_fxx(valid_time):
    if valid_time.hour in (0, 6, 12, 18):
        return valid_time, 0

    return valid_time - timedelta(hours=3), 3


def get_gfs(valid_time):
    run_time, fxx = get_run_and_fxx(valid_time)

    H = Herbie(
        run_time,
        model="gfs",
        product="pgrb2.0p25",
        fxx=fxx
    )

    return H, run_time, fxx


def get_3h_precip(valid_time):
    run_time, fxx = get_run_and_fxx(valid_time)

    if fxx == 3:
        H = Herbie(
            run_time,
            model="gfs",
            product="pgrb2.0p25",
            fxx=3
        )

        ds = H.xarray(
            ":APCP:surface:0-3 hour acc fcst"
        )

        var_name = list(ds.data_vars)[0]

        return ds[var_name]

    previous_run = valid_time - timedelta(hours=6)

    H6 = Herbie(
        previous_run,
        model="gfs",
        product="pgrb2.0p25",
        fxx=6
    )

    H3 = Herbie(
        previous_run,
        model="gfs",
        product="pgrb2.0p25",
        fxx=3
    )

    ds6 = H6.xarray(
        ":APCP:surface:0-6 hour acc fcst"
    )

    ds3 = H3.xarray(
        ":APCP:surface:0-3 hour acc fcst"
    )

    var6 = list(ds6.data_vars)[0]
    var3 = list(ds3.data_vars)[0]

    rain = ds6[var6] - ds3[var3]

    return rain.clip(min=0)


def load_surface_data(valid_time):
    start = time.perf_counter()

    H, run_time, fxx = get_gfs(valid_time)

    print(
        f"[LOAD] "
        f"Valid={valid_time:%Y-%m-%d %H:%M UTC} "
        f"Run={run_time:%Y-%m-%d %H:%M UTC} "
        f"F{fxx:03d}"
    )

    mslp = H.xarray(
        ":PRMSL:mean sea level"
    )

    wind_u = H.xarray(
        ":UGRD:10 m above ground"
    )

    wind_v = H.xarray(
        ":VGRD:10 m above ground"
    )

    rain = None

    try:
        rain = get_3h_precip(valid_time)

    except Exception as e:
        print(
            f"[PRECIP ERROR] "
            f"{valid_time:%Y-%m-%d %H:%M}: "
            f"{e}"
        )

    pressure = mslp["prmsl"].sel(
        latitude=slice(DATA_LAT_MAX, DATA_LAT_MIN),
        longitude=slice(DATA_LON_MIN, DATA_LON_MAX)
    )

    u = wind_u["u10"].sel(
        latitude=slice(DATA_LAT_MAX, DATA_LAT_MIN),
        longitude=slice(DATA_LON_MIN, DATA_LON_MAX)
    )

    v = wind_v["v10"].sel(
        latitude=slice(DATA_LAT_MAX, DATA_LAT_MIN),
        longitude=slice(DATA_LON_MIN, DATA_LON_MAX)
    )

    if rain is not None:
        rain = rain.sel(
            latitude=slice(DATA_LAT_MAX, DATA_LAT_MIN),
            longitude=slice(DATA_LON_MIN, DATA_LON_MAX)
        )

        rain_values = np.asarray(
            rain.values,
            dtype=np.float32
        )

    else:
        rain_values = np.zeros_like(
            pressure.values,
            dtype=np.float32
        )

    result = {
        "valid_time": valid_time,
        "longitude": np.asarray(
            pressure.longitude.values,
            dtype=np.float32
        ),
        "latitude": np.asarray(
            pressure.latitude.values,
            dtype=np.float32
        ),
        "pressure": np.asarray(
            pressure.values / 100.0,
            dtype=np.float32
        ),
        "u": np.asarray(
            u.values,
            dtype=np.float32
        ),
        "v": np.asarray(
            v.values,
            dtype=np.float32
        ),
        "rain": rain_values
    }

    elapsed = time.perf_counter() - start

    print(
        f"[LOAD DONE] "
        f"{valid_time:%Y-%m-%d %H:%M} "
        f"{elapsed:.2f}s"
    )

    return result


def interpolate_array(a, b, weight):
    return (
        a * (1.0 - weight)
        + b * weight
    )


def interpolate_surface_data(
    data_a,
    data_b,
    weight,
    valid_time
):
    return {
        "valid_time": valid_time,
        "longitude": data_a["longitude"],
        "latitude": data_a["latitude"],
        "pressure": interpolate_array(
            data_a["pressure"],
            data_b["pressure"],
            weight
        ),
        "u": interpolate_array(
            data_a["u"],
            data_b["u"],
            weight
        ),
        "v": interpolate_array(
            data_a["v"],
            data_b["v"],
            weight
        ),
        "rain": interpolate_array(
            data_a["rain"],
            data_b["rain"],
            weight
        )
    }


def find_pressure_centers(
    pressure,
    lon,
    lat
):
    lon_mask = (
        (lon >= MAP_LON_MIN)
        & (lon <= MAP_LON_MAX)
    )

    lat_mask = (
        (lat >= MAP_LAT_MIN)
        & (lat <= MAP_LAT_MAX)
    )

    lon_indices = np.where(lon_mask)[0]
    lat_indices = np.where(lat_mask)[0]

    if len(lon_indices) == 0 or len(lat_indices) == 0:
        return []

    i_start = lat_indices[0]
    i_end = lat_indices[-1]

    j_start = lon_indices[0]
    j_end = lon_indices[-1]

    radius = 12

    candidates = []

    for i in range(
        i_start + radius,
        i_end - radius + 1
    ):
        for j in range(
            j_start + radius,
            j_end - radius + 1
        ):
            value = pressure[i, j]

            area = pressure[
                i - radius:i + radius + 1,
                j - radius:j + radius + 1
            ]

            local_min = np.min(area)
            local_max = np.max(area)

            if value == local_min:
                candidates.append(
                    {
                        "type": "L",
                        "pressure": float(value),
                        "lon": float(lon[j]),
                        "lat": float(lat[i])
                    }
                )

            elif value == local_max:
                candidates.append(
                    {
                        "type": "H",
                        "pressure": float(value),
                        "lon": float(lon[j]),
                        "lat": float(lat[i])
                    }
                )

    lows = sorted(
        [
            x
            for x in candidates
            if x["type"] == "L"
        ],
        key=lambda x: x["pressure"]
    )

    highs = sorted(
        [
            x
            for x in candidates
            if x["type"] == "H"
        ],
        key=lambda x: x["pressure"],
        reverse=True
    )

    selected = []

    def far_enough(candidate):
        for existing in selected:
            dx = (
                candidate["lon"]
                - existing["lon"]
            )

            dy = (
                candidate["lat"]
                - existing["lat"]
            )

            distance = np.sqrt(
                dx * dx + dy * dy
            )

            if distance < 8.0:
                return False

        return True

    for candidate in lows:
        if far_enough(candidate):
            selected.append(candidate)

        if len(
            [
                x
                for x in selected
                if x["type"] == "L"
            ]
        ) >= 4:
            break

    for candidate in highs:
        if far_enough(candidate):
            selected.append(candidate)

        if len(
            [
                x
                for x in selected
                if x["type"] == "H"
            ]
        ) >= 4:
            break

    return selected


def draw_pressure_centers(
    ax,
    centers
):
    for center in centers:
        lon = center["lon"]
        lat = center["lat"]
        pressure = center["pressure"]
        center_type = center["type"]

        if center_type == "L":
            color = "red"
        else:
            color = "blue"

        ax.text(
            lon,
            lat,
            center_type,
            color=color,
            fontsize=18,
            fontweight="bold",
            ha="center",
            va="center",
            transform=ccrs.PlateCarree(),
            zorder=10
        )

        ax.text(
            lon,
            lat - 1.2,
            f"{pressure:.0f}",
            color=color,
            fontsize=8,
            fontweight="bold",
            ha="center",
            va="top",
            transform=ccrs.PlateCarree(),
            zorder=10
        )


def render_interpolated_frame(
    data,
    frame_number,
    total_frames
):
    frame_start = time.perf_counter()

    valid_time = data["valid_time"]

    filename = (
        f"{valid_time:%Y%m%d_%H%M}.png"
    )

    output_path = FRAME_DIR / filename

    if output_path.exists():
        print(
            f"[CACHE] "
            f"{frame_number:03d}/{total_frames:03d} "
            f"{valid_time:%Y-%m-%d %H:%M UTC}"
        )

        return output_path, None

    pressure_hpa = data["pressure"]
    u = data["u"]
    v = data["v"]
    rain = data["rain"]

    lon = data["longitude"]
    lat = data["latitude"]

    centers = find_pressure_centers(
        pressure_hpa,
        lon,
        lat
    )

    draw_start = time.perf_counter()

    fig = plt.figure(
        figsize=(10, 7),
        dpi=IMAGE_DPI
    )

    ax = fig.add_axes(
        [0.05, 0.08, 0.80, 0.78],
        projection=ccrs.PlateCarree()
    )

    cax = fig.add_axes(
        [0.88, 0.16, 0.025, 0.62]
    )

    ax.set_extent(
        [
            MAP_LON_MIN,
            MAP_LON_MAX,
            MAP_LAT_MIN,
            MAP_LAT_MAX
        ],
        crs=ccrs.PlateCarree()
    )

    rain_levels = [
        0.1,
        1,
        3,
        5,
        10,
        20,
        30,
        50,
        80
    ]

    cmap = plt.get_cmap(
        "Blues"
    )

    norm = colors.BoundaryNorm(
        rain_levels,
        cmap.N,
        extend="max"
    )

    ax.contourf(
        lon,
        lat,
        rain,
        levels=rain_levels,
        cmap=cmap,
        norm=norm,
        alpha=1.0,
        extend="max",
        transform=ccrs.PlateCarree()
    )

    sm = plt.cm.ScalarMappable(
        norm=norm,
        cmap=cmap
    )

    sm.set_array([])

    cbar = fig.colorbar(
        sm,
        cax=cax,
        orientation="vertical",
        boundaries=rain_levels,
        ticks=rain_levels,
        extend="max"
    )

    cbar.set_label(
        "3-hour precipitation (mm)"
    )

    cs = ax.contour(
        lon,
        lat,
        pressure_hpa,
        levels=np.arange(
            940,
            1062,
            2
        ),
        colors="black",
        linewidths=0.8,
        transform=ccrs.PlateCarree()
    )

    ax.clabel(
        cs,
        inline=True,
        fontsize=7,
        fmt="%d"
    )

    skip = 12

    ax.barbs(
        lon[::skip],
        lat[::skip],
        u[::skip, ::skip],
        v[::skip, ::skip],
        length=4.5,
        linewidth=0.5,
        transform=ccrs.PlateCarree()
    )

    ax.coastlines(
        linewidth=0.8
    )

    ax.add_feature(
        cfeature.BORDERS,
        linewidth=0.5
    )

    draw_pressure_centers(
        ax,
        centers
    )

    valid_jst = (
        valid_time
        + timedelta(hours=9)
    )

    ax.set_title(
        "GFS Surface Pressure + 10m Wind "
        "+ 3h Precipitation\n"
        f"Valid: "
        f"{valid_jst:%Y-%m-%d %H:%M JST} "
        f"    "
        f"{frame_number:03d}/{total_frames:03d}",
        fontsize=11
    )

    draw_time = (
        time.perf_counter()
        - draw_start
    )

    save_start = time.perf_counter()

    fig.savefig(
        output_path,
        dpi=IMAGE_DPI
    )

    plt.close(fig)

    save_time = (
        time.perf_counter()
        - save_start
    )

    frame_time = (
        time.perf_counter()
        - frame_start
    )

    timing = {
        "draw": draw_time,
        "save": save_time,
        "total": frame_time
    }

    #print(
        #f"[FRAME] "
        #f"{frame_number:03d}/{total_frames:03d} "
        #f"{valid_time:%Y-%m-%d %H:%M} "
        #f"{frame_time:.2f}s"
    #)

    return output_path, timing


def build_interpolated_frames(
    source_times,
    source_data
):
    frames = []

    steps = int(
        INTERVAL_HOURS * 60
        / INTERPOLATION_MINUTES
    )

    for i in range(
        len(source_times) - 1
    ):
        time_a = source_times[i]
        time_b = source_times[i + 1]

        data_a = source_data[time_a]
        data_b = source_data[time_b]

        for step in range(steps):
            weight = step / steps

            valid_time = (
                time_a
                + timedelta(
                    minutes=(
                        step
                        * INTERPOLATION_MINUTES
                    )
                )
            )

            data = interpolate_surface_data(
                data_a,
                data_b,
                weight,
                valid_time
            )

            frames.append(data)

    final_time = source_times[-1]

    final_data = {
        "valid_time": final_time,
        "longitude": source_data[
            final_time
        ]["longitude"],
        "latitude": source_data[
            final_time
        ]["latitude"],
        "pressure": source_data[
            final_time
        ]["pressure"],
        "u": source_data[
            final_time
        ]["u"],
        "v": source_data[
            final_time
        ]["v"],
        "rain": source_data[
            final_time
        ]["rain"]
    }

    frames.append(final_data)

    return frames


def make_gif(frame_paths):
    print(
        "[GIF] Creating GIF..."
    )

    frames = []

    for path in frame_paths:
        with Image.open(path) as img:
            frames.append(
                img.convert("RGB").copy()
            )

    frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=GIF_DURATION_MS,
        loop=0,
        optimize=True
    )

    print(
        f"[GIF] Saved: {GIF_PATH}"
    )


def cleanup_cache(current_frames):
    keep = {
        path.resolve()
        for path in current_frames
    }

    for path in FRAME_DIR.glob(
        "*.png"
    ):
        if path.resolve() not in keep:
            print(
                f"[DELETE] {path}"
            )

            path.unlink()


def main():
    FRAME_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    GIF_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    total_start = time.perf_counter()

    latest_run = get_latest_run()

    start_time = (
        latest_run
        - timedelta(
            hours=HISTORY_HOURS
        )
    )

    source_times = []

    current_time = start_time

    while current_time <= latest_run:
        source_times.append(
            current_time
        )

        current_time += timedelta(
            hours=INTERVAL_HOURS
        )

    print(
        f"Start         : "
        f"{start_time:%Y-%m-%d %H:%M UTC}"
    )

    print(
        f"End           : "
        f"{latest_run:%Y-%m-%d %H:%M UTC}"
    )

    print(
        f"GFS times     : "
        f"{len(source_times)}"
    )

    print(
        f"GFS interval  : "
        f"{INTERVAL_HOURS} hours"
    )

    print(
        f"Video interval: "
        f"{INTERPOLATION_MINUTES} minutes"
    )

    print(
        f"Workers       : "
        f"{MAX_WORKERS}"
    )

    load_start = time.perf_counter()

    source_data = {}

    with ProcessPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                load_surface_data,
                valid_time
            ): valid_time
            for valid_time in source_times
        }

        for future in as_completed(
            futures
        ):
            valid_time = futures[future]

            source_data[
                valid_time
            ] = future.result()

    load_time = (
        time.perf_counter()
        - load_start
    )

    interpolation_start = (
        time.perf_counter()
    )

    interpolated_frames = (
        build_interpolated_frames(
            source_times,
            source_data
        )
    )

    interpolation_time = (
        time.perf_counter()
        - interpolation_start
    )

    total_frames = len(
        interpolated_frames
    )

    print(
        f"Output frames : "
        f"{total_frames}"
    )

    render_start = time.perf_counter()

    frame_paths = []
    timings = []

    for frame_number, data in enumerate(
        interpolated_frames,
        start=1
    ):
        path, timing = (
            render_interpolated_frame(
                data,
                frame_number,
                total_frames
            )
        )

        frame_paths.append(path)

        if timing is not None:
            timings.append(timing)

    render_time = (
        time.perf_counter()
        - render_start
    )

    gif_start = time.perf_counter()

    make_gif(
        frame_paths
    )

    gif_time = (
        time.perf_counter()
        - gif_start
    )

    cleanup_cache(
        frame_paths
    )

    total_time = (
        time.perf_counter()
        - total_start
    )

    print()
    print(
        "========== Timing =========="
    )

    print(
        f"GFS data loading   : "
        f"{load_time:.2f} sec"
    )

    print(
        f"Interpolation      : "
        f"{interpolation_time:.2f} sec"
    )

    if timings:
        count = len(timings)

        print(
            f"Average drawing    : "
            f"{sum(x['draw'] for x in timings) / count:.3f} sec"
        )

        print(
            f"Average PNG save   : "
            f"{sum(x['save'] for x in timings) / count:.3f} sec"
        )

        print(
            f"Average frame      : "
            f"{sum(x['total'] for x in timings) / count:.3f} sec"
        )

    print(
        f"Frame generation   : "
        f"{render_time:.2f} sec"
    )

    print(
        f"GIF generation     : "
        f"{gif_time:.2f} sec"
    )

    print(
        f"Total              : "
        f"{total_time:.2f} sec"
    )

    print(
        "============================"
    )

    print(
        "Complete."
    )


if __name__ == "__main__":
    main()