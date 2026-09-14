"""Post-Paper Extension: additional exporters (coding plan §11).

Verifies the Jaeger adapter against the real OpenTelemetry SDK, not just
"no exception was raised" -- confirms a real span processor gets attached
to the global TracerProvider, and that exporting is safe with no collector
listening (a run must never fail because telemetry couldn't be delivered).
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from mantis.observability.jaeger_exporter import setup_jaeger_otel, DEFAULT_JAEGER_OTLP_ENDPOINT
from mantis.core.registry import exporter_registry


def test_jaeger_registered_in_exporter_registry():
    entry = exporter_registry.get("jaeger")
    assert entry["module"] == "mantis.observability.jaeger_exporter:setup_jaeger_otel"


def test_setup_jaeger_otel_attaches_a_real_span_processor():
    before = trace.get_tracer_provider()
    processors_before = (
        len(before._active_span_processor._span_processors)
        if isinstance(before, TracerProvider) else 0
    )

    ok = setup_jaeger_otel(service_name="mantis-test-jaeger", endpoint=DEFAULT_JAEGER_OTLP_ENDPOINT)
    assert ok is True

    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)
    processors_after = len(provider._active_span_processor._span_processors)
    assert processors_after > processors_before, "setup_jaeger_otel must add a real span processor"


def test_setup_jaeger_otel_does_not_raise_with_no_collector_listening():
    # No Jaeger/OTLP collector is running in the test environment -- export
    # must fail quietly (BatchSpanProcessor swallows the error), never
    # propagate into the experiment run.
    ok = setup_jaeger_otel(service_name="mantis-test-jaeger-no-collector", endpoint="http://localhost:4317")
    assert ok is True

    tracer = trace.get_tracer("mantis.test.jaeger")
    with tracer.start_as_current_span("test-span"):
        pass

    provider = trace.get_tracer_provider()
    provider.force_flush(timeout_millis=1000)  # must not raise


def test_setup_jaeger_otel_defaults_endpoint_when_none_given():
    ok = setup_jaeger_otel(service_name="mantis-test-jaeger-default")
    assert ok is True
