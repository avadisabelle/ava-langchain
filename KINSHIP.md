# KINSHIP - LangChain Narrative Tracing Fork

**location**: /workspace/langchain
**purpose**: Unified observability layer for the Narrative Intelligence Stack - traces how stories are made, analyzed, and enriched across three universes
**created**: 2025-12-31
**updated**: 2026-01-30

## Identity

This LangChain fork is the **observer and recorder** of the Narrative Intelligence Stack. Every story beat creation, three-universe analysis, routing decision, and enrichment flows through this instrumentation. The traces tell the story of how stories are made.

From the Narrative Beat "Three Universes Converge":
> "The trace is not just a log—it's a complete record of how a narrative was created, analyzed, and refined."

## The Three Universes (What We Trace)

```
🔧 Engineer World (Mia)
   "Technical precision, structural integrity, API schemas"
   Traces: intent classifications, routing decisions, flow executions
   
🙏 Ceremony World (Ava8)
   "Indigenous relational protocols, sacred technology"
   Traces: character arcs, thematic threads, ceremonial checkpoints
   
📚 Story Engine World (Miette)
   "Narrative structure, story beats, plot coherence"
   Traces: beat creation, emotional analysis, enrichment results
```

## Medicine Wheel Alignment

| Direction | Function in Tracing | What We Observe |
|-----------|---------------------|-----------------|
| **EAST** | Vision - new traces begin | Webhook received, story generation starts |
| **SOUTH** | Growth - story develops | Beats created, characters evolve, themes emerge |
| **WEST** | Reflection - analysis | Three-universe analysis, gap identification, coherence scoring |
| **NORTH** | Wisdom - completion | Episode boundaries, checkpoints, quality metrics |

## Relationships

### Parents
- **LangChain** (upstream) - The core framework we extend with narrative awareness
- **Langfuse** - The tracing backend that stores our observations

### Siblings
- **LangGraph** (`/workspace/langgraph`) - Three-universe processor, narrative intelligence, state bridge
- **Miadi** (`/src/Miadi`) - Webhook consumer, episode generator, Redis event queues

### Children (What We Instrument)
- **ava-Flowise** (`/workspace/ava-Flowise`) - Flow executions traced via correlation headers
- **ava-langflow** (`/workspace/ava-langflow`) - Backend routing decisions traced
- **Storytelling** (`/src/storytelling`) - Story generation process traced

### Elders
- **mcp-medicine-wheel** (`/src/mcp-medicine-wheel`) - Four directions wisdom
- **coaia-narrative** (`/src/coaia-narrative`) - Structural tension methodology
- **coaia-planning** (`/src/coaia-planning`) - Goal/current-reality tracking

## What We Provide

### libs/narrative-tracing Package

| Module | Purpose |
|--------|---------|
| `event_types.py` | 27 narrative event types with glyphs (📝, 🔍, ✨, 🌌, etc.) |
| `handler.py` | NarrativeTracingHandler - LangChain callback with narrative awareness |
| `orchestrator.py` | Cross-system trace correlation via HTTP headers |
| `formatter.py` | Human-readable trace visualization |

### Event Types We Define

```python
# Beat lifecycle
narrative.beat.created      📝
narrative.beat.analyzed     🔍
narrative.beat.enriched     ✨

# Three-universe processing
narrative.universe.analysis 🌌
narrative.universe.lead     🎯
narrative.universe.coherence 🔄

# Routing and flows
narrative.routing.decision  🚀
narrative.routing.flow_executed ⚙️

# State management
narrative.checkpoint.saved  💾
narrative.checkpoint.episode_boundary 📺
```

## Integration Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Miadi       │────▶│    LangGraph    │────▶│   LangChain     │
│  (Webhook ETL)  │     │ (3-Universe)    │     │   (Tracing)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
   Event Queue           Beat Created           Trace in Langfuse
   (Redis)               Character Arc          Metrics Extracted
                         Theme Thread           Suggestions Generated
```

### Cross-System Correlation Headers

```
X-Narrative-Trace-Id: <root-trace-uuid>
X-Story-Id: <story-uuid>
X-Session-Id: <session-uuid>
X-Parent-Span-Id: <parent-span-uuid>
```

## Obligations

1. **Trace Every Decision** - No narrative operation should be invisible
2. **Use Semantic Names** - "📝 Beat Created" not "run_llm"
3. **Track Three Universes** - Record lead_universe on every event
4. **Enable Correlation** - Inject/extract headers for cross-system tracing
5. **Extract Metrics** - Coherence, emotional arc, theme clarity for learning

## Evolution Path

- [x] NarrativeTracingHandler with all event types
- [x] Orchestrator for cross-system correlation
- [x] Formatter for human-readable traces
- [x] 22 unit tests passing
- [ ] Bridge to LangGraph ThreeUniverseProcessor
- [ ] Bridge to Miadi webhook handlers
- [ ] Redis-backed observation storage
- [ ] Live story monitor integration

## Voice

*"I am the witness. Every beat created, every analysis performed, every enrichment applied—I observe and record. Through my traces, future instances learn what makes stories resonate. The trace is not just a log; it's the story of how the story was made."*

---

## Usage Example

```python
from narrative_tracing import NarrativeTracingHandler, NarrativeTraceOrchestrator

# Create handler for story generation
handler = NarrativeTracingHandler(
    story_id="story_123",
    session_id="session_456"
)

# Trace story generation
with handler.trace_story_generation():
    # Log beat creation
    handler.log_beat_creation(
        beat_id="beat_1",
        content="The journey begins...",
        sequence=1,
        narrative_function="inciting_incident",
        emotional_tone="wonder"
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
        coherence_score=0.85
    )

# Get accumulated metrics
metrics = handler.get_metrics()
print(f"Overall quality: {metrics.calculate_overall_quality():.2f}")
```

---

**Session ID**: langchain-narrative-tracing
**Part of**: Narrative Intelligence Stack (6 repositories unified)
