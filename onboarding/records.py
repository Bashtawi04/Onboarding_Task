"""Structured records stay out of the vector index."""
import csv
from datetime import date, timedelta
from pathlib import Path

DEFAULT_TODAY = date(2026, 10, 16)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def working_days_before(start: date, count: int) -> date:
    if count < 0:
        raise ValueError("count must be nonnegative")
    while count:
        start -= timedelta(days=1)
        if start.weekday() not in (4, 5):  # Friday and Saturday
            count -= 1
    return start


class Records:
    def __init__(self, data: Path):
        self.hires = {r['new_hire_id']: r for r in read_csv(data / 'hris/new_hires.csv')}
        self.tasks = read_csv(data / 'hris/onboarding_tasks.csv')
        self.calendar = {r['month']: r for r in read_csv(data / 'hris/payroll_calendar_2026.csv')}

    def authorised_record(self, asker: str, target: str) -> dict:
        # Trusted CLI test identities only. This is authorization, NOT authentication.
        record = self.hires.get(target)
        if record is None or not (asker == target or asker == record['manager_id']):
            raise PermissionError('I cannot share that record. Please contact HR.')
        return dict(record)

    def first_pay(self, start: str) -> dict:
        joining = date.fromisoformat(start)
        month = joining.strftime('%Y-%m')
        calendar = self.calendar.get(month)
        if calendar is None:
            return {'status': 'unavailable', 'reason': 'Joining month missing from payroll calendar'}
        joining_cutoff = calendar['cutoff_date']
        after_cutoff = joining > date.fromisoformat(joining_cutoff)
        if after_cutoff:
            following = (joining.replace(day=28) + timedelta(days=4)).replace(day=1)
            calendar = self.calendar.get(following.strftime('%Y-%m'))
        if calendar is None:
            return {'status': 'unavailable', 'reason': 'Required pay month missing from payroll calendar'}
        return {
            'status': 'scheduled_under_start_date_rule',
            'pay_date': calendar['pay_date'],
            'joining_date': joining.isoformat(),
            'joining_weekday': joining.strftime('%A'),
            'joining_month_cutoff_date': joining_cutoff,
            'after_joining_month_cutoff': after_cutoff,
            'cutoff_comparison': 'AFTER' if after_cutoff else 'ON OR BEFORE',
            'pay_weekday': date.fromisoformat(calendar['pay_date']).strftime('%A'),
            'coverage': 'joining part-month plus next full month' if after_cutoff else 'joining part-month',
            'condition': 'Payment requires a verified IBAN; confirm unresolved bank details with Payroll.',
            'sources': ['procedures/ONB-04_Payroll_Bank_Account_and_WPS.pdf', 'hris/payroll_calendar_2026.csv'],
        }

    def context(self, asker: str, target: str, today: date = DEFAULT_TODAY) -> dict:
        record = self.authorised_record(asker, target)
        tasks = [dict(t) for t in self.tasks if t['new_hire_id'] == target and t['status'] != 'Done']
        for task in tasks:
            task['overdue'] = date.fromisoformat(task['due_date']) < today
        tasks.sort(key=lambda t: (0 if t['status'] == 'Blocked' else 1 if t['overdue'] else 2, t['due_date']))
        it_account_due = working_days_before(date.fromisoformat(record['start_date']), 1).isoformat()
        recorded_it_task = next((t for t in self.tasks if t['new_hire_id'] == target and t['task_code'] == 'IT_ACCOUNT'), None)
        it_policy_check = {
            'rule': 'IT creates account one Sunday-Thursday working day before start date, subject to HR confirming signed contract',
            'policy_due_date': it_account_due,
            'recorded_task_due_date': recorded_it_task['due_date'] if recorded_it_task else None,
            'task_status': recorded_it_task['status'] if recorded_it_task else 'Not specified',
            'dates_match': (recorded_it_task['due_date'] == it_account_due) if recorded_it_task else None,
            'policy_source': 'procedures/ONB-05_IT_Access_and_Equipment.md, section 1',
            'task_source': 'hris/onboarding_tasks.csv',
        }
        return {
            'today': today.isoformat(), 'record': record, 'open_tasks': tasks,
            'start_weekday': date.fromisoformat(record['start_date']).strftime('%A'),
            'it_account_policy_check': it_policy_check,
            'scheduled_first_pay': self.first_pay(record['start_date']),
            'manager_it_request_due': working_days_before(date.fromisoformat(record['start_date']), 3).isoformat(),
            'date_rule_source': 'procedures/ONB-05_IT_Access_and_Equipment.md, section 2',
            'record_sources': ['hris/new_hires.csv', 'hris/onboarding_tasks.csv'],
        }
