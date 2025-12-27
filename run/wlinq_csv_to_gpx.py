from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys
import tempfile
import re
import pandas as pd

from dateutil import tz  # comes with pandas (python-dateutil)
from gpx_converter import Converter


# Column mapping for WunderLINQ TripLog exports (CSV header -> internal field).
WLINQ_COLS = {
    "lat": "Latitude",
    "lon": "Longitude",
    "time": "Time (yyyyMMdd-HH:mm:ss.SSS)",
    "ele": "Elevation (m)",

    "speed": "Speed (kmh)",
    "gps_speed": "GPS Speed (kmh)",
    "rear_wheel_speed": "Rear Wheel Speed (kmh)",
    "rpm": "RPM",
    "gear": "Gear",
    "throttle": "Throttle Position (%)",

    "engine_temp": "Engine Temperature (C)",
    "ambient_temp": "Ambient Temperature (C)",
    "front_tire_pr": "Front Tire Pressure (bar)",
    "rear_tire_pr": "Rear Tire Pressure (bar)",

    "odo": "Odometer (km)",
    "bt_volt": "Voltage (V)",
    "device_batt": "Device Battery (%)",

    "front_brakes": "Front Brakes",
    "rear_brakes": "Rear Brakes",
    "shifts": "Shifts",

    "vin": "VIN",
    "ambient_light": "Ambient Light",

    "trip1": "Trip 1 (km)",
    "trip2": "Trip 2 (km)",
    "trip_auto": "Trip Auto (km)",
    "avg_speed": "Average Speed (kmh)",

    "current_consumption": "Current Consumption (L/100)",
    "fuel1_economy": "Fuel Economy 1 (L/100)",
    "fuel2_economy": "Fuel Economy 2 (L/100)",
    "fuel_range": "Fuel Range (km)",

    "lean_angle_mobile": "Lean Angle Mobile",
    "lean_angle": "Lean Angle",
    "g_force": "g-force",
    "bearing": "Bearing",
    "barometer_kpa": "Barometer (kPa)",
}


@dataclass(frozen=True)
class WunderlinqToGpxConfig:
    csv_path: Path
    output_gpx_path: Path

    # Input format from WunderLINQ CSV, e.g. 20250615-18:24:20.306
    time_format: str = "%Y%m%d-%H:%M:%S.%f"

    # Convert CSV local timestamps -> UTC and emit UTC times in GPX (with Z)
    time_utc: bool = False

    # Local timezone to interpret CSV times
    local_tz: str = "Asia/Nicosia"


def validate_columns(csv_path: Path, mapping: dict[str, str]) -> None:
    df_head = pd.read_csv(csv_path, nrows=1)
    headers = set(df_head.columns)

    required_headers = set(mapping.values())
    missing = sorted(h for h in required_headers if h and h not in headers)

    if missing:
        raise ValueError(
            "CSV is missing required columns:\n- "
            + "\n- ".join(missing)
            + "\n\nAvailable columns:\n- "
            + "\n- ".join(sorted(headers))
        )


def _rewrite_csv_time_to_utc_temp_csv(
    src_csv: Path,
    time_col: str,
    in_time_format: str,
    local_tz_name: str,
) -> Path:
    """
    Reads CSV, parses time_col according to in_time_format as *local time* in local_tz_name,
    converts each row to UTC, and writes a temp CSV where the time column is replaced with UTC
    timestamps in the same numeric format (YYYYmmdd-HH:MM:SS.fff).
    """
    df = pd.read_csv(src_csv)

    if time_col not in df.columns:
        raise ValueError(f"Time column not found in CSV: {time_col!r}")

    tz_local = tz.gettz(local_tz_name)
    if tz_local is None:
        raise ValueError(
            f"Unknown timezone {local_tz_name!r}. "
            f"Tip: use IANA names like 'Asia/Nicosia', 'Europe/Athens', etc."
        )
    tz_utc = tz.UTC

    # Parse as naive datetimes using the given format (errors raise so you catch bad formats immediately)
    parsed = pd.to_datetime(df[time_col], format=in_time_format, errors="raise")

    # Convert row-by-row to avoid pandas tz_localize edge-case issues on older stacks
    utc_strings = []
    for ts in parsed:
        if pd.isna(ts):
            utc_strings.append("")
            continue

        dt_naive = ts.to_pydatetime()
        # Attach local tz (dateutil tz handles DST correctly using system tzdata)
        dt_local = dt_naive.replace(tzinfo=tz_local)
        dt_utc = dt_local.astimezone(tz_utc)

        # Keep milliseconds precision (WunderLINQ style .SSS)
        utc_strings.append(dt_utc.strftime("%Y%m%d-%H:%M:%S.%f")[:-3])

    df[time_col] = utc_strings

    tmp = tempfile.NamedTemporaryFile(prefix="wlinq_utc_", suffix=".csv", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    df.to_csv(tmp_path, index=False)
    return tmp_path


def _force_gpx_times_to_have_z(gpx_path: Path) -> None:
    """
    gpx_converter often writes naive ISO timestamps like:
      2025-12-25T10:16:08.412000
    When we're doing --time-utc we want explicit UTC:
      2025-12-25T10:16:08.412000Z
    """
    p = gpx_path.expanduser().resolve()
    txt = p.read_text(encoding="utf-8")

    def repl(m: re.Match) -> str:
        t = m.group(1).strip()
        # If already has Z or offset, keep
        if t.endswith("Z") or re.search(r"[+-]\d\d:\d\d$", t):
            return m.group(0)
        return f"<time>{t}Z</time>"

    txt2 = re.sub(r"<time>([^<]+)</time>", repl, txt)
    p.write_text(txt2, encoding="utf-8")


def convert_wunderlinq_csv_to_gpx(cfg: WunderlinqToGpxConfig) -> None:
    csv_path = cfg.csv_path.expanduser().resolve()
    out_path = cfg.output_gpx_path.expanduser().resolve()

    validate_columns(csv_path, WLINQ_COLS)

    input_csv_for_converter = csv_path
    converter_time_format = cfg.time_format
    converter_time_utc = False  # we will set True only if we rewrote times to UTC

    temp_csv = None
    try:
        if cfg.time_utc:
            temp_csv = _rewrite_csv_time_to_utc_temp_csv(
                src_csv=csv_path,
                time_col=WLINQ_COLS["time"],
                in_time_format=cfg.time_format,
                local_tz_name=cfg.local_tz,
            )
            input_csv_for_converter = temp_csv
            converter_time_format = "%Y%m%d-%H:%M:%S.%f"
            converter_time_utc = True

        Converter(input_file=str(input_csv_for_converter)).csv_to_gpx(
            lats_colname=WLINQ_COLS["lat"],
            longs_colname=WLINQ_COLS["lon"],
            times_colname=WLINQ_COLS["time"],
            alts_colname=WLINQ_COLS["ele"],

            speed_colname=WLINQ_COLS.get("speed"),
            gps_speed_colname=WLINQ_COLS.get("gps_speed"),
            rear_wheel_speed_colname=WLINQ_COLS.get("rear_wheel_speed"),

            rpm_colname=WLINQ_COLS.get("rpm"),
            gear_colname=WLINQ_COLS.get("gear"),
            throttle_colname=WLINQ_COLS.get("throttle"),

            engine_temp_colname=WLINQ_COLS.get("engine_temp"),
            ambient_temp_colname=WLINQ_COLS.get("ambient_temp"),
            front_tire_pr_colname=WLINQ_COLS.get("front_tire_pr"),
            rear_tire_pr_colname=WLINQ_COLS.get("rear_tire_pr"),

            odo_colname=WLINQ_COLS.get("odo"),
            bt_volt_colname=WLINQ_COLS.get("bt_volt"),
            device_batt_colname=WLINQ_COLS.get("device_batt"),

            front_brakes_colname=WLINQ_COLS.get("front_brakes"),
            rear_brakes_colname=WLINQ_COLS.get("rear_brakes"),
            shifts_colname=WLINQ_COLS.get("shifts"),

            vin_colname=WLINQ_COLS.get("vin"),
            ambient_light_colname=WLINQ_COLS.get("ambient_light"),

            trip1_colname=WLINQ_COLS.get("trip1"),
            trip2_colname=WLINQ_COLS.get("trip2"),
            trip_auto_colname=WLINQ_COLS.get("trip_auto"),
            avg_speed_colname=WLINQ_COLS.get("avg_speed"),

            crnt_consumption_colname=WLINQ_COLS.get("current_consumption"),
            fuel1_economy_colname=WLINQ_COLS.get("fuel1_economy"),
            fuel2_economy_colname=WLINQ_COLS.get("fuel2_economy"),
            fuel_range_colname=WLINQ_COLS.get("fuel_range"),

            lean_angle_mobile_colname=WLINQ_COLS.get("lean_angle_mobile"),
            lean_angle_colname=WLINQ_COLS.get("lean_angle"),
            g_force_colname=WLINQ_COLS.get("g_force"),
            bearing_colname=WLINQ_COLS.get("bearing"),
            barometer_kpa_colname=WLINQ_COLS.get("barometer_kpa"),

            time_format=converter_time_format,
            time_utc=converter_time_utc,
            output_file=str(out_path),
        )

        # Ensure GPX times are explicitly UTC (Z) so gopro-dashboard won't compare aware vs naive
        if cfg.time_utc:
            _force_gpx_times_to_have_z(out_path)

    finally:
        # Best-effort cleanup of temp CSV
        if temp_csv is not None:
            try:
                temp_csv.unlink()
            except Exception:
                pass


def default_output_path_for(csv_path: Path) -> Path:
    return csv_path.with_name(f"{csv_path.stem}-converted.gpx")


def parse_args(argv: list[str]) -> WunderlinqToGpxConfig:
    p = argparse.ArgumentParser(
        description="Convert WunderLINQ TripLog CSV to GPX (with extensions)."
    )

    p.add_argument(
        "csv_path",
        type=Path,
        help="Path to WunderLINQ TripLog CSV file",
    )

    p.add_argument(
        "--output-gpx-path",
        type=Path,
        default=None,
        help="Output GPX path. Default: <input>-converted.gpx in same folder.",
    )

    p.add_argument(
        "--time-format",
        default="%Y%m%d-%H:%M:%S.%f",
        help='Input timestamp format (default: "%Y%m%d-%H:%M:%S.%f")',
    )

    p.add_argument(
        "--time-utc",
        action="store_true",
        help="Interpret CSV timestamps as local time and convert to UTC (recommended for merging with GoPro GPS).",
    )

    p.add_argument(
        "--local-tz",
        default="Asia/Nicosia",
        help='IANA timezone name for CSV timestamps (default: "Asia/Nicosia").',
    )

    args = p.parse_args(argv)

    csv_path = args.csv_path.expanduser().resolve()
    out_path = (
        args.output_gpx_path.expanduser().resolve()
        if args.output_gpx_path is not None
        else default_output_path_for(csv_path)
    )

    return WunderlinqToGpxConfig(
        csv_path=csv_path,
        output_gpx_path=out_path,
        time_format=args.time_format,
        time_utc=args.time_utc,
        local_tz=args.local_tz,
    )


if __name__ == "__main__":
    cfg = parse_args(sys.argv[1:])
    convert_wunderlinq_csv_to_gpx(cfg)
    print(f"GPX written to: {cfg.output_gpx_path}")
