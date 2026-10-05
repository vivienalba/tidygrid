"""In-memory report exports. Uploaded strings are never written as Excel formulas."""

import io
from html import escape
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

GREEN = "F6D46B"


def display_records(df):
    d = df.copy()
    for col in ["Activity date", "Due date", "Completed date"]:
        if col in d:
            d[col] = d[col].dt.strftime("%Y-%m-%d").fillna("")
    return d


def excel_bytes(report):
    wb = Workbook()
    wb.remove(wb.active)
    summary = pd.DataFrame(
        {"Metric": list(report["metrics"]), "Value": list(report["metrics"].values())}
    )
    settings = {
        "Report": report["title"],
        "Frequency": report["kind"],
        "Period start": str(report["start"]),
        "Period end": str(report["end"]),
        "Cutoff date": str(report["as_of"]),
        "Date format": report["date_format"],
        "Completed statuses": ", ".join(report["completed_values"]),
        "Excluded statuses": ", ".join(report["excluded_values"]),
    }
    settings.update(
        {"Column: " + k: v or "Not mapped" for k, v in report["mapping"].items()}
    )
    frames = {
        "Summary": summary,
        "Activities": display_records(report["records"]),
        "By owner": report["owners"],
        "By status": report["statuses"],
        "Trend": report["trend"],
        "Data issues": report["issues"],
        "Methodology": pd.DataFrame({"Notes": report["notes"]}),
        "Settings": pd.DataFrame(
            {"Setting": list(settings), "Value": list(settings.values())}
        ),
    }
    for name, frame in frames.items():
        ws = wb.create_sheet(name)
        ws.append(list(frame.columns))
        for row in frame.itertuples(index=False, name=None):
            values = [
                None if pd.isna(v) else v.item() if hasattr(v, "item") else v
                for v in row
            ]
            ws.append(values)
            for cell in ws[ws.max_row]:
                if isinstance(cell.value, str):
                    cell.data_type = "s"
        for cell in ws[1]:
            cell.data_type = "s"
            cell.font = Font(name="Arial", bold=True, color="000000")
            cell.fill = PatternFill("solid", fgColor=GREEN)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 28
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            letter = col[0].column_letter
            ws.column_dimensions[letter].width = min(
                62, max(18, max(len(str(c.value or "")) for c in col) + 2)
            )
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font = Font(name="Arial", size=11, color="0D0D0D")
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.fill = PatternFill("solid", fgColor="D4C2EF" if cell.column == 1 else "FFFFFF")
        edge = Side(style="thin", color="CDCDCD")
        for row in ws:
            for cell in row:
                cell.border = Border(left=edge, right=edge, top=edge, bottom=edge)
    if len(report["statuses"]):
        ws = wb["By status"]
        chart = BarChart()
        chart.title = "Activities by status"
        chart.add_data(
            Reference(ws, min_col=2, min_row=1, max_row=ws.max_row),
            titles_from_data=True,
        )
        chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=ws.max_row))
        ws.add_chart(chart, "D2")
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def pdf_bytes(report):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=(595.28, 841.89),
        rightMargin=40,
        leftMargin=40,
        topMargin=42,
        bottomMargin=42,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=colors.HexColor("#0D0D0D"),
            spaceAfter=15,
        )
    )
    styles.add(
        ParagraphStyle(name="SmallCell", fontName="Helvetica", fontSize=9, leading=12, alignment=1)
    )

    def para(text, style="BodyText"):
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style])

    def table(frame, widths=None):
        rows = [[para(c, "SmallCell") for c in frame.columns]]
        rows += [
            [para("" if pd.isna(v) else v, "SmallCell") for v in row]
            for row in frame.itertuples(index=False, name=None)
        ]
        if len(rows) == 1:
            return para("No records in this section.")
        t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F6D46B")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#CDCDCD")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F5F7EE")],
                    ),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#0D0D0D")),
                ]
            )
        )
        return t

    story = [
        para(report["title"], "ReportTitle"),
        para(
            f'{report["kind"]} | {report["start"]} to {report["end"]} | Cutoff {report["as_of"]}'
        ),
        Spacer(1, 16),
        para(report["summary"]),
        Spacer(1, 16),
    ]
    metrics = pd.DataFrame(
        {
            "Metric": list(report["metrics"]),
            "Value": [
                (
                    f"{v:,.1f}"
                    if isinstance(v, float)
                    else "Not available" if v is None else str(v)
                )
                for v in report["metrics"].values()
            ],
        }
    )
    story += [
        table(metrics, [335, 180]),
        Spacer(1, 18),
        para("Team workload", "Heading2"),
        table(report["owners"], [175, 85, 85, 85, 85]),
        Spacer(1, 18),
        para("Status breakdown", "Heading2"),
        table(report["statuses"], [335, 180]),
        PageBreak(),
        para("Items needing attention", "Heading2"),
    ]
    attention = (
        report["records"]
        .loc[report["records"]["Overdue by cutoff"], ["Activity", "Owner", "Due date"]]
        .head(30)
    )
    attention = display_records(attention)
    story += [
        table(attention, [260, 150, 105]),
        para(
            "Up to 30 overdue activities are shown here; the Excel export contains the full activity list."
        ),
        Spacer(1, 18),
        para("Methodology & data quality", "Heading2"),
    ]
    for note in report["notes"]:
        story += [para(note), Spacer(1, 7)]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#494741"))
        canvas.drawString(40, 24, "TidyGrid | Review before business use")
        canvas.drawRightString(555, 24, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
