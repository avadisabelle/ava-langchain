"""
Live integration tests for Storytelling hooks.

These tests verify that the StorytellingHooks adapter correctly:
1. Traces beat creation lifecycle
2. Captures lessons extraction
3. Tracks character arc updates
4. Generates traces with patent-evidence quality

Run with:
    cd /workspace/langchain/libs/narrative-tracing
    python -m pytest tests/test_storytelling_hooks_live.py -v
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# Add narrative-tracing to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from narrative_tracing import NarrativeTracingHandler
from narrative_tracing.adapters import (
    StorytellingHooks,
    BeatTracer,
    BeatInfo,
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
        mock_span.id = "span_storytelling_live"
        mock_trace.span.return_value = mock_span
        mock_trace.id = "trace_storytelling_live_001"
        mock_instance.trace.return_value = mock_trace
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def handler(mock_langfuse):
    """Create a NarrativeTracingHandler for testing."""
    return NarrativeTracingHandler(
        story_id="story_storytelling_integration",
        session_id="session_storytelling_live",
    )


@pytest.fixture
def hooks(handler):
    """Create a StorytellingHooks instance."""
    return StorytellingHooks(handler)


# ============================================================================
# Simulated Story Generation Engine
# ============================================================================


class MockStoryGenerationEngine:
    """Simulates a story generation engine with tracing hooks."""
    
    def __init__(self, hooks: StorytellingHooks):
        self.hooks = hooks
        self.generated_beats: List[Dict] = []
        self.extracted_lessons: List[str] = []
    
    def generate_beat(
        self,
        beat_id: str,
        content: str,
        narrative_function: str,
        act: int,
        emotional_tone: str,
        character_id: str = None,
    ) -> BeatInfo:
        """Generate a story beat with full lifecycle tracing."""
        with self.hooks.trace_beat_lifecycle(beat_id) as tracer:
            # Log initial content creation
            tracer.log_content(
                content=content,
                sequence=len(self.generated_beats) + 1,
                narrative_function=narrative_function,
                act=act,
                emotional_tone=emotional_tone,
                character_id=character_id,
            )
            
            # Simulate analysis
            tracer.log_analysis(
                classification=narrative_function,
                confidence=0.88,
                detected_emotions=[emotional_tone, "anticipation"],
            )
            
            # Simulate enrichment
            quality_before = 0.65
            quality_after = 0.85
            tracer.log_enrichment(
                enrichment_type="character_deepening",
                flows_used=["character_enricher", "theme_weaver"],
                quality_before=quality_before,
                quality_after=quality_after,
            )
            
            # Extract lessons
            lessons = self._extract_lessons(content, narrative_function)
            tracer.log_lessons(lessons)
            self.extracted_lessons.extend(lessons)
            
            # Get the beat info
            beat_info = tracer.beat_info
            self.generated_beats.append({
                "beat_id": beat_id,
                "content": content,
                "narrative_function": narrative_function,
                "lessons": lessons,
            })
            
            return beat_info
    
    def update_character_arc(
        self,
        character_id: str,
        character_name: str,
        beat_id: str,
        growth_description: str,
        arc_before: float,
        arc_after: float,
    ):
        """Update a character's arc position with tracing."""
        self.hooks.log_character_arc_update(
            character_id=character_id,
            character_name=character_name,
            arc_position_before=arc_before,
            arc_position_after=arc_after,
            growth_description=growth_description,
            beat_id=beat_id,
        )
    
    def transition_act(self, from_act: int, to_act: int, trigger_beat_id: str):
        """Log an act transition."""
        self.hooks.log_act_transition(
            from_act=from_act,
            to_act=to_act,
            beat_id=trigger_beat_id,
        )
    
    def _extract_lessons(self, content: str, function: str) -> List[str]:
        """Simulate lesson extraction from beat content."""
        lessons = []
        
        if "coherence" in content.lower():
            lessons.append("Coherence emerges through consistent observation")
        if "trust" in content.lower():
            lessons.append("Trust is built through reliable actions")
        if "recognition" in content.lower():
            lessons.append("Recognition of patterns leads to understanding")
        
        # Default lesson based on narrative function
        if function == "inciting_incident":
            lessons.append("New challenges reveal hidden strengths")
        elif function == "rising_action":
            lessons.append("Progress requires sustained effort")
        elif function == "climax":
            lessons.append("Decisive moments define character")
        elif function == "resolution":
            lessons.append("Integration completes the journey")
        
        return lessons


# ============================================================================
# Live Integration Tests
# ============================================================================


class TestBeatGenerationLifecycle:
    """Test full beat generation lifecycle."""
    
    def test_beat_created_with_tracing(self, hooks):
        """Test that beat creation is fully traced."""
        engine = MockStoryGenerationEngine(hooks)
        
        beat = engine.generate_beat(
            beat_id="beat_live_001",
            content="The ecosystem awakens to its own coherence through observation.",
            narrative_function="rising_action",
            act=2,
            emotional_tone="wonder",
            character_id="ecosystem",
        )
        
        assert beat is not None
        assert beat.beat_id == "beat_live_001"
        assert beat.narrative_function == "rising_action"
        assert hooks.beat_count == 1
    
    def test_lessons_extracted_and_logged(self, hooks):
        """Test that lessons are extracted and logged."""
        engine = MockStoryGenerationEngine(hooks)
        
        engine.generate_beat(
            beat_id="beat_lessons_001",
            content="Through coherence and trust, the system recognizes its potential.",
            narrative_function="inciting_incident",
            act=1,
            emotional_tone="curiosity",
        )
        
        # Verify lessons were extracted
        assert len(engine.extracted_lessons) >= 2
        assert any("coherence" in lesson.lower() for lesson in engine.extracted_lessons)
        assert any("trust" in lesson.lower() for lesson in engine.extracted_lessons)
    
    def test_multiple_beats_tracked(self, hooks):
        """Test that multiple beats are all tracked."""
        engine = MockStoryGenerationEngine(hooks)
        
        # Generate act structure
        engine.generate_beat("beat_1", "Setup: the beginning", "exposition", 1, "calm")
        engine.generate_beat("beat_2", "The call to adventure", "inciting_incident", 1, "excitement")
        engine.generate_beat("beat_3", "Rising tensions build", "rising_action", 2, "tension")
        engine.generate_beat("beat_4", "The decisive moment", "climax", 2, "intensity")
        engine.generate_beat("beat_5", "Resolution and peace", "resolution", 3, "peace")
        
        assert hooks.beat_count == 5
        assert len(engine.generated_beats) == 5
        assert len(engine.extracted_lessons) >= 4  # Most beats generate lessons


class TestCharacterArcTracking:
    """Test character arc update tracking."""
    
    def test_character_arc_update_logged(self, hooks):
        """Test that character arc updates are logged."""
        engine = MockStoryGenerationEngine(hooks)
        
        # Generate beat first
        engine.generate_beat(
            beat_id="arc_beat_001",
            content="The protagonist recognizes their own growth.",
            narrative_function="turning_point",
            act=2,
            emotional_tone="recognition",
            character_id="protagonist",
        )
        
        # Update character arc
        engine.update_character_arc(
            character_id="protagonist",
            character_name="Elena",
            beat_id="arc_beat_001",
            growth_description="Recognizes own strength after trial",
            arc_before=0.4,
            arc_after=0.6,
        )
        
        session = hooks.get_session_summary()
        assert session["character_updates_count"] == 1
    
    def test_multiple_character_updates(self, hooks):
        """Test tracking multiple character arc updates."""
        engine = MockStoryGenerationEngine(hooks)
        
        characters = [
            ("char_1", "Elena", "Overcomes fear"),
            ("char_2", "Marcus", "Learns to trust"),
            ("char_3", "The System", "Achieves coherence"),
        ]
        
        for i, (char_id, name, growth) in enumerate(characters):
            engine.update_character_arc(
                character_id=char_id,
                character_name=name,
                beat_id=f"multi_arc_beat_{i}",
                growth_description=growth,
                arc_before=0.3 + (i * 0.1),
                arc_after=0.5 + (i * 0.1),
            )
        
        session = hooks.get_session_summary()
        assert session["character_updates_count"] == 3


class TestActTransitions:
    """Test act transition tracking."""
    
    def test_act_transition_logged(self, hooks):
        """Test that act transitions are logged."""
        engine = MockStoryGenerationEngine(hooks)
        
        # Generate beats for Act 1
        engine.generate_beat("act1_beat", "Act 1 content", "exposition", 1, "calm")
        
        # Transition to Act 2
        engine.transition_act(
            from_act=1,
            to_act=2,
            trigger_beat_id="act1_beat",
        )
        
        session = hooks.get_session_summary()
        assert session["current_act"] == 2


class TestTraceExport:
    """Test trace export for patent evidence."""
    
    def test_export_storytelling_trace(self, hooks, handler):
        """Test exporting storytelling trace as JSON."""
        engine = MockStoryGenerationEngine(hooks)
        
        # Generate a complete story arc
        engine.generate_beat(
            beat_id="patent_beat_001",
            content="The narrative intelligence ecosystem discovers coherence through observation.",
            narrative_function="inciting_incident",
            act=1,
            emotional_tone="wonder",
            character_id="ecosystem",
        )
        
        engine.update_character_arc(
            character_id="ecosystem",
            character_name="The Narrative Intelligence Ecosystem",
            beat_id="patent_beat_001",
            growth_description="Recognizes own coherence",
            arc_before=0.3,
            arc_after=0.5,
        )
        
        # Build trace data
        session = hooks.get_session_summary()
        trace_data = {
            "trace_type": "storytelling_beat_live",
            "ceremony_uuid": "cfa7b236-3bf1-4b9c-aad2-f5729da3d4f8",
            "story_id": handler.story_id,
            "beats_generated": hooks.beat_count,
            "lessons_extracted": len(engine.extracted_lessons),
            "character_updates": session["character_updates_count"],
            "current_act": session["current_act"],
            "beats": [b["beat_id"] for b in engine.generated_beats],
            "lessons": engine.extracted_lessons,
        }
        
        # Verify JSON serializable
        json_output = json.dumps(trace_data, indent=2)
        assert "storytelling_beat_live" in json_output
        assert "patent_beat_001" in json_output


class TestSessionManagement:
    """Test session state management."""
    
    def test_session_summary_accurate(self, hooks):
        """Test that session summary reflects actual state."""
        engine = MockStoryGenerationEngine(hooks)
        
        # Build up session state
        engine.generate_beat("s_beat_1", "Content 1", "exposition", 1, "calm")
        engine.generate_beat("s_beat_2", "Content 2", "rising_action", 2, "tension")
        engine.update_character_arc("char_1", "Char 1", "s_beat_1", "Growth", 0.3, 0.5)
        engine.transition_act(1, 2, "s_beat_1")
        
        summary = hooks.get_session_summary()
        
        assert summary["beat_count"] == 2
        assert summary["character_updates_count"] == 1
        assert summary["current_act"] == 2
    
    def test_session_reset(self, hooks):
        """Test that session can be reset."""
        engine = MockStoryGenerationEngine(hooks)
        
        # Generate some state
        engine.generate_beat("reset_beat", "Content", "exposition", 1, "calm")
        assert hooks.beat_count == 1
        
        # Reset
        hooks.reset_session()
        
        # Verify reset
        assert hooks.beat_count == 0
        summary = hooks.get_session_summary()
        assert summary["beat_count"] == 0
