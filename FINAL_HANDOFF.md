# Final handoff | Onboarding Agent ID 32

## Files to give your mentor

1. Source folder (`ask.py`, `build_index.py`, `onboarding/`, `tests/`, `evaluate.py`, `requirements.txt`), fictional `data/`, and `README.md`.
2. `RESULTS_NOTE.md` with *baseline* measured evidence and clearly marked unmeasured items.
3. `artifacts/dev-evaluation-baseline.md` as the recorded 15-case run from 20 October.
4. A roughly 10-minute CLI demo: document answer, personalized task answer, denied access, missing-information refusal.

**Do not upload** `.venv/`, API keys, `.env`, or the large `artifacts/vector-index.json` to the mentor unless they explicitly ask and the organization's data/security rules permit it.

## Important: this package is NOT your VS Code workspace

Your existing Windows working folder is:
`C:\Users\Yahya\Downloads\onboarding-starter\onboarding-starter`

Keep using that folder with its `.venv` and Azure index. If applying the updated scripts, copy **only** `ask.py`, `onboarding/records.py` and `onboarding/validation.py` from this handoff into the corresponding locations in the existing workspace after backing up the originals. You do **not** need to unzip this package as a separate VS Code project or rebuild an existing 700-character index merely because those scripts changed.

## One-time final validation

In a terminal whose prompt ends in the existing project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluate.py
```

The evaluation asks for your Azure key and makes billed API requests. It overwrites `artifacts/dev-evaluation.md` and `artifacts/dev-evaluation.json`; save your baseline copy first. Check DEV-11 and DEV-15 first, then incomplete cases. Update `RESULTS_NOTE.md` only after verifying the outputs.

## 400 vs 800 retrieval comparison, if required by the mentor

**Caution:** Requires embeddings for each size and another **30 total answer-generation calls** across the two evaluation runs. Save the existing vector index first and restore it after the experiment. These commands are for the original Windows project folder.

```powershell
Copy-Item artifacts\vector-index.json artifacts\vector-index-700-backup.json -Force
.\.venv\Scripts\python.exe -m onboarding prepare --size 400 --overlap 100
.\.venv\Scripts\python.exe build_index.py --size 400
.\.venv\Scripts\python.exe evaluate.py
Copy-Item artifacts\dev-evaluation.json artifacts\dev-evaluation-400.json -Force

.\.venv\Scripts\python.exe -m onboarding prepare --size 800 --overlap 100
.\.venv\Scripts\python.exe build_index.py --size 800
.\.venv\Scripts\python.exe evaluate.py
Copy-Item artifacts\dev-evaluation.json artifacts\dev-evaluation-800.json -Force

Copy-Item artifacts\vector-index-700-backup.json artifacts\vector-index.json -Force
```

Compare `has_any_gold_retrieval` across the 13 applicable cases. Also manually inspect answer correctness: an any-hit diagnostic is not a final quality score. `dev-evaluation.json` files contain fictional questions and generated answers, not your API key.

## Demo flow

- **Knowledge retrieval:** employee asks for IT Helpdesk extension and email; show the cited source.
- **Personalization:** NH-2606 asks about laptop and HSE; show site and grade-based guidance.
- **Privacy:** NH-2607 asks for NH-2610 details; show denial and no record disclosure.
- **Honest unknown:** an overseas hire asks about family sponsorship duration; show the answer is not in the corpus.

## Boundaries

This is a read-only training prototype built using simulated IDs, not real organizational sign-in. It does not create tickets, update HR systems, or send notifications. The business value is a *potential* benefit, not measured savings.
