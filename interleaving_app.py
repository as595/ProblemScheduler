#!/usr/bin/env python3
"""
interleaving_app.py — Streamlit dashboard for interleaving_scheduler.py

Interactively generate and visualise BLOCKED vs INTERLEAVED problem
orderings in the style of Fig. 1 of Samani & Pan (2021),
"Interleaved practice enhances memory and problem-solving ability in
undergraduate physics", npj Science of Learning.
https://www.nature.com/articles/s41539-021-00110-x

Run with:
    streamlit run interleaving_app.py
"""

from __future__ import annotations

import colorsys
import io
from datetime import date

import pandas as pd
import streamlit as st

# Reuse the scheduling logic from the companion script.
from interleaving_scheduler import Schedule, generate, topic_label


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def topic_color(topic_index: int, num_topics: int) -> str:
    """Evenly spaced, readable hues so each topic has its own colour."""
    hue = (topic_index - 1) / max(num_topics, 1)
    r, g, b = colorsys.hls_to_rgb(hue, 0.80, 0.55)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def schedule_to_dataframe(sched: Schedule) -> pd.DataFrame:
    """Rows = sheets, columns = Q1..Qk, cells = 'A1' style labels ('' if empty)."""
    width = max((len(s) for s in sched.sheets), default=0)
    rows = []
    for sheet in sched.sheets:
        cells = [f"{topic_label(t)}{p}" for (t, p) in sheet]
        cells += [""] * (width - len(cells))
        rows.append(cells)
    cols = [f"Q{c + 1}" for c in range(width)]
    df = pd.DataFrame(rows, columns=cols)
    df.index = pd.Index(range(1, len(sched.sheets) + 1), name="Sheet")
    return df


# Fixed geometry so two independent tables line up row-for-row.
ROW_H = 30          # px height of every body row
SEP_H = 10          # px height of the gap row between weeks


def render_single_grid(sched: Schedule, num_topics: int, week_size: int,
                       title: str, n_rows: int, folded=None) -> str:
    """Render one schedule as its own HTML table with Week + Sheet columns.

    Every table uses the same fixed row height, the same header structure and
    is padded to `n_rows` body rows with the same week-separator gaps, so two
    of these placed side by side align week-for-week and row-for-row.
    """
    folded = folded or set()
    width = max((len(s) for s in sched.sheets), default=0)

    cell = (f"height:{ROW_H}px;padding:2px 8px;text-align:center;"
            "border:1px solid #ffffff;font-weight:600;color:#111;"
            "border-radius:4px;min-width:32px;")
    empty = f"height:{ROW_H}px;"
    head = ("padding:4px 8px;text-align:center;color:#666;"
            "font-size:12px;font-weight:600;")
    title_st = ("padding:6px 10px;text-align:center;color:inherit;"
                "font-size:15px;font-weight:700;")
    wk = "padding:2px 8px;text-align:center;color:#999;font-size:11px;"
    ncols = 2 + width

    html = ["<table style='border-collapse:separate;border-spacing:3px;'>"]
    html.append(f"<tr><th colspan='{ncols}' style='{title_st}'>{title}</th></tr>")
    html.append(f"<tr><th style='{head}'>Wk</th><th style='{head}'>Sheet</th>")
    for c in range(width):
        html.append(f"<th style='{head}'>Q{c + 1}</th>")
    html.append("</tr>")

    prev_week = None
    for idx in range(1, n_rows + 1):
        week = (idx - 1) // week_size + 1
        if prev_week is not None and week != prev_week:
            html.append(f"<tr><td colspan='{ncols}' "
                        f"style='height:{SEP_H}px;padding:0;'></td></tr>")
        prev_week = week

        sheet = sched.sheets[idx - 1] if idx <= len(sched.sheets) else []
        wlabel = week if (idx - 1) % week_size == 0 else ""
        html.append("<tr>")
        html.append(f"<td style='{wk}'>{wlabel}</td>")
        html.append(f"<td style='{head}'>{idx}</td>")
        for c in range(width):
            if c < len(sheet):
                t, p = sheet[c]
                bg = topic_color(t, num_topics)
                extra = ("outline:2px dashed #333;outline-offset:-3px;"
                         if (t, p) in folded else "")
                html.append(f"<td style='{cell}background:{bg};{extra}'>"
                            f"{topic_label(t)}{p}</td>")
            else:
                html.append(f"<td style='{empty}'></td>")
        html.append("</tr>")

    html.append("</table>")
    return "".join(html)


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
st.set_page_config(page_title="Problem Scheduler — Anna Scaife",
                   page_icon="📚", layout="wide")

# Substack "Anna Scaife" branding. Only the accent and typography are themed;
# backgrounds/text stay on Streamlit's theme so the app still works in dark
# mode. Change --brand-accent to match the publication's exact accent colour.
LOGO_URL = ("https://substackcdn.com/image/fetch/$s_!uwDA!,w_88,h_88,c_fill,"
            "f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-"
            "post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F4cb7edd6-1337-"
            "4e2b-8ccb-aaec5565a16f_580x580.png")
ARTICLE_URL = "https://howtobeastudent.substack.com/p/a-tangled-web"
PUBLICATION_URL = "https://howtobeastudent.substack.com/"

st.markdown(
    """
    <style>
      :root { --brand-accent: #FF6719; }
      h1, h2, h3, .masthead-name {
          font-family: Georgia, 'Iowan Old Style', 'Times New Roman', serif;
          letter-spacing: -0.01em;
      }
      a, a:visited { color: var(--brand-accent) !important; }
      .brand-rule {
          border: none; height: 3px; border-radius: 2px;
          background: var(--brand-accent); margin: 0.4rem 0 1.1rem;
      }
      .masthead { display: flex; align-items: center; gap: 14px; }
      .masthead img {
          width: 54px; height: 54px; border-radius: 50%;
          object-fit: cover; border: 2px solid var(--brand-accent);
      }
      .masthead-name { font-size: 1.5rem; font-weight: 700; line-height: 1.1;
                       color: inherit; }
      .masthead-tag { font-size: 0.9rem; opacity: 0.7; color: inherit; }
    </style>
    """,
    unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="masthead">
      <a href="{PUBLICATION_URL}" target="_blank"><img src="{LOGO_URL}"></a>
      <div>
        <div class="masthead-name">How to be a Student</div>
        <div class="masthead-tag">A positive guide to independent learning
        for undergraduate students</div>
      </div>
    </div>
    <hr class="brand-rule">
    """,
    unsafe_allow_html=True)

st.title("Blocked vs. Interleaved Problem Scheduler")
st.markdown(
    f"A companion to the post **[A tangled web]({ARTICLE_URL})** — *does "
    "regularly revisiting past topics help you learn better?*")
st.markdown(
    "When you work through a problem sheet after a lecture, should the "
    "questions be ordered sequentially in blocks by topic, or should the "
    "topics be interleaved, mixing in questions from earlier lectures? It "
    "might seem like a minor difference in approach, but studies have shown "
    "that the impact on learning outcomes can be surprisingly significant. "
    "This tool builds two different kinds of problem-sheet schedule: *blocked* "
    "and *interleaved* so you can apply them to your own courses. Adjust the "
    "details below, then compare the schedules side by side.")
st.caption(
    "This scheduler is inspired by the work of Samani & Pan (2021), "
    "*Interleaved practice enhances memory and problem-solving ability in "
    "undergraduate physics*, npj Science of Learning — "
    "[nature.com](https://www.nature.com/articles/s41539-021-00110-x).")

with st.sidebar:
    st.header("Course parameters")
    lectures_per_week = st.slider("Lectures per week", 1, 7, 3)
    weeks = st.slider("Weeks in course", 1, 20, 8)
    questions_per_sheet = st.slider(
        "Questions per sheet (= problems per topic)", 1, 8, 3)
    fit = st.toggle(
        "Fit interleaved within course weeks",
        value=True,
        help="Fold the trailing interleaved problems back into the course's "
             "weeks. Turn off to let it spill onto extra tail sheets beyond "
             "the course.")
    tail = st.radio(
        "Tail workload",
        options=("gradual", "concentrated"),
        format_func=lambda x: {"gradual": "Gradual (smooth ramp)",
                               "concentrated": "Concentrated (late spike)"}[x],
        disabled=not fit,
        help="Gradual eases the extra questions in across the last several "
             "sheets (lower, smoother peak) by letting the final few topics "
             "cluster slightly. Concentrated keeps every topic fully "
             "interleaved and piles the extras onto the final one or two "
             "sheets.")

    num_lectures = lectures_per_week * weeks
    st.divider()
    st.metric("Topics / lectures", num_lectures)
    st.metric("Total problems", num_lectures * questions_per_sheet)

blocked, interleaved = generate(
    lectures_per_week, weeks, questions_per_sheet,
    fit_within_course=fit, tail=tail)

st.info(
    f"**{weeks} weeks × {lectures_per_week} lectures/week = "
    f"{num_lectures} topics**, {questions_per_sheet} problems each. "
    "Both schedules contain the identical set of problems — only the "
    "arrangement differs. Colour = topic, number = problem within topic.")

st.caption(
    "**Blocked** = one topic practiced at a time (all Q problems together). "
    "**Interleaved** = one problem per topic per sheet, topics alternating, "
    "with a topic's problems spread across sheets. The two tables share the "
    "same rows, so weeks (grouped by the **Wk** column and the gaps) line up "
    "across them. Cells with a **dashed outline** are problems moved off their "
    "natural sheet to fit the schedule within the course.")

n_rows = max(len(blocked.sheets), len(interleaved.sheets))
col_b, col_i = st.columns(2)
with col_b:
    st.markdown(
        render_single_grid(blocked, num_lectures, lectures_per_week,
                            "Blocked", n_rows),
        unsafe_allow_html=True)
with col_i:
    st.markdown(
        render_single_grid(interleaved, num_lectures, lectures_per_week,
                            "Interleaved", n_rows,
                            folded=interleaved.folded),
        unsafe_allow_html=True)

# Problems-per-sheet profile for the interleaved schedule.
counts = [len(s) for s in interleaved.sheets]
profile = pd.DataFrame(
    {"problems": counts},
    index=pd.Index(range(1, len(counts) + 1), name="Sheet"))
st.caption(
    f"Interleaved problems per sheet (peak {max(counts)}): "
    + ", ".join(str(c) for c in counts))
st.bar_chart(profile, height=180)

st.divider()

# Tables + downloads
st.subheader("Tables & downloads")
tab_b, tab_i = st.tabs(["Blocked table", "Interleaved table"])
for tab, sched, name in ((tab_b, blocked, "blocked"),
                         (tab_i, interleaved, "interleaved")):
    with tab:
        df = schedule_to_dataframe(sched)
        st.dataframe(df, width="stretch")
        buf = io.StringIO()
        df.to_csv(buf)
        st.download_button(
            f"Download {name} schedule (CSV)",
            buf.getvalue(),
            file_name=f"{name}_schedule.csv",
            mime="text/csv",
            key=f"dl_{name}")

with st.expander("How the two schedules are built"):
    st.markdown(
        "- **Blocked** — sheet *i* holds topic *i* with problems 1..Q in "
        "order: `A1 A2 A3`.\n"
        "- **Interleaved** — topic *t*'s problem *p* lands on sheet "
        "*t + p − 1*, so each successive problem switches topic and a topic's "
        "Q problems are spread across consecutive sheets. This creates the "
        "short ramp-up at the start.\n"
        "- **Fit within course weeks** (on by default) keeps the schedule "
        "within the course's sheets. A moved problem is never placed before "
        "the sheet where it appears in the blocked schedule (sheet ≥ its "
        "topic index), and each topic's problems stay in order. Turning it "
        "off lets the schedule spill onto Q−1 extra tail sheets instead.\n"
        "- **Tail workload** shapes how the leftover questions are absorbed. "
        "*Gradual* eases them in across the last several sheets so the "
        "per-sheet count rises as a smooth staircase (e.g. 1, 2, 3, 3, 3, 3, "
        "4, 4, 4); this lets the final few topics — which can't be fully "
        "spread anyway — cluster slightly. *Concentrated* keeps every topic "
        "fully interleaved and instead piles the extras onto the final one or "
        "two sheets (dashed outline). Both keep the same total problems.\n"
        "- With **Q = 1** there is nothing to interleave, so the two "
        "schedules are identical.")

st.markdown('<hr class="brand-rule">', unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="text-align:center; font-size:0.85rem; opacity:0.7;">
      © {date.today().year} Anna Scaife ·
      <a href="{PUBLICATION_URL}" target="_blank">How to be a Student</a>
    </div>
    """,
    unsafe_allow_html=True)
