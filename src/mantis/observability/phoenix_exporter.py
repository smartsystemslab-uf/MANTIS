"""Arize Phoenix exporter adapter (Post-Paper Extension, coding plan §11:
"Additional exporters -- Jaeger, Grafana, Langfuse, Phoenix, or other
backends as adapters").

Phoenix (self-hosted or Phoenix Cloud) accepts spans natively over OTLP
gRPC, so -- exactly like `jaeger_exporter.py` / `grafana_exporter.py` --
this is a thin, backend-specific wrapper around the OpenTelemetry SDK's
OTLP span exporter rather than a bespoke protocol integration or a
dependency on the `arize-phoenix-otel` convenience package. Phoenix Cloud
requires an `api_key` header; a local, unauthenticated `phoenix serve`
instance does not.

Registered in `exporter_registry` as "phoenix" exactly like
`jsonl`/`mlflow`/`otel`/`jaeger`/`grafana` -- enabling it is a one-line
addition to `observability.export` in an experiment config, not a code
change.

If no Phoenix (or other OTLP-compatible) collector is reachable at the
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

DEFAULT_PHOENIX_OTLP_ENDPOINT = "http://localhost:4317"


def setup_phoenix_otel(
    service_name: str = "mantis_testbed",
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
) -> bool:
    """Attach a Phoenix-bound OTLP span exporter to the global TracerProvider.

    `api_key`, when set, is sent as the `api_key` gRPC metadata header
    Phoenix Cloud expects; a local `phoenix serve` collector needs none.

    Returns True if the exporter was attached (a collector being reachable
    is not required for this to succeed -- only misconfiguration, e.g. an
    invalid endpoint URL, does), False if attaching failed outright.
    """
    endpoint = endpoint or DEFAULT_PHOENIX_OTLP_ENDPOINT
    try:
        provider = trace.get_tracer_provider()
        if not isinstance(provider, TracerProvider):
            # setup_otel() hasn't run yet for this process -- Phoenix export
            # still needs a real TracerProvider to attach a span processor
            # to, so create one here rather than silently no-op.
            provider = TracerProvider(resource=Resource(attributes={"service.name": service_name}))
            trace.set_tracer_provider(provider)

        headers = {"api_key": api_key} if api_key else None
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=endpoint.startswith("http://"),
            headers=headers,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"Phoenix OTLP exporter attached for service '{service_name}' -> {endpoint}")
        return True
    except Exception as e:
        logger.warning(f"Failed to attach Phoenix exporter: {e}")
        return False
