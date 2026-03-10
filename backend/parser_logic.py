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


def parse_value(raw_segment: str, fmt: str, signed: bool, scaling: float, offset: float):

    if raw_segment is None or raw_segment.strip() == "":
        return None

    raw_segment = raw_segment.strip()

    # ASCII
    if fmt == "ASCII":
        return raw_segment

    # HEX (return raw)
    if fmt == "HEX":
        return raw_segment.upper()

    # BIN
    if fmt == "BIN":
        try:
            num = int(raw_segment, 16)
            return bin(num)[2:]
        except:
            return raw_segment

    # DEC (HEX → integer → scaling)
    if fmt == "DEC":
        try:
            num = int(raw_segment, 16)

            if signed:
                bits = len(raw_segment) * 4
                if num >= 2**(bits-1):
                    num -= 2**bits

            value = (num * scaling) + offset

            if value == int(value):
                return int(value)

            return round(value, 4)

        except:
            return raw_segment

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
