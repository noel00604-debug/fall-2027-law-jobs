#!/usr/bin/env python3
"""Build docs/index.html (the dashboard) and README.md from data/*.json.

  python3 tools/build_dashboard.py

Pure standard library. The page inlines the data, so it works on GitHub Pages with no fetches.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from common import (
    CONFIG_PATH,
    DOCS_DIR,
    JOBS_PATH,
    PROGRAMS_PATH,
    ROOT,
    RUNS_PATH,
    SOURCES_PATH,
    clean_record,
    load_json,
    now_iso,
    today,
)

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template.html")


def fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        d = dt.date.fromisoformat(iso)
    except ValueError:
        return iso
    return d.strftime("%b %-d, %Y") if os.name != "nt" else d.strftime("%b %d, %Y")


def build_readme(jobs, programs, runs, config, generated):
    day = today()
    d0 = dt.date.fromisoformat(day)
    open_jobs = [j for j in jobs if j.get("status") == "open"]
    week_ago = (d0 - dt.timedelta(days=7)).isoformat()
    new_week = sorted([j for j in open_jobs if j.get("first_seen", "") >= week_ago],
                      key=lambda j: (j.get("fit_rank", 3), j.get("employer", "")))
    soon = (d0 + dt.timedelta(days=30)).isoformat()
    dl_items = []
    for j in open_jobs:
        if j.get("deadline") and day <= j["deadline"] <= soon:
            dl_items.append((j["deadline"], f"{j['employer']}: {j['title']} ({j['city']})", j["url"]))
    for p in programs:
        if p.get("deadline") and day <= p["deadline"] <= soon and p.get("status_for_noel") != "closed":
            dl_items.append((p["deadline"], f"{p['organization']}: {p['name']}", p["url"]))
    dl_items.sort()
    pages_url = config.get("pages_url") or "docs/index.html"
    lines = []
    lines.append(f"# {config.get('title', 'Fall 2027 Job Search')}")
    lines.append("")
    lines.append(f"Dashboard: {pages_url}")
    lines.append("")
    lines.append(f"Entry-level and bar-pending attorney roles in Miami-Dade and Broward (Fort Lauderdale and south) for a 2027 start. "
                 f"Tax roles first, then government, courts and public interest, then everything else. "
                 f"An agent refreshes this every weekday morning; this file was generated {generated}.")
    lines.append("")
    lines.append(f"Open postings: {len(open_jobs)} (tax-fit {sum(1 for j in open_jobs if j.get('fit_rank') == 1)}). "
                 f"Programs tracked: {len(programs)}. Runs logged: {len(runs)}.")
    lines.append("")
    lines.append("## Deadlines in the next 30 days")
    lines.append("")
    if dl_items:
        for d, label, url in dl_items[:20]:
            lines.append(f"- {fmt_date(d)}: [{label}]({url})")
    else:
        lines.append("None on file.")
    lines.append("")
    lines.append("## New in the last 7 days")
    lines.append("")
    if new_week:
        for j in new_week[:40]:
            fit = {1: "TAX", 2: "GOV", 3: ""}.get(j.get("fit_rank"), "")
            fit = f"{fit} " if fit else ""
            lines.append(f"- {fit}[{j['employer']}: {j['title']}]({j['url']}), {j['city']}"
                         + (f", deadline {fmt_date(j['deadline'])}" if j.get("deadline") else ""))
    else:
        lines.append("Nothing new this week.")
    lines.append("")
    lines.append("## How it works")
    lines.append("")
    lines.append("`data/jobs.json` is the database of postings, `data/programs.json` tracks structured hiring programs and cycles, "
                 "`data/sources.json` is the checklist of places the agent searches, and `data/runs.json` is the run log. "
                 "`tools/db.py` is the only thing that writes to those files; `tools/validate.py` checks them; "
                 "`tools/build_dashboard.py` renders `docs/index.html` and this README. The agent's operating manual is `AGENT.md`.")
    lines.append("")
    return "\n".join(lines)


def main():
    jobs = [clean_record(j) for j in load_json(JOBS_PATH, [])]
    programs = [clean_record(p) for p in load_json(PROGRAMS_PATH, [])]
    sources = load_json(SOURCES_PATH, [])
    runs = load_json(RUNS_PATH, [])
    config = load_json(CONFIG_PATH, {})
    generated = now_iso()

    payload = {
        "generated_at": generated,
        "today": today(),
        "config": {
            "title": config.get("title", "Fall 2027 Job Search"),
            "owner": config.get("owner", "Noel"),
            "repo_url": config.get("repo_url"),
            "pages_url": config.get("pages_url"),
        },
        "jobs": jobs,
        "programs": programs,
        "sources": [{"id": s.get("id"), "name": s.get("name"), "url": s.get("url"),
                     "check_frequency": s.get("check_frequency"), "last_checked": s.get("last_checked")} for s in sources],
        "runs": runs[-15:],
    }
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as fh:
        template = fh.read()
    try:
        gen_dt = dt.datetime.fromisoformat(generated)
        updated_label = gen_dt.strftime("%b %-d, %Y, %-I:%M %p ET")
    except Exception:
        updated_label = generated
    page = (template
            .replace("__TITLE__", html.escape(payload["config"]["title"]))
            .replace("__UPDATED__", html.escape(updated_label))
            .replace("__REPO_URL__", html.escape(config.get("repo_url") or "#"))
            .replace("__DATA_JSON__", data_json))

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    open(os.path.join(DOCS_DIR, ".nojekyll"), "a").close()
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(build_readme(jobs, programs, runs, config, updated_label))
    print(json.dumps({"ok": True, "jobs": len(jobs), "open": sum(1 for j in jobs if j.get("status") == "open"),
                      "programs": len(programs), "generated_at": generated,
                      "wrote": ["docs/index.html", "README.md"]}, indent=2))


if __name__ == "__main__":
    main()
