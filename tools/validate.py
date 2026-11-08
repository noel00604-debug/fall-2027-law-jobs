#!/usr/bin/env python3
"""Validate data/*.json. Exit code 1 if any error. Warnings do not fail the run.

  python3 tools/validate.py
"""
from __future__ import annotations

import json
import sys

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from common import (
    CONFIDENCE,
    CONFIG_PATH,
    DASH_RE,
    EMPLOYER_TYPES,
    JOBS_PATH,
    JOB_STATUSES,
    PROGRAMS_PATH,
    PROGRAM_STATUSES,
    RUNS_PATH,
    SOURCES_PATH,
    is_iso_date,
    load_json,
    normalize_url,
    zone_check,
)


def strings_in(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings_in(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings_in(v)


def main():
    errors, warnings = [], []

    jobs = load_json(JOBS_PATH, None)
    if not isinstance(jobs, list):
        errors.append("data/jobs.json missing or not a list")
        jobs = []
    seen_ids, seen_urls = set(), {}
    for j in jobs:
        tag = f"job {j.get('id')!r}"
        for key in ("id", "employer", "title", "city", "county", "employer_type", "url", "first_seen", "last_seen", "status"):
            if not j.get(key):
                errors.append(f"{tag}: missing {key}")
        if j.get("id") in seen_ids:
            errors.append(f"{tag}: duplicate id")
        seen_ids.add(j.get("id"))
        if j.get("employer_type") not in EMPLOYER_TYPES:
            errors.append(f"{tag}: bad employer_type {j.get('employer_type')!r}")
        if j.get("fit_rank") not in (1, 2, 3):
            errors.append(f"{tag}: fit_rank must be 1, 2 or 3")
        if j.get("status") not in JOB_STATUSES:
            errors.append(f"{tag}: bad status {j.get('status')!r}")
        if j.get("confidence") not in CONFIDENCE:
            errors.append(f"{tag}: bad confidence {j.get('confidence')!r}")
        for key in ("deadline", "posted", "first_seen", "last_seen", "closed_on"):
            if key in j and not is_iso_date(j.get(key)):
                errors.append(f"{tag}: {key} is not an ISO date")
        if j.get("first_seen") and j.get("last_seen") and j["first_seen"] > j["last_seen"]:
            errors.append(f"{tag}: first_seen after last_seen")
        ok, reason = zone_check(j.get("city", ""), j.get("county", ""), bool(j.get("remote")))
        if not ok:
            errors.append(f"{tag}: {reason}")
        nurl = normalize_url(j.get("url", ""))
        if nurl in seen_urls:
            warnings.append(f"{tag}: same url as {seen_urls[nurl]!r}")
        seen_urls.setdefault(nurl, j.get("id"))
        for s in strings_in(j):
            if DASH_RE.search(s):
                errors.append(f"{tag}: contains an em or en dash: {s[:60]!r}")
                break

    programs = load_json(PROGRAMS_PATH, None)
    if not isinstance(programs, list):
        errors.append("data/programs.json missing or not a list")
        programs = []
    pids = set()
    for p in programs:
        tag = f"program {p.get('id')!r}"
        for key in ("id", "name", "organization", "url", "status_for_noel"):
            if not p.get(key):
                errors.append(f"{tag}: missing {key}")
        if p.get("id") in pids:
            errors.append(f"{tag}: duplicate id")
        pids.add(p.get("id"))
        if p.get("status_for_noel") not in PROGRAM_STATUSES:
            errors.append(f"{tag}: bad status_for_noel {p.get('status_for_noel')!r}")
        if not is_iso_date(p.get("deadline")):
            errors.append(f"{tag}: deadline is not an ISO date")
        for s in strings_in(p):
            if DASH_RE.search(s):
                errors.append(f"{tag}: contains an em or en dash: {s[:60]!r}")
                break

    sources = load_json(SOURCES_PATH, None)
    if not isinstance(sources, list):
        errors.append("data/sources.json missing or not a list")
        sources = []
    sids = set()
    for s in sources:
        tag = f"source {s.get('id')!r}"
        for key in ("id", "name", "url", "check_frequency"):
            if not s.get(key):
                errors.append(f"{tag}: missing {key}")
        if s.get("id") in sids:
            errors.append(f"{tag}: duplicate id")
        sids.add(s.get("id"))
        if s.get("check_frequency") not in ("every run", "weekly"):
            errors.append(f"{tag}: check_frequency must be 'every run' or 'weekly'")
        if not str(s.get("url", "")).lower().startswith("http"):
            errors.append(f"{tag}: url must start with http")

    runs = load_json(RUNS_PATH, [])
    if not isinstance(runs, list):
        errors.append("data/runs.json must be a list")

    config = load_json(CONFIG_PATH, {})
    if not config.get("pages_url"):
        warnings.append("data/config.json has no pages_url (dashboard links will be relative)")

    summary = {
        "ok": not errors,
        "jobs": len(jobs),
        "open_jobs": sum(1 for j in jobs if j.get("status") == "open"),
        "programs": len(programs),
        "sources": len(sources),
        "runs": len(runs),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
