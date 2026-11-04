# Checklist for reviewing a teammate's agent

Review it the way you would want yours reviewed: read the code, run it, and say what you found in plain words.
Leave comments on the pull request. Say what is good as well as what needs changing.

Safety (read the code, do not trust the README)
- [ ] The approval gate is code, not a sentence in the prompt. Find the exact line that decides whether a write may run.
- [ ] `approved_by` comes from `--by` and never from the model's output or a tool argument.
- [ ] No write to PeopleHub can run before the approval arrives. Look at every place that calls a write.
- [ ] After a `reject`, nothing is written. After a `modify`, the EDITED arguments are used.
- [ ] The list of approvers is worked out from the rules in the API guide, not hard-coded for one scenario.

Reliability
- [ ] State is saved on disk, so `resume` works in a new process. Kill it between `start` and `resume` and check.
- [ ] A failed call becomes a useful message for the model, not a crash. Retries have a limit.
- [ ] Asking twice for the same thing does not do it twice.

Engineering
- [ ] A fresh clone runs by following the README alone (new virtual environment, install, run the scenarios).
- [ ] No keys, `.env` files, databases or generated state in the repository (run `python tools/precommit_check.py`).
- [ ] The results note says what the scenarios do not cover.

Write three things at the end: the best part, the one change that matters most, and a question you would like the author to answer.
