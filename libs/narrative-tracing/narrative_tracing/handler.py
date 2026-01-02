"""
Narrative Langfuse Handler

Extends the CoaiapyLangfuseCallbackHandler with narrative-specific event types
and semantic span naming. This handler understands narrative concepts and creates
traces that tell the story of how a story was made.

Key Features:
- Custom narrative event logging
- Semantic span naming (📖 Beat Created, not "run_llm")
- Three-universe perspective tracking
- Character arc and theme span creation
- Cross-system correlation support

Integration:
- Extends CoaiapyLangfuseCallbackHandler from langchain_core
- Integrates with LangGraph unified_state_bridge.py types
- Supports Flowise/Langflow flow tracing via correlation headers

Session ID: langchain-narrative-tracing
Created: 2025-12-31
"""

import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Union

from .event_types import (
    EVENT_GLYPHS,
    NarrativeEventType,
    NarrativeMetrics,
    NarrativeSpan,
    TraceCorrelation,
)

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseCallbackHandler = object


class NarrativeTracingHandler(BaseCallbackHandler if LANGCHAIN_AVAILABLE else object):
    """
    Langfuse callback handler with narrative awareness.
    
    This handler extends standard LangChain tracing with narrative-specific
    event types, semantic naming, and three-universe perspective tracking.
    
    Example Usage:
    ```python
    from narrative_tracing import NarrativeTracingHandler
    
    handler = NarrativeTracingHandler(
        story_id="story_123",
        session_id="session_456"
    )
    
    # Log narrative events
    handler.log_beat_creation(beat, source="generator")
    handler.log_three_universe_analysis(analysis)
    handler.log_routing_decision(decision)
    
    # Use as LangChain callback
    llm.invoke(prompt, config={"callbacks": [handler]})
    ```
    
    Args:
        story_id: Current story being traced
        session_id: Session ID for grouping traces
        trace_id: Optional root trace ID
        enable_semantic_naming: Use narrative-aware span names (default: True)
        correlation_header: Header name for cross-system trace IDs
        public_key: Langfuse public key (or LANGFUSE_PUBLIC_KEY env var)
        secret_key: Langfuse secret key (or LANGFUSE_SECRET_KEY env var)
        host: Langfuse host URL (or LANGFUSE_HOST env var)
    """
    
    def __init__(
        self,
        story_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        enable_semantic_naming: bool = True,
        correlation_header: str = "X-Narrative-Trace-Id",
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        if LANGCHAIN_AVAILABLE:
            super().__init__(**kwargs)
        
        if not LANGFUSE_AVAILABLE:
            raise ImportError(
                "Langfuse is not installed. Install it with: pip install langfuse"
            )
        
        # Story context
        self.story_id = story_id or os.environ.get("NARRATIVE_STORY_ID", "unknown")
        self.session_id = session_id or os.environ.get("COAIAPY_SESSION_ID")
        self.root_trace_id = trace_id or os.environ.get("COAIAPY_TRACE_ID")
        
        # Configuration
        self.enable_semantic_naming = enable_semantic_naming
        self.correlation_header = correlation_header
        
        # Initialize Langfuse client
        self.langfuse = Langfuse(
            public_key=public_key or os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=secret_key or os.environ.get("LANGFUSE_SECRET_KEY"),
            host=host or os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        
        # Tracking maps
        self.trace_objects: Dict[str, Any] = {}
        self.span_objects: Dict[str, Any] = {}
        self.run_to_span_id: Dict[str, str] = {}
        self.correlation: Optional[TraceCorrelation] = None
        
        # Metrics accumulator
        self._metrics = NarrativeMetrics()
        
        # Initialize root trace if story_id provided
        if self.story_id and self.story_id != "unknown":
            self._ensure_root_trace()
    
    # =========================================================================
    # ROOT TRACE MANAGEMENT
    # =========================================================================
    
    def _ensure_root_trace(self) -> str:
        """Ensure root trace exists and return its ID."""
        if self.root_trace_id and self.root_trace_id in self.trace_objects:
            return self.root_trace_id
        
        trace_id = self.root_trace_id or str(uuid.uuid4())
        self.root_trace_id = trace_id
        
        if trace_id not in self.trace_objects:
            trace = self.langfuse.trace(
                id=trace_id,
                session_id=self.session_id,
                name=f"📖 Story Generation: {self.story_id}",
                metadata={
                    "story_id": self.story_id,
                    "session_id": self.session_id,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            self.trace_objects[trace_id] = trace
            
            # Initialize correlation
            self.correlation = TraceCorrelation(
                root_trace_id=trace_id,
                story_id=self.story_id,
                session_id=self.session_id or "",
                correlation_path=["langchain"],
            )
        
        return trace_id
    
    def get_correlation_header(self) -> Dict[str, str]:
        """Get headers for cross-system correlation."""
        return {
            self.correlation_header: self._ensure_root_trace(),
            "X-Story-Id": self.story_id,
            "X-Session-Id": self.session_id or "",
        }
    
    def receive_correlation_header(self, headers: Dict[str, str]) -> None:
        """Receive correlation from incoming request."""
        if self.correlation_header in headers:
            incoming_trace_id = headers[self.correlation_header]
            if self.correlation:
                self.correlation.add_child(incoming_trace_id, "external")
    
    # =========================================================================
    # NARRATIVE EVENT LOGGING
    # =========================================================================
    
    def log_event(
        self,
        event_type: NarrativeEventType,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None,
        beat_id: Optional[str] = None,
        character_ids: Optional[List[str]] = None,
        emotional_tone: Optional[str] = None,
        lead_universe: Optional[str] = None,
    ) -> str:
        """
        Log a narrative event to Langfuse.
        
        Args:
            event_type: The type of narrative event
            input_data: Input data for the operation
            output_data: Output/result data
            metadata: Additional metadata
            parent_span_id: Parent span for nesting
            beat_id: Associated story beat ID
            character_ids: Characters involved
            emotional_tone: Detected emotional tone
            lead_universe: Which universe led (engineer/ceremony/story_engine)
        
        Returns:
            The span ID for the logged event
        """
        trace_id = self._ensure_root_trace()
        trace = self.trace_objects[trace_id]
        
        span_id = str(uuid.uuid4())
        glyph = EVENT_GLYPHS.get(event_type, "⚙️")
        name = f"{glyph} {event_type.value.split('.')[-1].replace('_', ' ').title()}"
        
        # Add context to name
        if beat_id:
            name = f"{name} ({beat_id})"
        elif lead_universe:
            name = f"{name} ({lead_universe})"
        
        # Create span
        span = trace.span(
            id=span_id,
            name=name,
            input=input_data or {},
            output=output_data,
            metadata={
                "event_type": event_type.value,
                "story_id": self.story_id,
                "beat_id": beat_id,
                "character_ids": character_ids or [],
                "emotional_tone": emotional_tone,
                "lead_universe": lead_universe,
                **(metadata or {}),
            },
            parent_observation_id=parent_span_id,
        )
        
        self.span_objects[span_id] = span
        return span_id
    
    # =========================================================================
    # BEAT EVENTS
    # =========================================================================
    
    def log_beat_creation(
        self,
        beat_id: str,
        content: str,
        sequence: int,
        narrative_function: str,
        source: str = "generator",
        character_id: Optional[str] = None,
        emotional_tone: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log creation of a new story beat."""
        self._metrics.beats_generated += 1
        
        return self.log_event(
            event_type=NarrativeEventType.BEAT_CREATED,
            input_data={
                "sequence": sequence,
                "narrative_function": narrative_function,
                "source": source,
            },
            output_data={
                "beat_id": beat_id,
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
            },
            beat_id=beat_id,
            character_ids=[character_id] if character_id else None,
            emotional_tone=emotional_tone,
            parent_span_id=parent_span_id,
        )
    
    def log_beat_analysis(
        self,
        beat_id: str,
        analysis_type: str,
        classification: str,
        confidence: float,
        detected_emotions: Optional[List[str]] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log emotional/thematic analysis of a beat."""
        return self.log_event(
            event_type=NarrativeEventType.BEAT_ANALYZED,
            input_data={
                "beat_id": beat_id,
                "analysis_type": analysis_type,
            },
            output_data={
                "classification": classification,
                "confidence": confidence,
                "detected_emotions": detected_emotions or [],
            },
            beat_id=beat_id,
            emotional_tone=classification,
            parent_span_id=parent_span_id,
        )
    
    def log_beat_enrichment(
        self,
        beat_id: str,
        enrichment_type: str,
        flows_used: List[str],
        quality_before: float,
        quality_after: float,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log enrichment of a beat by agent flows."""
        self._metrics.enrichments_applied += 1
        
        return self.log_event(
            event_type=NarrativeEventType.BEAT_ENRICHED,
            input_data={
                "beat_id": beat_id,
                "enrichment_type": enrichment_type,
                "flows_used": flows_used,
                "quality_before": quality_before,
            },
            output_data={
                "quality_after": quality_after,
                "improvement": quality_after - quality_before,
            },
            beat_id=beat_id,
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # THREE-UNIVERSE EVENTS
    # =========================================================================
    
    def log_three_universe_analysis(
        self,
        event_id: str,
        engineer_intent: str,
        engineer_confidence: float,
        ceremony_intent: str,
        ceremony_confidence: float,
        story_engine_intent: str,
        story_engine_confidence: float,
        lead_universe: str,
        coherence_score: float,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log three-universe analysis of an event."""
        # Update metrics
        self._metrics.engineer_alignment = (
            self._metrics.engineer_alignment * 0.9 + engineer_confidence * 0.1
        )
        self._metrics.ceremony_alignment = (
            self._metrics.ceremony_alignment * 0.9 + ceremony_confidence * 0.1
        )
        self._metrics.story_engine_alignment = (
            self._metrics.story_engine_alignment * 0.9 + story_engine_confidence * 0.1
        )
        self._metrics.cross_universe_coherence = (
            self._metrics.cross_universe_coherence * 0.9 + coherence_score * 0.1
        )
        
        return self.log_event(
            event_type=NarrativeEventType.THREE_UNIVERSE_ANALYSIS,
            input_data={
                "event_id": event_id,
            },
            output_data={
                "engineer": {"intent": engineer_intent, "confidence": engineer_confidence},
                "ceremony": {"intent": ceremony_intent, "confidence": ceremony_confidence},
                "story_engine": {"intent": story_engine_intent, "confidence": story_engine_confidence},
                "lead_universe": lead_universe,
                "coherence_score": coherence_score,
            },
            lead_universe=lead_universe,
            metadata={"coherence_score": coherence_score},
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # CHARACTER ARC EVENTS
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
        """Log character arc progression."""
        self._metrics.character_arc_completion[character_id] = arc_position_after
        
        return self.log_event(
            event_type=NarrativeEventType.CHARACTER_ARC_UPDATED,
            input_data={
                "character_id": character_id,
                "character_name": character_name,
                "arc_position_before": arc_position_before,
            },
            output_data={
                "arc_position_after": arc_position_after,
                "growth": arc_position_after - arc_position_before,
                "growth_description": growth_description,
            },
            beat_id=beat_id,
            character_ids=[character_id],
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # ROUTING EVENTS
    # =========================================================================
    
    def log_routing_decision(
        self,
        decision_id: str,
        backend: str,
        flow: str,
        score: float,
        method: str = "narrative",
        lead_universe: Optional[str] = None,
        narrative_act: Optional[int] = None,
        narrative_phase: Optional[str] = None,
        success: bool = True,
        latency_ms: float = 0.0,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log a routing decision to a backend/flow."""
        self._metrics.routing_decisions += 1
        
        return self.log_event(
            event_type=NarrativeEventType.ROUTING_DECISION,
            input_data={
                "decision_id": decision_id,
                "method": method,
                "lead_universe": lead_universe,
                "narrative_position": {
                    "act": narrative_act,
                    "phase": narrative_phase,
                },
            },
            output_data={
                "backend": backend,
                "flow": flow,
                "score": score,
                "success": success,
                "latency_ms": latency_ms,
            },
            lead_universe=lead_universe,
            metadata={
                "backend": backend,
                "flow": flow,
            },
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # CHECKPOINT EVENTS
    # =========================================================================
    
    def log_checkpoint(
        self,
        checkpoint_id: str,
        story_id: str,
        beat_count: int,
        narrative_act: int,
        narrative_phase: str,
        overall_coherence: float,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log a narrative state checkpoint."""
        return self.log_event(
            event_type=NarrativeEventType.NARRATIVE_CHECKPOINT,
            input_data={
                "story_id": story_id,
            },
            output_data={
                "checkpoint_id": checkpoint_id,
                "beat_count": beat_count,
                "narrative_position": {
                    "act": narrative_act,
                    "phase": narrative_phase,
                },
                "overall_coherence": overall_coherence,
            },
            metadata={
                "checkpoint_id": checkpoint_id,
            },
            parent_span_id=parent_span_id,
        )
    
    def log_episode_boundary(
        self,
        episode_id: str,
        beat_count: int,
        reason: str = "beat_threshold",
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log an episode boundary (new episode starting)."""
        return self.log_event(
            event_type=NarrativeEventType.EPISODE_BOUNDARY,
            input_data={
                "reason": reason,
                "beat_count": beat_count,
            },
            output_data={
                "episode_id": episode_id,
            },
            metadata={
                "episode_id": episode_id,
            },
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # GAP EVENTS
    # =========================================================================
    
    def log_gap_identified(
        self,
        gap_type: str,
        description: str,
        severity: float,
        beat_id: Optional[str] = None,
        suggested_remediation: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log identification of a narrative gap."""
        return self.log_event(
            event_type=NarrativeEventType.GAP_IDENTIFIED,
            input_data={
                "beat_id": beat_id,
            },
            output_data={
                "gap_type": gap_type,
                "description": description,
                "severity": severity,
                "suggested_remediation": suggested_remediation,
            },
            beat_id=beat_id,
            parent_span_id=parent_span_id,
        )
    
    def log_gap_remediated(
        self,
        gap_type: str,
        remediation_method: str,
        flows_used: List[str],
        success: bool = True,
        beat_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """Log remediation of a narrative gap."""
        if success:
            self._metrics.gaps_remediated += 1
        
        return self.log_event(
            event_type=NarrativeEventType.GAP_REMEDIATED,
            input_data={
                "gap_type": gap_type,
                "remediation_method": remediation_method,
            },
            output_data={
                "flows_used": flows_used,
                "success": success,
            },
            beat_id=beat_id,
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # STORY LIFECYCLE EVENTS
    # =========================================================================
    
    @contextmanager
    def trace_story_generation(
        self,
        story_id: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Context manager for tracing entire story generation.
        
        Usage:
        ```python
        with handler.trace_story_generation("story_123") as trace_id:
            # Generate story...
            handler.log_beat_creation(...)
        # Automatically logs completion and metrics
        ```
        """
        if story_id:
            self.story_id = story_id
        
        start_time = datetime.utcnow()
        trace_id = self._ensure_root_trace()
        
        # Log start
        start_span_id = self.log_event(
            event_type=NarrativeEventType.STORY_GENERATION_START,
            input_data={"story_id": self.story_id},
        )
        
        try:
            yield trace_id
        finally:
            # Calculate timing
            end_time = datetime.utcnow()
            total_ms = (end_time - start_time).total_seconds() * 1000
            self._metrics.total_generation_time_ms = total_ms
            if self._metrics.beats_generated > 0:
                self._metrics.average_beat_time_ms = total_ms / self._metrics.beats_generated
            
            # Log end with metrics
            self.log_event(
                event_type=NarrativeEventType.STORY_GENERATION_END,
                input_data={"story_id": self.story_id},
                output_data={
                    "duration_ms": total_ms,
                    "beats_generated": self._metrics.beats_generated,
                },
                parent_span_id=start_span_id,
            )
            
            # Log final metrics
            self.log_event(
                event_type=NarrativeEventType.STORY_QUALITY_METRICS,
                output_data=self._metrics.to_dict(),
            )
    
    # =========================================================================
    # METRICS ACCESS
    # =========================================================================
    
    def get_metrics(self) -> NarrativeMetrics:
        """Get accumulated narrative metrics."""
        return self._metrics
    
    def reset_metrics(self) -> None:
        """Reset metrics accumulator."""
        self._metrics = NarrativeMetrics()
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    def flush(self) -> None:
        """Flush pending traces to Langfuse."""
        if hasattr(self, "langfuse"):
            self.langfuse.flush()
    
    def __del__(self) -> None:
        """Flush on destruction."""
        try:
            self.flush()
        except Exception:
            pass


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "NarrativeTracingHandler",
]
