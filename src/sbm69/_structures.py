from __future__ import annotations

from construct import (
    BitsInteger,
    BitsSwapped,
    BitStruct,
    Enum,
    Flag,
    If,
    Int8ul,
    Int16ul,
    Padding,
    Struct,
    this,
)

_FlagsStruct = BitStruct(
    "blood_pressure_units" / Flag,
    "time_stamp" / Flag,
    "pulse_rate" / Flag,
    "user_id" / Flag,
    "measurement_status" / Flag,
    "reserved" / Padding(3),
)


_TimeStampStruct = Struct(
    "year" / Int16ul, "month" / Int8ul, "day" / Int8ul, "hours" / Int8ul, "minutes" / Int8ul, "seconds" / Int8ul
)


_PulseRateRangeEnum = Enum(BitsInteger(2), not_exceeded=0, upper_limit_exceeded=1, lower_limit_exceeded=2)


_MeasurementStatusStruct = BitStruct(
    "body_movement_detected" / Flag,
    "cuff_too_loose" / Flag,
    "irregular_pulse" / Flag,
    "pulse_rate_range" / _PulseRateRangeEnum,
    "improper_measurement_position" / Flag,
    "reserved" / Padding(10),
)


_BloodPressureMeasurementStruct = Struct(
    "flags" / BitsSwapped(_FlagsStruct),
    "systolic" / Int16ul,  # This diverges from the HDP specification
    "diastolic" / Int16ul,  # This diverges from the HDP specification
    "mean_arterial_pressure" / Int16ul,  # This diverges from the HDP specification
    "time_stamp" / If(this.flags.time_stamp, _TimeStampStruct),
    "pulse_rate" / If(this.flags.pulse_rate, Int16ul),  # This diverges from the HDP specification
    "user_id" / If(this.flags.user_id, Int8ul),
    "measurement_status"
    / If(
        this.flags.measurement_status,
        BitsSwapped(_MeasurementStatusStruct),
    ),
)
