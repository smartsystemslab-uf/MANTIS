"""Ported from Citi_P3's citi_banking_adk/bank_adk/sar_prompt.py: formats
compiled AML case facts into deterministic SAR drafting prompt context, so
the SAR drafting agent works off the investigator's actual findings instead
of inventing names/amounts/dates itself."""
from typing import Any


def format_sar_case_facts(case_facts: dict[str, Any]) -> str:
    """Format compiled AML case facts into deterministic SAR prompt context."""
    if not isinstance(case_facts, dict):
        case_facts = {}

    sections = [
        ("Names", case_facts.get("names", [])),
        ("Amounts", case_facts.get("amounts", [])),
        ("Dates", case_facts.get("dates", [])),
        ("Red flags", case_facts.get("red_flags", [])),
    ]

    lines = ["Compiled SAR case facts:"]

    for label, values in sections:
        lines.append(f"{label}:")

        if values is None:
            values = []
        elif not isinstance(values, (list, tuple)):
            values = [values]

        if values:
            lines.extend(f"- {value}" for value in values)
        else:
            lines.append("- none provided")

    return "\n".join(lines)
