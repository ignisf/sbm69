"""SMB69 Blood Pressure Monitor CLI."""
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime
import io
import sys

import construct
import inflection
from bleak import BleakScanner

from .connection import SBM69Connection

CSV_FIELD_NAMES = [
    "Time Stamp",
    "Systolic Pressure",
    "Diastolic Pressure",
    "Mean Arterial Pressure",
    "Pulse Rate",
    "User ID",
    "Body Movement",
    "Cuff Too Loose",
    "Irregular Pulse",
    "Pulse Rate Range",
    "Improper Measurement Position",
]


def __blood_pressure_measurements_as_csv(measurements: construct.Container) -> str:
    result = io.StringIO()

    writer = csv.writer(result)
    writer.writerow(CSV_FIELD_NAMES)

    for measurement in measurements:
        writer.writerow(
            [
                datetime.datetime(
                    measurement.time_stamp.year,
                    measurement.time_stamp.month,
                    measurement.time_stamp.day,
                    measurement.time_stamp.hours,
                    measurement.time_stamp.minutes,
                    measurement.time_stamp.seconds,
                ),
                measurement.systolic,
                measurement.diastolic,
                measurement.mean_arterial_pressure,
                measurement.pulse_rate,
                measurement.user_id,
                measurement.measurement_status.body_movement_detected,
                measurement.measurement_status.cuff_too_loose,
                measurement.measurement_status.irregular_pulse,
                measurement.measurement_status.pulse_rate_range,
                measurement.measurement_status.improper_measurement_position,
            ]
        )

    return result.getvalue()


async def __async_main(args: argparse.Namespace) -> None:
    try:
        if args.address is not None:
            print(f"Scanning for an SBM69 Device with address {args.address}...", file=sys.stderr)
            device = await BleakScanner.find_device_by_address(args.address)
        else:
            print("Scanning for an SBM69 Device...", file=sys.stderr)
            device = await BleakScanner.find_device_by_filter(
                lambda device, advertisement_data: advertisement_data.local_name == "SBM69"
            )
    except Exception as exception:
        sys.exit(f"Scan failed: {exception}")

    if device:
        print(f"Device with address {device.address} found.", file=sys.stderr)
    else:
        sys.exit("Device not found.")

    print("Connecting...", file=sys.stderr)

    try:
        connection = SBM69Connection(device)
        data = await connection.fetch_data()

        for item, value in {k: v for k, v in data.items() if k != "blood_pressure_measurements"}.items():
            print(f"{inflection.humanize(item)} : {value}", file=sys.stderr)

        print(__blood_pressure_measurements_as_csv(data["blood_pressure_measurements"]))
    except Exception as exception:
        sys.exit(f"Connection failed: {exception}.")


def main() -> None:
    """SMB69 Blood Pressure Monitor CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="sbm69", description="This command downloads data from an SBM69 device and prints it as CSV."
    )
    parser.add_argument("address", help="Optionally the Bluetooth address of a specific SBM69 device", nargs="?")
    args = parser.parse_args()

    asyncio.run(__async_main(args))
