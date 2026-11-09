# Review notes — 8 November 2026

## Status

Implemented locally and verified with **42 offline tests**: 20 approval/recovery tests and 22 conversation tests. Model responses are mocked; PeopleHub database effects and approval checks use the real simulator. These are not live Azure results.

The mentor reproduced the original 24/24 public runs, 12/12 additional runs and 20/20 units, then obtained 17/18 on unseen runs. Those scores belong to the original submission.

## Changes

| Finding | Change and verification |
|---|---|
| Stops after the first action | Save the actual tool result and continue the model conversation after approval, rejection or failure. A laptop/medical/email test checks effects after three separate approvals. Repeated resume does not replay completed writes. |
| Missing loop coverage | Fake-client tests exercise run_agent: tool batches, eight-call limit, malformed JSON, unexpected arguments, unknown tools, read-only answers, rejection, failures and continuation recovery. |
| Raw JSON replies | Readable action descriptions, hire and approver names. Structured tool results remain in saved state. English proposal and Arabic template tests pass. |
| Welcome email redirected to HR | Require the hire's recorded address or an address explicitly supplied in the current user request; otherwise ask for clarification. PeopleHub still validates allowed addresses. Both missing-address refusal and explicit HR recipient are tested. |
| Scenario-specific policy/context | Removed OB-08-specific prompt rule, duplicated grade policy and blanket contract warnings. Actual failed checks remain in conversation. Tests cover laptop-only requests and blocked-account context across laptop approval. |
| Forbidden follow-up call | Stop the turn in code immediately on ERR_FORBIDDEN. Test confirms one forbidden API call and no further model call. |
| Unsupported follow-up promise | Removed the absolute prompt-only promise. The prompt asks for focused replies; model-written wording is not universally guaranteed. |
| Missing guidance | README now includes Linux/macOS commands and the limits of withdrawing pending requests. |

## New live scenarios

- REV-01: laptop, medical appointment and email, with a separate approval for each. Its fixture supplies a work email to isolate continuation.
- REV-02: a missing hire email must not silently become an email to HR.

Original harness, PeopleHub, public and own scenario files, and original live result artifacts were not changed.

## Validation and remaining work

- 42/42 offline tests passed; Python syntax compilation passed.
- Git whitespace validation and supplied precommit checker passed.
- Final receipt revision: public 24/24, additional 12/12 and workflow 15/15 live runs passed, with zero reported safety violations.
- The mentor's private unseen suite is unavailable locally.
- Local verification was not a fresh installation of the exact pinned Windows dependencies. Recheck in the existing Windows environment before submission.
- Both review branches are uploaded. Teammate peer review, mentor rerun and demonstration remain separate delivery steps.

Run all unit tests using `python -m unittest discover -s tests -v`. README includes the three live scenario commands. Save new results separately from original evidence and inspect every summary; do not report revised live scores before running them.

## Limits

Arabic templates are covered, but names, some service/slot labels and API errors may remain English. Model-written final wording can vary. Recipient matching is conservative: “email HR” without an address may require clarification.

Within one user request, repeated actions of the same tool/hire/kind or service/recipient are treated as resolved. Intentionally distinct repeated actions in that category should be separate requests.

A new say message does not withdraw a pending proposal: an eligible approver must reject it. Executed actions cannot be cancelled through this workflow. Forbidden access stops the entire turn and leaves other work unresolved. CLI identities are simulated, not production authentication.

## Results from the first revision

The three reports supplied by Yahya confirm 24/24 public runs, 12/12 additional
runs and 6/6 review runs, with no reported safety violations. The installation
also passed 38 unit tests on Windows. Those results belong to the first patch.

Reading the full replies found errors that the original harness assertions did
not catch: wrong weekday, a human rejection described as ineligibility, an
executed request described as awaiting approval, and an execution failure
described as a proposal failure.

## Final action summaries

The model still continues after each decision and can propose the next requested
action. Once a turn has resolved actions, its final message uses saved outcomes,
not a model-written paraphrase. Appointment weekdays come from Python's date
calculation, rejection names come from the recorded human decision, and created
request IDs and statuses come from PeopleHub.

The final receipt omits model-written notes and email body text; email content
remains visible for approval. Read-only turns still use model answers.
Mixed requests with separate informational questions receive an explicitly
limited action receipt; ask those informational questions in a separate turn.
This avoids claiming that every possible part of a mixed request was answered.

Four new offline tests intentionally provide misleading model replies and
verify they do not appear in the final receipt. REV-03 through REV-05 add live
checks for rejection attribution, weekday and execution status. These expanded live scenarios passed 15/15 runs against Azure.

Conversation tests are in tests/test_conversation.py. The old test_loop.py
contains only a relocation notice so copying this patch over the first patch
does not run duplicate tests. Original scenario IDs and PeopleHub names remain
unchanged for traceability.

## Verified results — 9 November 2026

The latest published reports record **51/51 live scenario runs passing**:
24/24 public, 12/12 additional and 15/15 workflow runs, with **zero
reported safety violations**. Windows terminal output records **42/42
unit tests passing**.

- [Public results](results-public-latest.json)
- [Additional results](results-additional-latest.json)
- [Workflow results](results-workflow-latest.json)

These results cover the exercised scenarios, not every possible request.
The mentor's private unseen suite has not been rerun here.
Teammate PR review, mentor acceptance and final demonstration remain
separate tasks. The review branch has been uploaded to Azure DevOps and
GitHub; uploading does not merge it into the main branches.
