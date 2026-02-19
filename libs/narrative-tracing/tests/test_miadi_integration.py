"""
Tests for Miadi Integration Adapter

Tests the adapter that enables trace correlation between narrative-tracing
and Miadi webhook handlers/episode generators.

Test Coverage:
- Header injection for outgoing requests
- Header extraction for incoming requests
- Webhook event tracing
- Episode boundary logging
- Redis queue correlation
- Correlation context validation
"""

import pytest
from typing import Dict
from unittest.mock import MagicMock, patch


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_langfuse():
    """Mock Langfuse to avoid network calls."""
    with patch("narrative_tracing.handler.Langfuse") as mock:
        mock_instance = MagicMock()
        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_span.id = "test_span_id"
        mock_trace.span.return_value = mock_span
        mock_instance.trace.return_value = mock_trace
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def handler(mock_langfuse):
    """Create a NarrativeTracingHandler with mocked Langfuse."""
    from narrative_tracing import NarrativeTracingHandler
    return NarrativeTracingHandler(
        story_id="test_story",
        session_id="test_session",
    )


@pytest.fixture
def miadi(handler):
    """Create MiadiIntegration with handler."""
    from narrative_tracing.adapters import MiadiIntegration
    return MiadiIntegration(handler)


# =============================================================================
# HEADER INJECTION TESTS
# =============================================================================

class TestHeaderInjection:
    """Test injecting correlation headers into outgoing requests."""
    
    def test_inject_creates_new_headers(self, miadi):
        """inject_correlation_headers creates headers dict if None passed."""
        headers = miadi.inject_correlation_headers(None)
        assert isinstance(headers, dict)
    
    def test_inject_preserves_existing_headers(self, miadi):
        """Existing headers are preserved."""
        existing = {"Authorization": "Bearer token", "Content-Type": "application/json"}
        headers = miadi.inject_correlation_headers(existing)
        
        assert headers["Authorization"] == "Bearer token"
        assert headers["Content-Type"] == "application/json"
    
    def test_inject_adds_trace_id(self, miadi):
        """Trace ID header is added."""
        from narrative_tracing.adapters import HEADER_TRACE_ID
        
        headers = miadi.inject_correlation_headers({})
        assert HEADER_TRACE_ID in headers
    
    def test_inject_adds_story_id(self, miadi):
        """Story ID header is added when story_id is set."""
        from narrative_tracing.adapters import HEADER_STORY_ID
        
        headers = miadi.inject_correlation_headers({})
        assert HEADER_STORY_ID in headers
        assert headers[HEADER_STORY_ID] == "test_story"
    
    def test_inject_adds_session_id(self, miadi):
        """Session ID header is added when session_id is set."""
        from narrative_tracing.adapters import HEADER_SESSION_ID
        
        headers = miadi.inject_correlation_headers({})
        assert HEADER_SESSION_ID in headers
        assert headers[HEADER_SESSION_ID] == "test_session"
    
    def test_inject_adds_optional_beat_id(self, miadi):
        """Beat ID header is added when provided."""
        from narrative_tracing.adapters import HEADER_BEAT_ID
        
        headers = miadi.inject_correlation_headers({}, beat_id="beat_001")
        assert HEADER_BEAT_ID in headers
        assert headers[HEADER_BEAT_ID] == "beat_001"
    
    def test_inject_adds_optional_episode_id(self, miadi):
        """Episode ID header is added when provided."""
        from narrative_tracing.adapters import HEADER_EPISODE_ID
        
        headers = miadi.inject_correlation_headers({}, episode_id="s01e07")
        assert HEADER_EPISODE_ID in headers
        assert headers[HEADER_EPISODE_ID] == "s01e07"
    
    def test_inject_adds_parent_span_id(self, miadi):
        """Parent span ID header is added when provided."""
        from narrative_tracing.adapters import HEADER_PARENT_SPAN_ID
        
        headers = miadi.inject_correlation_headers({}, parent_span_id="span_123")
        assert HEADER_PARENT_SPAN_ID in headers
        assert headers[HEADER_PARENT_SPAN_ID] == "span_123"


# =============================================================================
# HEADER EXTRACTION TESTS
# =============================================================================

class TestHeaderExtraction:
    """Test extracting correlation headers from incoming requests."""
    
    def test_extract_returns_context(self, miadi):
        """extract_correlation returns CorrelationContext."""
        from narrative_tracing.adapters import CorrelationContext
        
        context = miadi.extract_correlation({})
        assert isinstance(context, CorrelationContext)
    
    def test_extract_gets_trace_id(self, miadi):
        """Trace ID is extracted from headers."""
        from narrative_tracing.adapters import HEADER_TRACE_ID
        
        headers = {HEADER_TRACE_ID: "trace_abc123"}
        context = miadi.extract_correlation(headers)
        
        assert context.trace_id == "trace_abc123"
    
    def test_extract_gets_story_id(self, miadi):
        """Story ID is extracted from headers."""
        from narrative_tracing.adapters import HEADER_STORY_ID
        
        headers = {HEADER_STORY_ID: "story_xyz"}
        context = miadi.extract_correlation(headers)
        
        assert context.story_id == "story_xyz"
    
    def test_extract_gets_all_headers(self, miadi):
        """All correlation headers are extracted."""
        from narrative_tracing.adapters import (
            HEADER_TRACE_ID,
            HEADER_STORY_ID,
            HEADER_SESSION_ID,
            HEADER_PARENT_SPAN_ID,
            HEADER_BEAT_ID,
            HEADER_EPISODE_ID,
        )
        
        headers = {
            HEADER_TRACE_ID: "trace_123",
            HEADER_STORY_ID: "story_456",
            HEADER_SESSION_ID: "session_789",
            HEADER_PARENT_SPAN_ID: "span_abc",
            HEADER_BEAT_ID: "beat_001",
            HEADER_EPISODE_ID: "s01e07",
        }
        
        context = miadi.extract_correlation(headers)
        
        assert context.trace_id == "trace_123"
        assert context.story_id == "story_456"
        assert context.session_id == "session_789"
        assert context.parent_span_id == "span_abc"
        assert context.beat_id == "beat_001"
        assert context.episode_id == "s01e07"
    
    def test_extract_handles_missing_headers(self, miadi):
        """Missing headers result in None values."""
        context = miadi.extract_correlation({})
        
        assert context.trace_id is None
        assert context.story_id is None
        assert context.session_id is None


# =============================================================================
# CORRELATION CONTEXT TESTS
# =============================================================================

class TestCorrelationContext:
    """Test CorrelationContext data class."""
    
    def test_is_valid_with_trace_id(self):
        """Context is valid when trace_id is present."""
        from narrative_tracing.adapters import CorrelationContext
        
        context = CorrelationContext(trace_id="trace_123")
        assert context.is_valid is True
    
    def test_is_valid_without_trace_id(self):
        """Context is invalid when trace_id is None."""
        from narrative_tracing.adapters import CorrelationContext
        
        context = CorrelationContext()
        assert context.is_valid is False
    
    def test_to_dict(self):
        """Context converts to dictionary."""
        from narrative_tracing.adapters import CorrelationContext
        
        context = CorrelationContext(
            trace_id="trace_123",
            story_id="story_456",
        )
        
        data = context.to_dict()
        
        assert data["trace_id"] == "trace_123"
        assert data["story_id"] == "story_456"
        assert data["session_id"] is None
    
    def test_from_headers_class_method(self):
        """Can create context from headers via class method."""
        from narrative_tracing.adapters import (
            CorrelationContext,
            HEADER_TRACE_ID,
            HEADER_STORY_ID,
        )
        
        headers = {
            HEADER_TRACE_ID: "trace_abc",
            HEADER_STORY_ID: "story_xyz",
        }
        
        context = CorrelationContext.from_headers(headers)
        
        assert context.trace_id == "trace_abc"
        assert context.story_id == "story_xyz"


# =============================================================================
# WEBHOOK EVENT TRACING TESTS
# =============================================================================

class TestWebhookEventTracing:
    """Test webhook event logging."""
    
    def test_log_webhook_received(self, miadi):
        """Can log webhook received event."""
        span_id = miadi.log_webhook_received(
            event_id="evt_123",
            event_type="github.push",
            source="github",
            repository="owner/repo",
            sender="username",
        )
        
        assert span_id is not None
    
    def test_log_webhook_increments_count(self, miadi):
        """Logging webhook increments count."""
        assert miadi.webhook_count == 0
        
        miadi.log_webhook_received(
            event_id="evt_1",
            event_type="github.push",
            source="github",
        )
        
        assert miadi.webhook_count == 1
        
        miadi.log_webhook_received(
            event_id="evt_2",
            event_type="github.issue",
            source="github",
        )
        
        assert miadi.webhook_count == 2
    
    def test_log_webhook_transformed(self, miadi):
        """Can log webhook transformation event."""
        span_id = miadi.log_webhook_transformed(
            event_id="evt_123",
            output_format="narrative_event",
            fields_extracted=["title", "body", "author"],
        )
        
        assert span_id is not None


# =============================================================================
# EPISODE TRACKING TESTS
# =============================================================================

class TestEpisodeTracking:
    """Test episode boundary logging."""
    
    def test_log_episode_boundary(self, miadi):
        """Can log episode boundary."""
        span_id = miadi.log_episode_boundary(
            episode_id="s01e08",
            beat_count=15,
            reason="beat_threshold",
        )
        
        assert span_id is not None
    
    def test_episode_boundary_increments_count(self, miadi):
        """Episode boundary increments count."""
        assert miadi.episode_count == 0
        
        miadi.log_episode_boundary(
            episode_id="s01e07",
            beat_count=10,
        )
        
        assert miadi.episode_count == 1


# =============================================================================
# REDIS QUEUE CORRELATION TESTS
# =============================================================================

class TestRedisQueueCorrelation:
    """Test Redis queue trace correlation."""
    
    def test_create_redis_event_metadata(self, miadi):
        """Creates metadata with trace correlation."""
        metadata = miadi.create_redis_event_metadata(
            event_id="evt_123",
            queue_name="narrative_events",
        )
        
        assert "trace_id" in metadata
        assert "story_id" in metadata
        assert "session_id" in metadata
        assert metadata["event_id"] == "evt_123"
        assert metadata["queue_name"] == "narrative_events"
        assert "enqueued_at" in metadata
    
    def test_restore_from_redis_metadata(self, miadi):
        """Can restore trace context from Redis metadata."""
        metadata = {
            "trace_id": "trace_redis",
            "story_id": "story_redis",
            "session_id": "session_redis",
        }
        
        trace_id = miadi.restore_from_redis_metadata(metadata)
        
        assert trace_id == "trace_redis"
        assert miadi.handler.story_id == "story_redis"
        assert miadi.handler.session_id == "session_redis"
    
    def test_restore_handles_empty_metadata(self, miadi):
        """Restore handles empty metadata gracefully."""
        trace_id = miadi.restore_from_redis_metadata({})
        assert trace_id is None
    
    def test_restore_handles_none_metadata(self, miadi):
        """Restore handles None metadata gracefully."""
        trace_id = miadi.restore_from_redis_metadata(None)
        assert trace_id is None


# =============================================================================
# CONTINUE TRACE TESTS
# =============================================================================

class TestContinueTrace:
    """Test continuing trace from incoming headers."""
    
    def test_continue_trace_updates_handler(self, miadi):
        """continue_trace_from_headers updates handler context."""
        from narrative_tracing.adapters import (
            HEADER_TRACE_ID,
            HEADER_STORY_ID,
            HEADER_SESSION_ID,
        )
        
        headers = {
            HEADER_TRACE_ID: "incoming_trace",
            HEADER_STORY_ID: "incoming_story",
            HEADER_SESSION_ID: "incoming_session",
        }
        
        trace_id = miadi.continue_trace_from_headers(headers)
        
        assert trace_id == "incoming_trace"
        assert miadi.handler.root_trace_id == "incoming_trace"
        assert miadi.handler.story_id == "incoming_story"
        assert miadi.handler.session_id == "incoming_session"
    
    def test_continue_trace_returns_none_without_trace_id(self, miadi):
        """Returns None when headers don't have trace_id."""
        trace_id = miadi.continue_trace_from_headers({})
        assert trace_id is None


# =============================================================================
# STATISTICS TESTS
# =============================================================================

class TestStatistics:
    """Test integration statistics."""
    
    def test_reset_counts(self, miadi):
        """Can reset all counts."""
        # Generate some counts
        miadi.log_webhook_received("evt_1", "github.push", "github")
        miadi.log_webhook_received("evt_2", "github.push", "github")
        miadi.log_episode_boundary("s01e07", 10)
        
        assert miadi.webhook_count == 2
        assert miadi.episode_count == 1
        
        miadi.reset_counts()
        
        assert miadi.webhook_count == 0
        assert miadi.episode_count == 0


# =============================================================================
# WEBHOOK EVENT DATA CLASS TESTS
# =============================================================================

class TestWebhookEvent:
    """Test WebhookEvent data class."""
    
    def test_webhook_event_creation(self):
        """Can create WebhookEvent."""
        from narrative_tracing.adapters import WebhookEvent
        
        event = WebhookEvent(
            event_id="evt_123",
            event_type="github.push",
            source="github",
            repository="owner/repo",
        )
        
        assert event.event_id == "evt_123"
        assert event.event_type == "github.push"
        assert event.source == "github"
        assert event.repository == "owner/repo"
    
    def test_webhook_event_auto_timestamp(self):
        """WebhookEvent auto-generates timestamp."""
        from narrative_tracing.adapters import WebhookEvent
        
        event = WebhookEvent(
            event_id="evt_123",
            event_type="github.push",
            source="github",
        )
        
        assert event.timestamp != ""
        assert "T" in event.timestamp  # ISO format check
    
    def test_webhook_event_to_dict(self):
        """WebhookEvent converts to dictionary."""
        from narrative_tracing.adapters import WebhookEvent
        
        event = WebhookEvent(
            event_id="evt_123",
            event_type="github.push",
            source="github",
        )
        
        data = event.to_dict()
        
        assert data["event_id"] == "evt_123"
        assert data["event_type"] == "github.push"
        assert data["source"] == "github"
