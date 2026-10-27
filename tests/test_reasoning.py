"""Offline validation tests; no Azure requests, keys or vector index required."""
import unittest
from datetime import date
from pathlib import Path

from onboarding.records import Records
from onboarding.validation import (
    correct_weekday_adjacent_to_iso_date,
    has_false_cutoff_comparison,
    deterministic_payroll_explanation,
)

ROOT = Path(__file__).resolve().parents[1]


class DateReasoningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = Records(ROOT / 'data')

    def test_joining_cutoff_comparison_is_after(self):
        pay = self.records.first_pay('2026-09-27')
        self.assertTrue(pay['after_joining_month_cutoff'])
        self.assertEqual(pay['joining_month_cutoff_date'], '2026-09-15')
        self.assertEqual(pay['pay_date'], '2026-10-28')

    def test_payroll_false_cutoff_detected(self):
        pay = self.records.first_pay('2026-09-27')
        mistaken = 'Joining was on or before the September payroll cut-off.'
        self.assertTrue(has_false_cutoff_comparison(mistaken, pay))
        correct = 'Joining was after the September payroll cut-off.'
        self.assertFalse(has_false_cutoff_comparison(correct, pay))

    def test_payroll_fallback_contains_verifiable_dates(self):
        pay = self.records.first_pay('2026-09-27')
        answer = deterministic_payroll_explanation(pay)
        self.assertIn('**after**', answer)
        self.assertIn('2026-09-15', answer)
        self.assertIn('2026-10-28', answer)
        self.assertIn('verified IBAN', answer)

    def test_arabic_weekday_corrected(self):
        answer = 'أول يوم هو الجمعة 2026-11-01.'
        corrected = correct_weekday_adjacent_to_iso_date(answer, '2026-11-01')
        self.assertEqual(corrected, 'أول يوم هو الأحد 2026-11-01.')

    def test_true_weekday_unchanged(self):
        answer = 'Start on Sunday 2026-11-01.'
        self.assertEqual(correct_weekday_adjacent_to_iso_date(answer, '2026-11-01'), answer)

    def test_other_dates_not_rewritten(self):
        answer = 'Friday 2026-11-06 is the deadline; Sunday 2026-11-01 is your start.'
        self.assertEqual(correct_weekday_adjacent_to_iso_date(answer, '2026-11-01'), answer)

    def test_known_employee_start_weekday(self):
        ctx = self.records.context('NH-2608', 'NH-2608', date(2026, 10, 16))
        self.assertEqual(ctx['start_weekday'], 'Sunday')


if __name__ == '__main__':
    unittest.main()
