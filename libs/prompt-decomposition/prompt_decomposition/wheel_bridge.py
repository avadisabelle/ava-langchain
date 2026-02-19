"""
Medicine Wheel Bridge

Bridges PDE Four Directions with Medicine Wheel quadrants:
  EAST → SPIRITUAL (vision, purpose)
  SOUTH → MENTAL (analysis, learning)
  WEST → EMOTIONAL (reflection, ceremony)
  NORTH → PHYSICAL (action, execution)
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List

from prompt_decomposition.directional_decomposer import Direction, DirectionalAnalysis


class WheelQuadrant(str, Enum):
    PHYSICAL = "physical"
    EMOTIONAL = "emotional"
    MENTAL = "mental"
    SPIRITUAL = "spiritual"


DIRECTION_TO_QUADRANT: Dict[Direction, WheelQuadrant] = {
    Direction.EAST: WheelQuadrant.SPIRITUAL,
    Direction.SOUTH: WheelQuadrant.MENTAL,
    Direction.WEST: WheelQuadrant.EMOTIONAL,
    Direction.NORTH: WheelQuadrant.PHYSICAL,
}

QUADRANT_TO_DIRECTION: Dict[WheelQuadrant, Direction] = {
    WheelQuadrant.SPIRITUAL: Direction.EAST,
    WheelQuadrant.MENTAL: Direction.SOUTH,
    WheelQuadrant.EMOTIONAL: Direction.WEST,
    WheelQuadrant.PHYSICAL: Direction.NORTH,
}


class WheelEnrichedAnalysis:
    """A DirectionalAnalysis enriched with Medicine Wheel quadrant assessment."""

    def __init__(
        self,
        analysis: DirectionalAnalysis,
        quadrant_presence: Dict[WheelQuadrant, float],
        relational_coverage: float,
        ceremony_required: bool,
    ):
        self.analysis = analysis
        self.quadrant_presence = quadrant_presence
        self.relational_coverage = relational_coverage
        self.ceremony_required = ceremony_required

    # Delegate key attributes to underlying analysis
    @property
    def id(self) -> str:
        return self.analysis.id

    @property
    def balance(self) -> float:
        return self.analysis.balance

    @property
    def lead_direction(self) -> Direction:
        return self.analysis.lead_direction

    @property
    def neglected_directions(self) -> List[Direction]:
        return self.analysis.neglected_directions


class MedicineWheelBridge:
    """Maps PDE directions to Medicine Wheel quadrants and assesses ceremony need."""

    def __init__(self, ceremony_threshold: float = 0.3):
        self.ceremony_threshold = ceremony_threshold

    def enrich(self, analysis: DirectionalAnalysis) -> WheelEnrichedAnalysis:
        total_insights = sum(
            len(insights) for insights in analysis.directions.values()
        ) or 1

        quadrant_presence: Dict[WheelQuadrant, float] = {
            WheelQuadrant.SPIRITUAL: len(analysis.directions.get(Direction.EAST, [])) / total_insights,
            WheelQuadrant.MENTAL: len(analysis.directions.get(Direction.SOUTH, [])) / total_insights,
            WheelQuadrant.EMOTIONAL: len(analysis.directions.get(Direction.WEST, [])) / total_insights,
            WheelQuadrant.PHYSICAL: len(analysis.directions.get(Direction.NORTH, [])) / total_insights,
        }

        represented = sum(1 for v in quadrant_presence.values() if v > 0.05)
        relational_coverage = represented / 4.0

        ceremonial_presence = (
            quadrant_presence[WheelQuadrant.SPIRITUAL]
            + quadrant_presence[WheelQuadrant.EMOTIONAL]
        )
        ceremony_required = ceremonial_presence < self.ceremony_threshold

        return WheelEnrichedAnalysis(
            analysis=analysis,
            quadrant_presence=quadrant_presence,
            relational_coverage=relational_coverage,
            ceremony_required=ceremony_required,
        )

    def can_proceed_without_ceremony(self, analysis: DirectionalAnalysis) -> bool:
        enriched = self.enrich(analysis)
        return not enriched.ceremony_required

    def get_relational_guidance(self, analysis: DirectionalAnalysis) -> List[str]:
        enriched = self.enrich(analysis)
        guidance: List[str] = []

        if enriched.quadrant_presence[WheelQuadrant.SPIRITUAL] < 0.1:
            guidance.append(
                "EAST/Spiritual: The vision is unclear. What is the deeper purpose? Who does this serve?"
            )
        if enriched.quadrant_presence[WheelQuadrant.EMOTIONAL] < 0.1:
            guidance.append(
                "WEST/Emotional: Reflection is missing. What ceremonies or protocols should be honored?"
            )
        if enriched.quadrant_presence[WheelQuadrant.MENTAL] < 0.1:
            guidance.append(
                "SOUTH/Mental: Analysis is thin. What needs to be researched before proceeding?"
            )
        if enriched.quadrant_presence[WheelQuadrant.PHYSICAL] < 0.1:
            guidance.append(
                "NORTH/Physical: No actionable steps found. What concrete actions will manifest this work?"
            )
        if enriched.ceremony_required:
            guidance.append(
                "⚠️ Ceremony Required: Spiritual and emotional dimensions are underrepresented. "
                "Pause for relational check-in before proceeding."
            )

        return guidance
