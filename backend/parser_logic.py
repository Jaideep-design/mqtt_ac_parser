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

def parse_packet(raw_packet: str, registers: List[Dict[str, Any]]):
    """
    Parse a raw packet string using a list of register dicts.
    For now we implement a simple extraction:
      - Take substring raw_packet[index:index+size]
      - Apply trivial 'value = raw' (placeholder for more complex conversion).
    Returns: list of row dicts that can be turned into a DataFrame on the frontend.
    """
    rows = []
    if raw_packet is None:
        return rows

    for reg in registers:
        idx = int(reg["index"])
        size = int(reg["size"])
        segment = raw_packet[idx : idx + size] if 0 <= idx < len(raw_packet) else ""

        # Placeholder conversion; you can expand with actual DEC/HEX/BIN/ASCII logic
        value = segment

        rows.append(
            {
                "Short name": reg["short_name"],
                "Raw": segment,
                "format": reg["format"],
                "scaling": reg["scaling"],
                "offset": reg["offset"],
                "Value": value,
            }
        )
    return rows
