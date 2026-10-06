"""Quiet, readable charts with the TidyGrid palette."""

import altair as alt
import streamlit as st
from analytics import COLORS


def show_chart(chart):
    st.altair_chart(
        chart.configure_view(stroke=None)
        .configure_axis(
            labelFont="Metropolis, Arial, sans-serif",
            titleFont="Metropolis, Arial, sans-serif",
            labelFontSize=11,
            titleFontSize=12,
            gridColor="#cdcdcd",
            domainColor="#cdcdcd",
            labelColor="#000000",
            titleColor="#000000",
        )
        .configure_legend(
            labelFont="Metropolis, Arial, sans-serif", titleFont="Metropolis, Arial, sans-serif", labelFontSize=11, labelColor="#000000", titleColor="#000000", orient="bottom"
        )
        .properties(height=285, background="#ffffff"),
        width="stretch",
        theme=None,
    )


def grouped_chart(frame, style="Bar", integer=False):
    if frame.empty:
        st.info("No valid values match these filters.")
        return
    shown = frame.head(20)
    base = alt.Chart(shown).encode(
        tooltip=["Group:N", alt.Tooltip("Value:Q", format=",.0f" if integer else ",.2f")]
    )
    if style == "Donut" and (shown.Value >= 0).all():
        chart = base.mark_arc(innerRadius=70, stroke="white", strokeWidth=2).encode(
            theta="Value:Q",
            color=alt.Color("Group:N", scale=alt.Scale(range=COLORS), legend=None),
        )
    else:
        chart = base.mark_bar(color=COLORS[0], cornerRadiusEnd=3).encode(
            x=alt.X("Value:Q", title=None, axis=alt.Axis(tickMinStep=1, format=",.0f") if integer else alt.Axis()), y=alt.Y("Group:N", sort="-x", title=None)
        )
    show_chart(chart)
    if len(frame) > 20:
        st.caption(
            "Chart shows the 20 largest groups. The summary download includes every group."
        )
