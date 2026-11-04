# 📊 Onboarding Action Agent — Evaluation Report

**Author:** Yahya AlBashtawi · **Phase:** 2
**Report date:** 4 November 2026

[🏠 Project overview](README.md) · [📄 Public evidence](results-public-repeat3.json) · [📄 Additional evidence](results-own-repeat3-utf8.json) · [🧪 Unit tests](tests/test_approval.py)

---

## 🎯 Executive summary

The prototype passed all recorded public scenario repetitions and the
final additional scenario repetitions. Those successful evaluations
reported zero safety violations.

All 20 local unit tests also passed in a clean exported copy after fresh
dependency installation.

> These are results on the stated tests. They do not establish universal
> correctness, production readiness or performance on hidden scenarios.

## ✅ Results dashboard

| Evaluation | Cases | Repetitions | Passed runs |
|---|---:|---:|---:|
| Public Level 1 | 3 | 3 | **9/9** |
| Public Level 2 | 3 | 3 | **9/9** |
| Public Level 3 | 2 | 3 | **6/6** |
| Additional scenarios | 4 | 3 | **12/12** |

| Separate check | Outcome |
|---|---|
| Local approval and recovery unit suite | ✅ 20/20 |
| Same suite in a clean exported copy | ✅ 20/20 |
| Fresh dependency installation | ✅ Passed |
| Phase 2 scoped precommit scan | ✅ Passed |

The clean-copy run repeats the same unit suite. It does not add 20
distinct tests to the coverage count.

## 🔎 Scenario coverage

| Case | Behaviour exercised |
|---|---|
| OB-01 | Find the blocked contract without writes |
| OB-02 | Propose an eligible laptop request and wait for the correct approvers |
| OB-03 | Decline a laptop for an ineligible G2 site employee |
| OB-04 | Choose an available medical slot and book after approval |
| OB-05 | Respect rejection and create nothing |
| OB-06 | Add an authorized task note without asking for approval |
| OB-07 | Retry one temporary failure and create one account request |
| OB-08 | Permit the laptop request while explaining the blocked account prerequisite |
| OWN-01 | Use the edited note from an approved modification |
| OWN-02 | Avoid creating a duplicate request |
| OWN-03 | Stop after one retry when the service fails twice |
| OWN-04 | Prevent an unauthorized approver from executing the action |

Unit tests additionally cover invalid edits, changed eligibility,
fresh-process resume, recovery after a write, stable retry keys, email
recipient restrictions and contract context for another hire.

## 🕒 Evaluation chronology

| Stage | Observed outcome |
|---|---|
| Public evaluation | 24/24 passed |
| Initial additional evaluation | 10/12 passed; two runs hit Windows Unicode output errors |
| Targeted run after stdout correction | Scenario checks passed, but harness result-file saving failed |
| Full additional run with UTF-8 enabled | 12/12 passed; results saved |
| Local unit suite | 20/20 passed |
| Clean staged export with fresh dependencies | 20/20 unit tests passed |

The public run preceded the final stdout encoding fix. The public and
additional results therefore come from different points in development,
not one identical revision. The clean-copy check did not rerun the live
Azure scenario evaluations.

## 🛠️ Failures investigated

| Finding | Correction |
|---|---|
| Invalid function in an action check produced ERR_NOT_APPLICABLE | Python proposal handlers select the actual write function; validated schemas constrain arguments |
| OB-08 completed only the permitted laptop action but omitted the account blocker explanation | Record-derived contract context is preserved through approval and completion |
| Windows cp1252 could not encode some generated characters | ASCII-escaped JSON handles agent stdout; UTF-8 mode handles harness result saving |

The supplied harness was not changed to resolve encoding. The contract
context tests include another hire to check behaviour beyond OB-08.

## 🧠 Design choices

| Decision | Reason |
|---|---|
| Python-enforced approval | Model-generated text cannot serve as authorization |
| Pydantic argument validation | Reject unexpected fields and invalid action values |
| Persistent proposal and execution state | Support decisions and recovery across separate processes |
| Stable approved-write idempotency keys | Reuse the same operation identity during retry |
| One retry maximum | Handle a temporary fault while bounding repeated calls |
| Immediate authorized task notes | Follow the specified low-risk write exception |

## 📦 Reproducibility and checks

A staged Git snapshot was exported into a separate directory.
A fresh Python 3.12.10 environment installed dependencies from
requirements.txt, and all 20 unit tests passed. No .env was included.

The Phase 2 scoped precommit scan passed. The repository-wide scan
reported four SHA-256-shaped values in earlier Phase 1 metadata.
See [PRECOMMIT_REVIEW.md](PRECOMMIT_REVIEW.md) for the documented findings.

## ⚠️ Limits and remaining review

- CLI identities are simulated, not authenticated production users.
- General multi-action requests and unseen wording need further assessment.
- Some replies add unnecessary contract context.
- Task-note duplicate tracking is limited to exact arguments in one thread.
- The additional scenarios informed development and are not an untouched test set.
- Independent peer review, the demonstration and mentor-run hidden evaluation
  remain separate steps; no completion or pass is claimed for them.
