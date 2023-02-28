# sbm69

This project provides a library and a CLI to export blood pressure measurements
from SilverCrest® SBM69 Bluetooth Blood Pressure Monitor devices.

## Installation

Just clone the repo and then execute:

    $ pip install sbm69

## Usage

    $ sbm69 [-h] [address]

For example:

    $ sbm69 > john-doe-blood-pressure-`date +%F`.csv

## Before first use

The device requires a one-time pairing in order to provide access to its stored
blood pressure measurements. Before the first connection attempt, perform the
following:

### On Linux

1. Start a terminal and run `bluetoothctl`.
2. In a second terminal issue the `sbm69` command without any arguments.
3. Press the `M` button on the SBM69 device.
4. In the second terminal you will see output similar to this:
   ```
   Scanning for an SBM69 Device...
   Device with address B8:B7:7D:XX:XX:XX found.
   ```

5. In the first terminal you will see output similar to this:
   ```
   [CHG] Device B8:B7:7D:XX:XX:XX UUIDs: 00001800-0000-1000-8000-00805f9b34fb
   [CHG] Device B8:B7:7D:XX:XX:XX UUIDs: 00001801-0000-1000-8000-00805f9b34fb
   [CHG] Device B8:B7:7D:XX:XX:XX UUIDs: 0000180a-0000-1000-8000-00805f9b34fb
   [CHG] Device B8:B7:7D:XX:XX:XX UUIDs: 00001810-0000-1000-8000-00805f9b34fb
   [CHG] Device B8:B7:7D:XX:XX:XX ServicesResolved: yes
   [CHG] Device B8:B7:7D:XX:XX:XX Trusted: yes
   Request passkey
   [agent] Enter passkey (number in 0-999999):
   ```

6. Enter the passkey displayed on the SBM69 device's display before it
   disappears.

### On macos

1. Start a terminal that [can request Bluetooth access](https://github.com/hbldh/bleak/issues/761).
   Macos' default terminal should do.
2. Call the `sbm69` command.
3. You will be presented with a 'XXX.app would like to use Bluetooth' message.
   Click OK.
4. Call the `sbm69` command again.
5. Press the `M` button of your SBM69 device.
6. You will be presented with a dialogue window asking you to enter a
   passcode.
7. Enter the passcode displayed on the SBM69 device before it disappears.

## On the protocol

The device uses a protocol based on but not compliant to the Blood Pressure
Profile HDP. It exposes the following BLE services and characteristics:

```
Service: Blood Pressure (00001810-0000-1000-8000-00805f9b34fb)
  Characteristic: Blood Pressure Feature (00002a49-0000-1000-8000-00805f9b34fb), properties: read
    Value:  (0400)
  Characteristic: Intermediate Cuff Pressure (00002a36-0000-1000-8000-00805f9b34fb), properties: notify
    Descriptor: Client Characteristic Configuration (00002902-0000-1000-8000-00805f9b34fb)
  Characteristic: Blood Pressure Measurement (00002a35-0000-1000-8000-00805f9b34fb), properties: indicate
    Descriptor: Client Characteristic Configuration (00002902-0000-1000-8000-00805f9b34fb)
    Value: 1eXXXXXXXXXXXXe70702190d3200XX00000000
    Value: 1eXXXXXXXXXXXXe70702190d3300XX00000000
    Value: 1eXXXXXXXXXXXXe70702190d3500XX00000400
    Value: 1eXXXXXXXXXXXXe7070219170000XX00000000

Service: Device Information (0000180a-0000-1000-8000-00805f9b34fb)
  Characteristic: PnP ID (00002a50-0000-1000-8000-00805f9b34fb), properties: read
    Value:  ()
  Characteristic: Serial Number String (00002a25-0000-1000-8000-00805f9b34fb), properties: read
    Value: XXXXXXXXXXXX (XXXXXXXXXXXXXXXXXXXXXXXX)
  Characteristic: Software Revision String (00002a28-0000-1000-8000-00805f9b34fb), properties: read
    Value: 2.0 (322e30)
  Characteristic: Firmware Revision String (00002a26-0000-1000-8000-00805f9b34fb), properties: read
    Value: 2.0 (322e30)
  Characteristic: Hardware Revision String (00002a27-0000-1000-8000-00805f9b34fb), properties: read
    Value: 7100 (37313030)
  Characteristic: IEEE 11073-20601 Regulatory Cert. Data List (00002a2a-0000-1000-8000-00805f9b34fb), properties: read
    Value:  ()
  Characteristic: Model Number String (00002a24-0000-1000-8000-00805f9b34fb), properties: read
    Value: SBM69 (53424d3639)
  Characteristic: Manufacturer Name String (00002a29-0000-1000-8000-00805f9b34fb), properties: read
    Value: Hans Dinslage GmbH (48616e732044696e736c61676520476d6248)
  Characteristic: System ID (00002a23-0000-1000-8000-00805f9b34fb), properties: read
    Value:  (0000000000000000)

Service: Generic Attribute Profile (00001801-0000-1000-8000-00805f9b34fb)
  Characteristic: Service Changed (00002a05-0000-1000-8000-00805f9b34fb), properties: indicate
    Descriptor: Client Characteristic Configuration (00002902-0000-1000-8000-00805f9b34fb)
```

The `Blood Pressure Feature` characteristic seems to provide incorrect data. It
indicates that the device only supports 'Pulse Rate Range Detection Support',
which is not the case.

The `Intermediate Cuff Pressure` characteristic is not usable because the device
does not activate Bluetooth during a measurement.

The `Blood Pressure Measurement` characteristic is used for transferring the
blood pressure measurements stored in the device. When a user registers for
indications from it, the device immediately starts sending data. After all
records have been sent as indications, the device proceeds to turn off its
Bluetooth functionality, thus disconnecting the user.

The following ImHex pattern can be used to parse the data contained in each of
the characteristic's notifications:

```c++
bitfield Flags {
  blood_pressure_units: 1;
  time_stamp: 1;
  pulse_rate: 1;
  user_id: 1;
  measurement_status: 1;
  vreserved_for_future_use: 3;
};

bitfield MeasurementStatus {
  body_movement_detected: 1;
  cuff_too_loose: 1;
  irregular_pulse: 1;
  pulse_rate_exceeds_lower_limit: 1;
  pulse_rate_exceeds_upper_limit: 1;
  improper_measurement_position: 1;
  reserved_for_future_use: 10;
};

struct BloodPressureMeasurement {
  le Flags flags;

  if (flags.blood_pressure_units) {
    le u16 systolic_kpa;
    le u16 diastolic_kpa;
    le u16 mean_arterial_pressure_kpa;
  } else {
    le u16 systolic_mmhg;
    le u16 diastolic_mmhg;
    le u16 mean_arterial_pressure_mmhg;
  }

  if (flags.time_stamp) {
    le u16 year;
    u8 month;
    u8 day;
    u8 hours;
    u8 minutes;
    u8 seconds;
  }

  if (flags.pulse_rate) {
    le u16 pulse_rate;
  }

  if (flags.user_id) {
    u8 user_id;
  }

  if (flags.measurement_status) {
    le MeasurementStatus measurement_status;
  }
};

BloodPressureMeasurement bpm @ 0x00;
```

Note that the `medfloat16` fields from the HDP profile specification have been
replaced with `uint16` fields.

### Further reading:

* https://www.bluetooth.com/specifications/specs/gatt-specification-supplement/
* https://www.bluetooth.com/specifications/specs/blood-pressure-service-1-1-1/
* https://www.bluetooth.com/specifications/specs/blood-pressure-profile-1-1-1/

## License

Copyright &copy; Petko Bordjukov, 2023

The program is available as open source under the terms of the
[GNU Affero General Public License v3 or later (AGPLv3+)](https://opensource.org/licenses/AGPL-3.0).
