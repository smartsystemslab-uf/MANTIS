"""Langfuse exporter adapter (Post-Paper Extension, coding plan §11:
"Additional exporters -- Jaeger, Grafana, Langfuse, Phoenix, or other
backends as adapters").

Unlike Jaeger/Grafana/Phoenix, Langfuse's OTLP ingestion endpoint
(`/api/public/otel`) is HTTP/protobuf only, not gRPC, and always requires
HTTP Basic auth (a Langfuse public key as the username, secret key as the
password) even for a self-hosted instance -- so this adapter is built on
`opentelemetry.exporter.otlp.proto.http` rather than the `.grpc` exporter
the other three backends share, and takes credentials instead of an
optional auth header.

Registered in `exporter_registry` as "langfuse" exactly like
`jsonl`/`mlflow`/`otel`/`jaeger`/`grafana`/`phoenix` -- enabling it is a
one-line addition to `observability.export` in an experiment config, not a
code change.

If Langfuse is unreachable or rejects the credentials, span export fails
silently in the background (the SDK's BatchSpanProcessor retries and logs
a warning; it does not raise into the run) -- exporting telemetry must
never be able to fail an experiment run.
"""
import base64
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)

DEFAULT_LANGFUSE_OTLP_ENDPOINT = "https://cloud.langfuse.com/api/public/otel/v1/traces"


def setup_langfuse_otel(
    service_name: str = "mantis_testbed",
    endpoint: Optional[str] = None,
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
) -> bool:
    """Attach a Langfuse-bound OTLP/HTTP span exporter to the global TracerProvider.

    `public_key`/`secret_key` are Langfuse's project API credentials,
    encoded here as the HTTP Basic auth header Langfuse's OTLP endpoint
    requires. Omitting them attaches the exporter unauthenticated, which
    Langfuse will reject at export time -- caught the same way an
    unreachable collector is, not raised into the run.

    Returns True if the exporter was attached (Langfuse being reachable and
    the credentials being valid are not required for this to succeed --
    only misconfiguration, e.g. an invalid endpoint URL, does), False if
    attaching failed outright.
    """
    endpoint = endpoint or DEFAULT_LANGFUSE_OTLP_ENDPOINT
    try:
        provider = trace.get_tracer_provider()
        if not isinstance(provider, TracerProvider):
            # setup_otel() hasn't run yet for this process -- Langfuse export
            # still needs a real TracerProvider to attach a span processor
            # to, so create one here rather than silently no-op.
            provider = TracerProvider(resource=Resource(attributes={"service.name": service_name}))
            trace.set_tracer_provider(provider)

        headers = None
        if public_key and secret_key:
            token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
            headers = {"Authorization": f"Basic {token}"}

        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"Langfuse OTLP/HTTP exporter attached for service '{service_name}' -> {endpoint}")
        return True
    except Exception as e:
        logger.warning(f"Failed to attach Langfuse exporter: {e}")
        return False
