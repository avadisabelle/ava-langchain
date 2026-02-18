"""
Dependency Mapper

Maps dependencies between tasks, detects cycles, and produces
a dependency-aware execution order.

This is the SOUTH (Analysis) function of PDE.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from prompt_decomposition.directional_decomposer import Direction
from prompt_decomposition.intent_extractor import SecondaryIntent


@dataclass
class DependencyNode:
    id: str
    intent_id: str
    action: str
    target: str
    direction: Direction
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    depth: int = 0
    completed: bool = False


@dataclass
class DependencyGraph:
    id: str
    nodes: Dict[str, DependencyNode]
    roots: List[str]
    leaves: List[str]
    max_depth: int
    has_cycle: bool


@dataclass
class ExecutionOrder:
    layers: List[List[DependencyNode]]
    total_steps: int
    critical_path: List[str]


class DependencyMapper:
    """Builds dependency graphs from intents and computes execution order."""

    def build_graph(
        self,
        intents: List[SecondaryIntent],
        direction_map: Optional[Dict[str, Direction]] = None,
    ) -> DependencyGraph:
        graph_id = str(uuid.uuid4())
        nodes: Dict[str, DependencyNode] = {}

        for intent in intents:
            direction = (
                direction_map.get(intent.id, self._infer_direction(intent))
                if direction_map
                else self._infer_direction(intent)
            )
            nodes[intent.id] = DependencyNode(
                id=intent.id,
                intent_id=intent.id,
                action=intent.action,
                target=intent.target,
                direction=direction,
            )

        # Wire explicit dependencies
        for intent in intents:
            if intent.dependency and intent.dependency in nodes:
                node = nodes[intent.id]
                dep_node = nodes[intent.dependency]
                node.dependencies.append(dep_node.id)
                dep_node.dependents.append(node.id)

        # Infer structural dependencies
        self._infer_structural_dependencies(nodes)

        has_cycle = self._detect_cycle(nodes)
        if not has_cycle:
            self._calculate_depths(nodes)

        roots = [nid for nid, n in nodes.items() if not n.dependencies]
        leaves = [nid for nid, n in nodes.items() if not n.dependents]
        max_depth = max((n.depth for n in nodes.values()), default=0)

        return DependencyGraph(
            id=graph_id,
            nodes=nodes,
            roots=roots,
            leaves=leaves,
            max_depth=max_depth,
            has_cycle=has_cycle,
        )

    def compute_execution_order(self, graph: DependencyGraph) -> ExecutionOrder:
        if graph.has_cycle:
            all_nodes = list(graph.nodes.values())
            return ExecutionOrder(
                layers=[[n] for n in all_nodes],
                total_steps=len(all_nodes),
                critical_path=[n.id for n in all_nodes],
            )

        layers: List[List[DependencyNode]] = []
        visited: Set[str] = set()

        for depth in range(graph.max_depth + 1):
            layer = [
                n for n in graph.nodes.values()
                if n.depth == depth and n.id not in visited
            ]
            if layer:
                for n in layer:
                    visited.add(n.id)
                layers.append(layer)

        remaining = [n for n in graph.nodes.values() if n.id not in visited]
        if remaining:
            layers.append(remaining)

        critical_path = self._find_critical_path(graph)

        return ExecutionOrder(
            layers=layers,
            total_steps=len(layers),
            critical_path=critical_path,
        )

    def _infer_direction(self, intent: SecondaryIntent) -> Direction:
        action = intent.action.lower()
        if action in ("investigate", "research", "explore", "study", "analyze"):
            return Direction.SOUTH
        if action in ("test", "verify", "validate", "review", "check"):
            return Direction.WEST
        if action in ("create", "build", "implement", "add", "deploy", "install", "modify", "use", "run"):
            return Direction.NORTH
        if action in ("draft", "plan", "design", "manage"):
            return Direction.EAST
        return Direction.NORTH

    def _infer_structural_dependencies(self, nodes: Dict[str, DependencyNode]) -> None:
        node_list = list(nodes.values())
        south_nodes = [n for n in node_list if n.direction == Direction.SOUTH]
        north_nodes = [n for n in node_list if n.direction == Direction.NORTH]
        west_nodes = [n for n in node_list if n.direction == Direction.WEST]

        for south in south_nodes:
            for north in north_nodes:
                if (
                    self._topics_related(south.target, north.target)
                    and north.id not in [south.id]
                    and north.id not in south.dependencies
                    and south.id not in north.dependencies
                ):
                    north.dependencies.append(south.id)
                    south.dependents.append(north.id)

        for north in north_nodes:
            for west in west_nodes:
                if (
                    self._topics_related(north.target, west.target)
                    and west.id not in north.dependencies
                    and north.id not in west.dependencies
                ):
                    west.dependencies.append(north.id)
                    north.dependents.append(west.id)

    def _topics_related(self, a: str, b: str) -> bool:
        words_a = {w for w in a.lower().split() if len(w) > 3}
        words_b = {w for w in b.lower().split() if len(w) > 3}
        return len(words_a & words_b) >= 2

    def _detect_cycle(self, nodes: Dict[str, DependencyNode]) -> bool:
        visited: Set[str] = set()
        in_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            if node_id in in_stack:
                return True
            if node_id in visited:
                return False
            visited.add(node_id)
            in_stack.add(node_id)
            node = nodes.get(node_id)
            if node:
                for dep in node.dependents:
                    if dfs(dep):
                        return True
            in_stack.discard(node_id)
            return False

        return any(dfs(nid) for nid in nodes)

    def _calculate_depths(self, nodes: Dict[str, DependencyNode]) -> None:
        calculated: Set[str] = set()

        def calc_depth(node_id: str) -> int:
            if node_id in calculated:
                return nodes[node_id].depth
            node = nodes.get(node_id)
            if not node:
                return 0
            if not node.dependencies:
                node.depth = 0
                calculated.add(node_id)
                return 0
            max_dep = max(calc_depth(d) for d in node.dependencies)
            node.depth = max_dep + 1
            calculated.add(node_id)
            return node.depth

        for nid in nodes:
            calc_depth(nid)

    def _find_critical_path(self, graph: DependencyGraph) -> List[str]:
        if not graph.leaves:
            return []

        longest: List[str] = []

        def build_path(node_id: str, path: List[str]) -> None:
            nonlocal longest
            node = graph.nodes.get(node_id)
            if not node:
                return
            path = path + [node_id]
            if not node.dependencies:
                if len(path) > len(longest):
                    longest = path[:]
            else:
                for dep_id in node.dependencies:
                    build_path(dep_id, path)

        for leaf_id in graph.leaves:
            build_path(leaf_id, [])

        return list(reversed(longest))
