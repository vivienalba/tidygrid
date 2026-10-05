"""Reporting logic: one row is one activity; periods follow calendar boundaries."""

from datetime import date, timedelta
from calendar import monthrange
import io
import pandas as pd

PERIODS = ["Weekly", "Monthly", "Quarterly", "Annual"]
DATE_FORMATS = {
    "YYYY-MM-DD": "%Y-%m-%d",
    "DD/MM/YYYY": "%d/%m/%Y",
    "MM/DD/YYYY": "%m/%d/%Y",
}


def period_bounds(kind, anchor):
    if kind == "Weekly":
        start = anchor - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=6)
    if kind == "Monthly":
        return anchor.replace(day=1), anchor.replace(
            day=monthrange(anchor.year, anchor.month)[1]
        )
    if kind == "Quarterly":
        m = ((anchor.month - 1) // 3) * 3 + 1
        return date(anchor.year, m, 1), date(
            anchor.year, m + 2, monthrange(anchor.year, m + 2)[1]
        )
    if kind == "Annual":
        return date(anchor.year, 1, 1), date(anchor.year, 12, 31)
    raise ValueError("Unsupported reporting frequency")


def parse_dates(series, fmt):
    # Datetime-valued Excel cells remain dates; strings use the selected format.
    from datetime import datetime

    def parse(v):
        if isinstance(v, (date, datetime, pd.Timestamp)):
            return pd.Timestamp(v).normalize().tz_localize(None)
        if pd.isna(v) or not str(v).strip():
            return pd.NaT
        return pd.to_datetime(str(v).strip(), format=DATE_FORMATS[fmt], errors="coerce")

    return pd.to_datetime(series.map(parse), errors="coerce")


def load_file(raw, filename, encoding="utf-8-sig", separator="Auto-detect", sheet=0):
    if filename.lower().endswith(".xlsx"):
        return pd.read_excel(
            io.BytesIO(raw),
            sheet_name=sheet,
            dtype=object,
            keep_default_na=False,
            engine="openpyxl",
        )
    import csv

    text = raw.decode(encoding)
    separators = {"Comma": ",", "Tab": "\t", "Semicolon": ";", "Pipe": "|"}
    if separator == "Auto-detect":
        if filename.lower().endswith(".tsv"):
            sep = "\t"
        else:
            try:
                sep = csv.Sniffer().sniff(text[:65536], delimiters=",;\t|").delimiter
            except csv.Error:
                sep = ","
    else:
        sep = separators[separator]
    return pd.read_csv(
        io.StringIO(text), sep=sep, dtype="string", keep_default_na=False
    )


def sample_data():
    rows = []
    names = ["Alex", "Sam", "Jamie", "Morgan"]
    tasks = [
        "Review client records",
        "Prepare quotation",
        "Confirm booking",
        "Update inventory",
        "Prepare weekly report",
        "Follow up inquiry",
    ]
    for i, day in enumerate(pd.date_range("2025-01-01", "2026-12-31", freq="2D")):
        status = ["Completed", "Completed", "In progress", "Pending", "Cancelled"][
            i % 5
        ]
        rows.append(
            {
                "Activity": tasks[i % 6],
                "Activity date": day.strftime("%Y-%m-%d"),
                "Status": status,
                "Owner": names[i % 4],
                "Due date": (day + pd.Timedelta(days=3)).strftime("%Y-%m-%d"),
                "Completed date": (
                    (day + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
                    if status == "Completed"
                    else ""
                ),
                "Category": ["Client support", "Sales", "Bookings"][i % 3],
                "Value": 100 + (i % 8) * 125,
            }
        )
    return pd.DataFrame(rows)


def build_report(
    original,
    mapping,
    kind,
    anchor,
    fmt,
    completed_values,
    excluded_values,
    title,
    value_label,
):
    start, end = period_bounds(kind, anchor)
    previous_start, previous_end = period_bounds(kind, start - timedelta(days=1))
    d = pd.DataFrame(index=original.index)
    d["Source row"] = range(1, len(original) + 1)
    d["Activity"] = (
        original[mapping["Activity"]].astype("string").fillna("")
        if mapping.get("Activity")
        else ["Activity " + str(i + 1) for i in range(len(original))]
    )
    d["Activity date"] = parse_dates(original[mapping["Activity date"]], fmt)
    d["Status"] = (
        original[mapping["Status"]]
        .astype("string")
        .fillna("")
        .str.strip()
        .replace("", "Unknown")
    )
    for field in ["Owner", "Category"]:
        d[field] = (
            original[mapping[field]]
            .astype("string")
            .fillna("")
            .str.strip()
            .replace("", "Unassigned" if field == "Owner" else "Uncategorized")
            if mapping.get(field)
            else ("Unassigned" if field == "Owner" else "Uncategorized")
        )
    notes = []
    invalid = d["Activity date"].isna()
    issues = d.loc[invalid, ["Source row", "Activity", "Status"]].copy()
    issues["Issue"] = "Missing or invalid activity date; excluded from period totals"
    for field in ["Due date", "Completed date"]:
        d[field] = (
            parse_dates(original[mapping[field]], fmt) if mapping.get(field) else pd.NaT
        )
        if mapping.get(field):
            raw_nonempty = (
                original[mapping[field]].astype("string").fillna("").str.strip().ne("")
            )
            bad = raw_nonempty & d[field].isna()
            if bad.any():
                notes.append(
                    f"{int(bad.sum())} invalid {field.lower()} values; those dates were not used."
                )
    if mapping.get("Value"):
        raw_values = original[mapping["Value"]].astype("string").fillna("").str.strip()
        d["Value"] = pd.to_numeric(raw_values, errors="coerce")
        bad = raw_values.ne("") & d["Value"].isna()
        if bad.any():
            notes.append(
                f"{int(bad.sum())} nonnumeric values excluded from {value_label} totals. Use plain numbers without currency symbols or thousands separators."
            )
    else:
        d["Value"] = float("nan")
    completed_set = {str(v).strip().casefold() for v in completed_values}
    excluded_set = {str(v).strip().casefold() for v in excluded_values}
    done = d["Status"].str.casefold().isin(completed_set)
    excluded = d["Status"].str.casefold().isin(excluded_set)
    today = pd.Timestamp.now(tz="Asia/Manila").date()
    as_of = min(end, today)
    if mapping.get("Completed date"):
        completed_asof = (
            done
            & d["Completed date"].notna()
            & (d["Completed date"] <= pd.Timestamp(as_of))
        )
        missing_done_date = done & d["Completed date"].isna()
        if missing_done_date.any():
            notes.append(
                f"{int(missing_done_date.sum())} completed-status rows lack a usable completion date; completion timing is unverified and they are counted as open."
            )
    else:
        completed_asof = done
        notes.append(
            "Completion is based on the uploaded status snapshot; historical completion timing cannot be verified without a completion date."
        )
    d["Completed by cutoff"] = completed_asof
    d["Excluded status"] = excluded
    d["Overdue by cutoff"] = (
        ~completed_asof
        & ~excluded
        & d["Due date"].notna()
        & (d["Due date"] < pd.Timestamp(as_of))
    )

    # Count activities by the user-mapped activity date, including all end-day times.
    def select(a, b):
        return d.loc[
            d["Activity date"].between(
                pd.Timestamp(a),
                pd.Timestamp(b) + pd.Timedelta(days=1),
                inclusive="left",
            )
        ].copy()

    current, previous = select(start, end), select(previous_start, previous_end)
    current["Open by cutoff"] = (
        ~current["Completed by cutoff"] & ~current["Excluded status"]
    )
    eligible = len(current) - int(current["Excluded status"].sum())
    completed = int(
        (current["Completed by cutoff"] & ~current["Excluded status"]).sum()
    )
    metrics = {
        "Activities": len(current),
        "Completed": completed,
        "Open": int(current["Open by cutoff"].sum()),
        "Overdue": int(current["Overdue by cutoff"].sum()),
        "Excluded statuses": int(current["Excluded status"].sum()),
        "Completion rate (%)": round(completed / eligible * 100, 1) if eligible else 0,
        "Previous period activities": len(previous),
        "Activity change": len(current) - len(previous),
    }
    if mapping.get("Value"):
        metrics[value_label] = (
            float(current["Value"].sum(min_count=1))
            if current["Value"].notna().any()
            else None
        )
    owners = (
        current.groupby("Owner", dropna=False)
        .agg(
            Activities=("Activity", "size"),
            Completed=(
                "Completed by cutoff",
                lambda col: int(
                    (col & ~current.loc[col.index, "Excluded status"]).sum()
                ),
            ),
            Open=("Open by cutoff", "sum"),
            Overdue=("Overdue by cutoff", "sum"),
        )
        .reset_index()
    )
    statuses = current.groupby("Status").size().reset_index(name="Activities")
    buckets = (
        current["Activity date"]
        .dt.to_period("D" if kind in ["Weekly", "Monthly"] else "M")
        .astype(str)
    )
    trend = (
        current.assign(Period=buckets)
        .groupby("Period")
        .size()
        .reset_index(name="Activities")
    )
    notes += [
        f'Each row is treated as one activity. The cohort is selected by {mapping["Activity date"]}. Duplicates are not removed automatically.',
        f"Completion and overdue cutoff: {as_of.isoformat()} (Asia/Manila). Overdue means an open activity due before the cutoff; only activities in the selected period are included.",
        "Completion rate excludes the selected excluded statuses. Open includes all other statuses not verified as completed.",
        f"Previous period activity comparison: {previous_start.isoformat()} to {previous_end.isoformat()}. A missing period is not proof of zero business activity.",
    ]
    if end > today:
        notes.append(
            "This period includes future dates. Its activity count may include planned work; completion and overdue figures stop at today."
        )
    notes.append(
        f"{int(invalid.sum())} rows excluded due to missing or invalid activity dates."
    )
    summary = f'{kind} report: {len(current):,} activities, {completed:,} completed, {metrics["Open"]:,} open, and {metrics["Overdue"]:,} overdue at the cutoff. Completion rate is {metrics["Completion rate (%)"]:.1f}% of eligible activities.'
    return {
        "title": title,
        "kind": kind,
        "start": start,
        "end": end,
        "as_of": as_of,
        "metrics": metrics,
        "summary": summary,
        "records": current,
        "owners": owners,
        "statuses": statuses,
        "trend": trend,
        "issues": issues,
        "notes": notes,
        "mapping": mapping,
        "date_format": fmt,
        "completed_values": completed_values,
        "excluded_values": excluded_values,
    }
