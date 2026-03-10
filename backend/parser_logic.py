import jsonschema
from jsonschema import validate
from typing import List, Dict, Any


# JSON schema for a single register entry
REGISTER_SCHEMA = {
    "type": "object",
    "properties": {
        "short_name": {"type": "string"},
        "index": {"type": "integer", "minimum": 0},
        "size": {"type": "integer", "minimum": 1},
        "format": {"type": "string", "enum": ["ASCII", "DEC", "HEX", "BIN"]},
        "signed": {"type": "boolean"},
        "scaling": {"type": "number"},
        "offset": {"type": "number"}
    },
    "required": ["short_name", "index", "size", "format", "signed", "scaling", "offset"],
}


def validate_register(reg: Dict[str, Any]):
    """Validate a register dict against the schema."""
    validate(instance=reg, schema=REGISTER_SCHEMA)


def validate_registers(registers: List[Dict[str, Any]]):
    for reg in registers:
        validate_register(reg)


def parse_value(raw_segment: str, fmt: str, signed: bool, scaling: float, offset: float):
    """
    Convert ASCII substring into interpreted value.
    """

    if raw_segment is None or raw_segment == "":
        return None

    raw_segment = raw_segment.strip()

    # ------------------------
    # ASCII (literal text)
    # ------------------------
    if fmt == "ASCII":
        return raw_segment

    # ------------------------
    # Binary
    # ------------------------
    if fmt in ["BIN", "BINARY"]:
        try:
            num = int(raw_segment)
            return bin(num)[2:]
        except:
            return raw_segment

    # ------------------------
    # Decimal ASCII
    # ------------------------
    if fmt == "DEC":
        try:
            numeric_val = float(raw_segment)
            final_val = (numeric_val * scaling) + offset

            if final_val == int(final_val):
                return int(final_val)
            else:
                return round(final_val, 4)

        except ValueError:
            # Try HEX fallback
            try:
                numeric_val = int(raw_segment, 16)
                final_val = (numeric_val * scaling) + offset
                return final_val
            except:
                return raw_segment

    # ------------------------
    # HEX (return uppercase)
    # ------------------------
    if fmt == "HEX":
        return raw_segment.upper()

    return raw_segment


def parse_packet(raw_packet: str, registers: List[Dict[str, Any]]):
    """
    Parse an ASCII packet string using register dictionary.
    """

    rows = []

    if raw_packet is None:
        return rows

    raw_packet = raw_packet.strip()

    for reg in registers:

        start = int(reg["index"])
        size = int(reg["size"])
        end = start + size

        if 0 <= start < len(raw_packet):
            segment = raw_packet[start:end]
        else:
            segment = ""

        fmt = str(reg["format"]).upper()
        signed = bool(reg["signed"])
        scaling = float(reg["scaling"])
        offset = float(reg["offset"])

        converted_value = parse_value(segment, fmt, signed, scaling, offset)

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
