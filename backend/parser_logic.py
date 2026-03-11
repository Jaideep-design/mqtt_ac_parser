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

def parse_value(raw_hex: str, fmt: str, signed: bool, scaling: float, offset: float):
    """
    Convert raw hex substring into final interpreted value.
    raw_hex: string of hex chars (e.g. '0A1B')
    fmt: ASCII / DEC / HEX / BIN
    """

    if raw_hex is None or raw_hex == "":
        return None

    hex_clean = raw_hex.replace(" ", "")

    # ------------------------
    # ASCII
    # ------------------------
    if fmt == "ASCII":
        try:
            # convert hex → bytes → ASCII
            b = bytes.fromhex(hex_clean)
            return b.decode("ascii", errors="ignore").strip()
        except:
            return raw_hex

    # ------------------------
    # BIN (convert hex to 8-bit binary string)
    # ------------------------
    if fmt in ["BIN", "BINARY"]:
        try:
            b = bytes.fromhex(hex_clean)
            return ''.join(f"{x:08b}" for x in b)
        except:
            return raw_hex

    # ------------------------
    # DEC (hex → decimal, scaled)
    # ------------------------
    if fmt == "DEC":
        try:
            b = bytes.fromhex(hex_clean)
            num = int.from_bytes(b, byteorder="big", signed=signed)
            return num * scaling + offset
        except:
            return raw_hex

    # ------------------------
    # HEX (return cleaned hex)
    # ------------------------
    if fmt == "HEX":
        return hex_clean.upper()

    # DEFAULT fallback
    return raw_hex

def parse_packet(raw_packet: str, registers: List[Dict[str, Any]]):
    """
    Parse a raw packet string using the register dictionary.
    Each register extracts a substring (index:size) and converts it.
    """
    rows = []
    if raw_packet is None:
        return rows

    for reg in registers:
        idx = int(reg["index"])
        size = int(reg["size"])

        # Extract raw hex segment
        segment = raw_packet[idx : idx + size] if 0 <= idx < len(raw_packet) else ""

        fmt = str(reg["format"]).upper()
        signed = bool(reg["signed"])
        scaling = float(reg["scaling"])
        offset = float(reg["offset"])

        # Convert the value properly
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
