"""Jaeger exporter adapter (Post-Paper Extension, coding plan §11:
"Additional exporters -- Jaeger, Grafana, Langfuse, Phoenix, or other
backends as adapters").

Jaeger (v1.35+) accepts spans natively over OTLP, so this adapter is a
thin, Jaeger-specific wrapper around the OpenTelemetry SDK's OTLP span
exporter rather than a bespoke protocol integration: it attaches an
OTLPSpanExporter, over gRPC, to the same TracerProvider
`mantis.observability.otel.setup_otel` configures. Registered in
`exporter_registry` as "jaeger" exactly like `jsonl`/`mlflow`/`otel` --
enabling it is a one-line addition to `observability.export` in an
experiment config, not a code change.

If no Jaeger (or other OTLP-compatible) collector is reachable at the
configured endpoint, span export fails silently in the background (the
SDK's BatchSpanProcessor retries and logs a warning; it does not raise
into the run) -- exporting telemetry must never be able to fail an
experiment run.
"""
import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)

DEFAULT_JAEGER_OTLP_ENDPOINT = "http://localhost:4317"


def setup_jaeger_otel(service_name: str = "mantis_testbed", endpoint: str = None) -> bool:
    """Attach a Jaeger-bound OTLP span exporter to the global TracerProvider.

    Returns True if the exporter was attached (a collector being reachable
    is not required for this to succeed -- only misconfiguration, e.g. an
    invalid endpoint URL, does), False if attaching failed outright.
    """
    endpoint = endpoint or DEFAULT_JAEGER_OTLP_ENDPOINT
    try:
        provider = trace.get_tracer_provider()
        if not isinstance(provider, TracerProvider):
            # setup_otel() hasn't run yet for this process -- Jaeger export
            # still needs a real TracerProvider to attach a span processor
            # to, so create one here rather than silently no-op.
            provider = TracerProvider(resource=Resource(attributes={"service.name": service_name}))
            trace.set_tracer_provider(provider)

        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=endpoint.startswith("http://"))
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"Jaeger OTLP exporter attached for service '{service_name}' -> {endpoint}")
        return True
    except Exception as e:
        logger.warning(f"Failed to attach Jaeger exporter: {e}")
        return False
