"""Monthly expense/bill ledger. Unknown amounts and missing coverage stay unknown."""

import csv
import io
import json
import math
import re
from pathlib import Path
import pandas as pd
from analytics import expense_data, parse_amounts
from typography import font_css

LEDGER_COLUMNS = [
    "Month",
    "Date",
    "Description",
    "Amount",
    "Category",
    "Card",
    "Payment Status",
    "Type",
    "Source",
]
CURRENCIES = ["PHP", "USD", "EUR", "GBP", "Other"]


def read_month_csv(raw):
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    if not lines:
        raise ValueError("The file is empty.")
    try:
        sep = (
            csv.Sniffer()
            .sniff(
                "\n".join(lines[1:20] if len(lines) > 1 else lines), delimiters=",;\t|"
            )
            .delimiter
        )
    except csv.Error:
        sep = ","
    first = next(csv.reader([lines[0]], delimiter=sep))
    title = None
    if len(lines) > 1 and len([v for v in first if v.strip()]) == 1:
        second = next(csv.reader([lines[1]], delimiter=sep))
        if len(second) > 1:
            title = next(v.strip() for v in first if v.strip())
            text = "\n".join(lines[1:])
    frame = pd.read_csv(
        io.StringIO(text), sep=sep, dtype="string", keep_default_na=False
    )
    if frame.empty:
        raise ValueError("The file has no data rows.")
    return frame, title


def ledger_frame(
    data, mapping, fmt="YYYY-MM-DD", record_type="Expense", source="", import_month=None
):
    if not mapping.get("Amount"):
        raise ValueError("Choose an Amount column.")
    if fmt == "D-Mon (year from import month)":
        if not import_month:
            raise ValueError("Choose an import month to provide the year.")
        copied = data.copy()
        date_column = mapping.get("Date")
        if date_column:
            copied[date_column] = pd.to_datetime(
                copied[date_column].astype("string").str.strip()
                + f"-{import_month.year}",
                format="%d-%b-%Y",
                errors="coerce",
            )
        result = expense_data(copied, mapping, "YYYY-MM-DD")
    else:
        result = expense_data(data, mapping, fmt)
    result["Month"] = result["Date"].dt.strftime("%Y-%m")
    if not mapping.get("Date") and import_month:
        result["Month"] = import_month.strftime("%Y-%m")
    if mapping.get("Type"):
        types = (
            data[mapping["Type"]]
            .astype("string")
            .str.strip()
            .str.casefold()
            .map(
                {
                    "expense": "Expense",
                    "expenses": "Expense",
                    "bill": "Bill",
                    "bills": "Bill",
                }
            )
        )
        if types.isna().any():
            raise ValueError("Type values must be Expense or Bill.")
        result["Type"] = types
    else:
        result["Type"] = record_type
    result["Source"] = source
    return result[LEDGER_COLUMNS].reset_index(drop=True)


def monthly_snapshot(ledger, snapshots, months):
    rows = []
    for month in months:
        d = ledger.loc[ledger["Month"].eq(month)]
        exp = d.loc[d["Type"].eq("Expense"), "Amount"]
        bills = d.loc[d["Type"].eq("Bill")]

        def total(values):
            return float(values.sum(min_count=1)) if values.notna().any() else None

        expense, billed = total(exp), total(bills["Amount"])
        paid = (
            float(bills.loc[bills["Payment Status"].eq("Paid"), "Amount"].sum())
            if billed is not None
            else None
        )
        unpaid = (
            float(bills.loc[bills["Payment Status"].eq("Unpaid"), "Amount"].sum())
            if billed is not None
            else None
        )
        unknown = (
            float(bills.loc[bills["Payment Status"].eq("Unknown"), "Amount"].sum())
            if billed is not None
            else None
        )
        manual = snapshots.get(month, {})
        income, worth = manual.get("Income"), manual.get("Net Worth")
        cash = (
            income - expense - paid
            if all(v is not None for v in (income, expense, paid))
            else None
        )
        rows.append(
            {
                "Month": month,
                "Income": income,
                "Expenses": expense,
                "Bills": billed,
                "Unpaid Bills": unpaid,
                "Unknown Bill Status": unknown,
                "Net Worth": worth,
                "Recorded Cash Flow": cash,
            }
        )
    return pd.DataFrame(rows)


def review_suggestions(ledger, months):
    d = ledger.loc[ledger["Month"].isin(months)]
    results = []
    unpaid = d.loc[d["Type"].eq("Bill") & d["Payment Status"].eq("Unpaid")]
    if len(unpaid):
        amount = unpaid.Amount.sum(min_count=1)
        recorded = (
            f"totaling {amount:,.2f}"
            if pd.notna(amount)
            else "with no usable amount total"
        )
        results.append(
            f"{len(unpaid):,} bills are marked unpaid, {recorded} in the selected months. Check the due dates and payment records."
        )
    unknown = d.loc[d["Type"].eq("Bill") & d["Payment Status"].eq("Unknown")]
    if len(unknown):
        results.append(
            f"{len(unknown):,} bills have an unknown payment status. Confirm them before relying on the unpaid total."
        )
    positive = d.loc[d["Type"].eq("Expense") & d["Amount"].gt(0)]
    categories = (
        positive.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    )
    if len(categories):
        results.append(
            f"{categories.index[0]} is the largest recorded expense category: {categories.iloc[0]:,.2f}, or {categories.iloc[0]/categories.sum()*100:.1f}% of positive expenses. Refunds are excluded from this share."
        )
    recurring = positive.groupby("Description")["Month"].nunique()
    names = recurring[recurring >= 2].index.tolist()
    if names:
        results.append(
            "Repeated across months: "
            + ", ".join(map(str, names[:5]))
            + ". Review whether these recurring costs still serve your needs."
        )
    if d.Amount.isna().any():
        results.append(
            f"{int(d.Amount.isna().sum()):,} records have missing or invalid amounts and are excluded from monetary totals."
        )
    if not results:
        results.append(
            "No review flags were found in the recorded values for these months. Confirm that your imports cover all transactions."
        )
    return results


def sample_ledger():
    expenses = []
    bills = []
    manual = {}
    for i, month in enumerate(["2026-07", "2026-08", "2026-09"]):
        for j in range(18):
            expenses.append(
                {
                    "Date": f"{month}-{j+1:02d}",
                    "Description": [
                        "Groceries",
                        "Transit",
                        "Lunch",
                        "Software",
                        "Coffee",
                        "Supplies",
                    ][j % 6],
                    "Amount": str(250 + (j % 6) * 140 + i * 40),
                    "Expense Category": [
                        "Food",
                        "Transport",
                        "Food",
                        "Work",
                        "Dining",
                        "Work",
                    ][j % 6],
                    "Card Used": ["Cash", "Debit", "Credit"][j % 3],
                    "Paid?": "Yes",
                }
            )
        for j, (name, amount) in enumerate(
            [
                ("Rent", 9500),
                ("Electricity", 1700),
                ("Internet", 1499),
                ("Equipment", 1800),
                ("Insurance", 1400),
            ]
        ):
            bills.append(
                {
                    "Month": month,
                    "Date": pd.Timestamp(f"{month}-{5+j*4:02d}"),
                    "Description": name,
                    "Amount": float(amount),
                    "Category": "Bills",
                    "Card": "Bank",
                    "Payment Status": "Unpaid" if i == 2 and j > 1 else "Paid",
                    "Type": "Bill",
                    "Source": "Sample bills",
                }
            )
        manual[month] = {"Income": 45000 + i * 1800, "Net Worth": 180000 + i * 7000}
    return pd.DataFrame(expenses), pd.DataFrame(bills, columns=LEDGER_COLUMNS), manual


def export_workspace(ledger, snapshots, currency):
    frame = ledger.copy()
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.strftime("%Y-%m-%d")
    records = frame.astype(object).where(frame.notna(), None).to_dict("records")
    return json.dumps(
        {
            "format": "tidygrid-ledger",
            "version": 1,
            "currency": currency,
            "records": records,
            "snapshots": snapshots,
        },
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
    ).encode()


def restore_workspace(raw):
    payload = json.loads(raw)
    if (
        not isinstance(payload, dict)
        or payload.get("format") != "tidygrid-ledger"
        or payload.get("version") != 1
    ):
        raise ValueError("Choose a TidyGrid ledger JSON export.")
    rows = payload.get("records")
    if (
        not isinstance(rows, list)
        or len(rows) > 250000
        or any(
            not isinstance(row, dict) or not set(LEDGER_COLUMNS).issubset(row)
            for row in rows
        )
    ):
        raise ValueError("Invalid ledger records.")
    d = pd.DataFrame(rows, columns=LEDGER_COLUMNS)
    if (
        not d["Type"].isin(["Expense", "Bill"]).all()
        or not d["Payment Status"].isin(["Paid", "Unpaid", "Unknown"]).all()
    ):
        raise ValueError("Invalid record type or payment status.")
    for value in d["Month"].dropna():
        if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", str(value)):
            raise ValueError("Invalid month.")
    d["Date"] = pd.to_datetime(d["Date"], format="%Y-%m-%d", errors="coerce")
    d["Amount"] = parse_amounts(d["Amount"])
    snapshots = payload.get("snapshots", {})
    if not isinstance(snapshots, dict):
        raise ValueError("Invalid monthly snapshots.")
    for month, values in snapshots.items():
        if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", month) or not isinstance(
            values, dict
        ):
            raise ValueError("Invalid snapshot month.")
        for key in ("Income", "Net Worth"):
            value = values.get(key)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (float, int))
                or not math.isfinite(value)
            ):
                raise ValueError("Snapshot amounts must be finite numbers or blank.")
    currency = payload.get("currency", "PHP")
    if currency not in CURRENCIES:
        raise ValueError("Invalid currency label.")
    return d, snapshots, currency


def dashboard_html(ledger, snapshots, currency, months):
    payload = json.loads(export_workspace(ledger, snapshots, currency))
    payload["selected"] = months
    safe = (
        json.dumps(payload, ensure_ascii=False, allow_nan=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    root = Path(__file__).parent
    template = (root / "assets/dashboard-export.html").read_text()
    return (
        template.replace("__STYLE__", (root / "assets/dashboard-export.css").read_text().replace("__FONTS__", font_css(embed=True)))
        .replace("__DATA__", safe)
        .replace(
            "__ANIME__",
            (root / "components/presentation/vendor/anime.umd.min.js").read_text(),
        )
        .encode()
    )
