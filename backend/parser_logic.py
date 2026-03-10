import jsonschema
from jsonschema import validate
from typing import List, Dict, Any


REGISTER_SCHEMA = {
    "type": "object",
    "properties": {
        "short_name": {"type": "string"},
        "index": {"type": "integer", "minimum": 0},
        "size": {"type": "integer", "minimum": 1},  # actually END index
        "format": {"type": "string", "enum": ["ASCII", "DEC", "HEX", "BIN"]},
        "signed": {"type": "boolean"},
        "scaling": {"type": "number"},
        "offset": {"type": "number"}
    },
    "required": ["short_name", "index", "size", "format", "signed", "scaling", "offset"],
}


def validate_register(reg: Dict[str, Any]):
    validate(instance=reg, schema=REGISTER_SCHEMA)


def validate_registers(registers: List[Dict[str, Any]]):
    for reg in registers:
        validate_register(reg)


def parse_value(raw_segment: str, fmt: str, scaling: float, offset: float):

    if raw_segment is None or raw_segment == "":
        return None

    raw_segment = raw_segment.strip()

    # ASCII text
    if fmt == "ASCII":
        return raw_segment

    try:
        numeric_val = float(raw_segment)
        final_val = (numeric_val * scaling) + offset

        if final_val == int(final_val):
            return int(final_val)
        else:
            return round(final_val, 4)

    except ValueError:

        # fallback HEX parsing
        try:
            numeric_val = int(raw_segment, 16)
            return (numeric_val * scaling) + offset
        except:
            return raw_segment


def parse_packet(raw_packet: str, registers: List[Dict[str, Any]]):

    rows = []

    if raw_packet is None:
        return rows

    raw_packet = raw_packet.strip()

    for reg in registers:

        start = int(reg["index"])
        end = int(reg["size"])   # IMPORTANT: size = end index

        if 0 <= start < len(raw_packet):
            segment = raw_packet[start:end]
        else:
            segment = ""

        fmt = str(reg["format"]).upper()
        scaling = float(reg["scaling"])
        offset = float(reg["offset"])

        converted_value = parse_value(segment, fmt, scaling, offset)

        rows.append(
            {
                "Short name": reg["short_name"],
                "Raw": segment,
                "format": fmt,
                "scaling": scaling,
                "offset": offset,
                "Value": converted_value,
            }
        )

    return rows
