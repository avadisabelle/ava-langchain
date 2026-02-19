"""
LangChain Runnable wrappers for Prompt Decomposition Engine.

Provides RunnableDecomposer, RunnableDirectionalAnalyzer, and RunnableWheelGate
that integrate with LangChain's LCEL (LangChain Expression Language) for
chain composability.

Usage:
    from prompt_decomposition.runnable import RunnableDecomposer

    decomposer = RunnableDecomposer()
    result = decomposer.invoke("Build a module. Test it. Deploy it.")

    # Chain with other runnables
    chain = decomposer | (lambda r: r["primaryAction"])
    action = chain.invoke("Research the codebase.")
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from prompt_decomposition.pipeline import decompose
from prompt_decomposition.directional_decomposer import DirectionalDecomposer
from prompt_decomposition.wheel_bridge import MedicineWheelBridge

try:
    from langchain_core.runnables import RunnableLambda

    _HAS_LANGCHAIN = True
except ImportError:
    _HAS_LANGCHAIN = False


def _make_base_class():
    """Return RunnableLambda if available, else a minimal fallback."""
    if _HAS_LANGCHAIN:
        return RunnableLambda
    # Minimal fallback so the class works without langchain_core installed
    class _FallbackRunnable:
        def __init__(self, func):
            self._func = func

        def invoke(self, input: Any, config: Any = None) -> Any:
            return self._func(input)

        def batch(self, inputs: List[Any], config: Any = None) -> List[Any]:
            return [self.invoke(inp) for inp in inputs]

    return _FallbackRunnable


class RunnableDecomposer(_make_base_class()):
    """
    LangChain Runnable that decomposes prompts through the Four Directions.

    Accepts a string prompt and returns a dict with:
    - decomposition: full DecompositionResult
    - wheelEnriched: WheelEnrichedAnalysis
    - json: JSON string output
    - markdown: Markdown string output
    - ceremonyRequired: bool
    - balance: float (0-1)
    - primaryAction: str or None
    - actionCount: int
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None, **kwargs):
        self._options = options or {}

        def _decompose(prompt: str) -> Dict[str, Any]:
            # Map options to decompose() keyword args
            decompose_kwargs: Dict[str, Any] = {}
            action_opts = self._options.get("actionStack", {})
            wheel_opts = self._options.get("wheelBridge", {})
            if "maxItems" in action_opts:
                decompose_kwargs["max_items"] = action_opts["maxItems"]
            if "ceremonyThreshold" in wheel_opts:
                decompose_kwargs["ceremony_threshold"] = wheel_opts["ceremonyThreshold"]

            result = decompose(prompt, **decompose_kwargs)

            decomp = result["decomposition"]
            actions = decomp.action_stack
            primary = actions[0].text if actions else None

            wheel = result["wheel_enriched"]

            return {
                "decomposition": {
                    "actionStack": [
                        {"action": a.text, "direction": a.direction.value, "confidence": a.confidence}
                        for a in actions
                    ],
                    "primary": decomp.primary,
                    "secondary": decomp.secondary,
                    "balance": decomp.balance,
                },
                "wheelEnriched": {
                    "ceremonyRequired": wheel.ceremony_required,
                    "relationalCoverage": wheel.relational_coverage,
                    "quadrantPresence": wheel.quadrant_presence,
                },
                "json": result["json"],
                "markdown": result["markdown"],
                "ceremonyRequired": wheel.ceremony_required,
                "balance": wheel.relational_coverage,
                "primaryAction": primary,
                "actionCount": len(actions),
            }

        super().__init__(_decompose, **kwargs)


class RunnableDirectionalAnalyzer(_make_base_class()):
    """
    Runnable that classifies prompt segments by Four Directions.

    Returns dict with:
    - directions: dict mapping direction name to list of segments
    - leadDirection: the direction with most segments
    - balance: float 0-1 coverage score
    """

    def __init__(self, **kwargs):
        def _analyze(prompt: str) -> Dict[str, Any]:
            dd = DirectionalDecomposer()
            analysis = dd.decompose(prompt)

            dir_map: Dict[str, List[str]] = {}
            for direction, insights in analysis.directions.items():
                name = direction.value.upper()
                dir_map[name] = [ins.text for ins in insights if ins.text]

            # Lead = direction with most segments
            lead = max(dir_map, key=lambda d: len(dir_map[d])) if dir_map else "EAST"

            # Balance = how many of 4 directions are covered
            coverage = len(dir_map) / 4.0

            return {
                "directions": dir_map,
                "leadDirection": lead,
                "balance": coverage,
            }

        super().__init__(_analyze, **kwargs)


class RunnableWheelGate(_make_base_class()):
    """
    Runnable that checks directional balance and ceremony requirements.

    Returns dict with:
    - ceremonyRequired: bool
    - guidance: list of suggestions
    - relationalCoverage: float 0-1
    - missingDirections: list of direction names not covered
    """

    def __init__(self, threshold: float = 0.5, **kwargs):
        self._threshold = threshold

        def _gate(prompt: str) -> Dict[str, Any]:
            dd = DirectionalDecomposer()
            bridge = MedicineWheelBridge()

            analysis = dd.decompose(prompt)
            enriched = bridge.enrich(analysis)
            guidance_list = bridge.get_relational_guidance(analysis)

            coverage = enriched.relational_coverage
            ceremony = enriched.ceremony_required

            # Detect missing directions
            present = {
                d.value.upper()
                for d, insights in analysis.directions.items()
                if insights  # non-empty list
            }
            all_dirs = {"EAST", "SOUTH", "WEST", "NORTH"}
            missing = sorted(all_dirs - present)

            return {
                "ceremonyRequired": ceremony,
                "guidance": guidance_list,
                "relationalCoverage": coverage,
                "missingDirections": missing,
            }

        super().__init__(_gate, **kwargs)
