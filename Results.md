# Onboarding RAG Assistant — Results
Author: Yahya
Date: 23 October 2026

## What I built
A Python assistant for the fictional Al Dana onboarding dataset.
It retrieves relevant policy passages, combines them with authorized
employee records, and uses an Azure-hosted language model to answer
with source citations.

Employee records are looked up directly from CSV files. Access checks
allow an employee's own record or a manager's direct report.
These are simulated identities, not production authentication.

## Approach
- Extract text from PDF and Markdown documents.
- Exclude superseded policies using document metadata.
- Create embeddings with text-embedding-3-small.
- Store embeddings and source metadata in a local JSON index.
- Retrieve five distinct pages using cosine similarity.
- Calculate payroll and working-day facts in Python.
- Generate answers with gpt-5.4-mini and record an audit trail.

## Experiments and verification
Compared 400-character and 800-character chunks with 100-character
overlap. Selected 400 characters because the earlier comparison
retrieved expected documents more consistently.

All 17 local automated tests passed.

The latest full evaluation completed all 15 development questions:
14 answers were generated and one privacy request was declined.
For the 13 questions expecting an answer, at least one expected
policy document was retrieved for 12 questions.

These are retrieval and execution results, not an answer-accuracy score.
Zero automated flags does not prove that every answer is correct.

## Subsequent changes
Added authorized open-task names to broad task searches.
A targeted test then retrieved the HSE procedure, but still missed
the probation procedure.

Strengthened completeness instructions. A targeted probation test
included duration, final review, outcomes and decision makers,
but still omitted the Day 30/60/90 check-ins.

These changes have targeted checks, not a new full evaluation.

## Limitations and next steps
Some answers omit details, include unrelated information or miss
relevant procedures. Citation-label validation does not prove that
every claim is supported.

The prototype suggests actions; it does not update HR records.
Voice integration and a web interface are not included.

Next improvements: better retrieval for broad questions, systematic
answer-completeness checks, and testing on unseen questions.

<!-- mentor-review-results:start -->
## Mentor review follow-up: 29 October 2026

### Execution results

- Local unit tests: 35 passed.
- Development evaluation: 14 of 15 cases completed without runtime errors.
- Fresh evaluation: 10 of 10 cases completed without runtime errors.
- DEV-06 initially failed with a JSONDecodeError. A separate retry
  generated an answer. The original failure remains in the saved evaluation.
- These counts measure execution, not factual correctness.

### Fresh-question expected-point review

Scoring: 1 when the complete expected point is present; otherwise 0.
Compound points require all their listed elements.
This is an AI-assisted review for the author to verify against the saved
answers and source documents, not an independent human assessment.

| Case | Points met |
|---|---:|
| NEW-01 | 2/3 |
| NEW-02 | 2/3 |
| NEW-03 | 2/2 |
| NEW-04 | 4/5 |
| NEW-05 | 3/3 |
| NEW-06 | 3/3 |
| NEW-07 | 3/3 |
| NEW-08 | 2/2 |
| NEW-09 | 2/2 |
| NEW-10 | 3/3 |
| Total | 26/29 |

Expected-point coverage: 89.7%. This is not an overall accuracy score.
Scores are in:
`artifacts/fresh-dense-20261029-153806-276606/scores.csv`.

Missing points: PeopleHub kiosk in NEW-01, VPN access in NEW-02,
and confirmed/not confirmed outcomes in NEW-04.

### Remaining limitations

- DEV-04 omits the requested probation check-ins.
- DEV-05 still puts day-one reporting ahead of resolving the visa blocker
  in the generated explanation, although the table preserves the blocker.
- DEV-07 begins with a contradictory "Yes" before saying no laptop.
- DEV-13 begins with an unsupported "No" about family eligibility;
  the evidence establishes uncertainty, not ineligibility.
- Some answers repeat records, add unrelated advice, omit dates,
  or incorrectly describe compatible guidance as overridden.
- JSON output parsing can fail. The successful DEV-06 retry does not
  establish that the underlying formatting issue is resolved.
- Citation-label validation does not prove that a source supports a claim.
- The fresh questions have now informed development decisions and should
  not be described as an untouched held-out test set.

### Implemented changes

- Shared environment-based Azure configuration.
- Python-rendered task names, owners, deadlines and statuses.
- Recorded blocker notes and separate manager equipment-request deadlines.
- Regression tests for weekday, payroll and IT-conflict safeguards.
- Adjacent and grouped citation parsing checks.
- Clarification or denial for named-colleague requests.
- Saved evaluation answers and expected-point scoring.
- A narrow record-only route for supported question patterns.
  It checks access first and returns recorded facts without Azure calls.
  Other wording continues through RAG.

The narrow record-only route was verified separately with the manager
task-list question and the pre-start blocker question. It does not guarantee
equivalent behavior for every paraphrase.

Hybrid search and reranking remain optional experiments. These final dense
evaluation results do not establish an improvement from either option.
<!-- mentor-review-results:end -->
