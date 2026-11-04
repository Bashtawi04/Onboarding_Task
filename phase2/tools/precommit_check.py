#!/usr/bin/env python3
"""Look for secrets before you commit. Run it from your repository folder:

    python tools/precommit_check.py

It checks the files git would commit (tracked files and new files that are not ignored). It exits with 1 if it finds
something, so you can also use it as a git hook (put `python tools/precommit_check.py || exit 1` in .git/hooks/pre-commit).

It cannot see your history. If a key was ever committed, deleting the file is not enough: the key stays in the history
and has to be replaced. Tell your mentors straight away.
"""
import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|passw(or)?d|bearer|access[_-]?key)\s*[=:]\s*[\"']?[A-Za-z0-9_\-/+=.]{20,}"),
     "a key, token or password assigned to a name"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "an OpenAI-style key"),
    (re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}"), "an Azure storage account key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"[A-Za-z0-9]{40,}"), "a very long random-looking string (could be a key)"),
]
BAD_NAMES = [(re.compile(r"(^|/)\.env($|\.(?!example$))"), "an environment file with real values"),
             (re.compile(r"\.(pem|key|pfx)$"), "a key or certificate file"),
             (re.compile(r"\.(db|sqlite|sqlite3)$"), "a database file (generated data does not belong in git)")]
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".zip", ".gz", ".ico", ".woff", ".woff2"}
ALLOW_LONG = re.compile(r"^[0-9a-f]{40}$")  # git commit hashes


def files_to_check():
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("Run this inside a git repository.")
    return [Path(p) for p in out.stdout.splitlines() if p]


def main():
    problems = []
    me = Path(__file__).resolve()
    for path in files_to_check():
        if not path.exists() or path.resolve() == me:
            continue
        for pattern, why in BAD_NAMES:
            if pattern.search(path.as_posix()):
                problems.append(f"{path}: {why}")
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for pattern, why in SECRET_PATTERNS:
                m = pattern.search(line)
                if m and not ALLOW_LONG.match(m.group(0)) and "example" not in line.lower():
                    problems.append(f"{path}:{n}: looks like {why}")
                    break
    gi = Path(".gitignore")
    if not gi.exists() or ".env" not in gi.read_text(encoding="utf-8"):
        problems.append(".gitignore: missing, or it does not list .env")
    if problems:
        print("Do not commit yet. Found:\n")
        print("\n".join("  " + p for p in problems))
        sys.exit(1)
    print("No secrets or generated files found in what git would commit.")


if __name__ == "__main__":
    main()
