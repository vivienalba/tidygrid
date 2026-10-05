"""The original CSV / TSV cleaning rules."""

import csv
import io
import re
from pathlib import Path
import pandas as pd

SAMPLE_CSV = "Customer Name,Email Address,Mobile Number,Booking Status,Service Requested\n  Maria Santos  ,MARIA.SANTOS@EMAIL.COM ,0917-123-4567,Confirmed,Dental Cleaning\nJuan Dela Cruz, juan@email.com,0918 222 3333,Pending,Consultation\n  Maria Santos  ,MARIA.SANTOS@EMAIL.COM ,0917-123-4567,Confirmed,Dental Cleaning\nAna Reyes,,0919-555-0101,Pending,Teeth Whitening\nCarlo Lim ,CARLO@EXAMPLE.COM,,Cancelled,Consultation\n Bianca Cruz,bianca@email.com ,+63 920 111 2222,Confirmed,\n"

RULES = [
    (
        "headers",
        "Standardize Column Names",
        "Use lowercase names with underscores. Duplicate names get a unique suffix.",
    ),
    (
        "whitespace",
        "Trim Extra Spaces",
        "Remove spaces at the beginning and end of text values.",
    ),
    (
        "emails",
        "Lowercase Email Addresses",
        "Apply to columns whose names contain email or e-mail. This does not validate addresses.",
    ),
    (
        "phones",
        "Format Philippine Mobiles",
        "Convert recognized 09, 9, or 639 mobile formats to +639. Other numbers are kept as entered.",
    ),
    (
        "duplicates",
        "Remove Duplicate Rows",
        "Keep the first of any rows that match after the selected cleaning rules.",
    ),
]


def clean_column_name(name):
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def unique_column_names(columns):
    """Do not let punctuation-only or colliding headers break a DataFrame."""
    used, names = set(), []
    for index, column in enumerate(columns, start=1):
        base = clean_column_name(column) or f"column_{index}"
        candidate, suffix = base, 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        names.append(candidate)
    return names


def clean_phone(value):
    if pd.isna(value):
        return value
    text = str(value)
    # Only normalize recognizable mobile numbers; retain extensions/other formats.
    if not re.fullmatch(r"[+\d\s().-]+", text):
        return text
    digits = re.sub(r"\D", "", text)
    if re.fullmatch(r"09\d{9}", digits):
        return "+63" + digits[1:]
    if re.fullmatch(r"639\d{9}", digits):
        return "+" + digits
    if re.fullmatch(r"9\d{9}", digits):
        return "+63" + digits
    return text


def count_changes(before, after):
    return int((before.fillna("") != after.fillna("")).sum().sum())


def clean_dataframe(original, options=None):
    options = options or {key: True for key, _, _ in RULES}
    data = original.astype("string").copy()
    old_columns = list(data.columns)
    log = []
    blank_mask = data.apply(lambda column: column.str.fullmatch(r"\s*", na=False))
    data = data.mask(blank_mask, pd.NA)
    baseline = data.copy()

    def record(rule, count, unit, key):
        log.append(
            {
                "Cleaning rule": rule,
                "Status": "Applied" if options[key] else "Off",
                "Affected": f"{count:,} {unit}" if options[key] else "—",
            }
        )

    renamed = unique_column_names(old_columns) if options["headers"] else old_columns
    rename_count = sum(str(old) != str(new) for old, new in zip(old_columns, renamed))
    record("Column names", rename_count, "columns", "headers")

    before = data.copy()
    if options["whitespace"]:
        data = data.apply(lambda column: column.str.strip())
    record("Extra spaces", count_changes(before, data), "cells", "whitespace")

    before = data.copy()
    if options["emails"]:
        for column in old_columns:
            if "email" in clean_column_name(column).replace("_", ""):
                data[column] = data[column].str.lower().str.strip()
    record("Email casing", count_changes(before, data), "cells", "emails")

    before = data.copy()
    if options["phones"]:
        for column in old_columns:
            field = clean_column_name(column)
            if any(token in field for token in ("phone", "mobile", "contact_number")):
                data[column] = data[column].apply(clean_phone).astype("string")
    record("Philippine mobile format", count_changes(before, data), "cells", "phones")

    # Count individual cells only once, even if several rules changed them.
    edited_cells = count_changes(baseline, data)
    candidates = int(data.duplicated().sum())
    removed = candidates if options["duplicates"] else 0
    if options["duplicates"]:
        data = data.drop_duplicates()
    record("Duplicate rows", removed, "rows", "duplicates")
    data.columns = renamed
    # Preserve source row indexes for comparing original and cleaned previews.
    missing = data.isna().sum()
    missing = missing[missing > 0]
    missing_table = pd.DataFrame(
        {"Column": missing.index, "Missing cells": missing.values}
    )
    missing_table["Share of rows"] = (
        missing.values / len(data) * 100 if len(data) else 0
    )
    report = {
        "original_rows": len(original),
        "cleaned_rows": len(data),
        "duplicates_removed": removed,
        "duplicates_remaining": candidates if not options["duplicates"] else 0,
        "edited_cells": edited_cells,
        "columns_standardized": rename_count,
        "missing_cells": int(missing.sum()),
        "missing_rows": int(data.isna().any(axis=1).sum()),
        "missing_table": missing_table,
        "log": pd.DataFrame(log),
        "column_map": pd.DataFrame(
            {"Original name": old_columns, "Current name": renamed}
        ),
    }
    return data, report


def read_csv(raw, encoding="utf-8-sig", separator="Auto-detect", filename="data.csv"):
    extension = Path(filename).suffix.lower()
    if extension == ".xlsx":
        return pd.read_excel(
            io.BytesIO(raw),
            sheet_name=0,
            dtype="string",
            keep_default_na=False,
            engine="openpyxl",
        )
    text = raw.decode(encoding)
    separators = {"Comma": ",", "Semicolon": ";", "Tab": "\t", "Pipe": "|"}
    if separator == "Auto-detect":
        if extension == ".tsv":
            delimiter = "\t"
        else:
            try:
                delimiter = (
                    csv.Sniffer().sniff(text[:65536], delimiters=",;\t|").delimiter
                )
            except csv.Error:
                delimiter = ","
    else:
        delimiter = separators[separator]
    return pd.read_csv(
        io.StringIO(text), sep=delimiter, dtype="string", keep_default_na=False
    )
