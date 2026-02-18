"""Tests for langchain-prompt-decomposition - full parity with JS tests."""

import json
import pytest

from prompt_decomposition import (
    Direction,
    ALL_DIRECTIONS,
    DIRECTION_NAMES,
    DIRECTION_QUESTIONS,
    DirectionalDecomposer,
    IntentExtractor,
    Urgency,
    DependencyMapper,
    ActionStackBuilder,
    MedicineWheelBridge,
    WheelQuadrant,
    DIRECTION_TO_QUADRANT,
    ONTOLOGY_CORE_MAP,
    PACKAGE_MAPPING,
    action_to_narrative_beat,
    decompose,
)


# =============================================================================
# DirectionalDecomposer
# =============================================================================

class TestDirectionalDecomposer:
    def setup_method(self):
        self.decomposer = DirectionalDecomposer()

    def test_decompose_produces_valid_analysis(self):
        result = self.decomposer.decompose(
            "Research the existing patterns. Build the implementation. Test the results."
        )
        assert result.id
        assert result.timestamp
        assert "Research" in result.prompt
        for d in ALL_DIRECTIONS:
            assert d in result.directions

    def test_classifies_research_to_south(self):
        result = self.decomposer.decompose(
            "Research the existing codebase and analyze the patterns used."
        )
        assert len(result.directions[Direction.SOUTH]) > 0

    def test_classifies_build_to_north(self):
        result = self.decomposer.decompose(
            "Build the new package and implement the core modules."
        )
        assert len(result.directions[Direction.NORTH]) > 0

    def test_classifies_test_to_west(self):
        result = self.decomposer.decompose(
            "Test the results and verify the integration works correctly."
        )
        assert len(result.directions[Direction.WEST]) > 0

    def test_classifies_vision_to_east(self):
        result = self.decomposer.decompose(
            "Our vision is to create a system that aspires to embody relational knowing."
        )
        assert len(result.directions[Direction.EAST]) > 0

    def test_detects_neglected_directions(self):
        result = self.decomposer.decompose(
            "Build it. Deploy it. Ship it now. Execute the plan immediately."
        )
        assert result.lead_direction == Direction.NORTH
        assert len(result.neglected_directions) > 0

    def test_calculates_balance(self):
        result = self.decomposer.decompose(
            "Research the context. Build the implementation. Test the results. Envision the purpose."
        )
        assert 0 <= result.balance <= 1

    def test_is_balanced_returns_false_for_unbalanced(self):
        result = self.decomposer.decompose("Build build build deploy code.")
        assert not self.decomposer.is_balanced(result)

    def test_get_guidance_provides_help(self):
        result = self.decomposer.decompose("Build deploy implement code now.")
        guidance = self.decomposer.get_guidance(result)
        assert len(guidance) > 0

    def test_direction_constants_complete(self):
        for d in ALL_DIRECTIONS:
            assert d in DIRECTION_NAMES
            assert d in DIRECTION_QUESTIONS


# =============================================================================
# IntentExtractor
# =============================================================================

class TestIntentExtractor:
    def setup_method(self):
        self.extractor = IntentExtractor()

    def test_extracts_primary_intent(self):
        result = self.extractor.extract(
            "Create a new package for prompt decomposition."
        )
        assert result.primary.action == "create"
        assert result.primary.confidence > 0

    def test_extracts_secondary_intents(self):
        result = self.extractor.extract(
            "Research the existing patterns. Build the implementation. Test the results."
        )
        assert len(result.secondary) > 0

    def test_detects_immediate_urgency(self):
        result = self.extractor.extract("Fix this immediately!")
        assert result.primary.urgency == Urgency.IMMEDIATE

    def test_detects_session_urgency(self):
        result = self.extractor.extract("Let's build a new package today.")
        assert result.primary.urgency == Urgency.SESSION

    def test_extracts_file_paths(self):
        result = self.extractor.extract(
            "Check /src/mcp-pde/ and build a new module."
        )
        assert "/src/mcp-pde/" in result.context.files_needed

    def test_extracts_at_references(self):
        result = self.extractor.extract(
            "Use @ava-langchainjs/libs/ to build the package."
        )
        assert any("ava-langchainjs" in f for f in result.context.files_needed)

    def test_unique_secondary_ids(self):
        result = self.extractor.extract(
            "Create module A. Build module B. Test module C."
        )
        ids = [s.id for s in result.secondary]
        assert len(set(ids)) == len(ids)

    def test_maps_dependencies(self):
        result = self.extractor.extract(
            "Investigate the git submodule patterns. Create scripts mimicking those patterns."
        )
        investigate = next((s for s in result.secondary if s.action == "investigate"), None)
        create = next((s for s in result.secondary if s.action == "create"), None)
        if investigate and create:
            assert create.dependency == investigate.id

    def test_no_implicit_when_disabled(self):
        extractor = IntentExtractor(extract_implicit=False)
        result = extractor.extract(
            "Build the system which needs proper testing."
        )
        implicit = [s for s in result.secondary if s.implicit]
        assert len(implicit) == 0

    def test_boosts_confidence_for_paths(self):
        result = self.extractor.extract(
            "Create /workspace/repos/new-package/src/index.ts module."
        )
        assert result.primary.confidence > 0.7

    def test_reduces_confidence_for_hedging(self):
        result = self.extractor.extract(
            "Maybe we could possibly create a new module."
        )
        assert result.primary.confidence < 0.8


# =============================================================================
# DependencyMapper
# =============================================================================

class TestDependencyMapper:
    def setup_method(self):
        self.mapper = DependencyMapper()
        self.extractor = IntentExtractor()

    def test_builds_graph(self):
        result = self.extractor.extract(
            "Research the patterns. Build the implementation. Test the results."
        )
        graph = self.mapper.build_graph(result.secondary)
        assert graph.id
        assert len(graph.nodes) > 0

    def test_identifies_roots(self):
        result = self.extractor.extract(
            "Investigate the codebase. Create the module."
        )
        graph = self.mapper.build_graph(result.secondary)
        assert len(graph.roots) > 0

    def test_no_cycles_in_simple_graph(self):
        result = self.extractor.extract(
            "Research first. Build second. Test third."
        )
        graph = self.mapper.build_graph(result.secondary)
        assert not graph.has_cycle

    def test_root_nodes_have_depth_zero(self):
        result = self.extractor.extract(
            "Research the patterns. Build the implementation."
        )
        graph = self.mapper.build_graph(result.secondary)
        for root_id in graph.roots:
            assert graph.nodes[root_id].depth == 0

    def test_computes_execution_layers(self):
        result = self.extractor.extract(
            "Investigate the code. Create the module. Test the module."
        )
        graph = self.mapper.build_graph(result.secondary)
        order = self.mapper.compute_execution_order(graph)
        assert len(order.layers) > 0
        assert order.total_steps > 0

    def test_parallel_tasks_in_same_layer(self):
        result = self.extractor.extract(
            "Research topic A. Research topic B. Research topic C."
        )
        graph = self.mapper.build_graph(result.secondary)
        order = self.mapper.compute_execution_order(graph)
        assert len(order.layers[0]) >= 2

    def test_computes_critical_path(self):
        result = self.extractor.extract(
            "Research the topic. Build the code. Test the code. Deploy the code."
        )
        graph = self.mapper.build_graph(result.secondary)
        order = self.mapper.compute_execution_order(graph)
        assert len(order.critical_path) > 0


# =============================================================================
# ActionStackBuilder + Pipeline
# =============================================================================

class TestActionStackBuilder:
    def setup_method(self):
        self.builder = ActionStackBuilder()
        self.decomposer = DirectionalDecomposer()
        self.extractor = IntentExtractor()
        self.mapper = DependencyMapper()

    def test_builds_complete_result(self):
        prompt = "Research the existing patterns. Build the new module. Test the integration."
        directions = self.decomposer.decompose(prompt)
        intents = self.extractor.extract(prompt)
        graph = self.mapper.build_graph(intents.secondary)
        order = self.mapper.compute_execution_order(graph)
        result = self.builder.build(directions, intents, order)

        assert result.id
        assert result.primary["action"]
        assert len(result.action_stack) > 0

    def test_produces_valid_json(self):
        prompt = "Create a package and deploy it."
        directions = self.decomposer.decompose(prompt)
        intents = self.extractor.extract(prompt)
        result = self.builder.build(directions, intents)

        json_str = self.builder.to_json(result)
        parsed = json.loads(json_str)
        assert parsed["id"] == result.id

    def test_produces_markdown(self):
        prompt = "Research. Build. Test. Vision."
        directions = self.decomposer.decompose(prompt)
        intents = self.extractor.extract(prompt)
        result = self.builder.build(directions, intents)

        md = self.builder.to_markdown(result)
        assert "Prompt Decomposition" in md
        assert "Action Stack" in md

    def test_respects_max_items(self):
        builder = ActionStackBuilder(max_items=2)
        prompt = "Create A. Build B. Test C. Deploy D. Research E."
        directions = self.decomposer.decompose(prompt)
        intents = self.extractor.extract(prompt)
        result = builder.build(directions, intents)
        assert len(result.action_stack) <= 2


class TestMedicineWheelBridge:
    def setup_method(self):
        self.bridge = MedicineWheelBridge()
        self.decomposer = DirectionalDecomposer()

    def test_enriches_with_quadrant_presence(self):
        analysis = self.decomposer.decompose(
            "Research the context. Build the code. Test it. Envision the purpose."
        )
        enriched = self.bridge.enrich(analysis)
        assert enriched.quadrant_presence is not None
        assert 0 <= enriched.relational_coverage <= 1

    def test_flags_ceremony_when_spiritual_lacking(self):
        analysis = self.decomposer.decompose(
            "Build code. Deploy code. Ship it now. Execute."
        )
        enriched = self.bridge.enrich(analysis)
        assert enriched.ceremony_required is True

    def test_provides_relational_guidance(self):
        analysis = self.decomposer.decompose("Build deploy ship execute.")
        guidance = self.bridge.get_relational_guidance(analysis)
        assert len(guidance) > 0
        assert any("Ceremony Required" in g for g in guidance)


class TestPipeline:
    def test_full_pipeline(self):
        result = decompose(
            "Investigate the existing codebase patterns. Design a new relational intelligence module. "
            "Build and test the implementation. Ensure ceremonial protocols are respected."
        )
        assert result["decomposition"] is not None
        assert result["wheel_enriched"] is not None
        assert result["json"]
        assert result["markdown"]
        assert len(result["decomposition"].action_stack) > 0

    def test_produces_parseable_json(self):
        result = decompose("Create a knowledge graph with ceremony.")
        parsed = json.loads(result["json"])
        assert "id" in parsed
        assert "result" in parsed


class TestV0OntologyBridge:
    def test_ontology_core_map_complete(self):
        for d in ALL_DIRECTIONS:
            assert d in ONTOLOGY_CORE_MAP
            concept = ONTOLOGY_CORE_MAP[d]
            assert concept.indigenous_name
            assert concept.act in (1, 2, 3, 4)

    def test_action_to_narrative_beat(self):
        beat = action_to_narrative_beat(
            action_id="test-123",
            text="Build the module",
            direction=Direction.NORTH,
            confidence=0.9,
            implicit=False,
        )
        assert beat.act == 4
        assert beat.direction == Direction.NORTH

    def test_package_mapping_complete(self):
        assert len(PACKAGE_MAPPING) == 5
        for key in PACKAGE_MAPPING:
            assert "existing_packages" in PACKAGE_MAPPING[key]

    def test_direction_quadrant_mapping(self):
        assert DIRECTION_TO_QUADRANT[Direction.EAST] == WheelQuadrant.SPIRITUAL
        assert DIRECTION_TO_QUADRANT[Direction.SOUTH] == WheelQuadrant.MENTAL
        assert DIRECTION_TO_QUADRANT[Direction.WEST] == WheelQuadrant.EMOTIONAL
        assert DIRECTION_TO_QUADRANT[Direction.NORTH] == WheelQuadrant.PHYSICAL
