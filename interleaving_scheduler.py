#!/usr/bin/env python3
"""
interleaving_scheduler.py

Generate BLOCKED and INTERLEAVED problem orderings that follow the general
pattern of Figure 1 in:

    Samani & Pan (2021), "Interleaved practice enhances memory and
    problem-solving ability in undergraduate physics", npj Science of Learning.
    https://www.nature.com/articles/s41539-021-00110-x

--------------------------------------------------------------------------
The scheme (as described in the paper / Fig. 1)
--------------------------------------------------------------------------
- There is one homework problem sheet per lecture.
- Each lecture introduces one new *topic*.
- Every topic is practiced with Q problems, numbered 1..Q ("subscripts").
  In the paper Q = 3 (e.g. topic A -> A1, A2, A3).

BLOCKED: a topic is practiced all at once. The sheet that follows a lecture
contains that lecture's own topic, with its Q problems in succession:
        sheet i  ->  [ i1, i2, i3, ... iQ ]
(i.e. "one topic practiced at a time").

INTERLEAVED: only one problem per topic appears on a sheet, and a topic's
Q problems are spread across Q consecutive sheets. Problem 1 of a topic
appears on the sheet right after its lecture, problem 2 on the next sheet,
and so on:
        sheet j  ->  [ j1, (j-1)2, (j-2)3, ... (j-Q+1)Q ]
so every successive problem on a sheet switches topic.

Both schedules contain exactly the same set of problems; only the
arrangement differs. Because a topic's later problems land on later
sheets, the interleaved schedule has a short "ramp-up" at the start (the
first sheets can only draw on the few topics introduced so far). By
default the schedule is kept within the weeks of the course: the trailing
problems of the final topics, which would otherwise spill past the last
lecture, are folded onto the final sheet(s), so those later sheets simply
hold extra questions. This is consistent with the figure in the paper.
--------------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import List, Set, Tuple


# A single problem is identified by (topic_index, problem_number), both 1-based.
Problem = Tuple[int, int]


@dataclass
class Schedule:
    """A list of sheets; each sheet is a list of (topic, problem_number)."""
    kind: str                       # "blocked" or "interleaved"
    sheets: List[List[Problem]] = field(default_factory=list)
    # Problems that were folded from a past-the-course "tail" sheet onto an
    # earlier sheet (only populated for a fitted interleaved schedule).
    folded: Set[Problem] = field(default_factory=set)

    def total_problems(self) -> int:
        return sum(len(s) for s in self.sheets)


def topic_label(topic_index: int) -> str:
    """1 -> 'A', 26 -> 'Z', 27 -> 'AA', ... (spreadsheet-style)."""
    label = ""
    n = topic_index
    while n > 0:
        n, rem = divmod(n - 1, 26)
        label = chr(ord("A") + rem) + label
    return label


def build_blocked(num_lectures: int, questions_per_sheet: int) -> Schedule:
    """
    One sheet per lecture. Each sheet holds a single topic, all Q problems
    in order: topic i -> [(i,1), (i,2), ..., (i,Q)].
    """
    q = questions_per_sheet
    sheets = [[(i, p) for p in range(1, q + 1)]
              for i in range(1, num_lectures + 1)]
    return Schedule(kind="blocked", sheets=sheets)


MAX_EXTRA_PER_SHEET = 2   # target cap on folded problems added to a sheet


def _gradual_profile(n: int, q: int) -> List[int]:
    """Return a per-sheet target problem-count that rises smoothly.

    Start from the natural interleaved load min(k, Q) -- the ramp-up 1, 2,
    ..., Q at the start and a flat Q thereafter -- then add the surplus
    Q(Q-1)/2 (the problems that would otherwise spill past the course) as +1
    bumps applied to the LATER sheets first. The result is a non-decreasing
    "staircase" such as 1, 2, 3, 3, 3, 3, 4, 4, 4 that eases up to its peak
    rather than jumping at the very end.
    """
    target = [min(k, q) for k in range(1, n + 1)]
    surplus = n * q - sum(target)
    # Sheets eligible for a bump: the flat region [q, n], latest first.
    region = list(range(n, q - 1, -1)) or list(range(n, 0, -1))
    i = 0
    while surplus > 0:
        target[region[i % len(region)] - 1] += 1
        surplus -= 1
        i += 1
    return target


def _place_to_profile(n: int, q: int, target: List[int]):
    """Assign every problem to a sheet so the per-sheet counts match `target`.

    Keeps each topic's problems in order, never places a problem before its
    topic's lecture (sheet >= t), and prefers one problem per topic per sheet
    (interleaving). A topic is only clustered (more than one of its problems
    on a sheet) when it is forced -- i.e. a late topic with too few sheets
    left to spread its problems -- which is exactly what lets the tail grow
    gradually. Returns (sheets, folded) where `folded` are the problems that
    ended up somewhere other than their natural sheet (t + p - 1).
    """
    remaining = {t: q for t in range(1, n + 1)}
    next_p = {t: 1 for t in range(1, n + 1)}
    sheets: List[List[Problem]] = [[] for _ in range(n)]

    for k in range(1, n + 1):
        slots = target[k - 1]
        placed_here: Set[int] = set()

        # Forced: a topic with more problems left than sheets remaining after
        # this one must place the excess now (clustering).
        for t in range(1, k + 1):
            if remaining[t] <= 0:
                continue
            must = max(0, remaining[t] - (n - k))
            for _ in range(must):
                sheets[k - 1].append((t, next_p[t]))
                next_p[t] += 1
                remaining[t] -= 1
                slots -= 1
                placed_here.add(t)

        # Fill the rest with distinct topics, most urgent (least slack) first.
        while slots > 0:
            cands = [t for t in range(1, k + 1)
                     if remaining[t] > 0 and t not in placed_here]
            if not cands:                       # allow a repeat only if forced
                cands = [t for t in range(1, k + 1) if remaining[t] > 0]
            if not cands:
                break
            t = min(cands, key=lambda t: ((n - k + 1) - remaining[t], t))
            sheets[k - 1].append((t, next_p[t]))
            next_p[t] += 1
            remaining[t] -= 1
            slots -= 1
            placed_here.add(t)

    folded: Set[Problem] = set()
    ordered: List[List[Problem]] = []
    for k in range(1, n + 1):
        row = sorted(sheets[k - 1], key=lambda tp: (tp[1], tp[0]))
        for (t, p) in row:
            if k != t + p - 1:
                folded.add((t, p))
        ordered.append(row)
    return ordered, folded


def build_interleaved(num_lectures: int, questions_per_sheet: int,
                      fit_within_course: bool = True,
                      tail: str = "gradual") -> Schedule:
    """
    One problem per topic per sheet; a topic's Q problems are spread over
    consecutive sheets:

        topic t, problem p  ->  natural sheet (t + p - 1)

    With fit_within_course=False, the schedule spills onto Q-1 extra "tail"
    sheets beyond the course (num_lectures + Q - 1 sheets total); every sheet
    then holds at most Q problems. (`tail` is ignored in this case.)

    When fit_within_course=True, `tail` controls how the schedule is packed
    into the course's `num_lectures` sheets:

      * "gradual" (default): the per-sheet problem count rises as a smooth
        non-decreasing staircase (e.g. 1, 2, 3, 3, 3, 3, 4, 4, 4). This is
        achieved by letting the final few topics -- which cannot be fully
        spread out anyway -- cluster slightly earlier, so the extra questions
        ease in across the last several sheets instead of spiking on the last
        one or two.
      * "concentrated": the natural interleaving is kept intact for every
        topic and only the spill-over problems are folded back, which piles
        the extra questions onto the final one or two sheets.

    In both tail modes a problem is never placed before the sheet where it
    appears in the BLOCKED schedule (sheet >= t, since topic t is only
    introduced at lecture t), each topic's problems stay in order, and the
    set of problems that moved off their natural sheet is recorded on the
    returned Schedule.
    """
    q = questions_per_sheet
    n = num_lectures

    if not fit_within_course:
        n_sheets = n + q - 1
        buckets: List[List[Problem]] = [[] for _ in range(n_sheets)]
        for t in range(1, n + 1):
            for p in range(1, q + 1):
                buckets[t + p - 2].append((t, p))
        sheets = [sorted(b, key=lambda tp: (tp[1], tp[0])) for b in buckets]
        return Schedule(kind="interleaved", sheets=sheets)

    if tail == "gradual" and n > q:
        target = _gradual_profile(n, q)
        sheets, folded_set = _place_to_profile(n, q, target)
        return Schedule(kind="interleaved", sheets=sheets, folded=folded_set)

    # --- fitted schedule (concentrated tail) ------------------------------
    base: List[List[Problem]] = [[] for _ in range(n)]     # natural placement
    spillover: List[Problem] = []
    for t in range(1, n + 1):
        for p in range(1, q + 1):
            j = t + p - 1                                  # natural sheet
            if j <= n:
                base[j - 1].append((t, p))
            else:
                spillover.append((t, p))

    fold: List[List[Problem]] = [[] for _ in range(n)]     # folded extras
    extras = [0] * n
    folded_set: Set[Problem] = set()

    # Place the most-constrained (largest topic index) spill-overs first.
    for (t, p) in sorted(spillover, key=lambda tp: (-tp[0], -tp[1])):
        lo = t                                             # blocked boundary
        placed = None
        # Prefer the earliest feasible sheet that still has room: this fills
        # sheets to a single extra before doubling any, and -- because later
        # topics have more spill-overs forced onto later sheets -- leaves the
        # doubles sitting towards the final sheet.
        for s in range(lo, n + 1):
            if extras[s - 1] < MAX_EXTRA_PER_SHEET:
                placed = s
                break
        if placed is None:                                 # cap unavoidable
            placed = n                                     # (large Q only)
        fold[placed - 1].append((t, p))
        extras[placed - 1] += 1
        folded_set.add((t, p))

    sheets = []
    for s in range(n):
        row = (sorted(base[s], key=lambda tp: (tp[1], tp[0])) +
               sorted(fold[s], key=lambda tp: (tp[1], tp[0])))
        sheets.append(row)
    return Schedule(kind="interleaved", sheets=sheets, folded=folded_set)


def format_schedule(sched: Schedule, week_size: int | None = None) -> str:
    """Render a schedule as a text grid resembling Fig. 1.

    Each problem shows as e.g. 'A1' (topic letter + problem number).
    If week_size (lectures per week) is given, a blank line separates weeks.
    """
    lines = [f"{sched.kind.upper()} schedule "
             f"({len(sched.sheets)} sheets, "
             f"{sched.total_problems()} problems)"]
    width = max((len(s) for s in sched.sheets), default=0)
    header = "Sheet | " + "  ".join(f"Q{c+1:<3}" for c in range(width))
    lines.append(header)
    lines.append("-" * len(header))
    for idx, sheet in enumerate(sched.sheets, start=1):
        cells = [f"{topic_label(t)}{p}" for (t, p) in sheet]
        cells += [""] * (width - len(cells))          # pad ragged rows
        row = f"{idx:>4}  | " + "  ".join(f"{c:<4}" for c in cells)
        lines.append(row.rstrip())
        if week_size and idx % week_size == 0 and idx != len(sched.sheets):
            lines.append("")
    return "\n".join(lines)


def generate(lectures_per_week: int, weeks: int, questions_per_sheet: int,
             fit_within_course: bool = True, tail: str = "gradual"
             ) -> Tuple[Schedule, Schedule]:
    """Top-level helper. Returns (blocked, interleaved) schedules."""
    if min(lectures_per_week, weeks, questions_per_sheet) < 1:
        raise ValueError("all parameters must be >= 1")
    num_lectures = lectures_per_week * weeks
    blocked = build_blocked(num_lectures, questions_per_sheet)
    interleaved = build_interleaved(num_lectures, questions_per_sheet,
                                    fit_within_course=fit_within_course,
                                    tail=tail)
    return blocked, interleaved


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate blocked & interleaved problem orderings "
                    "in the style of Fig. 1 of Samani & Pan (2021).")
    ap.add_argument("-l", "--lectures-per-week", type=int, required=True,
                    help="number of lectures (and problem sheets) per week")
    ap.add_argument("-w", "--weeks", type=int, required=True,
                    help="number of weeks in the course")
    ap.add_argument("-q", "--questions-per-sheet", type=int, required=True,
                    help="problems per topic (= questions on a blocked sheet)")
    ap.add_argument("--spill", action="store_true",
                    help="let the interleaved schedule spill onto extra tail "
                         "sheets beyond the course instead of fitting it "
                         "within the course")
    ap.add_argument("--tail", choices=("gradual", "concentrated"),
                    default="gradual",
                    help="when fitting within the course, whether the extra "
                         "questions ease in gradually across the last sheets "
                         "(default) or pile onto the final one or two")
    args = ap.parse_args()

    blocked, interleaved = generate(
        args.lectures_per_week, args.weeks, args.questions_per_sheet,
        fit_within_course=not args.spill, tail=args.tail)

    n = args.lectures_per_week * args.weeks
    print(f"Course: {args.weeks} weeks x {args.lectures_per_week} lectures/week "
          f"= {n} lectures/topics; {args.questions_per_sheet} problems/topic\n")
    print(format_schedule(blocked, week_size=args.lectures_per_week))
    print()
    print(format_schedule(interleaved, week_size=args.lectures_per_week))


if __name__ == "__main__":
    main()
