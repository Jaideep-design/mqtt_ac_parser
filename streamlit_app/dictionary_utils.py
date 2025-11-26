import pandas as pd
import jsonschema
from jsonschema import validate

SCHEMA = {
    "type": "array",
    "items": {
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
        "required": ["short_name", "index", "size", "format", "signed", "scaling", "offset"]
    }
}

def normalize_excel_headers(uploaded_file):
    """Detect header row (first with >=3 non-null cells) and return a cleaned DataFrame."""
    df_raw = pd.read_excel(uploaded_file, header=None)
    header_row = None

    for i in range(len(df_raw)):
        if df_raw.iloc[i].count() >= 3:
            header_row = i
            break

    if header_row is None:
        raise ValueError("Header row not detected")

    header = df_raw.iloc[header_row].tolist()
    df = df_raw.iloc[header_row + 1 :].copy()
    df.columns = header
    df.dropna(how="all", inplace=True)

    return df

def validate_register(reg):
    try:
        validate(instance=reg, schema=SCHEMA["items"])
        return True, None
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message

def excel_to_json(uploaded_file):
    """Convert the uploaded Excel dictionary into a list of JSON-register dicts."""
    df = normalize_excel_headers(uploaded_file)

    required = ["Short name", "Index", "Size [byte]", "Data format"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    registers = []

    for _, row in df.iterrows():
        if pd.isna(row["Short name"]) or pd.isna(row["Index"]):
            continue
    
        fmt = str(row["Data format"]).strip().upper()
        if fmt == "BINARY":
            fmt = "BIN"
    
        # FIX: Handle NaN scaling and offset
        sc = row.get("Scaling factor")
        if pd.isna(sc):
            sc = 1.0
    
        off = row.get("Offset")
        if pd.isna(off):
            off = 0.0
    
        reg = {
            "short_name": str(row["Short name"]).strip().upper(),
            "index": int(row["Index"]),
            "size": int(row["Size [byte]"]),
            "format": fmt,
            "signed": str(row.get("Signed/Unsigned", "U")).strip().upper() == "S",
            "scaling": float(sc),
            "offset": float(off),
        }

        ok, err = validate_register(reg)
        if not ok:
            raise ValueError(f"Validation Failed: {err}")

        registers.append(reg)

    return registers
