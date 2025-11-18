import asyncio
import os
import uuid
from langchain_core.runnables import RunnableLambda
from langchain_core.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List, Optional, Union

# Import the CoaiapyLangfuseCallbackHandler and the (placeholder) coaia_fuse functions
from langchain_core.callbacks.langfuse_handler import (
    CoaiapyLangfuseCallbackHandler,
    coaia_fuse_trace_create,
    coaia_fuse_add_observation
)

# Create an instance of the callback handler
my_coaiapy_handler = CoaiapyLangfuseCallbackHandler(
    session_id=str(uuid.uuid4()),
    trace_id=str(uuid.uuid4())
)

# Define callback config to directly use the handler
callback_config = {"callbacks": [my_coaiapy_handler]}

def add_one(x: int) -> int:
    return x + 1

def multiply_by_two(x: int) -> int:
    return x * 2

# Create a simple runnable sequence
sequence = RunnableLambda(add_one, name="AddOne") | RunnableLambda(multiply_by_two, name="MultiplyByTwo")

print(f"Running sequence with input 5. Check console output for Coaiapy trace messages.")

# Invoke the sequence with the callback config
result = sequence.invoke(5, config=callback_config)

print(f"Sequence result: {result}")

# Now, let's try an async version
async def async_add_one(x: int) -> int:
    await asyncio.sleep(0.01) # Simulate async work
    return x + 1

async def async_multiply_by_two(x: int) -> int:
    await asyncio.sleep(0.01) # Simulate async work
    return x * 2

async_sequence = RunnableLambda(async_add_one, name="AsyncAddOne") | RunnableLambda(async_multiply_by_two, name="AsyncMultiplyByTwo")

print(f"\nRunning async sequence with input 10. Check console output for Coaiapy trace messages.")

async_result = asyncio.run(async_sequence.ainvoke(10, config=callback_config))

print(f"Async sequence result: {async_result}")

# Test with an error
def error_func(x: int) -> int:
    if x == 7:
        raise ValueError("Error on 7!")
    return x

error_sequence = RunnableLambda(error_func, name="ErrorFunc")

print(f"\nRunning error sequence with input 7. Expect an error trace message.")
try:
    error_sequence.invoke(7, config=callback_config)
except ValueError as e:
    print(f"Caught expected error: {e}")

# Test with no error
print(f"\nRunning error sequence with input 8. Expect no error trace message.")
error_sequence.invoke(8, config=callback_config)
