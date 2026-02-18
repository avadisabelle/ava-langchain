"""Tests for the LangChain Runnable wrappers."""

import pytest
from prompt_decomposition.runnable import (
    RunnableDecomposer,
    RunnableDirectionalAnalyzer,
    RunnableWheelGate,
)


class TestRunnableDecomposer:
    def test_invoke_basic(self):
        decomposer = RunnableDecomposer()
        result = decomposer.invoke(
            "Research the codebase. Build the module. Test the integration."
        )
        assert "decomposition" in result
        assert "wheelEnriched" in result
        assert "json" in result
        assert "markdown" in result
        assert isinstance(result["ceremonyRequired"], bool)
        assert isinstance(result["balance"], float)
        assert result["actionCount"] > 0

    def test_batch(self):
        decomposer = RunnableDecomposer()
        results = decomposer.batch([
            "Build a module.",
            "Research the topic.",
        ])
        assert len(results) == 2
        assert results[0]["primaryAction"] is not None
        assert results[1]["primaryAction"] is not None

    def test_custom_options(self):
        decomposer = RunnableDecomposer(options={"actionStack": {"maxItems": 2}})
        result = decomposer.invoke(
            "Create A. Build B. Test C. Deploy D. Research E."
        )
        assert len(result["decomposition"]["actionStack"]) <= 2

    def test_primary_action_present(self):
        decomposer = RunnableDecomposer()
        result = decomposer.invoke("Build a knowledge graph for ceremonies.")
        assert result["primaryAction"] is not None


class TestRunnableDirectionalAnalyzer:
    def test_analyze(self):
        analyzer = RunnableDirectionalAnalyzer()
        result = analyzer.invoke(
            "Research the patterns and build the implementation."
        )
        assert "directions" in result
        assert "leadDirection" in result
        assert "balance" in result
        assert result["balance"] >= 0.0
        assert result["balance"] <= 1.0

    def test_lead_direction(self):
        analyzer = RunnableDirectionalAnalyzer()
        result = analyzer.invoke("Build deploy ship execute now.")
        assert result["leadDirection"] in ("EAST", "SOUTH", "WEST", "NORTH")


class TestRunnableWheelGate:
    def test_imbalanced(self):
        gate = RunnableWheelGate()
        result = gate.invoke("Build deploy ship execute now.")
        assert result["ceremonyRequired"] is True
        assert len(result["guidance"]) > 0

    def test_has_coverage(self):
        gate = RunnableWheelGate()
        result = gate.invoke(
            "Envision the purpose. Research the patterns. Verify the approach. Build the module."
        )
        assert "relationalCoverage" in result
        assert result["relationalCoverage"] >= 0.0

    def test_missing_directions(self):
        gate = RunnableWheelGate()
        result = gate.invoke("Build deploy ship execute now.")
        assert isinstance(result["missingDirections"], list)
