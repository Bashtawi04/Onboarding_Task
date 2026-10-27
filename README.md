# Onboarding RAG Assistant

### Employee guidance grounded in company policies and records

**Yahya AlBashtawi · Cerebrum Internship · Agent Bank ID 32**

> A Python assistant that brings together company documents, employee records, and Azure AI to explain onboarding tasks, deadlines, and policies.

---

## 📌 Project Overview

New employees often need to check several documents or speak to different teams to understand what they should do next.

This project brings that information together. Employees can ask about equipment, HSE induction, payroll, probation, and outstanding onboarding tasks. The assistant finds relevant policy passages and combines them with the employee records the requester is permitted to access.

The project uses **Retrieval-Augmented Generation (RAG)**: it retrieves supporting information first, then asks the model to explain it.

| Project detail | Description |
|---|---|
| Scenario | Employee onboarding at the fictional Al Dana Group |
| Users | New employees and permitted managers |
| Interface | Python command line |
| AI platform | Model deployments hosted in Microsoft Azure |
| Knowledge sources | Supplied PDF and Markdown documents |
| Employee information | Structured CSV records |
| Current status | Working prototype with documented limitations |

The assistant provides guidance. It does not complete tasks, send emails, submit requests, or change HR records.

---

## 🎯 What the Assistant Helps With

| Example question | Information needed |
|---|---|
| “What is still open for me?” | Recorded tasks, statuses, owners, and deadlines |
| “When will I receive my first salary?” | Joining date, payroll rules, and payment calendar |
| “Do I get a laptop?” | Equipment policy and employee circumstances |
| “When must I complete HSE induction?” | Location-specific guidance and recorded tasks |
| “What happens during probation?” | Probation duration, check-ins, review, and decision rules |
| “Can I see another employee’s tasks?” | Requester identity and permitted record access |

The supplied company documents and employee records are fictional training data.

---

## 🏗️ Architecture & Pipeline


[Open the full-size architecture diagram](architecture.png)

### Workflow A: Prepare the documents

The application reads the supplied documents, extracts their text, and divides it into overlapping chunks.

Azure’s embedding model converts each chunk into a numerical vector that represents aspects of its meaning. The application saves these vectors alongside the source text and metadata in a local JSON index.

**Purpose:** make the documents searchable by meaning.

### Workflow B: Answer a question

The application checks access, reads the permitted employee’s records, calculates supported dates, and searches for relevant policy passages.

It sends those facts and passages to the Azure answering model. The answer is displayed with source references and recorded for review.

**Purpose:** combine company guidance with the employee’s recorded situation.

### Three different responsibilities

| Component | Responsibility | Example |
|---|---|---|
| Python logic | Handle exact records and business rules | Find outstanding tasks and calculate supported deadlines |
| Embedding model | Help locate relevant information | Find payroll passages for a salary question |
| Answering model | Explain the supplied evidence | Present the payment date, conditions, and sources |

**RAG does not train the answering model on the documents. It supplies relevant evidence when a question is asked.**

---

## ⚙️ Core System Layers

### 1. Request & Access Control

**Main files:** `ask.py`, `onboarding/records.py`

The application accepts three inputs:

- The requester’s ID.
- The target employee’s ID.
- The question.

It checks the prototype’s self-access and manager/direct-report rules before retrieving personal context. Requests that do not meet those rules are declined.

**Why this is handled in code:** the language model should not decide who is allowed to access an employee record.

**Current boundary:** command-line IDs simulate identity. They are not a real sign-in system.

### 2. Employee Context & Business Rules

**Main file:** `onboarding/records.py`

The application reads employee and task records to find:

- Who the employee is.
- Their grade, location, joining date, and employee type.
- Which onboarding tasks remain open.
- Each task’s recorded owner, deadline, and status.
- The information needed for supported payroll and IT date calculations.

Employee records stay outside the vector index. They are retrieved by exact identity rather than similarity.

**Why:** a policy explains what should happen. A task record shows what is actually recorded for a person.

The scenario uses **16 October 2026** as its reference date. Overdue status is evaluated against that date, not automatically against the day of a demonstration.

### 3. Document Preparation

**Main files:** `onboarding/documents.py`, the `onboarding` command-line package

The preparation process:

1. Selects documents using the supplied document-selection rules.
2. Extracts text from PDF and Markdown files.
3. Keeps source and page information where available.
4. Splits the text into overlapping chunks.
5. Saves the prepared chunks for embedding.

**Why overlap is useful:** information can fall across a chunk boundary. Repeating part of the text helps retain the surrounding context.

Extracted tables and Arabic text should be checked before relying on the resulting index.

### 4. Embedding & Vector Storage

**Main file:** `build_index.py`

The script sends document chunks to the Azure `text-embedding-3-small` deployment.

The returned vectors are saved with their text and metadata in:

```text
artifacts/vector-index.json
```

**Why:** saving the vectors allows the application to reuse the prepared knowledge base instead of embedding every document for every question.

This is a lightweight local index, not a managed vector database.

### 5. Evidence Retrieval

**Main file:** `ask.py`

For an authorized question, the application:

1. Builds a search query from the question and relevant employee context.
2. Adds outstanding task names for supported broad task questions.
3. Creates a query embedding using the same embedding model.
4. Compares the query vector with stored document vectors using cosine similarity.
5. Collects up to five distinct source pages.
6. Attaches source labels and passes the evidence to the answering model.

**Why select distinct pages:** several highly ranked chunks may come from the same page. Selecting distinct pages reduces repetition and leaves room for other useful sources.

### 6. Answer Generation

**Main file:** `ask.py`

The application calls the Azure `gpt-5.4-mini` deployment through the native OpenAI Python SDK.

The model receives:

- The user’s question.
- Authorized employee context.
- Retrieved document passages.
- Source labels.
- Instructions on how to answer.

These instructions cover policy precedence, missing evidence, task status, date handling, and answer completeness.

**Why:** the model should explain the supplied evidence instead of guessing company-specific rules from general knowledge.

The instructions help reduce errors, but they do not guarantee that every answer will be complete or factually correct.

### 7. Validation, Audit & Evaluation

**Main files:** `ask.py`, `evaluate.py`, `tests/`

The application checks citation labels, records local audit information, and supports two kinds of testing:

- **Unit tests:** check deterministic code behavior.
- **Development evaluation:** runs the supplied questions and records answers and retrieval diagnostics.

Citation-label checks confirm that a referenced label exists. They do not prove that the source supports every claim in the answer.

---

## 🧰 Technology Stack

| Component | Technology |
|---|---|
| Application language | Python |
| Model integration | Native OpenAI Python SDK |
| Answering deployment | `gpt-5.4-mini` |
| Embedding deployment | `text-embedding-3-small` |
| PDF extraction | PyMuPDF |
| Employee and task data | CSV |
| Vector storage | Local JSON |
| Similarity calculation | Cosine similarity |
| Interface | Command line |
| Source control | Git and Azure Repos |

### What runs where?

| Location | Responsibility |
|---|---|
| Local Python application | Document processing, record access, date calculations, vector search, validation, and evaluation |
| Microsoft Azure | Embedding generation and answer generation |
| Azure Repos | Code storage and version history |

Uploading the repository does not deploy a hosted application. This prototype runs locally and calls the deployed Azure models.

---

## 🔨 Development Process

| Stage | Work completed | Reason |
|---|---|---|
| Understand the task | Reviewed the scenario, documents, employee data, and development questions | Establish what the assistant needs to do |
| Prepare the knowledge base | Extracted text, preserved metadata, and created chunks | Make the documents searchable |
| Build employee context | Added record lookup, access rules, and supported date calculations | Supply exact personal facts |
| Connect Azure | Added embedding and answer-generation calls | Use deployed AI models from Python |
| Implement retrieval | Ranked chunks and assembled evidence | Find relevant policy guidance |
| Compare chunk sizes | Tested 400- and 800-character chunks | Understand how chunk size affects retrieval |
| Improve evidence selection | Collected distinct pages | Reduce repeated evidence |
| Improve task searches | Added relevant outstanding task names | Give broad questions more search context |
| Refine answer instructions | Clarified dates, source priority, missing evidence, and completeness | Address problems found in generated answers |
| Evaluate and document | Ran tests and demonstrations and recorded limitations | Make the results easier to review |

---

## 📊 Evaluation & Findings

### Chunk-size comparison

Both configurations used **100-character overlap**.

| Chunk size | Prepared chunks | Dimensions per vector |
|---|---:|---:|
| 400 characters | 149 | 1,536 |
| 800 characters | 71 | 1,536 |

The working configuration uses **400-character chunks with 100-character overlap**.

The comparison showed that chunk size changes which documents are retrieved. Neither configuration resolved every retrieval problem.

### Recorded verification

| Check | Recorded result | What it establishes |
|---|---|---|
| Unit tests | 17 passed in the recorded local run | The tested deterministic behavior passed |
| Development evaluation | 15 cases processed | The evaluation completed |
| Response outcomes | 14 answers generated and one request declined | Processing outcomes, not an accuracy score |
| Unauthorized request | Cross-employee request declined | The tested access rule behaved as intended |
| Payroll example | Conditional first-pay date explained | Employee context and calculated rules were combined |
| HSE example | Current site procedure prioritized | Policy conflict handling was demonstrated |
| Probation example | Some answers omitted scheduled check-ins | Answer completeness remains a limitation |

**An answer being generated does not mean it is correct. Zero automated flags does not mean 100% accuracy.**

### Evaluation status

The saved full evaluation was run before the final task-query expansion and answer-completeness instructions were added.

Targeted questions were tested after those changes. A fresh full evaluation of the final changes remains outstanding.

### Supporting reports

- [Results summary](Results.md)
- [Development evaluation report](artifacts/dev-evaluation.md)
- [Development evaluation data](artifacts/dev-evaluation.json)

---

## 🚀 How to Run

### 1. Check the prerequisites

You need:

- Python 3.12.
- Access to the approved Azure resource.
- Access to the embedding and answering deployments.
- The supplied `data/` folder.

The Azure endpoint and deployment names are configured in the scripts. Review them before using another Azure resource.

### 2. Create the Python environment

Open PowerShell in the repository folder:

```powershell
python -m venv .venv
```

The virtual environment keeps this project’s dependencies separate from other Python projects.

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Run the unit tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

### 5. Prepare the documents

```powershell
.\.venv\Scripts\python.exe -m onboarding prepare --size 400 --overlap 100
```

This creates the prepared chunks. It does not create the vector index.

### 6. Build the vector index

```powershell
.\.venv\Scripts\python.exe build_index.py --size 400
```

Enter the Azure API key when prompted. The input is hidden.

This step makes billed embedding calls. Reuse a valid index when the documents, chunk settings, and embedding configuration have not changed.

### 7. Ask a question

```powershell
.\.venv\Scripts\python.exe ask.py --asker NH-2606 --target NH-2606 --question "When will I get my first salary?"
```

| Argument | Meaning |
|---|---|
| `--asker` | Requester identity being simulated |
| `--target` | Employee whose record is requested |
| `--question` | Question to answer |

### 8. Run the development evaluation

```powershell
.\.venv\Scripts\python.exe evaluate.py
```

Evaluation makes billed Azure calls and writes:

```text
artifacts/dev-evaluation.md
artifacts/dev-evaluation.json
```

These filenames are reused. Preserve earlier reports before running another comparison.

Keep API keys out of source files, commits, screenshots, and documentation.

---

## 🧪 Demonstration Examples

### Employee-specific guidance

```powershell
.\.venv\Scripts\python.exe ask.py --asker NH-2606 --target NH-2606 --question "Do I get a laptop, and where is my HSE induction?"
```

**What to inspect:** whether the equipment and induction guidance matches the employee’s grade and location.

### Conflicting policy guidance

```powershell
.\.venv\Scripts\python.exe ask.py --asker NH-2611 --target NH-2611 --question "How long do I have to complete my HSE induction? I'll be working at Ras Laffan."
```

**What to inspect:** whether the current site procedure takes priority over conflicting lower-priority guidance.

### Unauthorized record access

```powershell
.\.venv\Scripts\python.exe ask.py --asker NH-2603 --target NH-2610 --question "What tasks are still open?"
```

**Expected response:**

> I cannot share that record. Please contact HR.

### Answer completeness

```powershell
.\.venv\Scripts\python.exe ask.py --asker NH-2610 --target NH-2610 --question "Explain my complete probation timeline, including its duration, all scheduled check-ins, the final review, possible outcomes, and who makes the decision."
```

**What to inspect:** whether the answer covers every requested detail. Earlier tests omitted scheduled check-ins even when other probation details were explained.

---

## 🛠️ Engineering Challenges & Lessons

### Repeated evidence from one page

**Problem:** several highly ranked chunks could come from the same page.

**Change:** collect distinct pages after ranking the chunks.

**Lesson:** high similarity scores alone do not ensure enough variety in the evidence.

### Broad questions lacked context

**Problem:** a question such as “What is still open?” does not name the policy topics that need to be searched.

**Change:** include outstanding task names in supported task-search queries.

**Lesson:** employee context can make the search query more useful.

### Dates could be explained inconsistently

**Problem:** answers could confuse payroll cutoffs, working-day rules, or unsupported calendar dates.

**Change:** calculate supported dates in Python and instruct the model to use those values.

**Lesson:** keep calculation separate from explanation.

### Relevant documents could disagree

**Problem:** lower-priority guidance could conflict with a current numbered procedure.

**Change:** provide source metadata and explicit precedence instructions.

**Lesson:** a source’s authority matters as well as its relevance.

### Related evidence could answer the wrong question

**Problem:** employee residence guidance could be used in place of missing spouse-sponsorship guidance.

**Change:** instruct the model to acknowledge when evidence about the exact subject is missing.

**Lesson:** a similar topic does not establish the requested procedure or fee.

### Answers could sound complete while missing details

**Problem:** an answer could explain probation outcomes but leave out scheduled check-ins.

**Change:** add completeness instructions and inspect targeted outputs.

**Lesson:** a readable answer can still be incomplete. This remains an evaluation priority.

---

## 📁 Repository Guide

| Path | Purpose |
|---|---|
| `ask.py` | Coordinates the question-answering workflow |
| `build_index.py` | Generates embeddings and saves the index |
| `evaluate.py` | Runs development questions and writes reports |
| `onboarding/` | Contains document-processing and employee-context logic |
| `onboarding/records.py` | Handles employee records and supported date calculations |
| `data/` | Contains supplied documents, records, and development cases |
| `tests/` | Contains unit tests |
| `artifacts/` | Holds generated files and selected evaluation reports |
| `architecture.png` | Shows the architecture diagram |
| `requirements.txt` | Lists Python dependencies |
| `Results.md` | Summarizes findings and limitations |
| `README.md` | Explains the project and how to use it |

Selected evaluation reports are included in the repository. Credentials, virtual environments, generated vector indexes, and local audit logs are excluded from tracking.

A fresh checkout needs an index built before document question answering can run.

---

## 🔍 Current Limitations

- **Simulated identity:** command-line employee IDs are not authentication.
- **Retrieval gaps:** relevant policy documents can still be missed.
- **Incomplete answers:** requested details may be omitted.
- **Source attribution:** the model may attribute a statement to the wrong source.
- **Limited citation checks:** valid labels do not prove that the cited evidence supports the answer.
- **Prompt-based safeguards:** instructions do not guarantee refusal when evidence is missing.
- **Local storage:** the JSON index is intended for a small prototype dataset.
- **Fixed scenario date:** deadlines and overdue status depend on the configured reference date.
- **No hosted interface:** this version has no web UI, voice interface, Teams connection, or live HR integration.

---

## ➡️ Next Steps

1. Run a fresh full evaluation of the final retrieval and instruction changes.
2. Review the remaining failures and test questions outside the development set.
3. Improve retrieval coverage and answer completeness.
4. Move deployment settings into a consistent configuration layer.
5. Add authenticated access before using real employee information.
6. Consider a user interface once the underlying behavior is sufficiently reliable.

---

**Project outcome:** a working onboarding RAG prototype that combines document retrieval, employee records, Python calculations, and Azure-generated answers, with documented results and clear limitations.
