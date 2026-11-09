# 📊 Evaluation results

**Yahya AlBashtawi · Cerebrum · Phase 2 · Updated 8 November 2026**

[Project overview](README.md) · [Review notes](CHANGELOG.md)

## ✅ Current status

The current action-summary update passes **42/42 offline tests**. Its live
Azure verification is pending. Earlier live scores below belong to earlier
code revisions and must not be presented as scores for the current update.

## 🧪 Results by revision

| Revision | Public runs | Additional runs | Review runs | Unit tests |
|---|---:|---:|---:|---:|
| Original submission | 24/24 | 12/12 | Not present | 20/20 |
| First review update | 24/24 | 12/12 | 6/6 | 38/38 |
| Current action-summary update | 24/24 | 12/12 | 15/15 | **42/42** |

The first review update's 42 live runs reported **zero safety violations**.
The mentor also reported **17/18 unseen runs** for the original submission.
The private unseen suite has not been rerun here.

## 📁 Evidence

| Report | Revision |
|---|---|
| [Original public results](results-public-repeat3.json) | Original submission |
| [Original additional results](results-own-repeat3-utf8.json) | Original submission |
| [Public rerun](results-public-baseline.json) | First review update |
| [Additional rerun](results-additional-baseline.json) | First review update |
| [Workflow rerun](results-workflow-baseline.json) | First review update |

Original public and additional reports were generated at different development
points around the Windows encoding fix. They are preserved as historical evidence.
The first review update's Windows terminal output also recorded 38 passing units.
Current offline tests use canned model responses and real PeopleHub simulator
checks and database effects; they do not make Azure model requests.

## 🔎 What the review uncovered

| Issue | Correction | Regression coverage |
|---|---|---|
| Stops after the first approved write | Continue after execution, rejection or failure | Three actions, three independent approvals |
| Missing hire email silently replaced by HR | Ask for an explicit recipient | No email written without an appropriate address |
| Wrong human rejection explanation | Render the recorded human decision | Misleading model explanation cannot replace receipt |
| Completed request described as pending | Render saved execution result and request ID | Contradictory model wording excluded |
| Wrong appointment weekday | Calculate weekday from returned date | Tuesday 2026-10-20 checked |
| Failed execution described as failed proposal | Keep the recorded execution failure | No invented proposal-failure explanation |
| Unnecessary contract warnings | Preserve actual failed checks only | Laptop-only and blocked-account/laptop cases |
| Further calls after forbidden access | Stop the turn in code | No second forbidden call |

## 🛡️ Coverage

- 20 approval/recovery tests: decision identity, allowed edits, changed eligibility,
  rejection, retries, duplicate prevention, fresh-process resume and crash recovery.
- 22 conversation tests: tool validation, malformed arguments, batches, eight-call
  limit, continuation, missing recipients, readable messages and truthful receipts.
- 8 supplied public scenarios and 4 existing additional scenarios remain unchanged.
- 5 review scenarios cover three-action continuation, missing email, rejection
  attribution, appointment weekday and executed account status.

The supplied PeopleHub and evaluation harness remain unchanged. Added scenarios
and tests informed development; they are regression tests, not an untouched test set.

## ⚠️ Interpretation and remaining work

Passing checks is evidence for the cases exercised, not universal correctness.
The first review update passed every scenario while some generated explanations
were still wrong; reading the full replies revealed those gaps.

Current offline checks and the supplied secret checker pass. A fresh installation
of the current revision's exact pinned dependencies has not been verified here.
Mentor rerun, teammate peer review and final demonstration
remain separate delivery steps. Final receipts cover recorded actions; separate
informational questions in mixed requests should be asked in their own turn.
CLI identities are simulated and all operations use a mock HR system.

## ▶️ Reproduce

Run from phase2 with the existing configured environment. All unit tests:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
```

For each suite (public, own, review), use the harness instructions in README.
Save current outputs as results-public-latest.json, results-additional-latest.json and
results-workflow-latest.json. Inspect every reply and summary before replacing
pending entries with verified scores. Live runs use billable Azure requests.

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
