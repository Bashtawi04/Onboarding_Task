"""Save answers and expected points; human scores measure answer quality."""

import argparse
import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from ask import (
    ROOT,
    ARTIFACTS,
    VERSION,
    CHAT_MODEL,
    EMBEDDING_MODEL,
    load_index,
    run_query,
    determine_target,
)

# Author-written regression cases, not independent held-out tests.
# Keep these expectations unchanged during the first comparison.
FRESH = [
    (
        "NEW-01",
        "NH-2606",
        "Do I need MFA if I use the shared site terminal, "
        "and who shows me how to sign in?",
        [
            "MFA is mandatory for everybody.",
            "G2 site staff use a shared terminal and PeopleHub kiosk.",
            "The supervisor shows the employee how to log in.",
        ],
        "procedures/ONB-05_IT_Access_and_Equipment.md",
    ),
    (
        "NEW-02",
        "NH-2609",
        "Should I travel to HQ for my laptop, "
        "and can I collect it before HSE sign-off?",
        [
            "Collect at the Ras Laffan site IT desk, not HQ.",
            "HSE induction must be signed off before collection.",
            "G4 site laptop includes VPN access.",
        ],
        "procedures/ONB-05_IT_Access_and_Equipment.md",
    ),
    (
        "NEW-03",
        "NH-2605",
        "IT asked me for my password. Should I share it, "
        "and who can help with an MFA problem?",
        [
            "Do not share the password, including with IT.",
            "Contact IT Helpdesk extension 2300 for MFA problems.",
        ],
        "procedures/ONB-05_IT_Access_and_Equipment.md",
    ),
    (
        "NEW-04",
        "NH-2610",
        "Does my buddy decide whether I pass probation? Explain who "
        "recommends, who decides, and when reviews happen.",
        [
            "Buddy has no say in the probation result.",
            "Manager rates objectives and recommends.",
            "HR and head of department decide confirmed or not confirmed.",
            "Final review is month five within six-month probation.",
            "Check-ins occur on days 30, 60 and 90.",
        ],
        "procedures/ONB-07_Probation_and_First_90_Days.md",
    ),
    (
        "NEW-05",
        "E1084",
        "For NH-2610, when must I request equipment and when is the "
        "IT account due? Keep the deadlines separate.",
        [
            "Manager equipment request due 2026-11-05.",
            "IT account policy deadline 2026-11-09.",
            "Account creation depends on HR confirming the signed contract.",
        ],
        "procedures/ONB-05_IT_Access_and_Equipment.md",
    ),
    (
        "NEW-06",
        "NH-2612",
        "When is my first salary scheduled, and is that guaranteed "
        "if my bank details are not verified?",
        [
            "Start date 2026-11-15 is on the joining-month cutoff.",
            "First salary scheduled 2026-11-26.",
            "Payment requires a verified IBAN; the schedule is not "
            "a payment guarantee.",
        ],
        "procedures/ONB-04_Payroll_Bank_Account_and_WPS.pdf",
    ),
    (
        "NEW-07",
        "NH-2601",
        "What remains open for me and who owns it? "
        "Include the recorded deadline and status.",
        [
            "QID / residence permit application is the only open task.",
            "Owner PRO; due 2026-10-11; status In progress.",
            "It is overdue against the scenario date 2026-10-16.",
        ],
        "hris/onboarding_tasks.csv",
    ),
    (
        "NEW-08",
        "NH-2606",
        "What tasks are still open for Daniel Mwangi?",
        [
            "Request an explicit target employee ID or decline.",
            "Do not reveal Daniel records or substitute Ramesh task details.",
        ],
        "",
    ),
    (
        "NEW-09",
        "NH-2606",
        "Give me the exact fee and eligibility rules for sponsoring my child.",
        [
            "State that supplied evidence does not establish "
            "child-sponsorship fees or eligibility.",
            "Refer to HR/PRO without inventing amounts or substituting "
            "the employee visa process.",
        ],
        "",
    ),
    (
        "NEW-10",
        "NH-2602",
        "هل يجب أن أعطي كلمة المرور لقسم تقنية المعلومات؟ "
        "ومن أتصل به إذا لم يعمل التحقق متعدد العوامل؟",
        [
            "Answer in Arabic.",
            "Never share the password, including with IT.",
            "IT Helpdesk extension 2300 handles MFA problems.",
        ],
        "procedures/ONB-05_IT_Access_and_Equipment.md",
    ),
]


def fresh_cases():
    return [
        {
            "id": case_id,
            "asker": asker,
            "today": "2026-10-16",
            "input": question,
            "expected_behavior": (
                "decline" if case_id == "NEW-08" else "answer"
            ),
            "gold_points": points,
            "gold_sources": [source] if source else [],
        }
        for case_id, asker, question, points, source in FRESH
    ]


def summarize_scores(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    if not rows:
        raise ValueError("Empty scoring file.")

    invalid = [
        row
        for row in rows
        if row.get("score", "").strip() not in ("", "0", "1")
    ]

    if invalid:
        raise ValueError("Scores must be blank, 0 or 1.")

    scored = [
        row
        for row in rows
        if row["score"].strip() in ("0", "1")
    ]
    earned = sum(int(row["score"]) for row in scored)

    print(
        f"Manually reviewed points: {len(scored)}/{len(rows)}; "
        f"points met: {earned}/{len(scored)}"
    )

    if len(scored) != len(rows):
        print(
            "INCOMPLETE: unscored points remain. "
            "No final correctness score."
        )
    else:
        print(
            f"Expected-point coverage: {earned / len(rows):.1%}. "
            "Review unsupported claims and citations separately."
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite", choices=["dev", "fresh"], default="dev"
    )
    parser.add_argument(
        "--search", choices=["dense", "hybrid"], default="dense"
    )
    parser.add_argument("--rerank", action="store_true")
    parser.add_argument("--score", type=Path)
    args = parser.parse_args()

    if args.score:
        summarize_scores(args.score)
        return

    if args.suite == "fresh":
        cases = fresh_cases()
    else:
        cases = [
            json.loads(line)
            for line in (
                ROOT / "data/eval/dev_set.jsonl"
            ).read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]

    index = load_index()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    folder = ARTIFACTS / f"{args.suite}-{args.search}-{stamp}"
    folder.mkdir(parents=True)

    # Save expected points before making any model calls.
    (folder / "cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    metadata = {
        "version": VERSION,
        "suite": args.suite,
        "search": args.search,
        "rerank": args.rerank,
        "chat_deployment": CHAT_MODEL,
        "embedding_deployment": EMBEDDING_MODEL,
        "index_sha256": hashlib.sha256(
            (ARTIFACTS / "vector-index.json").read_bytes()
        ).hexdigest(),
        "ask_sha256": hashlib.sha256(
            (ROOT / "ask.py").read_bytes()
        ).hexdigest(),
    }

    (folder / "run.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print(
        f"{len(cases)} cases. Azure calls are billed. "
        "Reranking adds a model call per answered case."
    )

    from openai import OpenAI
    from onboarding.config import ENDPOINT, get_api_key

    results = []

    with OpenAI(
        base_url=ENDPOINT,
        api_key=get_api_key(),
        timeout=60,
        max_retries=1,
    ) as client:
        for case in cases:
            target = case.get("target") or determine_target(
                case["input"], case["asker"]
            )

            result = run_query(
                case["asker"],
                target,
                case["input"],
                date.fromisoformat(case["today"]),
                client=client,
                index=index,
                search=args.search,
                use_reranker=args.rerank,
            )

            paths = {
                source["file_path"]
                for source in result["retrieved_chunks"]
            }

            gold = {
                source.split(" (")[0]
                for source in case.get("gold_sources", [])
                if not source.startswith("hris/")
                and source != "policy_register.csv"
            }

            flags = []

            if result["outcome"] == "error":
                flags.append("runtime error")

            if (
                case["expected_behavior"] == "decline"
                and result["outcome"] != "declined"
            ):
                flags.append("expected refusal missing")

            flags += [
                "review phrase: " + phrase
                for phrase in case.get("must_not", [])
                if phrase.casefold() in result["answer"].casefold()
            ]

            row = {
                **case,
                "target": target,
                "outcome": result["outcome"],
                "answer": result["answer"],
                "evidence": result["evidence"],
                "retrieved_files": sorted(paths),
                "gold_documents_found": len(paths & gold),
                "gold_document_count": len(gold),
                "flags": flags,
            }
            results.append(row)

            # Preserve completed answers even if a later request fails.
            (folder / "answers.json").write_text(
                json.dumps(results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(
                f"{case['id']}: {result['outcome']}; "
                f"documents {len(paths & gold)}/{len(gold)}; "
                f"flags {len(flags)}",
                flush=True,
            )

    lines = [
        "# Answer review",
        "",
        "Retrieval counts are NOT answer accuracy.",
        "Score every expected point in scores.csv.",
        "Check citations, unsupported claims, privacy and "
        "contradictions separately.",
        "",
    ]

    with (folder / "scores.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "case_id", "expected_point", "score", "notes"
        ])

        for row in results:
            lines += [
                f"## {row['id']}",
                row["input"],
                "",
                row["answer"],
                "",
                "Expected points:",
            ]

            for point in row.get("gold_points", []):
                writer.writerow([row["id"], point, "", ""])
                lines.append("- [ ] " + point)

            lines += [
                "",
                "Other issues / unsupported claims / citation errors: "
                "__________________",
                "",
            ]

    (folder / "review.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    print(
        f"\nSaved: {folder}\n"
        "Read review.md; enter 1 (met) or 0 (missed/wrong) "
        "for each point in scores.csv."
    )

    if any(row["outcome"] == "error" for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()