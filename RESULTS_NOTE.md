# Onboarding Agent (ID 32) | Development results note

**As-of scenario:** 16 October 2026  
**Scope:** Al Dana Group fictional dataset; Python CLI + Microsoft Azure OpenAI prototype, **not** a production HR service.

## What works

- Approved PDFs/Markdown -> clean text -> 700-character chunks -> Azure embeddings -> top-5 cosine retrieval -> Azure-generated answer and source labels.
- Employee/task CSV records remain outside the vector index. Python enforces simulated own-record/direct-manager access and calculates workdays and conditional salary dates.
- The user's Windows run reported **17/17 offline tests passing** before the latest reasoning changes; the **13 bundled tests** have also passed locally. Changes still require a final rerun on the user's environment.
- **15/15** official development cases executed, **14** generated responses and **1** declined unauthorized request (DEV-14). At least one listed expected document was among the retrieved results in **11/13** applicable cases (**84.6% any-hit diagnostic**, not total recall or answer accuracy).

## Manual review of the *baseline* 15 answers

| Classification | Cases | Reviewer note |
|---|---|---|
| Substantially meets visible expected points | DEV-01, 02, 08, 12, 13, 14 | DEV-13 safely says family residence is outside the evidence, but adds unnecessary discussion. |
| Useful but incomplete | DEV-03, 04, 05, 06, 07, 09, 10 | Missing at least one expected policy/condition or an actionable detail. |
| Material accuracy error | DEV-11, 15 | DEV-11 reversed 27 Sep vs 15 Sep cutoff; DEV-15 said Friday for Sunday 1 Nov. |

This is a conservative, qualitative review of the **original** `dev-evaluation.md` answers, **not a certified 70% accuracy score**. In particular, citation labels have been checked for existence, **not independently verified as supporting every claim**.

## Improvements prepared after the baseline

- Python now sends explicit joining-month cutoff, comparison, weekday and start-date weekday to the model rather than relying on calendar inference.
- A new `onboarding/validation.py` module contains reusable checks that correct an incorrect weekday when adjacent to a trusted ISO start date; a detected inverted payroll-cutoff explanation falls back to structured Python facts.
- Prompt instructions now emphasize complete multipart responses and task priority. **The 15 Azure cases have not yet been rerun with these changes.**

## Chunk-size experiment: preliminary offline preparation

| Size | Number of chunks | Source documents | Top-5 retrieval performance |
|---|---:|---:|---|
| 400 characters | 149 | 11 | **Not measured** |
| 700 characters (baseline) | 80 | 11 | 11/13 any listed gold document hit |
| 800 characters | 71 | 11 | **Not measured** |

The 400/800 chunks were prepared and counted offline. Proper comparison still requires two Azure embedding indexes and identical evaluation queries, with the same model, `k=5` and other settings held constant. Chunk count alone says nothing about retrieval quality.

## Remaining sign-off steps

1. On the existing Windows project, apply reviewed fixes and rerun automated tests and all 15 Azure cases.
2. Manually check answer content, citations, denied access, missing information, and Arabic date accuracy; score against gold points.
3. Run 400/800 experiment or document why it was deferred, then finish the mentor demo. Never label this prototype "production-ready": caller IDs simulate identity, and generated citations need semantic validation.
