# -*- coding: utf-8 -*-
"""
Created on Thu Nov 27 15:35:20 2025

@author: Admin
"""

import pandas as pd
import jsonschema
from jsonschema import validate
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# JSON Schema for the full register array
# ---------------------------------------------------------------------------
REGISTER_SCHEMA = {
    "type": "object",
    "properties": {
        "short_name": {"type": "string"},
        "index": {"type": "integer", "minimum": 0},
        "size": {"type": "integer", "minimum": 1},
        "format": {"type": "string", "enum": ["ASCII", "DEC", "HEX", "BIN"]},
        "signed": {"type": "boolean"},
        "scaling": {"type": "number"},
        "offset": {"type": "number"},
    },
    "required": ["short_name", "index", "size", "format", "signed", "scaling", "offset"],
}

LIST_SCHEMA = {
    "type": "array",
    "items": REGISTER_SCHEMA,
}


# ---------------------------------------------------------------------------
# Detect header row in raw Excel files
# ---------------------------------------------------------------------------
def normalize_excel_headers(uploaded_file) -> pd.DataFrame:
    """
    Detect the header row (first row with >=3 non-null cells)
    and return a cleaned DataFrame with those headers applied.
    """

    df_raw = pd.read_excel(uploaded_file, header=None)
    header_row = None

    for i in range(len(df_raw)):
        if df_raw.iloc[i].count() >= 3:  # heuristically detect a header row
            header_row = i
            break

    if header_row is None:
        raise ValueError("Header row not detected — Excel dictionary is malformed.")

    # Extract header and apply
    header = df_raw.iloc[header_row].tolist()
    df = df_raw.iloc[header_row + 1:].copy()
    df.columns = header
    df.dropna(how="all", inplace=True)

    return df


# ---------------------------------------------------------------------------
# Validate a single register entry
# ---------------------------------------------------------------------------
def validate_register(reg: Dict[str, Any]):
    validate(instance=reg, schema=REGISTER_SCHEMA)


# ---------------------------------------------------------------------------
# Validate the entire register list
# ---------------------------------------------------------------------------
def validate_register_list(registers: List[Dict[str, Any]]):
    validate(instance=registers, schema=LIST_SCHEMA)

def validate_registers(registers: List[Dict[str, Any]]):
    """Validate all registers in the dictionary."""
    for reg in registers:
        validate_register(reg)
        
# ---------------------------------------------------------------------------
# Convert Excel dictionary → JSON register list
# ---------------------------------------------------------------------------
def excel_to_json(uploaded_file) -> List[Dict[str, Any]]:

    df = normalize_excel_headers(uploaded_file)

    required_cols = ["Short name", "Index", "Total Upto", "Size [byte]", "Data format"]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in dictionary: {col}")

    registers = []

    for row in df.to_dict("records"):

        if (
            pd.isna(row["Short name"])
            or pd.isna(row["Index"])
        ):
            continue

        short_name = str(row["Short name"]).strip().upper()

        # Convert format
        fmt = str(row["Data format"]).strip().upper()

        format_map = {
            "BINARY": "BIN",
            "BIN": "BIN",
            "HEX": "HEX",
            "DEC": "DEC",
            "DECIMAL": "DEC",
            "ASCII": "ASCII",
        }

        if fmt not in format_map:
            raise ValueError(f"Unsupported data format: {fmt}")

        fmt = format_map[fmt]

        # Convert Index (Excel 1-based → Python 0-based)
        start_excel = int(row["Index"])
        start = start_excel - 1
        
        if fmt == "ASCII":
        
            if pd.isna(row["Total Upto"]):
                raise ValueError(f"Missing 'Total Upto' for ASCII register {short_name}")
        
            end_excel = int(row["Total Upto"])
        
            size = end_excel - start_excel + 1
        
        else:
        
            byte_size = int(row["Size [byte]"])
            size = byte_size * 2

        # Scaling
        scaling = row.get("Scaling factor")
        if pd.isna(scaling):
            scaling = 1.0

        # Offset
        offset = row.get("Offset")
        if pd.isna(offset):
            offset = 0.0

        # Signed flag
        signed_raw = str(row.get("Signed/Unsigned", "U")).strip().upper()
        signed_flag = signed_raw == "S"

        reg = {
            "short_name": short_name,
            "index": start,
            "size": int(size),
            "format": fmt,
            "signed": signed_flag,
            "scaling": float(scaling),
            "offset": float(offset),
        }

        validate_register(reg)

        registers.append(reg)

    validate_registers(registers)

    return registers
