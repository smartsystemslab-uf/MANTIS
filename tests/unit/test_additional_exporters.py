"""Post-Paper Extension: additional exporters (coding plan §11) -- Grafana
Tempo, Phoenix (both OTLP/gRPC, same adapter shape as Jaeger, see
test_jaeger_exporter.py), and Langfuse (OTLP/HTTP, the one backend that
genuinely needs a different exporter transport and Basic-auth credentials).

Verifies each adapter against the real OpenTelemetry SDK, not just "no
exception was raised" -- confirms a real span processor gets attached to
the global TracerProvider, and that exporting is safe with no collector
listening (a run must never fail because telemetry couldn't be delivered).

Requires the optional `exporters` dependency group (`pip install -e
".[exporters]"`) -- skipped, not failed, when it isn't installed, since
the base install this project documents for the offline test suite does
not include it.
"""
import pytest

pytest.importorskip("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from mantis.observability.grafana_exporter import setup_grafana_otel, DEFAULT_GRAFANA_OTLP_ENDPOINT
from mantis.observability.phoenix_exporter import setup_phoenix_otel, DEFAULT_PHOENIX_OTLP_ENDPOINT
from mantis.observability.langfuse_exporter import setup_langfuse_otel, DEFAULT_LANGFUSE_OTLP_ENDPOINT
from mantis.core.registry import exporter_registry


def _processor_count(provider):
    return len(provider._active_span_processor._span_processors) if isinstance(provider, TracerProvider) else 0


def test_all_three_registered_in_exporter_registry():
    assert exporter_registry.get("grafana")["module"] == "mantis.observability.grafana_exporter:setup_grafana_otel"
    assert exporter_registry.get("phoenix")["module"] == "mantis.observability.phoenix_exporter:setup_phoenix_otel"
    assert exporter_registry.get("langfuse")["module"] == "mantis.observability.langfuse_exporter:setup_langfuse_otel"


def test_setup_grafana_otel_attaches_a_real_span_processor():
    before = _processor_count(trace.get_tracer_provider())
    ok = setup_grafana_otel(service_name="mantis-test-grafana", endpoint=DEFAULT_GRAFANA_OTLP_ENDPOINT)
    assert ok is True
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)
    assert _processor_count(provider) > before


def test_setup_grafana_otel_accepts_a_cloud_auth_header_without_raising():
    ok = setup_grafana_otel(
        service_name="mantis-test-grafana-cloud",
        endpoint="https://tempo-us-central1.grafana.net:443",
        auth_header="Basic ZmFrZTpjcmVkZW50aWFscw==",
    )
    assert ok is True


def test_setup_phoenix_otel_attaches_a_real_span_processor():
    before = _processor_count(trace.get_tracer_provider())
    ok = setup_phoenix_otel(service_name="mantis-test-phoenix", endpoint=DEFAULT_PHOENIX_OTLP_ENDPOINT)
    assert ok is True
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)
    assert _processor_count(provider) > before


def test_setup_phoenix_otel_accepts_an_api_key_without_raising():
    ok = setup_phoenix_otel(
        service_name="mantis-test-phoenix-cloud",
        endpoint="https://app.phoenix.arize.com/v1/traces",
        api_key="fake-phoenix-key",
    )
    assert ok is True


def test_setup_langfuse_otel_attaches_a_real_span_processor():
    before = _processor_count(trace.get_tracer_provider())
    ok = setup_langfuse_otel(service_name="mantis-test-langfuse", endpoint=DEFAULT_LANGFUSE_OTLP_ENDPOINT)
    assert ok is True
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)
    assert _processor_count(provider) > before


def test_setup_langfuse_otel_builds_a_real_basic_auth_header_from_credentials():
    import base64
    from unittest.mock import patch

    captured = {}

    class _CapturingExporter:
        def __init__(self, endpoint=None, headers=None):
            captured["endpoint"] = endpoint
            captured["headers"] = headers

        def export(self, spans):
            from opentelemetry.sdk.trace.export import SpanExportResult
            return SpanExportResult.SUCCESS

        def shutdown(self):
            pass

    with patch("mantis.observability.langfuse_exporter.OTLPSpanExporter", _CapturingExporter):
        ok = setup_langfuse_otel(
            service_name="mantis-test-langfuse-auth",
            public_key="pk-lf-test",
            secret_key="sk-lf-test",
        )
    assert ok is True
    expected = base64.b64encode(b"pk-lf-test:sk-lf-test").decode()
    assert captured["headers"] == {"Authorization": f"Basic {expected}"}


def test_setup_langfuse_otel_does_not_raise_with_no_collector_listening():
    # No real Langfuse endpoint is reachable in the test environment --
    # export must fail quietly (BatchSpanProcessor swallows the error),
    # never propagate into the experiment run.
    ok = setup_langfuse_otel(service_name="mantis-test-langfuse-no-collector")
    assert ok is True

    tracer = trace.get_tracer("mantis.test.langfuse")
    with tracer.start_as_current_span("test-span"):
        pass

    provider = trace.get_tracer_provider()
    provider.force_flush(timeout_millis=1000)  # must not raise


def test_all_three_default_endpoint_when_none_given():
    assert setup_grafana_otel(service_name="mantis-test-grafana-default") is True
    assert setup_phoenix_otel(service_name="mantis-test-phoenix-default") is True
    assert setup_langfuse_otel(service_name="mantis-test-langfuse-default") is True
