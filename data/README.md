# Data card: Onboarding Agent (ID 32)

**ALL DATA IS SYNTHETIC.** Al Dana Group W.L.L., its people, systems, phone extensions, email addresses (`@aldana-group.example`) and every document in this folder are fictional. The documents are written to behave like real company documents. They are not official guidance. Anything that looks like a legal or government statement is a short, deliberately general summary for training (see `mol_guidance/`).

Snapshot date of the data: **2026-10-01**. "Today" for the eval questions: **2026-10-16**. Currency QAR, dates ISO `YYYY-MM-DD`. Qatar weekend is Friday-Saturday; the company working week is Sunday-Thursday.

## Documents (text to retrieve from)

| Path | What it is | Real system it stands in for |
|---|---|---|
| `handbook/New_Hire_Handbook.pdf` | HB-01 v3.0, 9 pages, bilingual cover | HR intranet / SharePoint handbook |
| `procedures/ONB-01_Before_You_Arrive.pdf` | documents to send, by employee type | HR procedure library |
| `procedures/ONB-02_First_Day_and_ID_Card.pdf` | day one, ID card, QID steps by type | HR procedure library |
| `procedures/ONB-03_Medical_Fitness_and_Health_Insurance.pdf` | medical test, group insurance | HR procedure library |
| `procedures/ONB-04_Payroll_Bank_Account_and_WPS.pdf` | bank account, cut-off, first-salary rule | Finance / payroll procedure library |
| `procedures/ONB-05_IT_Access_and_Equipment.md` | current IT procedure (v2.1), intranet page | IT knowledge base |
| `procedures/ONB-06_HSE_Induction.pdf` | HSE induction, site vs office | HSE management system |
| `procedures/ONB-07_Probation_and_First_90_Days.md` | probation, check-ins, review | HR intranet |
| `procedures/archive/ONB-05_IT_Access_v1.0.pdf` | an old version kept in the archive | what real shared drives contain |
| `faq/new_hire_faq.md` | informal intranet FAQ, 15 Q&As | intranet FAQ page |
| `mol_guidance/mol_digest_onboarding.md` | one-page synthetic summary of general Qatar labour rules | official Ministry of Labour (MOL) sources |
| `arabic/Welcome_Letter_AR_EN.pdf` | one-page bilingual welcome letter | HR letter template |
| `policy_register.csv` | which version is current, document types, order of authority | document management system |

Order of authority when documents disagree: **Procedure (rank 1) > Handbook (rank 2) > FAQ (rank 3)**. A document with status `Superseded` is history only.

## Tables (`hris/`, stand in for the HRIS "PeopleHub")

`new_hires.csv` (12 rows): `new_hire_id` (NH-2601..NH-2612), `full_name_en`, `full_name_ar` (blank for non-Arabic names), `job_title`, `department`, `grade` (1-10), `location` (Doha HQ / Mesaieed Site / Ras Laffan Site), `employee_type` (Overseas hire / Resident hire / Qatari national), `start_date`, `manager_id` and `buddy_id` (real ids from `employees.csv`), `work_email` (blank until IT creates the account).

`onboarding_tasks.csv` (117 rows): `task_id`, `new_hire_id`, `task_code` (e.g. CONTRACT_SIGNED, DOCS_SUBMITTED, VISA_PROCESSING, IT_ACCOUNT, LAPTOP_ISSUED, ID_CARD, HSE_INDUCTION, MEDICAL_FITNESS, QID_APPLICATION, BANK_ACCOUNT, PROBATION_PLAN), `task_name`, `owner_team` (HR / PRO / IT / Payroll / HSE / Manager / New hire), `due_date`, `status` (Done / In progress / Not started / Blocked), `completed_on` (only when Done), `notes`.

`payroll_calendar_2026.csv` (12 rows): `month` (YYYY-MM), `cutoff_date`, `pay_date`.

`contacts_directory.csv`: `team`, `contact_role`, `email`, `extension`, `hours`, `location`.

`employees.csv`, `departments.csv`, `locations.csv`, `salary_bands.csv`: the shared company files (100 employees E1001-E1100). Managers and buddies of the new hires are taken from here.

`policy_register.csv`: `doc_id`, `title`, `version`, `status` (Current / Superseded), `effective_from`, `owner`, `doc_type` (Procedure / Handbook / FAQ), `authority_rank` (1 = highest), `file_path`.

## Things to know

- The PDFs were produced from word-processor layouts, so they contain running headers and footers ("Page 2 of 2", "fictional training data") that end up in the extracted text. Real documents do the same.
- Statuses in `onboarding_tasks.csv` are consistent with the start dates and with today (2026-10-16): hires who have started mostly have Done tasks, future hires mostly have Not started.
- The agent may only see the record of the person asking (new hires: their own; managers: their direct reports). See the brief.
- There are a few deliberate gotchas in the data. Finding them is part of the exercise.

## Eval

`eval/dev_set.jsonl`: 15 questions in JSON Lines. Fields: `id`, `category`, `language`, `today`, `asker`, `input`, `expected_behavior` (answer / decline / say_not_in_documents), `gold_points`, `gold_sources`, `must_not`, `notes`.
