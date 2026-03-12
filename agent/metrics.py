"""
metrics.py — Prometheus Observability Layer for Zodit Gold
Exposes a /metrics endpoint compatible with Prometheus scraping.
"""
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)
from fastapi import APIRouter, Response
from logger import log

# ============================================================
# METRIC DEFINITIONS
# ============================================================

# Request counters
REQUESTS_TOTAL = Counter(
    "zodit_requests_total",
    "Total number of requests handled by the orchestrator",
    ["sender", "tool"]
)

# Cache metrics
CACHE_HITS = Counter(
    "zodit_cache_hits_total",
    "Total number of Semantic Cache HIT events"
)

CACHE_MISSES = Counter(
    "zodit_cache_misses_total",
    "Total number of Semantic Cache MISS events"
)

# Latency histogram for LLM responses
LLM_LATENCY = Histogram(
    "zodit_llm_response_seconds",
    "Histogram of LLM response latency in seconds",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

# Active sessions gauge
ACTIVE_SESSIONS = Gauge(
    "zodit_active_sessions",
    "Current number of active chat sessions"
)

# Error counter
ERRORS_TOTAL = Counter(
    "zodit_errors_total",
    "Total number of errors",
    ["component"]
)

# WhatsApp messages counter
WHATSAPP_MESSAGES = Counter(
    "zodit_whatsapp_messages_total",
    "Total WhatsApp messages sent",
    ["direction"]  # inbound / outbound
)

# Tool execution summary
TOOL_EXEC_SUMMARY = Summary(
    "zodit_tool_execution_seconds",
    "Time spent executing individual tools",
    ["tool_name"]
)

# ============================================================
# ROUTER
# ============================================================
router = APIRouter()

@router.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    """Prometheus-compatible scrape endpoint."""
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

# ============================================================
# HELPER FUNCTIONS — call these throughout the codebase
# ============================================================

def record_request(sender: str, tool: str):
    """Increment the global request counter."""
    REQUESTS_TOTAL.labels(sender=sender, tool=tool).inc()

def record_cache_hit():
    """Record a Semantic Cache HIT."""
    CACHE_HITS.inc()

def record_cache_miss():
    """Record a Semantic Cache MISS."""
    CACHE_MISSES.inc()

def record_error(component: str):
    """Increment the error counter for a specific component."""
    ERRORS_TOTAL.labels(component=component).inc()
    log.error(f"[METRICS] Error recorded for component: {component}")

def set_active_sessions(count: int):
    """Update the gauge of active sessions."""
    ACTIVE_SESSIONS.set(count)

def record_whatsapp(direction: str = "outbound"):
    """Record a WhatsApp message event (inbound or outbound)."""
    WHATSAPP_MESSAGES.labels(direction=direction).inc()
