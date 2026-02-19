#!/usr/bin/env python3
"""
Three-System Integration Example

Demonstrates how narrative-tracing coordinates traces across the
three-project Narrative Intelligence Stack:
1. LangGraph (three-universe processing)
2. Miadi (webhook consumption and episode generation)
3. Storytelling (beat creation and enrichment)

This example simulates the complete flow:
GitHub Webhook → Miadi Receives → LangGraph Analyzes (3 universes) →
Storytelling Creates Beat → Traces Captured End-to-End

Run with:
    cd libs/narrative-tracing
    python examples/three_system_integration_example.py

Session ID: langchain-narrative-tracing
Created: 2026-01-30
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Demonstrate the three-system integration."""
    
    # =========================================================================
    # Setup: Create handlers and adapters
    # =========================================================================
    
    print("=" * 60)
    print("Three-System Integration Example")
    print("=" * 60)
    print()
    
    # Note: In production, Langfuse credentials would be set via environment
    # For this example, we mock the Langfuse client
    from unittest.mock import MagicMock, patch
    
    with patch("narrative_tracing.handler.Langfuse") as mock_langfuse:
        # Setup mock
        mock_instance = MagicMock()
        mock_trace = MagicMock()
        mock_span = MagicMock()
        mock_span.id = "mock_span_001"
        mock_trace.span.return_value = mock_span
        mock_instance.trace.return_value = mock_trace
        mock_langfuse.return_value = mock_instance
        
        # Import after patching
        from narrative_tracing import NarrativeTracingHandler
        from narrative_tracing.adapters import (
            LangGraphBridge,
            MiadiIntegration,
            StorytellingHooks,
            HEADER_TRACE_ID,
        )
        
        # Create the main handler
        handler = NarrativeTracingHandler(
            story_id="story_github_integration",
            session_id="session_three_system_demo",
        )
        
        # Create adapters for each system
        langgraph_bridge = LangGraphBridge(handler)
        miadi = MiadiIntegration(handler)
        storytelling = StorytellingHooks(handler)
        
        print("✅ Created handler and adapters for all three systems")
        print()
        
        # =====================================================================
        # Step 1: Miadi Receives Webhook
        # =====================================================================
        
        print("-" * 60)
        print("Step 1: Miadi Receives GitHub Webhook")
        print("-" * 60)
        
        # Simulate incoming webhook
        webhook_event = {
            "event_id": "webhook_001",
            "event_type": "github.issue",
            "source": "github",
            "payload": {
                "issue": {
                    "id": 12345,
                    "title": "Add three-universe processing to LangGraph",
                    "body": "We need to analyze events through engineer, ceremony, and story engine lenses.",
                    "user": {"login": "developer_1"},
                },
                "repository": {"full_name": "org/narrative-intelligence"},
            },
        }
        
        # Log webhook received
        miadi.log_webhook_received(
            event_id=webhook_event["event_id"],
            event_type=webhook_event["event_type"],
            source=webhook_event["source"],
            repository="org/narrative-intelligence",
            sender="developer_1",
            payload_preview=webhook_event["payload"]["issue"]["title"],
        )
        
        print(f"  📥 Received webhook: {webhook_event['event_type']}")
        print(f"  📋 Issue: {webhook_event['payload']['issue']['title']}")
        print()
        
        # Log transformation
        miadi.log_webhook_transformed(
            event_id=webhook_event["event_id"],
            output_format="narrative_event",
            fields_extracted=["title", "body", "author", "repository"],
        )
        
        print("  🔄 Transformed to narrative event format")
        print()
        
        # Get correlation headers for passing to LangGraph
        headers = miadi.inject_correlation_headers({})
        print(f"  📤 Correlation headers prepared:")
        print(f"     {HEADER_TRACE_ID}: {headers.get(HEADER_TRACE_ID, 'N/A')[:20]}...")
        print()
        
        # =====================================================================
        # Step 2: LangGraph Three-Universe Analysis
        # =====================================================================
        
        print("-" * 60)
        print("Step 2: LangGraph Three-Universe Analysis")
        print("-" * 60)
        
        # Simulate three-universe analysis results
        # (In production, this comes from ThreeUniverseProcessor.process())
        engineer_result = {
            "intent": "feature_implementation",
            "confidence": 0.85,
            "suggested_flows": ["code_review", "integration_test"],
            "context": {"technical_scope": "core_processing", "complexity": "high"},
        }
        
        ceremony_result = {
            "intent": "co_creation",
            "confidence": 0.75,
            "suggested_flows": ["witness_collaboration", "honor_contributions"],
            "context": {"is_collaborative": True, "relationship_depth": "community"},
        }
        
        story_engine_result = {
            "intent": "rising_action",
            "confidence": 0.90,
            "suggested_flows": ["advance_narrative", "develop_characters"],
            "context": {"act": 2, "dramatic_tension": 0.7, "narrative_function": "turning_point"},
        }
        
        # Create callback and log analysis
        callback = langgraph_bridge.create_three_universe_callback()
        callback(
            event_id=webhook_event["event_id"],
            event_content=webhook_event["payload"]["issue"]["title"],
            engineer_result=engineer_result,
            ceremony_result=ceremony_result,
            story_engine_result=story_engine_result,
            lead_universe="story_engine",  # Story engine leads with 0.90 confidence
            coherence_score=0.82,
        )
        
        print("  🌌 Three-Universe Analysis Complete:")
        print(f"     🔧 Engineer: {engineer_result['intent']} ({engineer_result['confidence']:.0%})")
        print(f"     🙏 Ceremony: {ceremony_result['intent']} ({ceremony_result['confidence']:.0%})")
        print(f"     📚 Story Engine: {story_engine_result['intent']} ({story_engine_result['confidence']:.0%})")
        print(f"     🎯 Lead Universe: story_engine")
        print(f"     📊 Coherence Score: 0.82")
        print()
        
        # =====================================================================
        # Step 3: Storytelling Creates Beat
        # =====================================================================
        
        print("-" * 60)
        print("Step 3: Storytelling Creates Beat from Event")
        print("-" * 60)
        
        # Use context manager for full beat lifecycle
        with storytelling.trace_beat_lifecycle("beat_webhook_001") as tracer:
            # Log beat content creation
            beat_content = (
                "A new feature request emerges from the community—the call for "
                "three-universe processing in LangGraph. This isn't just a technical "
                "enhancement; it represents the ecosystem's growing awareness that "
                "every event deserves multiple perspectives. The engineer sees "
                "architecture, the ceremony keeper sees relationships, and the story "
                "engine sees narrative progression. Together, they form coherent "
                "understanding."
            )
            
            tracer.log_content(
                content=beat_content,
                sequence=1,
                narrative_function="turning_point",
                act=2,
                emotional_tone="collaborative_growth",
                character_id="the_ecosystem",
            )
            
            print(f"  📝 Beat Created: turning_point (Act 2)")
            print(f"     Content preview: {beat_content[:80]}...")
            print()
            
            # Log analysis
            tracer.log_analysis(
                classification="collaborative_growth",
                confidence=0.88,
                detected_emotions=["curiosity", "anticipation", "unity"],
            )
            
            print("  🔍 Analysis: collaborative_growth (88% confidence)")
            print("     Emotions: curiosity, anticipation, unity")
            print()
            
            # Log enrichment
            tracer.log_enrichment(
                enrichment_type="narrative_deepening",
                flows_used=["theme_strengthener", "character_connector"],
                quality_before=0.7,
                quality_after=0.88,
            )
            
            print("  ✨ Enrichment: +18% quality improvement")
            print("     Flows: theme_strengthener, character_connector")
            print()
            
            # Log lessons
            lessons = [
                "Three complete systems form an integrated whole when seen together",
                "Cross-session coordination proves parallel instances can work on same narrative",
                "Ecosystem coherence emerges when observations are traced and visible",
            ]
            tracer.log_lessons(lessons)
            
            print("  📚 Lessons Extracted:")
            for lesson in lessons:
                print(f"     • {lesson}")
            print()
        
        # Log character arc update
        storytelling.log_character_arc_update(
            character_id="the_ecosystem",
            character_name="The Narrative Intelligence Ecosystem",
            arc_position_before=0.4,
            arc_position_after=0.55,
            growth_description="Ecosystem recognizes its own coherence through tracing",
            beat_id="beat_webhook_001",
        )
        
        print("  📈 Character Arc: The Ecosystem (40% → 55%)")
        print("     Growth: Ecosystem recognizes its own coherence")
        print()
        
        # =====================================================================
        # Summary: Trace Statistics
        # =====================================================================
        
        print("=" * 60)
        print("Integration Summary")
        print("=" * 60)
        print()
        
        # Handler metrics
        metrics = handler.get_metrics()
        print("📊 Trace Metrics:")
        print(f"   Beats Generated: {metrics.beats_generated}")
        print(f"   Enrichments Applied: {metrics.enrichments_applied}")
        print(f"   Routing Decisions: {metrics.routing_decisions}")
        print(f"   Engineer Alignment: {metrics.engineer_alignment:.0%}")
        print(f"   Ceremony Alignment: {metrics.ceremony_alignment:.0%}")
        print(f"   Story Engine Alignment: {metrics.story_engine_alignment:.0%}")
        print(f"   Cross-Universe Coherence: {metrics.cross_universe_coherence:.0%}")
        print()
        
        # Adapter statistics
        print("🔌 Adapter Statistics:")
        print(f"   LangGraph analyses: {langgraph_bridge.analysis_count}")
        print(f"   Miadi webhooks: {miadi.webhook_count}")
        print(f"   Storytelling beats: {storytelling.beat_count}")
        print()
        
        # Session summary
        session = storytelling.get_session_summary()
        print("📖 Storytelling Session:")
        print(f"   Current Act: {session['current_act']}")
        print(f"   Current Sequence: {session['current_sequence']}")
        print(f"   Character Updates: {session['character_updates_count']}")
        print()
        
        print("=" * 60)
        print("✅ Three-System Integration Complete!")
        print()
        print("This example demonstrated:")
        print("  1. Webhook received and transformed (Miadi)")
        print("  2. Three-universe analysis with coherence scoring (LangGraph)")
        print("  3. Beat lifecycle with lessons extracted (Storytelling)")
        print("  4. End-to-end trace correlation via HTTP headers")
        print("  5. Metrics accumulated across all systems")
        print("=" * 60)


if __name__ == "__main__":
    main()
