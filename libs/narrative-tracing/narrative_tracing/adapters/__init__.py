"""
Narrative Tracing Adapters

Bridge adapters that wire narrative-tracing to the three target systems:
- LangGraph ThreeUniverseProcessor
- Miadi webhook handlers
- Storytelling beat generators

These adapters enable automatic trace logging when events flow through
the Narrative Intelligence Stack.
"""

from .langgraph_bridge import LangGraphBridge
from .miadi_integration import (
    MiadiIntegration,
    CorrelationContext,
    WebhookEvent,
    create_correlation_middleware,
    HEADER_TRACE_ID,
    HEADER_STORY_ID,
    HEADER_SESSION_ID,
    HEADER_PARENT_SPAN_ID,
    HEADER_BEAT_ID,
    HEADER_EPISODE_ID,
    ALL_CORRELATION_HEADERS,
)
from .storytelling_hooks import (
    StorytellingHooks,
    BeatTracer,
    BeatInfo,
    CharacterUpdate,
    ThemeUpdate,
)

__all__ = [
    # LangGraph
    "LangGraphBridge",
    # Miadi
    "MiadiIntegration",
    "CorrelationContext",
    "WebhookEvent",
    "create_correlation_middleware",
    "HEADER_TRACE_ID",
    "HEADER_STORY_ID",
    "HEADER_SESSION_ID",
    "HEADER_PARENT_SPAN_ID",
    "HEADER_BEAT_ID",
    "HEADER_EPISODE_ID",
    "ALL_CORRELATION_HEADERS",
    # Storytelling
    "StorytellingHooks",
    "BeatTracer",
    "BeatInfo",
    "CharacterUpdate",
    "ThemeUpdate",
]
