"""
Arize Phoenix + OpenTelemetry observability.

Used by both:
    - CLI Copilot application
    - Streamlit application

The configuration is intentionally idempotent so Streamlit
reruns do not create multiple TracerProviders.
"""

import os
from contextlib import nullcontext

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)


DEFAULT_ENDPOINT = "http://localhost:6006/v1/traces"
DEFAULT_PROJECT = "github-copilot-repository-agent"
SERVICE_NAME = "github-copilot-repository-agent"


_tracing_enabled = False
_tracer_provider = None
_tracer = None
_initialized = False


def configure_tracing():
    """
    Initialize Phoenix tracing exactly once per Python process.
    """

    global _tracing_enabled
    global _tracer_provider
    global _tracer
    global _initialized

    # --------------------------------------------------------
    # Already initialized
    # --------------------------------------------------------

    if _initialized:

        return (
            _tracer_provider,
            os.getenv(
                "PHOENIX_COLLECTOR_ENDPOINT",
                DEFAULT_ENDPOINT,
            ).removesuffix("/v1/traces"),
            os.getenv(
                "PHOENIX_PROJECT_NAME",
                DEFAULT_PROJECT,
            ),
        )

    _initialized = True

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    if (
        os.getenv(
            "PHOENIX_ENABLED",
            "false",
        ).lower()
        != "true"
    ):

        print(
            "[INFO] Phoenix tracing disabled."
        )

        return (
            None,
            "http://localhost:6006",
            DEFAULT_PROJECT,
        )

    if (
        os.getenv(
            "OTEL_SDK_DISABLED",
            "false",
        ).lower()
        == "true"
    ):

        print(
            "[WARN] OTEL_SDK_DISABLED=true"
        )

        print(
            "[WARN] Phoenix tracing disabled."
        )

        return (
            None,
            "http://localhost:6006",
            DEFAULT_PROJECT,
        )

    # --------------------------------------------------------
    # Endpoint
    # --------------------------------------------------------

    endpoint = os.getenv(
        "PHOENIX_COLLECTOR_ENDPOINT",
        DEFAULT_ENDPOINT,
    ).rstrip("/")

    if not endpoint.endswith(
        "/v1/traces"
    ):

        endpoint = (
            f"{endpoint}/v1/traces"
        )

    phoenix_url = endpoint.removesuffix(
        "/v1/traces"
    )

    # --------------------------------------------------------
    # Project
    # --------------------------------------------------------

    project_name = os.getenv(
        "PHOENIX_PROJECT_NAME",
        DEFAULT_PROJECT,
    )

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PHOENIX OTEL CONFIGURATION")
    print("=" * 60)

    print(
        f"Project:       {project_name}"
    )

    print(
        f"Endpoint:      {endpoint}"
    )

    print(
        "Protocol:      OTLP HTTP/protobuf"
    )

    print(
        "Processor:     SimpleSpanProcessor"
    )

    print(
        f"Service name:  {SERVICE_NAME}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Resource
    # --------------------------------------------------------

    resource = Resource.create(
        {
            "service.name":
                SERVICE_NAME,

            "service.version":
                "1.0.0",

            "phoenix.project.name":
                project_name,
        }
    )

    # --------------------------------------------------------
    # Provider
    # --------------------------------------------------------

    provider = TracerProvider(
        resource=resource
    )

    # --------------------------------------------------------
    # Exporter
    # --------------------------------------------------------

    exporter = OTLPSpanExporter(
        endpoint=endpoint
    )

    # --------------------------------------------------------
    # Processor
    # --------------------------------------------------------

    processor = SimpleSpanProcessor(
        exporter
    )

    provider.add_span_processor(
        processor
    )

    # --------------------------------------------------------
    # Global provider
    # --------------------------------------------------------

    trace.set_tracer_provider(
        provider
    )

    _tracer_provider = provider

    _tracer = provider.get_tracer(
        SERVICE_NAME
    )

    _tracing_enabled = True

    print(
        "[OK] Phoenix TracerProvider configured."
    )

    print(
        "[OK] OTLP exporter configured."
    )

    return (
        provider,
        phoenix_url,
        project_name,
    )


def get_tracer():
    """Return the configured tracer."""

    return _tracer


def get_tracer_provider():
    """Return the configured provider."""

    return _tracer_provider


def is_tracing_enabled():
    """Return whether tracing is enabled."""

    return _tracing_enabled


def optional_span(
    name: str,
    attributes: dict | None = None,
):
    """
    Create a span if Phoenix tracing is enabled.
    """

    if (
        not _tracing_enabled
        or _tracer is None
    ):

        return nullcontext()

    return _tracer.start_as_current_span(
        name,
        attributes=attributes or {},
    )


def record_event_span(
    name: str,
    attributes: dict | None = None,
):
    """
    Create and immediately export a short-lived span.
    """

    if (
        not _tracing_enabled
        or _tracer is None
    ):

        return

    with _tracer.start_as_current_span(
        name,
        attributes=attributes or {},
    ):
        pass


def record_tool_span(
    tool_name: str,
    attributes: dict | None = None,
):
    """
    Compatibility function used by the custom repository tools.
    """

    if (
        not _tracing_enabled
        or _tracer is None
    ):

        return nullcontext()

    tool_attributes = {
        "tool.name":
            tool_name,

        "tool.type":
            "custom_repository_tool",
    }

    if attributes:
        tool_attributes.update(
            attributes
        )

    return _tracer.start_as_current_span(
        f"tool.{tool_name}",
        attributes=tool_attributes,
    )


def flush_traces():
    """
    Force pending spans to Phoenix.
    """

    if not _tracing_enabled:
        return True

    if _tracer_provider is None:
        return False

    try:

        result = (
            _tracer_provider.force_flush()
        )

        print(
            f"[OK] Phoenix force_flush result: "
            f"{result}"
        )

        return bool(result)

    except Exception as exc:

        print(
            "[ERROR] Phoenix force_flush failed:"
        )

        print(
            repr(exc)
        )

        return False


def shutdown_tracing():
    """
    Shutdown the tracing provider.
    """

    global _tracing_enabled
    global _tracer
    global _tracer_provider
    global _initialized

    if _tracer_provider is None:
        return

    try:

        _tracer_provider.shutdown()

        print(
            "[OK] Phoenix tracing shutdown complete."
        )

    except Exception as exc:

        print(
            "[WARN] Phoenix shutdown failed:"
        )

        print(
            repr(exc)
        )

    finally:

        _tracing_enabled = False
        _tracer = None
        _tracer_provider = None
        _initialized = False