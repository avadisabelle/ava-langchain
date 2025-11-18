# LangChain + Langfuse Integration Guide

## Overview

This guide documents the Langfuse tracing integration for LangChain, implemented via the `CoaiapyLangfuseCallbackHandler`. This integration provides automatic, structured observability for all LangChain operations, following best practices from the Coaiapy Aetherial tracing framework.

## Quick Start

### 1. Environment Setup

Set the following environment variables:

```bash
# Langfuse Configuration
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"  # or your self-hosted instance

# Session and Trace IDs (optional)
export COAIAPY_SESSION_ID="your-session-id"
export COAIAPY_TRACE_ID="your-trace-id"  # optional: groups multiple runs

# Enable auto-injection (recommended)
export COAIAPY_TRACING_ENABLED="true"
```

### 2. Auto-Injection Mode (Recommended)

When `COAIAPY_TRACING_ENABLED=true`, tracing is **automatically enabled** for all LangChain runnables:

```python
import os
from langchain_core.runnables import RunnableLambda

# Set environment variable
os.environ["COAIAPY_TRACING_ENABLED"] = "true"

# Define your runnable - NO callback configuration needed!
def add_one(x: int) -> int:
    return x + 1

chain = RunnableLambda(add_one, name="AddOne")

# Invoke - tracing happens automatically
result = chain.invoke(5)  # ✨ Automatically traced to Langfuse!
```

### 3. Manual Handler Mode

For more control, create and configure the handler explicitly:

```python
from langchain_core.callbacks.langfuse_handler import CoaiapyLangfuseCallbackHandler
from langchain_core.runnables import RunnableLambda

# Create handler
handler = CoaiapyLangfuseCallbackHandler(
    session_id="my-session-id",
    trace_id="my-trace-id",  # optional
    public_key="pk-lf-...",  # or use env vars
    secret_key="sk-lf-...",
)

# Use handler in config
def add_one(x: int) -> int:
    return x + 1

chain = RunnableLambda(add_one, name="AddOne")

# Pass handler via config
result = chain.invoke(5, config={"callbacks": [handler]})
```

## Architecture

### Trace Hierarchy

The handler automatically creates a hierarchical structure in Langfuse:

```
🧠 LangChain Execution (Trace)
├── 🔗 MyChain (SPAN)
│   ├── 🤖 GPT-4 (GENERATION)
│   ├── 🔧 CalculatorTool (SPAN)
│   └── 📚 VectorStoreRetriever (SPAN)
└── 💬 ChatModel (GENERATION)
```

### Observation Types

- **TRACE**: Root container for an execution (created per top-level run)
- **SPAN**: For chains, tools, and retrievers
- **GENERATION**: For LLM calls (includes token usage tracking)

### Glyph Mapping

Operations are automatically tagged with visual glyphs:

| Type | Glyph | Example |
|------|-------|---------|
| LLM | 🤖 | `🤖 GPT-4` |
| Chat | 💬 | `💬 ChatOpenAI` |
| Chain | 🔗 | `🔗 SequentialChain` |
| Tool | 🔧 | `🔧 Calculator` |
| Retriever | 📚 | `📚 VectorStore` |
| Agent | 🧭 | `🧭 ReActAgent` |
| Generic | ⚙️ | `⚙️ CustomRunnable` |

## Supported Operations

### LLM Calls

```python
from langchain_core.language_models import FakeLLM

llm = FakeLLM()
result = llm.invoke("Hello!")  # Traced as GENERATION
```

**Captured Data:**
- Input: Prompts
- Output: Generated text
- Metadata: Model name, serialized config
- Usage: Token counts (prompt, completion, total)

### Chains

```python
from langchain_core.runnables import RunnableLambda

chain = RunnableLambda(lambda x: x + 1, name="Incrementer")
result = chain.invoke(5)  # Traced as SPAN
```

**Captured Data:**
- Input: Chain inputs
- Output: Chain outputs
- Metadata: Serialized chain config, tags

### Tools

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> float:
    """Calculate a mathematical expression."""
    return eval(expression)

result = calculator.invoke("2 + 2")  # Traced as SPAN
```

**Captured Data:**
- Input: Tool input string
- Output: Tool result
- Metadata: Tool name, serialized config

### Retrievers

```python
from langchain_core.retrievers import BaseRetriever

retriever = MyVectorStoreRetriever()
docs = retriever.invoke("search query")  # Traced as SPAN
```

**Captured Data:**
- Input: Query string
- Output: Retrieved documents (content + metadata), count
- Metadata: Retriever config

### Error Handling

Errors are automatically captured with ERROR level observations:

```python
def error_func(x: int) -> int:
    if x == 7:
        raise ValueError("Error on 7!")
    return x

chain = RunnableLambda(error_func)

try:
    chain.invoke(7)  # Captured as ERROR observation
except ValueError:
    pass
```

**Captured Data:**
- Status: ERROR
- Message: Exception message
- Output: Error details (type, message)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | Required |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | Required |
| `LANGFUSE_HOST` | Langfuse API host | `https://cloud.langfuse.com` |
| `COAIAPY_SESSION_ID` | Session ID for grouping traces | Auto-generated |
| `COAIAPY_TRACE_ID` | Trace ID for grouping runs | Auto-generated per run |
| `COAIAPY_TRACING_ENABLED` | Enable auto-injection | `false` |

### Handler Parameters

```python
CoaiapyLangfuseCallbackHandler(
    session_id: Optional[str] = None,       # Langfuse session ID
    trace_id: Optional[str] = None,         # Optional trace ID for grouping
    public_key: Optional[str] = None,       # Langfuse public key
    secret_key: Optional[str] = None,       # Langfuse secret key
    host: Optional[str] = None,             # Langfuse host URL
)
```

## Best Practices

### 1. The 20-Second Rule

Per `llms-coaiapy-langfuse-tracing-best-practices.md`, wait at least 20 seconds after creating traces before querying the session view, as backend indexing takes time.

```python
import time

# Create traces
chain.invoke(input_data)

# Flush immediately
handler.langfuse.flush()

# Wait for backend indexing
time.sleep(20)

# Now safe to query session view
```

### 2. Session Management

Use consistent session IDs to group related executions:

```python
SESSION_ID = "a50f3fc2-eb8c-434d-a37e-ef9615d9c07d"

handler = CoaiapyLangfuseCallbackHandler(session_id=SESSION_ID)

# All runs with this handler will be grouped in the same session
```

### 3. Trace Grouping

Use trace IDs to group multiple runs under a single trace:

```python
TRACE_ID = "74f9e759-66ad-4f10-bebe-331f75f0742a"

handler = CoaiapyLangfuseCallbackHandler(
    session_id=SESSION_ID,
    trace_id=TRACE_ID,  # All runs share this trace
)

# Multiple invocations will appear as observations under the same trace
chain.invoke(input_1)
chain.invoke(input_2)
chain.invoke(input_3)
```

### 4. Flush on Completion

Always flush pending traces before exit:

```python
try:
    # Your LangChain operations
    result = chain.invoke(data)
finally:
    # Ensure all traces are sent
    handler.langfuse.flush()
```

### 5. Rich Metadata

Add tags and metadata for better observability:

```python
result = chain.invoke(
    input_data,
    config={
        "callbacks": [handler],
        "tags": ["production", "user-123"],
        "metadata": {
            "user_id": "user-123",
            "request_id": "req-456",
            "version": "v1.2.3",
        },
    },
)
```

## Integration with Launch Script

The `LAUNCH__session_id__avaLangChainComponents_2511180702.sh` script sets up the complete environment:

```bash
#!/bin/bash
. _env.sh

export COAIAPY_TRACING_ENABLED="true"
export COAIAPY_SESSION_ID="74f9e759-66ad-4f10-bebe-331f75f0742a"
export PYTHONPATH="/home/user/ava-langchain/libs/core:${PYTHONPATH}"

# Your LangChain code will now automatically trace to Langfuse
python my_langchain_app.py
```

## Testing

Run the test suite to verify integration:

```bash
# Set credentials first
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."

# Run tests
python temp_test_tracing.py
```

Expected output:
```
✅ CoaiapyLangfuseCallbackHandler initialized successfully

================================================================================
🧪 TEST 1: Simple Sync Runnable Sequence
================================================================================
Running sequence with input 5...
✅ Sequence result: 12 (expected: 12)
📊 Check Langfuse dashboard for trace observations

[... more tests ...]

🎉 ALL TESTS COMPLETED
Session ID: a50f3fc2-eb8c-434d-a37e-ef9615d9c07d
Trace ID: 74f9e759-66ad-4f10-bebe-331f75f0742a
```

## Troubleshooting

### Handler Not Initializing

**Error:** `ImportError: Langfuse is not installed`

**Solution:** Install Langfuse:
```bash
pip install langfuse
```

### Missing Traces in Dashboard

**Cause:** Backend indexing delay

**Solution:** Wait 20 seconds after trace creation, ensure `flush()` was called

### Auto-Injection Not Working

**Cause:** `COAIAPY_TRACING_ENABLED` not set or not `"true"`

**Solution:**
```bash
export COAIAPY_TRACING_ENABLED="true"
```

### Authentication Errors

**Cause:** Invalid or missing credentials

**Solution:** Verify environment variables:
```bash
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
```

## Advanced Usage

### Custom Trace Names

Override the default trace name:

```python
# The handler creates traces with name "🧠 LangChain Execution" by default
# For custom names, directly use Langfuse SDK in combination with handler
```

### Parallel Observations

The handler automatically handles nested and parallel observations based on `parent_run_id`:

```python
# Parent chain
parent_chain = ...

# Child chains (will nest under parent)
child_chain_1 = ...
child_chain_2 = ...

# Execution preserves hierarchy
result = parent_chain.invoke(data)
```

### Async Support

The handler works seamlessly with async operations:

```python
async def async_operation(x: int) -> int:
    await asyncio.sleep(0.1)
    return x * 2

async_chain = RunnableLambda(async_operation, name="AsyncOp")

# Async invoke - fully traced
result = await async_chain.ainvoke(5)
```

## Architecture Diagrams

### Auto-Injection Flow

```
┌─────────────────────────────────────────────────────────────┐
│ COAIAPY_TRACING_ENABLED=true                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ get_callback_manager_for_config() in config.py             │
│ • Checks environment variable                               │
│ • Creates CoaiapyLangfuseCallbackHandler                    │
│ • Adds to callback manager with inherit=True                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ All LangChain Runnables                                     │
│ • Chains, LLMs, Tools, Retrievers                           │
│ • Automatically receive the handler                         │
│ • No code changes needed                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Langfuse Dashboard                                          │
│ • Traces appear with rich metadata                          │
│ • Hierarchical structure preserved                          │
│ • Token usage tracked                                       │
└─────────────────────────────────────────────────────────────┘
```

### Handler Lifecycle

```
on_chain_start()
    ↓
    _get_or_create_trace()  →  Creates/retrieves Langfuse trace
    ↓
    trace.span()  →  Creates SPAN observation with metadata
    ↓
    Store observation in run_to_observation_id

... execution ...

on_chain_end()
    ↓
    Retrieve observation from run_to_observation_id
    ↓
    observation.end(output=result)  →  Updates with output
    ↓
    Langfuse SDK queues for backend

__del__() or explicit flush()
    ↓
    langfuse.flush()  →  Sends all pending traces
```

## Files Reference

### Implementation Files

- `libs/core/langchain_core/callbacks/langfuse_handler.py` - Handler implementation (444 lines)
- `libs/core/langchain_core/runnables/config.py` - Auto-injection mechanism
- `libs/core/langchain_core/stores.py` - Import path fix

### Configuration Files

- `LAUNCH__session_id__avaLangChainComponents_2511180702.sh` - Launch script with env setup
- `_env.sh` - Environment variable definitions

### Test Files

- `temp_test_tracing.py` - Comprehensive test suite

### Documentation Files

- `__llms/llms-coaiapy-langfuse-tracing-best-practices.md` - Best practices guide
- `LANGFUSE_INTEGRATION_GUIDE.md` - This file

## Contributing

When extending the handler:

1. **Preserve type hints** - All methods must have complete type annotations
2. **Follow glyph conventions** - Use `_add_glyph()` for consistent naming
3. **Handle errors gracefully** - Use try/except in lifecycle methods
4. **Test thoroughly** - Add tests for new observation types
5. **Document metadata** - Clearly specify what metadata is captured

## License

MIT License - See repository LICENSE file

## Support

For issues or questions:
- GitHub Issues: [avadisabelle/ava-langchain](https://github.com/avadisabelle/ava-langchain)
- Documentation: `__llms/` directory
- Langfuse Docs: [https://langfuse.com/docs](https://langfuse.com/docs)
