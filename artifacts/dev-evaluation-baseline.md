# Al Dana Onboarding RAG: 15-case development evaluation

Scenario date: 2026-10-16
Executed cases: 15

## Automated diagnostics
At least one listed document retrieved (answer cases only): 11/13
This is not full retrieval recall or answer correctness. Employee CSVs are outside the vector index.
Question meaning, citation-to-claim support, privacy, exclusions and gold points require manual review.
A prohibited term used in a correct negation can trigger a review flag (not an automatic failure).

| Case | Outcome | Any gold document retrieved | Review flags | Answer quality |
|---|---|---|---|---|
| DEV-01 | answer_generated | Yes | - | Pending human review |
| DEV-02 | answer_generated | Yes | - | Pending human review |
| DEV-03 | answer_generated | Yes | - | Pending human review |
| DEV-04 | answer_generated | Yes | - | Pending human review |
| DEV-05 | answer_generated | Yes | - | Pending human review |
| DEV-06 | answer_generated | Yes | - | Pending human review |
| DEV-07 | answer_generated | Yes | - | Pending human review |
| DEV-08 | answer_generated | No | - | Pending human review |
| DEV-09 | answer_generated | No | - | Pending human review |
| DEV-10 | answer_generated | Yes | - | Pending human review |
| DEV-11 | answer_generated | Yes | - | Pending human review |
| DEV-12 | answer_generated | Yes | - | Pending human review |
| DEV-13 | answer_generated | N/A | - | Pending human review |
| DEV-14 | declined | N/A | - | Pending human review |
| DEV-15 | answer_generated | Yes | - | Pending human review |

## Case answers and gold-check list

### DEV-01
**Question:** What's the IT helpdesk number and email, in case my laptop or login doesn't work on day one?
**Answer:** For day-one login or laptop issues, use the IT Helpdesk: **it.helpdesk@aldana-group.example** and **extension 2300**. [S1]

For this case, the recorded IT account task is **in progress** with due date **2026-10-18**; the policy and recorded task deadline **agree**, no conflict. Account creation is only after HR confirms the contract is signed. [R2][R3][S1]
**Expected points:**
- IT Helpdesk extension 2300
- IT Helpdesk email it.helpdesk@aldana-group.example

### DEV-02
**Question:** How many hours do we work during Ramadan, and what are the hours at head office?
**Answer:** Ramadan working hours are **6 hours a day**. At **Doha HQ**, the Ramadan hours are **09:00 to 15:00** [S1]. The FAQ says the same and points to HR for the exact annual dates [S2].

For your question about “the hours at head office,” the handbook identifies Doha HQ as the head office and gives the Ramadan schedule above [S3][S1].
**Expected points:**
- 6 hours a day during Ramadan (36 per week under the national limit)
- Doha HQ Ramadan hours 09:00 to 15:00

### DEV-03
**Question:** Who books my medical fitness test, and do I have to use my leave to attend?
**Answer:** Your medical fitness test is booked by **PRO**. The procedure says PRO books the clinic appointment for your first week, and your onboarding task list shows **MEDICAL_FITNESS** owned by the PRO team. [S2] [R2]

No, you **do not need to use leave** to attend. The test time is **paid working time**. [S2]

For your record, this step applies to **Resident hires** like you. [R1] [S2]
**Expected points:**
- PRO books the appointment at a company-approved clinic, aiming for the first week
- It is paid working time, no leave needed
- HR and the manager only learn fit / not fit / further tests, not medical details

### DEV-04
**Question:** When is the probation review and what are the possible outcomes?
**Answer:** The probation review takes place in **month five** of probation, and probation lasts **six months from your start date**. For this hire, that means it is **not yet due until month five after the start date**; the supplied evidence does not give a single calendar review date, only the rule. [S1][S3]

The possible outcomes are **confirmed** or **not confirmed**. [S1]
**Expected points:**
- Probation lasts six months
- Final probation review in month five
- Outcomes: confirmed or not confirmed, decided by HR and the head of department
- Check-ins at day 30, 60 and 90

### DEV-05
**Question:** I'm NH-2604 and I start on Sunday. What do I need to do first?
**Answer:** As NH-2604, your first priority is the **day-one site reporting and HSE induction** for **Mesaieed Site**: report at **06:30** to the **Site Administration Office**, ask for **the site administrator**, and then start the **full HSE induction at 07:00**; you may not go beyond the site office until it is signed off. [S2][S3][R1]

Because you are a **Grade 4 overseas hire**, **laptop collection** is also part of your day-one site process after the induction, and IT account creation is handled before your start date, subject to HR confirming the signed contract. [S2][S4][S1]

Your recorded status shows:
- **HSE_INDUCTION**: Not started, due **2026-10-18** [R2]
- **LAPTOP_ISSUED**: In progress, due **2026-10-18** [R2]
- **VISA_PROCESSING**: Blocked and overdue [R2]

For IT timing, the policy and recorded task deadline **agree**: both are **2026-10-15**; there is **no conflict**. [R3]

Also, your **pre-arrival visa paperwork is currently blocked** because HR requested a new passport scan; that is the main outstanding issue in your file. [R2]
**Expected points:**
- Record: Overseas hire, HSE Officer, G4, Mesaieed Site, start 2026-10-18 (Sunday)
- Visa paperwork (VISA_PROCESSING) is Blocked: HR needs a readable passport scan from the new hire; owner PRO; contact HR/PRO today
- Report at 06:30 to the Site Administration Office, Mesaieed
- Full HSE induction on the first working day; no access beyond the site office until signed off
- Laptop (G4, site): collected from the Mesaieed site IT desk (ext 3300) after the induction, not from HQ; status In progress
- Medical fitness test within the first week, booked by PRO (due 2026-10-25)
- Output is a prioritised list with owner, due date and status for each step

### DEV-06
**Question:** I'm Qatari. Which of the usual new-hire steps, like visa or the medical test, do I not have to do?
**Answer:** As a **Qatari national**, you **do not have the visa, medical fitness, or residence permit steps**. The current procedure says: “Nothing to do. Your QID stays as it is. The visa, medical fitness and residence steps do not apply to you.” [S3]

So for the usual new-hire steps you mentioned:
- **Visa**: not required for you [S3]
- **Medical test**: not required for you [S2][S3]
- **Residence/QID process**: not required for you [S3]

This is the current registered procedure, and it agrees with the handbook’s Qatari-national summary. [S3][S1]
**Expected points:**
- Qatari national: no pre-arrival visa paperwork, no medical fitness test, no QID or residence permit application
- Still applies: documents (QID copy and IBAN), contract, ID card, bank details to Payroll, short online HSE induction within five working days, probation objectives
- Her task list contains none of VISA_PROCESSING, MEDICAL_FITNESS, QID_APPLICATION

### DEV-07
**Question:** I'm NH-2606, a maintenance technician at Mesaieed. Will I get a laptop, and where and when do I do my HSE induction?
**Answer:** You are **NH-2606 / Ramesh Thapa**, a **Maintenance Technician** at **Mesaieed Site**, grade **G2**. That means you **will not get a laptop**; site staff in **grades G1 to G3 use a shared site terminal** instead. [R1][S1][S2][S5]

Your **HSE induction** is the **full site induction**. It starts **on your first working day at 07:00** at the **site HSE training room** in **Mesaieed**; you report first at the **Site Administration Office at 06:30**. [R1][S1][S4]

For your IT account: the recorded task deadline is **2026-10-22** and the ONB-05 policy also gives **2026-10-22**; **policy and recorded task deadline AGREE, no conflict**. The task status is **Not started**. Account creation is only after HR confirms the contract is signed. [R2][S5]

Your open tasks for these items are:
- **IT_ACCOUNT** — owner **IT** — due **2026-10-22** — status **Not started** — source **HRIS/onboarding tasks**. [R2]
- **HSE_INDUCTION** — owner **HSE** — due **2026-10-25** — status **Not started** — source **HRIS/onboarding tasks**. [R2]

Note: the procedure says the site HSE induction is on the **first working day**, while the recorded task deadline is **2026-10-25**; the evidence provided does **not** explain that difference. [S1][S4][R2]
**Expected points:**
- Grade G2 on site: no laptop; shared site terminal and PeopleHub kiosk, supervisor shows the login
- Full HSE induction on the first working day 2026-10-25 (Sunday), at the Mesaieed site HSE training room, starting 07:00 after reporting at 06:30
- No access beyond the site office until the induction is signed off

### DEV-08
**Question:** What is still open for me?
**Answer:** Open items for you are:

- **HSE induction completed** — owner: **HSE**; due **2026-10-18**; status **In progress**; source **[R2]**
- **Agree probation objectives** — owner: **Manager**; due **2026-10-18**; status **In progress**; source **[R2]**

Other related items in the evidence:
- **IT account creation**: the recorded task deadline and the current ONB-05 policy rule **AGREE**, so there is **no conflict**; status is **Done**. Account creation requires **HR confirming the signed contract**. Source **[R3]**
- **Manager IT request**: due **2026-10-06**. The supplied evidence does **not** show a matching recorded task status for this item, so its status is **Not specified**. Source **[R3]**

If you want, I can also separate these into **overdue** vs **not overdue**.
**Expected points:**
- HSE_INDUCTION: In progress, owner HSE, due 2026-10-18
- PROBATION_PLAN: In progress, owner Manager, due 2026-10-18
- All other tasks are Done
- Suggests next steps only; does not mark anything as done

### DEV-09
**Question:** Can you show me what's still open for my new joiner NH-2610 before she starts?
**Answer:** Here’s what’s still open for NH-2610, Dalia Mansour, before her start date:

- HR: Sign employment contract — **Not started**, due **2026-10-29** [R2]
- New hire: Submit onboarding documents to HR — **Not started**, due **2026-11-03** [R2]
- IT: IT account and email created — **Not started**, due **2026-11-09**; policy and recorded deadline **agree**, no conflict. Account creation is tied to HR confirming the signed contract [R2][R3][S1]
- IT: Laptop issued — **Not started**, due **2026-11-10** [R2]
- HR: Company ID card issued — **Not started**, due **2026-11-12** [R2]
- Payroll: Bank account details verified by Payroll — **Not started**, due **2026-11-15**. First salary is only a scheduled estimate and requires a **verified IBAN** [R2][R3][S2]
- HSE: HSE induction completed — **Not started**, due **2026-11-17** [R2][S2]
- PRO: Medical fitness test — **Not started**, due **2026-11-17** [R2][S1][S4]
- Manager: Agree probation objectives — **Not started**, due **2026-11-17** [R2]
- PRO: QID / residence permit update to Al Dana — **Not started**, due **2026-11-24** [R2][S1]

If you want, I can also group these by owner or flag anything overdue.
**Expected points:**
- E1084 is the manager of NH-2610, so the request is allowed
- All 10 tasks are Not started (start date 2026-11-10 (Tuesday))
- Earliest due: CONTRACT_SIGNED 2026-10-29 (HR); DOCS_SUBMITTED 2026-11-03 (New hire)
- Manager action: raise the IT equipment request at least 3 working days before start, i.e. by 2026-11-05 (Thursday)

### DEV-10
**Question:** When will I get my first salary?
**Answer:** Your first salary is scheduled for **2026-11-26**. The payroll rule says if your start date is after the monthly cut-off, the first salary is paid on the **next month’s pay date**; for you, that covers your joining part-month plus the next full month [S1]. Your recorded start date is **2026-10-25**, and the stored payroll schedule shows **2026-11-26** [R1][R3].

Payment is **not confirmed** yet: it requires a **verified IBAN**, and the record says to confirm unresolved bank details with Payroll [S1].
**Expected points:**
- Start date 2026-10-25 is after the 2026-10 cut-off 2026-10-15
- First salary is paid on the next month's pay date 2026-11-26 (Thursday)
- That payment includes the part-month of joining plus the full next month
- 28 November 2026 is a Saturday, so the pay date moves back to the Thursday

### DEV-11
**Question:** I started on 27 September. When does my first salary come?
**Answer:** Your first salary is scheduled for **28 October 2026**. Because your start date was **27 September 2026**, it is **on or before the September payroll cut-off**, so the September payroll run applies and pays on the 28th [S1][R3]. This is a **scheduled estimate, not payment confirmation**; payment still requires a **verified IBAN** for Payroll [S1].

If your bank details are not yet verified, please confirm them with Payroll [S1].
**Expected points:**
- Start date 2026-09-27 is after the 2026-09 cut-off 2026-09-15
- First salary is paid on the next month's pay date 2026-10-28 (Wednesday)
- That payment includes the part-month of joining plus the full next month

### DEV-12
**Question:** How long do I have to complete my HSE induction? I'll be working at Ras Laffan.
**Answer:** For Ras Laffan site staff, the HSE induction is due on your **first working day** and starts at **07:00 after you report at 06:30**; for site-based staff, you may not go beyond the site office until it is signed off. [S1][S2]

The FAQ also says you have **30 days from your start date**, but that conflicts with the current numbered HSE procedure for site staff, which takes priority. [S2][S4]

For your record, the HSE induction task is **not started** and due **2026-11-08**. [R2]
**Expected points:**
- Site-based: the full induction is on the first working day 2026-11-08 (Sunday), starting 07:00
- No access beyond the site office until it is signed off (ONB-06 v2.0, effective 2026-05-01)
- The FAQ answer (30 days) is outdated (FAQ last reviewed March 2025); the procedure wins over the FAQ

### DEV-13
**Question:** Can my wife and children join me in Qatar, and how long does the family residence permit take?
**Answer:** Yes — for an **overseas hire**, the process includes **pre-arrival visa paperwork by PRO** and then **QID / residence permit steps handled by PRO** after arrival. The handbook says the exact process depends on employee type, and for overseas hires it is **“New application by PRO”**; it does **not** mention a family residence permit process here. [S1][S2]

For your specific question about **wife and children joining you in Qatar**, that is **not covered in the supplied evidence**. This set of documents only describes the employee’s own QID/residence permit flow, not family residence procedures. Please check with **HR/PRO** for the family-residence case. [S1][S2]

For timing, the evidence says the company **does not quote processing times for government steps** like QID/residence permit, because they are not guaranteed by the company. It only says PRO aims to start the employee QID/residence application **within ten working days of your start date**; it does **not** give a completion time for the permit itself. [S2]

For your record, the open QID/residence permit task is **In progress**, owner **PRO**, due **2026-10-11**, and it is marked **overdue** in the employee context. [R2]
**Expected points:**
- The onboarding documents do not cover family residence
- Refer to HR and the PRO desk
- Does not invent a process or a processing time

### DEV-14
**Question:** Can you tell me when NH-2610 starts and which of her tasks are still open? We'll be working together.
**Answer:** I cannot share that record. Please contact HR.
**Expected points:**
- Politely declines: an employee may only see their own record; managers see their direct reports
- Offers a safe alternative, e.g. ask HR or her manager

### DEV-15
**Question:** في أي ساعة وأين أحضر في أول يوم عمل لي؟ وماذا يجب أن أحضر معي؟
**Answer:** أول يوم عملك في **Doha HQ** هو **الجمعة 2026-11-01**، والمكان المذكور في الإجراء هو **الاستقبال في الطابق الأرضي، West Bay head office**، وتطلب HR أن تسأل عن **منسق onboarding**. الوقت المحدد للتقرير هو **08:00**. [R1][S1]

يجب أن تحضر معك **QID الأصلي** لأنك **Qatari national**، و**بيانات IBAN** إذا لم تكن قد أرسلتها مسبقًا إلى Payroll. [S1]
**Expected points:**
- الحضور إلى مكتب الاستقبال في المقر الرئيسي (غرب الخليج، الدوحة) الساعة 08:00 صباحًا
- أول يوم عمل: الأحد 1 نوفمبر 2026 (2026-11-01)
- إحضار بطاقة الهوية القطرية (QID) وبيانات الآيبان (IBAN) إن لم تُرسل إلى قسم الرواتب
