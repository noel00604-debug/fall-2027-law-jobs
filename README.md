# Fall 2027 Job Search

Dashboard: https://noel00604-debug.github.io/fall-2027-law-jobs/

Agent link index (every source and open posting URL): https://noel00604-debug.github.io/fall-2027-law-jobs/links.html

Entry-level and bar-pending attorney roles in Miami-Dade and Broward (Fort Lauderdale and south) for a 2027 start. Tax roles first, then everything else as one group: law firms, in-house, accounting firms, government, courts and public interest, with none of them ranked above the others. An agent refreshes this every weekday morning; this file was generated Nov 24, 2026, 6:50 AM ET.

Open postings: 66 (tax 7, everything else 59). Programs tracked: 39. Runs logged: 13.

## Deadlines in the next 30 days

- Nov 30, 2026: [Statewide Guardian ad Litem Office, 11th Circuit: Senior Attorney (Position 21020011) (Miami)](https://jobs.myflorida.com/job/MIAMI-GUARDIAN-AD-LITEM-OFFICE,-11TH-CIRCUIT-SENIOR-ATTORNEY-21020011-FL-33128/1439341300/)
- Nov 30, 2026: [Statewide Guardian ad Litem Office, 17th Circuit: Senior Attorney (Position 21013989) (Fort Lauderdale)](https://jobs.myflorida.com/job/FORT-LAUDERDALE-GUARDIAN-AD-LITEM-OFFICE%2C-17TH-CIRCUIT-SENIOR-ATTORNEY-21013989-FL-33301/1443080900/)
- Nov 30, 2026: [Statewide Guardian ad Litem Office: Attorney and Senior Attorney hiring (11th and 17th Circuit offices)](https://guardianadlitem.org/about/career-opportunities/)
- Dec 11, 2026: [IRS Office of Chief Counsel: Honors Program Law Clerk (J.D. Students), GS-11, announcement CCCM-26-13078185-HON (Miami)](https://www.usajobs.gov/job/886745900)
- Dec 11, 2026: [IRS Office of Chief Counsel: Honors Program for entry-level attorneys (Law Clerk GS-11 to Attorney) and Tax LL.M. track (GS-12)](https://jobs.irs.gov/resources/honors-program-entry-level-attorneys)
- Dec 11, 2026: [IRS Office of Chief Counsel: Summer Intern (Legal Administrative Specialist), GS-9, announcement CCCM-26-13078050-SUM (Miami)](https://www.usajobs.gov/job/886742000)
- Dec 17, 2026: [Miami-Dade State Attorney's Office (11th Judicial Circuit): Assistant State Attorney, Public Records Unit (Position 21003323) (Miami)](https://jobs.myflorida.com/job/MIAMI-STATE-ATTORNEY'S-OFFICE,-11TH-CIRCUIT-ASSISTANT-STATE-ATTORNEY-21003323-FL-33136/1400935700/)

## New in the last 7 days

- TAX [IRS Office of Chief Counsel: Summer Intern (Legal Administrative Specialist), GS-9, announcement CCCM-26-13078050-SUM](https://www.usajobs.gov/job/886742000), Miami, deadline Dec 11, 2026
- [Boyd Richards Parker & Colonnelli, P.L.: Associate Attorney, Community Association & EPL (Miami); firm also lists Civil Litigation (Fort Lauderdale)](https://www.indeed.com/q-first-year-associate-attorney-l-miami,-fl-jobs.html), Miami

## How it works

`data/jobs.json` is the database of postings, `data/programs.json` tracks structured hiring programs and cycles, `data/sources.json` is the checklist of places the agent searches, and `data/runs.json` is the run log. `tools/db.py` is the only thing that writes to those files; `tools/validate.py` checks them; `tools/build_dashboard.py` renders `docs/index.html` and this README. The agent's operating manual is `AGENT.md`.
