"""
Miadi Integration Adapter

Enables narrative-tracing to inject trace correlation headers into HTTP calls
to Miadi, so traces flow across system boundaries.

Miadi is the webhook consumer and episode generator. When events flow from
GitHub webhooks through LangGraph's three-universe processing and into
episode generation, this adapter ensures the trace correlation persists.

Key Features:
- HTTP header injection for outgoing requests
- Header extraction for incoming requests  
- Webhook event tracing
- Episode boundary detection
- Redis event queue correlation

Usage:
```python
from narrative_tracing import NarrativeTracingHandler
from narrative_tracing.adapters import MiadiIntegration

handler = NarrativeTracingHandler(story_id="story_123")
miadi = MiadiIntegration(handler)

# Inject headers for outgoing HTTP call to Miadi
headers = miadi.inject_correlation_headers({})
response = requests.post(miadi_url, json=event, headers=headers)

# Extract correlation from incoming request (in Miadi)
trace_id, story_id = miadi.extract_correlation(request.headers)

# Log webhook events
miadi.log_webhook_received(event_id, event_type, source)
miadi.log_webhook_transformed(event_id, output_format)
```

Session ID: langchain-narrative-tracing
Created: 2026-01-30
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

from ..handler import NarrativeTracingHandler
from ..event_types import NarrativeEventType


# =============================================================================
# CONSTANTS
# =============================================================================

# Standard correlation headers
HEADER_TRACE_ID = "X-Narrative-Trace-Id"
HEADER_STORY_ID = "X-Story-Id"
HEADER_SESSION_ID = "X-Session-Id"
HEADER_PARENT_SPAN_ID = "X-Parent-Span-Id"
HEADER_BEAT_ID = "X-Beat-Id"
HEADER_EPISODE_ID = "X-Episode-Id"

# All headers for convenience
ALL_CORRELATION_HEADERS = [
    HEADER_TRACE_ID,
    HEADER_STORY_ID,
    HEADER_SESSION_ID,
    HEADER_PARENT_SPAN_ID,
    HEADER_BEAT_ID,
    HEADER_EPISODE_ID,
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CorrelationContext:
    """Extracted correlation context from headers."""
    
    trace_id: Optional[str] = None
    story_id: Optional[str] = None
    session_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    beat_id: Optional[str] = None
    episode_id: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if we have minimum required correlation data."""
        return self.trace_id is not None
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "story_id": self.story_id,
            "session_id": self.session_id,
            "parent_span_id": self.parent_span_id,
            "beat_id": self.beat_id,
            "episode_id": self.episode_id,
        }
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> "CorrelationContext":
        """Create from HTTP headers dictionary."""
        return cls(
            trace_id=headers.get(HEADER_TRACE_ID),
            story_id=headers.get(HEADER_STORY_ID),
            session_id=headers.get(HEADER_SESSION_ID),
            parent_span_id=headers.get(HEADER_PARENT_SPAN_ID),
            beat_id=headers.get(HEADER_BEAT_ID),
            episode_id=headers.get(HEADER_EPISODE_ID),
        )


@dataclass
class WebhookEvent:
    """Represents a webhook event for tracing."""
    
    event_id: str
    event_type: str  # e.g., "github.push", "github.issue"
    source: str  # e.g., "github", "gitlab"
    payload_preview: str = ""
    timestamp: str = ""
    repository: Optional[str] = None
    sender: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "payload_preview": self.payload_preview,
            "timestamp": self.timestamp,
            "repository": self.repository,
            "sender": self.sender,
        }


# =============================================================================
# MIADI INTEGRATION
# =============================================================================

class MiadiIntegration:
    """
    Integration adapter for Miadi webhook consumer and episode generator.
    
    Provides HTTP header-based trace correlation so that traces flow
    seamlessly from:
    - GitHub webhooks received by Miadi
    - Through LangGraph three-universe processing
    - Into episode generation and storage
    
    Args:
        handler: NarrativeTracingHandler instance for logging
        auto_generate_trace_id: Generate trace IDs if not present
    
    Example:
    ```python
    handler = NarrativeTracingHandler(story_id="story_123")
    miadi = MiadiIntegration(handler)
    
    # When making HTTP call to Miadi
    headers = miadi.inject_correlation_headers({})
    # headers now contains X-Narrative-Trace-Id, X-Story-Id, etc.
    
    # In Miadi, extract correlation
    context = miadi.extract_correlation(request.headers)
    if context.is_valid:
        # Continue the trace
        pass
    ```
    """
    
    def __init__(
        self,
        handler: NarrativeTracingHandler,
        auto_generate_trace_id: bool = True,
    ) -> None:
        """Initialize Miadi integration."""
        self.handler = handler
        self.auto_generate_trace_id = auto_generate_trace_id
        self._webhook_count = 0
        self._episode_count = 0
    
    # =========================================================================
    # HEADER INJECTION (Outgoing Requests)
    # =========================================================================
    
    def inject_correlation_headers(
        self,
        headers: Optional[Dict[str, str]] = None,
        parent_span_id: Optional[str] = None,
        beat_id: Optional[str] = None,
        episode_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Inject trace correlation headers for outgoing HTTP requests.
        
        This method adds the standard correlation headers to an HTTP request
        headers dictionary, enabling trace propagation across system boundaries.
        
        Args:
            headers: Existing headers dict (will be modified and returned)
            parent_span_id: Optional parent span for nesting
            beat_id: Optional current beat ID
            episode_id: Optional current episode ID
        
        Returns:
            Headers dict with correlation headers added
        
        Example:
        ```python
        # Basic usage
        headers = miadi.inject_correlation_headers({})
        
        # With additional context
        headers = miadi.inject_correlation_headers(
            {"Authorization": "Bearer token"},
            beat_id="beat_001",
            episode_id="s01e07"
        )
        ```
        """
        if headers is None:
            headers = {}
        
        # Get or generate trace ID
        trace_id = self.handler.root_trace_id
        if not trace_id and self.auto_generate_trace_id:
            trace_id = str(uuid.uuid4())
        
        # Inject standard headers
        if trace_id:
            headers[HEADER_TRACE_ID] = trace_id
        
        if self.handler.story_id and self.handler.story_id != "unknown":
            headers[HEADER_STORY_ID] = self.handler.story_id
        
        if self.handler.session_id:
            headers[HEADER_SESSION_ID] = self.handler.session_id
        
        # Inject optional context
        if parent_span_id:
            headers[HEADER_PARENT_SPAN_ID] = parent_span_id
        
        if beat_id:
            headers[HEADER_BEAT_ID] = beat_id
        
        if episode_id:
            headers[HEADER_EPISODE_ID] = episode_id
        
        return headers
    
    # =========================================================================
    # HEADER EXTRACTION (Incoming Requests)
    # =========================================================================
    
    def extract_correlation(
        self,
        headers: Dict[str, str],
    ) -> CorrelationContext:
        """
        Extract trace correlation from incoming HTTP request headers.
        
        Use this in Miadi's webhook handlers to continue traces that
        originated from other parts of the system.
        
        Args:
            headers: HTTP request headers dictionary
        
        Returns:
            CorrelationContext with extracted values (may have None fields)
        
        Example:
        ```python
        # In Miadi webhook handler
        context = miadi.extract_correlation(request.headers)
        
        if context.is_valid:
            # We have a trace to continue
            handler.root_trace_id = context.trace_id
        else:
            # Start a new trace
            handler.create_root_trace()
        ```
        """
        return CorrelationContext.from_headers(headers)
    
    def continue_trace_from_headers(
        self,
        headers: Dict[str, str],
    ) -> Optional[str]:
        """
        Continue an existing trace from incoming headers.
        
        This updates the handler's trace context based on incoming headers
        and returns the trace ID for reference.
        
        Args:
            headers: HTTP request headers dictionary
        
        Returns:
            The trace ID if found, None otherwise
        """
        context = self.extract_correlation(headers)
        
        if context.is_valid:
            # Update handler with incoming correlation
            if context.trace_id:
                self.handler.root_trace_id = context.trace_id
            if context.story_id:
                self.handler.story_id = context.story_id
            if context.session_id:
                self.handler.session_id = context.session_id
            
            return context.trace_id
        
        return None
    
    # =========================================================================
    # WEBHOOK EVENT TRACING
    # =========================================================================
    
    def log_webhook_received(
        self,
        event_id: str,
        event_type: str,
        source: str,
        repository: Optional[str] = None,
        sender: Optional[str] = None,
        payload_preview: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log receipt of a webhook event.
        
        Call this when Miadi first receives a webhook from GitHub/GitLab/etc.
        
        Args:
            event_id: Unique identifier for the event
            event_type: Type of event (github.push, github.issue, etc.)
            source: Source system (github, gitlab, etc.)
            repository: Optional repository name
            sender: Optional sender username
            payload_preview: Optional preview of payload (first 200 chars)
            parent_span_id: Optional parent span for nesting
        
        Returns:
            The span ID of the logged event
        """
        self._webhook_count += 1
        
        return self.handler.log_event(
            event_type=NarrativeEventType.WEBHOOK_RECEIVED,
            input_data={
                "event_id": event_id,
                "event_type": event_type,
                "source": source,
                "repository": repository,
                "sender": sender,
            },
            output_data={
                "payload_preview": payload_preview[:200] if payload_preview else None,
            },
            metadata={
                "webhook_count": self._webhook_count,
            },
            parent_span_id=parent_span_id,
        )
    
    def log_webhook_transformed(
        self,
        event_id: str,
        output_format: str,
        fields_extracted: Optional[List[str]] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log transformation of webhook event to internal format.
        
        Call this after Miadi transforms the raw webhook into the
        internal event format for processing.
        
        Args:
            event_id: Same event ID from log_webhook_received
            output_format: Format produced (e.g., "narrative_event", "redis_queue")
            fields_extracted: List of fields extracted from payload
            parent_span_id: Optional parent span for nesting
        
        Returns:
            The span ID of the logged event
        """
        return self.handler.log_event(
            event_type=NarrativeEventType.WEBHOOK_TRANSFORMED,
            input_data={
                "event_id": event_id,
            },
            output_data={
                "output_format": output_format,
                "fields_extracted": fields_extracted or [],
            },
            parent_span_id=parent_span_id,
        )
    
    def log_webhook_routed(
        self,
        event_id: str,
        destination: str,
        routing_reason: str,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log routing decision for a webhook event.
        
        Call this when Miadi decides where to route a webhook
        for further processing.
        
        Args:
            event_id: Same event ID from log_webhook_received
            destination: Where the event is being routed
            routing_reason: Why this destination was chosen
            parent_span_id: Optional parent span for nesting
        
        Returns:
            The span ID of the logged event
        """
        return self.handler.log_event(
            event_type=NarrativeEventType.ROUTING_DECISION,
            input_data={
                "event_id": event_id,
            },
            output_data={
                "destination": destination,
                "routing_reason": routing_reason,
            },
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # EPISODE TRACKING
    # =========================================================================
    
    def log_episode_boundary(
        self,
        episode_id: str,
        beat_count: int,
        reason: str = "beat_threshold",
        previous_episode_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log an episode boundary (transition to new episode).
        
        Episodes are collections of beats. This logs when the system
        determines a new episode should begin.
        
        Args:
            episode_id: New episode identifier (e.g., "s01e08")
            beat_count: Number of beats that triggered the boundary
            reason: Why the boundary was triggered
            previous_episode_id: Optional ID of the previous episode
            parent_span_id: Optional parent span for nesting
        
        Returns:
            The span ID of the logged event
        """
        self._episode_count += 1
        
        return self.handler.log_episode_boundary(
            episode_id=episode_id,
            beat_count=beat_count,
            reason=reason,
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # REDIS QUEUE CORRELATION
    # =========================================================================
    
    def create_redis_event_metadata(
        self,
        event_id: str,
        queue_name: str = "narrative_events",
    ) -> Dict[str, Any]:
        """
        Create metadata for Redis queue events with trace correlation.
        
        When events are pushed to Redis queues, include this metadata
        so consumers can continue the trace.
        
        Args:
            event_id: Event identifier
            queue_name: Name of the Redis queue
        
        Returns:
            Metadata dict to include with Redis event
        
        Example:
        ```python
        metadata = miadi.create_redis_event_metadata("evt_123")
        redis_client.lpush(queue_name, json.dumps({
            "event": event_data,
            "trace_metadata": metadata
        }))
        ```
        """
        return {
            "trace_id": self.handler.root_trace_id,
            "story_id": self.handler.story_id,
            "session_id": self.handler.session_id,
            "event_id": event_id,
            "queue_name": queue_name,
            "enqueued_at": datetime.utcnow().isoformat(),
        }
    
    def restore_from_redis_metadata(
        self,
        metadata: Dict[str, Any],
    ) -> Optional[str]:
        """
        Restore trace context from Redis event metadata.
        
        Use this when consuming events from Redis to continue the trace.
        
        Args:
            metadata: The trace_metadata from Redis event
        
        Returns:
            The trace ID if found, None otherwise
        """
        if not metadata:
            return None
        
        trace_id = metadata.get("trace_id")
        if trace_id:
            self.handler.root_trace_id = trace_id
        
        story_id = metadata.get("story_id")
        if story_id:
            self.handler.story_id = story_id
        
        session_id = metadata.get("session_id")
        if session_id:
            self.handler.session_id = session_id
        
        return trace_id
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    @property
    def webhook_count(self) -> int:
        """Number of webhooks logged through this integration."""
        return self._webhook_count
    
    @property
    def episode_count(self) -> int:
        """Number of episode boundaries logged."""
        return self._episode_count
    
    def reset_counts(self) -> None:
        """Reset all counts."""
        self._webhook_count = 0
        self._episode_count = 0


# =============================================================================
# MIDDLEWARE HELPER
# =============================================================================

def create_correlation_middleware(
    handler: NarrativeTracingHandler,
) -> Callable:
    """
    Create ASGI/WSGI middleware for automatic correlation.
    
    This is a convenience function for integrating with web frameworks.
    
    Args:
        handler: NarrativeTracingHandler instance
    
    Returns:
        Middleware function
    
    Example (FastAPI):
    ```python
    from fastapi import FastAPI, Request
    
    app = FastAPI()
    middleware = create_correlation_middleware(handler)
    
    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):
        return await middleware(request, call_next)
    ```
    """
    miadi = MiadiIntegration(handler)
    
    async def middleware(request: Any, call_next: Callable) -> Any:
        # Extract correlation from incoming request
        headers = dict(request.headers) if hasattr(request, "headers") else {}
        miadi.continue_trace_from_headers(headers)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    return middleware


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "MiadiIntegration",
    "CorrelationContext",
    "WebhookEvent",
    "create_correlation_middleware",
    "HEADER_TRACE_ID",
    "HEADER_STORY_ID",
    "HEADER_SESSION_ID",
    "HEADER_PARENT_SPAN_ID",
    "HEADER_BEAT_ID",
    "HEADER_EPISODE_ID",
    "ALL_CORRELATION_HEADERS",
]
