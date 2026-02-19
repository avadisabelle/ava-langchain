# langchain-narrative-tracing

Narrative-aware Langfuse tracing for the Narrative Intelligence Stack.

## Overview

This package extends LangChain's Langfuse integration with narrative-specific event types, semantic span naming, and cross-system trace correlation. It's designed to work with the Narrative Intelligence Toolkit and related systems.

## Features

- **Narrative Event Types**: Custom event types for beats, character arcs, themes, and three-universe analysis
- **Semantic Span Naming**: Spans named by narrative function (📝 Beat Created, not "run_llm")
- **Three-Universe Support**: Track Engineer, Ceremony, and Story Engine perspectives
- **Cross-System Correlation**: Trace IDs flow through LangGraph → Flowise → Langflow
- **Human-Readable Formatting**: Output traces in narrative-aware formats

## Installation

```bash
pip install langchain-narrative-tracing
```

Or for development:

```bash
cd libs/narrative-tracing
pip install -e ".[dev,langchain]"
```

## Quick Start

### Simple Handler Usage

```python
from narrative_tracing import NarrativeTracingHandler

# Create handler
handler = NarrativeTracingHandler(
    story_id="story_123",
    session_id="session_456"
)

# Use context manager for automatic start/end tracing
with handler.trace_story_generation():
    # Log beat creation
    handler.log_beat_creation(
        beat_id="beat_1",
        content="The protagonist discovers a hidden door...",
        sequence=1,
        narrative_function="inciting_incident",
        emotional_tone="mysterious"
    )
    
    # Log three-universe analysis
    handler.log_three_universe_analysis(
        event_id="evt_123",
        engineer_intent="feature_request",
        engineer_confidence=0.8,
        ceremony_intent="co_creation",
        ceremony_confidence=0.7,
        story_engine_intent="inciting_incident",
        story_engine_confidence=0.95,
        lead_universe="story_engine",
        coherence_score=0.88
    )
    
    # Log routing decision
    handler.log_routing_decision(
        decision_id="route_1",
        backend="flowise",
        flow="character_deepener",
        score=0.92,
        lead_universe="story_engine"
    )
```

### Cross-System Orchestration

```python
from narrative_tracing import NarrativeTraceOrchestrator

# Create orchestrator
orchestrator = NarrativeTraceOrchestrator()

# Create root trace
root = orchestrator.create_story_generation_root("story_123", "session_456")

# Create child spans
beat_span_id = orchestrator.create_beat_span(
    beat_id="beat_1",
    beat_content="The protagonist discovers...",
    beat_sequence=1,
    narrative_function="inciting_incident",
    root_trace=root,
    emotional_tone="mysterious"
)

# Get headers for outgoing HTTP calls
headers = orchestrator.inject_correlation_header({}, root.trace_id)

# Make call to Flowise with correlation headers
# response = flowise_client.call(flow_id, data, headers=headers)

# Finalize trace
completed = orchestrator.finalize_story_trace(
    root.trace_id,
    final_story="The complete story...",
    metrics=handler.get_metrics()
)
```

### Formatting Traces

```python
from narrative_tracing import NarrativeTraceFormatter

formatter = NarrativeTraceFormatter()

# Human-readable display
print(formatter.format_for_display(completed_trace))

# Timeline view
print(formatter.format_as_timeline(completed_trace))

# Markdown export
markdown = formatter.export_as_markdown(completed_trace)

# Get improvement suggestions
metrics = formatter.extract_story_metrics(completed_trace)
suggestions = formatter.generate_improvement_suggestions(metrics)
```

## Event Types

The package defines semantic event types for narrative operations:

### Beat Events
- `BEAT_CREATED` - New story beat generated
- `BEAT_ANALYZED` - Beat emotionally classified
- `BEAT_ENRICHED` - Beat improved by agent flow
- `BEAT_QUALITY_ASSESSED` - Quality score calculated

### Character Events
- `CHARACTER_ARC_ANALYZED` - Arc analysis performed
- `CHARACTER_ARC_UPDATED` - Arc position changed
- `CHARACTER_RELATIONSHIP_CHANGED` - K'é relationship updated

### Theme Events
- `THEME_DETECTED` - New theme identified
- `THEME_TENSION_IDENTIFIED` - Thematic tension found
- `THEME_STRENGTH_CHANGED` - Theme visibility adjusted

### Three-Universe Events
- `THREE_UNIVERSE_ANALYSIS` - All 3 perspectives computed
- `UNIVERSE_LEAD_DETERMINED` - Lead universe selected
- `UNIVERSE_COHERENCE_CALCULATED` - Cross-universe alignment

### Routing Events
- `INTENT_CLASSIFIED` - Query intent identified
- `ROUTING_DECISION` - Backend/flow selection recorded
- `FLOW_EXECUTED` - Agent flow ran
- `FLOW_RESULT` - Flow completed

### Checkpoint Events
- `NARRATIVE_CHECKPOINT` - State saved
- `NARRATIVE_RESTORED` - State restored
- `EPISODE_BOUNDARY` - New episode started

## Integration with Narrative Intelligence Stack

This package is the **unified observability layer** for the three-project Narrative Intelligence Stack:

1. **LangChain** (this fork) - Instruments and traces all narrative operations via Langfuse
2. **LangGraph Narrative Intelligence Toolkit** - Processes events through three universes (Engineer/Ceremony/Story Engine)
3. **Miadi Platform** - Consumes webhooks and generates episodes

### Three-Universe Bridge Adapters

The package provides specialized adapters for integrating each system:

#### LangGraph Bridge

Bridges the NarrativeTracingHandler to LangGraph's `ThreeUniverseProcessor`:

```python
from narrative_tracing import NarrativeTracingHandler
from narrative_tracing.adapters import LangGraphBridge

handler = NarrativeTracingHandler(story_id="story_123")
bridge = LangGraphBridge(handler)

# Option 1: Callback approach
callback = bridge.create_three_universe_callback()
callback(
    event_id="evt_001",
    event_content="Feature request: add three-universe processing",
    engineer_result={"intent": "feature_implementation", "confidence": 0.85},
    ceremony_result={"intent": "co_creation", "confidence": 0.75},
    story_engine_result={"intent": "rising_action", "confidence": 0.90},
    lead_universe="story_engine",
    coherence_score=0.82
)

# Option 2: Decorator approach
@bridge.trace_processor()
def process_event(event_id: str, content: str):
    # Your processing logic
    return {
        "engineer_result": {...},
        "ceremony_result": {...},
        "story_engine_result": {...},
        "lead_universe": "story_engine",
        "coherence_score": 0.82
    }

# Option 3: Context manager
with bridge.trace_analysis(event_id="evt_001") as ctx:
    # Your processing logic
    ctx.result = analysis_result
```

#### Miadi Integration

Enables cross-system trace correlation via HTTP headers:

```python
from narrative_tracing.adapters import MiadiIntegration

miadi = MiadiIntegration(handler)

# Log webhook received
miadi.log_webhook_received(
    event_id="webhook_001",
    event_type="github.issue",
    source="github",
    repository="org/narrative-intelligence",
    sender="developer_1"
)

# Inject correlation headers for outgoing requests
headers = miadi.inject_correlation_headers({})
# headers now contains X-Narrative-Trace-Id, X-Story-Id, etc.

# Extract correlation from incoming requests
context = miadi.extract_correlation(incoming_headers)
print(context.trace_id, context.story_id)

# Log episode boundaries
miadi.log_episode_boundary(
    episode_id="episode_001",
    beat_count=5,
    trigger="time_boundary"
)
```

#### Storytelling Hooks

Traces beat lifecycle in the Storytelling system:

```python
from narrative_tracing.adapters import StorytellingHooks

storytelling = StorytellingHooks(handler)

# Context manager for full beat lifecycle
with storytelling.trace_beat_lifecycle("beat_001") as tracer:
    tracer.log_content(
        content="The protagonist discovers...",
        sequence=1,
        narrative_function="inciting_incident",
        act=1
    )
    tracer.log_analysis(
        classification="mystery",
        confidence=0.92,
        detected_emotions=["curiosity", "anticipation"]
    )
    tracer.log_enrichment(
        enrichment_type="character_deepening",
        flows_used=["character_enricher"],
        quality_before=0.7,
        quality_after=0.88
    )
    tracer.log_lessons([
        "Trust is established through consistency",
        "Small moments build larger arcs"
    ])

# Track character arc updates
storytelling.log_character_arc_update(
    character_id="protagonist_01",
    character_name="Elena",
    arc_position_before=0.3,
    arc_position_after=0.45,
    growth_description="Recognizes own strength"
)

# Log act transitions
storytelling.log_act_transition(
    from_act=1,
    to_act=2,
    trigger_beat_id="beat_001"
)
```

### End-to-End Example

For a complete example showing all three adapters working together, see:
`examples/three_system_integration_example.py`

```bash
cd libs/narrative-tracing
python examples/three_system_integration_example.py
```

### Additional Integrations

- **ava-langflow Universal Router** - Correlation headers for routing decisions
- **ava-Flowise Agent Coordination** - Trace agent flow execution
- **Storytelling System** - Trace story generation lifecycle

## Environment Variables

```bash
# Langfuse Configuration
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"

# Session Configuration
export COAIAPY_SESSION_ID="your-session-id"
export COAIAPY_TRACE_ID="your-trace-id"

# Narrative Configuration
export NARRATIVE_STORY_ID="story_123"
```

## API Reference

### NarrativeTracingHandler

Main handler for logging narrative events to Langfuse.

```python
handler = NarrativeTracingHandler(
    story_id: str,              # Story identifier
    session_id: str,            # Session for grouping
    trace_id: str,              # Optional root trace ID
    enable_semantic_naming: bool,  # Use narrative-aware names
    correlation_header: str,    # Header name for correlation
)
```

Key methods:
- `log_beat_creation()` - Log new beat
- `log_beat_analysis()` - Log beat classification
- `log_beat_enrichment()` - Log beat improvement
- `log_three_universe_analysis()` - Log 3-universe processing
- `log_character_arc_update()` - Log character progression
- `log_routing_decision()` - Log routing choice
- `log_checkpoint()` - Log state save
- `trace_story_generation()` - Context manager for full trace

### NarrativeTraceOrchestrator

Coordinates traces across system boundaries.

```python
orchestrator = NarrativeTraceOrchestrator()
```

Key methods:
- `create_story_generation_root()` - Create root trace
- `create_beat_span()` - Create beat child span
- `create_analysis_span()` - Create analysis span
- `create_agent_flow_span()` - Create flow execution span
- `inject_correlation_header()` - Add trace ID to headers
- `extract_correlation_header()` - Read trace ID from headers
- `finalize_story_trace()` - Close trace with metrics

### NarrativeTraceFormatter

Formats traces for human understanding.

```python
formatter = NarrativeTraceFormatter()
```

Key methods:
- `format_for_display()` - Human-readable tree
- `format_as_timeline()` - Chronological view
- `format_as_arc_graph()` - Character arc visualization
- `export_as_markdown()` - Documentation format
- `extract_story_metrics()` - Pull metrics from trace
- `generate_improvement_suggestions()` - Quality recommendations

## License

MIT License
