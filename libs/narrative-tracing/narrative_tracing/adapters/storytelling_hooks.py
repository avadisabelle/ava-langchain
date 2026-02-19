"""
Storytelling Hooks Adapter

Provides hooks for the Storytelling system to automatically trace
beat creation, lesson extraction, and narrative arc progression.

The Storytelling system generates stories through beats. Each beat
has a narrative function (inciting_incident, rising_action, etc.)
and can have lessons extracted from it. This adapter ensures all
of this is traced.

Key Features:
- Beat lifecycle tracing (created, analyzed, enriched)
- Lesson extraction recording
- Act and narrative function tracking
- Character arc updates
- Theme thread evolution

Usage:
```python
from narrative_tracing import NarrativeTracingHandler
from narrative_tracing.adapters import StorytellingHooks

handler = NarrativeTracingHandler(story_id="story_123")
hooks = StorytellingHooks(handler)

# Hook into beat creation
with hooks.trace_beat_lifecycle("beat_001") as beat_tracer:
    content = generate_beat_content()
    beat_tracer.log_content(content, narrative_function="inciting_incident")
    
    # Analyze and enrich
    analysis = analyze_beat(content)
    beat_tracer.log_analysis(analysis)
    
    enriched = enrich_beat(content)
    beat_tracer.log_enrichment(enriched)
    
    # Extract lessons
    lessons = extract_lessons(content)
    beat_tracer.log_lessons(lessons)
```

Session ID: langchain-narrative-tracing
Created: 2026-01-30
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional

from ..handler import NarrativeTracingHandler
from ..event_types import NarrativeEventType, NarrativeMetrics


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BeatInfo:
    """Information about a story beat being traced."""
    
    beat_id: str
    sequence: int = 0
    content: str = ""
    narrative_function: str = "beat"
    act: int = 2
    emotional_tone: Optional[str] = None
    character_id: Optional[str] = None
    lessons: List[str] = field(default_factory=list)
    
    # Timing
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Quality tracking
    quality_before: float = 0.0
    quality_after: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "beat_id": self.beat_id,
            "sequence": self.sequence,
            "content_preview": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "narrative_function": self.narrative_function,
            "act": self.act,
            "emotional_tone": self.emotional_tone,
            "character_id": self.character_id,
            "lessons": self.lessons,
            "created_at": self.created_at,
            "quality_before": self.quality_before,
            "quality_after": self.quality_after,
        }


@dataclass
class CharacterUpdate:
    """Character arc update information."""
    
    character_id: str
    character_name: str
    arc_position_before: float
    arc_position_after: float
    growth_description: str
    beat_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "character_id": self.character_id,
            "character_name": self.character_name,
            "arc_position_before": self.arc_position_before,
            "arc_position_after": self.arc_position_after,
            "growth": self.arc_position_after - self.arc_position_before,
            "growth_description": self.growth_description,
            "beat_id": self.beat_id,
        }


@dataclass
class ThemeUpdate:
    """Theme thread update information."""
    
    theme_id: str
    theme_name: str
    strength_before: float
    strength_after: float
    description: str
    beat_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "theme_id": self.theme_id,
            "theme_name": self.theme_name,
            "strength_before": self.strength_before,
            "strength_after": self.strength_after,
            "change": self.strength_after - self.strength_before,
            "description": self.description,
            "beat_id": self.beat_id,
        }


# =============================================================================
# BEAT TRACER (Context Manager Helper)
# =============================================================================

class BeatTracer:
    """
    Context-scoped tracer for a single beat's lifecycle.
    
    This is returned by StorytellingHooks.trace_beat_lifecycle()
    and provides methods for logging each stage of beat processing.
    """
    
    def __init__(
        self,
        beat_id: str,
        handler: NarrativeTracingHandler,
        parent_span_id: Optional[str] = None,
    ) -> None:
        """Initialize beat tracer."""
        self.beat_id = beat_id
        self.handler = handler
        self.parent_span_id = parent_span_id
        
        # Track what's been logged
        self.content_logged = False
        self.analysis_logged = False
        self.enrichment_logged = False
        self.lessons_logged = False
        
        # Store span IDs for linking
        self._content_span_id: Optional[str] = None
        self._analysis_span_id: Optional[str] = None
        self._enrichment_span_id: Optional[str] = None
        
        # Beat info
        self._beat_info = BeatInfo(beat_id=beat_id)
    
    def log_content(
        self,
        content: str,
        sequence: int = 0,
        narrative_function: str = "beat",
        act: int = 2,
        emotional_tone: Optional[str] = None,
        character_id: Optional[str] = None,
    ) -> str:
        """
        Log beat content creation.
        
        Args:
            content: The beat text content
            sequence: Sequence number in the story
            narrative_function: Function like inciting_incident, rising_action
            act: Which act (1, 2, or 3)
            emotional_tone: Detected emotional tone
            character_id: Primary character involved
        
        Returns:
            The span ID of the logged event
        """
        self._beat_info.content = content
        self._beat_info.sequence = sequence
        self._beat_info.narrative_function = narrative_function
        self._beat_info.act = act
        self._beat_info.emotional_tone = emotional_tone
        self._beat_info.character_id = character_id
        
        self._content_span_id = self.handler.log_beat_creation(
            beat_id=self.beat_id,
            content=content,
            sequence=sequence,
            narrative_function=narrative_function,
            emotional_tone=emotional_tone,
            character_id=character_id,
            parent_span_id=self.parent_span_id,
        )
        
        self.content_logged = True
        return self._content_span_id
    
    def log_analysis(
        self,
        classification: str,
        confidence: float,
        detected_emotions: Optional[List[str]] = None,
        analysis_type: str = "emotional",
    ) -> str:
        """
        Log beat analysis results.
        
        Args:
            classification: Result classification
            confidence: Confidence score (0-1)
            detected_emotions: List of detected emotions
            analysis_type: Type of analysis performed
        
        Returns:
            The span ID of the logged event
        """
        self._analysis_span_id = self.handler.log_beat_analysis(
            beat_id=self.beat_id,
            analysis_type=analysis_type,
            classification=classification,
            confidence=confidence,
            detected_emotions=detected_emotions,
            parent_span_id=self._content_span_id or self.parent_span_id,
        )
        
        self._beat_info.emotional_tone = classification
        self.analysis_logged = True
        return self._analysis_span_id
    
    def log_enrichment(
        self,
        enrichment_type: str,
        flows_used: List[str],
        quality_before: float,
        quality_after: float,
    ) -> str:
        """
        Log beat enrichment results.
        
        Args:
            enrichment_type: Type of enrichment performed
            flows_used: List of flows/agents used
            quality_before: Quality score before enrichment
            quality_after: Quality score after enrichment
        
        Returns:
            The span ID of the logged event
        """
        self._enrichment_span_id = self.handler.log_beat_enrichment(
            beat_id=self.beat_id,
            enrichment_type=enrichment_type,
            flows_used=flows_used,
            quality_before=quality_before,
            quality_after=quality_after,
            parent_span_id=self._analysis_span_id or self._content_span_id or self.parent_span_id,
        )
        
        self._beat_info.quality_before = quality_before
        self._beat_info.quality_after = quality_after
        self.enrichment_logged = True
        return self._enrichment_span_id
    
    def log_lessons(
        self,
        lessons: List[str],
    ) -> None:
        """
        Log extracted lessons.
        
        Args:
            lessons: List of lesson strings extracted from beat
        """
        self._beat_info.lessons = lessons
        self.lessons_logged = True
        
        # Log as metadata on the beat (lessons don't need their own span)
        # The handler will include this in the beat's trace metadata
    
    @property
    def beat_info(self) -> BeatInfo:
        """Get the accumulated beat info."""
        return self._beat_info


# =============================================================================
# STORYTELLING HOOKS
# =============================================================================

class StorytellingHooks:
    """
    Hooks for integrating narrative-tracing with the Storytelling system.
    
    Provides context managers and methods for tracing:
    - Beat creation lifecycle
    - Lesson extraction
    - Character arc updates
    - Theme thread evolution
    - Act transitions
    
    Args:
        handler: NarrativeTracingHandler instance for logging
        auto_sequence: Automatically increment sequence numbers
    
    Example:
    ```python
    hooks = StorytellingHooks(handler)
    
    # Trace a beat's full lifecycle
    with hooks.trace_beat_lifecycle("beat_001") as tracer:
        tracer.log_content(content, narrative_function="inciting_incident")
        tracer.log_analysis("wonder", 0.85)
        tracer.log_lessons(["Integration requires patience"])
    
    # Log character updates
    hooks.log_character_arc_update(
        character_id="char_001",
        character_name="The Developer",
        arc_position_before=0.2,
        arc_position_after=0.35,
        growth_description="Gained confidence in integration"
    )
    ```
    """
    
    def __init__(
        self,
        handler: NarrativeTracingHandler,
        auto_sequence: bool = True,
    ) -> None:
        """Initialize storytelling hooks."""
        self.handler = handler
        self.auto_sequence = auto_sequence
        
        # Track sequences
        self._sequence_counter = 0
        self._current_act = 1
        
        # Track beats in current session
        self._beats: List[BeatInfo] = []
        
        # Track arc and theme updates
        self._character_updates: List[CharacterUpdate] = []
        self._theme_updates: List[ThemeUpdate] = []
    
    # =========================================================================
    # BEAT LIFECYCLE
    # =========================================================================
    
    @contextmanager
    def trace_beat_lifecycle(
        self,
        beat_id: str,
        parent_span_id: Optional[str] = None,
    ) -> Generator[BeatTracer, None, None]:
        """
        Context manager for tracing a beat's full lifecycle.
        
        Creates a BeatTracer that can log each stage of beat processing.
        
        Args:
            beat_id: Unique identifier for the beat
            parent_span_id: Optional parent span for nesting
        
        Yields:
            BeatTracer for logging beat stages
        
        Example:
        ```python
        with hooks.trace_beat_lifecycle("beat_001") as tracer:
            tracer.log_content("The story begins...", narrative_function="inciting_incident")
            tracer.log_analysis("wonder", 0.9)
        ```
        """
        if self.auto_sequence:
            self._sequence_counter += 1
        
        tracer = BeatTracer(
            beat_id=beat_id,
            handler=self.handler,
            parent_span_id=parent_span_id,
        )
        
        try:
            yield tracer
        finally:
            # Store the beat info
            self._beats.append(tracer.beat_info)
    
    def log_beat_creation(
        self,
        beat_id: str,
        content: str,
        narrative_function: str = "beat",
        act: int = 2,
        emotional_tone: Optional[str] = None,
        character_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log beat creation directly (without context manager).
        
        Use this for simple beat logging without the full lifecycle.
        
        Args:
            beat_id: Unique identifier for the beat
            content: The beat text content
            narrative_function: Function like inciting_incident
            act: Which act (1, 2, or 3)
            emotional_tone: Detected emotional tone
            character_id: Primary character involved
            parent_span_id: Optional parent span
        
        Returns:
            The span ID of the logged event
        """
        if self.auto_sequence:
            self._sequence_counter += 1
        
        span_id = self.handler.log_beat_creation(
            beat_id=beat_id,
            content=content,
            sequence=self._sequence_counter,
            narrative_function=narrative_function,
            emotional_tone=emotional_tone,
            character_id=character_id,
            parent_span_id=parent_span_id,
        )
        
        # Track the beat
        self._beats.append(BeatInfo(
            beat_id=beat_id,
            sequence=self._sequence_counter,
            content=content,
            narrative_function=narrative_function,
            act=act,
            emotional_tone=emotional_tone,
            character_id=character_id,
        ))
        
        return span_id
    
    # =========================================================================
    # CHARACTER ARC TRACKING
    # =========================================================================
    
    def log_character_arc_update(
        self,
        character_id: str,
        character_name: str,
        arc_position_before: float,
        arc_position_after: float,
        growth_description: str,
        beat_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log a character arc update.
        
        Args:
            character_id: Unique character identifier
            character_name: Display name for the character
            arc_position_before: Arc position before this beat (0-1)
            arc_position_after: Arc position after this beat (0-1)
            growth_description: Description of the character's growth
            beat_id: Optional beat that caused this update
            parent_span_id: Optional parent span
        
        Returns:
            The span ID of the logged event
        """
        span_id = self.handler.log_character_arc_update(
            character_id=character_id,
            character_name=character_name,
            arc_position_before=arc_position_before,
            arc_position_after=arc_position_after,
            growth_description=growth_description,
            beat_id=beat_id,
            parent_span_id=parent_span_id,
        )
        
        # Track the update
        self._character_updates.append(CharacterUpdate(
            character_id=character_id,
            character_name=character_name,
            arc_position_before=arc_position_before,
            arc_position_after=arc_position_after,
            growth_description=growth_description,
            beat_id=beat_id,
        ))
        
        return span_id
    
    # =========================================================================
    # THEME TRACKING
    # =========================================================================
    
    def log_theme_update(
        self,
        theme_id: str,
        theme_name: str,
        strength_before: float,
        strength_after: float,
        description: str,
        beat_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log a theme thread update.
        
        Args:
            theme_id: Unique theme identifier
            theme_name: Display name for the theme
            strength_before: Theme strength before (0-1)
            strength_after: Theme strength after (0-1)
            description: Description of how theme evolved
            beat_id: Optional beat that caused this update
            parent_span_id: Optional parent span
        
        Returns:
            The span ID of the logged event
        """
        span_id = self.handler.log_event(
            event_type=NarrativeEventType.THEME_STRENGTH_CHANGED,
            input_data={
                "theme_id": theme_id,
                "theme_name": theme_name,
                "strength_before": strength_before,
            },
            output_data={
                "strength_after": strength_after,
                "change": strength_after - strength_before,
                "description": description,
            },
            beat_id=beat_id,
            parent_span_id=parent_span_id,
        )
        
        # Track the update
        self._theme_updates.append(ThemeUpdate(
            theme_id=theme_id,
            theme_name=theme_name,
            strength_before=strength_before,
            strength_after=strength_after,
            description=description,
            beat_id=beat_id,
        ))
        
        return span_id
    
    # =========================================================================
    # ACT TRANSITIONS
    # =========================================================================
    
    def log_act_transition(
        self,
        from_act: int,
        to_act: int,
        beat_id: Optional[str] = None,
        reason: str = "narrative_progression",
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log transition between acts.
        
        Args:
            from_act: Previous act number (1, 2, or 3)
            to_act: New act number
            beat_id: Optional beat that caused the transition
            reason: Reason for the transition
            parent_span_id: Optional parent span
        
        Returns:
            The span ID of the logged event
        """
        self._current_act = to_act
        
        return self.handler.log_event(
            event_type=NarrativeEventType.STORY_GENERATION_END,  # Using closest event type
            input_data={
                "transition": "act_change",
                "from_act": from_act,
                "to_act": to_act,
            },
            output_data={
                "reason": reason,
                "beat_id": beat_id,
            },
            metadata={
                "current_act": to_act,
            },
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # GAP TRACKING
    # =========================================================================
    
    def log_narrative_gap(
        self,
        gap_type: str,
        description: str,
        severity: float,
        beat_id: Optional[str] = None,
        suggested_remediation: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log identification of a narrative gap.
        
        Args:
            gap_type: Type of gap (structural, thematic, character, etc.)
            description: Description of the gap
            severity: How severe (0-1)
            beat_id: Optional related beat
            suggested_remediation: Optional suggestion for fixing
            parent_span_id: Optional parent span
        
        Returns:
            The span ID of the logged event
        """
        return self.handler.log_gap_identified(
            gap_type=gap_type,
            description=description,
            severity=severity,
            beat_id=beat_id,
            suggested_remediation=suggested_remediation,
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # SESSION STATISTICS
    # =========================================================================
    
    @property
    def beat_count(self) -> int:
        """Number of beats logged in this session."""
        return len(self._beats)
    
    @property
    def current_sequence(self) -> int:
        """Current sequence number."""
        return self._sequence_counter
    
    @property
    def current_act(self) -> int:
        """Current act number."""
        return self._current_act
    
    @property
    def beats(self) -> List[BeatInfo]:
        """All beats logged in this session."""
        return list(self._beats)
    
    @property
    def character_updates(self) -> List[CharacterUpdate]:
        """All character updates logged."""
        return list(self._character_updates)
    
    @property
    def theme_updates(self) -> List[ThemeUpdate]:
        """All theme updates logged."""
        return list(self._theme_updates)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the storytelling session."""
        return {
            "beat_count": self.beat_count,
            "current_sequence": self.current_sequence,
            "current_act": self.current_act,
            "character_updates_count": len(self._character_updates),
            "theme_updates_count": len(self._theme_updates),
            "beats": [b.to_dict() for b in self._beats],
        }
    
    def reset_session(self) -> None:
        """Reset session state."""
        self._sequence_counter = 0
        self._current_act = 1
        self._beats.clear()
        self._character_updates.clear()
        self._theme_updates.clear()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "StorytellingHooks",
    "BeatTracer",
    "BeatInfo",
    "CharacterUpdate",
    "ThemeUpdate",
]
