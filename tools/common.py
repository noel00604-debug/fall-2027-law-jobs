"""Shared helpers for the Fall 2027 job-search agent repo.

Standard library only. Python 3.9+.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
DOCS_DIR = os.path.join(ROOT, "docs")

JOBS_PATH = os.path.join(DATA_DIR, "jobs.json")
PROGRAMS_PATH = os.path.join(DATA_DIR, "programs.json")
SOURCES_PATH = os.path.join(DATA_DIR, "sources.json")
RUNS_PATH = os.path.join(DATA_DIR, "runs.json")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

ALLOWED_COUNTIES = ("Miami-Dade", "Broward")

EMPLOYER_TYPES = (
    "law_firm",
    "accounting_firm",
    "government",
    "federal",
    "clerkship",
    "public_interest",
    "in_house",
    "other",
)

JOB_STATUSES = ("open", "closed", "expired")
CONFIDENCE = ("verified", "search_result")
PROGRAM_STATUSES = ("open now", "rolling", "opens later", "likely missed for 2027", "closed")

# Geography. Fort Lauderdale is the northern line. Everything in Miami-Dade is in.
IN_ZONE_CITIES = [
    # Miami-Dade
    "Miami", "Miami Beach", "Coral Gables", "Hialeah", "Doral", "Homestead", "Kendall",
    "Aventura", "North Miami", "North Miami Beach", "Miami Gardens", "Miami Lakes",
    "Cutler Bay", "Palmetto Bay", "Pinecrest", "South Miami", "Sweetwater", "Key Biscayne",
    "Sunny Isles", "Bal Harbour", "Surfside", "Opa-locka", "Hialeah Gardens", "Medley",
    "Florida City", "Coconut Grove", "Brickell", "Wynwood", "Little Havana", "Downtown Miami",
    # Broward, at or south of Fort Lauderdale
    "Fort Lauderdale", "Ft. Lauderdale", "Ft Lauderdale", "Wilton Manors", "Oakland Park",
    "Lauderhill", "Lauderdale Lakes", "Plantation", "Sunrise", "Davie", "Cooper City",
    "Weston", "Southwest Ranches", "Hollywood", "Dania Beach", "Dania", "Hallandale",
    "Pembroke Pines", "Pembroke Park", "Miramar", "West Park",
]

OUT_OF_ZONE_CITIES = [
    # Broward north of Fort Lauderdale
    "Pompano Beach", "Pompano", "Deerfield Beach", "Deerfield", "Coconut Creek", "Coral Springs",
    "Parkland", "Margate", "Tamarac", "North Lauderdale", "Lighthouse Point",
    "Lauderdale-by-the-Sea", "Lauderdale By The Sea", "Sea Ranch Lakes",
    # Palm Beach County and north
    "West Palm Beach", "Palm Beach", "Boca Raton", "Boca", "Delray Beach", "Boynton Beach",
    "Jupiter", "Juno Beach", "Wellington", "Lake Worth", "Palm Beach Gardens", "Stuart",
    "Fort Pierce", "Port St. Lucie", "Vero Beach", "Melbourne",
    # Monroe County
    "Key West", "Key Largo", "Marathon", "Islamorada", "Monroe County",
    # Rest of Florida and elsewhere
    "Tallahassee", "Orlando", "Tampa", "Jacksonville", "Naples", "Fort Myers", "Sarasota",
    "Gainesville", "Pensacola", "Daytona", "St. Petersburg", "Saint Petersburg", "Ocala",
    "Lakeland", "Clearwater", "Atlanta", "New York", "Washington", "Chicago", "Houston",
    "Dallas", "Los Angeles", "San Francisco", "Charlotte", "Boston", "Philadelphia",
]

DASH_RE = re.compile("[—–‒―]")


def today() -> str:
    """ISO date in America/New_York. The sandbox clock is UTC."""
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+

        return _dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:  # pragma: no cover
        return _dt.date.today().isoformat()


def now_iso() -> str:
    try:
        from zoneinfo import ZoneInfo

        return _dt.datetime.now(ZoneInfo("America/New_York")).replace(microsecond=0).isoformat()
    except Exception:  # pragma: no cover
        return _dt.datetime.now().replace(microsecond=0).isoformat()


def clean_text(value):
    """Remove em and en dashes (house style) and tidy whitespace. Leaves non-strings alone."""
    if not isinstance(value, str):
        return value
    s = unicodedata.normalize("NFC", value)
    s = s.replace("—", ", ").replace("―", ", ")  # em dash and horizontal bar
    s = s.replace("–", "-").replace("‒", "-")  # en dash and figure dash
    s = re.sub(r"\s*,\s*,\s*", ", ", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    return s.strip()


def clean_record(rec: dict) -> dict:
    out = {}
    for k, v in rec.items():
        if isinstance(v, str):
            out[k] = clean_text(v)
        elif isinstance(v, list):
            out[k] = [clean_text(x) if isinstance(x, str) else x for x in v]
        else:
            out[k] = v
    return out


def slugify(text: str, max_len: int = 48) -> str:
    s = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"&", " and ", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s or "x"


TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid",
    "ref", "refid", "src", "source", "trk", "trackingid", "from", "tk", "vjs", "sjdu",
    "position", "pageNum", "currentJobId", "originalSubdomain",
}


def normalize_url(url: str) -> str:
    """Lowercase host, drop tracking params and fragments, strip trailing slash."""
    if not url:
        return ""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return url.strip().lower()
    scheme = (parts.scheme or "https").lower()
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
             if k not in TRACKING_PARAMS and not k.lower().startswith("utm_")]
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, host, path, urlencode(sorted(query)), ""))


def norm_key(text: str) -> str:
    s = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"\b(the|llp|llc|pllc|p\.a\.|pa|inc|esq|office of|offices of|law offices?)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def zone_check(city: str, county: str, remote: bool = False):
    """Return (ok: bool, reason: str)."""
    county = (county or "").strip()
    if county not in ALLOWED_COUNTIES:
        return False, f"county must be one of {ALLOWED_COUNTIES}, got {county!r}"
    c = city or ""
    c_low = c.lower()
    hits_in = [name for name in IN_ZONE_CITIES if name.lower() in c_low]
    hits_out = [name for name in OUT_OF_ZONE_CITIES if name.lower() in c_low]
    if remote and ("remote" in c_low or hits_in):
        return True, "remote, Florida-eligible"
    if hits_in:
        return True, "in zone: " + ", ".join(sorted(set(hits_in), key=len, reverse=True)[:3])
    if hits_out:
        return False, "out of zone: " + ", ".join(sorted(set(hits_out))[:3])
    if county == "Broward" and ("broward" in c_low):
        return True, "Broward (county-level listing; confirm the office is Fort Lauderdale or south)"
    if county == "Miami-Dade" and ("miami-dade" in c_low or "dade" in c_low):
        return True, "Miami-Dade (county-level listing)"
    return False, f"city {city!r} not recognized as inside the zone"


def is_iso_date(value) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        _dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def job_id_for(rec: dict) -> str:
    city_first = re.split(r"[/,(]| or | and ", rec.get("city") or "")[0]
    return "-".join([
        slugify(rec.get("employer", ""), 40),
        slugify(rec.get("title", ""), 56),
        slugify(city_first, 18),
    ]).strip("-")
