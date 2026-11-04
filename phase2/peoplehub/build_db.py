"""Build a fresh PeopleHub database for one track.

    python -m peoplehub.build_db onboarding peoplehub.db
"""
import importlib
import sys

from . import core

TRACKS = ("onboarding", "learning", "recruiting")


def track_module(name):
    if name in TRACKS:
        return importlib.import_module(f"peoplehub.{name}")
    try:  # mentor tests may load a toy track that lives outside the package
        return importlib.import_module(name)
    except ModuleNotFoundError:
        raise SystemExit(f"Unknown track {name!r}. Choose one of {TRACKS}.")


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 2:
        raise SystemExit(__doc__)
    path = core.build_db(argv[1], track_module(argv[0]))
    print(f"Built {path} for track {argv[0]}")


if __name__ == "__main__":
    main()
