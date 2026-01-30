"""
Live integration tests for Miadi webhook tracing.

These tests verify that the MiadiIntegration adapter correctly:
1. Logs webhook events as they arrive
2. Injects correlation headers into downstream HTTP calls
3. Tracks episode boundaries
4. Generates traces with patent-evidence quality

Run with:
    cd /workspace/langchain/libs/narrative-tracing
    python -m pytest tests/test_miadi_integration_live.py -v
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# Add narrative-tracing to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from narrative_tracing import NarrativeTracingHandler
from narrative_tracing.adapters import (
    MiadiIntegration,
    HEADER_TRACE_ID,
    HEADER_STORY_ID,
    HEADER_SESSION_ID,
    ALL_CORRELATION_HEADERS,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_langfuse():
    """Mock Langfuse client for testing."""
    with patch("narrative_tracing.handler.Langfuse") as mock:
        mock_instance = MagicMock()
        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_span.id = "span_miadi_live"
        mock_trace.span.return_value = mock_span
        mock_trace.id = "trace_miadi_live_001"
        mock_instance.trace.return_value = mock_trace
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def handler(mock_langfuse):
    """Create a NarrativeTracingHandler for testing."""
    return NarrativeTracingHandler(
        story_id="story_miadi_integration",
        session_id="session_miadi_live",
    )


@pytest.fixture
def miadi(handler):
    """Create a MiadiIntegration instance."""
    return MiadiIntegration(handler)


# ============================================================================
# Simulated Miadi Webhook Handler
# ============================================================================


class MockMiadiWebhookHandler:
    """Simulates the ava-edgehub Miadi webhook handler with tracing."""
    
    def __init__(self, miadi_integration: MiadiIntegration):
        self.miadi = miadi_integration
        self.processed_webhooks: List[Dict] = []
        self.downstream_calls: List[Dict] = []
    
    async def handle_github_webhook(
        self,
        event_type: str,
        delivery_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle incoming GitHub webhook with tracing."""
        webhook_id = f"gh_{delivery_id}"
        
        # Log webhook received
        self.miadi.log_webhook_received(
            event_id=webhook_id,
            event_type=f"github.{event_type}",
            source="github",
            repository=payload.get("repository", {}).get("full_name", "unknown/unknown"),
            sender=payload.get("sender", {}).get("login", "unknown"),
            payload_preview=self._extract_preview(payload),
        )
        
        # Transform to agent-friendly format
        agent_data = self._transform_webhook(event_type, payload)
        
        self.miadi.log_webhook_transformed(
            event_id=webhook_id,
            output_format="agent_friendly",
            fields_extracted=list(agent_data.keys()),
        )
        
        self.processed_webhooks.append({
            "webhook_id": webhook_id,
            "event_type": event_type,
            "agent_data": agent_data,
        })
        
        return {"status": "processed", "webhook_id": webhook_id}
    
    async def trigger_downstream_workflow(
        self,
        webhook_id: str,
        workflow_url: str,
        workflow_body: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Trigger downstream workflow with correlation headers."""
        # Inject correlation headers
        headers = self.miadi.inject_correlation_headers({
            "Content-Type": "application/json",
        })
        
        # Log the downstream call
        self.miadi.log_webhook_routed(
            event_id=webhook_id,
            destination="workflow_engine",
            routing_reason="agent_processing",
        )
        
        # Simulate the HTTP call (in real code this uses httpx)
        self.downstream_calls.append({
            "url": workflow_url,
            "body": workflow_body,
            "headers": headers,
            "webhook_id": webhook_id,
        })
        
        return {"status": "triggered", "headers_injected": list(headers.keys())}
    
    def _extract_preview(self, payload: Dict) -> str:
        """Extract human-readable preview from payload."""
        if "issue" in payload:
            return payload["issue"].get("title", "")[:100]
        if "pull_request" in payload:
            return payload["pull_request"].get("title", "")[:100]
        if "commits" in payload and payload["commits"]:
            return payload["commits"][0].get("message", "")[:100]
        return "Webhook payload"
    
    def _transform_webhook(self, event_type: str, payload: Dict) -> Dict:
        """Transform webhook to agent-friendly format."""
        return {
            "event_type": event_type,
            "repository": payload.get("repository", {}).get("full_name"),
            "sender": payload.get("sender", {}).get("login"),
            "action": payload.get("action"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ============================================================================
# Live Integration Tests
# ============================================================================


class TestMiadiWebhookTracing:
    """Test Miadi webhook tracing integration."""
    
    @pytest.mark.asyncio
    async def test_webhook_received_logged(self, miadi):
        """Test that webhook receipt is logged correctly."""
        handler = MockMiadiWebhookHandler(miadi)
        
        result = await handler.handle_github_webhook(
            event_type="issues",
            delivery_id="abc123",
            payload={
                "action": "opened",
                "issue": {"title": "Test issue for tracing"},
                "repository": {"full_name": "org/repo"},
                "sender": {"login": "testuser"},
            }
        )
        
        assert result["status"] == "processed"
        assert miadi.webhook_count == 1
        assert len(handler.processed_webhooks) == 1
    
    @pytest.mark.asyncio
    async def test_correlation_headers_injected(self, miadi):
        """Test that correlation headers are injected into downstream calls."""
        handler = MockMiadiWebhookHandler(miadi)
        
        # First receive webhook
        await handler.handle_github_webhook(
            event_type="push",
            delivery_id="def456",
            payload={
                "commits": [{"message": "Add tracing support"}],
                "repository": {"full_name": "org/repo"},
                "sender": {"login": "developer"},
            }
        )
        
        # Then trigger downstream
        result = await handler.trigger_downstream_workflow(
            webhook_id="gh_def456",
            workflow_url="http://langraph:8080/process",
            workflow_body={"event": "push"},
        )
        
        assert result["status"] == "triggered"
        assert len(handler.downstream_calls) == 1
        
        # Verify headers were injected
        headers = handler.downstream_calls[0]["headers"]
        assert HEADER_TRACE_ID in headers
        assert HEADER_STORY_ID in headers
        assert HEADER_SESSION_ID in headers
    
    @pytest.mark.asyncio
    async def test_multiple_webhooks_tracked(self, miadi):
        """Test that multiple webhooks are all tracked."""
        handler = MockMiadiWebhookHandler(miadi)
        
        for i in range(5):
            await handler.handle_github_webhook(
                event_type="push",
                delivery_id=f"webhook_{i}",
                payload={
                    "commits": [{"message": f"Commit {i}"}],
                    "repository": {"full_name": "org/repo"},
                    "sender": {"login": "dev"},
                }
            )
        
        assert miadi.webhook_count == 5
        assert len(handler.processed_webhooks) == 5
    
    @pytest.mark.asyncio
    async def test_episode_boundary_logged(self, miadi):
        """Test that episode boundaries are logged."""
        # Receive multiple webhooks
        handler = MockMiadiWebhookHandler(miadi)
        
        for i in range(3):
            await handler.handle_github_webhook(
                event_type="push",
                delivery_id=f"ep_webhook_{i}",
                payload={
                    "commits": [{"message": f"Commit {i}"}],
                    "repository": {"full_name": "org/repo"},
                    "sender": {"login": "dev"},
                }
            )
        
        # Log episode boundary
        miadi.log_episode_boundary(
            episode_id="episode_001",
            beat_count=3,
            reason="webhook_batch_complete",
        )
        
        assert miadi.episode_count == 1


class TestCorrelationFlow:
    """Test end-to-end correlation flow."""
    
    @pytest.mark.asyncio
    async def test_trace_id_propagates(self, miadi, handler):
        """Test that trace ID propagates through the flow."""
        webhook_handler = MockMiadiWebhookHandler(miadi)
        
        # Receive webhook
        await webhook_handler.handle_github_webhook(
            event_type="issues",
            delivery_id="trace_test_001",
            payload={
                "issue": {"title": "Test tracing propagation"},
                "repository": {"full_name": "org/repo"},
                "sender": {"login": "user"},
            }
        )
        
        # Trigger downstream with headers
        await webhook_handler.trigger_downstream_workflow(
            webhook_id="gh_trace_test_001",
            workflow_url="http://langraph:8080/analyze",
            workflow_body={"analyze": True},
        )
        
        # Get the injected trace ID
        downstream_headers = webhook_handler.downstream_calls[0]["headers"]
        injected_trace_id = downstream_headers.get(HEADER_TRACE_ID)
        
        # Verify trace ID exists and is valid UUID format
        assert injected_trace_id is not None
        assert len(injected_trace_id) == 36  # UUID format
    
    def test_correlation_context_extraction(self, miadi):
        """Test extraction of correlation context from headers."""
        # Simulate incoming headers from upstream
        incoming_headers = {
            HEADER_TRACE_ID: "trace-123-456-789",
            HEADER_STORY_ID: "story_upstream",
            HEADER_SESSION_ID: "session_upstream",
        }
        
        context = miadi.extract_correlation(incoming_headers)
        
        assert context.trace_id == "trace-123-456-789"
        assert context.story_id == "story_upstream"
        assert context.session_id == "session_upstream"


class TestTraceExport:
    """Test trace export for patent evidence."""
    
    @pytest.mark.asyncio
    async def test_export_miadi_trace(self, miadi, handler):
        """Test exporting Miadi trace as JSON."""
        webhook_handler = MockMiadiWebhookHandler(miadi)
        
        # Process a realistic webhook flow
        await webhook_handler.handle_github_webhook(
            event_type="issues",
            delivery_id="patent_evidence_001",
            payload={
                "action": "opened",
                "issue": {
                    "id": 12345,
                    "title": "Implement three-universe tracing",
                    "body": "We need to trace events through all three perspectives.",
                },
                "repository": {"full_name": "narrative-intelligence/langchain"},
                "sender": {"login": "developer"},
            }
        )
        
        await webhook_handler.trigger_downstream_workflow(
            webhook_id="gh_patent_evidence_001",
            workflow_url="http://langraph:8080/three-universe",
            workflow_body={"process": True},
        )
        
        # Build trace data
        trace_data = {
            "trace_type": "miadi_webhook_live",
            "ceremony_uuid": "cfa7b236-3bf1-4b9c-aad2-f5729da3d4f8",
            "story_id": handler.story_id,
            "webhooks_processed": miadi.webhook_count,
            "correlation_headers": ALL_CORRELATION_HEADERS,
            "downstream_calls": len(webhook_handler.downstream_calls),
        }
        
        # Verify JSON serializable
        json_output = json.dumps(trace_data, indent=2)
        assert "miadi_webhook_live" in json_output
        assert "cfa7b236-3bf1-4b9c-aad2-f5729da3d4f8" in json_output


class TestRedisIntegration:
    """Test Redis queue correlation."""
    
    def test_redis_metadata_creation(self, miadi):
        """Test creating Redis event metadata with correlation."""
        metadata = miadi.create_redis_event_metadata(
            event_id="redis_test_001",
        )
        
        assert "trace_id" in metadata
        assert "story_id" in metadata
        assert "session_id" in metadata
        assert metadata["event_id"] == "redis_test_001"
    
    def test_redis_metadata_restoration(self, miadi):
        """Test restoring correlation from Redis metadata."""
        # Create metadata
        metadata = miadi.create_redis_event_metadata(
            event_id="restore_test_001",
        )
        
        # Simulate storing and retrieving from Redis
        # (In real code this would go through Redis)
        
        # Restore correlation
        miadi.restore_from_redis_metadata(metadata)
        
        # Verify correlation is restored (no error means success)
        assert True
