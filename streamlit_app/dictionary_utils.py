# -*- coding: utf-8 -*-

import pandas as pd
from jsonschema import validate
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# JSON Schema
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


# ---------------------------------------------------------------------------
# Detect header row in Excel
# ---------------------------------------------------------------------------
def normalize_excel_headers(uploaded_file) -> pd.DataFrame:

    df_raw = pd.read_excel(uploaded_file, header=None)

    header_row = None
    for i in range(len(df_raw)):
        if df_raw.iloc[i].count() >= 3:
            header_row = i
            break

    if header_row is None:
        raise ValueError("Could not detect header row in Excel dictionary")

    header = df_raw.iloc[header_row].astype(str).str.strip()
    df = df_raw.iloc[header_row + 1:].copy()

    df.columns = header
    df = df.dropna(how="all")

    # normalize column names
    df.columns = df.columns.str.strip()

    return df


# ---------------------------------------------------------------------------
# Validate register
# ---------------------------------------------------------------------------
def validate_register(reg: Dict[str, Any]):
    validate(instance=reg, schema=REGISTER_SCHEMA)


# ---------------------------------------------------------------------------
# Excel → JSON
# ---------------------------------------------------------------------------
def excel_to_json(uploaded_file) -> List[Dict[str, Any]]:

    df = normalize_excel_headers(uploaded_file)

    required_cols = ["Short name", "Index", "Data format"]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    registers: List[Dict[str, Any]] = []

    format_map = {
        "BINARY": "BIN",
        "BIN": "BIN",
        "HEX": "HEX",
        "DEC": "DEC",
        "DECIMAL": "DEC",
        "ASCII": "ASCII",
    }

    for _, row in df.iterrows():

        if pd.isna(row["Short name"]) or pd.isna(row["Index"]):
            continue

        short_name = str(row["Short name"]).strip().upper()

        fmt_raw = str(row["Data format"]).strip().upper()

        if fmt_raw not in format_map:
            raise ValueError(f"Unsupported data format: {fmt_raw}")

        fmt = format_map[fmt_raw]

        # Excel index is 1-based
        start_excel = int(float(row["Index"]))
        start = start_excel - 1

        # --------------------------------------------------
        # ASCII registers use Index + Total Upto
        # --------------------------------------------------
        if fmt == "ASCII":

            if "Total Upto" not in df.columns or pd.isna(row["Total Upto"]):
                raise ValueError(f"ASCII register missing 'Total Upto': {short_name}")

            end_excel = int(float(row["Total Upto"]))

            size = end_excel - start_excel + 1

        # --------------------------------------------------
        # Binary / Decimal / Hex registers use byte size
        # --------------------------------------------------
        else:

            if "Size [byte]" not in df.columns or pd.isna(row["Size [byte]"]):
                raise ValueError(f"Register missing 'Size [byte]': {short_name}")

            byte_size = int(float(row["Size [byte]"]))

            # each byte = 2 hex characters
            size = byte_size * 2

        # scaling
        scaling = row.get("Scaling factor", 1)
        scaling = 1.0 if pd.isna(scaling) else float(scaling)

        # offset
        offset = row.get("Offset", 0)
        offset = 0.0 if pd.isna(offset) else float(offset)

        # signed
        signed_raw = str(row.get("Signed/Unsigned", "U")).strip().upper()
        signed_flag = signed_raw == "S"

        reg = {
            "short_name": short_name,
            "index": start,
            "size": int(size),
            "format": fmt,
            "signed": signed_flag,
            "scaling": scaling,
            "offset": offset,
        }

        validate_register(reg)

        registers.append(reg)

    return registers


  
