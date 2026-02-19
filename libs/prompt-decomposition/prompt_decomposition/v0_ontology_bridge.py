"""
V0 Ontology Bridge

Maps PDE concepts to the V0 Medicine Wheel Developer Suite ontology vision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from prompt_decomposition.directional_decomposer import Direction
from prompt_decomposition.wheel_bridge import WheelQuadrant


@dataclass
class OntologyCoreConcept:
    direction: Direction
    quadrant: WheelQuadrant
    indigenous_name: str
    act: int
    season: str
    element: str


ONTOLOGY_CORE_MAP: Dict[Direction, OntologyCoreConcept] = {
    Direction.EAST: OntologyCoreConcept(
        direction=Direction.EAST, quadrant=WheelQuadrant.SPIRITUAL,
        indigenous_name="Waabinong", act=1, season="spring", element="air",
    ),
    Direction.SOUTH: OntologyCoreConcept(
        direction=Direction.SOUTH, quadrant=WheelQuadrant.MENTAL,
        indigenous_name="Zhaawanong", act=2, season="summer", element="fire",
    ),
    Direction.WEST: OntologyCoreConcept(
        direction=Direction.WEST, quadrant=WheelQuadrant.EMOTIONAL,
        indigenous_name="Epangishmok", act=3, season="autumn", element="water",
    ),
    Direction.NORTH: OntologyCoreConcept(
        direction=Direction.NORTH, quadrant=WheelQuadrant.PHYSICAL,
        indigenous_name="Kiiwedinong", act=4, season="winter", element="earth",
    ),
}


@dataclass
class NarrativeBeatMapping:
    action_id: str
    direction: Direction
    act: int
    description: str
    implicit: bool
    confidence: float


def action_to_narrative_beat(
    action_id: str,
    text: str,
    direction: Direction,
    confidence: float,
    implicit: bool,
) -> NarrativeBeatMapping:
    concept = ONTOLOGY_CORE_MAP.get(direction)
    return NarrativeBeatMapping(
        action_id=action_id,
        direction=direction,
        act=concept.act if concept else 4,
        description=text,
        implicit=implicit,
        confidence=confidence,
    )


PACKAGE_MAPPING: Dict[str, Dict[str, Any]] = {
    "@medicine-wheel/ontology-core": {
        "existing_packages": [
            "langchain-prompt-decomposition (Direction, WheelQuadrant types)",
            "langchain-relational-intelligence (MedicineWheelFilter, ImportanceUnit)",
        ],
        "provided_by": "Direction enum, WheelBridge, ONTOLOGY_CORE_MAP",
        "missing": "RDF triple store, OWL vocabulary, SPARQL queries",
    },
    "@medicine-wheel/graph-viz": {
        "existing_packages": [
            "langchain-prompt-decomposition (DependencyGraph visualization)",
        ],
        "provided_by": "DependencyMapper produces graph structure",
        "missing": "D3 force-directed layout, Medicine Wheel overlay renderer",
    },
    "@medicine-wheel/narrative-engine": {
        "existing_packages": [
            "langgraph-narrative-intelligence (ThreeUniverseProcessor, CoherenceEngine)",
            "langchain-narrative-tracing (NarrativeTracingHandler)",
            "langgraph-prompt-decomposition-engine (DecompositionGraph)",
        ],
        "provided_by": "ActionStack -> beats, DecompositionGraph -> ceremonial cadence",
        "missing": "Timeline/categorical view React components",
    },
    "@medicine-wheel/relational-query": {
        "existing_packages": [
            "langchain-relational-intelligence (ImportanceStore, SpiralTracker, ValueGate)",
            "langchain-prompt-decomposition (DependencyMapper)",
        ],
        "provided_by": "DependencyGraph + ImportanceStore",
        "missing": "SPARQL-like query builder, OCAP-aware access control",
    },
    "@medicine-wheel/ui-components": {
        "existing_packages": [
            "ava-Flowise (PromptDecomposition node, MedicineWheelGate node)",
            "ava-langflow (PromptDecomposition component, MedicineWheelGate component)",
        ],
        "provided_by": "AgentFlow nodes for Flowise + Langflow components",
        "missing": "Standalone React components, direction cards, beat timelines",
    },
}
