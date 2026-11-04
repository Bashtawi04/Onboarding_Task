"""Your agent's command-line interface. Start here and fill in the TODOs.

The runner (harness/run_scenarios.py) starts this program once per command, as a NEW process each time:

    python agent_cli.py start  --thread T --user U --message "text"
    python agent_cli.py say    --thread T --message "text" [--user U]
    python agent_cli.py resume --thread T --decision approve|reject|modify --by EMPLOYEE_ID [--edit '{"key": "value"}']

Every command prints exactly ONE JSON object on standard output (print logs to standard error).
Read harness/README.md for what the fields mean. The rules that matter most:

  * Nothing is written to PeopleHub until a human has approved the action.
  * `approved_by` comes from --by (the human), never from the model.
  * Everything you need between two commands is saved under $AGENT_STATE_DIR.
"""
import argparse
import json
import os
import sys
from pathlib import Path

STATE_DIR = Path(os.environ.get("AGENT_STATE_DIR", ".agent_state"))


def respond(status, message, pending=None):
    """Print the one JSON object the runner expects."""
    print(json.dumps({"status": status, "message": message, "pending": pending}, ensure_ascii=False))


def save_state(thread, state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / f"{thread}.json").write_text(json.dumps(state, ensure_ascii=False))


def load_state(thread):
    path = STATE_DIR / f"{thread}.json"
    return json.loads(path.read_text()) if path.exists() else {}


def start(thread, user, message):
    # TODO: run your agent on `message`, acting on behalf of `user`.
    #   * If it only needs to look things up or answer: respond("done", answer)
    #   * If it wants to change something in PeopleHub: save what you need to carry it out later,
    #     then respond("awaiting_approval", text_for_the_human, pending={
    #         "tool": ..., "args": {...}, "approvers": [employee ids], "summary": ...})
    #     and do NOT call the write yet.
    raise NotImplementedError


def say(thread, user, message):
    # TODO: a follow-up message on a conversation whose last request finished.
    raise NotImplementedError


def resume(thread, decision, by, edit):
    # TODO: load the saved state for `thread` (resume has no --user: save the user when you start).
    #   approve -> carry out the pending action with approved_by=by
    #   reject  -> do not carry it out; tell the user
    #   modify  -> carry it out with `edit` merged over the proposed arguments
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "say", "resume"])
    parser.add_argument("--thread", required=True)
    parser.add_argument("--user")
    parser.add_argument("--message")
    parser.add_argument("--decision", choices=["approve", "reject", "modify"])
    parser.add_argument("--by")
    parser.add_argument("--edit")
    a = parser.parse_args()
    try:
        if a.command == "start":
            start(a.thread, a.user, a.message)
        elif a.command == "say":
            say(a.thread, a.user, a.message)
        else:
            resume(a.thread, a.decision, a.by, json.loads(a.edit) if a.edit else {})
    except Exception as exc:  # a crash must still print valid JSON
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        respond("error", "Something went wrong on my side, and nothing was changed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
