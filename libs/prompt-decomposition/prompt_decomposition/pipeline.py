"""
Full PDE Pipeline

Convenience function that runs the complete decomposition pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from prompt_decomposition.directional_decomposer import DirectionalDecomposer
from prompt_decomposition.intent_extractor import IntentExtractor
from prompt_decomposition.dependency_mapper import DependencyMapper
from prompt_decomposition.action_stack import ActionStackBuilder, DecompositionResult
from prompt_decomposition.wheel_bridge import MedicineWheelBridge, WheelEnrichedAnalysis


def decompose(
    prompt: str,
    *,
    extract_implicit: bool = True,
    map_dependencies: bool = True,
    max_items: int = 20,
    ceremony_threshold: float = 0.3,
    neglect_threshold: float = 0.1,
    balance_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Run the full PDE pipeline on a prompt.

    Returns a dict with:
        - decomposition: DecompositionResult
        - wheel_enriched: WheelEnrichedAnalysis
        - json: str (PDE JSON format)
        - markdown: str (human-readable)
    """
    decomposer = DirectionalDecomposer(
        neglect_threshold=neglect_threshold,
        balance_threshold=balance_threshold,
    )
    extractor = IntentExtractor(
        extract_implicit=extract_implicit,
        map_dependencies=map_dependencies,
    )
    mapper = DependencyMapper()
    builder = ActionStackBuilder(
        include_implicit=extract_implicit,
        max_items=max_items,
    )
    bridge = MedicineWheelBridge(ceremony_threshold=ceremony_threshold)

    directional_analysis = decomposer.decompose(prompt)
    intent_result = extractor.extract(prompt)
    graph = mapper.build_graph(intent_result.secondary)
    order = mapper.compute_execution_order(graph)
    decomposition = builder.build(directional_analysis, intent_result, order)
    wheel_enriched = bridge.enrich(directional_analysis)

    return {
        "decomposition": decomposition,
        "wheel_enriched": wheel_enriched,
        "json": builder.to_json(decomposition),
        "markdown": builder.to_markdown(decomposition),
    }
