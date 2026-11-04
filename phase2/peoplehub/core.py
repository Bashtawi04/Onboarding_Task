"""PeopleHub mock: shared plumbing for every track.

PeopleHub is a fictional HR system for Al Dana Group. It is a small Python library on top of one SQLite file,
so there is nothing to install or start. Every public function behaves like a call to a real company API:

* it validates its inputs and the business rules, and raises ApiError with a fixed error code when it refuses;
* every call (read or write, success or failure) is recorded in the audit_log table;
* every write needs an `actor` (who the request is on behalf of) and an `approved_by` (a human who said yes);
* a write can be given an `idempotency_key`; calling again with the same key returns the first result and
  creates nothing new.

Point the library at a database file with the PEOPLEHUB_DB environment variable (default ./peoplehub.db).
"""
import csv
import functools
import inspect
import json
import os
import sqlite3
from pathlib import Path

TODAY = "2026-10-16"  # the scenario date for every question, same as Phase 1
HERE = Path(__file__).resolve().parent


class ApiError(Exception):
    """A refusal from the mock system. `code` is stable and documented; `message` is for people."""

    def __init__(self, code, message, retryable=False):
        super().__init__(f"{code}: {message}")
        self.code, self.message, self.retryable = code, message, retryable

    def as_dict(self):
        return {"error": self.code, "message": self.message, "retryable": self.retryable}


def db_path():
    return os.environ.get("PEOPLEHUB_DB", "peoplehub.db")


def connect(path=None):
    conn = sqlite3.connect(path or db_path(), timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


COMMON_SCHEMA = """
CREATE TABLE employees (employee_id TEXT PRIMARY KEY, full_name_en TEXT, full_name_ar TEXT, gender TEXT, nationality TEXT,
  department TEXT, job_title TEXT, grade INTEGER, location TEXT, hire_date TEXT, manager_id TEXT, contract_type TEXT,
  work_email TEXT, language_pref TEXT);
CREATE TABLE audit_log (seq INTEGER PRIMARY KEY AUTOINCREMENT, function TEXT, kind TEXT, args TEXT, actor TEXT,
  approved_by TEXT, outcome TEXT, error_code TEXT, result TEXT);
CREATE TABLE faults (id INTEGER PRIMARY KEY AUTOINCREMENT, function TEXT, remaining INTEGER, code TEXT, message TEXT,
  retryable INTEGER DEFAULT 1);
CREATE TABLE idempotency (key TEXT, function TEXT, fingerprint TEXT, result TEXT, PRIMARY KEY (key, function));
"""


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_employees(conn, seed_dir=None):
    rows = read_csv((seed_dir or HERE / "seed_data" / "common") / "employees.csv")
    cols = ["employee_id", "full_name_en", "full_name_ar", "gender", "nationality", "department", "job_title", "grade",
            "location", "hire_date", "manager_id", "contract_type", "work_email", "language_pref"]
    conn.executemany(f"INSERT INTO employees ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                     [[r[c] for c in cols] for r in rows])


class Ctx:
    """Handed to each API function as its first argument by @api. Not part of the public signature."""

    def __init__(self, conn, fn_name, kind, actor, approved_by):
        self.conn, self.fn_name, self.kind, self.actor, self.approved_by = conn, fn_name, kind, actor, approved_by
        self.today = TODAY

    def one(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()

    def all(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def employee(self, employee_id):
        row = self.one("SELECT * FROM employees WHERE employee_id=?", (employee_id,))
        if row is None:
            raise ApiError("ERR_NOT_FOUND", f"No employee {employee_id}")
        return row

    def require_actor(self):
        if not self.actor:
            raise ApiError("ERR_NO_ACTOR", "Every call needs an actor: the person the request is made for.")
        self.employee(self.actor)

    def approved_set(self):
        """approved_by is one id ("E1060") or several joined by commas ("E1060,E1068")."""
        return {x.strip() for x in (self.approved_by or "").split(",") if x.strip()}

    def require_approval(self, allowed_ids):
        """One approval, from any one of allowed_ids. The id comes from a human decision, never from the model."""
        self.require_approvals([allowed_ids])

    def require_approvals(self, groups):
        """Several approvals: for each group (a set of acceptable ids) one member must have approved.
        Anyone who approved but belongs to no group is refused."""
        got = self.approved_set()
        if not got:
            raise ApiError("ERR_NOT_APPROVED", "This action needs a human approval (approved_by) and none was given.")
        groups = [set(g) for g in groups]
        extra = got - set().union(*groups)
        if extra:
            raise ApiError("ERR_APPROVER_NOT_ALLOWED",
                           f"{sorted(extra)} may not approve this action. Allowed: {[sorted(g) for g in groups]}.")
        for g in groups:
            if not got & g:
                raise ApiError("ERR_APPROVAL_INCOMPLETE",
                               f"Still needs an approval from one of {sorted(g)}. Approvals given: {sorted(got)}.")


def _public_signature(fn):
    sig = inspect.signature(fn)
    return sig.replace(parameters=list(sig.parameters.values())[1:])


def api(kind):
    """Decorator for PeopleHub functions. kind is 'read' or 'write'.

    Writes may take the keyword arguments actor, approved_by and idempotency_key; reads take actor.
    """
    assert kind in ("read", "write")

    def deco(fn):
        inner_sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                bound = _public_signature(fn).bind(*args, **kwargs)
            except TypeError as e:
                if "actor" in str(e):
                    raise ApiError("ERR_NO_ACTOR", "Every call needs the keyword actor: the person the request is made for.")
                raise
            conn = connect()
            bound.apply_defaults()
            params = dict(bound.arguments)
            actor, approved_by = params.get("actor"), params.get("approved_by")
            idem = params.get("idempotency_key")
            ctx = Ctx(conn, fn.__name__, kind, actor, approved_by)
            outcome, code, result_json, to_return, error = "ok", None, None, None, None
            try:
                fault = conn.execute("SELECT * FROM faults WHERE function=? AND remaining>0 ORDER BY id LIMIT 1",
                                     (fn.__name__,)).fetchone()
                if fault is not None:
                    conn.execute("UPDATE faults SET remaining=remaining-1 WHERE id=?", (fault["id"],))
                    conn.commit()
                    raise ApiError(fault["code"], fault["message"] or "Service temporarily unavailable.",
                                   bool(fault["retryable"]))
                ctx.require_actor()
                fingerprint = json.dumps({k: v for k, v in params.items() if k not in ("approved_by", "idempotency_key")},
                                         sort_keys=True, default=str)
                if kind == "write" and idem:
                    hit = conn.execute("SELECT fingerprint, result FROM idempotency WHERE key=? AND function=?",
                                       (idem, fn.__name__)).fetchone()
                    if hit is not None:
                        if hit["fingerprint"] != fingerprint:
                            raise ApiError("ERR_IDEMPOTENCY_CONFLICT",
                                           "That idempotency_key was already used for a different request (other caller or other arguments).")
                        to_return = dict(json.loads(hit["result"]), duplicate=True)
                if to_return is None:
                    to_return = fn(ctx, *args, **kwargs)
                    if kind == "write" and idem:
                        conn.execute("INSERT OR REPLACE INTO idempotency VALUES (?,?,?,?)",
                                     (idem, fn.__name__, fingerprint, json.dumps(to_return, default=str)))
                conn.commit()
                result_json = json.dumps(to_return, default=str)[:2000]
            except ApiError as e:
                conn.rollback()
                outcome, code, error = "error", e.code, e
                result_json = json.dumps(e.as_dict())
            except Exception:
                conn.rollback()
                raise
            finally:
                try:
                    shown = {k: v for k, v in params.items()}
                    conn.execute(
                        "INSERT INTO audit_log (function, kind, args, actor, approved_by, outcome, error_code, result) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (fn.__name__, kind, json.dumps(shown, default=str), actor, approved_by, outcome, code,
                         result_json))
                    conn.commit()
                finally:
                    conn.close()
            if error is not None:
                raise error
            return to_return

        wrapper.__signature__ = _public_signature(fn)
        wrapper.api_kind = kind
        return wrapper

    return deco


def build_db(out_path, track_module=None):
    """Create a fresh database: common tables, employees, then the track's own tables and seed rows."""
    out = Path(out_path)
    if out.exists():
        out.unlink()
    conn = connect(str(out))
    conn.executescript(COMMON_SCHEMA)
    load_employees(conn)
    if track_module is not None:
        track_module.create_schema(conn)
        track_module.seed(conn, HERE / "seed_data" / track_module.TRACK)
    conn.commit()
    conn.close()
    return out


def add_fault(function, times=1, code="ERR_UNAVAILABLE", message="The service is temporarily unavailable. Try again.",
              retryable=True, path=None):
    conn = connect(path)
    conn.execute("INSERT INTO faults (function, remaining, code, message, retryable) VALUES (?,?,?,?,?)",
                 (function, times, code, message, int(retryable)))
    conn.commit()
    conn.close()
