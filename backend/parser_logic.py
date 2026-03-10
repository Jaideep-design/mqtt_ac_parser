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
    Uses the same logic as the working ASCII parser.
    """

    rows = []

    if raw_packet is None:
        return rows

    # Remove whitespace from MQTT payload
    raw_packet = raw_packet.replace(" ", "").strip()

    for reg in registers:

        try:
            short_name = reg["short_name"]

            start = int(reg["index"])
            end = start + int(reg["size"])

            # Extract raw substring
            raw_segment = raw_packet[start:end].strip()

            if not raw_segment:
                rows.append(
                    {
                        "Short name": short_name,
                        "Raw": "",
                        "format": reg["format"],
                        "scaling": reg["scaling"],
                        "offset": reg["offset"],
                        "Value": None,
                    }
                )
                continue

            data_format = str(reg["format"]).upper()
            scaling = float(reg["scaling"])
            offset = float(reg["offset"])

            # ASCII fields
            if data_format == "ASCII":
                final_val = raw_segment

            else:
                # Attempt decimal conversion first
                try:
                    numeric_val = float(raw_segment)
                    final_val = (numeric_val * scaling) + offset

                    if final_val == int(final_val):
                        final_val = int(final_val)
                    else:
                        final_val = round(final_val, 4)

                except ValueError:
                    # Try hex conversion
                    try:
                        numeric_val = int(raw_segment, 16)
                        final_val = (numeric_val * scaling) + offset
                    except:
                        final_val = raw_segment

            rows.append(
                {
                    "Short name": short_name,
                    "Raw": raw_segment,
                    "format": data_format,
                    "scaling": scaling,
                    "offset": offset,
                    "Value": final_val,
                }
            )

        except Exception:
            continue

    return rows
