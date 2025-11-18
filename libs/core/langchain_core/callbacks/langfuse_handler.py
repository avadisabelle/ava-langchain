import os
import uuid
from typing import Any, Dict, List, Optional, Union

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# Define placeholder functions for coaia_fuse tools.
# These will not print anything to reduce noise for current debugging.
def coaia_fuse_trace_create(trace_id: str, name: str, input_data: Any = None, output_data: Any = None, metadata: Optional[Dict] = None, session_id: Optional[str] = None, user_id: Optional[str] = None):
    pass

def coaia_fuse_add_observation(trace_id: str, observation_id: str, name: str, observation_type: str = "SPAN", input_data: Any = None, output_data: Any = None, metadata: Optional[Dict] = None, parent_id: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None):
    pass

class CoaiapyLangfuseCallbackHandler(BaseCallbackHandler):
    """Callback Handler for Coaiapy Aetherial and Langfuse.

    This handler integrates with Langfuse via coaiapy_aetherial tools to provide
    structured tracing for LangChain runnables.
    """

    def __init__(self, session_id: Optional[str] = None, trace_id: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        print("DEBUG: CoaiapyLangfuseCallbackHandler __init__ called.")
        self.session_id = session_id or os.environ.get("COAIAPY_SESSION_ID")
        self.trace_id = trace_id or os.environ.get("COAIAPY_TRACE_ID")
        
        # If no trace_id is provided or found in env, create a new one for the session
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
            # We don't call coaia_fuse_trace_create here in debug mode to avoid nested prints
        
        self.run_to_observation_id: Dict[str, str] = {}
        self.trace_created_for_run: Dict[str, bool] = {}

    def _get_parent_id(self, parent_run_id: Optional[uuid.UUID]) -> Optional[str]:
        """Helper to get the Langfuse parent_id from a LangChain parent_run_id."""
        return self.run_to_observation_id.get(str(parent_run_id)) if parent_run_id else None

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
        print(f"DEBUG: CoaiapyLangfuseCallbackHandler.on_run_start called for run_id={run_id}, name={name}, parent_run_id={parent_run_id}")

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
        print(f"DEBUG: CoaiapyLangfuseCallbackHandler.on_run_end called for run_id={run_id}, parent_run_id={parent_run_id}")

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
        print(f"DEBUG: CoaiapyLangfuseCallbackHandler.on_run_error called for run_id={run_id}, error={error}, parent_run_id={parent_run_id}")

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        pass

    def on_llm_end(self, response: LLMResult, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        pass

    def on_chain_end(self, outputs: Dict[str, Any], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        pass

    def on_tool_end(self, output: str, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass

    def on_retriever_start(self, serialized: Dict[str, Any], query: str, *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        pass

    def on_retriever_end(self, documents: List[Any], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass

    def on_retriever_error(self, error: Union[Exception, KeyboardInterrupt], *, run_id: uuid.UUID, parent_run_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None, **kwargs: Any) -> None:
        pass
