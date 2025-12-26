from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import argparse
import sys

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

    # WunderLINQ timestamps are typically like: 20250615-18:24:20.123
    # Default format matches: %Y%m%d-%H:%M:%S.%f
    time_format: str | None = "%Y%m%d-%H:%M:%S.%f"
    time_utc: bool = False


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


def convert_wunderlinq_csv_to_gpx(cfg: WunderlinqToGpxConfig) -> None:
    csv_path = cfg.csv_path.expanduser().resolve()
    out_path = cfg.output_gpx_path.expanduser().resolve()

    validate_columns(csv_path, WLINQ_COLS)

    Converter(input_file=str(csv_path)).csv_to_gpx(
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

        time_format=cfg.time_format,
        time_utc=cfg.time_utc,

        output_file=str(out_path),
    )

def default_output_path_for(csv_path: Path) -> Path:
    # Default output: <input-stem>-converted.gpx next to the CSV.
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
        help='Timestamp format (default: "%Y%m%d-%H:%M:%S.%f")',
    )

    p.add_argument(
        "--time-utc",
        action="store_true",
        help="Treat parsed timestamps as UTC (default: false).",
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
    )

if __name__ == "__main__":
    # Example:
    #   python csv_to_gpx.py trip.csv --output-gpx-path trip.gpx
    cfg = parse_args(sys.argv[1:])
    convert_wunderlinq_csv_to_gpx(cfg)
    print(f"GPX written to: {cfg.output_gpx_path}")
