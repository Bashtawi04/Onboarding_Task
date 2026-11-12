"""Free model-loop tests: canned model responses, real PeopleHub effects."""
import json
import os
import tempfile
import unittest
from contextlib import closing
from types import SimpleNamespace as NS
from unittest.mock import patch

import agent_cli as a
from peoplehub import core, onboarding


def answer(text="Finished; no further actions requested."):
    return NS(choices=[NS(message=NS(content=text, tool_calls=None))])


def call(name, args, cid="c1"):
    return NS(choices=[NS(message=NS(content=None, tool_calls=[NS(
        id=cid, function=NS(name=name, arguments=json.dumps(args)))]))])


IT = {"new_hire_id": "NH-2607", "kind": "laptop", "note": "Requested laptop"}
EMAIL = {"new_hire_id": "NH-2607", "to": "hr.onboarding@aldana-group.example",
         "subject": "Welcome", "body": "Dear Lina, welcome."}


class ConversationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        env = patch.dict(os.environ, {"PEOPLEHUB_DB": temp.name + "/db.sqlite",
            "AGENT_STATE_DIR": temp.name + "/state", "AZURE_OPENAI_ENDPOINT": "https://example.invalid",
            "AZURE_OPENAI_API_KEY": "example", "AZURE_OPENAI_DEPLOYMENT": "fake"})
        env.start(); self.addCleanup(env.stop)
        core.build_db(os.environ["PEOPLEHUB_DB"], onboarding)
        model = patch.object(a, "OpenAI")
        self.client = model.start().return_value
        self.addCleanup(model.stop)
        self.create = self.client.chat.completions.create
        self.state = {"actor": "E1091", "pending": None, "messages": [
            {"role": "system", "content": a.PROMPT},
            {"role": "user", "content": "Request Lina's laptop and IT account."}]}

    def count(self, table):
        with closing(core.connect()) as c:
            return c.execute("SELECT count(*) FROM " + table).fetchone()[0]

    def test_two_actions_pause_separately_and_execute_once(self):
        before = self.count("it_requests")
        self.create.side_effect = [call("propose_it_request", IT),
            call("propose_it_request", {**IT, "kind": "account"}, "c2"), answer()]
        self.assertEqual(a.run_agent("T", self.state)["status"], "awaiting_approval")
        self.assertEqual(self.count("it_requests"), before)
        result = a.resume("T", self.state, "approve", "E1091", {})
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertEqual(result["pending"]["args"]["kind"], "account")
        self.assertEqual(self.count("it_requests"), before + 1)
        # Reload persisted state, as the real CLI does between approvals.
        self.state = json.loads(a.state_path("T").read_text())
        result = a.resume("T", self.state, "approve", "E1091", {})
        self.assertEqual(result["status"], "done")
        self.assertEqual(self.count("it_requests"), before + 2)
        a.resume("T", self.state, "approve", "E1091", {})
        self.assertEqual(self.count("it_requests"), before + 2)
        self.assertEqual(self.create.call_count, 3)

    def test_rejection_continues_without_reproposing(self):
        before = self.count("it_requests")
        self.create.side_effect = [call("propose_it_request", IT),
            call("propose_it_request", IT, "repeat"),
            call("propose_it_request", {**IT, "kind": "account"}, "c2")]
        a.run_agent("T", self.state)
        result = a.resume("T", self.state, "reject", "E1091", {})
        self.assertEqual(result["status"], "awaiting_approval")
        self.assertIn("rejected", result["message"])
        self.assertEqual(self.count("it_requests"), before)
        self.assertEqual(result["pending"]["args"]["kind"], "account")

    def test_failed_write_continues_without_repeating(self):
        core.add_fault("create_it_request", times=2)
        self.create.side_effect = [call("propose_it_request", IT), answer()]
        before = self.count("it_requests")
        a.run_agent("T", self.state)
        result = a.resume("T", self.state, "approve", "E1091", {})
        self.assertIn("failed", result["message"])
        self.assertEqual(self.count("it_requests"), before)

    def test_continuation_failure_recovers_without_second_write(self):
        self.create.side_effect = [call("propose_it_request", IT), RuntimeError("offline"), answer()]
        before = self.count("it_requests")
        a.run_agent("T", self.state)
        result = a.resume("T", self.state, "approve", "E1091", {})
        self.assertEqual(result["status"], "error")
        self.assertIn("Action completed", result["message"])
        self.state = json.loads(a.state_path("T").read_text())
        self.assertEqual(a.resume("T", self.state, "approve", "E1091", {})["status"], "done")
        self.assertEqual(self.count("it_requests"), before + 1)

    def test_initial_model_failure_can_resume(self):
        self.create.side_effect = [RuntimeError("offline"), answer("Recovered.")]
        self.assertEqual(a.run_agent("T", self.state)["status"], "error")
        self.state = json.loads(a.state_path("T").read_text())
        self.assertTrue(self.state["continuation_due"])
        self.assertEqual(a.resume("T", self.state, "approve", "E1091", {})["status"], "done")
        self.assertEqual(self.create.call_count, 2)

    def test_rejection_receipt_names_the_human_decision(self):
        self.create.side_effect = [call("propose_it_request", IT),
            answer("PeopleHub rejected it because it is ineligible.")]
        a.run_agent("T", self.state)
        reply = a.resume("T", self.state, "reject", "E1091", {})["message"]
        self.assertIn("rejected by Fatima Hamid", reply)
        self.assertNotIn("ineligible", reply)
        self.assertNotIn("PeopleHub rejected", reply)

    def test_completed_request_is_not_reported_as_pending(self):
        self.create.side_effect = [call("propose_it_request", IT),
            answer("Only prepared for approval, not executed yet.")]
        a.run_agent("T", self.state)
        reply = a.resume("T", self.state, "approve", "E1091", {})["message"]
        self.assertIn("Action completed", reply)
        self.assertIn("Request ID:", reply)
        self.assertNotIn("not executed yet", reply)
        self.assertNotIn(IT["note"], reply)

    def test_booking_weekday_comes_from_returned_date(self):
        appointment = {"new_hire_id": "NH-2605", "service": "medical",
                       "slot_id": "MED-20261020-0900"}
        # HR may request this hire's booking.
        self.state["actor"] = "E1068"
        self.state["messages"][-1]["content"] = "Book Hesham's medical test."
        self.create.side_effect = [call("propose_pro_appointment", appointment),
            answer("Booked Monday 20 October 2026.")]
        result = a.run_agent("T", self.state)
        self.assertEqual(result["status"], "awaiting_approval")
        by = result["pending"]["approvers"][0]
        reply = a.resume("T", self.state, "approve", by, {})["message"]
        self.assertIn("Tuesday 2026-10-20 09:00", reply)
        self.assertNotIn("Monday", reply)

    def test_failed_write_is_not_described_as_failed_proposal(self):
        core.add_fault("create_it_request", times=2)
        self.create.side_effect = [call("propose_it_request", IT),
            answer("The proposal could not be prepared.")]
        a.run_agent("T", self.state)
        reply = a.resume("T", self.state, "approve", "E1091", {})["message"]
        self.assertIn("Action failed", reply)
        self.assertNotIn("proposal could not", reply)

    def test_multi_call_batch_does_not_execute(self):
        batch = call("propose_it_request", IT)
        batch.choices[0].message.tool_calls *= 2
        self.create.return_value = batch
        before = self.count("audit_log")
        self.assertEqual(a.run_agent("T", self.state)["status"], "error")
        self.assertEqual(self.count("audit_log"), before)

    def test_eight_turn_limit(self):
        self.create.return_value = call("get_today", {})
        result = a.run_agent("T", self.state)
        self.assertEqual(result["status"], "error")
        self.assertEqual(self.create.call_count, 8)
        self.assertIn("unresolved", result["message"])

    def test_invalid_arguments_do_not_reach_api(self):
        self.create.side_effect = [call("propose_it_request", {**IT, "approved_by": "E1068"}), answer()]
        before = self.count("audit_log")
        a.run_agent("T", self.state)
        self.assertEqual(self.count("audit_log"), before)
        self.assertIn("INVALID_ARGUMENTS", self.state["messages"][-2]["content"])

    def test_malformed_json(self):
        bad = call("get_today", {})
        bad.choices[0].message.tool_calls[0].function.arguments = "{broken"
        self.create.side_effect = [bad, answer()]
        a.run_agent("T", self.state)
        self.assertIn("INVALID_ARGUMENTS", self.state["messages"][-2]["content"])

    def test_unknown_tool(self):
        self.create.side_effect = [call("delete_all_records", {}), answer()]
        a.run_agent("T", self.state)
        self.assertIn("Unknown tool", self.state["messages"][-2]["content"])

    def test_forbidden_ends_turn_after_one_call(self):
        self.create.side_effect = [call("get_new_hire", {"new_hire_id": "NH-2609"}),
                                  call("list_tasks", {"new_hire_id": "NH-2609"})]
        result = a.run_agent("T", self.state)
        self.assertEqual(self.create.call_count, 1)
        self.assertIn("Access refused", result["message"])
        with closing(core.connect()) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM audit_log WHERE error_code='ERR_FORBIDDEN'").fetchone()[0], 1)

    def test_missing_email_never_substitutes_hr(self):
        self.state["messages"][-1]["content"] = "Send Lina a welcome email."
        self.create.side_effect = [call("propose_email", EMAIL), answer("Please clarify.")]
        before = self.count("outbox")
        result = a.run_agent("T", self.state)
        self.assertIsNone(result["pending"])
        self.assertIn("missing", result["message"])
        self.assertEqual(self.count("outbox"), before)

    def test_explicit_hr_address_can_be_proposed(self):
        self.state["messages"][-1]["content"] = "Email HR at " + EMAIL["to"] + " about Lina."
        self.create.return_value = call("propose_email", EMAIL)
        self.assertEqual(a.run_agent("T", self.state)["status"], "awaiting_approval")

    def test_readable_names_and_no_json(self):
        self.create.return_value = call("propose_it_request", IT)
        result = a.run_agent("T", self.state)
        self.assertIn("Lina Khoury", result["message"])
        self.assertIn("Fatima Hamid", result["message"])
        self.assertNotIn('{"', result["message"])

    def test_arabic_approval(self):
        self.state["messages"][-1]["content"] = "أريد طلب حاسوب محمول للينا"
        self.create.return_value = call("propose_it_request", IT)
        self.assertIn("بانتظار الموافقة", a.run_agent("T", self.state)["message"])

    def test_laptop_medical_and_email_each_require_approval(self):
        email = {**EMAIL, "to": "lina.khoury@aldana-group.example"}
        with closing(core.connect()) as c:
            c.execute("UPDATE new_hires SET work_email=? WHERE new_hire_id='NH-2607'", (email["to"],))
            c.commit()
        self.state["messages"][-1]["content"] = "Request Lina's laptop, book her medical test and send her a welcome email."
        medical = {"new_hire_id": "NH-2607", "service": "medical", "slot_id": "MED-20261026-0900"}
        self.create.side_effect = [call("propose_it_request", IT),
            call("propose_pro_appointment", medical, "c2"),
            call("propose_email", email, "c3"), answer()]
        before = {table: self.count(table) for table in ["it_requests", "pro_appointments", "outbox"]}
        a.run_agent("T", self.state)
        r = a.resume("T", self.state, "approve", "E1091", {})
        self.assertEqual(r["pending"]["tool"], "book_pro_appointment")
        self.assertEqual(self.count("pro_appointments"), before["pro_appointments"])
        r = a.resume("T", self.state, "approve", "E1091", {})
        self.assertEqual(r["pending"]["tool"], "send_email")
        self.assertEqual(self.count("outbox"), before["outbox"])
        r = a.resume("T", self.state, "approve", "E1068", {})
        self.assertEqual(r["status"], "done")
        for table, n in before.items():
            self.assertEqual(self.count(table), n + 1)
        with closing(core.connect()) as c:
            rows = c.execute("SELECT function,approved_by FROM audit_log WHERE kind='write' AND outcome='ok'").fetchall()
        self.assertEqual([(r[0],r[1]) for r in rows], [
            ("create_it_request", "E1091"), ("book_pro_appointment", "E1091"), ("send_email", "E1068")])

    def test_blocked_account_reason_survives_laptop(self):
        self.state["actor"] = "E1007"
        self.state["messages"][-1]["content"] = "Request Joselito's account and laptop."
        args = {**IT, "new_hire_id": "NH-2609"}
        self.create.side_effect = [call("propose_it_request", {**args, "kind": "account"}),
                                  call("propose_it_request", args, "c2"), answer()]
        r = a.run_agent("T", self.state)
        self.assertIn("contract", r["message"].lower())
        r = a.resume("T", self.state, "approve", "E1007", {})
        self.assertIn("contract", r["message"].lower())

    def test_readonly_response(self):
        self.create.side_effect = [call("get_today", {}), answer("Today is Friday.")]
        self.assertEqual(a.run_agent("T", self.state)["message"], "Today is Friday.")


if __name__ == "__main__":
    unittest.main()
