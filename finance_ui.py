"""Month comparisons, bills, editable snapshots and a portable dashboard."""

import hashlib
import html
import io
from datetime import date
import altair as alt
import pandas as pd
import streamlit as st
from ui import centered_dataframe
from analytics import COLORS, parse_amounts
from charts import show_chart
from finance import (
    CURRENCIES,
    LEDGER_COLUMNS,
    dashboard_html,
    export_workspace,
    ledger_frame,
    monthly_snapshot,
    read_month_csv,
    restore_workspace,
    review_suggestions,
)

NONE = "Not Mapped"
ALIASES = {
    "Amount": ["amount", "value", "cost"],
    "Date": ["date", "due date", "activity date"],
    "Description": ["description", "biller", "bill", "activity", "item"],
    "Category": ["expense category", "category"],
    "Card": ["card used", "card", "payment method"],
    "Payment Status": ["paid", "paid?", "payment status", "paid status"],
    "Type": ["type", "record type"],
}


def guessed(data, field):
    for col in data.columns:
        if str(col).strip().casefold().replace("_", " ") in ALIASES[field]:
            return col
    return NONE


def mapping_controls(data, prefix, with_type=False, defaults=None):
    fields = ["Amount", "Date", "Description", "Category", "Card", "Payment Status"] + (
        ["Type"] if with_type else []
    )
    choices = [NONE] + list(data.columns)
    mapping = {}
    cols = st.columns(2)
    for i, field in enumerate(fields):
        key = prefix + "_" + field.replace(" ", "_")
        if st.session_state.get(key) not in choices:
            initial = (
                defaults.get(field)
                if defaults is not None and field in defaults
                else guessed(data, field)
            )
            st.session_state[key] = initial if initial in choices else NONE
        with cols[i % 2]:
            chosen = st.selectbox(field, choices, key=key)
            mapping[field] = None if chosen == NONE else chosen
    return mapping


def render_finance(context):
    digest = context["digest"]
    data = context["analysis_data"]
    if st.session_state.get("_finance_state", {}).get("digest") != digest:
        seed = st.session_state.get("_finance_seed")
        st.session_state["_finance_state"] = {
            "digest": digest,
            "imports": {"Sample bills": seed[0]} if seed else {},
            "snapshots": dict(seed[1]) if seed else {},
            "currency": "PHP",
        }
    state = st.session_state["_finance_state"]
    if state.pop("restore_pending", False):
        for key in list(st.session_state):
            if key.startswith("finance_base_") or key == "finance_months":
                del st.session_state[key]
        state["base"] = {"mapping": {"Amount": None}}
        state["selected"] = None
        st.session_state["finance_base_Amount"] = NONE
        st.session_state["finance_currency"] = state["currency"]
    settings = state.setdefault("base", {})
    for key, default in [
        ("finance_base_format", settings.get("format", "YYYY-MM-DD")),
        ("finance_base_record_type", settings.get("kind", "Expense")),
        ("finance_base_month", settings.get("month", date.today().replace(day=1))),
        ("finance_currency", state["currency"]),
    ]:
        st.session_state.setdefault(key, default)
    st.caption(
        "Compare months, track bills, and enter your own income and net-worth snapshots. These figures describe your uploaded records."
    )
    with st.expander("Map This Dataset", expanded=not bool(state["imports"])):
        mapping = mapping_controls(data, "finance_base", True, settings.get("mapping"))
        left, right = st.columns(2)
        with left:
            fmt = st.selectbox(
                "Date Format",
                ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"],
                key="finance_base_format",
            )
            record_type = st.selectbox(
                "Record Type",
                ["Expense", "Bill"],
                key="finance_base_record_type",
                help="Used when no Type column is mapped.",
            )
        with right:
            currency = st.selectbox(
                "Currency Label", CURRENCIES, key="finance_currency"
            )
            month = st.date_input(
                "Month for Records Without a Date",
                value=(
                    None
                    if "finance_base_month" in st.session_state
                    else date.today().replace(day=1)
                ),
                key="finance_base_month",
            )
        state["currency"] = currency
        settings.update(mapping=mapping, format=fmt, kind=record_type, month=month)
        st.caption(
            "A currency label does not convert currencies. Keep each ledger in one currency. Do not also import paid bills as expenses, or they will be counted twice in cash flow."
        )
    try:
        base = (
            ledger_frame(data, mapping, fmt, record_type, context["filename"], month)
            if mapping["Amount"]
            else pd.DataFrame(columns=LEDGER_COLUMNS)
        )
    except ValueError as exc:
        st.error(str(exc))
        return
    with st.expander("Add Future Months  /  Import CSV or TSV"):
        files = st.file_uploader(
            "Add One or Several Files",
            type=["csv", "tsv"],
            accept_multiple_files=True,
            key="finance_import_files",
        )
        staged = {}
        valid = True
        for i, file in enumerate(files or []):
            try:
                imported, title = read_month_csv(file.getvalue())
                st.markdown("**" + html.escape(file.name) + "**")
                if title:
                    st.caption(
                        "Month title detected: "
                        + title
                        + ". Confirm the year and date mapping below."
                    )
                prefix = (
                    "finance_import_"
                    + hashlib.sha256((file.name + str(i)).encode()).hexdigest()[:10]
                )
                m = mapping_controls(imported, prefix, True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    kind = st.selectbox(
                        "Record Type",
                        ["Expense", "Bill"],
                        index=(
                            1
                            if (
                                "biller" in " ".join(imported.columns).lower()
                                or "bill" in file.name.lower()
                            )
                            else 0
                        ),
                        key=prefix + "_kind",
                    )
                with c2:
                    form = st.selectbox(
                        "Date Format",
                        [
                            "YYYY-MM-DD",
                            "DD/MM/YYYY",
                            "MM/DD/YYYY",
                            "D-Mon (year from import month)",
                        ],
                        key=prefix + "_fmt",
                    )
                with c3:
                    anchor = st.date_input(
                        "Import Month / Year",
                        value=date.today().replace(day=1),
                        key=prefix + "_month",
                    )
                staged[file.name] = ledger_frame(
                    imported, m, form, kind, file.name, anchor
                )
            except (
                ValueError,
                UnicodeError,
                pd.errors.ParserError,
                pd.errors.EmptyDataError,
            ) as exc:
                valid = False
                st.error(f"{file.name}: {exc}")
        if st.button(
            "Add Files to Ledger",
            disabled=not staged or not valid,
            key="finance_add_files",
            type="primary",
        ):
            state["imports"].update(staged)
            st.success(
                f"{len(staged)} files added. Re-importing the same filename replaces its earlier rows."
            )
        for name, frame in list(state["imports"].items()):
            a, b = st.columns([4, 1])
            a.caption(f"{name}  /  {len(frame):,} rows")
            if b.button(
                "Remove",
                key="finance_remove_" + hashlib.sha256(name.encode()).hexdigest()[:10],
            ):
                del state["imports"][name]
                st.rerun()
        saved_file = st.file_uploader(
            "Restore a TidyGrid Ledger JSON", type=["json"], key="finance_restore_file"
        )
        if st.button(
            "Restore Saved Ledger", disabled=saved_file is None, key="finance_restore"
        ):
            try:
                restored, snapshots, currency = restore_workspace(saved_file.getvalue())
                state.update(
                    imports={"Restored ledger": restored},
                    snapshots=snapshots,
                    currency=currency,
                    restore_pending=True,
                )
                st.rerun()
            except (ValueError, TypeError, KeyError) as exc:
                st.error(f"Could not restore this file: {exc}")
    frames = [frame for frame in [base] + list(state["imports"].values()) if len(frame)]
    ledger = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=LEDGER_COLUMNS)
    )
    if ledger.empty:
        st.info(
            "Map an Amount column or add files to start your monthly dashboard. You can also load the Expenses + Bills sample from the sidebar."
        )
        return
    with st.expander("Income & Net Worth  /  Monthly Entries"):
        st.caption(
            "Enter observed amounts for a month. Leave a value blank to keep it unknown. Entries stay in this session; save a Ledger JSON to keep them."
        )
        with st.form("finance_snapshot_form"):
            month = st.date_input("Snapshot Month", value=date.today().replace(day=1))
            c1, c2 = st.columns(2)
            with c1:
                income = st.text_input("Monthly Income", placeholder="e.g. 45000")
            with c2:
                worth = st.text_input("Month-End Net Worth", placeholder="e.g. 180000")
            if st.form_submit_button("Save Monthly Entry", type="primary"):
                parsed = parse_amounts(pd.Series([income, worth]))
                if any(
                    str(v).strip() and pd.isna(parsed.iloc[i])
                    for i, v in enumerate([income, worth])
                ):
                    st.error("Use numeric amounts, such as 45,000.00.")
                else:
                    state["snapshots"][month.strftime("%Y-%m")] = {
                        "Income": (
                            float(parsed.iloc[0]) if pd.notna(parsed.iloc[0]) else None
                        ),
                        "Net Worth": (
                            float(parsed.iloc[1]) if pd.notna(parsed.iloc[1]) else None
                        ),
                    }
                    st.success("Monthly entry saved.")
        if state["snapshots"]:
            centered_dataframe(
                pd.DataFrame.from_dict(state["snapshots"], orient="index").rename_axis(
                    "Month"
                ),
                width="stretch",
            )
    months = sorted(set(ledger.Month.dropna().tolist()) | set(state["snapshots"]))
    if not months:
        st.info(
            "No valid months were found. Adjust the Date Format or import a file without dates and assign its month."
        )
        return
    key = "finance_months"
    if key not in st.session_state or not set(st.session_state[key]).issubset(months):
        st.session_state[key] = [
            m
            for m in (
                months[-2:] if state.get("selected") is None else state["selected"]
            )
            if m in months
        ]
    selected = st.multiselect("Months to Compare", months, key=key)
    state["selected"] = sorted(selected)
    if not selected:
        st.info("Select at least one month to compare.")
        return
    selected = sorted(selected)
    state["selected"] = selected
    chosen = ledger.loc[ledger.Month.isin(selected)].copy()
    snapshot = monthly_snapshot(ledger, state["snapshots"], selected)
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        st.markdown("### Month Snapshot")
        centered_dataframe(
            snapshot,
            width="stretch",
            hide_index=True,
            column_config={
                col: st.column_config.NumberColumn(col, format="%.2f")
                for col in snapshot.columns
                if col != "Month"
            },
        )
        st.caption(
            "Blank = not recorded / no valid coverage. Cash flow uses income minus expenses minus paid bills. It is a recorded-data calculation, not your verified bank balance."
        )
    with right:
        total = chosen.loc[chosen.Type.eq("Expense"), "Amount"].sum(min_count=1)
        value = f"{total:,.0f}" if pd.notna(total) else "—"
        st.markdown(
            f'<div class="dark-statement"><div class="eyebrow">RECORDED EXPENSES  /  {currency}</div><div class="statement-number">{value}</div><p>{len(selected)} months selected.<br>Amounts are calculated from the imported records.</p></div>',
            unsafe_allow_html=True,
        )
    net = snapshot[["Month", "Net Worth"]].copy()
    net["Net Worth"] = pd.to_numeric(net["Net Worth"])
    c1, c2 = st.columns(2, gap="large")
    with c1:
        with st.container(key="finance_chart_panel"):
            st.markdown("### Net Worth Over Time")
            if net["Net Worth"].notna().any():
                show_chart(
                    alt.Chart(net)
                    .mark_line(
                        color=COLORS[0], point=True, invalid="break-paths-show-domains"
                    )
                    .encode(
                        x=alt.X("Month:O", title=None),
                        y=alt.Y("Net Worth:Q", title=currency),
                        tooltip=["Month", alt.Tooltip("Net Worth:Q", format=",.2f")],
                    )
                )
            else:
                st.info("Add month-end net worth entries to see this chart.")
    with c2:
        st.markdown("### Income, Expenses & Bills")
        totals = snapshot.melt(
            id_vars="Month",
            value_vars=["Income", "Expenses", "Bills"],
            var_name="Measure",
            value_name="Amount",
        ).dropna(subset=["Amount"])
        if len(totals):
            show_chart(
                alt.Chart(totals)
                .mark_bar(cornerRadiusEnd=3)
                .encode(
                    x=alt.X("Month:N", title=None),
                    xOffset="Measure:N",
                    y=alt.Y("Amount:Q", title=currency),
                    color=alt.Color(
                        "Measure:N",
                        scale=alt.Scale(
                            domain=["Income", "Expenses", "Bills"],
                            range=[COLORS[0], COLORS[1], COLORS[3]],
                        ),
                    ),
                    tooltip=[
                        "Month",
                        "Measure",
                        alt.Tooltip("Amount:Q", format=",.2f"),
                    ],
                )
            )
    st.markdown("### Where the Expenses Go")
    categories = (
        chosen.loc[chosen.Type.eq("Expense") & chosen.Amount.notna()]
        .groupby(["Month", "Category"])["Amount"]
        .sum()
        .reset_index()
    )
    if len(categories):
        show_chart(
            alt.Chart(categories)
            .mark_bar()
            .encode(
                x=alt.X("Month:N", title=None),
                y=alt.Y("Amount:Q", title=currency),
                color=alt.Color("Category:N", scale=alt.Scale(range=COLORS)),
                tooltip=["Month", "Category", alt.Tooltip("Amount:Q", format=",.2f")],
            )
        )
    bills = chosen.loc[chosen.Type.eq("Bill")].copy()
    st.markdown("### Bills & Payment Status")
    status = st.selectbox(
        "Payment Status",
        ["All", "Paid", "Unpaid", "Unknown"],
        key="finance_bill_filter",
    )
    if status != "All":
        bills = bills.loc[bills["Payment Status"].eq(status)]
    centered_dataframe(
        bills[["Month", "Description", "Amount", "Date", "Payment Status"]].head(500),
        width="stretch",
        hide_index=True,
        column_config={
            "Description": "Biller",
            "Date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
            "Amount": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.caption(
        "Showing up to 500 bills. Unknown payment status is not treated as paid or unpaid."
    )
    st.markdown("### A Closer Look")
    for i, suggestion in enumerate(review_suggestions(ledger, selected), 1):
        st.markdown(
            f'<div class="insight-row"><span>{i:02d}</span><div>{html.escape(suggestion)}</div></div>',
            unsafe_allow_html=True,
        )
    positive = (
        chosen.loc[chosen.Type.eq("Expense") & chosen.Amount.gt(0)]
        .groupby("Category")
        .Amount.sum()
    )
    if len(positive):
        with st.expander("What If?  /  Explore a Smaller Expense Budget"):
            if st.session_state.get("finance_scenario_category") not in positive.index:
                st.session_state["finance_scenario_category"] = positive.index[0]
            cat = st.selectbox(
                "Expense Category",
                list(positive.index),
                key="finance_scenario_category",
            )
            percent = st.slider(
                "Hypothetical Reduction (%)", 0, 50, 10, key="finance_scenario_percent"
            )
            st.markdown(
                f'<div class="scenario">A {percent}% reduction in {html.escape(str(cat))} would reduce the recorded positive expenses by <strong>{positive[cat]*percent/100:,.2f} {currency}</strong> over the selected months.</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "A scenario using your recorded category total. This does not change your ledger or predict future savings."
            )
    with st.expander("Ledger Records & Import Quality"):
        centered_dataframe(chosen.head(500), width="stretch", hide_index=True)
        st.caption(
            f"{int(ledger.Amount.isna().sum()):,} missing/invalid amounts excluded from totals. {int(ledger.Month.isna().sum()):,} records lack a usable month and are excluded from monthly charts. The downloads contain all ledger rows."
        )
    a, b, c = st.columns(3)
    with a:
        st.download_button(
            "Download Dashboard HTML",
            dashboard_html(ledger, state["snapshots"], currency, selected),
            "tidygrid_dashboard.html",
            "text/html",
            type="primary",
            width="stretch",
            on_click="ignore",
        )
    with b:
        st.download_button(
            "Export Ledger CSV",
            ledger.to_csv(index=False).encode("utf-8-sig"),
            "tidygrid_ledger.csv",
            "text/csv",
            width="stretch",
            on_click="ignore",
        )
    with c:
        st.download_button(
            "Save Ledger JSON",
            export_workspace(ledger, state["snapshots"], currency),
            "tidygrid_ledger.json",
            "application/json",
            width="stretch",
            on_click="ignore",
        )
    st.caption(
        "HTML is an offline, interactive snapshot with month filters and charts. Ledger JSON restores imported records and manual entries in TidyGrid."
    )
