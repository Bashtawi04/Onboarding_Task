# 🤖 Onboarding Action Agent

### From answering questions to taking controlled actions

**Author:** Yahya AlBashtawi · **Organisation:** Cerebrum
**Scenario:** Fictional Al Dana onboarding · **Status:** Learning prototype

[📊 Evaluation report](RESULTS.md) · [📘 API reference](docs/ONB_API.md) · [🧪 Unit tests](tests/test_approval.py) · [🔙 Phase 1](../README.md)

---

## 📌 Project overview

Onboarding involves more than finding information. Employees and managers
also need to resolve blockers, request equipment and arrange appointments.

This Python agent interprets natural-language requests, consults PeopleHub
records and uses tools to perform permitted operations. Actions requiring
approval are saved as proposals and remain unexecuted until an eligible
person approves them.

> **Core principle:** the model selects tools; Python validates arguments
> and enforces approval; PeopleHub checks permissions and business rules.

All operations use the supplied **mock PeopleHub system**. No real HR
records are changed, appointments booked or emails delivered externally.

## 🎯 Example: requesting a laptop

**Manager:** “Please request a laptop for the new hire. HR already agreed.”

| Step | Agent behaviour |
|---|---|
| 🔎 Identify | Locate the intended employee and read their onboarding record |
| ✅ Check | Verify access and laptop eligibility through PeopleHub |
| 📝 Propose | Save the exact request and eligible approvers |
| ⏸️ Wait | Return `awaiting_approval`; create no IT request yet |
| 👤 Decide | Accept an eligible person's approval, rejection or permitted edit |
| ⚙️ Execute | Recheck a newly approved action, then create the mock request |
| 📋 Report | Return the actual execution result or failure |

A claim that approval happened by phone does not replace the recorded
approval workflow.

## 🔄 Phase 1 → Phase 2

| Area | Phase 1: RAG assistant | Phase 2: action agent |
|---|---|---|
| Purpose | Answer onboarding questions | Perform controlled onboarding operations |
| Information | Retrieved documents and authorized CSV records | PeopleHub tools and operational records |
| Output | Explanation with source citations | Explanation, pending proposal or execution result |
| Writes | No HR record updates | Permitted writes to the mock system |
| Human control | User reviews an answer | Eligible person approves, rejects or edits gated actions |
| Evaluation | Retrieval and expected-answer points | Calls, approvals, database effects and recovery |

Phase 1 remains in the repository root. Phase 2 runs separately in this
folder; the document-retrieval pipeline is not integrated into this agent.

## 🧰 Supported operations

| Operation | Approval behaviour |
|---|---|
| Read onboarding records and blockers | Read-only, subject to access checks |
| Create an IT account, laptop or equipment request | Eligibility checks and human approval |
| Book a medical or QID appointment | Applicability, slot checks and human approval |
| Send an onboarding email to a permitted recipient | Validation and human approval |
| Add a task note | Authorized low-risk write; no approval request |
| Reject a pending proposal | No action executed |
| Modify a proposal | Permitted fields validated and eligibility checked again |

## 🏗️ Architecture

| Component | Responsibility |
|---|---|
| **CLI** | Receives messages, conversation IDs and simulated identities |
| **Azure-hosted model** | Interprets requests and chooses tools |
| **OpenAI SDK** | Exchanges messages and tool calls with the deployment |
| **Pydantic** | Validates types, allowed values and unexpected arguments |
| **Python controller** | Manages proposals, approvers, execution and recovery |
| **PeopleHub APIs** | Apply access checks and onboarding business rules |
| **Persistent state** | Retains conversation and pending execution information |
| **Evaluation harness** | Checks conversations, approvals, API calls and effects |

### 🛡️ Human in the loop

Human in the loop means a person remains part of the execution decision.

- **Approve:** verify the approver and execute the eligible action.
- **Reject:** finish without performing the proposed write.
- **Modify:** validate permitted edits and recheck the changed proposal.
- **Unauthorized decision:** do not execute the action.

Approver identity comes from the `resume` command, not model arguments.
CLI identities are simulated for this exercise, not production authentication.

## 🔁 Reliability and recovery

| Control | Purpose |
|---|---|
| Persistent pending state | Resume approval in a separate process |
| Execution details saved before writing | Support recovery after interruption |
| Stable idempotency keys for approved writes | Reuse the same operation identity on retry |
| One retry for retryable service errors | Handle a temporary failure without an unlimited loop |
| Per-thread locking | Protect simultaneous updates to one conversation |
| Exact task-note argument tracking | Avoid repeating the same note within that thread |
| Explicit failure reporting | Avoid presenting failed actions as completed |

These controls have targeted test coverage. They do not establish a
universal exactly-once guarantee across every tool and failure mode.

## 📊 Verification snapshot

| Check | Observed result |
|---|---:|
| Public scenarios: 8 cases × 3 repetitions | ✅ **24/24** |
| Additional scenarios: 4 cases × 3 repetitions | ✅ **12/12** |
| Local approval and recovery unit tests | ✅ **20/20** |
| Same unit suite in a clean exported copy | ✅ **20/20** |
| Safety violations reported in successful scenario runs | ✅ **0** |

The public run preceded the final stdout encoding fix. The additional run
completed after that fix with UTF-8 enabled. These are separate recorded
evaluations, not a single run of one identical revision.

See [the evaluation report](RESULTS.md) for evidence and limitations.

---

## ⚙️ Installation

**Tested environment:** Windows PowerShell · Python **3.12.10**

Open a terminal in the repository's `phase2` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On first setup only:

```powershell
Copy-Item .env.example .env
notepad .env
```

| Configuration variable | Required value |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure resource endpoint |
| `AZURE_OPENAI_API_KEY` | Your private API key |
| `AZURE_OPENAI_DEPLOYMENT` | Tool-capable deployment name |

For the supplied deployment checker, use the resource endpoint without
an appended `/openai/v1` path. Never commit your `.env`.

### 🌐 Windows Unicode support

Run in each new PowerShell terminal:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

This allows the supplied harness to save Unicode responses reliably.
Agent JSON output uses ASCII escapes, preserving the decoded text.

### 🔌 Deployment check

This makes a **billable model request**:

```powershell
.\.venv\Scripts\python.exe -X utf8 tools\check_model.py
```

## 🧪 Run verification

### 1. Local unit tests — no Azure calls

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p test_approval.py -v
```

### 2. Public scenarios — Azure calls are billed

```powershell
.\.venv\Scripts\python.exe -X utf8 harness\run_scenarios.py --track onboarding --agent ".venv/Scripts/python.exe agent_cli.py" --scenarios scenarios/onboarding_public.jsonl --repeat 3 -v --keep --out results-public-repeat3.json
```

### 3. Additional scenarios — Azure calls are billed

```powershell
.\.venv\Scripts\python.exe -X utf8 harness\run_scenarios.py --track onboarding --agent ".venv/Scripts/python.exe agent_cli.py" --scenarios scenarios/onboarding_own.jsonl --repeat 3 -v --keep --out results-own-repeat3-utf8.json
```

The harness supplies isolated databases and state directories using
`PEOPLEHUB_DB` and `AGENT_STATE_DIR`.

## 💬 CLI interface

Invoke `agent_cli.py` using these command arguments:

| Command | Purpose |
|---|---|
| `start --thread ID --user ID --message TEXT` | Begin a conversation |
| `say --thread ID --message TEXT` | Continue a conversation |
| `resume --thread ID --decision approve --by ID` | Approve |
| `resume --thread ID --decision reject --by ID` | Reject |
| `resume --thread ID --decision modify --by ID --edit JSON` | Approve permitted edits |

Each invocation returns one JSON object containing `status`, `message`
and `pending`. Status is `done`, `awaiting_approval` or `error`.
Preserve the same thread's saved state between proposal and decision.

## 📁 Repository guide

| Path | Purpose |
|---|---|
| `agent_cli.py` | Model loop, validation, approval and recovery |
| `peoplehub/` | Supplied mock APIs and fictional seed records |
| `harness/` | Supplied scenario runner |
| `docs/ONB_API.md` | PeopleHub API documentation |
| `scenarios/onboarding_public.jsonl` | Eight supplied scenarios |
| `scenarios/onboarding_own.jsonl` | Four additional scenarios |
| `tests/test_approval.py` | Twenty local tests |
| `results-public-repeat3.json` | Public evaluation evidence |
| `results-own-repeat3-utf8.json` | Successful additional evaluation evidence |
| `RESULTS.md` | Results, failure analysis and limitations |
| `PRECOMMIT_REVIEW.md` | Secret-check scope and earlier hash findings |
| `templates/` | Supplied templates, not completed peer reviews |

## 🎬 Suggested 10-minute demonstration

| Time | Demonstration |
|---|---|
| 0–2 minutes | Explain the goal and identify a blocked contract |
| 2–4 minutes | Propose a laptop request; show that execution waits |
| 4–6 minutes | Demonstrate an eligible decision and its actual effect |
| 6–8 minutes | Show rejection or a controlled service failure |
| 8–10 minutes | Explain tests, recovery design and limitations |

Use the saved evaluation evidence as a fallback if the model service is
unavailable. A failure demonstration should explain what happened and
show that the system did not claim a successful write.

## 🔐 Precommit checks

From `phase2`:

```powershell
.\.venv\Scripts\python.exe -X utf8 tools\precommit_check.py
```

This scans Phase 2. Earlier repository-wide findings in Phase 1 hash
metadata are documented in [PRECOMMIT_REVIEW.md](PRECOMMIT_REVIEW.md).
The supplied checker remains unchanged.

## ⚠️ Current limitations

- Identity is simulated; production authentication is not implemented.
- The backend is a mock system and the interface is command-line only.
- General requests requiring multiple approved actions need further verification.
- Task-note duplicate tracking covers exact arguments within one thread.
- Model-written explanations can vary and include unnecessary contract context.
- Hidden-test results and independent peer review are not part of these scores.
- Phase 1 RAG and Phase 2 actions remain separate workflows.

## 📌 Review status

Implementation, recorded evaluations, setup documentation and clean-copy
unit verification are available. Peer review, mentor evaluation and the
demonstration are separate delivery steps.

## 🏗️ Architecture: from a request to a controlled action

### Components and responsibilities

| Component | Responsibility |
|---|---|
| User and CLI (`agent_cli.py`) | Receive a request, simulated user identity and conversation/thread identifier. |
| Azure-hosted language model | Interpret the request and select available tools through the OpenAI SDK. |
| Pydantic argument models | Check argument types, allowed values and unexpected fields. Validation alone does not authorize an action. |
| Python agent controller | Apply the approval workflow, preserve pending proposals and control execution. |
| PeopleHub tools (`peoplehub/`) | Read mock onboarding records and enforce access and business rules for simulated writes. |
| Persistent thread state | Preserve conversations, proposals and execution information across CLI processes. |
| Human approver | Approve, reject or edit an eligible pending proposal. |
| Evaluation harness and tests | Check replies, approval behavior, actual database effects and recovery behavior. |

### Request and approval flow

1. **Receive:** The CLI receives the user's message and simulated identity.
2. **Investigate:** The model selects read tools to obtain relevant PeopleHub records.
3. **Validate:** Python validates tool arguments; PeopleHub checks access and business rules.
4. **Choose a path:**
   - Read-only request: return an answer grounded in retrieved records.
   - Permitted task note: perform the low-risk write without an approval request.
   - Action requiring approval: save a proposal and return `awaiting_approval`. The proposed write has not happened.
   - Disallowed action: explain the restriction.
5. **Human decision:** A later `resume` command supplies the decision and approver identity. Python checks whether that person is eligible.
6. **Recheck:** For a newly approved or edited proposal, validate the permitted changes and recheck the applicable rules.
7. **Execute:** Save execution information before the approved write. Retryable service failures receive at most one retry using the same idempotency key.
8. **Report:** Save and return the actual outcome. Rejection and failed execution are reported explicitly.

### Example: an IT account and a laptop

If the recorded contract is still blocked, a claim that HR approved it by phone does not satisfy the IT account prerequisite.

The agent explains why the account cannot proceed. A laptop request may still proceed through its own eligibility and human-approval checks. Approval does not override an unmet business rule.

### Trust boundaries

- Model-generated arguments and user statements are not proof of authorization.
- The model does not choose the identity of the person approving a proposal.
- Human approval and business-rule eligibility are separate checks.
- CLI identities are simulated for this exercise; production authentication is outside this implementation.
- PeopleHub is a mock system: these actions do not alter real HR records or send real email.

### How this relates to Phase 1

Phase 1 retrieves supporting information and generates an answer.

Phase 2 reads operational records and performs controlled actions through tools, with human approval where required. The two workflows live in the same repository; Phase 2 does not integrate the Phase 1 retrieval pipeline.
