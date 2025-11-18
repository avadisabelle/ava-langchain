"""Callback handler for Langfuse integration via Coaiapy Aetherial.

This module provides LangChain callback handlers that automatically trace
execution to Langfuse, following the best practices outlined in
llms-coaiapy-langfuse-tracing-best-practices.md.
"""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGenerationChunk, LLMResult

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None

class CoaiapyLangfuseCallbackHandler(BaseCallbackHandler):
    """Callback Handler for Langfuse integration in LangChain.

    This handler integrates with Langfuse to provide structured tracing for
    LangChain runnables, following best practices from the Coaiapy Aetherial
    tracing guidelines.

    Features:
    - Automatic trace and observation creation
    - Hierarchical structure preservation (parent-child relationships)
    - Rich metadata and input/output capture
    - Support for LLM, Chain, Tool, and Retriever operations
    - Glyph-enhanced naming for visual context

    Args:
        session_id: Langfuse session ID. Defaults to COAIAPY_SESSION_ID env var.
        trace_id: Optional trace ID for grouping. If not provided, creates per-run traces.
        public_key: Langfuse public key. Defaults to LANGFUSE_PUBLIC_KEY env var.
        secret_key: Langfuse secret key. Defaults to LANGFUSE_SECRET_KEY env var.
        host: Langfuse host URL. Defaults to LANGFUSE_HOST env var.
        trace_name: Custom name for traces. Defaults to "🧠 LangChain Execution".
        flush_on_exit: Whether to flush pending traces on handler destruction. Defaults to `True`.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        trace_name: Optional[str] = None,
        flush_on_exit: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        if not LANGFUSE_AVAILABLE:
            raise ImportError(
                "Langfuse is not installed. Install it with: pip install langfuse"
            )

        # Session and trace configuration
        self.session_id = session_id or os.environ.get("COAIAPY_SESSION_ID")
        self.default_trace_id = trace_id or os.environ.get("COAIAPY_TRACE_ID")
        self.trace_name = trace_name or "🧠 LangChain Execution"
        self.flush_on_exit = flush_on_exit

        # Initialize Langfuse client
        self.langfuse = Langfuse(
            public_key=public_key or os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=secret_key or os.environ.get("LANGFUSE_SECRET_KEY"),
            host=host or os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )

        # Tracking maps
        self.run_to_trace_id: Dict[str, str] = {}  # Maps run_id -> trace_id
        self.run_to_observation_id: Dict[str, str] = {}  # Maps run_id -> observation_id
        self.trace_objects: Dict[str, Any] = {}  # Store trace objects
        self.observation_objects: Dict[str, Any] = {}  # Store observation objects
        self.run_start_times: Dict[str, datetime] = {}  # Track start times

    def _get_parent_id(self, parent_run_id: Optional[uuid.UUID]) -> Optional[str]:
        """Get the Langfuse parent observation ID from a LangChain parent run ID."""
        return self.run_to_observation_id.get(str(parent_run_id)) if parent_run_id else None

    def _get_or_create_trace(self, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None) -> str:
        """Get existing trace ID or create a new trace for this run."""
        run_id_str = str(run_id)

        # If this run already has a trace, return it
        if run_id_str in self.run_to_trace_id:
            return self.run_to_trace_id[run_id_str]

        # If there's a parent, use its trace
        if parent_run_id:
            parent_trace_id = self.run_to_trace_id.get(str(parent_run_id))
            if parent_trace_id:
                self.run_to_trace_id[run_id_str] = parent_trace_id
                return parent_trace_id

        # No parent and no existing trace - create a new one
        # Use default_trace_id if available, otherwise create new
        trace_id = self.default_trace_id or str(uuid.uuid4())
        self.run_to_trace_id[run_id_str] = trace_id

        # Create the trace in Langfuse if it doesn't exist
        if trace_id not in self.trace_objects:
            trace = self.langfuse.trace(
                id=trace_id,
                session_id=self.session_id,
                name=self.trace_name,
            )
            self.trace_objects[trace_id] = trace

        return trace_id

    def _add_glyph(self, name: str, run_type: str) -> str:
        """Add appropriate glyph to observation name based on type."""
        glyph_map = {
            "llm": "🤖",
            "chat": "💬",
            "chain": "🔗",
            "tool": "🔧",
            "retriever": "📚",
            "agent": "🧭",
        }
        glyph = glyph_map.get(run_type, "⚙️")
        return f"{glyph} {name}" if name and not name.startswith(glyph) else name or "Unnamed"

    def on_run_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Run when any LangChain runnable starts."""
        self.run_start_times[str(run_id)] = datetime.now()

    def on_run_end(
        self,
        outputs: Any,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when any LangChain runnable ends."""
        # Update observation with output if it exists
        obs_id = self.run_to_observation_id.get(str(run_id))
        if obs_id and obs_id in self.observation_objects:
            obs = self.observation_objects[obs_id]
            obs.end(output=outputs)

    def on_run_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Run when any LangChain runnable errors."""
        obs_id = self.run_to_observation_id.get(str(run_id))
        if obs_id and obs_id in self.observation_objects:
            obs = self.observation_objects[obs_id]
            obs.end(
                level="ERROR",
                status_message=str(error),
                output={"error": str(error), "error_type": type(error).__name__}
            )

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts."""
        trace_id = self._get_or_create_trace(run_id, parent_run_id)
        trace = self.trace_objects[trace_id]

        name = self._add_glyph(
            metadata.get("ls_model_name") if metadata else None or "LLM",
            "llm"
        )

        # Create generation observation
        generation = trace.generation(
            id=str(run_id),
            name=name,
            input=prompts,
            metadata={
                "tags": tags or [],
                "serialized": serialized,
                **(metadata or {}),
            },
            parent_observation_id=self._get_parent_id(parent_run_id),
        )

        self.run_to_observation_id[str(run_id)] = str(run_id)
        self.observation_objects[str(run_id)] = generation

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM ends."""
        obs_id = self.run_to_observation_id.get(str(run_id))
        if obs_id and obs_id in self.observation_objects:
            generation = self.observation_objects[obs_id]
            # Extract generations for output
            outputs = [gen.text for gens in response.generations for gen in gens]
            generation.end(
                output=outputs,
                usage={
                    "prompt_tokens": response.llm_output.get("token_usage", {}).get("prompt_tokens")
                    if response.llm_output else None,
                    "completion_tokens": response.llm_output.get("token_usage", {}).get("completion_tokens")
                    if response.llm_output else None,
                    "total_tokens": response.llm_output.get("token_usage", {}).get("total_tokens")
                    if response.llm_output else None,
                }
            )

    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM errors."""
        self.on_run_error(error, run_id=run_id, parent_run_id=parent_run_id, tags=tags, **kwargs)

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when chat model starts."""
        trace_id = self._get_or_create_trace(run_id, parent_run_id)
        trace = self.trace_objects[trace_id]

        name = self._add_glyph(
            metadata.get("ls_model_name") if metadata else None or "ChatModel",
            "chat"
        )

        # Serialize messages for input
        serialized_messages = [
            [{"role": msg.type, "content": msg.content} for msg in message_list]
            for message_list in messages
        ]

        # Create generation observation
        generation = trace.generation(
            id=str(run_id),
            name=name,
            input=serialized_messages,
            metadata={
                "tags": tags or [],
                "serialized": serialized,
                "message_count": sum(len(msgs) for msgs in messages),
                **(metadata or {}),
            },
            parent_observation_id=self._get_parent_id(parent_run_id),
        )

        self.run_to_observation_id[str(run_id)] = str(run_id)
        self.observation_objects[str(run_id)] = generation

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when chain starts."""
        trace_id = self._get_or_create_trace(run_id, parent_run_id)
        trace = self.trace_objects[trace_id]

        name = self._add_glyph(
            serialized.get("name") or serialized.get("id", ["", "Chain"])[-1],
            "chain"
        )

        # Create span observation for chain
        span = trace.span(
            id=str(run_id),
            name=name,
            input=inputs,
            metadata={
                "tags": tags or [],
                "serialized": serialized,
                **(metadata or {}),
            },
            parent_observation_id=self._get_parent_id(parent_run_id),
        )

        self.run_to_observation_id[str(run_id)] = str(run_id)
        self.observation_objects[str(run_id)] = span

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when chain ends."""
        self.on_run_end(outputs, run_id=run_id, parent_run_id=parent_run_id, tags=tags, **kwargs)

    def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when chain errors."""
        self.on_run_error(error, run_id=run_id, parent_run_id=parent_run_id, tags=tags, **kwargs)

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when tool starts."""
        trace_id = self._get_or_create_trace(run_id, parent_run_id)
        trace = self.trace_objects[trace_id]

        name = self._add_glyph(serialized.get("name", "Tool"), "tool")

        # Create span observation for tool
        span = trace.span(
            id=str(run_id),
            name=name,
            input=input_str,
            metadata={
                "tags": tags or [],
                "serialized": serialized,
                **(metadata or {}),
            },
            parent_observation_id=self._get_parent_id(parent_run_id),
        )

        self.run_to_observation_id[str(run_id)] = str(run_id)
        self.observation_objects[str(run_id)] = span

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when tool ends."""
        self.on_run_end(output, run_id=run_id, parent_run_id=parent_run_id, tags=tags, **kwargs)

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when tool errors."""
        self.on_run_error(error, run_id=run_id, parent_run_id=parent_run_id, tags=tags, **kwargs)

    def on_retriever_start(
        self,
        serialized: Dict[str, Any],
        query: str,
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when retriever starts."""
        trace_id = self._get_or_create_trace(run_id, parent_run_id)
        trace = self.trace_objects[trace_id]

        name = self._add_glyph(serialized.get("name", "Retriever"), "retriever")

        # Create span observation for retriever
        span = trace.span(
            id=str(run_id),
            name=name,
            input={"query": query},
            metadata={
                "tags": tags or [],
                "serialized": serialized,
                **(metadata or {}),
            },
            parent_observation_id=self._get_parent_id(parent_run_id),
        )

        self.run_to_observation_id[str(run_id)] = str(run_id)
        self.observation_objects[str(run_id)] = span

    def on_retriever_end(
        self,
        documents: List[Any],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when retriever ends."""
        # Format documents for output
        doc_outputs = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            if hasattr(doc, "page_content") else str(doc)
            for doc in documents
        ]
        self.on_run_end(
            {"documents": doc_outputs, "count": len(documents)},
            run_id=run_id,
            parent_run_id=parent_run_id,
            tags=tags,
            **kwargs
        )

    def on_retriever_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: uuid.UUID,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when retriever errors."""
        self.on_run_error(error, run_id=run_id, parent_run_id=parent_run_id, tags=tags, **kwargs)

    def flush(self) -> None:
        """Manually flush pending traces to Langfuse.

        This method can be called to ensure all traces are sent immediately,
        rather than waiting for automatic flushing.
        """
        if hasattr(self, "langfuse"):
            self.langfuse.flush()

    def __del__(self) -> None:
        """Flush pending traces on handler destruction if enabled."""
        try:
            if self.flush_on_exit and hasattr(self, "langfuse"):
                self.langfuse.flush()
        except Exception:
            pass  # Silently fail on cleanup
