"""
Tests for LangGraph Bridge Adapter

Tests the bridge that wires LangGraph ThreeUniverseProcessor to narrative-tracing.

Test Coverage:
- Bridge instantiation
- Callback receives universe data
- Callback logs to handler
- Coherence score validation (0-1 range)
- Lead universe validation (engineer|ceremony|story_engine)
- Analysis object logging
- Decorator approach
- Beat creation tracking
"""

import pytest
from typing import Any, Dict, List
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
def bridge(handler):
    """Create a LangGraphBridge with handler."""
    from narrative_tracing.adapters import LangGraphBridge
    return LangGraphBridge(handler)


@pytest.fixture
def sample_engineer_result() -> Dict[str, Any]:
    """Sample engineer universe result."""
    return {
        "intent": "feature_implementation",
        "confidence": 0.85,
        "suggested_flows": ["code_review", "integration_test"],
        "context": {"technical_scope": "api_layer"},
    }


@pytest.fixture
def sample_ceremony_result() -> Dict[str, Any]:
    """Sample ceremony universe result."""
    return {
        "intent": "co_creation",
        "confidence": 0.75,
        "suggested_flows": ["witness_collaboration", "honor_contributions"],
        "context": {"is_collaborative": True},
    }


@pytest.fixture
def sample_story_engine_result() -> Dict[str, Any]:
    """Sample story engine universe result."""
    return {
        "intent": "rising_action",
        "confidence": 0.90,
        "suggested_flows": ["advance_narrative", "develop_characters"],
        "context": {"act": 2, "dramatic_tension": 0.6},
    }


# =============================================================================
# BRIDGE INSTANTIATION TESTS
# =============================================================================

class TestBridgeInstantiation:
    """Test bridge can be created with handler."""
    
    def test_bridge_creation(self, handler):
        """Can create bridge with handler."""
        from narrative_tracing.adapters import LangGraphBridge
        bridge = LangGraphBridge(handler)
        assert bridge is not None
        assert bridge.handler is handler
    
    def test_bridge_with_auto_flush(self, handler):
        """Can create bridge with auto_flush enabled."""
        from narrative_tracing.adapters import LangGraphBridge
        bridge = LangGraphBridge(handler, auto_flush=True)
        assert bridge.auto_flush is True
    
    def test_bridge_initial_count(self, bridge):
        """Bridge starts with zero analysis count."""
        assert bridge.analysis_count == 0


# =============================================================================
# CALLBACK TESTS
# =============================================================================

class TestCallbackReceivesData:
    """Test callback accepts all required parameters."""
    
    def test_callback_creation(self, bridge):
        """Can create callback function."""
        callback = bridge.create_three_universe_callback()
        assert callable(callback)
    
    def test_callback_accepts_all_parameters(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Callback accepts all universe data parameters."""
        callback = bridge.create_three_universe_callback()
        
        # Should not raise
        span_id = callback(
            event_id="evt_test",
            event_content="feat: add new feature",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="story_engine",
            coherence_score=0.82,
        )
        
        assert span_id is not None
    
    def test_callback_increments_count(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Callback increments analysis count."""
        callback = bridge.create_three_universe_callback()
        
        assert bridge.analysis_count == 0
        
        callback(
            event_id="evt_1",
            event_content="test",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="engineer",
            coherence_score=0.75,
        )
        
        assert bridge.analysis_count == 1
        
        callback(
            event_id="evt_2",
            event_content="test 2",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="ceremony",
            coherence_score=0.80,
        )
        
        assert bridge.analysis_count == 2


class TestCallbackLogsToHandler:
    """Test callback calls handler.log_three_universe_analysis."""
    
    def test_callback_calls_handler_log(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Callback invokes handler's log method."""
        # Spy on handler method
        bridge.handler.log_three_universe_analysis = MagicMock(return_value="mock_span_id")
        
        callback = bridge.create_three_universe_callback()
        callback(
            event_id="evt_test",
            event_content="test content",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="story_engine",
            coherence_score=0.85,
        )
        
        bridge.handler.log_three_universe_analysis.assert_called_once()
        
        # Verify call arguments
        call_kwargs = bridge.handler.log_three_universe_analysis.call_args.kwargs
        assert call_kwargs["event_id"] == "evt_test"
        assert call_kwargs["engineer_intent"] == "feature_implementation"
        assert call_kwargs["engineer_confidence"] == 0.85
        assert call_kwargs["ceremony_intent"] == "co_creation"
        assert call_kwargs["ceremony_confidence"] == 0.75
        assert call_kwargs["story_engine_intent"] == "rising_action"
        assert call_kwargs["story_engine_confidence"] == 0.90
        assert call_kwargs["lead_universe"] == "story_engine"
        assert call_kwargs["coherence_score"] == 0.85


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestCoherenceScoreRange:
    """Test coherence score must be 0.0-1.0."""
    
    def test_valid_coherence_min(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Coherence score of 0.0 is valid."""
        callback = bridge.create_three_universe_callback()
        # Should not raise
        callback(
            event_id="evt_test",
            event_content="test",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="engineer",
            coherence_score=0.0,
        )
    
    def test_valid_coherence_max(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Coherence score of 1.0 is valid."""
        callback = bridge.create_three_universe_callback()
        callback(
            event_id="evt_test",
            event_content="test",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="engineer",
            coherence_score=1.0,
        )
    
    def test_invalid_coherence_negative(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Coherence score below 0.0 raises ValueError."""
        callback = bridge.create_three_universe_callback()
        
        with pytest.raises(ValueError, match="coherence_score must be between"):
            callback(
                event_id="evt_test",
                event_content="test",
                engineer_result=sample_engineer_result,
                ceremony_result=sample_ceremony_result,
                story_engine_result=sample_story_engine_result,
                lead_universe="engineer",
                coherence_score=-0.1,
            )
    
    def test_invalid_coherence_above_one(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Coherence score above 1.0 raises ValueError."""
        callback = bridge.create_three_universe_callback()
        
        with pytest.raises(ValueError, match="coherence_score must be between"):
            callback(
                event_id="evt_test",
                event_content="test",
                engineer_result=sample_engineer_result,
                ceremony_result=sample_ceremony_result,
                story_engine_result=sample_story_engine_result,
                lead_universe="engineer",
                coherence_score=1.5,
            )


class TestLeadUniverseValues:
    """Test lead universe must be engineer|ceremony|story_engine."""
    
    def test_valid_lead_engineer(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """lead_universe='engineer' is valid."""
        callback = bridge.create_three_universe_callback()
        callback(
            event_id="evt_test",
            event_content="test",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="engineer",
            coherence_score=0.8,
        )
    
    def test_valid_lead_ceremony(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """lead_universe='ceremony' is valid."""
        callback = bridge.create_three_universe_callback()
        callback(
            event_id="evt_test",
            event_content="test",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="ceremony",
            coherence_score=0.8,
        )
    
    def test_valid_lead_story_engine(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """lead_universe='story_engine' is valid."""
        callback = bridge.create_three_universe_callback()
        callback(
            event_id="evt_test",
            event_content="test",
            engineer_result=sample_engineer_result,
            ceremony_result=sample_ceremony_result,
            story_engine_result=sample_story_engine_result,
            lead_universe="story_engine",
            coherence_score=0.8,
        )
    
    def test_invalid_lead_universe(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Invalid lead_universe raises ValueError."""
        callback = bridge.create_three_universe_callback()
        
        with pytest.raises(ValueError, match="lead_universe must be one of"):
            callback(
                event_id="evt_test",
                event_content="test",
                engineer_result=sample_engineer_result,
                ceremony_result=sample_ceremony_result,
                story_engine_result=sample_story_engine_result,
                lead_universe="invalid_universe",
                coherence_score=0.8,
            )


# =============================================================================
# UNIVERSE RESULT TESTS
# =============================================================================

class TestUniverseResult:
    """Test UniverseResult data class."""
    
    def test_from_dict(self):
        """Can create UniverseResult from dict."""
        from narrative_tracing.adapters.langgraph_bridge import UniverseResult
        
        data = {
            "intent": "feature_implementation",
            "confidence": 0.85,
            "suggested_flows": ["code_review"],
            "context": {"scope": "api"},
        }
        
        result = UniverseResult.from_dict(data)
        
        assert result.intent == "feature_implementation"
        assert result.confidence == 0.85
        assert result.suggested_flows == ["code_review"]
        assert result.context["scope"] == "api"
    
    def test_to_dict(self):
        """Can convert UniverseResult to dict."""
        from narrative_tracing.adapters.langgraph_bridge import UniverseResult
        
        result = UniverseResult(
            intent="bug_fix",
            confidence=0.9,
            suggested_flows=["regression_test"],
            context={"severity": "high"},
        )
        
        data = result.to_dict()
        
        assert data["intent"] == "bug_fix"
        assert data["confidence"] == 0.9
        assert data["suggested_flows"] == ["regression_test"]
        assert data["context"]["severity"] == "high"
    
    def test_defaults_for_missing_keys(self):
        """UniverseResult handles missing dict keys gracefully."""
        from narrative_tracing.adapters.langgraph_bridge import UniverseResult
        
        result = UniverseResult.from_dict({})
        
        assert result.intent == "unknown"
        assert result.confidence == 0.0
        assert result.suggested_flows == []
        assert result.context == {}


# =============================================================================
# BEAT CREATION TESTS
# =============================================================================

class TestBeatCreation:
    """Test beat creation tracking through bridge."""
    
    def test_log_beat_creation(self, bridge):
        """Can log beat creation via bridge."""
        bridge.handler.log_beat_creation = MagicMock(return_value="beat_span_id")
        
        span_id = bridge.log_beat_creation(
            beat_id="beat_001",
            content="The journey begins with a single step.",
            sequence=1,
            narrative_function="inciting_incident",
            emotional_tone="wonder",
        )
        
        assert span_id == "beat_span_id"
        bridge.handler.log_beat_creation.assert_called_once()
        
        call_kwargs = bridge.handler.log_beat_creation.call_args.kwargs
        assert call_kwargs["beat_id"] == "beat_001"
        assert call_kwargs["sequence"] == 1
        assert call_kwargs["narrative_function"] == "inciting_incident"


# =============================================================================
# RESET AND STATISTICS TESTS
# =============================================================================

class TestStatistics:
    """Test bridge statistics tracking."""
    
    def test_reset_count(
        self,
        bridge,
        sample_engineer_result,
        sample_ceremony_result,
        sample_story_engine_result,
    ):
        """Can reset analysis count."""
        callback = bridge.create_three_universe_callback()
        
        # Log some analyses
        for i in range(3):
            callback(
                event_id=f"evt_{i}",
                event_content="test",
                engineer_result=sample_engineer_result,
                ceremony_result=sample_ceremony_result,
                story_engine_result=sample_story_engine_result,
                lead_universe="engineer",
                coherence_score=0.8,
            )
        
        assert bridge.analysis_count == 3
        
        bridge.reset_count()
        
        assert bridge.analysis_count == 0
