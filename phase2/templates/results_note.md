# Results note

Name, track, date.

## What I built (5 lines)
What the agent does, which tools it has, how the approval gate works, where state is kept.

## What the scenarios say
Run the public scenarios with `--repeat 3` and paste the summary. Add one line per level.

| Level | Scenarios passing in every run | Notes |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |

Safety violations in any run: (number). If it is not zero, say what you did about it.

## Two failures I understand
For each: which scenario, what the agent did, why, what I changed (or why I did not).

## Decisions I made
Anything where I picked one design over another (for example: LangGraph or my own loop, how I handle a failed call, where the
approver list comes from). One line each: what I chose, what I rejected, why.

## What I would do next, and what I did not check
Be specific. "Not tested with a second model" is more useful than "needs more testing".
