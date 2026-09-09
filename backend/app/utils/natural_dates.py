"""Natural-language date parsing for voice input.

Resolves spoken/typed dates without demanding YYYY-MM-DD.
Two entry points:

  resolve_date_range(text)      -> (start, end) | (None, reason)
      "july to august"   -> Jul 1 .. Aug 31   (current year for past months, next year if the range is entirely in the future)
      "for july"         -> Jul 1 .. Jul 31
      "last month" / "this month" / "next month" / "last 3 months"

  resolve_single_date(text)     -> (date, None) | (None, reason)
      "today"/"tomorrow"/"next tuesday"/"15th of next month"/"aug 15"/"in 3 days"/"next week"
      Future-shifted: bare past dates roll to the next occurrence.

Range parsing is back-looking (reports): month names resolve to the current
year, so "july to august" said in September means this year's Jul–Aug.
"""
import calendar as _cal
import re
from datetime import date, timedelta

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
for _m, _n in list(MONTHS.items()):
    MONTHS[_m[:3]] = _n

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}
for _w, _n in list(WEEKDAYS.items()):
    WEEKDAYS[_w[:3]] = _n


def _safe_date(y, m, d):
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _month_end(y, mo):
    return date(y, mo, _cal.monthrange(y, mo)[1])


def _parse_single(s: str, today: date, future_bias: bool):
    """Parse one date phrase -> date | None. future_bias: past dates roll forward."""
    s = s.strip().lower().strip(".,?").strip()
    if not s:
        return None

    # strip a leading "the "
    s = re.sub(r"^the\s+", "", s)

    # ISO
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    if s == "today":
        return today
    if s == "tomorrow":
        return today + timedelta(days=1)
    if s == "yesterday":
        d = today - timedelta(days=1)
        return d

    # "in N days/weeks/months"
    m = re.fullmatch(r"in\s+(a|\d+)\s+(day|week|month)s?", s)
    if m:
        n = 1 if m.group(1) == "a" else int(m.group(1))
        unit = m.group(2)
        if unit == "day":
            return today + timedelta(days=n)
        if unit == "week":
            return today + timedelta(weeks=n)
        y, mo = today.year, today.month + n
        y += (mo - 1) // 12
        mo = (mo - 1) % 12 + 1
        day = min(today.day, _cal.monthrange(y, mo)[1])
        return date(y, mo, day)

    if s in ("next week",):
        return today + timedelta(weeks=1)
    if s in ("next month",):
        y, mo = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        day = min(today.day, _cal.monthrange(y, mo)[1])
        return date(y, mo, day)
    if s in ("end of month", "month end", "end of this month"):
        return _month_end(today.year, today.month)

    # "next <weekday>" or bare weekday
    for prefix in ("next ", "this ", "coming ", "on ", ""):
        if s.startswith(prefix) and len(s) > len(prefix):
            wd = WEEKDAYS.get(s[len(prefix):])
            if wd is not None:
                delta = (wd - today.weekday()) % 7
                if delta == 0:
                    delta = 7 if prefix in ("next ", "coming ") else 0
                return today + timedelta(days=delta)
        if prefix == "":
            break

    # "<N>th of next month" / "<N>th of this month"
    m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(next|this)\s+month", s)
    if m:
        y, mo = (today.year, today.month) if m.group(2) == "this" else (
            (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1))
        day = int(m.group(1))
        return _safe_date(y, mo, day) or _safe_date(y, mo, _cal.monthrange(y, mo)[1])

    # "<month> <day>" / "<month> <day>, <year>"
    m = re.fullmatch(r"([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?", s)
    if m and m.group(1) in MONTHS:
        mo, day = MONTHS[m.group(1)], int(m.group(2))
        year = int(m.group(3)) if m.group(3) else None
        if year:
            return _safe_date(year, mo, day)
        d = _safe_date(today.year, mo, day)
        if d and future_bias and d < today:
            d = _safe_date(today.year + 1, mo, day) or d
        return d

    # "<day> <month>" / "<day>th of <month>" / "<day>th <month>"
    m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([a-z]+)(?:,?\s+(\d{4}))?", s)
    if m and m.group(2) in MONTHS:
        day, mo = int(m.group(1)), MONTHS[m.group(2)]
        year = int(m.group(3)) if m.group(3) else today.year
        d = _safe_date(year, mo, day)
        if d and future_bias and d < today:
            d = _safe_date(year + 1, mo, day) or d
        return d

    # "<month> <year>" -> 1st of that month/year
    m = re.fullmatch(r"([a-z]+)\s*,?\s*(\d{4})", s)
    if m and m.group(1) in MONTHS:
        return _safe_date(int(m.group(2)), MONTHS[m.group(1)], 1)

    # bare month -> 1st of that month (ranges use year directly; singles future-shift)
    if s in MONTHS:
        mo = MONTHS[s]
        if future_bias:
            d = _safe_date(today.year, mo, 1)
            if d and d < today.replace(day=1):
                d = _safe_date(today.year + 1, mo, 1)
            return d
        return _safe_date(today.year, mo, 1)

    # bare ordinal day -> that day of the current month (roll forward if past)
    m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", s)
    if m:
        day = int(m.group(1))
        if 1 <= day <= 31:
            d = _safe_date(today.year, today.month, day)
            if d is None and day >= 29:
                # day doesn't exist in this month -> next month that has it
                y, mo = today.year, today.month
                for _ in range(12):
                    mo += 1
                    if mo > 12:
                        y, mo = y + 1, 1
                    d = _safe_date(y, mo, day)
                    if d:
                        break
            if d and d < today and future_bias:
                y, mo = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)
                d = _safe_date(y, mo, day)
            return d
    return None


def resolve_date_range(text: str, today: date | None = None):
    """Back-looking range parser (reports). Month names -> current year."""
    if today is None:
        today = date.today()
    raw = (text or "").strip()
    if not raw:
        return None, "no date text provided"

    s = raw.lower().replace("–", "-").replace("—", "-")
    # strip conversational filler so "show report from july to august" / "for july" work
    s = re.sub(r"^\s*(?:please\s+)?(?:show|get|generate|give|pull|display|open)\b[^a-z0-9]*(?:the\b|a\b)?[^a-z0-9]*", "", s)
    s = re.sub(r"^\s*(?:report|statement|summary)\b\s*", "", s)
    s = re.sub(r"^(?:for|from|during|between|in)\s+", "", s)
    s = re.sub(r"\s+report\b.*$", "", s)

    # month-name extraction anywhere in the phrase
    months_found = [mo for mo in MONTHS if re.search(rf"\b{mo}\b", s)]
    months_found.sort(key=lambda mo: s.find(mo))

    # 1) explicit separator
    s = re.sub(r"^between\s+", "", s)
    s = re.sub(r"\s+between\s+", " to ", s)
    parts = re.split(r"\s+(?:to|till|until|through|thru|and|-)\s+", s, maxsplit=1, flags=re.I)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        a = _parse_single(parts[0], today, future_bias=False)
        b = _parse_single(parts[1], today, future_bias=False)
        if a and b:
            if a > b:
                a, b = b, a
            a_raw = parts[0].strip().strip(".,? ")
            b_raw = parts[1].strip().strip(".,? ")
            # bare month names (start AND/OR end) span full months:
            #   "july to august" -> Jul 1 .. Aug 31 ; "march 2025 to august 2025" -> .. Aug 31 2025
            a_is_bare_month = a_raw in MONTHS
            b_is_bare_month = b_raw in MONTHS
            if b_is_bare_month:
                b = _month_end(b.year, b.month)
            elif b_raw.split() and b_raw.split()[0] in MONTHS and re.search(r"\b[1-9][0-9]{3}\b", b_raw):
                b = _month_end(b.year, b.month)
            if a_is_bare_month:
                a = date(a.year, a.month, 1)
            if a > b:
                a, b = b, a
            return a, b
        if a and b is None:
            return None, f"couldn't understand the end date '{parts[1].strip()}'"
        if b and a is None:
            return None, f"couldn't understand the start date '{parts[0].strip()}'"

    t = s.strip()

    # "<month> <year>" / "<month>, <year>" -> whole month of that year
    m = re.search(r"\b([a-z]+)\s*,?\s*(\d{4})\b", t)
    if m and m.group(1) in MONTHS:
        mo, yr = MONTHS[m.group(1)], int(m.group(2))
        return date(yr, mo, 1), _month_end(yr, mo)

    # 2) bare month -> whole month (current year)
    if t in MONTHS:
        mo = MONTHS[t]
        return date(today.year, mo, 1), _month_end(today.year, mo)

    # "the month of <month>"
    m = re.search(r"month\s+of\s+([a-z]+)", t)
    if m and m.group(1) in MONTHS:
        mo = MONTHS[m.group(1)]
        return date(today.year, mo, 1), _month_end(today.year, mo)

    if t in ("last month", "previous month"):
        y, mo = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
        return date(y, mo, 1), _month_end(y, mo)
    if t in ("this month", "current month"):
        return date(today.year, today.month, 1), _month_end(today.year, today.month)
    if t in ("next month",):
        y, mo = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)
        return date(y, mo, 1), _month_end(y, mo)
    if t in ("this year",):
        return date(today.year, 1, 1), date(today.year, 12, 31)
    if t in ("last year",):
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)

    # "last N months" / "past N months" (includes current month)
    m = re.fullmatch(r"(?:the\s+)?(?:last|past|previous)\s+(\d+)\s+months?", t)
    if m:
        n = int(m.group(1))
        y, mo = today.year, today.month
        for _ in range(n - 1):
            mo -= 1
            if mo == 0:
                y, mo = y - 1, 12
        return date(y, mo, 1), _month_end(today.year, today.month)

    # 3) single date -> same-day range
    d = _parse_single(t, today, future_bias=False)
    if d:
        return d, d

    return None, (f"couldn't understand the date '{raw}'. "
                  "Try like 'July to August', 'this month', 'last 3 months', or '15th August'.")


def resolve_single_date(text: str, today: date | None = None):
    """Parse one spoken date, future-biased (for due dates, appointments...).

    Returns (date, None) or (None, reason).
    """
    if today is None:
        today = date.today()
    raw = (text or "").strip()
    if not raw:
        return None, "no date text provided"
    s = raw.lower().replace("–", "-").replace("—", "-")

    d = _parse_single(s, today, future_bias=True)
    if d:
        return d, None

    # "next <month>" -> 1st of that month next occurrence
    m = re.fullmatch(r"next\s+([a-z]+)", s.strip())
    if m and m.group(1) in MONTHS:
        mo = MONTHS[m.group(1)]
        d = _safe_date(today.year, mo, 1)
        if d and d <= today:
            d = _safe_date(today.year + 1, mo, 1)
        if d:
            return d, None

    return None, (f"couldn't understand the date '{raw}'. "
                  "Try like 'tomorrow', 'next Tuesday', '15th of next month', '25th August', or 'in 3 days'.")