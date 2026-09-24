"""Post-Paper Extension: security mechanism plugins (coding plan §11).

Covers response_redaction's own logic in isolation, its registration, and
its behavior at the real "output" control point through the HookBus.
Includes a regression test for a real gap found via live verification:
an LLM naturally wrote an account id using a Unicode non-breaking hyphen
rather than ASCII "-", which the original regex silently missed.
"""
from mantis.hooks import HookBus, HookContext, HookAction
from mantis.plugins.policies.response_redaction import ResponseRedactionPlugin, _redact_account_ids
from mantis.core.registry import plugin_registry


def test_response_redaction_registered():
    cls = plugin_registry.get("response_redaction")
    assert cls is ResponseRedactionPlugin


def test_redacts_account_id_in_a_plain_string():
    assert _redact_account_ids("Transfer from CHK-002 to EXT-998") == "Transfer from CHK-*02 to EXT-*98"


def test_redacts_account_ids_with_unicode_hyphen_variants():
    """Regression test: a live run of response_redaction_demo.yaml showed
    an LLM writing 'CUST‑002' (U+2011 non-breaking hyphen) in prose
    instead of ASCII '-', which an ASCII-only regex silently failed to
    match and left completely unredacted."""
    text = "Transfer from CHK-002 to EXT‑998 for CUST–002"
    result = _redact_account_ids(text)
    assert "EXT‑998" not in result, "the full unmasked account id must not survive"
    assert "CUST–002" not in result
    assert result == "Transfer from CHK-*02 to EXT‑*98 for CUST–*02"


def test_redacts_account_ids_nested_in_dicts_and_lists():
    value = {"account": "CHK-001", "history": ["EXT-998", {"customer": "CUST-002"}]}
    redacted = _redact_account_ids(value)
    assert redacted == {"account": "CHK-*01", "history": ["EXT-*98", {"customer": "CUST-*02"}]}


def test_redacts_account_ids_inside_a_json_string_tool_result():
    import json
    raw = json.dumps({"source_account": "CHK-002", "destination_account": "EXT-998"})
    redacted = json.loads(_redact_account_ids(raw))
    assert redacted == {"source_account": "CHK-*02", "destination_account": "EXT-*98"}


def test_leaves_text_with_no_account_ids_unchanged():
    assert _redact_account_ids("no account ids here") == "no account ids here"


def test_apply_continues_when_no_events_in_payload():
    plugin = ResponseRedactionPlugin()
    ctx = HookContext(run_id="test", trace_id="test", workflow_id="test", stage="output", payload={})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_apply_continues_when_events_contain_no_account_ids():
    plugin = ResponseRedactionPlugin()
    ctx = HookContext(run_id="test", trace_id="test", workflow_id="test", stage="output", payload={"events": {"summary": "all clear"}})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_apply_mutates_when_events_contain_an_account_id():
    plugin = ResponseRedactionPlugin()
    ctx = HookContext(run_id="test", trace_id="test", workflow_id="test", stage="output", payload={"events": {"customer_message": "Sent to CHK-001"}})
    res = plugin.apply(ctx)
    assert res.action == HookAction.MUTATE
    assert res.payload["events"]["customer_message"] == "Sent to CHK-*01"


def test_redacts_through_the_real_hook_bus_at_the_output_stage():
    """The actual point of this extension: register the plugin on a real
    HookBus and confirm the bus's aggregate MUTATE reaches the caller for
    an output-stage dispatch, the same as mantis.banking.runner.run_message
    depends on."""
    hooks = HookBus()
    hooks.register(ResponseRedactionPlugin())

    ctx = HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage="output", source="run", target="final_result",
        payload={"events": {"customer_message": "The transfer to EXT-998 has completed."}},
    )
    result = hooks.dispatch("after_output", ctx)

    assert result.action == HookAction.MUTATE
    assert result.payload["events"]["customer_message"] == "The transfer to EXT-*98 has completed."
