"""
Intent Extractor

Extracts primary and secondary intents from a prompt following PDE structure:
- Primary: single action-target-urgency-confidence tuple
- Secondary: multiple action items with dependency mapping and confidence
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Urgency(str, Enum):
    IMMEDIATE = "immediate"
    SESSION = "session"
    SPRINT = "sprint"
    ONGOING = "ongoing"


@dataclass
class PrimaryIntent:
    action: str
    target: str
    urgency: Urgency
    confidence: float


@dataclass
class SecondaryIntent:
    id: str
    action: str
    target: str
    implicit: bool
    dependency: Optional[str]  # ID of another secondary intent
    confidence: float


@dataclass
class ExtractionContext:
    files_needed: List[str]
    tools_required: List[str]
    assumptions: List[str]


@dataclass
class IntentExtractionResult:
    id: str
    timestamp: str
    prompt: str
    primary: PrimaryIntent
    secondary: List[SecondaryIntent]
    context: ExtractionContext


ACTION_VERBS: Dict[str, List[str]] = {
    "create": ["create", "build", "make", "generate", "write", "develop", "design", "scaffold", "initialize", "init"],
    "modify": ["modify", "update", "change", "edit", "adjust", "refactor", "rename", "move", "restructure"],
    "investigate": ["investigate", "research", "explore", "understand", "learn", "study", "analyze", "examine", "look", "check", "review", "see"],
    "add": ["add", "install", "include", "import", "integrate", "connect", "wire", "attach", "link"],
    "remove": ["remove", "delete", "clean", "prune", "drop", "uninstall"],
    "test": ["test", "verify", "validate", "ensure", "confirm", "check", "assert"],
    "deploy": ["deploy", "ship", "publish", "release", "push", "launch"],
    "manage": ["manage", "organize", "coordinate", "orchestrate", "maintain", "handle"],
    "use": ["use", "leverage", "utilize", "employ", "apply", "run", "execute"],
    "draft": ["draft", "outline", "plan", "sketch", "propose", "document"],
}

URGENCY_KEYWORDS: Dict[Urgency, List[str]] = {
    Urgency.IMMEDIATE: ["now", "immediately", "urgent", "asap", "right away", "quickly"],
    Urgency.SESSION: ["today", "this session", "let's", "get to work", "start"],
    Urgency.SPRINT: ["this week", "sprint", "soon", "next", "upcoming"],
    Urgency.ONGOING: ["eventually", "someday", "long-term", "future", "ongoing", "continuous"],
}


class IntentExtractor:
    """Extracts primary + secondary intents from a prompt."""

    def __init__(
        self,
        extract_implicit: bool = True,
        map_dependencies: bool = True,
    ):
        self.extract_implicit = extract_implicit
        self.map_dependencies = map_dependencies

    def extract(self, prompt: str) -> IntentExtractionResult:
        result_id = str(uuid.uuid4())
        sentences = self._split_sentences(prompt)
        raw_intents = self._extract_raw_intents(sentences)

        primary = self._determine_primary(raw_intents, prompt)
        secondary = self._build_secondary_intents(raw_intents)
        context = self._extract_context(prompt)

        return IntentExtractionResult(
            id=result_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt=prompt,
            primary=primary,
            secondary=secondary,
            context=context,
        )

    def _split_sentences(self, text: str) -> List[str]:
        parts = re.split(r'(?<=[.!?])\s+|\n+|;\s+', text)
        return [s.strip() for s in parts if len(s.strip()) > 5]

    def _extract_raw_intents(
        self, sentences: List[str]
    ) -> List[Dict]:
        intents: List[Dict] = []

        for sentence in sentences:
            lower = sentence.lower()
            best_action = ""
            best_category = ""
            found = False

            for category, verbs in ACTION_VERBS.items():
                for verb in verbs:
                    if verb in lower:
                        if not found or len(verb) > len(best_action):
                            best_action = verb
                            best_category = category
                            found = True

            if found:
                verb_idx = lower.index(best_action)
                after_verb = sentence[verb_idx + len(best_action):].strip()
                target = re.sub(r'^(the|a|an|this|that|our|your)\s+', '', after_verb, flags=re.IGNORECASE).strip()

                intents.append({
                    "action": best_category,
                    "target": target or sentence,
                    "confidence": self._calculate_confidence(sentence, best_action),
                    "implicit": False,
                    "sentence": sentence,
                })

        if self.extract_implicit:
            intents.extend(self._find_implicit_intents(sentences, intents))

        return intents

    def _find_implicit_intents(
        self, sentences: List[str], explicit: List[Dict]
    ) -> List[Dict]:
        implicit: List[Dict] = []
        explicit_sentences = {i["sentence"] for i in explicit}

        for sentence in sentences:
            lower = sentence.lower()
            if "which" in lower and sentence not in explicit_sentences:
                implicit.append({
                    "action": "investigate",
                    "target": sentence,
                    "confidence": 0.6,
                    "implicit": True,
                    "sentence": sentence,
                })

        for sentence in sentences:
            lower = sentence.lower()
            if (lower.startswith("if ") or " if " in lower or "when " in lower) and sentence not in explicit_sentences:
                implicit.append({
                    "action": "test",
                    "target": sentence,
                    "confidence": 0.5,
                    "implicit": True,
                    "sentence": sentence,
                })

        return implicit

    def _determine_primary(self, raw_intents: List[Dict], prompt: str) -> PrimaryIntent:
        if not raw_intents:
            return PrimaryIntent(
                action="investigate",
                target=prompt[:100],
                urgency=self._detect_urgency(prompt),
                confidence=0.5,
            )

        sorted_intents = sorted(raw_intents, key=lambda x: x["confidence"], reverse=True)
        top = sorted_intents[0]

        return PrimaryIntent(
            action=top["action"],
            target=top["target"][:200],
            urgency=self._detect_urgency(prompt),
            confidence=top["confidence"],
        )

    def _build_secondary_intents(self, raw_intents: List[Dict]) -> List[SecondaryIntent]:
        secondaries = [
            SecondaryIntent(
                id=str(uuid.uuid4()),
                action=raw["action"],
                target=raw["target"][:300],
                implicit=raw["implicit"],
                dependency=None,
                confidence=raw["confidence"],
            )
            for raw in raw_intents
        ]

        if self.map_dependencies and len(secondaries) > 1:
            self._infer_dependencies(secondaries)

        return secondaries

    def _infer_dependencies(self, intents: List[SecondaryIntent]) -> None:
        investigations = [i for i in intents if i.action == "investigate"]
        creations = [i for i in intents if i.action in ("create", "add", "modify")]
        tests = [i for i in intents if i.action == "test"]
        deploys = [i for i in intents if i.action == "deploy"]

        for creation in creations:
            for inv in investigations:
                if self._targets_overlap(inv.target, creation.target):
                    creation.dependency = inv.id
                    break

        for test in tests:
            for creation in creations:
                if self._targets_overlap(creation.target, test.target):
                    test.dependency = creation.id
                    break

        for deploy in deploys:
            if tests:
                deploy.dependency = tests[-1].id
            elif creations:
                deploy.dependency = creations[-1].id

    def _targets_overlap(self, a: str, b: str) -> bool:
        words_a = {w for w in a.lower().split() if len(w) > 3}
        words_b = {w for w in b.lower().split() if len(w) > 3}
        return len(words_a & words_b) >= 1

    def _detect_urgency(self, prompt: str) -> Urgency:
        lower = prompt.lower()
        for urgency, keywords in URGENCY_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    return urgency
        return Urgency.SESSION

    def _calculate_confidence(self, sentence: str, verb: str) -> float:
        lower = sentence.lower()
        confidence = 0.7

        if lower.startswith(verb):
            confidence += 0.15
        if re.search(r'/[a-z]', lower) or re.search(r'@[a-z]', lower):
            confidence += 0.1
        if re.search(r'maybe|perhaps|could|might|possibly', lower):
            confidence -= 0.2

        return max(0.1, min(1.0, confidence))

    def _extract_context(self, prompt: str) -> ExtractionContext:
        files_needed: List[str] = []
        tools_required: List[str] = []

        path_matches = re.findall(r'(?:/[\w.-]+)+/?', prompt)
        files_needed.extend(set(path_matches))

        at_refs = re.findall(r'@[\w./-]+', prompt)
        files_needed.extend(r[1:] for r in at_refs)

        tool_matches = re.findall(r'(?:mcp|tool|use)\s+(\S+)', prompt, re.IGNORECASE)
        tools_required.extend(tool_matches)

        return ExtractionContext(
            files_needed=files_needed,
            tools_required=tools_required,
            assumptions=[],
        )
