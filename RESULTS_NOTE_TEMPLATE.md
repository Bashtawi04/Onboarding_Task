# Onboarding RAG Agent, ID 32 — One-page Results Note

**Evaluation scenario:** 2026-10-16 | **Status:** Offline functionality validated; Azure evaluation pending on your account.

## Solution
Approved source PDFs/Markdown -> cleaned document chunks -> Azure embeddings -> top-5 cosine retrieval -> Azure mini chat model. Scoped CSV access, task status, and dates are computed in Python and provided to the model separately. Outputs include source labels and JSONL audit records.

## Measured results (fill in after running `evaluate.py`)
- Official development cases run: **___ / 15**
- Relevant document retrieved in top 5: **___ / applicable cases** (note single gold hit vs full recall)
- Correct answers by *manual review*: **___ / 15 (___%)**
- Privacy refusal (DEV-14): **Pass / Fail**
- Family sponsorship unsupported-answer case (DEV-13): **Pass / Fail**
- Citations substantively support claims: **___ / ___**
- Chunk-size comparison, 400 vs 800 characters: **Not yet performed / results**

**Do not substitute automated string matching for manual judgment of answer correctness.**

## Verified offline checks
Six local tests pass, including employee isolation, manager-to-direct-report access, Sunday–Thursday dates, current ONB-05 corpus inclusion and exclusion of archived v1.0. Current prototype computes NH-2606 account due 2026-10-22, matching the task record; manager IT request due 2026-10-20 is a separate rule.

## Remaining limitations
CLI identity flags simulate trust and are not authentication. Citations are syntactically checked, but semantic source support requires review. Model answers have not been independently proven free from hallucination. This is a training prototype, not production HR deployment.

## Recommended next step
Run 15 official cases, manually grade gold points and refusals, then note the results for mentor signoff. Improve retrieval only if measured misses justify it.
