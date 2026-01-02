"""
Narrative Trace Formatter

Formats narrative traces for human understanding, not just machine parsing.
Transforms generic spans into narrative-aware displays that tell the story
of how a story was made.

Instead of:
  - run_llm
  - get_value
  - vectorstore_query

Produces:
  📖 Story Generation (root)
    ├─ 📝 Beat 1: "The Discovery" (character_arc: 0→20, emotion: intrigue)
    │  ├─ 🔍 Emotional Analysis (detected: wonder, curiosity)
    │  ├─ 🚀 Agent Enrichment (routed to: dialogue_enhancer)
    │  └─ ✨ Enriched Result (character_arc: 20→35, improved resonance)
    ├─ 📝 Beat 2: "The Challenge" (character_arc: 35→60, emotion: tension)
    │  └─ ...
    └─ 📊 Final Metrics (coherence: 0.87, emotional_arc: 0.92)

Session ID: langchain-narrative-tracing
Created: 2025-12-31
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .event_types import (
    EVENT_GLYPHS,
    NarrativeEventType,
    NarrativeMetrics,
    NarrativeSpan,
)
from .orchestrator import CompletedTrace


# =============================================================================
# FORMATTED OUTPUT STRUCTURES
# =============================================================================

@dataclass
class FormattedSpan:
    """A span formatted for human display."""
    
    display_name: str
    details: List[str] = field(default_factory=list)
    children: List["FormattedSpan"] = field(default_factory=list)
    indent_level: int = 0
    
    def to_string(self, indent: int = 0) -> str:
        """Convert to formatted string."""
        prefix = "│  " * indent
        connector = "├─ " if indent > 0 else ""
        
        lines = [f"{prefix}{connector}{self.display_name}"]
        
        for detail in self.details:
            lines.append(f"{prefix}│  └─ {detail}")
        
        for i, child in enumerate(self.children):
            is_last = i == len(self.children) - 1
            child_prefix = "└─ " if is_last else "├─ "
            lines.append(child.to_string(indent + 1))
        
        return "\n".join(lines)


@dataclass
class StoryArcVisualization:
    """Visualization of story arc progression."""
    
    character_arcs: Dict[str, List[float]] = field(default_factory=dict)
    emotional_beats: List[str] = field(default_factory=list)
    theme_mentions: Dict[str, int] = field(default_factory=dict)
    
    def to_ascii_chart(self, character_id: str, width: int = 50) -> str:
        """Generate ASCII chart for character arc."""
        if character_id not in self.character_arcs:
            return f"No arc data for {character_id}"
        
        positions = self.character_arcs[character_id]
        if not positions:
            return "Empty arc"
        
        # Scale to width
        chart_height = 10
        lines = []
        
        for row in range(chart_height, -1, -1):
            line = ""
            threshold = row / chart_height
            for i, pos in enumerate(positions):
                if pos >= threshold:
                    line += "█"
                else:
                    line += "·"
            lines.append(f"{row/chart_height:.1f} │{line}")
        
        # X-axis
        lines.append("    └" + "─" * len(positions))
        lines.append("      " + "".join([str(i % 10) for i in range(len(positions))]))
        
        return "\n".join(lines)


# =============================================================================
# NARRATIVE TRACE FORMATTER
# =============================================================================

class NarrativeTraceFormatter:
    """
    Formats narrative traces for human understanding.
    
    Provides multiple output formats:
    - Display: Human-readable tree format
    - Timeline: Chronological beat sequence
    - Arc Graph: Character-centric view
    - Markdown: Documentation-ready format
    
    Example:
    ```python
    formatter = NarrativeTraceFormatter()
    
    # Format for display
    display = formatter.format_for_display(completed_trace)
    print(display)
    
    # Extract metrics
    metrics = formatter.extract_story_metrics(completed_trace)
    
    # Get improvement suggestions
    suggestions = formatter.generate_improvement_suggestions(metrics)
    ```
    """
    
    def __init__(self) -> None:
        """Initialize formatter."""
        pass
    
    # =========================================================================
    # DISPLAY FORMATTING
    # =========================================================================
    
    def format_for_display(self, trace: CompletedTrace) -> str:
        """
        Generate human-readable trace with narrative structure.
        
        Args:
            trace: Completed trace to format
        
        Returns:
            Formatted string representation
        """
        lines = []
        
        # Header
        lines.append(f"📖 Story Generation: {trace.story_id}")
        lines.append(f"   Session: {trace.session_id}")
        lines.append(f"   Duration: {trace.duration_ms:.0f}ms")
        lines.append("")
        
        # Group spans by beat
        beats: Dict[str, List[NarrativeSpan]] = {}
        other_spans: List[NarrativeSpan] = []
        
        for span in trace.spans:
            if span.beat_id:
                if span.beat_id not in beats:
                    beats[span.beat_id] = []
                beats[span.beat_id].append(span)
            else:
                other_spans.append(span)
        
        # Format beats
        for beat_id, beat_spans in beats.items():
            # Find the creation span
            creation_span = next(
                (s for s in beat_spans if s.event_type == NarrativeEventType.BEAT_CREATED),
                None
            )
            
            if creation_span:
                emotional_tone = creation_span.emotional_tone or "neutral"
                lines.append(f"├─ 📝 Beat: {beat_id} ({emotional_tone})")
                
                # Add child spans
                for span in beat_spans:
                    if span.span_id != creation_span.span_id:
                        glyph = EVENT_GLYPHS.get(span.event_type, "⚙️")
                        event_name = span.event_type.value.split(".")[-1].replace("_", " ").title()
                        lines.append(f"│  ├─ {glyph} {event_name}")
                        
                        # Add output details
                        if span.output_data:
                            for key, value in span.output_data.items():
                                if isinstance(value, (int, float, str, bool)):
                                    lines.append(f"│  │  └─ {key}: {value}")
        
        # Format other spans
        if other_spans:
            lines.append("│")
            for span in other_spans:
                glyph = EVENT_GLYPHS.get(span.event_type, "⚙️")
                event_name = span.event_type.value.split(".")[-1].replace("_", " ").title()
                context = ""
                if span.lead_universe:
                    context = f" (lead: {span.lead_universe})"
                lines.append(f"├─ {glyph} {event_name}{context}")
        
        # Final metrics
        if trace.metrics:
            lines.append("│")
            lines.append(f"└─ 📊 Final Metrics")
            lines.append(f"   ├─ coherence: {trace.metrics.coherence_score:.2f}")
            lines.append(f"   ├─ emotional_arc: {trace.metrics.emotional_arc_strength:.2f}")
            lines.append(f"   ├─ theme_clarity: {trace.metrics.theme_clarity:.2f}")
            lines.append(f"   ├─ beats_generated: {trace.metrics.beats_generated}")
            lines.append(f"   └─ overall_quality: {trace.metrics.calculate_overall_quality():.2f}")
        
        return "\n".join(lines)
    
    def format_as_timeline(self, trace: CompletedTrace) -> str:
        """
        Generate chronological beat sequence view.
        
        Args:
            trace: Completed trace to format
        
        Returns:
            Timeline formatted string
        """
        lines = []
        lines.append(f"📅 Timeline: {trace.story_id}")
        lines.append(f"   {trace.start_time} → {trace.end_time}")
        lines.append("")
        
        # Sort spans by start time
        sorted_spans = sorted(trace.spans, key=lambda s: s.start_time)
        
        for i, span in enumerate(sorted_spans):
            glyph = EVENT_GLYPHS.get(span.event_type, "⚙️")
            event_name = span.event_type.value.split(".")[-1].replace("_", " ").title()
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(span.start_time.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S.%f")[:-3]
            except (ValueError, AttributeError):
                time_str = "??:??:??"
            
            connector = "└─" if i == len(sorted_spans) - 1 else "├─"
            lines.append(f"{time_str} {connector} {glyph} {event_name}")
            
            # Add beat context
            if span.beat_id:
                lines.append(f"          │   beat: {span.beat_id}")
            if span.emotional_tone:
                lines.append(f"          │   emotion: {span.emotional_tone}")
            if span.lead_universe:
                lines.append(f"          │   universe: {span.lead_universe}")
        
        return "\n".join(lines)
    
    def format_as_arc_graph(self, trace: CompletedTrace) -> str:
        """
        Generate character-centric arc view.
        
        Args:
            trace: Completed trace to format
        
        Returns:
            Arc graph formatted string
        """
        lines = []
        lines.append(f"🎭 Character Arcs: {trace.story_id}")
        lines.append("")
        
        # Extract character arc data
        arc_data = self._extract_character_arcs(trace)
        
        if not arc_data.character_arcs:
            lines.append("No character arc data found")
            return "\n".join(lines)
        
        for character_id, positions in arc_data.character_arcs.items():
            lines.append(f"Character: {character_id}")
            lines.append(arc_data.to_ascii_chart(character_id, width=40))
            lines.append("")
        
        # Emotional beat summary
        if arc_data.emotional_beats:
            lines.append("Emotional Journey:")
            for i, emotion in enumerate(arc_data.emotional_beats):
                lines.append(f"  {i+1}. {emotion}")
        
        return "\n".join(lines)
    
    def export_as_markdown(self, trace: CompletedTrace) -> str:
        """
        Generate documentation-ready markdown format.
        
        Args:
            trace: Completed trace to format
        
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Title
        lines.append(f"# Story Generation Trace: {trace.story_id}")
        lines.append("")
        
        # Metadata
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Story ID**: {trace.story_id}")
        lines.append(f"- **Session ID**: {trace.session_id}")
        lines.append(f"- **Duration**: {trace.duration_ms:.0f}ms")
        lines.append(f"- **Beats Generated**: {trace.beat_count}")
        lines.append("")
        
        # Metrics
        if trace.metrics:
            lines.append("## Quality Metrics")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Coherence | {trace.metrics.coherence_score:.2f} |")
            lines.append(f"| Emotional Arc | {trace.metrics.emotional_arc_strength:.2f} |")
            lines.append(f"| Theme Clarity | {trace.metrics.theme_clarity:.2f} |")
            lines.append(f"| Cross-Universe Coherence | {trace.metrics.cross_universe_coherence:.2f} |")
            lines.append(f"| Overall Quality | {trace.metrics.calculate_overall_quality():.2f} |")
            lines.append("")
        
        # Beat breakdown
        lines.append("## Beat Breakdown")
        lines.append("")
        
        beat_spans = [s for s in trace.spans if s.event_type == NarrativeEventType.BEAT_CREATED]
        for span in beat_spans:
            lines.append(f"### Beat: {span.beat_id}")
            lines.append("")
            if span.emotional_tone:
                lines.append(f"- **Emotional Tone**: {span.emotional_tone}")
            if span.character_ids:
                lines.append(f"- **Characters**: {', '.join(span.character_ids)}")
            if span.lead_universe:
                lines.append(f"- **Lead Universe**: {span.lead_universe}")
            lines.append("")
        
        # Correlation path
        if trace.correlation and trace.correlation.correlation_path:
            lines.append("## System Correlation")
            lines.append("")
            lines.append(f"Path: {' → '.join(trace.correlation.correlation_path)}")
            lines.append("")
        
        # Story preview
        if trace.story_content:
            lines.append("## Story Preview")
            lines.append("")
            lines.append("```")
            preview = trace.story_content[:1000] + "..." if len(trace.story_content) > 1000 else trace.story_content
            lines.append(preview)
            lines.append("```")
        
        return "\n".join(lines)
    
    # =========================================================================
    # METRICS EXTRACTION
    # =========================================================================
    
    def extract_story_metrics(self, trace: CompletedTrace) -> NarrativeMetrics:
        """
        Extract narrative metrics from a completed trace.
        
        Args:
            trace: Completed trace to analyze
        
        Returns:
            NarrativeMetrics with extracted values
        """
        if trace.metrics:
            return trace.metrics
        
        # Calculate from spans
        metrics = NarrativeMetrics()
        
        # Count beats
        metrics.beats_generated = sum(
            1 for s in trace.spans
            if s.event_type == NarrativeEventType.BEAT_CREATED
        )
        
        # Count enrichments
        metrics.enrichments_applied = sum(
            1 for s in trace.spans
            if s.event_type == NarrativeEventType.BEAT_ENRICHED
        )
        
        # Count gaps
        metrics.gaps_remediated = sum(
            1 for s in trace.spans
            if s.event_type == NarrativeEventType.GAP_REMEDIATED
        )
        
        # Count routing decisions
        metrics.routing_decisions = sum(
            1 for s in trace.spans
            if s.event_type == NarrativeEventType.ROUTING_DECISION
        )
        
        # Calculate average coherence from three-universe analyses
        universe_spans = [
            s for s in trace.spans
            if s.event_type == NarrativeEventType.THREE_UNIVERSE_ANALYSIS
        ]
        if universe_spans:
            coherences = [
                s.output_data.get("coherence_score", 0.5)
                for s in universe_spans
                if s.output_data
            ]
            if coherences:
                metrics.cross_universe_coherence = sum(coherences) / len(coherences)
        
        # Timing
        metrics.total_generation_time_ms = trace.duration_ms
        if metrics.beats_generated > 0:
            metrics.average_beat_time_ms = trace.duration_ms / metrics.beats_generated
        
        return metrics
    
    def _extract_character_arcs(self, trace: CompletedTrace) -> StoryArcVisualization:
        """Extract character arc data from trace."""
        viz = StoryArcVisualization()
        
        # Find character arc update spans
        arc_spans = [
            s for s in trace.spans
            if s.event_type == NarrativeEventType.CHARACTER_ARC_UPDATED
        ]
        
        for span in arc_spans:
            if span.character_ids:
                char_id = span.character_ids[0]
                if char_id not in viz.character_arcs:
                    viz.character_arcs[char_id] = []
                
                # Extract arc position from output
                if span.output_data and "arc_position_after" in span.output_data:
                    viz.character_arcs[char_id].append(span.output_data["arc_position_after"])
        
        # Extract emotional beats
        beat_spans = [
            s for s in trace.spans
            if s.event_type == NarrativeEventType.BEAT_CREATED and s.emotional_tone
        ]
        viz.emotional_beats = [s.emotional_tone for s in beat_spans if s.emotional_tone]
        
        return viz
    
    # =========================================================================
    # IMPROVEMENT SUGGESTIONS
    # =========================================================================
    
    def generate_improvement_suggestions(
        self,
        metrics: NarrativeMetrics,
    ) -> List[str]:
        """
        Generate suggestions for narrative improvement based on metrics.
        
        Args:
            metrics: Narrative metrics to analyze
        
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Coherence suggestions
        if metrics.coherence_score < 0.6:
            suggestions.append(
                "🔍 Low coherence detected. Consider adding transition beats "
                "to improve flow between scenes."
            )
        
        # Emotional arc suggestions
        if metrics.emotional_arc_strength < 0.5:
            suggestions.append(
                "💓 Emotional arc is weak. Try adding beats with stronger "
                "emotional contrast or character reactions."
            )
        
        # Theme clarity suggestions
        if metrics.theme_clarity < 0.6:
            suggestions.append(
                "🎨 Themes are unclear. Consider reinforcing thematic elements "
                "through dialogue or symbolic actions."
            )
        
        # Cross-universe coherence suggestions
        if metrics.cross_universe_coherence < 0.5:
            suggestions.append(
                "🌌 Three-universe alignment is low. Review if Engineer, Ceremony, "
                "and Story Engine perspectives are all represented."
            )
        
        # Enrichment suggestions
        if metrics.enrichments_applied < metrics.beats_generated * 0.3:
            suggestions.append(
                "✨ Few beats were enriched. Consider running more beats through "
                "specialized flows for quality improvement."
            )
        
        # Character arc suggestions
        incomplete_arcs = [
            char_id for char_id, completion in metrics.character_arc_completion.items()
            if completion < 0.6
        ]
        if incomplete_arcs:
            suggestions.append(
                f"🎭 Characters with incomplete arcs: {', '.join(incomplete_arcs)}. "
                "Add beats that advance their personal journeys."
            )
        
        # Performance suggestions
        if metrics.average_beat_time_ms > 5000:
            suggestions.append(
                "⚡ Beat generation is slow. Consider optimizing prompts or "
                "using faster model variants for initial drafts."
            )
        
        # If everything looks good
        if not suggestions:
            suggestions.append(
                "✅ Narrative metrics look healthy! The story maintains good "
                "coherence, emotional arc, and thematic clarity."
            )
        
        return suggestions


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FormattedSpan",
    "StoryArcVisualization",
    "NarrativeTraceFormatter",
]
