"""Deterministic validation of simple calendar claims in model answers.

These helpers are deliberately pure so they can be tested without Azure.
"""

import re
from datetime import date

def correct_weekday_adjacent_to_iso_date(answer, iso_date):
    """Correct an incorrect weekday directly attached to a trusted ISO start date.

    Only edits an immediately preceding weekday; does not manufacture unseen dates.
    """
    date_obj = date.fromisoformat(iso_date)
    english = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    arabic = ['الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت','الأحد']
    weekday = date_obj.weekday()
    labels = english + arabic
    pattern = r'(?<!\w)(' + '|'.join(map(re.escape, labels)) + r')(\s+)' + re.escape(iso_date)
    def replace(match):
        found = match.group(1)
        proper = arabic[weekday] if found in arabic else english[weekday]
        return proper + match.group(2) + iso_date
    return re.sub(pattern, replace, answer, flags=re.IGNORECASE)


def has_false_cutoff_comparison(answer, first_pay):
    """Catch the observed inverted comparison; always use Python-calculated facts."""
    if first_pay.get('status') != 'scheduled_under_start_date_rule':
        return False
    after = first_pay.get('after_joining_month_cutoff')
    if after:
        return bool(re.search(r'(?:on or before|before|earlier than)\s+(?:the\s+)?(?:\w+\s+){0,3}(?:payroll\s+)?cut.?off',answer,re.I))
    return bool(re.search(r'after\s+(?:the\s+)?(?:\w+\s+){0,3}(?:payroll\s+)?cut.?off',answer,re.I))


def deterministic_payroll_explanation(first_pay):
    """Fail-safe response if the model reverses the payroll cutoff condition."""
    comparator = 'after' if first_pay['after_joining_month_cutoff'] else 'on or before'
    return (
        f"You joined on **{first_pay['joining_date']}**, which is **{comparator}** "
        f"the payroll cut-off of **{first_pay['joining_month_cutoff_date']}**. "
        f"Your first salary is scheduled for **{first_pay['pay_date']}** "
        f"({first_pay['pay_weekday']}) and covers {first_pay['coverage']}. "
        f"This is a scheduled date, not payment confirmation; payment requires "
        f"a verified IBAN. [R1][R3]"
    )


