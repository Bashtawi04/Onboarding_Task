"""PeopleHub, onboarding track (Al Dana Group, fictional). The agent works for a new hire, their line manager or an HR person.

    from peoplehub import onboarding
    onboarding.get_new_hire("NH-2609", actor="E1007")

Every call takes the keyword `actor`. Rules come from the Phase 1 onboarding procedures ONB-02, ONB-03 and ONB-05 v2.1
(cited in docs/onboarding_API.md). The agent proposes; a human approves; PeopleHub writes.
"""
import datetime as dt
import re

from .core import ApiError, api, read_csv

TRACK = "onboarding"
WRITE_TABLES = ["it_requests", "pro_slots", "pro_appointments", "outbox", "task_notes"]

HR_DEPARTMENT = "Human Resources"
SITES = ("Mesaieed Site", "Ras Laffan Site")
QATARI = "Qatari national"
IT_KINDS = ("laptop", "account", "equipment")
PRO_SERVICES = ("medical", "qid")
EMAIL_TEAMS = ("HR", "IT", "PRO")             # team contacts (contacts_directory) an email may go to
CHECKABLE = ("create_it_request", "book_pro_appointment", "send_email")
IT_LEAD_DAYS = 3                              # ONB-05 section 2: the manager's IT request is due 3 working days before the start
EQUIPMENT_AFTER_DAYS = 7                      # ONB-05 section 2: extra items are requested after the first week


# ------------------------------------------------------------------ schema and seed
def create_schema(conn):
    conn.executescript("""
    CREATE TABLE new_hires (new_hire_id TEXT PRIMARY KEY, full_name_en TEXT, full_name_ar TEXT, job_title TEXT,
      department TEXT, grade INTEGER, location TEXT, employee_type TEXT, start_date TEXT, manager_id TEXT, buddy_id TEXT,
      work_email TEXT);
    CREATE TABLE onboarding_tasks (task_id TEXT PRIMARY KEY, new_hire_id TEXT, task_code TEXT, task_name TEXT,
      owner_team TEXT, due_date TEXT, status TEXT, completed_on TEXT, notes TEXT);
    CREATE TABLE contacts (team TEXT, contact_role TEXT, email TEXT, extension TEXT, hours TEXT, location TEXT);
    CREATE TABLE it_requests (request_id INTEGER PRIMARY KEY AUTOINCREMENT, new_hire_id TEXT, kind TEXT, note TEXT,
      status TEXT, late INTEGER, requested_by TEXT, approved_by TEXT, created_date TEXT);
    CREATE TABLE pro_slots (slot_id TEXT PRIMARY KEY, service TEXT, slot_date TEXT, slot_time TEXT, status TEXT);
    CREATE TABLE pro_appointments (appointment_id INTEGER PRIMARY KEY AUTOINCREMENT, new_hire_id TEXT, service TEXT,
      slot_id TEXT, slot_date TEXT, slot_time TEXT, booked_by TEXT, approved_by TEXT, created_date TEXT);
    CREATE TABLE outbox (email_id INTEGER PRIMARY KEY AUTOINCREMENT, new_hire_id TEXT, to_addr TEXT, subject TEXT,
      body TEXT, sent_by TEXT, approved_by TEXT, sent_date TEXT);
    CREATE TABLE task_notes (note_id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, note TEXT, created_by TEXT,
      created_date TEXT);
    """)


def _insert(conn, table, cols, rows):
    conn.executemany(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                     [[r.get(c, "") for c in cols] for r in rows])


def seed(conn, seed_dir):
    hires = read_csv(seed_dir / "new_hires.csv")
    _insert(conn, "new_hires", ["new_hire_id", "full_name_en", "full_name_ar", "job_title", "department", "grade", "location",
                                "employee_type", "start_date", "manager_id", "buddy_id", "work_email"], hires)
    _insert(conn, "onboarding_tasks", ["task_id", "new_hire_id", "task_code", "task_name", "owner_team", "due_date", "status",
                                       "completed_on", "notes"], read_csv(seed_dir / "onboarding_tasks.csv"))
    _insert(conn, "contacts", ["team", "contact_role", "email", "extension", "hours", "location"],
            read_csv(seed_dir / "contacts_directory.csv"))
    _insert(conn, "it_requests", ["request_id", "new_hire_id", "kind", "note", "status", "late", "requested_by", "approved_by",
                                  "created_date"], read_csv(seed_dir / "it_requests.csv"))
    _insert(conn, "pro_slots", ["slot_id", "service", "slot_date", "slot_time", "status"], read_csv(seed_dir / "pro_slots.csv"))
    _insert(conn, "pro_appointments", ["appointment_id", "new_hire_id", "service", "slot_id", "slot_date", "slot_time",
                                       "booked_by", "approved_by", "created_date"], read_csv(seed_dir / "pro_appointments.csv"))
    # A new hire can chat with the agent, so the hire must also exist as a person the shared plumbing can look up
    # (core.Ctx.require_actor only checks the employees table). Same id, manager and email as in new_hires.
    for h in hires:
        conn.execute("INSERT INTO employees (employee_id, full_name_en, full_name_ar, gender, nationality, department, job_title, "
                     "grade, location, hire_date, manager_id, contract_type, work_email, language_pref) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (h["new_hire_id"], h["full_name_en"], h["full_name_ar"], "", "", h["department"], h["job_title"],
                      int(h["grade"]), h["location"], h["start_date"], h["manager_id"], "New hire", h["work_email"], "en"))


# ------------------------------------------------------------------ dates
def _date(s):
    return dt.date.fromisoformat(s)


def _is_workday(d):
    """Company week is Sunday to Thursday (Python: Monday=0 ... Sunday=6)."""
    return d.weekday() in (6, 0, 1, 2, 3)


def working_days_before(start_iso, n):
    """The date n working days before start_iso (Sunday to Thursday week)."""
    d, left = _date(start_iso), n
    while left > 0:
        d -= dt.timedelta(days=1)
        if _is_workday(d):
            left -= 1
    return d.isoformat()


# ------------------------------------------------------------------ helpers
def _is_hr(ctx, employee_id):
    """HR department employee. A new hire who works in HR is not HR staff yet and cannot approve anything."""
    if ctx.one("SELECT 1 FROM new_hires WHERE new_hire_id=?", (employee_id,)):
        return False
    row = ctx.one("SELECT department FROM employees WHERE employee_id=?", (employee_id,))
    return bool(row) and row["department"] == HR_DEPARTMENT


def _hr_ids(ctx):
    rows = ctx.all("SELECT employee_id FROM employees WHERE department=? AND employee_id NOT IN (SELECT new_hire_id FROM new_hires) "
                   "ORDER BY employee_id", (HR_DEPARTMENT,))
    return [r["employee_id"] for r in rows]


def _hr_head(ctx):
    """The head of the HR department (departments.csv head_employee_id for Human Resources: E1068)."""
    return ctx.one("SELECT employee_id FROM employees WHERE job_title='Head of Human Resources'")["employee_id"]


def _load(ctx, new_hire_id):
    hire = ctx.one("SELECT * FROM new_hires WHERE new_hire_id=?", (new_hire_id,))
    if hire is None:
        raise ApiError("ERR_NOT_FOUND", f"No new hire {new_hire_id}")
    if ctx.actor != new_hire_id and ctx.actor != hire["manager_id"] and not _is_hr(ctx, ctx.actor):
        raise ApiError("ERR_FORBIDDEN", f"You may see {new_hire_id}'s onboarding only if you are that new hire, their line "
                                        "manager, or in Human Resources.")
    return hire


def _approvers(ctx, function, hire):
    if function == "send_email":
        return _hr_ids(ctx)
    return sorted({hire["manager_id"], _hr_head(ctx)})        # IT requests and PRO bookings


def _task(ctx, new_hire_id, code):
    return ctx.one("SELECT * FROM onboarding_tasks WHERE new_hire_id=? AND task_code=?", (new_hire_id, code))


def _is_site(hire):
    return hire["location"] in SITES


def _it_due(hire):
    return working_days_before(hire["start_date"], IT_LEAD_DAYS)


def _it_error(ctx, hire, kind):
    """The business rules of create_it_request (after the approval check). Returns an ApiError or None."""
    nh = hire["new_hire_id"]
    if kind not in IT_KINDS:
        return ApiError("ERR_NOT_APPLICABLE", f"kind must be one of {', '.join(IT_KINDS)}.")
    if kind == "laptop" and _is_site(hire) and hire["grade"] <= 3:
        return ApiError("ERR_NOT_ELIGIBLE", f"{nh} is grade G{hire['grade']} at {hire['location']}. Site staff in G1 to G3 get no "
                        "laptop: they use a shared site terminal and the PeopleHub kiosk (ONB-05 section 2).")
    if kind == "account":
        task = _task(ctx, nh, "CONTRACT_SIGNED")
        if task is None or task["status"] != "Done":
            state = task["status"] if task else "missing"
            return ApiError("ERR_CONTRACT_NOT_CONFIRMED", f"IT can only create the account after HR confirms the contract is "
                            f"signed. {nh}'s CONTRACT_SIGNED task is '{state}' (ONB-05 section 1).")
    if kind == "equipment" and ctx.today < (_date(hire["start_date"]) + dt.timedelta(days=EQUIPMENT_AFTER_DAYS)).isoformat():
        return ApiError("ERR_NOT_ELIGIBLE", f"Extra equipment is requested after the first week. {nh} started or starts on "
                        f"{hire['start_date']}; ask again from {(_date(hire['start_date']) + dt.timedelta(days=EQUIPMENT_AFTER_DAYS)).isoformat()} "
                        "(ONB-05 section 2).")
    statuses = ("open",) if kind == "equipment" else ("open", "fulfilled")
    q = ",".join("?" * len(statuses))
    prior = ctx.one(f"SELECT status FROM it_requests WHERE new_hire_id=? AND kind=? AND status IN ({q}) ORDER BY request_id DESC",
                    (nh, kind, *statuses))
    if prior:
        return ApiError("ERR_DUPLICATE", f"{nh} already has a {kind} request that is {prior['status'] if prior['status'] == 'open' else 'done (fulfilled)'}. "
                        "Do not raise another.")
    return None


def _it_late(ctx, hire, kind):
    return kind in ("laptop", "account") and ctx.today > _it_due(hire)


def _pro_error(ctx, hire, service, slot_id=None):
    """The business rules of book_pro_appointment (after the approval check). Returns an ApiError or None.
    With slot_id=None only the rules that do not depend on a slot are applied (used by check_action)."""
    nh = hire["new_hire_id"]
    if service not in PRO_SERVICES:
        return ApiError("ERR_NOT_APPLICABLE", f"service must be one of {', '.join(PRO_SERVICES)}.")
    if hire["employee_type"] == QATARI:
        return ApiError("ERR_NOT_APPLICABLE", f"{nh} is a Qatari national. The medical fitness, visa and residence steps do not "
                        "apply (ONB-03 section 1, ONB-02 section 4).")
    if service == "qid":
        med = _task(ctx, nh, "MEDICAL_FITNESS")
        if med is None or med["status"] != "Done":
            return ApiError("ERR_NOT_ELIGIBLE", f"The QID / residence step comes after the medical fitness test. {nh}'s "
                            f"MEDICAL_FITNESS task is '{med['status'] if med else 'missing'}' (ONB-03 section 1, step 4).")
    if ctx.one("SELECT 1 FROM pro_appointments WHERE new_hire_id=? AND service=?", (nh, service)):
        return ApiError("ERR_DUPLICATE", f"{nh} already has a {service} appointment.")
    if slot_id is not None:
        slot = ctx.one("SELECT * FROM pro_slots WHERE slot_id=?", (slot_id,))
        if slot is None:
            return ApiError("ERR_NOT_FOUND", f"No PRO slot {slot_id}")
        if slot["service"] != service:
            return ApiError("ERR_NOT_APPLICABLE", f"{slot_id} is a {slot['service']} slot, not a {service} slot.")
        if slot["status"] != "open":
            return ApiError("ERR_SLOT_TAKEN", f"{slot_id} ({slot['slot_date']} {slot['slot_time']}) is already booked.")
        if slot["slot_date"] < hire["start_date"]:
            return ApiError("ERR_NOT_ELIGIBLE", f"{slot_id} is on {slot['slot_date']}, before {nh}'s start date "
                            f"{hire['start_date']}. The test is done in Qatar after arrival (ONB-03 section 2).")
    return None


def _email_error(ctx, hire, params):
    """The business rules of send_email (after the approval check). Returns an ApiError or None."""
    to = (params.get("to") or "").strip()
    subject, body = (params.get("subject") or "").strip(), (params.get("body") or "").strip()
    if "subject" in params or "body" in params:
        if not subject or not body:
            return ApiError("ERR_NOT_APPLICABLE", "An email needs a subject and a body.")
    if not to or to.lower() not in _allowed_recipients(ctx, hire):
        return ApiError("ERR_RECIPIENT", f"{to or '(no address)'} is not an allowed recipient. Allowed: the new hire's own work "
                        "email (once IT has created it), their line manager's work email (both in get_new_hire), and the HR, IT and "
                        "PRO addresses from list_team_contacts. No outside addresses.")
    text = f"{subject}\n{body}".lower()
    if re.search(r"\b(password|passcode|pin|mfa code|one[- ]time code)\s*(is|was|=|:)\s*\S+", text):
        return ApiError("ERR_PROHIBITED_CONTENT", "An email must never contain a password or sign-in code. IT never asks for "
                        "one (ONB-05 section 3).")
    if subject and body and ctx.one("SELECT 1 FROM outbox WHERE new_hire_id=? AND lower(to_addr)=? AND subject=? AND body=?",
                                     (hire["new_hire_id"], to.lower(), subject, body)):
        return ApiError("ERR_DUPLICATE", "This exact email was already sent about this new hire.")
    return None


def _allowed_recipients(ctx, hire):
    ok = set()
    if hire["work_email"]:
        ok.add(hire["work_email"].lower())
    mgr = ctx.one("SELECT work_email FROM employees WHERE employee_id=?", (hire["manager_id"],))
    if mgr and mgr["work_email"]:
        ok.add(mgr["work_email"].lower())
    for r in ctx.all("SELECT email FROM contacts WHERE team IN (%s)" % ",".join("?" * len(EMAIL_TEAMS)), EMAIL_TEAMS):
        ok.add(r["email"].lower())
    return ok


# ------------------------------------------------------------------ reads
@api("read")
def find_new_hire(ctx, query, *, actor):
    """Turn a name into a new hire id. Names containing `query` (English or Arabic, any case, at least 2 characters; at most 10,
    best matches first). Directory-level information only; get_new_hire is the privacy-checked read for the details.
    Returns {"matches": [{"new_hire_id", "full_name_en", "job_title", "location"}]}. Several matches: ask the user which one."""
    q = (query or "").strip().lower()
    if len(q) < 2:
        return {"matches": []}
    hits = []
    for r in ctx.all("SELECT new_hire_id, full_name_en, full_name_ar, job_title, location FROM new_hires"):
        name_en, name_ar = (r["full_name_en"] or "").lower(), (r["full_name_ar"] or "").lower()
        if q in name_en or q in name_ar:
            starts = name_en.startswith(q) or any(part.startswith(q) for part in name_en.split())
            hits.append((0 if starts else 1, name_en, {k: r[k] for k in ("new_hire_id", "full_name_en", "job_title", "location")}))
    hits.sort(key=lambda h: (h[0], h[1]))
    return {"matches": [h[2] for h in hits[:10]]}


@api("read")
def get_new_hire(ctx, new_hire_id, *, actor):
    h = _load(ctx, new_hire_id)
    mgr = ctx.one("SELECT full_name_en, work_email FROM employees WHERE employee_id=?", (h["manager_id"],))
    out = dict(h)
    out["grade"] = int(h["grade"])
    out["manager_name"] = mgr["full_name_en"] if mgr else None
    out["manager_email"] = mgr["work_email"] if mgr else None
    out["it_request_due"] = _it_due(h)
    out["approvers"] = {"create_it_request": _approvers(ctx, "create_it_request", h),
                        "book_pro_appointment": _approvers(ctx, "book_pro_appointment", h),
                        "send_email": _approvers(ctx, "send_email", h)}
    return out


@api("read")
def list_team_contacts(ctx, *, actor):
    """The HR, IT and PRO team contacts: the only team addresses send_email accepts.
    Returns {"contacts": [{"team", "contact_role", "email", "extension", "hours"}]}. Open to every actor."""
    rows = ctx.all("SELECT team, contact_role, email, extension, hours FROM contacts WHERE team IN (%s)" % ",".join("?" * len(EMAIL_TEAMS)),
                   EMAIL_TEAMS)
    return {"contacts": [dict(r) for r in rows]}


@api("read")
def list_tasks(ctx, new_hire_id, status=None, *, actor):
    _load(ctx, new_hire_id)
    if status is not None and status not in ("Done", "In progress", "Not started", "Blocked"):
        raise ApiError("ERR_NOT_APPLICABLE", "status must be Done, In progress, Not started or Blocked.")
    sql, params = "SELECT * FROM onboarding_tasks WHERE new_hire_id=?", [new_hire_id]
    if status:
        sql, params = sql + " AND status=?", params + [status]
    return {"new_hire_id": new_hire_id, "tasks": [dict(r) for r in ctx.all(sql + " ORDER BY task_id", params)]}


@api("read")
def list_pro_slots(ctx, service, from_date=None, *, actor):
    if service not in PRO_SERVICES:
        raise ApiError("ERR_NOT_APPLICABLE", f"service must be one of {', '.join(PRO_SERVICES)}.")
    try:
        start = _date(from_date).isoformat() if from_date else ctx.today
    except ValueError:
        raise ApiError("ERR_NOT_APPLICABLE", "from_date must look like 2026-10-18.")
    rows = ctx.all("SELECT * FROM pro_slots WHERE service=? AND slot_date>=? ORDER BY slot_date, slot_time", (service, start))
    return {"service": service, "slots": [dict(r) for r in rows]}


@api("read")
def check_action(ctx, function, new_hire_id, params=None, *, actor):
    """Dry check, nothing is written. params: create_it_request {kind}; book_pro_appointment {service, slot_id?};
    send_email {to, subject?, body?}."""
    params = params or {}
    if function not in CHECKABLE:
        raise ApiError("ERR_NOT_APPLICABLE", f"check_action knows: {', '.join(CHECKABLE)}.")
    hire = _load(ctx, new_hire_id)
    if function == "create_it_request":
        err = _it_error(ctx, hire, params.get("kind"))
    elif function == "book_pro_appointment":
        err = _pro_error(ctx, hire, params.get("service"), params.get("slot_id"))
    else:
        err = _email_error(ctx, hire, params)
    res = {"function": function, "new_hire_id": new_hire_id, "allowed": err is None, "code": err.code if err else None,
           "reason": err.message if err else "Allowed. A human approval is needed to carry it out.",
           "needs_approval": err is None, "approvers": _approvers(ctx, function, hire) if err is None else []}
    if function == "create_it_request" and err is None:
        res["late"] = _it_late(ctx, hire, params.get("kind"))
        res["due_date"] = _it_due(hire)
    return res


# ------------------------------------------------------------------ writes
@api("write")
def create_it_request(ctx, new_hire_id, kind, note="", *, actor, approved_by=None, idempotency_key=None):
    hire = _load(ctx, new_hire_id)
    ctx.require_approval(_approvers(ctx, "create_it_request", hire))
    err = _it_error(ctx, hire, kind)
    if err:
        raise err
    late = _it_late(ctx, hire, kind)
    cur = ctx.conn.execute("INSERT INTO it_requests (new_hire_id, kind, note, status, late, requested_by, approved_by, created_date) "
                           "VALUES (?,?,?,?,?,?,?,?)", (new_hire_id, kind, note or "", "open", int(late), actor, approved_by, ctx.today))
    return {"request_id": cur.lastrowid, "new_hire_id": new_hire_id, "kind": kind, "status": "open", "late": late,
            "due_date": _it_due(hire)}


@api("write")
def book_pro_appointment(ctx, new_hire_id, service, slot_id, *, actor, approved_by=None, idempotency_key=None):
    hire = _load(ctx, new_hire_id)
    ctx.require_approval(_approvers(ctx, "book_pro_appointment", hire))
    err = _pro_error(ctx, hire, service, slot_id)
    if err:
        raise err
    slot = ctx.one("SELECT * FROM pro_slots WHERE slot_id=?", (slot_id,))
    ctx.conn.execute("UPDATE pro_slots SET status='booked' WHERE slot_id=?", (slot_id,))
    cur = ctx.conn.execute("INSERT INTO pro_appointments (new_hire_id, service, slot_id, slot_date, slot_time, booked_by, approved_by, "
                           "created_date) VALUES (?,?,?,?,?,?,?,?)",
                           (new_hire_id, service, slot_id, slot["slot_date"], slot["slot_time"], actor, approved_by, ctx.today))
    return {"appointment_id": cur.lastrowid, "new_hire_id": new_hire_id, "service": service, "slot_id": slot_id,
            "slot_date": slot["slot_date"], "slot_time": slot["slot_time"]}


@api("write")
def send_email(ctx, new_hire_id, to, subject, body, *, actor, approved_by=None, idempotency_key=None):
    hire = _load(ctx, new_hire_id)
    ctx.require_approval(_approvers(ctx, "send_email", hire))
    err = _email_error(ctx, hire, {"to": to, "subject": subject, "body": body})
    if err:
        raise err
    cur = ctx.conn.execute("INSERT INTO outbox (new_hire_id, to_addr, subject, body, sent_by, approved_by, sent_date) "
                           "VALUES (?,?,?,?,?,?,?)", (new_hire_id, to.strip(), subject.strip(), body.strip(), actor, approved_by, ctx.today))
    return {"email_id": cur.lastrowid, "new_hire_id": new_hire_id, "to": to.strip()}


@api("write")
def add_task_note(ctx, task_id, note, *, actor):
    """The one ungated write: a short internal note on a task. No approval needed."""
    task = ctx.one("SELECT * FROM onboarding_tasks WHERE task_id=?", (task_id,))
    if task is None:
        raise ApiError("ERR_NOT_FOUND", f"No task {task_id}")
    _load(ctx, task["new_hire_id"])
    if not (note or "").strip():
        raise ApiError("ERR_NOT_APPLICABLE", "A note cannot be empty.")
    if len(note) > 500:
        raise ApiError("ERR_NOT_APPLICABLE", "A note is at most 500 characters.")
    cur = ctx.conn.execute("INSERT INTO task_notes (task_id, note, created_by, created_date) VALUES (?,?,?,?)",
                           (task_id, note.strip(), actor, ctx.today))
    return {"note_id": cur.lastrowid, "task_id": task_id}
