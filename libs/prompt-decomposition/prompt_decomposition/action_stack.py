"""
Action Stack Builder

Produces a dependency-ordered, direction-tagged execution plan.
This is the NORTH (Action) function of PDE — what actually executes.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from prompt_decomposition.directional_decomposer import Direction, DirectionalAnalysis
from prompt_decomposition.intent_extractor import IntentExtractionResult, SecondaryIntent
from prompt_decomposition.dependency_mapper import DependencyMapper, ExecutionOrder


@dataclass
class ActionItem:
    id: str
    text: str
    direction: Direction
    dependency: Optional[str]
    completed: bool
    confidence: float
    implicit: bool


@dataclass
class DecompositionResult:
    id: str
    timestamp: str
    prompt: str
    primary: Dict[str, Any]
    secondary: List[SecondaryIntent]
    context: Dict[str, Any]
    directions: Dict[str, List[Dict[str, Any]]]
    action_stack: List[ActionItem]
    balance: float
    lead_direction: Direction
    neglected_directions: List[Direction]
    ambiguities: List[str]


class ActionStackBuilder:
    """Builds the complete PDE output from analysis results."""

    def __init__(
        self,
        include_implicit: bool = True,
        max_items: int = 20,
    ):
        self.include_implicit = include_implicit
        self.max_items = max_items

    def build(
        self,
        directional_analysis: DirectionalAnalysis,
        intent_result: IntentExtractionResult,
        execution_order: Optional[ExecutionOrder] = None,
    ) -> DecompositionResult:
        result_id = str(uuid.uuid4())

        if execution_order:
            action_stack = self._from_execution_order(execution_order, intent_result)
        else:
            action_stack = self._from_intents(intent_result, directional_analysis)

        if len(action_stack) > self.max_items:
            action_stack = action_stack[:self.max_items]

        if not self.include_implicit:
            action_stack = [a for a in action_stack if not a.implicit]

        ambiguities = self._detect_ambiguities(directional_analysis, intent_result)

        directions_dict: Dict[str, List[Dict[str, Any]]] = {}
        for d in [Direction.EAST, Direction.SOUTH, Direction.WEST, Direction.NORTH]:
            insights = directional_analysis.directions.get(d, [])
            directions_dict[d.value] = [
                {"text": i.text, "confidence": i.confidence, "implicit": i.implicit}
                for i in insights
            ]

        return DecompositionResult(
            id=result_id,
            timestamp=intent_result.timestamp,
            prompt=intent_result.prompt,
            primary={
                "action": intent_result.primary.action,
                "target": intent_result.primary.target,
                "urgency": intent_result.primary.urgency.value,
                "confidence": intent_result.primary.confidence,
            },
            secondary=intent_result.secondary,
            context={
                "files_needed": intent_result.context.files_needed,
                "tools_required": intent_result.context.tools_required,
                "assumptions": intent_result.context.assumptions,
            },
            directions=directions_dict,
            action_stack=action_stack,
            balance=directional_analysis.balance,
            lead_direction=directional_analysis.lead_direction,
            neglected_directions=directional_analysis.neglected_directions,
            ambiguities=ambiguities,
        )

    def to_json(self, result: DecompositionResult) -> str:
        """Serialize to PDE JSON format (compatible with .pde/ structure)."""
        return json.dumps({
            "id": result.id,
            "timestamp": result.timestamp,
            "prompt": result.prompt,
            "result": {
                "primary": result.primary,
                "secondary": [
                    {
                        "id": s.id, "action": s.action, "target": s.target,
                        "implicit": s.implicit, "dependency": s.dependency,
                        "confidence": s.confidence,
                    }
                    for s in result.secondary
                ],
                "context": result.context,
                "directions": result.directions,
                "actionStack": [
                    {
                        "id": a.id, "text": a.text, "direction": a.direction.value,
                        "dependency": a.dependency, "completed": a.completed,
                        "confidence": a.confidence, "implicit": a.implicit,
                    }
                    for a in result.action_stack
                ],
                "ambiguities": result.ambiguities,
            },
            "options": {
                "extractImplicit": self.include_implicit,
                "mapDependencies": True,
            },
        }, indent=2)

    def to_markdown(self, result: DecompositionResult) -> str:
        """Render as human-readable Markdown."""
        lines = [
            "# 🧭 Prompt Decomposition",
            "",
            f"**Primary Intent:** {result.primary['action']} → {result.primary['target']}",
            f"**Urgency:** {result.primary['urgency']} | **Confidence:** {result.primary['confidence'] * 100:.0f}%",
            f"**Balance:** {result.balance * 100:.0f}% | **Lead:** {result.lead_direction.value}",
            "",
        ]

        dir_emoji = {"east": "🌅", "south": "🔥", "west": "🌊", "north": "❄️"}
        for d in ["east", "south", "west", "north"]:
            insights = result.directions.get(d, [])
            if insights:
                lines.append(f"## {dir_emoji[d]} {d.upper()}")
                for i in insights:
                    tag = " _(implicit)_" if i["implicit"] else ""
                    lines.append(f"- {i['text']}{tag} [{i['confidence'] * 100:.0f}%]")
                lines.append("")

        lines.append("## 📋 Action Stack")
        for a in result.action_stack:
            check = "x" if a.completed else " "
            dep = f" → depends on: {a.dependency}" if a.dependency else ""
            tag = " _(implicit)_" if a.implicit else ""
            lines.append(f"- [{check}] [{a.direction.value}] {a.text}{tag}{dep}")
        lines.append("")

        if result.ambiguities:
            lines.append("## ⚠️ Ambiguities")
            for amb in result.ambiguities:
                lines.append(f"- {amb}")

        return "\n".join(lines)

    def _from_execution_order(
        self, order: ExecutionOrder, intent_result: IntentExtractionResult
    ) -> List[ActionItem]:
        intent_map = {s.id: s for s in intent_result.secondary}
        items: List[ActionItem] = []

        for layer in order.layers:
            for node in layer:
                intent = intent_map.get(node.intent_id)
                items.append(ActionItem(
                    id=node.id,
                    text=f"{node.action} {node.target}",
                    direction=node.direction,
                    dependency=node.dependencies[0] if node.dependencies else None,
                    completed=node.completed,
                    confidence=intent.confidence if intent else 0.7,
                    implicit=intent.implicit if intent else False,
                ))
        return items

    def _from_intents(
        self, intent_result: IntentExtractionResult, analysis: DirectionalAnalysis
    ) -> List[ActionItem]:
        mapper = DependencyMapper()
        graph = mapper.build_graph(intent_result.secondary)
        order = mapper.compute_execution_order(graph)
        return self._from_execution_order(order, intent_result)

    def _detect_ambiguities(
        self, analysis: DirectionalAnalysis, intent_result: IntentExtractionResult
    ) -> List[str]:
        ambiguities: List[str] = []
        if intent_result.primary.confidence < 0.5:
            ambiguities.append(
                f"Primary intent has low confidence ({intent_result.primary.confidence * 100:.0f}%) "
                "— consider clarifying the main goal."
            )
        for d in analysis.neglected_directions:
            label = {
                Direction.EAST: "vision clarity",
                Direction.SOUTH: "research context",
                Direction.WEST: "validation criteria",
                Direction.NORTH: "actionable steps",
            }
            ambiguities.append(f"Direction {d.value} is neglected — the prompt lacks {label.get(d, 'coverage')}.")
        return ambiguities
