"""TidyGrid — python -m streamlit run app.py"""

import hashlib
import html
import io
import zipfile
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import ParseError
import altair as alt
import pandas as pd
import streamlit as st
from ui import centered_dataframe
from analytics import (
    COLORS,
    dataset_answer,
    expense_data,
    grouped_data,
    numeric_columns,
)
from charts import grouped_chart, show_chart
from cleaning import RULES, SAMPLE_CSV, clean_dataframe, clean_phone, read_csv
from finance import sample_ledger
from finance_ui import mapping_controls, render_finance
from report_exports import excel_bytes, pdf_bytes
from reporting import DATE_FORMATS, PERIODS, build_report, sample_data
from ui import (
    asset,
    before_after,
    csv_pairs,
    csv_summary,
    eyebrow,
    install_styles,
    result_summary,
    illustration,
    logo,
    motion,
    page_intro,
    workbook_summary,
)
from workbook_cleaner import WorkbookSource, clean_workbook

PAGES = ["Data", "Clean", "Dashboard", "Reports", "Ask TidyGrid", "Export"]
ICONS = ["table", "tune", "bar_chart", "description", "chat_bubble_outline", "download"]
ROOT = Path(__file__).parent


def clear_views():
    for key in list(st.session_state):
        if key.startswith(
            ("finance_", "chart_", "expense_", "report_", "wb_")
        ) or key in (
            "_finance_state",
            "_finance_seed",
            "_csv_result",
            "_workbook_result",
            "_wb_config",
            "cleaned_search",
            "cleaned_filter",
            "_answer",
            "dashboard_mode",
            "_dashboard_mode",
            "_latest_report",
            "_report_settings",
        ):
            del st.session_state[key]


def upload_key():
    return "uploaded_file_" + str(st.session_state.get("_generation", 0))


def go_home():
    clear_views()
    st.session_state.pop("_input", None)
    st.session_state["_generation"] = st.session_state.get("_generation", 0) + 1
    st.session_state["page"] = "Data"


def capture_upload():
    file = st.session_state.get(upload_key())
    if file is None:
        go_home()
        return
    clear_views()
    st.session_state["_input"] = (file.name, file.getvalue(), False)
    st.session_state["page"] = "Data"


def load_sample(kind="Cleaning"):
    clear_views()
    st.session_state["_generation"] = st.session_state.get("_generation", 0) + 1
    if kind == "Operations":
        data = sample_data()
        name = "sample_operations.csv"
    elif kind == "Expenses + Bills":
        data, bills, snapshots = sample_ledger()
        name = "sample_expenses.csv"
        st.session_state["_finance_seed"] = (bills, snapshots)
        st.session_state["dashboard_mode"] = "Bills & Cash Flow"
        st.session_state["_dashboard_mode"] = "Bills & Cash Flow"
    else:
        data = None
        name = "sample_operations_data.csv"
    raw = data.to_csv(index=False).encode() if data is not None else SAMPLE_CSV.encode()
    st.session_state["_input"] = (name, raw, True)
    st.session_state["page"] = (
        "Dashboard"
        if kind == "Expenses + Bills"
        else "Reports" if kind == "Operations" else "Data"
    )


def navigate(page):
    st.session_state["page"] = page


def select(label, choices, key):
    if st.session_state.get(key) not in choices:
        st.session_state[key] = choices[0]
    return st.selectbox(label, choices, key=key)


def save_rule(key):
    st.session_state["_rules"][key] = st.session_state["rule_" + key]


def reset_rules():
    st.session_state["_rules"] = {key: True for key, _, _ in RULES}
    for key, _, _ in RULES:
        st.session_state["rule_" + key] = True


def sidebar():
    with st.sidebar:
        st.markdown(logo(True), unsafe_allow_html=True)
        st.button("Back to Home", key="back_home", on_click=go_home, width="stretch")
        for page, icon in zip(PAGES, ICONS):
            st.button(
                page,
                key="nav_" + page,
                type="primary" if st.session_state["page"] == page else "tertiary",
                width="stretch",
                icon=None if icon in {"download", "upload", "arrow_back"} else f":material/{icon}:",
                on_click=navigate,
                args=(page,),
            )


def uploader(compact=False):
    with st.container(key="import_upload"):
        if compact:
            st.markdown("### Import Dataset")
        uploaded = st.file_uploader(
            "Upload CSV, TSV, or Excel",
            type=["csv", "tsv", "xlsx"],
            key=upload_key(),
            on_change=capture_upload,
            label_visibility="collapsed",
        )
        show_settings = uploaded is None or not uploaded.name.lower().endswith(".xlsx")
        with st.container(key="import_options"):
            columns = st.columns(2, gap="small") if compact and show_settings else [st.container()]
            if show_settings:
                with columns[0]:
                    with st.expander("Import Settings"):
                        st.selectbox(
                            "File Encoding",
                            ["UTF-8", "Windows-1252", "UTF-16"],
                            key="import_encoding",
                        )
                        st.selectbox(
                            "Column Separator",
                            ["Auto-detect", "Comma", "Semicolon", "Tab", "Pipe"],
                            key="import_separator",
                        )
            if compact:
                with columns[-1]:
                    with st.expander("Try a Sample Dataset"):
                        for kind in ("Cleaning", "Operations", "Expenses + Bills"):
                            st.button(kind, key="source_sample_" + kind, on_click=load_sample, args=(kind,), width="stretch")
    
    
@st.dialog("Terms and Policies", width="large")
def show_policies():
    policies = {
        "Privacy Policy": "TidyGrid processes files to clean, review, and report on the data you provide. Only upload information you are authorized to process. Hosting services may process technical information needed to run the application. Confirm the deployed application’s security before uploading sensitive or confidential information.",
        "Terms & Conditions": "Automated cleaning may not identify every error. You remain responsible for reviewing values, reports and exports before business use. Use the application only with data you are authorized to process.",
        "Cookie Policy": "This version does not intentionally use advertising cookies. The hosting platform may use technically necessary cookies or similar technologies.",
        "Data Upload Consent": "Uploading a file authorizes the processing needed for the functions you request. Files and monthly entries are held in your Streamlit session. Export a ledger JSON to retain dashboard entries after that session ends.",
        "Accessibility": "TidyGrid uses descriptive controls, keyboard focus, readable tables and reduced-motion support. Report any accessibility barriers you encounter.",
        "Important Notice": "Review cleaned records and report calculations before using them in a CRM, report, or production system. Dashboard insights are calculations from the uploaded records. Open-ended AI chat is not connected in this version.",
    }
    for title, body in policies.items():
        with st.expander(title):
            st.write(body)

def footer():
    with st.container(key="policy_footer"):
        a, b = st.columns([1, 1], vertical_alignment="center")
        with a:
            st.markdown(
                '<p class="footer-copyright">© 2026 FVA  /  TidyGrid</p>',
                unsafe_allow_html=True,
            )
        with b:
            if st.button(
                "Terms and Policies",
                key="open_policies",
                type="tertiary",
                width="stretch",
            ):
                show_policies()


def landing():
    with st.container(key="landing_header"):
        brand, links = st.columns(2, vertical_alignment="center")
        with brand:
            st.markdown(logo(), unsafe_allow_html=True)
        with links:
            st.markdown('<nav class="landing-nav"><a href="#the-workspace">The workspace</a><a href="#how-it-works">How it works</a><a href="#import-dataset">Import data</a></nav>', unsafe_allow_html=True)
    with st.container(key="hero"):
        artwork, copy = st.columns(2, gap="large", vertical_alignment="center")
        with artwork:
            illustration("art/reference-r3.webp", "Illustrated caretaker at work outdoors", "hero_art", 380)
        with copy:
            st.markdown('<h1 class="hero-title"><strong>Clean data.</strong><br><span>Clear direction.</span></h1><p class="hero-copy">A little order makes room for bigger things. Clean your spreadsheets, explore the patterns, and turn everyday operations into useful reports.</p>', unsafe_allow_html=True)
            with st.container(key="hero_actions"):
                a, b = st.columns(2)
                with a:
                    st.button("Explore the sample", type="primary", key="hero_sample", on_click=load_sample, args=("Cleaning",), width="stretch")
                with b:
                    st.markdown('<a class="hero-import-link" href="#import-dataset">Import a dataset</a>', unsafe_allow_html=True)
    with st.container(key="editorial_panel"):
        left, right = st.columns([1, 1.05], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<div class="section-title" role="heading" aria-level="2">Good work starts<br>with a clear view.</div><p class="editorial-copy">Bring the spreadsheet you already have. TidyGrid helps you review your records, choose what needs cleaning, and understand what changed.</p><p class="editorial-copy">Built for operations teams, administrators, freelancers and small businesses. Keep the details in focus, then take your work into a dashboard or report.</p><p class="editorial-note">You stay in control. Choose the rules and review the results. Excel exports retain original sheets and formatting definitions.</p>', unsafe_allow_html=True)
        with right:
            with st.container(key="source_panel"):
                st.markdown('<div id="import-dataset"></div>', unsafe_allow_html=True)
                st.markdown("## Import Dataset")
                st.caption("Start with a CSV, TSV, or Excel workbook.")
                uploader()
    with st.container(key="capabilities"):
        st.markdown('<div id="the-workspace" class="section-title" role="heading" aria-level="2">One workspace. A clearer way to work.</div>', unsafe_allow_html=True)
        items = [
            ("Clean with care.", "Choose your rules. Excel text edits retain the original workbook layout and formatting definitions.", "work-laptop.svg", "Try cleaning", "Cleaning"),
            ("See the pattern.", "Compare expenses, bills and monthly snapshots. Build a chart from the columns that matter.", "work-flag.svg", "Explore a dashboard", "Expenses + Bills"),
            ("Share the story.", "Weekly, monthly, quarterly or annual reports. Download a PDF, Excel report, or interactive dashboard.", "work-mountain.svg", "Build a report", "Operations"),
        ]
        for i, (col, item) in enumerate(zip(st.columns(3, gap="large"), items)):
            title, copy, art, action, kind = item
            with col:
                illustration(art, title, f"feature_art_{i}", 120)
                st.markdown(f'<div class="feature-title" role="heading" aria-level="3">{title}</div><p class="feature-copy">{copy}</p>', unsafe_allow_html=True)
                st.button(action, key=f"feature_sample_{i}", on_click=load_sample, args=(kind,), width="stretch")
    with st.container(key="workflow"):
        st.markdown('<div id="how-it-works" class="section-title" role="heading" aria-level="2">From a file to a fresh perspective.</div>', unsafe_allow_html=True)
        items = [("Bring your data", "Upload a CSV, TSV or Excel workbook."), ("Choose what changes", "Set cleaning rules and review your Excel ranges."), ("Look a little closer", "Compare values, filter records and build a view."), ("Take it with you", "Download cleaned data, dashboards and reports.")]
        for i, (col, (title, copy)) in enumerate(zip(st.columns(4, gap="large"), items)):
            with col:
                illustration(f"art/workflow-{i}.webp", title, f"workflow_art_{i}", 140)
                st.markdown(f'<div class="workflow-title" role="heading" aria-level="3">{title}</div><p class="workflow-copy">{copy}</p>', unsafe_allow_html=True)
    with st.container(key="work_anywhere"):
        left, right = st.columns([1, 1.2], gap="large", vertical_alignment="center")
        with left:
            st.markdown('<div class="section-title" role="heading" aria-level="2">Built around<br>your everyday work.</div><p class="editorial-copy">Customer records, monthly expenses, team activities. Start with your dataset and choose the view that helps you work.</p><p class="editorial-note">Use the same records across cleaning, dashboards and reports. Keep the original file and review each output.</p>', unsafe_allow_html=True)
        with right:
            illustration("reference-r1.svg", "World map with location markers", "map_art", 270)
    with st.container(key="ready_section"):
        left, right = st.columns([1.3, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown("## A useful report starts with the details.")
            st.write("Map your activity dates and statuses, choose a period, and review workload, completion and overdue records. Export an Excel or PDF report.")
            st.button("Try the operations sample", key="landing_reports", type="primary", on_click=load_sample, args=("Operations",))
        with right:
            illustration("art/caretaker.webp", "Illustrated caretaker and cat", "ready_art", 240)


def workbook_context(raw, filename, digest, page):
    source = WorkbookSource(raw)
    if st.session_state.get("_wb_config", {}).get("digest") != digest:
        names = list(source.sheets)
        st.session_state["_wb_config"] = {
            "digest": digest,
            "chosen": names[:1],
            "all": False,
            "ranges": {name: source.sheet(name)["extent"] for name in names},
            "options": {"whitespace": True, "emails": True, "phones": True},
            "current": names[0],
        }
    cfg = st.session_state["_wb_config"]
    names = list(source.sheets)
    if page in ("Data", "Clean"):
        page_intro(
            "EXCEL WORKBOOK",
            "Clean Your Workbook",
            "Select the sheets and the table ranges to review. Every original sheet stays in the export.",
        )
        left, right = st.columns([1.1, 1], gap="large")
        with left:
            with st.expander(f"Choose Sheets  /  {len(names)} Detected", expanded=True):
                cfg["all"] = st.checkbox(
                    "Clean All Sheets", value=cfg["all"], key="wb_all"
                )
                chosen = []
                for i, name in enumerate(names):
                    checked = st.checkbox(
                        name,
                        value=name in cfg["chosen"],
                        disabled=cfg["all"],
                        key=f"wb_sheet_{i}",
                    )
                    if cfg["all"] or checked:
                        chosen.append(name)
                cfg["chosen"] = chosen
                st.caption(f"{len(chosen)} of {len(names)} sheets selected")
        with right:
            with st.expander("Workbook Cleaning Rules", expanded=True):
                for key, label, help_text in RULES:
                    if key not in cfg["options"]:
                        continue
                    cfg["options"][key] = st.checkbox(
                        label,
                        value=cfg["options"][key],
                        key="wb_rule_" + key,
                        help=help_text,
                    )
                st.caption(
                    "Headers and duplicate rows stay in place to preserve the layout. Duplicates are flagged for review."
                )
        with st.expander("Data Ranges", expanded=True):
            st.caption(
                "Include the header row. Exclude titles, summary blocks, notes and separate tables."
            )
            for i, name in enumerate(cfg["chosen"]):
                cfg["ranges"][name] = st.text_input(
                    name + "  /  Range Including Header",
                    value=cfg["ranges"][name],
                    key="wb_range_" + str(names.index(name)),
                )
                if source.sheet(name)["protected"]:
                    st.caption(
                        name
                        + " is protected. Its values will be reviewed but not edited."
                    )
        with st.expander("How Excel Formatting Is Preserved"):
            st.write(
                "Only plain text in selected ranges is cleaned. Formulas, numbers, date values, rich text, merged cells, hyperlinks and protected sheets stay intact. Styles, images, charts, tables, print settings and unselected sheets are retained."
            )
            st.caption(
                "Changed values can affect conditional formatting, chart results and text wrapping. Dates and status labels are not guessed or standardized."
            )
        if st.button(
            "Clean All Sheets" if cfg["all"] else "Clean Selected Sheets",
            key="clean_workbook",
            type="primary",
            disabled=not cfg["chosen"],
            width="stretch",
        ):
            ranges = {name: cfg["ranges"][name] for name in cfg["chosen"]}
            with st.spinner("Cleaning workbook values…"):
                export, reports = clean_workbook(source, ranges, cfg["options"], clean_phone)
            signature = (digest, tuple(ranges.items()), tuple(cfg["options"].items()))
            st.session_state["_workbook_result"] = (signature, export, reports)
    ranges = {name: cfg["ranges"][name] for name in cfg["chosen"]}
    signature = (digest, tuple(ranges.items()), tuple(cfg["options"].items()))
    saved = st.session_state.get("_workbook_result")
    if not cfg["chosen"]:
        st.info("Choose at least one sheet to clean.")
        return None
    if saved is None or saved[0] != signature:
        st.info("Clean the selected sheets to prepare the preview and export.")
        return None
    _, export, reports = saved
    if cfg["current"] not in cfg["chosen"]:
        cfg["current"] = cfg["chosen"][0]
    if st.session_state.get("wb_current") not in cfg["chosen"]:
        st.session_state["wb_current"] = cfg["current"]
    cfg["current"] = st.selectbox(
        "Sheet to Review",
        cfg["chosen"],
        index=cfg["chosen"].index(cfg["current"]),
        key="wb_current",
    )
    current = cfg["current"]
    report = reports[current]
    # Typed analysis uses the edited workbook, while the original preview keeps exact row positions.
    from openpyxl.utils.cell import range_boundaries

    min_col, min_row, max_col, max_row = range_boundaries(cfg["ranges"][current])
    analysis = pd.read_excel(
        io.BytesIO(export),
        sheet_name=current,
        header=min_row - 1,
        usecols=list(range(min_col - 1, max_col)),
        nrows=max_row - min_row,
        keep_default_na=False,
        engine="openpyxl",
    )
    return {
        "kind": "xlsx",
        "filename": filename,
        "digest": hashlib.sha256(
            (digest + current + cfg["ranges"][current]).encode()
        ).hexdigest(),
        "sample": False,
        "data": report["cleaned"].astype("string"),
        "original": report["original"].astype("string"),
        "analysis_data": analysis,
        "report": report,
        "reports": reports,
        "export": export,
    }


def context(page):
    filename, raw, sample = st.session_state["_input"]
    digest = hashlib.sha256(raw).hexdigest()
    with st.expander("Source & Import Settings"):
        st.caption(filename)
        uploader(True)
    if filename.lower().endswith(".xlsx"):
        return workbook_context(raw, filename, digest, page)
    encoding = {"UTF-8": "utf-8-sig", "Windows-1252": "cp1252", "UTF-16": "utf-16"}.get(
        st.session_state.get("import_encoding"), "utf-8-sig"
    )
    sep = st.session_state.get("import_separator", "Auto-detect")
    signature = (digest, encoding, sep, tuple(st.session_state["_rules"].items()))
    cached = st.session_state.get("_csv_result")
    if cached is None or cached[0] != signature:
        original = read_csv(
            raw,
            "utf-8-sig" if sample else encoding,
            "Comma" if sample else sep,
            filename,
        )
        if original.empty:
            st.info(
                "No data rows found. Upload a table with a header and at least one data row."
            )
            return None
        with st.spinner("Preparing your dataset…"):
            cleaned, report = clean_dataframe(original, st.session_state["_rules"])
        export = cleaned.to_csv(index=False).encode("utf-8-sig")
        st.session_state["_csv_result"] = (signature, original, cleaned, report, export)
    _, original, cleaned, report, export = st.session_state["_csv_result"]
    return {
        "kind": "csv",
        "filename": filename,
        "digest": digest,
        "sample": sample,
        "data": cleaned,
        "original": original,
        "analysis_data": cleaned,
        "report": report,
        "export": export,
    }


def file_line(ctx):
    sample = '<span class="sample-label">Sample Data</span>' if ctx["sample"] else ""
    count = len(ctx["data"].columns)
    label = "Column" if count == 1 else "Columns"
    st.markdown(
        f'<div class="file-line"><span class="file-name">{html.escape(ctx["filename"])}</span>{sample}<span> /  {count:,} {label}</span></div>',
        unsafe_allow_html=True,
    )


def preview(data, key, query="", missing=False):
    d = data.copy().astype("string").replace(r"^\s*$", pd.NA, regex=True)
    if missing:
        d = d.loc[d.isna().any(axis=1)]
    if query.strip():
        d = d.loc[
            d.apply(
                lambda column: column.str.contains(
                    query.strip(), case=False, regex=False, na=False
                )
            ).any(axis=1)
        ]
    if d.empty:
        st.info("No rows match this view. Clear the search or choose All Rows.")
        return
    shown = d.head(250).fillna("").copy()
    if st.session_state.get("_preview_csv", True):
        shown.index = shown.index + 1
    centered_dataframe(
        shown,
        width="stretch",
        height=min(520, max(220, len(shown) * 32 + 40)),
        row_height=32,
        key=key,
    )
    st.caption(
        f"Showing {len(shown):,} of {len(d):,} rows in this view. Export contains the complete dataset. Row numbers refer to the source."
    )


def data_page(ctx):
    if ctx["kind"] == "csv":
        page_intro(
            "",
            "Review Your Dataset",
            "A clear view of your records, before and after cleaning.",
        )
        file_line(ctx)
        csv_summary(ctx["report"])
    else:
        workbook_summary(ctx["reports"])
    r = ctx["report"]
    st.session_state["_preview_csv"] = ctx["kind"] == "csv"
    tabs = st.tabs(
        ["Cleaned Data", "Original Data", "Change Log", "Missing Values"]
        + (["Duplicate Rows"] if ctx["kind"] == "xlsx" else [])
    )
    with tabs[0]:
        a, b = st.columns([2.3, 1])
        with a:
            q = st.text_input(
                "Search Cleaned Data",
                placeholder="Search any value…",
                key="cleaned_search",
                icon=":material/search:",
            )
        with b:
            row_view = st.selectbox(
                "Rows to Show",
                ["All Rows", "Rows with Missing Values"],
                key="cleaned_filter",
            )
        preview(ctx["data"], "cleaned_preview", q, row_view != "All Rows")
    with tabs[1]:
        preview(ctx["original"], "original_preview")
        st.caption(
            "The source values before cleaning. Your original file is never overwritten."
        )
    with tabs[2]:
        centered_dataframe(r["log"].head(500), static=True)
        if ctx["kind"] == "csv":
            st.caption(
                "One value may be affected by several rules. Values Updated counts each changed cell once before removing duplicates."
            )
            with st.expander("Column Names"):
                centered_dataframe(r["column_map"], static=True)
        else:
            st.caption(
                "Showing up to 500 changes. This value preview does not display Excel styles; the workbook export retains them."
            )
    with tabs[3]:
        missing = r["missing_table"] if ctx["kind"] == "csv" else r["missing"]
        if missing.empty:
            st.success("No missing values in this range.")
        else:
            centered_dataframe(missing.head(500), width="stretch", hide_index=True)
            st.caption(
                "Blank cells are not filled automatically. Review the affected rows before export."
            )
    if ctx["kind"] == "xlsx":
        with tabs[4]:
            centered_dataframe(r["duplicates"].head(500), width="stretch", hide_index=True)
            st.caption(
                "Duplicate rows stay in their original positions in the workbook."
            )
    st.button(
        "Choose Cleaning Rules",
        on_click=navigate,
        args=("Clean",),
        key="data_to_clean",
    )


def clean_page(ctx):
    page_intro(
        "",
        "A Little Order. A Big Difference.",
        "Choose what changes. Review actual examples before you export.",
    )
    left, right = st.columns([1, 2.2], gap="large")
    with left:
        with st.container(key="clean_controls"):
            if ctx["kind"] == "csv":
                for key, label, help_text in RULES:
                    st.checkbox(
                        label,
                        value=st.session_state["_rules"][key],
                        key="rule_" + key,
                        on_change=save_rule,
                        args=(key,),
                        help=help_text,
                    )
                st.button(
                    "Reset Recommended Rules",
                    type="tertiary",
                    on_click=reset_rules,
                    key="reset_rules",
                )
                st.caption(
                    "Blank and whitespace-only cells are always treated as missing."
                )
            else:
                st.write(
                    "Workbook text rules apply to the selected sheets and ranges above. Headers and duplicate rows stay in place."
                )
    with right:
        if ctx["kind"] == "csv":
            pairs = csv_pairs(ctx["original"], ctx["data"])
        else:
            log = ctx["report"]["log"]
            pairs = []
            for _, row in log.head(3).iterrows():
                pairs.append(
                    (
                        row.get("Cell", "Text"),
                        row.get("Before", ""),
                        row.get("After", ""),
                    )
                )
        before_after(pairs)
    if ctx["kind"] == "csv":
        csv_summary(ctx["report"])
    st.button(
        "Review the Cleaned Data",
        type="primary",
        on_click=navigate,
        args=("Data",),
        key="clean_to_data",
    )


def chart_builder(ctx):
    data=ctx["analysis_data"]
    with st.container(key="chart_controls"):
        a,b,c=st.columns([1.4,1,1],gap="medium")
        with a:group=select("Group By",list(data.columns),"chart_group")
        with b:aggregation=st.selectbox("Calculate",["Count","Sum","Average"],key="chart_aggregation")
        with c:style=st.radio("Chart Style",["Bar","Donut"],horizontal=True,key="chart_style")
        measure=None
        if aggregation!="Count":measure=select("Measure",list(data.columns),"chart_measure")
        with st.expander("Filter Records"):
            column=select("Filter Column",["None"]+list(data.columns),"chart_filter_column")
            if column!="None":
                choices=sorted(data[column].astype("string").fillna("(Missing)").unique().tolist())
                values=st.multiselect("Include Values",choices,default=choices,key="chart_filter_values_"+str(column))
                data=data.loc[data[column].astype("string").fillna("(Missing)").isin(values)]
    grouped,invalid=grouped_data(data,group,measure,aggregation)
    result_summary("The view in numbers",[(f"{len(data):,}","Records","After your filters"),(f"{len(grouped):,}","Groups",str(group).replace("_"," ")),(f"{invalid:,}","Invalid measures","Excluded from calculation")],"chart_summary")
    with st.container(key="chart_canvas"):
        chart,notes=st.columns([3,1],gap="large")
        with chart:
            st.markdown("### "+aggregation+" by "+str(group).replace("_"," "))
            grouped_chart(grouped,style,integer=aggregation=="Count")
            if style=="Donut" and (grouped.Value<0).any():st.caption("Negative values use a bar chart to preserve their sign.")
        with notes:
            st.markdown('<div class="chart-notes"><h3>Reading this view</h3><p>Count shows record volume. Sum and Average use valid numeric values.</p><p>Your selected filters apply to both the chart and its summary.</p></div>',unsafe_allow_html=True)
            if invalid:st.caption(f"{invalid:,} missing or invalid measures excluded.")
            st.download_button("Export Chart Summary CSV",grouped.to_csv(index=False).encode("utf-8-sig"),"tidygrid_chart_summary.csv","text/csv",on_click="ignore",width="stretch")
    with st.expander("Chart Data"):
        centered_dataframe(grouped,width="stretch",hide_index=True)


def expenses(ctx):
    data = ctx["analysis_data"]
    with st.expander("Map Expense Columns", expanded=True):
        mapping = mapping_controls(data, "expense")
        a, b = st.columns(2)
        with a:
            fmt = st.selectbox("Date Format", list(DATE_FORMATS), key="expense_format")
        with b:
            currency = st.selectbox(
                "Currency Label",
                ["PHP", "USD", "EUR", "GBP", "Other"],
                key="expense_currency",
            )
    if not mapping["Amount"]:
        st.info("Choose an Amount column to calculate expense totals.")
        return
    d = expense_data(data, mapping, fmt)
    d["Month"] = d.Date.dt.strftime("%Y-%m")
    months = sorted(d.Month.dropna().unique())
    a, b, c = st.columns(3)
    with a:
        month = select("Period", ["All Dates"] + months, "expense_month")
    with b:
        category = select(
            "Category",
            ["All Categories"] + sorted(d.Category.unique()),
            "expense_category",
        )
    with c:
        status = st.selectbox(
            "Payment Status", ["All", "Paid", "Unpaid", "Unknown"], key="expense_status"
        )
    filtered = d.copy()
    if month != "All Dates":
        filtered = filtered.loc[filtered.Month.eq(month)]
    if category != "All Categories":
        filtered = filtered.loc[filtered.Category.eq(category)]
    if status != "All":
        filtered = filtered.loc[filtered["Payment Status"].eq(status)]
    total = filtered.Amount.sum(min_count=1)
    value = f"{total:,.2f}" if pd.notna(total) else "—"
    left, right = st.columns([2.3, 1], gap="large")
    with left:
        grouped = (
            filtered.groupby("Category")
            .Amount.sum(min_count=1)
            .dropna()
            .sort_values(ascending=False)
            .rename_axis("Group")
            .reset_index(name="Value")
        )
        grouped_chart(grouped)
    with right:
        st.markdown(
            f'<div class="dark-statement"><div class="eyebrow">RECORDED EXPENSES  /  {currency}</div><div class="statement-number">{value}</div><p>{len(filtered):,} records match your filters.</p></div>',
            unsafe_allow_html=True,
        )
    trend = (
        filtered.dropna(subset=["Date", "Amount"])
        .groupby("Date")
        .Amount.sum()
        .reset_index()
    )
    if len(trend):
        show_chart(
            alt.Chart(trend)
            .mark_line(color=COLORS[0], point=True)
            .encode(
                x="Date:T",
                y=alt.Y("Amount:Q", title=currency),
                tooltip=["Date:T", alt.Tooltip("Amount:Q", format=",.2f")],
            )
        )
    with st.expander("Payment Methods & Records"):
        centered_dataframe(
            filtered.groupby("Card").Amount.sum(min_count=1).reset_index(),
            width="stretch",
            hide_index=True,
        )
        centered_dataframe(filtered.head(500), width="stretch", hide_index=True)
    st.caption(
        f"{int(d.Amount.isna().sum()):,} invalid/missing amounts excluded from totals. {int(d.Date.isna().sum()):,} dates missing or invalid; those records are excluded from dated charts. A currency label does not convert currencies."
    )
    st.download_button(
        "Export Filtered Expenses CSV",
        filtered.to_csv(index=False).encode("utf-8-sig"),
        "tidygrid_expenses.csv",
        "text/csv",
        on_click="ignore",
    )


def dashboard_page(ctx):
    page_intro(
        "",
        "A clear view of your operations",
        "Choose a view, refine your records, and review the figures before exporting.",
    )
    file_line(ctx)
    st.session_state.setdefault(
        "dashboard_mode", st.session_state.get("_dashboard_mode", "Chart Builder")
    )
    mode = st.radio(
        "Dashboard Workspace",
        ["Chart Builder", "Expense Dashboard", "Bills & Cash Flow"],
        horizontal=True,
        key="dashboard_mode",
    )
    st.session_state["_dashboard_mode"] = mode
    if mode == "Chart Builder":
        chart_builder(ctx)
    elif mode == "Expense Dashboard":
        expenses(ctx)
    else:
        render_finance(ctx)


def reports_page(ctx):
    page_intro(
        "",
        "Bring the Work into Focus.",
        "Weekly, monthly, quarterly, and annual reports built from your activity records.",
    )
    data = ctx["analysis_data"]
    left, right = st.columns([1, 2], gap="large")
    saved = st.session_state.setdefault("_report_settings", {})
    for key, value in saved.items():
        st.session_state.setdefault(key, value)
    with left:
        with st.container(key="report_controls"):
            illustration("pencil.svg", "Hand-drawn pencil", "report_pencil", 75)
            kind = st.selectbox("Reporting Frequency", PERIODS, key="report_kind")
            anchor = st.date_input(
                "A Date in the Reporting Period",
                value=None if "report_anchor" in st.session_state else date.today(),
                key="report_anchor",
            )
            fmt = st.selectbox("Date Format", list(DATE_FORMATS), key="report_format")
            mapping = {}
            choices = ["Not Mapped"] + list(data.columns)
            aliases = {
                "Activity date": ["activity date", "date", "created date"],
                "Status": ["status", "booking status"],
                "Activity": ["activity", "task", "description"],
                "Owner": ["owner", "assigned to"],
                "Due date": ["due date", "due"],
                "Completed date": ["completed date"],
                "Category": ["category"],
                "Value": ["value", "amount"],
            }

            def map_field(field):
                default = next(
                    (
                        col
                        for col in data.columns
                        if str(col).lower().replace("_", " ") in aliases[field]
                    ),
                    "Not Mapped",
                )
                key = "report_map_" + field
                if st.session_state.get(key) not in choices:
                    st.session_state[key] = default
                value = st.selectbox(field.title(), choices, key=key)
                mapping[field] = None if value == "Not Mapped" else value

            for field in ("Activity date", "Status"):
                map_field(field)
            with st.expander("Additional Report Columns"):
                for field in (
                    "Activity",
                    "Owner",
                    "Due date",
                    "Completed date",
                    "Category",
                    "Value",
                ):
                    map_field(field)
            title = st.text_input(
                "Report Title", value="Operations in Focus", key="report_title"
            )
            value_label = st.text_input(
                "Value Total Label", value="Recorded Value", key="report_value_label"
            )
    for key in list(st.session_state):
        if key.startswith("report_"):
            saved[key] = st.session_state[key]
    with right:
        if not mapping["Activity date"] or not mapping["Status"]:
            illustration("art/caretaker.webp", "Illustrated caretaker reviewing work", "report_empty_art", 250)
            st.info(
                "Map Activity Date and Status to build a report. Optional fields add workload, due-date and value summaries."
            )
            st.button(
                "Try the Operations Sample",
                on_click=load_sample,
                args=("Operations",),
                key="reports_try_sample",
                type="primary",
            )
            return
        statuses = sorted(
            data[mapping["Status"]]
            .astype("string")
            .fillna("")
            .str.strip()
            .unique()
            .tolist()
        )
        c1, c2 = st.columns(2)
        for key in ("report_completed", "report_excluded"):
            if key in st.session_state and not set(st.session_state[key]).issubset(
                statuses
            ):
                st.session_state[key] = [
                    v for v in st.session_state[key] if v in statuses
                ]
        with c1:
            completed = st.multiselect(
                "Completed Statuses",
                statuses,
                default=[
                    v
                    for v in statuses
                    if v.casefold() in ("done", "completed", "complete")
                ],
                key="report_completed",
            )
        with c2:
            excluded = st.multiselect(
                "Excluded Statuses",
                statuses,
                default=[
                    v for v in statuses if v.casefold() in ("cancelled", "canceled")
                ],
                key="report_excluded",
            )
        saved["report_completed"] = completed
        saved["report_excluded"] = excluded
        if set(completed) & set(excluded):
            st.error("A status cannot be both completed and excluded.")
            return
        report = build_report(
            data, mapping, kind, anchor, fmt, completed, excluded, title, value_label
        )
        st.session_state["_latest_report"] = report
        m = report["metrics"]
        with st.container(key="report_header"):
            st.markdown(f'<div class="eyebrow">{kind.upper()} REPORT</div><h2 class="report-title">{html.escape(title)}</h2><p class="report-period">{report["start"]} to {report["end"]} / Cutoff {report["as_of"]}</p>',unsafe_allow_html=True)
        result_summary("The period in numbers",[(f'{m["Activities"]:,}',"Activities",f'{m["Open"]:,} open'),(f'{m["Completed"]:,}',"Completed","Within the reporting cutoff"),(f'{m["Overdue"]:,}',"Overdue","At the reporting cutoff")],"report_summary")
        a, b = st.columns(2)
        with a:
            st.download_button(
                "Export Excel Report",
                excel_bytes(report),
                "tidygrid_" + kind.lower() + "_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                width="stretch",
                on_click="ignore",
            )
        with b:
            st.download_button(
                "Export PDF Report",
                pdf_bytes(report),
                "tidygrid_" + kind.lower() + "_report.pdf",
                "application/pdf",
                width="stretch",
                on_click="ignore",
            )
        if len(report["trend"]):
            show_chart(
                alt.Chart(report["trend"])
                .mark_bar(color=COLORS[0], cornerRadiusEnd=3)
                .encode(
                    x=alt.X("Period:O", title=None),
                    y="Activities:Q",
                    tooltip=["Period", "Activities"],
                )
            )
        st.markdown("### Team Workload")
        centered_dataframe(report["owners"], width="stretch", hide_index=True)
        st.caption(report["summary"])
        with st.expander("Methodology & Data Quality"):
            for note in report["notes"]:
                st.caption(note)
            centered_dataframe(report["issues"], width="stretch", hide_index=True)
        with st.expander("All Report Records"):
            centered_dataframe(report["records"], width="stretch", hide_index=True)


def ask_page(ctx):
    with st.container(key="ask_panel"):
        left, right = st.columns([1.5, 1], gap="large", vertical_alignment="center")
        with left:
            eyebrow("ASK TIDYGRID")
            st.markdown(
                '<div class="ask-title" role="heading" aria-level="1">A clear question.<br>A useful answer.</div><p>Start with the facts in your dataset. Review missing values, duplicate rows, changes, or recorded numeric totals.</p>',
                unsafe_allow_html=True,
            )
        with right:
            illustration("idea.svg", "Hand-drawn light bulb", "ask_art", 180)
    a, b, c = st.columns(3)
    for col, label in zip(
        [a, b, c],
        ["Summarize my dataset", "Find missing values", "Show duplicate rows"],
    ):
        with col:
            if st.button(label, key="ask_" + label, width="stretch"):
                st.session_state["_answer"] = dataset_answer(
                    label, ctx["data"], ctx["report"], ctx["kind"] == "xlsx"
                )
    with st.form("ask_form"):
        question = st.text_input(
            "Your Dataset Question",
            placeholder="e.g. Which columns have missing values?",
        )
        with st.container(key="ask_action"):
            submitted = st.form_submit_button("Ask TidyGrid", type="primary")
        if submitted:
            st.session_state["_answer"] = dataset_answer(
                question, ctx["data"], ctx["report"], ctx["kind"] == "xlsx"
            )
    if st.session_state.get("_answer"):
        st.markdown(
            '<div class="answer-panel" role="status" aria-live="polite">'
            + html.escape(st.session_state["_answer"])
            + "</div>",
            unsafe_allow_html=True,
        )
    st.caption(
        "Local dataset commands run on your current records. Open-ended AI chat is not connected; no data is sent to an AI provider."
    )


def export_page(ctx):
    with st.container(key="export_panel"):
        a, b = st.columns([1.5, 1], gap="large", vertical_alignment="center")
        with a:
            eyebrow("READY FOR THE NEXT STEP")
            st.markdown(
                '<div class="export-title" role="heading" aria-level="1">Clear data.<br>Ready to go.</div><p>Take the complete cleaned dataset with you.<br>Review the changes before using your records in a business system.</p>',
                unsafe_allow_html=True,
            )
        with b:
            illustration("art/walking.webp", "Illustrated person walking with a dog", "export_art", 195)
            st.markdown('<div class="export-file">' + html.escape(ctx["filename"]) + '</div>', unsafe_allow_html=True)
            excel = ctx["kind"] == "xlsx"
            extension = "xlsx" if excel else "csv"
            with st.container(key="export_download"):
                st.download_button(
                    "Export Cleaned Excel Workbook" if excel else "Export Cleaned CSV",
                    ctx["export"],
                    Path(ctx["filename"]).stem + "_cleaned." + extension,
                    (
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        if excel
                        else "text/csv"
                    ),
                    type="primary",
                    width="stretch",
                    on_click="ignore",
                )
            st.caption(
                "Every original sheet is included. Text values in your selected ranges are cleaned."
                if excel
                else "Every cleaned row is included, regardless of your search or preview filters."
            )
    if ctx["kind"] == "csv":
        csv_summary(ctx["report"])
    else:
        workbook_summary(ctx["reports"])
    st.button(
        "Back to the Dataset", on_click=navigate, args=("Data",), key="export_to_data"
    )


def main():
    st.set_page_config(
        page_title="TidyGrid",
        page_icon=str(ROOT / "favicon.png"),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    install_styles()
    st.session_state.setdefault("page", "Data")
    st.session_state.setdefault("_rules", {key: True for key, _, _ in RULES})
    if "_input" not in st.session_state:
        landing()
        footer()
        motion("home", "Home")
        return
    sidebar()
    with st.container(key="workspace_shell"):
        page = st.session_state["page"]
        try:
            ctx = context(page)
            if ctx:
                {
                    "Data": data_page,
                    "Clean": clean_page,
                    "Dashboard": dashboard_page,
                    "Reports": reports_page,
                    "Ask TidyGrid": ask_page,
                    "Export": export_page,
                }[page](ctx)
                st.markdown(
                    '<div class="workspace-footer"><span>Original preserved  /  Review every change</span><span>TidyGrid / '
                    + html.escape(page)
                    + "</span></div>",
                    unsafe_allow_html=True,
                )
        except UnicodeError:
            st.error(
                "Check the file encoding in Source & Import Settings. Try Windows-1252 or UTF-16, or export a CSV UTF-8 file."
            )
        except pd.errors.EmptyDataError:
            st.error(
                "This file is empty. Upload a file with a header row and at least one data row."
            )
        except (
            pd.errors.ParserError,
            ValueError,
            KeyError,
            IndexError,
            zipfile.BadZipFile,
            ParseError,
        ) as exc:
            st.error(f"The dataset could not be processed: {exc}")
            st.caption(
                "Check your file format, selected columns, and Excel ranges. No rows were silently skipped."
            )
        footer()
        motion("workspace", page)


if __name__ == "__main__":
    main()
