"""
Unit tests for Narrative Tracing package.

Tests cover:
- Event types and glyphs
- Handler event logging
- Orchestrator trace correlation
- Formatter output generation
- Metrics extraction
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


# =============================================================================
# EVENT TYPES TESTS
# =============================================================================

class TestNarrativeEventType:
    """Tests for NarrativeEventType enum and related structures."""
    
    def test_event_type_values(self):
        """Test event type values are properly formatted."""
        from narrative_tracing import NarrativeEventType
        
        assert NarrativeEventType.BEAT_CREATED.value == "narrative.beat.created"
        assert NarrativeEventType.THREE_UNIVERSE_ANALYSIS.value == "narrative.universe.analysis"
        assert NarrativeEventType.ROUTING_DECISION.value == "narrative.routing.decision"
    
    def test_all_event_types_have_glyphs(self):
        """Test all event types have associated glyphs."""
        from narrative_tracing import NarrativeEventType, EVENT_GLYPHS
        
        for event_type in NarrativeEventType:
            assert event_type in EVENT_GLYPHS, f"Missing glyph for {event_type}"
            assert isinstance(EVENT_GLYPHS[event_type], str)
            assert len(EVENT_GLYPHS[event_type]) > 0


class TestNarrativeSpan:
    """Tests for NarrativeSpan dataclass."""
    
    def test_span_creation(self):
        """Test creating a narrative span."""
        from narrative_tracing import NarrativeSpan, NarrativeEventType
        
        span = NarrativeSpan(
            span_id="span_123",
            trace_id="trace_456",
            event_type=NarrativeEventType.BEAT_CREATED,
            story_id="story_789",
            beat_id="beat_001",
            emotional_tone="mysterious"
        )
        
        assert span.span_id == "span_123"
        assert span.trace_id == "trace_456"
        assert span.story_id == "story_789"
        assert span.beat_id == "beat_001"
        assert span.emotional_tone == "mysterious"
        assert span.success is True
    
    def test_span_to_dict(self):
        """Test span serialization to dict."""
        from narrative_tracing import NarrativeSpan, NarrativeEventType
        
        span = NarrativeSpan(
            span_id="span_123",
            trace_id="trace_456",
            event_type=NarrativeEventType.BEAT_CREATED,
            story_id="story_789",
            lead_universe="story_engine"
        )
        
        data = span.to_dict()
        
        assert data["span_id"] == "span_123"
        assert data["event_type"] == "narrative.beat.created"
        assert data["lead_universe"] == "story_engine"
    
    def test_span_display_name(self):
        """Test span display name generation."""
        from narrative_tracing import NarrativeSpan, NarrativeEventType
        
        span = NarrativeSpan(
            span_id="span_123",
            trace_id="trace_456",
            event_type=NarrativeEventType.BEAT_CREATED,
            story_id="story_789",
            beat_id="beat_001"
        )
        
        display_name = span.get_display_name()
        
        assert "📝" in display_name
        assert "Created" in display_name
        assert "beat_001" in display_name


class TestTraceCorrelation:
    """Tests for TraceCorrelation dataclass."""
    
    def test_correlation_creation(self):
        """Test creating a trace correlation."""
        from narrative_tracing import TraceCorrelation
        
        correlation = TraceCorrelation(
            root_trace_id="root_123",
            story_id="story_456",
            session_id="session_789"
        )
        
        assert correlation.root_trace_id == "root_123"
        assert correlation.child_trace_ids == []
        assert correlation.correlation_path == []
    
    def test_add_child(self):
        """Test adding child traces."""
        from narrative_tracing import TraceCorrelation
        
        correlation = TraceCorrelation(
            root_trace_id="root_123",
            story_id="story_456"
        )
        
        correlation.add_child("child_1", "flowise")
        correlation.add_child("child_2", "langflow")
        
        assert "child_1" in correlation.child_trace_ids
        assert "child_2" in correlation.child_trace_ids
        assert "flowise" in correlation.correlation_path
        assert "langflow" in correlation.correlation_path


class TestNarrativeMetrics:
    """Tests for NarrativeMetrics dataclass."""
    
    def test_metrics_defaults(self):
        """Test default metric values."""
        from narrative_tracing import NarrativeMetrics
        
        metrics = NarrativeMetrics()
        
        assert metrics.coherence_score == 0.5
        assert metrics.emotional_arc_strength == 0.5
        assert metrics.beats_generated == 0
    
    def test_calculate_overall_quality(self):
        """Test overall quality calculation."""
        from narrative_tracing import NarrativeMetrics
        
        metrics = NarrativeMetrics(
            coherence_score=0.8,
            emotional_arc_strength=0.9,
            theme_clarity=0.7,
            cross_universe_coherence=0.85,
            dialogue_consistency=0.75
        )
        
        quality = metrics.calculate_overall_quality()
        
        # Should be weighted average
        expected = 0.8 * 0.25 + 0.9 * 0.25 + 0.7 * 0.20 + 0.85 * 0.15 + 0.75 * 0.15
        assert abs(quality - expected) < 0.001


# =============================================================================
# HANDLER TESTS (with mocked Langfuse)
# =============================================================================

class TestNarrativeTracingHandler:
    """Tests for NarrativeTracingHandler."""
    
    @patch('narrative_tracing.handler.Langfuse')
    @patch('narrative_tracing.handler.LANGFUSE_AVAILABLE', True)
    def test_handler_initialization(self, mock_langfuse_class):
        """Test handler initialization."""
        from narrative_tracing import NarrativeTracingHandler
        
        mock_langfuse = MagicMock()
        mock_langfuse_class.return_value = mock_langfuse
        
        handler = NarrativeTracingHandler(
            story_id="story_123",
            session_id="session_456"
        )
        
        assert handler.story_id == "story_123"
        assert handler.session_id == "session_456"
    
    @patch('narrative_tracing.handler.Langfuse')
    @patch('narrative_tracing.handler.LANGFUSE_AVAILABLE', True)
    def test_log_beat_creation(self, mock_langfuse_class):
        """Test logging beat creation."""
        from narrative_tracing import NarrativeTracingHandler
        
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_trace.span.return_value = mock_span
        mock_langfuse_class.return_value = mock_langfuse
        
        handler = NarrativeTracingHandler(story_id="story_123")
        
        span_id = handler.log_beat_creation(
            beat_id="beat_001",
            content="The protagonist discovers...",
            sequence=1,
            narrative_function="inciting_incident",
            emotional_tone="mysterious"
        )
        
        assert span_id is not None
        assert handler._metrics.beats_generated == 1
    
    @patch('narrative_tracing.handler.Langfuse')
    @patch('narrative_tracing.handler.LANGFUSE_AVAILABLE', True)
    def test_log_three_universe_analysis(self, mock_langfuse_class):
        """Test logging three-universe analysis."""
        from narrative_tracing import NarrativeTracingHandler
        
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_trace.span.return_value = mock_span
        mock_langfuse_class.return_value = mock_langfuse
        
        handler = NarrativeTracingHandler(story_id="story_123")
        
        span_id = handler.log_three_universe_analysis(
            event_id="evt_123",
            engineer_intent="feature_request",
            engineer_confidence=0.8,
            ceremony_intent="co_creation",
            ceremony_confidence=0.7,
            story_engine_intent="inciting_incident",
            story_engine_confidence=0.95,
            lead_universe="story_engine",
            coherence_score=0.88
        )
        
        assert span_id is not None
        # Check metrics were updated
        assert handler._metrics.cross_universe_coherence > 0.5
    
    @patch('narrative_tracing.handler.Langfuse')
    @patch('narrative_tracing.handler.LANGFUSE_AVAILABLE', True)
    def test_correlation_headers(self, mock_langfuse_class):
        """Test correlation header generation."""
        from narrative_tracing import NarrativeTracingHandler
        
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_langfuse_class.return_value = mock_langfuse
        
        handler = NarrativeTracingHandler(
            story_id="story_123",
            session_id="session_456"
        )
        
        headers = handler.get_correlation_header()
        
        assert "X-Narrative-Trace-Id" in headers
        assert "X-Story-Id" in headers
        assert headers["X-Story-Id"] == "story_123"


# =============================================================================
# ORCHESTRATOR TESTS (with mocked Langfuse)
# =============================================================================

class TestNarrativeTraceOrchestrator:
    """Tests for NarrativeTraceOrchestrator."""
    
    @patch('narrative_tracing.orchestrator.Langfuse')
    @patch('narrative_tracing.orchestrator.LANGFUSE_AVAILABLE', True)
    def test_create_root_trace(self, mock_langfuse_class):
        """Test creating root trace."""
        from narrative_tracing import NarrativeTraceOrchestrator
        
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_langfuse_class.return_value = mock_langfuse
        
        orchestrator = NarrativeTraceOrchestrator()
        
        root = orchestrator.create_story_generation_root(
            story_id="story_123",
            session_id="session_456"
        )
        
        assert root.story_id == "story_123"
        assert root.session_id == "session_456"
        assert root.trace_id is not None
        assert root.correlation is not None
    
    @patch('narrative_tracing.orchestrator.Langfuse')
    @patch('narrative_tracing.orchestrator.LANGFUSE_AVAILABLE', True)
    def test_create_beat_span(self, mock_langfuse_class):
        """Test creating beat span."""
        from narrative_tracing import NarrativeTraceOrchestrator
        
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_trace.span.return_value = mock_span
        mock_langfuse_class.return_value = mock_langfuse
        
        orchestrator = NarrativeTraceOrchestrator()
        root = orchestrator.create_story_generation_root("story_123")
        
        span_id = orchestrator.create_beat_span(
            beat_id="beat_001",
            beat_content="The protagonist discovers...",
            beat_sequence=1,
            narrative_function="inciting_incident",
            root_trace=root,
            emotional_tone="mysterious"
        )
        
        assert span_id is not None
        assert span_id in root.child_span_ids
    
    @patch('narrative_tracing.orchestrator.Langfuse')
    @patch('narrative_tracing.orchestrator.LANGFUSE_AVAILABLE', True)
    def test_inject_correlation_header(self, mock_langfuse_class):
        """Test injecting correlation headers."""
        from narrative_tracing import NarrativeTraceOrchestrator
        
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_langfuse_class.return_value = mock_langfuse
        
        orchestrator = NarrativeTraceOrchestrator()
        root = orchestrator.create_story_generation_root("story_123", "session_456")
        
        headers = orchestrator.inject_correlation_header({}, root.trace_id)
        
        assert "X-Narrative-Trace-Id" in headers
        assert headers["X-Narrative-Trace-Id"] == root.trace_id
        assert headers["X-Story-Id"] == "story_123"
        assert headers["X-Session-Id"] == "session_456"
    
    @patch('narrative_tracing.orchestrator.Langfuse')
    @patch('narrative_tracing.orchestrator.LANGFUSE_AVAILABLE', True)
    def test_extract_correlation_header(self, mock_langfuse_class):
        """Test extracting correlation headers."""
        from narrative_tracing import NarrativeTraceOrchestrator
        
        mock_langfuse = MagicMock()
        mock_langfuse_class.return_value = mock_langfuse
        
        orchestrator = NarrativeTraceOrchestrator()
        
        headers = {
            "X-Narrative-Trace-Id": "trace_123",
            "X-Story-Id": "story_456",
            "X-Session-Id": "session_789",
            "X-Parent-Span-Id": "span_abc",
        }
        
        trace_id, story_id, session_id, parent_span_id = orchestrator.extract_correlation_header(headers)
        
        assert trace_id == "trace_123"
        assert story_id == "story_456"
        assert session_id == "session_789"
        assert parent_span_id == "span_abc"


# =============================================================================
# FORMATTER TESTS
# =============================================================================

class TestNarrativeTraceFormatter:
    """Tests for NarrativeTraceFormatter."""
    
    def test_format_for_display(self):
        """Test display formatting."""
        from narrative_tracing import (
            NarrativeTraceFormatter,
            NarrativeSpan,
            NarrativeEventType,
            NarrativeMetrics,
        )
        from narrative_tracing.orchestrator import CompletedTrace
        
        # Create test spans
        spans = [
            NarrativeSpan(
                span_id="span_1",
                trace_id="trace_123",
                event_type=NarrativeEventType.BEAT_CREATED,
                story_id="story_456",
                beat_id="beat_001",
                emotional_tone="mysterious"
            ),
            NarrativeSpan(
                span_id="span_2",
                trace_id="trace_123",
                event_type=NarrativeEventType.BEAT_ANALYZED,
                story_id="story_456",
                beat_id="beat_001"
            ),
        ]
        
        metrics = NarrativeMetrics(
            coherence_score=0.87,
            emotional_arc_strength=0.92,
            beats_generated=1
        )
        
        trace = CompletedTrace(
            trace_id="trace_123",
            story_id="story_456",
            session_id="session_789",
            spans=spans,
            start_time="2025-12-31T10:00:00",
            end_time="2025-12-31T10:01:00",
            duration_ms=60000,
            metrics=metrics,
            beat_count=1
        )
        
        formatter = NarrativeTraceFormatter()
        output = formatter.format_for_display(trace)
        
        assert "📖 Story Generation" in output
        assert "story_456" in output
        assert "beat_001" in output
        assert "coherence" in output.lower()
    
    def test_export_as_markdown(self):
        """Test markdown export."""
        from narrative_tracing import (
            NarrativeTraceFormatter,
            NarrativeSpan,
            NarrativeEventType,
            NarrativeMetrics,
        )
        from narrative_tracing.orchestrator import CompletedTrace
        
        metrics = NarrativeMetrics(beats_generated=5)
        
        trace = CompletedTrace(
            trace_id="trace_123",
            story_id="story_456",
            session_id="session_789",
            spans=[],
            duration_ms=30000,
            metrics=metrics,
            beat_count=5
        )
        
        formatter = NarrativeTraceFormatter()
        markdown = formatter.export_as_markdown(trace)
        
        assert "# Story Generation Trace" in markdown
        assert "story_456" in markdown
        assert "| Metric |" in markdown
    
    def test_generate_improvement_suggestions(self):
        """Test improvement suggestion generation."""
        from narrative_tracing import NarrativeTraceFormatter, NarrativeMetrics
        
        # Low coherence metrics
        metrics = NarrativeMetrics(
            coherence_score=0.3,
            emotional_arc_strength=0.4,
            theme_clarity=0.5,
            cross_universe_coherence=0.4
        )
        
        formatter = NarrativeTraceFormatter()
        suggestions = formatter.generate_improvement_suggestions(metrics)
        
        assert len(suggestions) > 0
        assert any("coherence" in s.lower() for s in suggestions)
        assert any("emotional" in s.lower() for s in suggestions)
    
    def test_healthy_metrics_suggestions(self):
        """Test suggestions for healthy metrics."""
        from narrative_tracing import NarrativeTraceFormatter, NarrativeMetrics
        
        # Good metrics
        metrics = NarrativeMetrics(
            coherence_score=0.9,
            emotional_arc_strength=0.85,
            theme_clarity=0.8,
            cross_universe_coherence=0.88,
            enrichments_applied=10,
            beats_generated=20
        )
        
        formatter = NarrativeTraceFormatter()
        suggestions = formatter.generate_improvement_suggestions(metrics)
        
        assert len(suggestions) == 1
        assert "✅" in suggestions[0]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full tracing flow."""
    
    @patch('narrative_tracing.handler.Langfuse')
    @patch('narrative_tracing.handler.LANGFUSE_AVAILABLE', True)
    @patch('narrative_tracing.orchestrator.Langfuse')
    @patch('narrative_tracing.orchestrator.LANGFUSE_AVAILABLE', True)
    def test_full_tracing_flow(self, mock_orch_langfuse, mock_handler_langfuse):
        """Test complete tracing workflow."""
        from narrative_tracing import (
            NarrativeTracingHandler,
            NarrativeTraceOrchestrator,
            NarrativeTraceFormatter,
        )
        
        # Setup mocks
        mock_langfuse = MagicMock()
        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_langfuse.trace.return_value = mock_trace
        mock_trace.span.return_value = mock_span
        mock_orch_langfuse.return_value = mock_langfuse
        mock_handler_langfuse.return_value = mock_langfuse
        
        # Create orchestrator and root trace
        orchestrator = NarrativeTraceOrchestrator()
        root = orchestrator.create_story_generation_root("story_123", "session_456")
        
        # Create handler with same story
        handler = NarrativeTracingHandler(
            story_id="story_123",
            session_id="session_456",
            trace_id=root.trace_id
        )
        
        # Simulate story generation
        handler.log_beat_creation(
            beat_id="beat_001",
            content="The story begins...",
            sequence=1,
            narrative_function="setup"
        )
        
        handler.log_three_universe_analysis(
            event_id="evt_001",
            engineer_intent="setup",
            engineer_confidence=0.7,
            ceremony_intent="introduction",
            ceremony_confidence=0.6,
            story_engine_intent="setup",
            story_engine_confidence=0.9,
            lead_universe="story_engine",
            coherence_score=0.8
        )
        
        # Get metrics
        metrics = handler.get_metrics()
        
        assert metrics.beats_generated == 1
        assert metrics.cross_universe_coherence > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
