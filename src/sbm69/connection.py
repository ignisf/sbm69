from __future__ import annotations

import asyncio

import construct
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from ._structures import _BloodPressureMeasurementStruct

MANUFACTURER_NAME_CHAR_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_CHAR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_CHAR_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
HARDWARE_REVISION_CHAR_UUID = "00002a27-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_CHAR_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
SOFTWARE_REVISION_CHAR_UUID = "00002a28-0000-1000-8000-00805f9b34fb"
BLOOD_PRESSURE_MEASUREMENT_CHAR_UUID = "00002a35-0000-1000-8000-00805f9b34fb"


class SBM69Connection:
    def __init__(self, ble_device: BLEDevice, name="SBM69"):
        self._ble_device = ble_device
        self._name = name
        self._disconnected_event = asyncio.Event()
        self._connection_lock = asyncio.Lock()

    async def fetch_data(self) -> dict[str, str | construct.Container]:
        result = {}

        async with self._connection_lock:
            self._disconnected_event.clear()

            connection = await establish_connection(
                client_class=BleakClient,
                device=self._ble_device,
                name=self._name,
                disconnected_callback=lambda client: self._disconnected_event.set(),
                max_attempts=2,
                use_services_cache=True,
            )
            await connection.pair()

            result["manufacturer_name"] = self._bytearray_as_string(
                await connection.read_gatt_char(MANUFACTURER_NAME_CHAR_UUID)
            )
            result["model_number"] = self._bytearray_as_string(await connection.read_gatt_char(MODEL_NUMBER_CHAR_UUID))
            result["serial_number"] = self._bytearray_as_string(
                await connection.read_gatt_char(SERIAL_NUMBER_CHAR_UUID)
            )
            result["hardware_revision"] = self._bytearray_as_string(
                await connection.read_gatt_char(HARDWARE_REVISION_CHAR_UUID)
            )
            result["firmware_revision"] = self._bytearray_as_string(
                await connection.read_gatt_char(FIRMWARE_REVISION_CHAR_UUID)
            )
            result["software_revision"] = self._bytearray_as_string(
                await connection.read_gatt_char(SOFTWARE_REVISION_CHAR_UUID)
            )

            result["blood_pressure_measurements"] = []
            await connection.start_notify(
                BLOOD_PRESSURE_MEASUREMENT_CHAR_UUID,
                lambda handle, data: result["blood_pressure_measurements"].append(
                    _BloodPressureMeasurementStruct.parse(data)
                ),
            )

            await asyncio.wait_for(self._disconnected_event.wait(), timeout=120)
        return result

    def _bytearray_as_string(self, value: bytearray) -> str:
        return "".join(map(chr, value))
