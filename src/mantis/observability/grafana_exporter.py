"""Grafana (Tempo) exporter adapter (Post-Paper Extension, coding plan §11:
"Additional exporters -- Jaeger, Grafana, Langfuse, Phoenix, or other
backends as adapters").

Grafana Tempo (self-hosted or Grafana Cloud) accepts spans natively over
OTLP gRPC, so -- exactly like `jaeger_exporter.py` -- this is a thin,
backend-specific wrapper around the OpenTelemetry SDK's OTLP span exporter
rather than a bespoke protocol integration. The only real difference from
Jaeger is that Grafana Cloud's managed OTLP endpoint requires HTTP Basic
auth (instance ID as username, API token as password), which self-hosted
Tempo does not -- so this adapter accepts an optional `auth_header` instead
of assuming an open localhost collector.

Registered in `exporter_registry` as "grafana" exactly like
`jsonl`/`mlflow`/`otel`/`jaeger` -- enabling it is a one-line addition to
`observability.export` in an experiment config, not a code change.

If no Tempo (or other OTLP-compatible) collector is reachable at the
configured endpoint, span export fails silently in the background (the
SDK's BatchSpanProcessor retries and logs a warning; it does not raise
into the run) -- exporting telemetry must never be able to fail an
experiment run.
"""
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)

DEFAULT_GRAFANA_OTLP_ENDPOINT = "http://localhost:4317"


def setup_grafana_otel(
    service_name: str = "mantis_testbed",
    endpoint: Optional[str] = None,
    auth_header: Optional[str] = None,
) -> bool:
    """Attach a Grafana-Tempo-bound OTLP span exporter to the global TracerProvider.

    `auth_header` is the full "Basic <base64>" (or "Bearer <token>") value
    Grafana Cloud's OTLP gateway expects, if using a managed instance rather
    than a local, unauthenticated Tempo collector.

    Returns True if the exporter was attached (a collector being reachable
    is not required for this to succeed -- only misconfiguration, e.g. an
    invalid endpoint URL, does), False if attaching failed outright.
    """
    endpoint = endpoint or DEFAULT_GRAFANA_OTLP_ENDPOINT
    try:
        provider = trace.get_tracer_provider()
        if not isinstance(provider, TracerProvider):
            # setup_otel() hasn't run yet for this process -- Grafana export
            # still needs a real TracerProvider to attach a span processor
            # to, so create one here rather than silently no-op.
            provider = TracerProvider(resource=Resource(attributes={"service.name": service_name}))
            trace.set_tracer_provider(provider)

        headers = {"Authorization": auth_header} if auth_header else None
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=endpoint.startswith("http://"),
            headers=headers,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"Grafana (Tempo) OTLP exporter attached for service '{service_name}' -> {endpoint}")
        return True
    except Exception as e:
        logger.warning(f"Failed to attach Grafana exporter: {e}")
        return False
