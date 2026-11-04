"""PeopleHub mock for Al Dana Group (fictional). See core.py for how every call behaves.

    from peoplehub import onboarding   # or learning, or recruiting
    onboarding.list_tasks("NH-2609", actor="NH-2609")
"""
from .core import ApiError, TODAY, add_fault, build_db, connect, db_path  # noqa: F401
from . import directory  # noqa: E402,F401
