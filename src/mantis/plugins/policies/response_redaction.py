"""Response redaction filter (Post-Paper Extension, coding plan §11:
"Security mechanism plugins -- guardrails, policy checks, isolation, rate
limits, and response filters evaluated through the same experiment
framework").

A "response filter": watches the output control point and masks
account-number-shaped tokens (the same `XXX-###` id shape used throughout
the seeded banking data -- CHK-001, EXT-998, SVG-001, and so on) before
the final result reaches whoever asked. Registers at the same "output"
stage `mantis.banking.runner.run_message` now genuinely dispatches with
the real compacted result (see the fix alongside this file), not just the
workflow's terminal-state classification -- without that fix, this
plugin's MUTATE would be recorded in the trace while changing nothing the
caller actually sees, the same defect class this project has already
found and fixed once at the tool control point.
"""
import json
import re

from mantis.hooks import HookContext, HookAction, HookResult

# Matches the real account-id shape seeded throughout this codebase:
# 2-4 uppercase letters, a hyphen, 3+ digits (CHK-001, EXT-998, ACC-CHK-1001, ...).
#
# The hyphen class below is deliberately wider than ASCII "-": a live run
# of this exact demo (response_redaction_demo.yaml) showed an LLM writing
# account ids in prose/markdown using a Unicode non-breaking hyphen
# (U+2011, "CUST‑002") rather than ASCII "-", which an ASCII-only
# regex silently fails to match -- not a rare edge case but the kind of
# thing a live LLM does routinely when formatting text, and exactly the
# gap this project's practice of live-verifying (not just unit-testing)
# every plugin exists to catch.
_HYPHENS = "-‐‑‒–—−"
_ACCOUNT_ID_RE = re.compile(rf"\b([A-Z]{{2,4}}[{_HYPHENS}])+\d{{3,}}\b")


def _redact_account_ids(value):
    """Recursively walk a JSON-shaped value (dict / list / str / other) and
    mask every account-id-shaped token found in any string, keeping only
    the last 2 characters visible (CHK-001 -> CHK-**1)."""
    if isinstance(value, dict):
        return {k: _redact_account_ids(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_account_ids(v) for v in value]
    if isinstance(value, str):
        text = value

        def _mask(match: re.Match) -> str:
            token = match.group(0)
            # rfind over each hyphen variant, not just ASCII "-" -- see the
            # _HYPHENS comment above _ACCOUNT_ID_RE for why this matters.
            prefix_end = max(token.rfind(h) for h in _HYPHENS) + 1
            prefix, digits = token[:prefix_end], token[prefix_end:]
            if len(digits) <= 2:
                return token
            return prefix + "*" * (len(digits) - 2) + digits[-2:]

        redacted = _ACCOUNT_ID_RE.sub(_mask, text)
        # Tool results are frequently a JSON string rather than a native
        # dict (every banking tool in this codebase returns json.dumps(...)),
        # so also redact inside any parseable JSON string's own structure to
        # catch account ids that survive re-serialization unchanged.
        try:
            parsed = json.loads(text)
        except (TypeError, ValueError):
            return redacted
        if isinstance(parsed, (dict, list)):
            return json.dumps(_redact_account_ids(parsed))
        return redacted
    return value


class ResponseRedactionPlugin:
    name = "response_redaction"
    supported_stages = {"output"}

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def apply(self, ctx: HookContext) -> HookResult:
        events = (ctx.payload or {}).get("events")
        if events is None:
            return HookResult(action=HookAction.CONTINUE)

        redacted = _redact_account_ids(events)
        if redacted == events:
            return HookResult(action=HookAction.CONTINUE)
        return HookResult(action=HookAction.MUTATE, payload={"events": redacted})
