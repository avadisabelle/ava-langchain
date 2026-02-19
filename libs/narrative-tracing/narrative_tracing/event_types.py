"""
Narrative Event Types for Langfuse Tracing

Defines all narrative-specific event types that can be traced across the
Narrative Intelligence Stack. These event types provide semantic meaning
to traces, making them human-readable and learnable.

Event Categories:
- Beat Events: Story beat lifecycle (creation, analysis, enrichment)
- Character Events: Character arc tracking
- Theme Events: Thematic thread management
- Universe Events: Three-universe processing
- Routing Events: Flow routing decisions
- Checkpoint Events: State persistence

Integration with LangGraph:
These event types align with the unified_state_bridge.py types from
/workspace/langgraph/libs/narrative-intelligence/narrative_intelligence/schemas/

Session ID: langchain-narrative-tracing
Created: 2025-12-31
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# EVENT TYPE ENUMERATION
# =============================================================================

class NarrativeEventType(Enum):
    """Categories of traceable narrative operations."""
    
    # Beat Events
    BEAT_CREATED = "narrative.beat.created"
    BEAT_ANALYZED = "narrative.beat.analyzed"
    BEAT_ENRICHED = "narrative.beat.enriched"
    BEAT_QUALITY_ASSESSED = "narrative.beat.quality_assessed"
    
    # Character Events
    CHARACTER_ARC_ANALYZED = "narrative.character.arc_analyzed"
    CHARACTER_ARC_UPDATED = "narrative.character.arc_updated"
    CHARACTER_RELATIONSHIP_CHANGED = "narrative.character.relationship"
    
    # Theme Events
    THEME_DETECTED = "narrative.theme.detected"
    THEME_TENSION_IDENTIFIED = "narrative.theme.tension"
    THEME_STRENGTH_CHANGED = "narrative.theme.strength_changed"
    THEME_RESOLVED = "narrative.theme.resolved"
    
    # Three-Universe Events (from multiverse_3act)
    THREE_UNIVERSE_ANALYSIS = "narrative.universe.analysis"
    UNIVERSE_LEAD_DETERMINED = "narrative.universe.lead"
    UNIVERSE_COHERENCE_CALCULATED = "narrative.universe.coherence"
    
    # Routing Events
    INTENT_CLASSIFIED = "narrative.routing.intent"
    ROUTING_DECISION = "narrative.routing.decision"
    FLOW_EXECUTED = "narrative.routing.flow_executed"
    FLOW_RESULT = "narrative.routing.flow_result"
    
    # Checkpoint Events
    NARRATIVE_CHECKPOINT = "narrative.checkpoint.saved"
    NARRATIVE_RESTORED = "narrative.checkpoint.restored"
    EPISODE_BOUNDARY = "narrative.checkpoint.episode_boundary"
    
    # Story Generation Events
    STORY_GENERATION_START = "narrative.story.start"
    STORY_GENERATION_END = "narrative.story.end"
    STORY_QUALITY_METRICS = "narrative.story.metrics"
    
    # Gap Analysis Events
    GAP_IDENTIFIED = "narrative.gap.identified"
    GAP_REMEDIATED = "narrative.gap.remediated"
    
    # Webhook Events (from Miadi-46)
    WEBHOOK_RECEIVED = "narrative.webhook.received"
    WEBHOOK_TRANSFORMED = "narrative.webhook.transformed"


# =============================================================================
# EVENT GLYPHS FOR VISUAL DISPLAY
# =============================================================================

EVENT_GLYPHS = {
    # Beat Events
    NarrativeEventType.BEAT_CREATED: "📝",
    NarrativeEventType.BEAT_ANALYZED: "🔍",
    NarrativeEventType.BEAT_ENRICHED: "✨",
    NarrativeEventType.BEAT_QUALITY_ASSESSED: "📊",
    
    # Character Events
    NarrativeEventType.CHARACTER_ARC_ANALYZED: "🎭",
    NarrativeEventType.CHARACTER_ARC_UPDATED: "📈",
    NarrativeEventType.CHARACTER_RELATIONSHIP_CHANGED: "🤝",
    
    # Theme Events
    NarrativeEventType.THEME_DETECTED: "🎨",
    NarrativeEventType.THEME_TENSION_IDENTIFIED: "⚡",
    NarrativeEventType.THEME_STRENGTH_CHANGED: "📶",
    NarrativeEventType.THEME_RESOLVED: "🎯",
    
    # Three-Universe Events
    NarrativeEventType.THREE_UNIVERSE_ANALYSIS: "🌌",
    NarrativeEventType.UNIVERSE_LEAD_DETERMINED: "🎯",
    NarrativeEventType.UNIVERSE_COHERENCE_CALCULATED: "🔄",
    
    # Routing Events
    NarrativeEventType.INTENT_CLASSIFIED: "🧭",
    NarrativeEventType.ROUTING_DECISION: "🚀",
    NarrativeEventType.FLOW_EXECUTED: "⚙️",
    NarrativeEventType.FLOW_RESULT: "✅",
    
    # Checkpoint Events
    NarrativeEventType.NARRATIVE_CHECKPOINT: "💾",
    NarrativeEventType.NARRATIVE_RESTORED: "🔙",
    NarrativeEventType.EPISODE_BOUNDARY: "📺",
    
    # Story Generation Events
    NarrativeEventType.STORY_GENERATION_START: "📖",
    NarrativeEventType.STORY_GENERATION_END: "📕",
    NarrativeEventType.STORY_QUALITY_METRICS: "📈",
    
    # Gap Events
    NarrativeEventType.GAP_IDENTIFIED: "🕳️",
    NarrativeEventType.GAP_REMEDIATED: "🩹",
    
    # Webhook Events
    NarrativeEventType.WEBHOOK_RECEIVED: "🔔",
    NarrativeEventType.WEBHOOK_TRANSFORMED: "🔄",
}


# =============================================================================
# NARRATIVE SPAN CLASSES
# =============================================================================

@dataclass
class NarrativeSpan:
    """A traced operation with narrative context."""
    
    span_id: str
    trace_id: str
    event_type: NarrativeEventType
    
    # Story context
    story_id: str
    session_id: Optional[str] = None
    beat_id: Optional[str] = None
    
    # Character context
    character_ids: List[str] = field(default_factory=list)
    
    # Emotional/thematic context
    emotional_tone: Optional[str] = None
    theme_keywords: List[str] = field(default_factory=list)
    
    # Three-universe context
    lead_universe: Optional[str] = None  # "engineer", "ceremony", "story_engine"
    universe_coherence: Optional[float] = None
    
    # Data
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_span_id: Optional[str] = None
    
    # Status
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Langfuse."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "event_type": self.event_type.value,
            "story_id": self.story_id,
            "session_id": self.session_id,
            "beat_id": self.beat_id,
            "character_ids": self.character_ids,
            "emotional_tone": self.emotional_tone,
            "theme_keywords": self.theme_keywords,
            "lead_universe": self.lead_universe,
            "universe_coherence": self.universe_coherence,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "parent_span_id": self.parent_span_id,
            "success": self.success,
            "error": self.error,
        }
    
    def get_display_name(self) -> str:
        """Get human-readable display name with glyph."""
        glyph = EVENT_GLYPHS.get(self.event_type, "⚙️")
        name = self.event_type.value.split(".")[-1].replace("_", " ").title()
        
        # Add context for specific event types
        suffix = ""
        if self.beat_id:
            suffix = f" ({self.beat_id})"
        elif self.lead_universe:
            suffix = f" ({self.lead_universe})"
        elif self.emotional_tone:
            suffix = f" ({self.emotional_tone})"
        
        return f"{glyph} {name}{suffix}"


@dataclass
class TraceCorrelation:
    """Links traces across system boundaries."""
    
    root_trace_id: str
    child_trace_ids: List[str] = field(default_factory=list)
    story_id: str = ""
    session_id: str = ""
    
    # System hop sequence
    correlation_path: List[str] = field(default_factory=list)  # ["langgraph", "flowise", "langchain"]
    
    # Timing
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "root_trace_id": self.root_trace_id,
            "child_trace_ids": self.child_trace_ids,
            "story_id": self.story_id,
            "session_id": self.session_id,
            "correlation_path": self.correlation_path,
            "created_at": self.created_at,
        }
    
    def add_child(self, trace_id: str, system: str) -> None:
        """Add a child trace from a system."""
        self.child_trace_ids.append(trace_id)
        if system not in self.correlation_path:
            self.correlation_path.append(system)


# =============================================================================
# NARRATIVE METRICS
# =============================================================================

@dataclass
class NarrativeMetrics:
    """Extracted metrics from narrative traces."""
    
    # Story quality
    coherence_score: float = 0.5
    emotional_arc_strength: float = 0.5
    theme_clarity: float = 0.5
    dialogue_consistency: float = 0.5
    
    # Character metrics
    character_arc_completion: Dict[str, float] = field(default_factory=dict)
    relationship_depth: float = 0.5
    
    # Three-universe metrics
    engineer_alignment: float = 0.5
    ceremony_alignment: float = 0.5
    story_engine_alignment: float = 0.5
    cross_universe_coherence: float = 0.5
    
    # Process metrics
    beats_generated: int = 0
    enrichments_applied: int = 0
    gaps_remediated: int = 0
    routing_decisions: int = 0
    
    # Timing
    total_generation_time_ms: float = 0.0
    average_beat_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "coherence_score": self.coherence_score,
            "emotional_arc_strength": self.emotional_arc_strength,
            "theme_clarity": self.theme_clarity,
            "dialogue_consistency": self.dialogue_consistency,
            "character_arc_completion": self.character_arc_completion,
            "relationship_depth": self.relationship_depth,
            "engineer_alignment": self.engineer_alignment,
            "ceremony_alignment": self.ceremony_alignment,
            "story_engine_alignment": self.story_engine_alignment,
            "cross_universe_coherence": self.cross_universe_coherence,
            "beats_generated": self.beats_generated,
            "enrichments_applied": self.enrichments_applied,
            "gaps_remediated": self.gaps_remediated,
            "routing_decisions": self.routing_decisions,
            "total_generation_time_ms": self.total_generation_time_ms,
            "average_beat_time_ms": self.average_beat_time_ms,
        }
    
    def calculate_overall_quality(self) -> float:
        """Calculate overall narrative quality score."""
        return (
            self.coherence_score * 0.25 +
            self.emotional_arc_strength * 0.25 +
            self.theme_clarity * 0.20 +
            self.cross_universe_coherence * 0.15 +
            self.dialogue_consistency * 0.15
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "NarrativeEventType",
    "EVENT_GLYPHS",
    "NarrativeSpan",
    "TraceCorrelation",
    "NarrativeMetrics",
]
