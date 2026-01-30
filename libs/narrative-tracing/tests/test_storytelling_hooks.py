"""
Tests for Storytelling Hooks Adapter

Tests the adapter that provides hooks for tracing beat creation,
lesson extraction, and narrative arc progression.

Test Coverage:
- Beat lifecycle tracing (context manager)
- Direct beat logging
- Character arc updates
- Theme thread updates
- Act transitions
- Gap identification
- Session statistics
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
def hooks(handler):
    """Create StorytellingHooks with handler."""
    from narrative_tracing.adapters import StorytellingHooks
    return StorytellingHooks(handler)


# =============================================================================
# BEAT LIFECYCLE TESTS (Context Manager)
# =============================================================================

class TestBeatLifecycleContextManager:
    """Test beat lifecycle tracing with context manager."""
    
    def test_trace_beat_lifecycle_yields_tracer(self, hooks):
        """Context manager yields a BeatTracer."""
        from narrative_tracing.adapters import BeatTracer
        
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            assert isinstance(tracer, BeatTracer)
            assert tracer.beat_id == "beat_001"
    
    def test_tracer_log_content(self, hooks):
        """BeatTracer can log content."""
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            span_id = tracer.log_content(
                content="The story begins with a discovery.",
                narrative_function="inciting_incident",
                act=1,
            )
            
            assert span_id is not None
            assert tracer.content_logged is True
    
    def test_tracer_log_analysis(self, hooks):
        """BeatTracer can log analysis."""
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            tracer.log_content("Content here", narrative_function="beat")
            span_id = tracer.log_analysis(
                classification="wonder",
                confidence=0.85,
                detected_emotions=["curiosity", "excitement"],
            )
            
            assert span_id is not None
            assert tracer.analysis_logged is True
    
    def test_tracer_log_enrichment(self, hooks):
        """BeatTracer can log enrichment."""
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            tracer.log_content("Content here", narrative_function="beat")
            span_id = tracer.log_enrichment(
                enrichment_type="dialogue_improvement",
                flows_used=["dialogue_enhancer", "character_deepener"],
                quality_before=0.6,
                quality_after=0.85,
            )
            
            assert span_id is not None
            assert tracer.enrichment_logged is True
    
    def test_tracer_log_lessons(self, hooks):
        """BeatTracer can log extracted lessons."""
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            tracer.log_content("Content here", narrative_function="beat")
            tracer.log_lessons([
                "Integration requires patience",
                "Systems reveal their coherence through observation",
            ])
            
            assert tracer.lessons_logged is True
            assert len(tracer.beat_info.lessons) == 2
    
    def test_beat_info_accumulated(self, hooks):
        """BeatTracer accumulates info into BeatInfo."""
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            tracer.log_content(
                content="Test content",
                sequence=5,
                narrative_function="turning_point",
                act=2,
                emotional_tone="tension",
            )
            
            info = tracer.beat_info
            assert info.beat_id == "beat_001"
            assert info.sequence == 5
            assert info.narrative_function == "turning_point"
            assert info.act == 2
            assert info.emotional_tone == "tension"
    
    def test_beat_stored_after_context(self, hooks):
        """Beat info is stored after context manager exits."""
        assert len(hooks.beats) == 0
        
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            tracer.log_content("Content", narrative_function="beat")
        
        assert len(hooks.beats) == 1
        assert hooks.beats[0].beat_id == "beat_001"


# =============================================================================
# DIRECT BEAT LOGGING TESTS
# =============================================================================

class TestDirectBeatLogging:
    """Test direct beat logging without context manager."""
    
    def test_log_beat_creation(self, hooks):
        """Can log beat creation directly."""
        span_id = hooks.log_beat_creation(
            beat_id="beat_002",
            content="Direct beat content",
            narrative_function="rising_action",
        )
        
        assert span_id is not None
    
    def test_auto_sequence_increment(self, hooks):
        """Sequence auto-increments with each beat."""
        assert hooks.current_sequence == 0
        
        hooks.log_beat_creation("beat_1", "Content 1", "beat")
        assert hooks.current_sequence == 1
        
        hooks.log_beat_creation("beat_2", "Content 2", "beat")
        assert hooks.current_sequence == 2
    
    def test_beat_count_tracks_beats(self, hooks):
        """Beat count tracks number of beats logged."""
        assert hooks.beat_count == 0
        
        hooks.log_beat_creation("beat_1", "Content 1", "beat")
        hooks.log_beat_creation("beat_2", "Content 2", "beat")
        hooks.log_beat_creation("beat_3", "Content 3", "beat")
        
        assert hooks.beat_count == 3


# =============================================================================
# CHARACTER ARC TESTS
# =============================================================================

class TestCharacterArcTracking:
    """Test character arc update logging."""
    
    def test_log_character_arc_update(self, hooks):
        """Can log character arc update."""
        span_id = hooks.log_character_arc_update(
            character_id="char_001",
            character_name="The Developer",
            arc_position_before=0.2,
            arc_position_after=0.35,
            growth_description="Gained confidence in integration",
        )
        
        assert span_id is not None
    
    def test_character_updates_tracked(self, hooks):
        """Character updates are tracked."""
        assert len(hooks.character_updates) == 0
        
        hooks.log_character_arc_update(
            character_id="char_001",
            character_name="The Developer",
            arc_position_before=0.2,
            arc_position_after=0.35,
            growth_description="Gained confidence",
        )
        
        assert len(hooks.character_updates) == 1
        assert hooks.character_updates[0].character_id == "char_001"
        assert hooks.character_updates[0].character_name == "The Developer"


# =============================================================================
# THEME TRACKING TESTS
# =============================================================================

class TestThemeTracking:
    """Test theme thread update logging."""
    
    def test_log_theme_update(self, hooks):
        """Can log theme update."""
        span_id = hooks.log_theme_update(
            theme_id="theme_001",
            theme_name="Integration",
            strength_before=0.3,
            strength_after=0.5,
            description="Theme strengthens as systems connect",
        )
        
        assert span_id is not None
    
    def test_theme_updates_tracked(self, hooks):
        """Theme updates are tracked."""
        assert len(hooks.theme_updates) == 0
        
        hooks.log_theme_update(
            theme_id="theme_001",
            theme_name="Integration",
            strength_before=0.3,
            strength_after=0.5,
            description="Theme strengthens",
        )
        
        assert len(hooks.theme_updates) == 1
        assert hooks.theme_updates[0].theme_name == "Integration"


# =============================================================================
# ACT TRANSITION TESTS
# =============================================================================

class TestActTransitions:
    """Test act transition logging."""
    
    def test_log_act_transition(self, hooks):
        """Can log act transition."""
        span_id = hooks.log_act_transition(
            from_act=1,
            to_act=2,
            reason="inciting_incident_complete",
        )
        
        assert span_id is not None
    
    def test_act_transition_updates_current_act(self, hooks):
        """Act transition updates current_act property."""
        assert hooks.current_act == 1
        
        hooks.log_act_transition(from_act=1, to_act=2)
        assert hooks.current_act == 2
        
        hooks.log_act_transition(from_act=2, to_act=3)
        assert hooks.current_act == 3


# =============================================================================
# GAP TRACKING TESTS
# =============================================================================

class TestGapTracking:
    """Test narrative gap logging."""
    
    def test_log_narrative_gap(self, hooks):
        """Can log narrative gap."""
        span_id = hooks.log_narrative_gap(
            gap_type="structural",
            description="Missing transition between scenes",
            severity=0.7,
            suggested_remediation="Add bridging beat",
        )
        
        assert span_id is not None


# =============================================================================
# SESSION STATISTICS TESTS
# =============================================================================

class TestSessionStatistics:
    """Test session statistics and summary."""
    
    def test_get_session_summary(self, hooks):
        """Can get session summary."""
        # Log some activity
        hooks.log_beat_creation("beat_1", "Content 1", "inciting_incident")
        hooks.log_beat_creation("beat_2", "Content 2", "rising_action")
        hooks.log_character_arc_update(
            "char_1", "Hero", 0.1, 0.3, "Started journey"
        )
        
        summary = hooks.get_session_summary()
        
        assert summary["beat_count"] == 2
        assert summary["current_sequence"] == 2
        assert summary["character_updates_count"] == 1
        assert len(summary["beats"]) == 2
    
    def test_reset_session(self, hooks):
        """Can reset session state."""
        # Log some activity
        hooks.log_beat_creation("beat_1", "Content 1", "beat")
        hooks.log_beat_creation("beat_2", "Content 2", "beat")
        hooks.log_act_transition(1, 2)
        
        assert hooks.beat_count == 2
        assert hooks.current_act == 2
        
        hooks.reset_session()
        
        assert hooks.beat_count == 0
        assert hooks.current_sequence == 0
        assert hooks.current_act == 1


# =============================================================================
# DATA CLASS TESTS
# =============================================================================

class TestBeatInfo:
    """Test BeatInfo data class."""
    
    def test_beat_info_creation(self):
        """Can create BeatInfo."""
        from narrative_tracing.adapters import BeatInfo
        
        info = BeatInfo(
            beat_id="beat_001",
            sequence=1,
            content="Test content",
            narrative_function="inciting_incident",
        )
        
        assert info.beat_id == "beat_001"
        assert info.sequence == 1
    
    def test_beat_info_to_dict(self):
        """BeatInfo converts to dictionary."""
        from narrative_tracing.adapters import BeatInfo
        
        info = BeatInfo(
            beat_id="beat_001",
            content="Test content",
            narrative_function="inciting_incident",
        )
        
        data = info.to_dict()
        
        assert data["beat_id"] == "beat_001"
        assert "content_preview" in data
        assert data["narrative_function"] == "inciting_incident"
    
    def test_beat_info_truncates_long_content(self):
        """BeatInfo truncates long content in to_dict."""
        from narrative_tracing.adapters import BeatInfo
        
        long_content = "x" * 300
        info = BeatInfo(beat_id="beat_001", content=long_content)
        
        data = info.to_dict()
        
        assert len(data["content_preview"]) < len(long_content)
        assert "..." in data["content_preview"]


class TestCharacterUpdate:
    """Test CharacterUpdate data class."""
    
    def test_character_update_to_dict(self):
        """CharacterUpdate converts to dictionary with growth calculation."""
        from narrative_tracing.adapters import CharacterUpdate
        
        update = CharacterUpdate(
            character_id="char_001",
            character_name="Hero",
            arc_position_before=0.2,
            arc_position_after=0.5,
            growth_description="Major development",
        )
        
        data = update.to_dict()
        
        assert data["growth"] == 0.3  # 0.5 - 0.2


class TestThemeUpdate:
    """Test ThemeUpdate data class."""
    
    def test_theme_update_to_dict(self):
        """ThemeUpdate converts to dictionary with change calculation."""
        from narrative_tracing.adapters import ThemeUpdate
        
        update = ThemeUpdate(
            theme_id="theme_001",
            theme_name="Integration",
            strength_before=0.3,
            strength_after=0.6,
            description="Theme grows",
        )
        
        data = update.to_dict()
        
        assert data["change"] == pytest.approx(0.3)  # 0.6 - 0.3
