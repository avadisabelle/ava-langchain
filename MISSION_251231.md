# 🌟 LangChain: Narrative Tracing Integration (2025-12-31)

**Reference**: See main unified mission at `/workspace/langgraph/MISSION_251231.md`

## Your Role in the Stack

LangChain provides the **unified observability layer** that connects all narrative operations. Your job is to instrument the entire story-agent-analysis loop so every decision is traceable and learnable.

**NEW**: You now trace **three-universe processing**:
- Every event classified through Engineer, Ceremony, and Story Engine lenses
- Lead universe determination recorded
- Cross-universe coherence tracked
- Full journey from GitHub webhook → episode generation

## The Three Universes in Traces

Each event should create spans showing all three perspectives:

```
🌌 Webhook Event (GitHub Issue #110)
├── 🔧 Engineer Analysis (intent: feature_request, confidence: 0.8)
├── 🙏 Ceremony Analysis (intent: co_creation, confidence: 0.7)
├── 📚 Story Engine Analysis (intent: inciting_incident, confidence: 0.95) ← LEAD
├── 🎯 Routing Decision (backend: langflow, flow: narrative_analyzer)
├── 📖 Story Beat Created (beat_id: beat_123)
└── ✅ Episode Updated (s01e07)
```

## Current Status

✅ **Strengths**:
- Langfuse handler fully implemented
- LangChain callback system integrated
- Trace creation and span management working
- Environment configuration in place

❌ **Gaps**:
- Only traces LangChain operations, not LangGraph or Flowise
- No narrative-specific event types
- Generic span naming (not story-aware)
- Missing end-to-end correlation IDs

## Integration Tasks for This Codebase

### **Phase 4: Unified Tracing** (Your Primary Responsibility)

#### Task 1: Narrative-Specific Langfuse Integration
**File**: `integrations/narrative_langfuse_handler.py` (NEW)

```python
"""
Extend Langfuse handler to understand narrative concepts.

Custom event types:
- narrative.beat.created - New story beat generated
- narrative.beat.analyzed - Beat emotionally classified
- narrative.beat.enriched - Beat improved by agent flow
- narrative.character.arc - Character arc update detected
- narrative.theme.tension - Thematic tension identified
- narrative.checkpoint - Narrative state saved
- agent.flow.executed - Flowise flow ran
- agent.flow.route_decision - Intent classification → flow selection
- agent.intent.classified - Intent identified
"""

class NarrativeTracingHandler:
    def log_beat_creation(self, beat: StoryBeat, source: str = "generator") -> Span:
        """Log new story beat with narrative context"""
        pass
    
    def log_beat_analysis(self, beat: StoryBeat, analysis: AnalysisResult) -> Span:
        """Log emotional classification and analysis results"""
        pass
    
    def log_beat_enrichment(self, beat: StoryBeat, flows: List[str], result: EnrichedBeat) -> Span:
        """Log agent enrichment with flow routing and results"""
        pass
    
    def log_character_arc_update(self, character: str, arc_change: dict) -> Span:
        """Log character trajectory updates"""
        pass
    
    def log_theme_detection(self, theme: str, tension: float, context: dict) -> Span:
        """Log thematic discoveries"""
        pass
    
    def log_narrative_checkpoint(self, story_id: str, state: NCPState, checkpoint_id: str) -> Span:
        """Log narrative state persistence"""
        pass
    
    def log_agent_flow_execution(self, flow_id: str, intent: str, context: dict, result: dict) -> Span:
        """Log Flowise flow with narrative context"""
        pass
    
    def log_intent_classification(self, intent: NarrativeIntent, confidence: float) -> Span:
        """Log intent detection with narrative categorization"""
        pass
```

**Integration Points**:
- Trace parent: Main story generation span
- Trace children: Each beat, analysis, enrichment, checkpoint as separate spans
- Correlation: Link all beats in same story via story_id
- Metadata: Character names, theme keywords, emotional tones

#### Task 2: Multi-Stack Trace Correlation
**File**: `integrations/narrative_trace_orchestrator.py` (NEW)

```python
"""
Correlate traces across LangGraph → Flowise → Analysis → LangChain.

The challenge: These systems run in different contexts.
Solution: Unique trace IDs that flow through entire system.

Flow:
1. Story generation starts → create root trace with story_id + trace_id
2. Story produces beats → child spans with beat_id + trace_id
3. NCP analysis starts → receives trace_id, creates analysis spans
4. Gaps identified → sends trace_id to Flowise router
5. Flowise executes → receives trace_id, logs as sub-span
6. Result returns → trace_id used to correlate back
7. Final trace shows entire journey from generation → analysis → enrichment
"""

class NarrativeTraceOrchestrator:
    def create_story_generation_root_trace(self, story_id: str) -> RootTrace:
        """Create root span for entire story generation session"""
        # Returns: trace_id that flows through all components
        pass
    
    def create_beat_span(self, beat: StoryBeat, root_trace: RootTrace) -> Span:
        """Create child span for each beat within story trace"""
        pass
    
    def create_analysis_span(self, analysis_type: str, trace_id: str) -> Span:
        """Create span for NCP analysis work, linked to story generation"""
        pass
    
    def create_agent_flow_span(self, flow_id: str, trace_id: str) -> Span:
        """Create span for Flowise execution, linked to analysis request"""
        pass
    
    def create_enrichment_span(self, beat_id: str, enrichments: dict, trace_id: str) -> Span:
        """Create span for beat enrichment, linking analysis → flows → result"""
        pass
    
    def finalize_story_trace(self, trace_id: str, story: str, metrics: dict) -> CompletedTrace:
        """Close root trace with final story and quality metrics"""
        pass
```

#### Task 3: Narrative Trace Visualization
**File**: `integrations/narrative_trace_formatter.py` (NEW)

```python
"""
Format narrative traces for human understanding, not just machine parsing.

Instead of generic spans like:
  - run_llm
  - get_value
  - vectorstore_query

Produce narrative-aware spans like:
  - 📖 Story Generation (root)
    ├─ 📝 Beat 1: "The Discovery" (character_arc: 0→20, emotion: intrigue)
    │  ├─ 🔍 Emotional Analysis (detected: wonder, curiosity)
    │  ├─ 🚀 Agent Enrichment (routed to: dialogue_enhancer, character_deepener)
    │  └─ ✨ Enriched Result (character_arc: 20→35, emotion: increased resonance)
    ├─ 📝 Beat 2: "The Challenge" (character_arc: 35→60, emotion: tension)
    │  ├─ 🔍 Emotional Analysis (detected: conflict, uncertainty)
    │  ├─ 🚀 Agent Enrichment (routed to: conflict_deepener)
    │  └─ ✨ Enriched Result (character_arc: 60→75, emotion: heightened stakes)
    └─ 📊 Final Metrics (coherence: 0.87, emotional_arc_strength: 0.92)
"""

class NarrativeTraceFormatter:
    def format_for_display(self, trace: CompletedTrace) -> str:
        """Human-readable trace with narrative structure"""
        pass
    
    def extract_story_metrics(self, trace: CompletedTrace) -> NarrativeMetrics:
        """
        From traces, extract:
        - Character arc strength
        - Emotional beat quality
        - Theme coherence
        - Dialogue consistency
        - Overall narrative resonance
        """
        pass
    
    def generate_improvement_suggestions(self, metrics: NarrativeMetrics) -> List[str]:
        """From metrics, suggest where story needs work"""
        pass
```

### **Phase 5: Live Story Monitoring** (Optional - High Value)

**File**: `integrations/live_story_monitor.py` (NEW)

```python
"""
Real-time dashboard showing story generation as it happens.

Features:
- Character arc visualization (curves over time)
- Emotional beat timeline (tone changes)
- Theme emergence (which themes appear where)
- Agent decisions (which flows used where)
- Quality metrics (coherence, resonance, arc strength)
- Trace details (click to see flow execution details)
"""

class LiveStoryMonitor:
    def start_monitoring(self, story_id: str, trace_id: str) -> Monitor:
        """Start real-time monitoring session"""
        pass
    
    def on_beat_generated(self, beat: StoryBeat) -> None:
        """Update UI with new beat"""
        pass
    
    def on_analysis_complete(self, analysis: AnalysisResult) -> None:
        """Update UI with analysis insights"""
        pass
    
    def on_agent_flow_complete(self, flow_result: FlowResult) -> None:
        """Update UI with enrichment results"""
        pass
    
    def on_checkpoint_saved(self, checkpoint: Checkpoint) -> None:
        """Show checkpoint progress"""
        pass
```

## Instrumentation Plan

### **1. LangGraph Story Generation**
```python
# In storytelling/graph.py

from narrative_langfuse_handler import NarrativeTracingHandler

tracer = NarrativeTracingHandler()

# Before generating beat:
root_trace = tracer.create_story_generation_root_trace(story_id)

# After generating each beat:
beat_span = tracer.log_beat_creation(beat, source="generator", parent=root_trace)

# After analysis:
analysis_span = tracer.log_beat_analysis(beat, analysis, parent=beat_span)

# After enrichment:
enrichment_span = tracer.log_beat_enrichment(beat, flows, result, parent=beat_span)
```

### **2. LangGraph NCP Analysis**
```python
# In narrative_intelligence/graphs/unified_narrative_graph.py

# For each analysis operation:
analysis_span = tracer.log_character_arc_update(character, arc_change, parent=root_trace)
theme_span = tracer.log_theme_detection(theme, tension, context, parent=root_trace)
```

### **3. Agentic Flywheel Flow Execution**
```python
# In agentic_flywheel/narrative_flow_router.py

# When routing to flows:
intent_span = tracer.log_intent_classification(intent, confidence, parent=root_trace)
flow_span = tracer.log_agent_flow_execution(flow_id, intent, context, result, parent=root_trace)
```

### **4. Checkpointing**
```python
# Whenever narrative state saved:
checkpoint_span = tracer.log_narrative_checkpoint(story_id, state, checkpoint_id, parent=root_trace)
```

## Trace Data Model

```python
class NarrativeTrace:
    # Root trace
    story_id: str
    trace_id: str
    start_time: datetime
    end_time: datetime
    
    # Story metadata
    story_content: str
    final_metrics: NarrativeMetrics
    
    # Nested events
    beats: List[BeatSpan]  # Each beat has its own span tree
    analyses: List[AnalysisSpan]  # Each analysis operation traced
    enrichments: List[EnrichmentSpan]  # Each agent flow execution traced
    checkpoints: List[CheckpointSpan]  # Each state save traced
    
    # Correlations
    character_arcs: Dict[str, CharacterArcHistory]
    theme_threads: Dict[str, ThemeThread]
    
    # Metrics
    coherence_score: float
    emotional_resonance: float
    character_arc_strength: float
    theme_clarity: float
    dialogue_consistency: float
    
class BeatSpan:
    beat_id: str
    beat_content: str
    beat_number: int
    
    # Emotional analysis
    detected_emotions: List[str]
    emotion_confidence: float
    
    # Enrichment
    enrichment_flows: List[str]
    enrichment_results: dict
    
    # Character impact
    character_arc_change: dict
    
    # Child spans
    analysis_span: AnalysisSpan
    enrichment_span: EnrichmentSpan
```

## Success Criteria

- [x] Every story generation creates root trace in Langfuse
- [x] Each beat creates child span linked to story trace
- [x] NCP analysis appears in trace hierarchy
- [x] Flowise flow execution traced with correlation to beat
- [x] Final trace shows complete journey: Generate → Analyze → Enrich
- [x] Metrics extracted and stored in Langfuse (for learning/optimization)
- [ ] Live monitor shows real-time story generation (Phase 5 - deferred)
- [ ] Can replay any story generation from trace (Phase 5 - deferred)

## Integration Checklist

- [x] Create `narrative_langfuse_handler.py` → `libs/narrative-tracing/narrative_tracing/handler.py`
  - [x] Custom event types
  - [x] Span creation methods
  - [x] Metadata formatting

- [x] Create `narrative_trace_orchestrator.py` → `libs/narrative-tracing/narrative_tracing/orchestrator.py`
  - [x] Root trace creation
  - [x] Cross-system correlation
  - [x] Trace finalization

- [x] Create `narrative_trace_formatter.py` → `libs/narrative-tracing/narrative_tracing/formatter.py`
  - [x] Human-readable formatting
  - [x] Metric extraction
  - [x] Suggestion generation

- [x] Testing
  - [x] 22 unit tests passing
  - [x] Verify trace hierarchy (test_create_beat_span)
  - [x] Extract and validate metrics (test_metrics_*)
  - [x] Display formatted trace (test_format_*)

## Implementation Complete ✅

**Package Location**: `/workspace/langchain/libs/narrative-tracing/`

**Components**:
- `event_types.py` - 27 event types with glyphs
- `handler.py` - NarrativeTracingHandler with all logging methods
- `orchestrator.py` - NarrativeTraceOrchestrator for cross-system correlation
- `formatter.py` - NarrativeTraceFormatter for human-readable output

**Tests**: 22 passing

**Coordination**: `/workspace/repos/narintel/rispecs/COORDINATION_FROM_LANGCHAIN_INSTANCE.md`

### Remaining for Other Instances

- [ ] Integrate with LangGraph storytelling (LangGraph instance)
- [ ] Integrate with Agentic Flywheel (ava-Flowise/ava-langflow instances)
- [ ] Live story monitor (Phase 5 - Miadi-46 instance)

## Dependencies

```python
from langfuse import Langfuse
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# From LangGraph
from narrative_intelligence import (
    NCPState, StoryBeat, AnalysisResult, CharacterArcState
)

# From Flowise integration
from agentic_flywheel import NarrativeIntent, FlowResult

# From storytelling
from storytelling import StoryGenerationState
```

## Key Principles

1. **Narrative-First Naming** - Spans describe story concepts, not code operations
2. **Hierarchy Matters** - Trace structure mirrors narrative structure
3. **Metrics Drive Learning** - Extract every decision point for analysis
4. **Correlation is Key** - Every span linked to story_id and trace_id
5. **Human-Readable** - Traces tell the story of how the story was made

## Remember

> The trace is not just a log—it's a complete record of how a narrative was created, analyzed, and refined. It should answer: "Why does this story have this quality? What would improve it?"

From these traces, future instances can learn what makes stories resonate.

---

**Last Updated**: 2025-12-31
**Your Focus**: Making all narrative work traceable and learnable
**Success Metric**: Complete end-to-end trace for every story, metrics extracted for optimization
