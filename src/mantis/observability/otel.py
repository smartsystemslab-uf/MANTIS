from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)

def setup_otel(service_name: str = "mantis_testbed", enable_console: bool = False):
    """Initializes the OpenTelemetry TracerProvider."""
    try:
        resource = Resource(attributes={
            "service.name": service_name
        })

        provider = TracerProvider(resource=resource)
        
        if enable_console:
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            
        trace.set_tracer_provider(provider)
        logger.info(f"OpenTelemetry initialized for service: {service_name}")
    except Exception as e:
        logger.warning(f"Failed to setup OpenTelemetry: {e}")

def get_tracer(name: str = "mantis.tracer"):
    return trace.get_tracer(name)
