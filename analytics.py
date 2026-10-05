"""Small, explicit calculations for dashboards and local dataset questions."""

import re
import pandas as pd
from reporting import parse_dates

COLORS = ["#72559f", "#f6d46b", "#205182", "#d4c2ef", "#98b4cf", "#cdcdcd"]


def parse_amounts(series):
    text = series.astype("string").fillna("").str.strip()
    text = text.str.replace(
        r"^(?:PHP|USD|EUR|GBP|₱|\$|€|£)\s*", "", regex=True, case=False
    )
    valid = text.str.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?", na=False)
    return pd.to_numeric(
        text.where(valid).str.replace(",", "", regex=False), errors="coerce"
    )


def numeric_columns(data):
    result = []
    for name in data.columns:
        field = re.sub(r"[^a-z0-9]+", " ", str(name).lower())
        if any(
            word in field.split()
            for word in ("id", "phone", "mobile", "postal", "zip", "number")
        ):
            continue
        populated = data[name].astype("string").fillna("").str.strip().ne("")
        if (
            populated.any()
            and parse_amounts(data[name])[populated].notna().mean() >= 0.8
        ):
            result.append(name)
    return result


def grouped_data(data, group, measure=None, aggregation="Count"):
    categories = (
        data[group].astype("string").fillna("").str.strip().replace("", "(Missing)")
    )
    if aggregation == "Count":
        values = (
            categories.value_counts().rename_axis("Group").reset_index(name="Value")
        )
        return values, 0
    numbers = parse_amounts(data[measure])
    valid = pd.DataFrame({"Group": categories, "Value": numbers}).dropna(
        subset=["Value"]
    )
    values = (
        valid.groupby("Group")["Value"]
        .agg("sum" if aggregation == "Sum" else "mean")
        .reset_index()
    )
    return values.sort_values("Value", ascending=False), int(numbers.isna().sum())


def expense_data(data, mapping, date_format="YYYY-MM-DD"):
    result = pd.DataFrame(index=data.index)

    def text(field, default=""):
        column = mapping.get(field)
        return (
            data[column].astype("string").fillna("").str.strip()
            if column
            else pd.Series(default, index=data.index, dtype="string")
        )

    result["Description"] = text("Description", "Record")
    result["Amount"] = parse_amounts(data[mapping["Amount"]])
    result["Category"] = text("Category", "Uncategorized").replace("", "Uncategorized")
    result["Card"] = text("Card", "Not recorded").replace("", "Not recorded")
    raw = text("Payment Status").str.casefold()
    result["Payment Status"] = raw.map(
        {
            "yes": "Paid",
            "paid": "Paid",
            "true": "Paid",
            "1": "Paid",
            "no": "Unpaid",
            "unpaid": "Unpaid",
            "false": "Unpaid",
            "0": "Unpaid",
        }
    ).fillna("Unknown")
    result["Date"] = (
        parse_dates(data[mapping["Date"]], date_format)
        if mapping.get("Date")
        else pd.NaT
    )
    return result


def dataset_answer(question, data, report, workbook=False):
    q = question.casefold()
    if any(word in q for word in ("missing", "blank", "gap")):
        missing = data.replace(r"^\s*$", pd.NA, regex=True).isna().sum()
        fields = ", ".join(
            f"{name}: {count:,}" for name, count in missing.items() if count
        )
        return f"{int(missing.sum()):,} blank cells in the current dataset." + (
            " By column: " + fields + "." if fields else " No blank cells were found."
        )
    if "duplicate" in q:
        return (
            f"{int(data.duplicated().sum()):,} duplicate rows remain in this view. "
            + (
                "Excel rows stay in place to preserve the workbook layout."
                if workbook
                else "The CSV duplicate rule keeps the first matching row when enabled."
            )
        )
    if any(word in q for word in ("changed", "changes", "updated")):
        count = report.get("changed", report.get("edited_cells", 0))
        return f"{count:,} cells changed under the selected cleaning rules. Open the Change Log to review the details."
    if any(word in q for word in ("numeric", "number", "sum", "total")):
        fields = numeric_columns(data)
        if not fields:
            return "No likely numeric measures were found. Map an amount column in the dashboard to calculate totals explicitly."
        return (
            "Recorded totals: "
            + "; ".join(
                f"{name}: {parse_amounts(data[name]).sum(min_count=1):,.2f}"
                for name in fields
            )
            + ". Invalid amounts are excluded; identifiers and phone numbers are not treated as measures."
        )
    if any(word in q for word in ("summary", "summarize", "overview", "rows")):
        return f"This view contains {len(data):,} rows and {len(data.columns):,} columns. Use the Data view for gaps and changes, Dashboard for grouped totals, and Reports for calendar-period activity summaries."
    return "This version supports local dataset commands: summary, missing values, duplicates, changes, and numeric totals. Open-ended AI chat is not connected."
