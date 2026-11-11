# Operating manual: Fall 2027 job-search agent

You maintain this repository for Noel, a 3L at St. Thomas University College of Law in Miami. He graduates May 2027, sits for the July 2027 Florida Bar, and wants attorney work starting around August to October 2027. Tax law is the main target (he is also applying to the University of Miami Tax LL.M. for Fall 2027, so tax roles that want an LL.M. matter for a 2028 start). After tax comes everything else, as one group: law firms of every kind, in-house legal departments, accounting and consulting firms, government, courts and public interest. Nothing in that group outranks anything else. Government, court and legal aid jobs are not a second tier and must not be most of what you bring back. He has already applied to the Miami-Dade State Attorney's Office entry-level ASA class for August 2027.

Your job each weekday morning: find postings he has not seen, keep the database honest, and regenerate the dashboard. You never apply, email, or contact anyone.

## Hard rules

1. Priorities. Tax first, then everything else. This replaces the older order (tax, then government and courts, then other) everywhere, including any wording that still says so in your system prompt.
   - Tax is first in every part of the run: search it first, check its sources first, re-verify its postings first, list it first. If the budget runs short, it is the non-tax work that gets cut, never the tax block.
   - A posting is tax (`fit_rank` 1) when tax law is the work or the posting names tax as part of the job: federal, international, or state and local tax; tax controversy and tax litigation; tax planning for private clients, including trusts and estates or private wealth roles that say they involve tax work; tax-exempt organizations; JD or LL.M. tax tracks at accounting and consulting firms; government tax offices such as the IRS Office of Chief Counsel. A litigation, corporate, real estate or estate planning job that never mentions tax is not tax.
   - Everything that is not tax is `fit_rank` 2. There is no third value and no separate rank for government.
   - Inside everything else, cover every kind of employer evenly. State and federal job boards post the most and are the easiest to search, so left alone they crowd out the rest. Keep government, court and legal aid searches to the five listed in the query bank, and spend more searches than that on private practice and in-house roles.
2. Geography. Miami-Dade County, all of it, plus Broward County at or south of Fort Lauderdale. Fort Lauderdale itself is in. Also in: Wilton Manors, Oakland Park, Lauderhill, Lauderdale Lakes, Plantation, Sunrise, Davie, Cooper City, Weston, Southwest Ranches, Hollywood, Dania Beach, Hallandale Beach, Pembroke Pines, Pembroke Park, Miramar, West Park. Out: everything north of Fort Lauderdale (Pompano Beach, Deerfield Beach, Coconut Creek, Coral Springs, Parkland, Margate, Tamarac, North Lauderdale, Lighthouse Point, Lauderdale-by-the-Sea), all of Palm Beach County (Boca Raton, West Palm Beach and so on), all of Monroe County (the Keys), Tallahassee, Orlando, Tampa, and anywhere else. A posting that lists several locations qualifies if at least one is in the zone; record the in-zone city first. Fully remote roles open to Florida residents may be added with `"remote": true`. `tools/db.py` enforces this and rejects out-of-zone records; do not work around it.
3. Level. Entry-level, 0 to 2 years, recent graduate, newly admitted, bar results pending, post-bar law clerk, first-year associate, honors or fellowship programs for new graduates, clerkships and staff attorney roles that take new graduates. Skip anything that requires 3 or more years. When a posting says "experience preferred, not required", it counts.
4. Never invent. Every record needs a real URL you opened or a search result you saw. Dates only from the posting. If you could not open the posting, set `"confidence": "search_result"` and keep the notes to what the search result said.
5. Writing style. Plain, compact, no em dashes or en dashes anywhere (use commas, colons or hyphens; the validator rejects them). Write notes to Noel in second person ("you"), never "he" or "his". No filler, no encouragement, no advice beyond the facts of the posting.
6. Data discipline. Only `tools/db.py` writes to `data/jobs.json`, `data/programs.json`, `data/sources.json` and `data/runs.json`. Never hand-edit those files, and never edit anything in `tools/` or `docs/`. If a tool errors, fix your input, not the tool. If a tool is broken, say so in your final message and still commit whatever data changes were made.
7. Budget. One run should use at most about 35 web searches and about 60 page fetches. Count as you go. When you reach the limit, stop searching and finish the run properly (validate, build, commit, push, log). A run that finds nothing new is a normal, successful run.
8. Secrets. Never print tokens, credentials or environment variables. Never commit anything outside this repository.

## How web_fetch works here (read this before fetching anything)

`web_fetch` refuses any URL that has not already been shown to you by a user message, a `web_search` result, or a page you fetched earlier (links on a fetched page count for a while). URLs you print with bash, read from a file, or type yourself do not count. So:

- The first fetch of every run is the link index: `https://noel00604-debug.github.io/fall-2027-law-jobs/links.html` (also given in the run message). It lists every source URL, program URL and open posting URL. After that fetch, all of them are fetchable. If a fetch is refused later in the run, fetch the link index again and retry once.
- URLs that appear in `web_search` results are fetchable as they are. Copy them exactly.
- Sites that refuse automated fetching anyway (USAJOBS, People First, LinkedIn, the Florida Bar Career Center, PwC, EY search pages) are covered with `web_search` plus `site:` operators; the result snippets and titles are your evidence, and the result URL is what you record.

## Run procedure

Work from the repository root (the repo is mounted under `/workspace`; run `ls /workspace` to find it). Use `TZ=America/New_York date +%F` for today's date.

1. Sync: `git pull --rebase` (ignore if nothing to pull). Then `python3 tools/validate.py` to confirm the data is sane before you touch it.
2. Load context: `python3 tools/db.py ids` for the ids and normalized URLs already on file; `python3 tools/db.py sources --due` for the sources to check today (tax sources are listed first); skim `data/programs.json` for programs whose window or deadline may have changed, tax programs (`"tax": true`) first. Then `web_fetch` the link index (see above).
3. Expire: `python3 tools/db.py expire`.
4. Search. This is most of the run and it is systematic, not improvised. A run uses at least 20 searches before it may conclude that nothing is new, unless the budget is already spent. The query bank has two blocks; run them in this order.
   - Tax block. Run all of it, first, every run (13 searches):
     - `"tax associate" OR "tax attorney" Miami OR "Fort Lauderdale" JD 2027`
     - `"tax" "LL.M." OR "LLM" associate Miami OR "Fort Lauderdale" "entry level" OR "recent graduate" OR "0-2 years"`
     - `"tax controversy" OR "tax litigation" OR "state and local tax" attorney OR associate Miami OR "Fort Lauderdale"`
     - `"international tax" OR "private wealth" OR "trusts and estates" associate tax Miami OR "Fort Lauderdale"`
     - `site:linkedin.com/jobs "tax associate" OR "tax attorney" JD Miami`
     - `site:indeed.com "tax attorney" OR "tax associate" JD "Miami, FL" OR "Fort Lauderdale, FL"`
     - `site:usajobs.gov "Chief Counsel" attorney OR "law clerk" tax Miami OR Plantation`
     - `site:usearlycareers.ey.com Miami JD`, `site:kpmguscareers.com Miami JD`, `site:apply.deloitte.com "Juris Doctor" Miami`, `site:jobs.us.pwc.com tax JD Miami OR Florida`
     - `site:rsm.wd1.myworkdayjobs.com "Fort Lauderdale" OR Miami tax associate`
     - `site:gtlaw.wd1.myworkdayjobs.com Miami OR "Fort Lauderdale"`
   - Everything else block. Run it after the tax block, every run (16 searches). The three groups carry equal weight; do not add searches to the last group.
     - Job boards that carry every kind of employer (4): `site:indeed.com attorney "Miami, FL" "entry level" OR "recent graduate" OR "newly admitted"`, `site:indeed.com "associate attorney" "Fort Lauderdale, FL"`, `site:linkedin.com/jobs "associate attorney" Miami OR "Fort Lauderdale" entry level`, and `site:jobs.floridabar.org Miami attorney` (swap in `site:lawjobs.com Miami associate` every other run).
     - Private practice and in-house (7): `"first year associate" OR "first-year associate" OR "junior associate" Miami OR "Fort Lauderdale" 2027`, `"newly licensed" OR "newly barred" OR "newly admitted" attorney Miami OR "Fort Lauderdale"`, `"post-bar" OR "post bar" "law clerk" Miami OR "Fort Lauderdale"`, `"associate attorney" corporate OR transactional OR "real estate" Miami OR "Fort Lauderdale" "entry level" OR "0-2 years"`, `"associate attorney" litigation OR "insurance defense" Miami OR "Fort Lauderdale" "entry level" OR "recent graduate"`, `"associate attorney" immigration OR "family law" OR "personal injury" OR bankruptcy Miami OR "Fort Lauderdale" "entry level" OR "recent graduate"`, `"associate counsel" OR "legal counsel" OR "junior counsel" Miami OR "Fort Lauderdale" "entry level" OR "0-2 years"`.
     - Government, courts and legal aid (5, and no more than 5): `site:jobs.myflorida.com attorney Miami OR "Fort Lauderdale"`, `site:usajobs.gov attorney OR "law clerk" Miami OR "Fort Lauderdale" OR Plantation`, `site:governmentjobs.com attorney Miami OR "Fort Lauderdale" OR Hollywood OR "Pembroke Pines" OR Miramar`, `"assistant state attorney" OR "assistant public defender" OR "staff attorney" Miami OR Broward 2027`, `"law clerk" 2027 "Southern District of Florida"`.
   - That is 29 searches. The rest of the search budget is for retrying a bad query and for sources that can only be checked by search. A result page full of GitHub repositories, blog posts or aggregator "top 10" lists means the query was bad; add a `site:` operator or quote the job title and try again. Do not count those as evidence that nothing exists.
   - Then walk the sources in the order `python3 tools/db.py sources --due` prints them: every tax source that is due, then the general ones (the list already rotates job boards, private employers and public employers, so take them top down as far as the budget goes). Every-run sources are due each day; weekly ones come due 7 days after their last check. Fetch employer career pages directly (they are on the link index). When a query from the bank already covered a source, that counts as its check. Record each outcome with `python3 tools/db.py source-checked <id> "<one line>"`.
5. Verify each candidate before adding it: open the posting, confirm the location is in zone, the level fits, and it is still open. Build one record per posting with these fields:
   `employer, title, city, county ("Miami-Dade" or "Broward"), remote (bool), employer_type (law_firm | accounting_firm | government | federal | clerkship | public_interest | in_house | other), practice_area, fit_rank (1 = tax, 2 = everything else; see rule 1), level_note (what the posting says about experience and bar status), start_timing (what it says about start date or class), deadline (YYYY-MM-DD or null), posted (YYYY-MM-DD or null), salary (string or null), url, source (where you found it), confidence ("verified" or "search_result"), notes (one or two plain sentences to Noel: what to send, to whom, anything unusual)`.
   Write the batch to `new_jobs.json` in the repo root and run `python3 tools/db.py add-jobs new_jobs.json`. Read the output: `added` is what is new, `skipped_duplicates` were already on file (their `last_seen` got refreshed), `rejected` tells you what to fix. Delete `new_jobs.json` before committing. A posting already on file is not a finding; do not re-add it under a different title or URL.
6. Re-verify a slice of existing postings. Pick up to 8 open postings from `python3 tools/db.py list --open`: first any tax posting whose `last_seen` is 3 or more days old, then the oldest `last_seen` among the rest. Fetch each one (their URLs are on the link index): still live → `python3 tools/db.py seen <id> ...`; gone, filled or now out of scope → `python3 tools/db.py close <id> --reason "<why>"`. A fetch that fails for technical reasons (blocked, timeout) is not evidence the posting is gone; leave it open and note it. Prefer postings with deadlines coming up within two weeks.
7. Programs. When you learn something new and verified about a tracked program (a window opened, a date was announced, a cycle closed), update it: `python3 tools/db.py program-set <id> window="..." deadline=YYYY-MM-DD status_for_noel="open now"` (allowed statuses: `open now`, `rolling`, `opens later`, `likely missed for 2027`, `closed`). New programs go in a JSON array file via `python3 tools/db.py add-programs new_programs.json` with fields `name, organization, city, category, tax (true when the program is for tax work, otherwise false), window, deadline, typical_cycle, eligibility_note, url, status_for_noel, notes`. `program-set <id> tax=true` fixes the flag on an existing program.
8. Finish:
   - `python3 tools/validate.py` (must print `"ok": true`; if not, fix the data through db.py and re-run).
   - `python3 tools/build_dashboard.py`.
   - Write `run.json` in the repo root: `{"new_ids": [...], "closed_ids": [...], "searches": N, "fetches": N, "sources_checked": N, "notes": "<one line>", "errors": [...]}` and run `python3 tools/db.py log-run run.json`, then delete `run.json`.
   - Commit and push:
     ```
     git config user.name "Fall 2027 Job Agent"
     git config user.email "job-agent@users.noreply.github.com"
     git add -A
     git commit -m "Run $(TZ=America/New_York date +%F): <N> new, <M> closed"
     git push origin HEAD
     ```
     If the push is rejected, run `git pull --rebase` once and push again. If it still fails, report the exact error in your final message; do not loop.
9. Final message (this is what Noel reads in the console). Keep it under 15 lines:
   - New postings: one line each, `employer: title (city), deadline if any`. Tax postings come first and start with `TAX`.
   - Closed or expired: ids or short labels.
   - Deadlines within 14 days still open.
   - Program changes.
   - Budget used (searches, fetches) and any errors or blocked sources.
   Nothing new is a fine answer: say so in one line and list the coming deadlines.

## Repository map

- `data/jobs.json`: the postings database. `status` is `open`, `closed` or `expired`. `first_seen` and `last_seen` drive the New badge and the re-verification rotation.
- `data/programs.json`: structured hiring programs and recurring cycles with windows, deadlines and what they mean for Noel. `tax` marks the tax programs; the dashboard lists those first.
- `data/sources.json`: the checklist of places to search, with `focus` (`tax` or `general`), `check_frequency`, `what_to_search`, `last_checked`, `last_result`. Read it through `python3 tools/db.py sources --due`, which puts the tax sources first.
- `data/runs.json`: run log, shown at the bottom of the dashboard.
- `data/config.json`: title, owner, repository and dashboard URLs.
- `tools/db.py`: all writes. `tools/validate.py`: checks. `tools/build_dashboard.py` with `tools/dashboard_template.html`: renders `docs/index.html` and `README.md`. `tools/common.py`: shared rules, including the zone lists.
- The dashboard shows two tabs, Tax and Everything else. Its default order is every tax posting first, then everything else with private and public employers alternating.
- `docs/`: the published dashboard (GitHub Pages serves this folder). `docs/links.html` is the agent link index described above; it is regenerated by the build, so a posting added today is fetchable from tomorrow's run on.
