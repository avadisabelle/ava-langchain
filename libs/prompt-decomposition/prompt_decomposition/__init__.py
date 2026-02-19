"""
langchain-prompt-decomposition

Prompt Decomposition Engine (PDE) primitives for the Narrative Intelligence Stack.
Decomposes complex prompts through the Four Directions (Medicine Wheel):

- EAST (Waabinong/Vision): What is being asked?
- SOUTH (Zhaawanong/Analysis): What needs to be learned?
- WEST (Epangishmok/Validation): What needs reflection?
- NORTH (Kiiwedinong/Action): What executes?

Core Components:
- DirectionalDecomposer: Classifies prompt segments by direction
- IntentExtractor: Extracts primary + secondary intents with confidence
- DependencyMapper: Maps task dependencies and execution order
- ActionStackBuilder: Produces the final ordered execution plan
- MedicineWheelBridge: Maps directions to quadrants from relational-intelligence

Usage:
    from prompt_decomposition import decompose

    result = decompose("Investigate the codebase. Build a new module. Test everything.")
    print(result["markdown"])
"""

__version__ = "0.1.0"

from prompt_decomposition.directional_decomposer import (
    Direction,
    ALL_DIRECTIONS,
    DIRECTION_NAMES,
    DIRECTION_QUESTIONS,
    DIRECTION_KEYWORDS,
    DirectionalDecomposer,
)

from prompt_decomposition.intent_extractor import (
    Urgency,
    IntentExtractor,
)

from prompt_decomposition.dependency_mapper import (
    DependencyMapper,
)

from prompt_decomposition.action_stack import (
    ActionStackBuilder,
)

from prompt_decomposition.wheel_bridge import (
    WheelQuadrant,
    DIRECTION_TO_QUADRANT,
    QUADRANT_TO_DIRECTION,
    MedicineWheelBridge,
)

from prompt_decomposition.v0_ontology_bridge import (
    ONTOLOGY_CORE_MAP,
    PACKAGE_MAPPING,
    action_to_narrative_beat,
)

from prompt_decomposition.pipeline import decompose

from prompt_decomposition.runnable import (
    RunnableDecomposer,
    RunnableDirectionalAnalyzer,
    RunnableWheelGate,
)

__all__ = [
    "Direction",
    "ALL_DIRECTIONS",
    "DIRECTION_NAMES",
    "DIRECTION_QUESTIONS",
    "DIRECTION_KEYWORDS",
    "DirectionalDecomposer",
    "Urgency",
    "IntentExtractor",
    "DependencyMapper",
    "ActionStackBuilder",
    "WheelQuadrant",
    "DIRECTION_TO_QUADRANT",
    "QUADRANT_TO_DIRECTION",
    "MedicineWheelBridge",
    "ONTOLOGY_CORE_MAP",
    "PACKAGE_MAPPING",
    "action_to_narrative_beat",
    "decompose",
    "RunnableDecomposer",
    "RunnableDirectionalAnalyzer",
    "RunnableWheelGate",
]
