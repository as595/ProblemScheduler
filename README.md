# ProblemScheduler

**How to be a Student — Blocked vs. Interleaved Problem Scheduler**

When you work through a problem sheet after a lecture, should the questions be
ordered sequentially in blocks by topic, or should the topics be *interleaved*,
mixing in questions from earlier lectures? This tool builds both kinds of
problem-sheet schedule so you can apply them to your own courses and compare
them side by side.

It accompanies the post
[*A tangled web*](https://howtobeastudent.substack.com/p/a-tangled-web) on the
[How to be a Student](https://howtobeastudent.substack.com/) Substack, and the
schedules follow Fig. 1 of Samani & Pan (2021), *Interleaved practice enhances
memory and problem-solving ability in undergraduate physics*, npj Science of
Learning (<https://www.nature.com/articles/s41539-021-00110-x>).

## Contents

- `interleaving_scheduler.py` — the core library and a command-line interface
  that generates the blocked and interleaved orderings.
- `interleaving_app.py` — a [Streamlit](https://streamlit.io) dashboard for
  exploring the schedules interactively.
- `requirements.txt` — Python dependencies for the app.

## How the schedules are built

One problem sheet accompanies each lecture, and each lecture introduces one
topic that is practised with `Q` problems.

- **Blocked** — sheet *i* holds topic *i* with its problems in order
  (`A1 A2 A3`): one topic practised at a time.
- **Interleaved** — topic *t*'s problem *p* lands on sheet *t + p - 1*, so each
  successive problem switches topic and a topic's `Q` problems are spread across
  consecutive sheets.

When fitting the interleaved schedule within the course's weeks, the trailing
problems are folded back so nothing spills past the final lecture. A moved
problem is never placed before the sheet where it appears in the blocked
schedule (sheet >= its topic index). The **gradual** tail mode eases the extra
questions in across the last several sheets (a smooth staircase such as
`1, 2, 3, 3, 3, 3, 4, 4, 4`); the **concentrated** mode keeps every topic fully
interleaved and piles the extras onto the final one or two sheets.

## Usage

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the interactive app:

```bash
streamlit run interleaving_app.py
```

Or generate a schedule from the command line:

```bash
python interleaving_scheduler.py --lectures-per-week 3 --weeks 8 --questions-per-sheet 3
```

Command-line options:

- `-l, --lectures-per-week` — lectures (and problem sheets) per week.
- `-w, --weeks` — number of weeks in the course.
- `-q, --questions-per-sheet` — problems per topic (= questions on a blocked sheet).
- `--tail {gradual,concentrated}` — how leftover questions are absorbed (default `gradual`).
- `--spill` — let the interleaved schedule spill onto extra tail sheets instead of fitting within the course.

## Licence

See [LICENSE](LICENSE).
