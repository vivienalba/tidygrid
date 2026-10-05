"""TidyGrid presentation. Native widgets handle all data and actions."""

import base64
import html
from pathlib import Path
import streamlit as st
import streamlit.components.v2 as components_v2
from typography import font_css

ROOT = Path(__file__).resolve().parent
_presentation = None
_COMPONENT_CSS=(ROOT/'components/presentation/presentation.css').read_text()
_COMPONENT_JS=(ROOT/'components/presentation/vendor/anime.umd.min.js').read_text()+'\n'+(ROOT/'components/presentation/presentation.js').read_text()


def install_styles():
    global _presentation
    # Register through the public API once per script execution, including fresh runtimes.
    _presentation=components_v2.component('tidygrid_presentation', html='<style class="fonts"></style><div class="presentation"></div>', css=_COMPONENT_CSS, js=_COMPONENT_JS)
    st.markdown('<style>'+font_css()+(ROOT/'assets/design-system.css').read_text()+'</style>',unsafe_allow_html=True)


def asset(name):
    path = ROOT / "assets" / name
    mime = {".svg": "image/svg+xml", ".jpeg": "image/jpeg", ".jpg": "image/jpeg"}.get(path.suffix.lower(), "image/png")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def centered_dataframe(data, **kwargs):
    """Use native column alignment so canvas-rendered tables remain interactive."""
    if kwargs.pop("static", False):
        return st.table(data.style.hide(axis="index") if hasattr(data, "style") else data, border="horizontal", width="stretch")
    frame = getattr(data, "data", data) if not hasattr(data, "columns") else data
    supplied = kwargs.pop("column_config", {}) or {}
    config = {}
    for key in ["_index", *list(getattr(frame, "columns", [])), *supplied]:
        value = supplied.get(key)
        if isinstance(value, str):
            value = {"label": value}
        config[key] = {**(value or {}), "alignment": "center"}
    return st.dataframe(data, column_config=config, **kwargs)


def logo(dark=False):
    return (
        '<div class="tg-logo'
        + (" inverse" if dark else "")
        + '"><svg viewBox="0 0 32 32" aria-hidden="true"><rect x="2" y="2" width="27" height="27" rx="6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M3 12H29M12 3V29M13 21L18 25L26 16" fill="none" stroke="currentColor" stroke-width="1.5"/></svg><span>TidyGrid</span></div>'
    )


def eyebrow(text):
    st.markdown(
        '<div class="eyebrow">' + html.escape(text) + "</div>", unsafe_allow_html=True
    )


def page_intro(kicker, title, description=""):
    st.markdown(
        f'<div class="page-intro"><div class="eyebrow">{html.escape(kicker)}</div><h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></div>',
        unsafe_allow_html=True,
    )


def motion(mode,page):
    """Native controls use CSS; Anime runs only inside the supported component."""
    return None


def illustration(name,alt,key,height=300):
    _presentation(data={'kind':'art','src':asset(name),'alt':alt,'height':height,'fonts':font_css()},key=key)


def render_summary(stats,key):
    _presentation(data={'kind':'summary','items':[dict(value=f'{int(n):,}',label=label,detail=detail,warning=warn) for n,label,detail,warn in stats],'fonts':font_css()},key=key)


def csv_summary(report):
    render_summary(
        [
            (
                report["cleaned_rows"],
                "Rows to Export",
                f"From {report['original_rows']:,} source rows",
                False,
            ),
            (
                report["edited_cells"],
                "Values Updated",
                "Each changed cell counted once",
                False,
            ),
            (
                report["duplicates_removed"],
                "Duplicates Removed",
                "First occurrence kept",
                False,
            ),
            (
                report["missing_cells"],
                "Missing Cells",
                f"In {report['missing_rows']:,} rows",
                bool(report["missing_cells"]),
            ),
        ],
        "csv_summary",
    )


def workbook_summary(reports):
    render_summary(
        [
            (len(reports), "Sheets Reviewed", "Every original sheet retained", False),
            (
                sum(r["changed"] for r in reports.values()),
                "Text Cells Updated",
                "Inside the selected ranges",
                False,
            ),
            (
                sum(len(r["duplicates"]) for r in reports.values()),
                "Duplicates Flagged",
                "Rows stay in place",
                False,
            ),
            (
                sum(len(r["missing"]) for r in reports.values()),
                "Missing Cells",
                "Left blank for review",
                True,
            ),
        ],
        "workbook_summary",
    )


def csv_pairs(original, cleaned):
    pairs = []
    for i, name in enumerate(original.columns):
        before = original.loc[cleaned.index, name].astype("string").fillna("")
        after = cleaned.iloc[:, i].astype("string").fillna("")
        changed = before.ne(after)
        for index in before.index[changed][:1]:
            pairs.append((str(name), before.loc[index], after.loc[index]))
            if len(pairs) == 3:
                return pairs
    return pairs


def before_after(pairs):
    _presentation(data={'kind':'comparison','pairs':[[str(v) for v in row] for row in pairs],'fonts':font_css()},key='before_after')
    st.caption('Examples from actual changed cells. ␣ marks a space at the beginning or end.')
