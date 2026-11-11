#!/usr/bin/env python3
"""Command-line database for the job-search repo. All writes to data/*.json go through here.

Usage:
  python3 tools/db.py add-jobs NEW.json            # merge new postings (array of records)
  python3 tools/db.py seen ID [ID ...]              # mark postings as still live today
  python3 tools/db.py close ID [ID ...] --reason "posting removed"
  python3 tools/db.py expire                        # mark open postings whose deadline has passed
  python3 tools/db.py list [--open] [--fit 1]       # print a compact table of postings (fit 1 = tax, 2 = everything else)
  python3 tools/db.py add-programs NEW.json         # add structured programs (array)
  python3 tools/db.py program-set ID key=value ...  # update fields on one program
  python3 tools/db.py sources [--due] [--focus tax] # list the source checklist, tax sources first
  python3 tools/db.py source-checked ID "result"    # record that a source was checked today
  python3 tools/db.py log-run RUN.json              # append a run summary
  python3 tools/db.py ids                           # print every job id and normalized url (for dedupe)

Every command prints a JSON summary to stdout. Non-zero exit means nothing was written.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from common import (
    CONFIDENCE,
    EMPLOYER_TYPES,
    FIT_OTHER,
    FIT_RANKS,
    JOBS_PATH,
    PROGRAMS_PATH,
    PROGRAM_STATUSES,
    RUNS_PATH,
    SOURCE_FOCUS,
    SOURCES_PATH,
    clean_record,
    is_iso_date,
    job_id_for,
    load_json,
    norm_key,
    normalize_fit,
    normalize_url,
    now_iso,
    parse_bool,
    save_json,
    slugify,
    today,
    zone_check,
)

JOB_REQUIRED = ("employer", "title", "city", "county", "employer_type", "url")
JOB_FIELDS = (
    "id", "employer", "title", "city", "county", "remote", "employer_type", "practice_area",
    "fit_rank", "level_note", "start_timing", "deadline", "posted", "salary", "url", "source",
    "confidence", "notes", "first_seen", "last_seen", "status", "closed_on", "closed_reason",
)


def _titles_match(a: str, b: str) -> bool:
    ta, tb = set(norm_key(a).split()), set(norm_key(b).split())
    if not ta or not tb:
        return False
    if ta <= tb or tb <= ta:
        return True
    return len(ta & tb) / len(ta | tb) >= 0.5


def _fail(msg: str, code: int = 2):
    print(json.dumps({"ok": False, "error": msg}, indent=2))
    sys.exit(code)


def _validate_new_job(rec: dict, idx: int):
    problems = []
    for key in JOB_REQUIRED:
        if not rec.get(key):
            problems.append(f"missing {key}")
    if rec.get("employer_type") not in EMPLOYER_TYPES:
        problems.append(f"employer_type must be one of {EMPLOYER_TYPES}")
    if isinstance(rec.get("fit_rank"), bool) or rec.get("fit_rank") not in FIT_RANKS:
        problems.append("fit_rank must be 1 (tax) or 2 (everything else)")
    if rec.get("confidence") not in CONFIDENCE:
        problems.append(f"confidence must be one of {CONFIDENCE}")
    for key in ("deadline", "posted"):
        if not is_iso_date(rec.get(key)):
            problems.append(f"{key} must be an ISO date (YYYY-MM-DD) or null")
    if rec.get("url") and not str(rec["url"]).lower().startswith("http"):
        problems.append("url must start with http")
    ok, reason = zone_check(rec.get("city", ""), rec.get("county", ""), bool(rec.get("remote")))
    if not ok:
        problems.append("zone: " + reason)
    return problems


def cmd_add_jobs(args):
    new_records = load_json(args.file, None)
    if not isinstance(new_records, list):
        _fail(f"{args.file} must contain a JSON array of job records")
    jobs = load_json(JOBS_PATH, [])
    by_url = {normalize_url(j["url"]): j for j in jobs if j.get("url")}
    by_key = {(norm_key(j["employer"]), norm_key(j["title"]), norm_key(j["city"].split("(")[0])): j for j in jobs}
    ids = {j["id"] for j in jobs}
    added, skipped, rejected = [], [], []
    day = today()
    for idx, raw in enumerate(new_records):
        rec = clean_record(dict(raw))
        rec.setdefault("remote", False)
        rec.setdefault("confidence", "search_result")
        rec.setdefault("fit_rank", FIT_OTHER)
        # Two tiers only. A 3 from the old three-tier scheme means "everything else".
        rec["fit_rank"] = normalize_fit(rec["fit_rank"])
        for key in ("practice_area", "level_note", "start_timing", "salary", "source", "notes"):
            rec.setdefault(key, None)
        for key in ("deadline", "posted"):
            if rec.get(key) in ("", "null", "None"):
                rec[key] = None
        for key in ("start_timing", "salary", "practice_area", "level_note", "source", "notes"):
            if isinstance(rec.get(key), str) and rec[key].strip().lower() in ("", "not stated", "unknown", "n/a", "none", "null", "not specified"):
                rec[key] = None
        problems = _validate_new_job(rec, idx)
        if problems:
            rejected.append({"index": idx, "employer": rec.get("employer"), "title": rec.get("title"), "problems": problems})
            continue
        nurl = normalize_url(rec["url"])
        key = (norm_key(rec["employer"]), norm_key(rec["title"]), norm_key(rec["city"].split("(")[0]))
        dup = by_key.get(key)
        if not dup and nurl in by_url:
            # Same URL counts as the same posting only when the titles clearly match; many
            # employers list several openings on one careers page.
            cand = by_url[nurl]
            if _titles_match(cand.get("title", ""), rec["title"]):
                dup = cand
        if dup:
            dup["last_seen"] = day
            if dup.get("status") == "closed" and args.reopen:
                dup["status"] = "open"
                dup.pop("closed_on", None)
                dup.pop("closed_reason", None)
            # Fill in blanks the earlier record did not have.
            for fld in ("deadline", "posted", "salary", "level_note", "start_timing", "practice_area"):
                if not dup.get(fld) and rec.get(fld):
                    dup[fld] = rec[fld]
            skipped.append({"index": idx, "duplicate_of": dup["id"], "employer": rec["employer"], "title": rec["title"]})
            continue
        jid = job_id_for(rec)
        base, n = jid, 2
        while jid in ids:
            jid = f"{base}-{n}"
            n += 1
        record = {k: rec.get(k) for k in JOB_FIELDS}
        record.update({"id": jid, "first_seen": day, "last_seen": day, "status": "open"})
        record.pop("closed_on", None)
        record.pop("closed_reason", None)
        jobs.append(record)
        ids.add(jid)
        by_url[nurl] = record
        by_key[key] = record
        added.append(jid)
    if added or skipped:
        save_json(JOBS_PATH, jobs)
    print(json.dumps({"ok": True, "added": added, "skipped_duplicates": skipped, "rejected": rejected,
                      "total_jobs": len(jobs)}, indent=2, ensure_ascii=False))
    if rejected and not added and not skipped:
        sys.exit(1)


def cmd_seen(args):
    jobs = load_json(JOBS_PATH, [])
    day = today()
    hit = []
    for j in jobs:
        if j["id"] in args.ids:
            j["last_seen"] = day
            hit.append(j["id"])
    missing = sorted(set(args.ids) - set(hit))
    if hit:
        save_json(JOBS_PATH, jobs)
    print(json.dumps({"ok": True, "updated": hit, "unknown_ids": missing}, indent=2))


def cmd_close(args):
    jobs = load_json(JOBS_PATH, [])
    day = today()
    hit = []
    for j in jobs:
        if j["id"] in args.ids and j.get("status") == "open":
            j["status"] = "closed"
            j["closed_on"] = day
            j["closed_reason"] = args.reason
            hit.append(j["id"])
    if hit:
        save_json(JOBS_PATH, jobs)
    print(json.dumps({"ok": True, "closed": hit, "not_open_or_unknown": sorted(set(args.ids) - set(hit))}, indent=2))


def cmd_expire(args):
    jobs = load_json(JOBS_PATH, [])
    day = today()
    hit = []
    for j in jobs:
        if j.get("status") == "open" and j.get("deadline") and j["deadline"] < day:
            j["status"] = "expired"
            j["closed_on"] = day
            j["closed_reason"] = "application deadline passed"
            hit.append(j["id"])
    if hit:
        save_json(JOBS_PATH, jobs)
    print(json.dumps({"ok": True, "expired": hit}, indent=2))


def cmd_list(args):
    jobs = load_json(JOBS_PATH, [])
    rows = []
    for j in jobs:
        if args.open and j.get("status") != "open":
            continue
        if args.fit and j.get("fit_rank") != args.fit:
            continue
        rows.append(j)
    rows.sort(key=lambda j: (j.get("fit_rank", FIT_OTHER), j.get("deadline") or "9999", j.get("employer", "")))
    for j in rows:
        print(f"[{j.get('fit_rank')}] {j.get('status'):7} {j['id']:70} dl={j.get('deadline')} seen={j.get('last_seen')} {j.get('url')}")
    print(json.dumps({"ok": True, "count": len(rows)}))


def cmd_ids(args):
    jobs = load_json(JOBS_PATH, [])
    print(json.dumps([{"id": j["id"], "url": normalize_url(j.get("url", "")), "status": j.get("status")} for j in jobs],
                     indent=0, ensure_ascii=False))


def cmd_add_programs(args):
    new = load_json(args.file, None)
    if not isinstance(new, list):
        _fail(f"{args.file} must contain a JSON array of program records")
    programs = load_json(PROGRAMS_PATH, [])
    ids = {p["id"] for p in programs}
    added, rejected = [], []
    for idx, raw in enumerate(new):
        rec = clean_record(dict(raw))
        problems = []
        for key in ("name", "organization", "url", "status_for_noel"):
            if not rec.get(key):
                problems.append(f"missing {key}")
        if rec.get("status_for_noel") not in PROGRAM_STATUSES:
            problems.append(f"status_for_noel must be one of {PROGRAM_STATUSES}")
        if not is_iso_date(rec.get("deadline")):
            problems.append("deadline must be ISO date or null")
        if problems:
            rejected.append({"index": idx, "name": rec.get("name"), "problems": problems})
            continue
        pid = rec.get("id") or (slugify(rec["organization"], 36) + "-" + slugify(rec["name"], 40))
        base, n = pid, 2
        while pid in ids:
            pid = f"{base}-{n}"
            n += 1
        rec["id"] = pid
        rec["tax"] = bool(parse_bool(rec.get("tax")))
        rec.setdefault("category", "other")
        rec.setdefault("city", None)
        rec.setdefault("window", None)
        rec.setdefault("typical_cycle", None)
        rec.setdefault("eligibility_note", None)
        rec.setdefault("notes", None)
        rec["last_verified"] = today()
        programs.append(rec)
        ids.add(pid)
        added.append(pid)
    if added:
        save_json(PROGRAMS_PATH, programs)
    print(json.dumps({"ok": True, "added": added, "rejected": rejected}, indent=2, ensure_ascii=False))


def cmd_program_set(args):
    programs = load_json(PROGRAMS_PATH, [])
    target = next((p for p in programs if p["id"] == args.id), None)
    if not target:
        _fail(f"no program with id {args.id}")
    changes = {}
    for pair in args.pairs:
        if "=" not in pair:
            _fail(f"expected key=value, got {pair!r}")
        key, value = pair.split("=", 1)
        if key == "id":
            _fail("id cannot be changed")
        if value in ("null", "None", ""):
            value = None
        if key == "status_for_noel" and value not in PROGRAM_STATUSES:
            _fail(f"status_for_noel must be one of {PROGRAM_STATUSES}")
        if key == "deadline" and not is_iso_date(value):
            _fail("deadline must be ISO date or null")
        if key == "tax":
            flag = parse_bool(value)
            if flag is None:
                _fail("tax must be true or false")
            target[key] = flag
            changes[key] = flag
            continue
        target[key] = clean_record({"v": value})["v"]
        changes[key] = target[key]
    target["last_verified"] = today()
    save_json(PROGRAMS_PATH, programs)
    print(json.dumps({"ok": True, "id": args.id, "changes": changes}, indent=2, ensure_ascii=False))


def _source_due(src: dict, day: str) -> bool:
    """Every-run sources are always due. Weekly ones come due when they have never been checked
    or when the last check is 7 or more days old."""
    if src.get("check_frequency") == "every run":
        return True
    last = src.get("last_checked")
    if not last or not is_iso_date(last):
        return True
    return (dt.date.fromisoformat(day) - dt.date.fromisoformat(last)).days >= 7


def _oldest_first(rows):
    return sorted(rows, key=lambda r: (r[2].get("last_checked") or "", r[2].get("id", "")))


def _mix_by_category(rows):
    """Rotate through the categories (job boards, private employers, public employers) so a walk
    down the list covers every kind of employer instead of finishing one kind first."""
    groups = {}
    for row in _oldest_first(rows):
        groups.setdefault(row[2].get("category") or "other", []).append(row)
    order = [c for c in ("aggregator", "private_sector", "public_sector") if c in groups]
    order += sorted(c for c in groups if c not in order)
    mixed, i = [], 0
    while any(i < len(groups[c]) for c in order):
        for c in order:
            if i < len(groups[c]):
                mixed.append(groups[c][i])
        i += 1
    return mixed


def cmd_sources(args):
    sources = load_json(SOURCES_PATH, [])
    day = today()
    rows = []
    for s in sources:
        focus = s.get("focus") or "general"
        if args.focus and focus != args.focus:
            continue
        due = _source_due(s, day)
        if args.due and not due:
            continue
        rows.append((focus, due, s))
    # Order: tax sources that are due, then general sources that are due (mixed by kind of
    # employer), then whatever is not due yet. Inside each block the longest unchecked comes first.
    tax_due = _oldest_first([r for r in rows if r[0] == "tax" and r[1]])
    general_due = _mix_by_category([r for r in rows if r[0] != "tax" and r[1]])
    not_due = _oldest_first([r for r in rows if not r[1]])
    not_due.sort(key=lambda r: 0 if r[0] == "tax" else 1)
    rows = tax_due + general_due + not_due
    for focus, due, s in rows:
        print(f"[{focus:7}] {'due' if due else 'ok ':3} {s.get('check_frequency', ''):9} last={s.get('last_checked')} {s.get('id')}")
        print(f"          {s.get('name')} | {s.get('url')}")
        if s.get("what_to_search"):
            print(f"          look for: {s['what_to_search']}")
    print(json.dumps({"ok": True, "count": len(rows), "tax": sum(1 for r in rows if r[0] == "tax"),
                      "general": sum(1 for r in rows if r[0] != "tax"), "due": sum(1 for r in rows if r[1])}))


def cmd_source_checked(args):
    sources = load_json(SOURCES_PATH, [])
    target = next((s for s in sources if s["id"] == args.id), None)
    if not target:
        _fail(f"no source with id {args.id}")
    target["last_checked"] = today()
    target["last_result"] = clean_record({"v": args.result})["v"]
    save_json(SOURCES_PATH, sources)
    print(json.dumps({"ok": True, "id": args.id, "last_checked": target["last_checked"]}, indent=2))


def cmd_log_run(args):
    entry = load_json(args.file, None)
    if not isinstance(entry, dict):
        _fail(f"{args.file} must contain a JSON object")
    runs = load_json(RUNS_PATH, [])
    entry = clean_record(entry)
    entry.setdefault("date", today())
    entry.setdefault("logged_at", now_iso())
    runs.append(entry)
    save_json(RUNS_PATH, runs[-200:])
    print(json.dumps({"ok": True, "runs_logged": len(runs)}, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add-jobs"); p.add_argument("file"); p.add_argument("--reopen", action="store_true"); p.set_defaults(fn=cmd_add_jobs)
    p = sub.add_parser("seen"); p.add_argument("ids", nargs="+"); p.set_defaults(fn=cmd_seen)
    p = sub.add_parser("close"); p.add_argument("ids", nargs="+"); p.add_argument("--reason", required=True); p.set_defaults(fn=cmd_close)
    p = sub.add_parser("expire"); p.set_defaults(fn=cmd_expire)
    p = sub.add_parser("list"); p.add_argument("--open", action="store_true"); p.add_argument("--fit", type=int, choices=FIT_RANKS); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("ids"); p.set_defaults(fn=cmd_ids)
    p = sub.add_parser("add-programs"); p.add_argument("file"); p.set_defaults(fn=cmd_add_programs)
    p = sub.add_parser("program-set"); p.add_argument("id"); p.add_argument("pairs", nargs="+"); p.set_defaults(fn=cmd_program_set)
    p = sub.add_parser("sources"); p.add_argument("--due", action="store_true"); p.add_argument("--focus", choices=SOURCE_FOCUS); p.set_defaults(fn=cmd_sources)
    p = sub.add_parser("source-checked"); p.add_argument("id"); p.add_argument("result"); p.set_defaults(fn=cmd_source_checked)
    p = sub.add_parser("log-run"); p.add_argument("file"); p.set_defaults(fn=cmd_log_run)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
