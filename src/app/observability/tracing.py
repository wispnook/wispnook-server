from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config.settings import settings

# Suppress noisy OTLP exporter errors when collector is not available
logging.getLogger("opentelemetry.exporter.otlp").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.sdk.trace.export").setLevel(logging.CRITICAL)


def configure_tracing() -> bool:
    """Configure OpenTelemetry tracing if endpoint is configured."""
    if not settings.otel_exporter_otlp_endpoint:
        return False

    try:
        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)

        # Create OTLP exporter with timeout to fail fast
        span_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            timeout=5  # 5 second timeout to fail fast
        )
        span_processor = BatchSpanProcessor(span_exporter)
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)
        return True
    except Exception as e:
        # Log but don't fail the application if tracing setup fails
        logging.warning(f"Failed to configure tracing: {e}")
        return False


def instrument_app(app) -> None:  # type: ignore[annotations]
    """Instrument FastAPI app with OpenTelemetry if configured."""
    if settings.otel_exporter_otlp_endpoint:
        try:
            FastAPIInstrumentor.instrument_app(app)
        except Exception as e:
            logging.warning(f"Failed to instrument app with tracing: {e}")
