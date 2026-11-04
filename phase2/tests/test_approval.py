import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import agent_cli as agent
from peoplehub import core, onboarding


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.env = patch.dict(os.environ, {
            "PEOPLEHUB_DB": self.temp.name + "/db.sqlite",
            "AGENT_STATE_DIR": self.temp.name + "/state",
        })
        self.env.start()
        self.addCleanup(self.env.stop)

        core.build_db(os.environ["PEOPLEHUB_DB"], onboarding)
        self.actor = "E1091"
        self.state = self.proposal("propose_it_request", {
            "new_hire_id": "NH-2607",
            "kind": "laptop",
            "note": "Requested laptop",
        })

    def proposal(self, name, args):
        pending, error = agent.prepare_proposal(name, args, self.actor)
        self.assertIsNone(error)
        state = {
            "actor": self.actor,
            "pending": pending,
            "pending_call_id": "call_1",
            "messages": [{
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps(args),
                    },
                }],
            }],
        }
        agent.save("T", state)
        return state

    def count(self, kind="laptop"):
        with closing(core.connect()) as conn:
            return conn.execute(
                "SELECT count(*) FROM it_requests "
                "WHERE new_hire_id=? AND kind=?",
                ("NH-2607", kind),
            ).fetchone()[0]

    def decide(self, decision="approve", by="E1091", edit=None):
        return agent.resume(
            "T", self.state, decision, by, edit or {}
        )

    def test_proposal_does_not_write(self):
        self.assertEqual(self.count(), 0)
        self.assertEqual(
            self.state["pending"]["approvers"],
            ["E1091", "E1068"],
        )

    def test_approve_and_repeat(self):
        self.assertEqual(self.decide()["status"], "done")
        self.assertEqual(self.count(), 1)
        self.decide()
        self.assertEqual(self.count(), 1)
        with closing(core.connect()) as conn:
            calls = conn.execute(
                "SELECT count(*) FROM audit_log "
                "WHERE function='create_it_request'"
            ).fetchone()[0]
        self.assertEqual(calls, 1)

    def test_reject(self):
        self.assertIn("rejected", self.decide("reject")["message"])
        self.decide()
        self.assertEqual(self.count(), 0)

    def test_wrong_approver(self):
        result = self.decide(by="NH-2607")
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertEqual(self.count(), 0)

    def test_modify_note(self):
        self.decide("modify", edit={"note": "Approved amended note"})
        with closing(core.connect()) as conn:
            note = conn.execute(
                "SELECT note FROM it_requests "
                "WHERE new_hire_id='NH-2607'"
            ).fetchone()[0]
        self.assertEqual(note, "Approved amended note")

    def test_modify_forbidden_field(self):
        result = self.decide(
            "modify", edit={"new_hire_id": "NH-2609"}
        )
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertEqual(self.count(), 0)

    def test_modify_invalid_kind(self):
        result = self.decide("modify", edit={"kind": "phone"})
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertEqual(self.count(), 0)

    def test_modify_ineligible(self):
        result = self.decide("modify", edit={"kind": "equipment"})
        self.assertIn("not executed", result["message"])
        self.assertEqual(self.count("equipment"), 0)

    def test_changed_eligibility(self):
        with closing(core.connect()) as conn:
            conn.execute(
                "UPDATE new_hires SET location='Mesaieed Site',grade=2 "
                "WHERE new_hire_id='NH-2607'"
            )
            conn.commit()
        self.assertIn("not executed", self.decide()["message"])
        self.assertEqual(self.count(), 0)

    def test_temporary_failure_retry_same_key(self):
        core.add_fault("create_it_request", times=1)
        self.decide()
        self.assertEqual(self.count(), 1)
        with closing(core.connect()) as conn:
            rows = conn.execute(
                "SELECT args FROM audit_log "
                "WHERE function='create_it_request'"
            ).fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            json.loads(rows[0][0]), json.loads(rows[1][0])
        )

    def test_two_failures_stop(self):
        core.add_fault("create_it_request", times=2)
        self.assertIn("failed", self.decide()["message"])
        self.assertEqual(self.count(), 0)

    def test_fresh_process_resume(self):
        run = subprocess.run(
            [
                sys.executable,
                str(Path(agent.__file__).resolve()),
                "resume",
                "--thread", "T",
                "--decision", "approve",
                "--by", "E1091",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["status"], "done")
        self.assertEqual(self.count(), 1)

    def test_crash_after_write_recovered(self):
        with patch.object(
            agent,
            "finish_pending",
            side_effect=RuntimeError("Simulated interruption"),
        ):
            with self.assertRaises(RuntimeError):
                self.decide()

        self.assertEqual(self.count(), 1)
        self.state = json.loads(
            agent.state_path("T").read_text(encoding="utf-8")
        )
        self.assertEqual(self.decide()["status"], "done")
        self.assertEqual(self.count(), 1)

    def test_recovery_cannot_change_decision(self):
        with patch.object(
            agent,
            "finish_pending",
            side_effect=RuntimeError("Simulated interruption"),
        ):
            with self.assertRaises(RuntimeError):
                self.decide()

        self.state = json.loads(
            agent.state_path("T").read_text(encoding="utf-8")
        )
        result = self.decide("modify", edit={"kind": "account"})
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertEqual(self.count("account"), 0)

    def test_note_no_approval_and_deduplicated(self):
        state = {"actor": "E1007"}
        args = {
            "task_id": "T-2609-01",
            "note": "HR re-sent contract; awaiting signed last page.",
        }
        result = agent.add_note_once("N", state, "note_1", args)
        self.assertIn("note_id", result)
        agent.add_note_once("N", state, "note_2", args)

        with closing(core.connect()) as conn:
            count = conn.execute(
                "SELECT count(*) FROM task_notes"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_appointment(self):
        self.actor = "E1072"
        self.state = self.proposal("propose_pro_appointment", {
            "new_hire_id": "NH-2605",
            "service": "medical",
            "slot_id": "MED-20261020-0900",
        })
        self.assertEqual(self.decide(by="E1078")["status"], "done")

        with closing(core.connect()) as conn:
            count = conn.execute(
                "SELECT count(*) FROM pro_appointments "
                "WHERE new_hire_id='NH-2605'"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_contract_blocker_survives_laptop_success(self):
        self.actor = "E1007"
        self.state = self.proposal("propose_it_request", {
            "new_hire_id": "NH-2609",
            "kind": "laptop",
            "note": "Laptop requested",
        })
        self.assertIn("contract", self.state["pending"]["summary"])

        result = self.decide(by="E1007")
        self.assertIn("contract", result["message"])
        self.assertIn("Blocked", result["message"])

        with closing(core.connect()) as conn:
            rows = conn.execute(
                "SELECT kind FROM it_requests "
                "WHERE new_hire_id='NH-2609'"
            ).fetchall()
        self.assertEqual([row[0] for row in rows], ["laptop"])

    def test_contract_context_uses_record_for_other_hire(self):
        self.actor = "E1084"
        self.state = self.proposal("propose_it_request", {
            "new_hire_id": "NH-2610",
            "kind": "laptop",
            "note": "Laptop requested",
        })
        summary = self.state["pending"]["summary"]
        self.assertIn("Not started", summary)
        self.assertNotIn("Blocked", summary)

    def test_email(self):
        hire = onboarding.get_new_hire(
            "NH-2607", actor=self.actor
        )
        self.state = self.proposal("propose_email", {
            "new_hire_id": "NH-2607",
            "to": hire["manager_email"],
            "subject": "Onboarding update",
            "body": "Please check the onboarding tasks.",
        })
        self.assertEqual(self.decide(by="E1068")["status"], "done")

    def test_email_edit_external_refused(self):
        hire = onboarding.get_new_hire(
            "NH-2607", actor=self.actor
        )
        self.state = self.proposal("propose_email", {
            "new_hire_id": "NH-2607",
            "to": hire["manager_email"],
            "subject": "Onboarding update",
            "body": "Please check the onboarding tasks.",
        })
        result = self.decide(
            "modify",
            by="E1068",
            edit={"to": "outside@example.com"},
        )
        self.assertIn("not executed", result["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)