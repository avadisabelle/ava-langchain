"""Advanced Langfuse integration examples for LangChain.

This module demonstrates sophisticated usage patterns for the
CoaiapyLangfuseCallbackHandler, including:
- Custom trace naming
- Rich metadata and tags
- Nested chain execution
- Error handling and recovery
- Manual trace management
- Chat model integration
"""

import asyncio
import os
from typing import Dict, List

from langchain_core.callbacks import CoaiapyLangfuseCallbackHandler
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: Custom Trace Naming and Metadata
# ═══════════════════════════════════════════════════════════════════════════════


def example_custom_trace_naming():
    """Demonstrate custom trace naming and rich metadata."""
    print("\n" + "="*80)
    print("📋 EXAMPLE 1: Custom Trace Naming and Metadata")
    print("="*80)

    # Create handler with custom trace name
    handler = CoaiapyLangfuseCallbackHandler(
        session_id="advanced-examples-session",
        trace_name="🎯 Data Processing Pipeline",
    )

    def validate_data(data: Dict) -> Dict:
        """Validate input data."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        return {**data, "validated": True}

    def enrich_data(data: Dict) -> Dict:
        """Enrich data with additional metadata."""
        return {
            **data,
            "enriched_at": "2025-11-18",
            "enrichment_version": "v1.0",
        }

    # Create processing pipeline
    pipeline = (
        RunnableLambda(validate_data, name="DataValidator")
        | RunnableLambda(enrich_data, name="DataEnricher")
    )

    # Execute with rich metadata
    result = pipeline.invoke(
        {"user_id": "user-123", "action": "purchase"},
        config={
            "callbacks": [handler],
            "tags": ["production", "data-pipeline", "user-123"],
            "metadata": {
                "environment": "production",
                "request_id": "req-456",
                "version": "v2.1.0",
                "customer_tier": "premium",
            },
        },
    )

    print(f"✅ Pipeline result: {result}")
    print("📊 Check Langfuse for trace: '🎯 Data Processing Pipeline'")
    print(f"   - Tags: production, data-pipeline, user-123")
    print(f"   - Metadata: environment, request_id, version, customer_tier")

    handler.flush()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: Nested Chain Execution with Hierarchy
# ═══════════════════════════════════════════════════════════════════════════════


def example_nested_chains():
    """Demonstrate hierarchical observation structure with nested chains."""
    print("\n" + "="*80)
    print("🔗 EXAMPLE 2: Nested Chain Execution")
    print("="*80)

    handler = CoaiapyLangfuseCallbackHandler(
        trace_name="🔗 Nested Processing Chain",
        trace_id="nested-chain-example",
    )

    # Inner chain 1: Text preprocessing
    def lowercase(text: str) -> str:
        return text.lower()

    def remove_punctuation(text: str) -> str:
        return "".join(c for c in text if c.isalnum() or c.isspace())

    preprocess_chain = (
        RunnableLambda(lowercase, name="Lowercase")
        | RunnableLambda(remove_punctuation, name="RemovePunctuation")
    )

    # Inner chain 2: Text analysis
    def count_words(text: str) -> Dict:
        words = text.split()
        return {"word_count": len(words), "text": text}

    def analyze_length(data: Dict) -> Dict:
        return {
            **data,
            "is_long": data["word_count"] > 5,
        }

    analysis_chain = (
        RunnableLambda(count_words, name="WordCounter")
        | RunnableLambda(analyze_length, name="LengthAnalyzer")
    )

    # Outer chain: Complete pipeline
    complete_pipeline = preprocess_chain | analysis_chain

    # Execute nested chain
    result = complete_pipeline.invoke(
        "Hello, World! This is a TEST.",
        config={"callbacks": [handler], "tags": ["text-processing"]},
    )

    print(f"✅ Analysis result: {result}")
    print("📊 Check Langfuse for hierarchical structure:")
    print("   🔗 Nested Processing Chain (trace)")
    print("     └─ 🔗 RunnableSequence (parent chain)")
    print("        ├─ 🔗 Lowercase")
    print("        ├─ 🔗 RemovePunctuation")
    print("        ├─ 🔗 WordCounter")
    print("        └─ 🔗 LengthAnalyzer")

    handler.flush()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: Error Handling and Recovery
# ═══════════════════════════════════════════════════════════════════════════════


def example_error_handling():
    """Demonstrate error tracking and recovery patterns."""
    print("\n" + "="*80)
    print("⚠️  EXAMPLE 3: Error Handling and Recovery")
    print("="*80)

    handler = CoaiapyLangfuseCallbackHandler(
        trace_name="🔧 Error Handling Demo",
    )

    def risky_operation(value: int) -> int:
        """Operation that might fail."""
        if value < 0:
            raise ValueError(f"Negative value not allowed: {value}")
        if value > 100:
            raise ValueError(f"Value too large: {value}")
        return value * 2

    def safe_fallback(value: int) -> int:
        """Fallback operation."""
        return abs(value)  # Always returns positive

    risky_chain = RunnableLambda(risky_operation, name="RiskyOperation")
    safe_chain = RunnableLambda(safe_fallback, name="SafeFallback")

    # Test 1: Successful execution
    print("\n  Test 1: Valid input (50)")
    try:
        result = risky_chain.invoke(
            50,
            config={
                "callbacks": [handler],
                "tags": ["test-1", "success-case"],
                "metadata": {"test_type": "valid_input"},
            },
        )
        print(f"  ✅ Success: {result}")
    except ValueError as e:
        print(f"  ❌ Error: {e}")

    # Test 2: Error case (captured in Langfuse)
    print("\n  Test 2: Invalid input (-10) - will error")
    try:
        result = risky_chain.invoke(
            -10,
            config={
                "callbacks": [handler],
                "tags": ["test-2", "error-case"],
                "metadata": {"test_type": "negative_input"},
            },
        )
        print(f"  ✅ Success: {result}")
    except ValueError as e:
        print(f"  ✅ Error captured: {e}")
        print("     (Check Langfuse for ERROR observation)")

    # Test 3: Recovery with fallback
    print("\n  Test 3: Error recovery with fallback")
    try:
        # Try risky operation
        result = risky_chain.invoke(150, config={"callbacks": [handler]})
    except ValueError:
        # Fall back to safe operation
        result = safe_chain.invoke(
            150,
            config={
                "callbacks": [handler],
                "tags": ["test-3", "recovery"],
                "metadata": {"fallback": True},
            },
        )
        print(f"  ✅ Recovered with fallback: {result}")

    print("\n📊 Check Langfuse for:")
    print("   - SUCCESS observation for test 1")
    print("   - ERROR observation for test 2 (level=ERROR)")
    print("   - SUCCESS observation for test 3 recovery")

    handler.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 4: Async Operations
# ═══════════════════════════════════════════════════════════════════════════════


async def example_async_operations():
    """Demonstrate async operation tracing."""
    print("\n" + "="*80)
    print("⚡ EXAMPLE 4: Async Operations")
    print("="*80)

    handler = CoaiapyLangfuseCallbackHandler(
        trace_name="⚡ Async Processing Pipeline",
    )

    async def async_fetch_data(query: str) -> Dict:
        """Simulate async data fetching."""
        await asyncio.sleep(0.01)  # Simulate I/O
        return {"query": query, "results": [f"result_{i}" for i in range(3)]}

    async def async_process_results(data: Dict) -> Dict:
        """Simulate async processing."""
        await asyncio.sleep(0.01)  # Simulate processing
        return {
            **data,
            "processed": True,
            "result_count": len(data["results"]),
        }

    # Create async pipeline
    async_pipeline = (
        RunnableLambda(async_fetch_data, name="AsyncFetcher")
        | RunnableLambda(async_process_results, name="AsyncProcessor")
    )

    # Execute async pipeline
    result = await async_pipeline.ainvoke(
        "machine learning",
        config={
            "callbacks": [handler],
            "tags": ["async", "data-fetching"],
            "metadata": {"execution_mode": "async"},
        },
    )

    print(f"✅ Async result: {result}")
    print("📊 Check Langfuse for async trace with:")
    print("   - AsyncFetcher observation")
    print("   - AsyncProcessor observation")
    print("   - execution_mode: async in metadata")

    handler.flush()
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE 5: Conditional Flushing
# ═══════════════════════════════════════════════════════════════════════════════


def example_conditional_flushing():
    """Demonstrate manual flush control for batching."""
    print("\n" + "="*80)
    print("💾 EXAMPLE 5: Conditional Flushing")
    print("="*80)

    # Create handler with auto-flush disabled
    handler = CoaiapyLangfuseCallbackHandler(
        trace_name="💾 Batch Processing",
        flush_on_exit=False,  # Disable automatic flushing
    )

    def process_item(item: int) -> int:
        return item * 2

    chain = RunnableLambda(process_item, name="ItemProcessor")

    print("  Processing 5 items (no auto-flush)...")
    results = []
    for i in range(5):
        result = chain.invoke(
            i,
            config={
                "callbacks": [handler],
                "tags": [f"batch-item-{i}"],
            },
        )
        results.append(result)
        print(f"    ✅ Processed item {i}: {result}")

    print("\n  ⏸️  Traces buffered in memory (not yet sent)")
    print("  💾 Manually flushing now...")
    handler.flush()
    print("  ✅ All 5 traces sent to Langfuse in one batch")

    print("\n📊 Benefits of manual flushing:")
    print("   - Reduced network overhead (batch API calls)")
    print("   - Better control over trace lifecycle")
    print("   - Useful for high-throughput scenarios")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    """Run all advanced examples."""
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "ADVANCED LANGFUSE EXAMPLES" + " "*32 + "║")
    print("╚" + "="*78 + "╝")

    # Set dummy credentials for examples (replace with real ones)
    os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-test")

    try:
        # Run sync examples
        example_custom_trace_naming()
        example_nested_chains()
        example_error_handling()
        example_conditional_flushing()

        # Run async example
        print("\n  Running async example...")
        asyncio.run(example_async_operations())

        print("\n" + "="*80)
        print("🎉 ALL ADVANCED EXAMPLES COMPLETED")
        print("="*80)
        print("\n📊 Summary:")
        print("   - Example 1: Custom trace naming and metadata")
        print("   - Example 2: Nested chain hierarchies")
        print("   - Example 3: Error handling and recovery")
        print("   - Example 4: Async operations")
        print("   - Example 5: Manual flush control")
        print("\n⚠️  Remember: Wait 20 seconds before querying session views!")

    except ImportError as e:
        print(f"\n❌ ImportError: {e}")
        print("Please ensure langfuse is installed: pip install langfuse")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
