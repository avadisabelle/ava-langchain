"""
Narrative Tracing for LangChain

A Langfuse-based tracing integration for the Narrative Intelligence Stack.
Provides narrative-aware observability across LangGraph, Flowise, Langflow,
and the Storytelling system.

Key Components:
- NarrativeTracingHandler: Langfuse callback handler with narrative events
- NarrativeTraceOrchestrator: Cross-system trace correlation
- NarrativeTraceFormatter: Human-readable trace formatting
- Event Types: Semantic event types for narrative operations

Integration with Narrative Intelligence Stack:
- Traces align with unified_state_bridge.py types from LangGraph
- Supports three-universe (Engineer/Ceremony/Story Engine) tracking
- Cross-system correlation via HTTP headers
- Human-readable trace formatting

Example Usage:
```python
from narrative_tracing import (
    NarrativeTracingHandler,
    NarrativeTraceOrchestrator,
    NarrativeTraceFormatter,
    NarrativeEventType,
)

# Simple handler usage
handler = NarrativeTracingHandler(story_id="story_123")

with handler.trace_story_generation():
    handler.log_beat_creation(beat_id, content, sequence, "rising_action")
    handler.log_three_universe_analysis(...)
    handler.log_routing_decision(...)

# Orchestrator for cross-system correlation
orchestrator = NarrativeTraceOrchestrator()
root = orchestrator.create_story_generation_root("story_123", "session_456")

# Inject headers for outgoing calls to Flowise/Langflow
headers = orchestrator.inject_correlation_header({}, root.trace_id)

# Format completed traces
formatter = NarrativeTraceFormatter()
print(formatter.format_for_display(completed_trace))
```

Session ID: langchain-narrative-tracing
Created: 2025-12-31
"""

from .event_types import (
    EVENT_GLYPHS,
    NarrativeEventType,
    NarrativeMetrics,
    NarrativeSpan,
    TraceCorrelation,
)
from .handler import NarrativeTracingHandler
from .orchestrator import (
    CompletedTrace,
    NarrativeTraceOrchestrator,
    RootTrace,
)
from .formatter import (
    FormattedSpan,
    NarrativeTraceFormatter,
    StoryArcVisualization,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    
    # Event Types
    "NarrativeEventType",
    "EVENT_GLYPHS",
    "NarrativeSpan",
    "TraceCorrelation",
    "NarrativeMetrics",
    
    # Handler
    "NarrativeTracingHandler",
    
    # Orchestrator
    "NarrativeTraceOrchestrator",
    "RootTrace",
    "CompletedTrace",
    
    # Formatter
    "NarrativeTraceFormatter",
    "FormattedSpan",
    "StoryArcVisualization",
]
