"""Company directory: find people by name. Shared by every track.

An agent is usually asked about "Lina Khoury", not about "NH-2611". This is how it turns a name into an id.
The directory shows only what a staff directory would (id, name, job title, department, location). Details about a person
are behind the track's own read functions, which check who is asking.
"""
import datetime as dt

from .core import TODAY, api


@api("read")
def find_employee(ctx, query, *, actor):
    """Employees whose name contains `query` (English or Arabic, any case; at most 10, best matches first).
    Returns {"matches": [{"employee_id", "full_name_en", "job_title", "department", "location"}]}."""
    q = (query or "").strip().lower()
    if len(q) < 2:
        return {"matches": []}
    rows = ctx.all("SELECT employee_id, full_name_en, full_name_ar, job_title, department, location FROM employees")
    hits = []
    for r in rows:
        name_en, name_ar = (r["full_name_en"] or "").lower(), r["full_name_ar"] or ""
        if q in name_en or q in name_ar.lower():
            starts = name_en.startswith(q) or any(part.startswith(q) for part in name_en.split())
            hits.append((0 if starts else 1, name_en, {k: r[k] for k in ("employee_id", "full_name_en", "job_title", "department", "location")}))
    hits.sort(key=lambda h: (h[0], h[1]))
    return {"matches": [h[2] for h in hits[:10]]}


@api("read")
def get_today(ctx, *, actor):
    """The date in PeopleHub. It never reads your computer's clock: every scenario happens on this day.
    Returns {"today": "2026-10-16", "weekday": "Friday", "working_week": "Sunday to Thursday"}."""
    d = dt.date.fromisoformat(TODAY)
    return {"today": TODAY, "weekday": d.strftime("%A"), "working_week": "Sunday to Thursday"}
