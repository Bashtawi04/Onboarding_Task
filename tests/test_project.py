import unittest
from datetime import date
from pathlib import Path
from onboarding.records import Records, working_days_before
from onboarding.documents import manifest

ROOT=Path(__file__).resolve().parents[1]

class AgentFoundations(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.records=Records(ROOT/'data')

    def test_it_creation_date_and_task_match(self):
        ctx=self.records.context('NH-2606','NH-2606',date(2026,10,16))
        c=ctx['it_account_policy_check']
        self.assertEqual(c['policy_due_date'],'2026-10-22')
        self.assertEqual(c['recorded_task_due_date'],'2026-10-22')
        self.assertTrue(c['dates_match'])
        self.assertEqual(ctx['manager_it_request_due'],'2026-10-20')

    def test_no_other_employee_access(self):
        with self.assertRaises(PermissionError):
            self.records.context('NH-2607','NH-2610')

    def test_direct_report_access(self):
        ctx=self.records.context('E1084','NH-2610')
        self.assertEqual(ctx['record']['new_hire_id'],'NH-2610')

    def test_working_day_weekend(self):
        self.assertEqual(working_days_before(date(2026,10,25),1),date(2026,10,22))
        self.assertEqual(working_days_before(date(2026,10,25),3),date(2026,10,20))

    def test_outdated_policy_excluded(self):
        files=[m['file_path'] for m in manifest(ROOT/'data')]
        self.assertIn('procedures/ONB-05_IT_Access_and_Equipment.md',files)
        self.assertNotIn('procedures/archive/ONB-05_IT_Access_v1.0.pdf',files)

    def test_only_own_tasks(self):
        ctx=self.records.context('NH-2606','NH-2606')
        self.assertTrue(all(t['new_hire_id']=='NH-2606' for t in ctx['open_tasks']))
        self.assertEqual(len(ctx['open_tasks']),8)

if __name__=='__main__': unittest.main()
