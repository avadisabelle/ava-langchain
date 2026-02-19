"""
Directional Decomposer

Decomposes a prompt through the Four Directions:
- EAST (Vision/Waabinong): What is being asked? Requirements clarity
- SOUTH (Analysis/Zhaawanong): What needs to be learned? Dependencies/research
- WEST (Validation/Epangishmok): What needs reflection? Testing/verification
- NORTH (Action/Kiiwedinong): What executes? Implementation steps
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class Direction(str, Enum):
    EAST = "east"
    SOUTH = "south"
    WEST = "west"
    NORTH = "north"


ALL_DIRECTIONS = [Direction.EAST, Direction.SOUTH, Direction.WEST, Direction.NORTH]

DIRECTION_NAMES: Dict[Direction, str] = {
    Direction.EAST: "Waabinong (Vision)",
    Direction.SOUTH: "Zhaawanong (Analysis)",
    Direction.WEST: "Epangishmok (Validation)",
    Direction.NORTH: "Kiiwedinong (Action)",
}

DIRECTION_QUESTIONS: Dict[Direction, str] = {
    Direction.EAST: "What is being asked?",
    Direction.SOUTH: "What needs to be learned?",
    Direction.WEST: "What needs reflection?",
    Direction.NORTH: "What executes?",
}

DIRECTION_KEYWORDS: Dict[Direction, List[str]] = {
    Direction.EAST: [
        "vision", "goal", "purpose", "intention", "want", "need", "desire",
        "dream", "imagine", "envision", "aspire", "mission", "why", "objective",
        "outcome", "result", "achieve", "create", "build", "design",
    ],
    Direction.SOUTH: [
        "learn", "research", "investigate", "understand", "study", "analyze",
        "explore", "discover", "examine", "review", "compare", "assess",
        "dependency", "require", "prerequisite", "context", "background",
        "literature", "existing", "current", "pattern",
    ],
    Direction.WEST: [
        "test", "verify", "validate", "check", "ensure", "confirm",
        "reflect", "review", "audit", "quality", "feedback", "iterate",
        "ceremony", "accountable", "responsible", "ethical", "protocol",
        "appropriate", "respectful", "consent",
    ],
    Direction.NORTH: [
        "implement", "execute", "deploy", "run", "build", "code", "script",
        "install", "configure", "setup", "create", "write", "develop",
        "ship", "launch", "deliver", "produce", "output", "generate",
        "commit", "push", "merge",
    ],
}


@dataclass
class DirectionalInsight:
    text: str
    confidence: float
    implicit: bool


@dataclass
class DirectionalAnalysis:
    id: str
    timestamp: str
    prompt: str
    directions: Dict[Direction, List[DirectionalInsight]]
    lead_direction: Direction
    neglected_directions: List[Direction]
    balance: float  # 0-1


class DirectionalDecomposer:
    """Decomposes prompts into Four Directions analysis using keyword classification."""

    def __init__(
        self,
        neglect_threshold: float = 0.1,
        balance_threshold: float = 0.5,
    ):
        self.neglect_threshold = neglect_threshold
        self.balance_threshold = balance_threshold

    def decompose(self, prompt: str) -> DirectionalAnalysis:
        analysis_id = str(uuid.uuid4())
        segments = self._split_into_segments(prompt)
        directions: Dict[Direction, List[DirectionalInsight]] = {
            d: [] for d in ALL_DIRECTIONS
        }

        for segment in segments:
            scores = self._score_segment(segment)
            top_dir = self._get_top_direction(scores)
            is_implicit = scores[top_dir] < 0.3

            directions[top_dir].append(DirectionalInsight(
                text=segment.strip(),
                confidence=min(scores[top_dir] * 2, 1.0),
                implicit=is_implicit,
            ))

            # Cross-classify strong secondary signals
            for d in ALL_DIRECTIONS:
                if d != top_dir and scores[d] > 0.2:
                    directions[d].append(DirectionalInsight(
                        text=segment.strip(),
                        confidence=scores[d],
                        implicit=True,
                    ))

        # Calculate balance
        counts = [len(directions[d]) for d in ALL_DIRECTIONS]
        total = sum(counts) or 1
        proportions = [c / total for c in counts]
        deviation = sum(abs(p - 0.25) for p in proportions) / 4
        balance = max(0.0, min(1.0, 1.0 - deviation * 4))

        max_count = max(counts)
        lead_direction = ALL_DIRECTIONS[counts.index(max_count)]
        neglected = [
            d for d in ALL_DIRECTIONS
            if len(directions[d]) / total < self.neglect_threshold
        ]

        return DirectionalAnalysis(
            id=analysis_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt=prompt,
            directions=directions,
            lead_direction=lead_direction,
            neglected_directions=neglected,
            balance=balance,
        )

    def is_balanced(self, analysis: DirectionalAnalysis) -> bool:
        return analysis.balance >= self.balance_threshold

    def get_guidance(self, analysis: DirectionalAnalysis) -> List[str]:
        guidance: List[str] = []
        for d in analysis.neglected_directions:
            guidance.append(
                f"{DIRECTION_NAMES[d]}: {DIRECTION_QUESTIONS[d]} "
                "Consider what is missing from this perspective."
            )
        if analysis.balance < self.balance_threshold:
            guidance.append(
                f"Overall balance is {analysis.balance * 100:.0f}% — "
                "consider addressing all four directions before proceeding."
            )
        return guidance

    def _split_into_segments(self, text: str) -> List[str]:
        parts = re.split(r'(?<=[.!?])\s+|\n+', text)
        return [s.strip() for s in parts if len(s.strip()) > 3]

    def _score_segment(self, segment: str) -> Dict[Direction, float]:
        lower = segment.lower()
        words = lower.split()
        scores: Dict[Direction, float] = {d: 0.0 for d in ALL_DIRECTIONS}

        for d in ALL_DIRECTIONS:
            for kw in DIRECTION_KEYWORDS[d]:
                for word in words:
                    if kw in word:
                        scores[d] += 1.0

        total = sum(scores.values()) or 1.0
        return {d: scores[d] / total for d in ALL_DIRECTIONS}

    def _get_top_direction(self, scores: Dict[Direction, float]) -> Direction:
        return max(ALL_DIRECTIONS, key=lambda d: scores[d])
