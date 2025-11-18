"""Test script for LangChain + Langfuse integration via CoaiapyLangfuseCallbackHandler.

This script demonstrates the automatic tracing of LangChain runnables to Langfuse,
including sync and async operations, error handling, and hierarchical trace structures.
"""

import asyncio
import os
import uuid
from langchain_core.runnables import RunnableLambda
from langchain_core.callbacks.langfuse_handler import CoaiapyLangfuseCallbackHandler

# Set environment variables for testing
# NOTE: Replace these with your actual Langfuse credentials
os.environ["LANGFUSE_PUBLIC_KEY"] = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
os.environ["LANGFUSE_SECRET_KEY"] = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
os.environ["COAIAPY_SESSION_ID"] = "a50f3fc2-eb8c-434d-a37e-ef9615d9c07d"
os.environ["COAIAPY_TRACE_ID"] = "74f9e759-66ad-4f10-bebe-331f75f0742a"

# Create an instance of the callback handler
try:
    my_coaiapy_handler = CoaiapyLangfuseCallbackHandler(
        session_id=os.environ["COAIAPY_SESSION_ID"],
        trace_id=os.environ["COAIAPY_TRACE_ID"]
    )
    print("✅ CoaiapyLangfuseCallbackHandler initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize handler: {e}")
    print("Please ensure LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set")
    exit(1)

# Define callback config to directly use the handler
callback_config = {"callbacks": [my_coaiapy_handler]}

def add_one(x: int) -> int:
    return x + 1

def multiply_by_two(x: int) -> int:
    return x * 2

# Create a simple runnable sequence
sequence = RunnableLambda(add_one, name="AddOne") | RunnableLambda(multiply_by_two, name="MultiplyByTwo")

print("\n" + "="*80)
print("🧪 TEST 1: Simple Sync Runnable Sequence")
print("="*80)
print(f"Running sequence with input 5...")

# Invoke the sequence with the callback config
result = sequence.invoke(5, config=callback_config)

print(f"✅ Sequence result: {result} (expected: 12)")
print("📊 Check Langfuse dashboard for trace observations")

# Now, let's try an async version
async def async_add_one(x: int) -> int:
    await asyncio.sleep(0.01) # Simulate async work
    return x + 1

async def async_multiply_by_two(x: int) -> int:
    await asyncio.sleep(0.01) # Simulate async work
    return x * 2

async_sequence = RunnableLambda(async_add_one, name="AsyncAddOne") | RunnableLambda(async_multiply_by_two, name="AsyncMultiplyByTwo")

print("\n" + "="*80)
print("🧪 TEST 2: Async Runnable Sequence")
print("="*80)
print(f"Running async sequence with input 10...")

async_result = asyncio.run(async_sequence.ainvoke(10, config=callback_config))

print(f"✅ Async sequence result: {async_result} (expected: 22)")
print("📊 Check Langfuse dashboard for async trace observations")

# Test with an error
def error_func(x: int) -> int:
    if x == 7:
        raise ValueError("Error on 7!")
    return x

error_sequence = RunnableLambda(error_func, name="ErrorFunc")

print("\n" + "="*80)
print("🧪 TEST 3: Error Handling")
print("="*80)
print(f"Running error sequence with input 7 (should fail)...")
try:
    error_sequence.invoke(7, config=callback_config)
except ValueError as e:
    print(f"✅ Caught expected error: {e}")
    print("📊 Check Langfuse for error observation (level=ERROR)")

# Test with no error
print(f"\nRunning error sequence with input 8 (should succeed)...")
result_8 = error_sequence.invoke(8, config=callback_config)
print(f"✅ Success result: {result_8} (expected: 8)")

print("\n" + "="*80)
print("🎉 ALL TESTS COMPLETED")
print("="*80)
print(f"Session ID: {os.environ['COAIAPY_SESSION_ID']}")
print(f"Trace ID: {os.environ['COAIAPY_TRACE_ID']}")
print("\n⚠️  IMPORTANT: Wait 20 seconds before querying traces via session view")
print("   (per llms-coaiapy-langfuse-tracing-best-practices.md)")
print("\nFlushing traces to Langfuse...")
my_coaiapy_handler.langfuse.flush()
print("✅ Flush complete. Check your Langfuse dashboard!")
