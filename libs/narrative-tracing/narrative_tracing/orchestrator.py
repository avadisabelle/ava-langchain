"""
Narrative Trace Orchestrator

Correlates traces across system boundaries in the Narrative Intelligence Stack:
- LangGraph → Flowise → Langflow → LangChain

The challenge: These systems run in different contexts and processes.
Solution: Unique trace IDs that flow through the entire system via headers.

Flow Example:
1. Story generation starts → create root trace with story_id + trace_id
2. Story produces beats → child spans with beat_id + trace_id
3. NCP analysis starts → receives trace_id, creates analysis spans
4. Gaps identified → sends trace_id to Flowise router
5. Flowise executes → receives trace_id, logs as sub-span
6. Result returns → trace_id used to correlate back
7. Final trace shows entire journey from generation → analysis → enrichment

Session ID: langchain-narrative-tracing
Created: 2025-12-31
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .event_types import NarrativeEventType, NarrativeMetrics, NarrativeSpan, TraceCorrelation

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None


# =============================================================================
# ROOT TRACE CLASS
# =============================================================================

@dataclass
class RootTrace:
    """Root trace for a story generation session."""
    
    trace_id: str
    story_id: str
    session_id: str
    
    # Langfuse trace object
    trace_object: Any = None
    
    # Child tracking
    child_span_ids: List[str] = field(default_factory=list)
    
    # Timing
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Correlation
    correlation: Optional[TraceCorrelation] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "story_id": self.story_id,
            "session_id": self.session_id,
            "child_span_ids": self.child_span_ids,
            "created_at": self.created_at,
        }


# =============================================================================
# COMPLETED TRACE CLASS
# =============================================================================

@dataclass
class CompletedTrace:
    """A completed trace with all spans and metrics."""
    
    trace_id: str
    story_id: str
    session_id: str
    
    # Spans
    spans: List[NarrativeSpan] = field(default_factory=list)
    
    # Timing
    start_time: str = ""
    end_time: str = ""
    duration_ms: float = 0.0
    
    # Metrics
    metrics: Optional[NarrativeMetrics] = None
    
    # Story content
    story_content: Optional[str] = None
    beat_count: int = 0
    
    # Correlation
    correlation: Optional[TraceCorrelation] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "story_id": self.story_id,
            "session_id": self.session_id,
            "spans": [s.to_dict() for s in self.spans],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "story_content": self.story_content,
            "beat_count": self.beat_count,
            "correlation": self.correlation.to_dict() if self.correlation else None,
        }


# =============================================================================
# NARRATIVE TRACE ORCHESTRATOR
# =============================================================================

class NarrativeTraceOrchestrator:
    """
    Orchestrates traces across the Narrative Intelligence Stack.
    
    Provides:
    - Root trace creation with story context
    - Child span creation with parent linking
    - Cross-system correlation via headers
    - Trace reconstruction for complete view
    - Metrics extraction from completed traces
    
    Example:
    ```python
    orchestrator = NarrativeTraceOrchestrator()
    
    # Create root trace for story generation
    root = orchestrator.create_story_generation_root("story_123", "session_456")
    
    # Create child spans
    beat_span_id = orchestrator.create_beat_span(beat, root)
    analysis_span_id = orchestrator.create_analysis_span("emotional", root.trace_id)
    
    # Inject headers for outgoing calls
    headers = orchestrator.inject_correlation_header({}, root.trace_id)
    response = flowise_client.call(flow_id, data, headers=headers)
    
    # Finalize and get completed trace
    completed = orchestrator.finalize_story_trace(root.trace_id, final_story, metrics)
    ```
    """
    
    # Header names for cross-system correlation
    TRACE_ID_HEADER = "X-Narrative-Trace-Id"
    STORY_ID_HEADER = "X-Story-Id"
    SESSION_ID_HEADER = "X-Session-Id"
    PARENT_SPAN_HEADER = "X-Parent-Span-Id"
    
    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
    ) -> None:
        """
        Initialize the trace orchestrator.
        
        Args:
            public_key: Langfuse public key (or env var)
            secret_key: Langfuse secret key (or env var)
            host: Langfuse host URL (or env var)
        """
        if not LANGFUSE_AVAILABLE:
            raise ImportError("Langfuse is required. Install with: pip install langfuse")
        
        self.langfuse = Langfuse(
            public_key=public_key or os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=secret_key or os.environ.get("LANGFUSE_SECRET_KEY"),
            host=host or os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        
        # Track active traces
        self.active_traces: Dict[str, RootTrace] = {}
        self.spans: Dict[str, NarrativeSpan] = {}
    
    # =========================================================================
    # ROOT TRACE CREATION
    # =========================================================================
    
    def create_story_generation_root(
        self,
        story_id: str,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RootTrace:
        """
        Create root span for entire story generation session.
        
        Args:
            story_id: Unique story identifier
            session_id: Optional session for grouping
            trace_id: Optional specific trace ID
            metadata: Additional metadata
        
        Returns:
            RootTrace with trace_id that flows through all components
        """
        trace_id = trace_id or str(uuid.uuid4())
        session_id = session_id or os.environ.get("COAIAPY_SESSION_ID", str(uuid.uuid4()))
        
        # Create Langfuse trace
        trace_object = self.langfuse.trace(
            id=trace_id,
            session_id=session_id,
            name=f"📖 Story Generation: {story_id}",
            metadata={
                "story_id": story_id,
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {}),
            },
        )
        
        # Create correlation tracker
        correlation = TraceCorrelation(
            root_trace_id=trace_id,
            story_id=story_id,
            session_id=session_id,
            correlation_path=["langchain"],
        )
        
        root = RootTrace(
            trace_id=trace_id,
            story_id=story_id,
            session_id=session_id,
            trace_object=trace_object,
            correlation=correlation,
        )
        
        self.active_traces[trace_id] = root
        return root
    
    # =========================================================================
    # CHILD SPAN CREATION
    # =========================================================================
    
    def create_beat_span(
        self,
        beat_id: str,
        beat_content: str,
        beat_sequence: int,
        narrative_function: str,
        root_trace: RootTrace,
        emotional_tone: Optional[str] = None,
        character_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Create child span for a story beat.
        
        Args:
            beat_id: Unique beat identifier
            beat_content: The beat text content
            beat_sequence: Sequence number in story
            narrative_function: Narrative function (inciting_incident, etc.)
            root_trace: Parent root trace
            emotional_tone: Detected emotional tone
            character_id: Primary character involved
            parent_span_id: Optional parent span
        
        Returns:
            Span ID for the beat span
        """
        span_id = str(uuid.uuid4())
        
        # Create display name
        name = f"📝 Beat {beat_sequence}: {beat_id}"
        if emotional_tone:
            name = f"{name} ({emotional_tone})"
        
        # Create Langfuse span
        span = root_trace.trace_object.span(
            id=span_id,
            name=name,
            input={
                "beat_id": beat_id,
                "sequence": beat_sequence,
                "narrative_function": narrative_function,
            },
            output={
                "content_preview": beat_content[:200] + "..." if len(beat_content) > 200 else beat_content,
            },
            metadata={
                "beat_id": beat_id,
                "emotional_tone": emotional_tone,
                "character_id": character_id,
            },
            parent_observation_id=parent_span_id,
        )
        
        # Track span
        narrative_span = NarrativeSpan(
            span_id=span_id,
            trace_id=root_trace.trace_id,
            event_type=NarrativeEventType.BEAT_CREATED,
            story_id=root_trace.story_id,
            session_id=root_trace.session_id,
            beat_id=beat_id,
            emotional_tone=emotional_tone,
            character_ids=[character_id] if character_id else [],
        )
        
        self.spans[span_id] = narrative_span
        root_trace.child_span_ids.append(span_id)
        
        return span_id
    
    def create_analysis_span(
        self,
        analysis_type: str,
        trace_id: str,
        beat_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create span for NCP analysis work.
        
        Args:
            analysis_type: Type of analysis (emotional, thematic, character_arc)
            trace_id: Root trace ID to link to
            beat_id: Optional beat being analyzed
            parent_span_id: Optional parent span
            input_data: Input data for analysis
        
        Returns:
            Span ID for the analysis span
        """
        if trace_id not in self.active_traces:
            raise ValueError(f"Unknown trace ID: {trace_id}")
        
        root_trace = self.active_traces[trace_id]
        span_id = str(uuid.uuid4())
        
        # Map analysis type to glyph
        glyph_map = {
            "emotional": "🔍",
            "thematic": "🎨",
            "character_arc": "🎭",
            "three_universe": "🌌",
        }
        glyph = glyph_map.get(analysis_type, "🔬")
        name = f"{glyph} {analysis_type.replace('_', ' ').title()} Analysis"
        
        if beat_id:
            name = f"{name} ({beat_id})"
        
        # Create Langfuse span
        span = root_trace.trace_object.span(
            id=span_id,
            name=name,
            input=input_data or {"analysis_type": analysis_type, "beat_id": beat_id},
            metadata={
                "analysis_type": analysis_type,
                "beat_id": beat_id,
            },
            parent_observation_id=parent_span_id,
        )
        
        # Track span
        narrative_span = NarrativeSpan(
            span_id=span_id,
            trace_id=trace_id,
            event_type=NarrativeEventType.BEAT_ANALYZED,
            story_id=root_trace.story_id,
            session_id=root_trace.session_id,
            beat_id=beat_id,
        )
        
        self.spans[span_id] = narrative_span
        root_trace.child_span_ids.append(span_id)
        
        return span_id
    
    def create_agent_flow_span(
        self,
        flow_id: str,
        backend: str,
        trace_id: str,
        intent: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create span for Flowise/Langflow flow execution.
        
        Args:
            flow_id: Flow identifier
            backend: Backend name (flowise, langflow)
            trace_id: Root trace ID to link to
            intent: Classified intent
            parent_span_id: Optional parent span
            input_data: Input data for flow
        
        Returns:
            Span ID for the flow span
        """
        if trace_id not in self.active_traces:
            raise ValueError(f"Unknown trace ID: {trace_id}")
        
        root_trace = self.active_traces[trace_id]
        span_id = str(uuid.uuid4())
        
        name = f"🚀 {backend.title()} Flow: {flow_id}"
        if intent:
            name = f"{name} (intent: {intent})"
        
        # Create Langfuse span
        span = root_trace.trace_object.span(
            id=span_id,
            name=name,
            input=input_data or {"flow_id": flow_id, "backend": backend},
            metadata={
                "flow_id": flow_id,
                "backend": backend,
                "intent": intent,
            },
            parent_observation_id=parent_span_id,
        )
        
        # Track span
        narrative_span = NarrativeSpan(
            span_id=span_id,
            trace_id=trace_id,
            event_type=NarrativeEventType.FLOW_EXECUTED,
            story_id=root_trace.story_id,
            session_id=root_trace.session_id,
        )
        
        self.spans[span_id] = narrative_span
        root_trace.child_span_ids.append(span_id)
        
        # Update correlation
        if root_trace.correlation and backend not in root_trace.correlation.correlation_path:
            root_trace.correlation.correlation_path.append(backend)
        
        return span_id
    
    def create_enrichment_span(
        self,
        beat_id: str,
        enrichment_type: str,
        trace_id: str,
        flows_used: List[str],
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Create span for beat enrichment.
        
        Args:
            beat_id: Beat being enriched
            enrichment_type: Type of enrichment
            trace_id: Root trace ID
            flows_used: List of flows used
            parent_span_id: Optional parent span
        
        Returns:
            Span ID for the enrichment span
        """
        if trace_id not in self.active_traces:
            raise ValueError(f"Unknown trace ID: {trace_id}")
        
        root_trace = self.active_traces[trace_id]
        span_id = str(uuid.uuid4())
        
        name = f"✨ Enrichment: {enrichment_type} ({beat_id})"
        
        # Create Langfuse span
        span = root_trace.trace_object.span(
            id=span_id,
            name=name,
            input={
                "beat_id": beat_id,
                "enrichment_type": enrichment_type,
                "flows_used": flows_used,
            },
            metadata={
                "beat_id": beat_id,
                "enrichment_type": enrichment_type,
            },
            parent_observation_id=parent_span_id,
        )
        
        # Track span
        narrative_span = NarrativeSpan(
            span_id=span_id,
            trace_id=trace_id,
            event_type=NarrativeEventType.BEAT_ENRICHED,
            story_id=root_trace.story_id,
            session_id=root_trace.session_id,
            beat_id=beat_id,
        )
        
        self.spans[span_id] = narrative_span
        root_trace.child_span_ids.append(span_id)
        
        return span_id
    
    # =========================================================================
    # SPAN UPDATES
    # =========================================================================
    
    def update_span_output(
        self,
        span_id: str,
        output_data: Dict[str, Any],
    ) -> None:
        """Update a span with output data."""
        if span_id in self.spans:
            self.spans[span_id].output_data = output_data
            self.spans[span_id].end_time = datetime.utcnow().isoformat()
    
    def mark_span_error(
        self,
        span_id: str,
        error: str,
    ) -> None:
        """Mark a span as errored."""
        if span_id in self.spans:
            self.spans[span_id].success = False
            self.spans[span_id].error = error
            self.spans[span_id].end_time = datetime.utcnow().isoformat()
    
    # =========================================================================
    # CROSS-SYSTEM CORRELATION
    # =========================================================================
    
    def inject_correlation_header(
        self,
        headers: Dict[str, str],
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Inject correlation headers for outgoing HTTP calls.
        
        Args:
            headers: Existing headers dict
            trace_id: Trace ID to inject
            parent_span_id: Optional parent span ID
        
        Returns:
            Headers dict with correlation info added
        """
        if trace_id and trace_id in self.active_traces:
            root = self.active_traces[trace_id]
            headers[self.TRACE_ID_HEADER] = trace_id
            headers[self.STORY_ID_HEADER] = root.story_id
            headers[self.SESSION_ID_HEADER] = root.session_id
            if parent_span_id:
                headers[self.PARENT_SPAN_HEADER] = parent_span_id
        
        return headers
    
    def extract_correlation_header(
        self,
        headers: Dict[str, str],
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extract correlation info from incoming request headers.
        
        Args:
            headers: Request headers
        
        Returns:
            Tuple of (trace_id, story_id, session_id, parent_span_id)
        """
        return (
            headers.get(self.TRACE_ID_HEADER),
            headers.get(self.STORY_ID_HEADER),
            headers.get(self.SESSION_ID_HEADER),
            headers.get(self.PARENT_SPAN_HEADER),
        )
    
    def link_external_trace(
        self,
        trace_id: str,
        external_trace_id: str,
        external_system: str,
    ) -> None:
        """
        Link an external trace to our root trace.
        
        Args:
            trace_id: Our root trace ID
            external_trace_id: External system's trace ID
            external_system: Name of external system
        """
        if trace_id in self.active_traces:
            root = self.active_traces[trace_id]
            if root.correlation:
                root.correlation.add_child(external_trace_id, external_system)
    
    # =========================================================================
    # TRACE FINALIZATION
    # =========================================================================
    
    def finalize_story_trace(
        self,
        trace_id: str,
        final_story: Optional[str] = None,
        metrics: Optional[NarrativeMetrics] = None,
    ) -> CompletedTrace:
        """
        Close root trace with final story and quality metrics.
        
        Args:
            trace_id: Root trace ID
            final_story: Final generated story content
            metrics: Narrative quality metrics
        
        Returns:
            CompletedTrace with all spans and metrics
        """
        if trace_id not in self.active_traces:
            raise ValueError(f"Unknown trace ID: {trace_id}")
        
        root = self.active_traces[trace_id]
        end_time = datetime.utcnow().isoformat()
        
        # Calculate duration
        start_dt = datetime.fromisoformat(root.created_at.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration_ms = (end_dt - start_dt).total_seconds() * 1000
        
        # Gather all spans
        spans = [self.spans[sid] for sid in root.child_span_ids if sid in self.spans]
        
        # Count beats
        beat_count = sum(
            1 for s in spans
            if s.event_type == NarrativeEventType.BEAT_CREATED
        )
        
        # Create completed trace
        completed = CompletedTrace(
            trace_id=trace_id,
            story_id=root.story_id,
            session_id=root.session_id,
            spans=spans,
            start_time=root.created_at,
            end_time=end_time,
            duration_ms=duration_ms,
            metrics=metrics,
            story_content=final_story,
            beat_count=beat_count,
            correlation=root.correlation,
        )
        
        # Update Langfuse trace
        if root.trace_object:
            root.trace_object.update(
                output={
                    "final_story_preview": final_story[:500] + "..." if final_story and len(final_story) > 500 else final_story,
                    "beat_count": beat_count,
                    "duration_ms": duration_ms,
                    "metrics": metrics.to_dict() if metrics else None,
                },
            )
        
        # Clean up
        del self.active_traces[trace_id]
        for sid in root.child_span_ids:
            if sid in self.spans:
                del self.spans[sid]
        
        # Flush to Langfuse
        self.langfuse.flush()
        
        return completed
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    def flush(self) -> None:
        """Flush pending traces to Langfuse."""
        self.langfuse.flush()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RootTrace",
    "CompletedTrace",
    "NarrativeTraceOrchestrator",
]
