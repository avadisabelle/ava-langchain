"""
LangGraph Bridge Adapter

Wires the LangGraph ThreeUniverseProcessor to narrative-tracing,
so every three-universe analysis automatically logs to Langfuse.

This bridge provides:
- Callback function for injection into ThreeUniverseProcessor
- Decorator for wrapping processor.process() calls
- Context manager for trace scoping

Usage:
```python
from narrative_tracing import NarrativeTracingHandler
from narrative_tracing.adapters import LangGraphBridge

# Create handler and bridge
handler = NarrativeTracingHandler(story_id="story_123")
bridge = LangGraphBridge(handler)

# Option 1: Use as callback
callback = bridge.create_three_universe_callback()
# ... call after processor.process() completes

# Option 2: Use as decorator
@bridge.trace_processor()
def process_event(event):
    return processor.process(event)

# Option 3: Use context manager
with bridge.trace_analysis("evt_123") as span_id:
    result = processor.process(event)
    bridge.log_analysis_result(result, span_id)
```

Session ID: langchain-narrative-tracing
Created: 2026-01-30
"""

from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional, Protocol, TypeVar

from ..handler import NarrativeTracingHandler


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class UniversePerspectiveProtocol(Protocol):
    """Protocol matching LangGraph's UniversePerspective."""
    
    universe: Any
    intent: str
    confidence: float
    suggested_flows: List[str]
    context: Dict[str, Any]


class ThreeUniverseAnalysisProtocol(Protocol):
    """Protocol matching LangGraph's ThreeUniverseAnalysis."""
    
    engineer: UniversePerspectiveProtocol
    ceremony: UniversePerspectiveProtocol
    story_engine: UniversePerspectiveProtocol
    lead_universe: Any
    coherence_score: float


@dataclass
class UniverseResult:
    """Simplified result from a single universe analysis."""
    
    intent: str
    confidence: float
    suggested_flows: List[str]
    context: Dict[str, Any]
    
    @classmethod
    def from_perspective(cls, perspective: UniversePerspectiveProtocol) -> "UniverseResult":
        """Create from a UniversePerspective object."""
        return cls(
            intent=perspective.intent,
            confidence=perspective.confidence,
            suggested_flows=list(perspective.suggested_flows),
            context=dict(perspective.context),
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniverseResult":
        """Create from dictionary."""
        return cls(
            intent=data.get("intent", "unknown"),
            confidence=data.get("confidence", 0.0),
            suggested_flows=data.get("suggested_flows", []),
            context=data.get("context", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for callback compatibility."""
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "suggested_flows": self.suggested_flows,
            "context": self.context,
        }


# =============================================================================
# LANGGRAPH BRIDGE
# =============================================================================

class LangGraphBridge:
    """
    Wire LangGraph three-universe processing to narrative tracing.
    
    This bridge enables automatic Langfuse trace logging whenever
    events are processed through the ThreeUniverseProcessor.
    
    Args:
        handler: NarrativeTracingHandler instance for logging
        auto_flush: Whether to flush traces after each analysis
    
    Example:
    ```python
    handler = NarrativeTracingHandler(story_id="story_123")
    bridge = LangGraphBridge(handler)
    
    # Get callback for manual injection
    callback = bridge.create_three_universe_callback()
    
    # After processing an event
    callback(
        event_id="evt_123",
        event_content="feat: add three-universe processing",
        engineer_result={"intent": "feature_implementation", "confidence": 0.8},
        ceremony_result={"intent": "co_creation", "confidence": 0.7},
        story_engine_result={"intent": "rising_action", "confidence": 0.85},
        lead_universe="story_engine",
        coherence_score=0.82
    )
    ```
    """
    
    VALID_UNIVERSES = {"engineer", "ceremony", "story_engine"}
    
    def __init__(
        self,
        handler: NarrativeTracingHandler,
        auto_flush: bool = False,
    ) -> None:
        """Initialize the bridge with a tracing handler."""
        self.handler = handler
        self.auto_flush = auto_flush
        self._analysis_count = 0
    
    # =========================================================================
    # CALLBACK APPROACH
    # =========================================================================
    
    def create_three_universe_callback(
        self,
        parent_span_id: Optional[str] = None,
    ) -> Callable[..., str]:
        """
        Create callback function for logging three-universe analysis.
        
        Returns a callback that accepts analysis results and logs them
        to Langfuse via the handler.
        
        Args:
            parent_span_id: Optional parent span for nesting
        
        Returns:
            Callback function that logs analysis and returns span_id
        """
        def log_universe_analysis(
            event_id: str,
            event_content: str,
            engineer_result: Dict[str, Any],
            ceremony_result: Dict[str, Any],
            story_engine_result: Dict[str, Any],
            lead_universe: str,
            coherence_score: float,
        ) -> str:
            """
            Log three-universe analysis to Langfuse.
            
            Called after three-universe analysis completes.
            
            Args:
                event_id: Unique identifier for the event
                event_content: Content of the event being analyzed
                engineer_result: Dict with intent, confidence from engineer analysis
                ceremony_result: Dict with intent, confidence from ceremony analysis
                story_engine_result: Dict with intent, confidence from story engine analysis
                lead_universe: Which universe leads (engineer|ceremony|story_engine)
                coherence_score: How well perspectives align (0.0-1.0)
            
            Returns:
                The span_id of the logged trace
            
            Raises:
                ValueError: If lead_universe is not valid or coherence_score out of range
            """
            # Validate inputs
            self._validate_coherence_score(coherence_score)
            self._validate_lead_universe(lead_universe)
            
            # Log the analysis
            span_id = self.handler.log_three_universe_analysis(
                event_id=event_id,
                engineer_intent=engineer_result.get("intent", "unknown"),
                engineer_confidence=engineer_result.get("confidence", 0.0),
                ceremony_intent=ceremony_result.get("intent", "unknown"),
                ceremony_confidence=ceremony_result.get("confidence", 0.0),
                story_engine_intent=story_engine_result.get("intent", "unknown"),
                story_engine_confidence=story_engine_result.get("confidence", 0.0),
                lead_universe=lead_universe,
                coherence_score=coherence_score,
                parent_span_id=parent_span_id,
            )
            
            self._analysis_count += 1
            
            if self.auto_flush:
                self.handler.flush()
            
            return span_id
        
        return log_universe_analysis
    
    # =========================================================================
    # ANALYSIS OBJECT APPROACH
    # =========================================================================
    
    def log_analysis(
        self,
        event_id: str,
        analysis: ThreeUniverseAnalysisProtocol,
        event_content: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log a ThreeUniverseAnalysis object directly.
        
        This method accepts the actual analysis object returned by
        ThreeUniverseProcessor.process() for maximum convenience.
        
        Args:
            event_id: Unique identifier for the event
            analysis: ThreeUniverseAnalysis from processor.process()
            event_content: Optional content for trace metadata
            parent_span_id: Optional parent span for nesting
        
        Returns:
            The span_id of the logged trace
        """
        # Extract lead universe value (handle enum or string)
        lead_value = analysis.lead_universe
        if hasattr(lead_value, "value"):
            lead_value = lead_value.value
        
        return self.handler.log_three_universe_analysis(
            event_id=event_id,
            engineer_intent=analysis.engineer.intent,
            engineer_confidence=analysis.engineer.confidence,
            ceremony_intent=analysis.ceremony.intent,
            ceremony_confidence=analysis.ceremony.confidence,
            story_engine_intent=analysis.story_engine.intent,
            story_engine_confidence=analysis.story_engine.confidence,
            lead_universe=lead_value,
            coherence_score=analysis.coherence_score,
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # DECORATOR APPROACH
    # =========================================================================
    
    def trace_processor(
        self,
        event_id_extractor: Optional[Callable[[Dict[str, Any]], str]] = None,
    ) -> Callable:
        """
        Decorator that automatically traces processor.process() calls.
        
        Wraps a function that takes an event and returns a ThreeUniverseAnalysis,
        automatically logging the result.
        
        Args:
            event_id_extractor: Function to extract event_id from event dict.
                               Defaults to using event.get("event_id") or generating one.
        
        Returns:
            Decorator function
        
        Example:
        ```python
        @bridge.trace_processor()
        def analyze_event(event: Dict) -> ThreeUniverseAnalysis:
            return processor.process(event)
        
        result = analyze_event(my_event)  # Automatically traced
        ```
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(event: Dict[str, Any], *args: Any, **kwargs: Any) -> Any:
                # Extract event_id
                if event_id_extractor:
                    event_id = event_id_extractor(event)
                else:
                    event_id = event.get("event_id") or f"evt_{self._analysis_count}"
                
                # Call the wrapped function
                result = func(event, *args, **kwargs)
                
                # Log if result looks like an analysis
                if hasattr(result, "lead_universe") and hasattr(result, "coherence_score"):
                    self.log_analysis(
                        event_id=event_id,
                        analysis=result,
                        event_content=event.get("content"),
                    )
                
                return result
            
            return wrapper
        return decorator
    
    # =========================================================================
    # CONTEXT MANAGER APPROACH
    # =========================================================================
    
    @contextmanager
    def trace_analysis(
        self,
        event_id: str,
    ) -> Generator[str, None, None]:
        """
        Context manager for tracing analysis with explicit result logging.
        
        Creates a parent span for the analysis. Use log_analysis_result()
        within the context to log the final result.
        
        Args:
            event_id: Unique identifier for the event
        
        Yields:
            Parent span_id for nesting child spans
        
        Example:
        ```python
        with bridge.trace_analysis("evt_123") as span_id:
            result = processor.process(event)
            bridge.log_analysis_result(result, span_id)
        ```
        """
        # Create a parent span for the analysis
        parent_span_id = self.handler.log_event(
            event_type=self.handler._metrics.__class__.__module__,  # Placeholder event
            input_data={"event_id": event_id, "status": "analyzing"},
            metadata={"bridge": "langgraph"},
        ) if hasattr(self.handler, "log_event") else None
        
        try:
            yield parent_span_id or event_id
        finally:
            if self.auto_flush:
                self.handler.flush()
    
    # =========================================================================
    # BEAT CREATION TRACKING
    # =========================================================================
    
    def log_beat_creation(
        self,
        beat_id: str,
        content: str,
        sequence: int,
        narrative_function: str,
        analysis: Optional[ThreeUniverseAnalysisProtocol] = None,
        emotional_tone: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        Log creation of a story beat from three-universe analysis.
        
        This is typically called after processor.create_beat_from_analysis().
        
        Args:
            beat_id: Unique identifier for the beat
            content: The beat content text
            sequence: Sequence number in the story
            narrative_function: Narrative function (inciting_incident, etc.)
            analysis: Optional ThreeUniverseAnalysis for context
            emotional_tone: Detected emotional tone
            parent_span_id: Optional parent span for nesting
        
        Returns:
            The span_id of the logged trace
        """
        # Determine source based on lead universe
        source = "three_universe_processor"
        if analysis:
            lead = analysis.lead_universe
            if hasattr(lead, "value"):
                lead = lead.value
            source = f"{lead}_led"
        
        return self.handler.log_beat_creation(
            beat_id=beat_id,
            content=content,
            sequence=sequence,
            narrative_function=narrative_function,
            source=source,
            emotional_tone=emotional_tone,
            parent_span_id=parent_span_id,
        )
    
    # =========================================================================
    # VALIDATION HELPERS
    # =========================================================================
    
    def _validate_coherence_score(self, score: float) -> None:
        """Validate coherence score is in range 0.0-1.0."""
        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"coherence_score must be between 0.0 and 1.0, got {score}"
            )
    
    def _validate_lead_universe(self, universe: str) -> None:
        """Validate lead universe is a valid value."""
        if universe not in self.VALID_UNIVERSES:
            raise ValueError(
                f"lead_universe must be one of {self.VALID_UNIVERSES}, got '{universe}'"
            )
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    @property
    def analysis_count(self) -> int:
        """Number of analyses logged through this bridge."""
        return self._analysis_count
    
    def reset_count(self) -> None:
        """Reset the analysis count."""
        self._analysis_count = 0


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LangGraphBridge",
    "UniverseResult",
]
