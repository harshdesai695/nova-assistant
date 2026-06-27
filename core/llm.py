import os
import inspect
import json
import logging
import time
from typing import Generator
from typing import List, Callable, Dict, Any
from dataclasses import dataclass, field
import requests

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage, ToolMessage, ChatCompletionsToolDefinition, FunctionDefinition
from azure.core.credentials import AzureKeyCredential

from core.parallel_exec import execute_functions_parallel
from core.streaming import chunk_text

SYSTEM_INSTRUCTION = """
You are N.O.V.A, an advanced AI system.
Your goal is to assist the user with their tasks efficiently and accurately.

GUIDELINES:
1.  **Brevity:** You are a voice assistant. Keep answers concise (1-2 sentences) unless asked for details.
2.  **Personality:** Professional, efficient, with a very slight dry wit.
3.  **Tools:** You have access to real-world tools. USE THEM. Do not say "I can't do that" if you have a tool for it.
4.  **Confirmation:** When performing an action (like turning on lights), confirm briefly (e.g., "Lights enabled.").
5.  **Follow-ups:** In an active conversation, short instructions ("do it", "also", "tomorrow") usually refer to recent context.
6.  **Clarify only when needed:** Ask one short clarification question only if the request is genuinely ambiguous.
"""

logger = logging.getLogger("NOVA_BRAIN")

NOVA_CLIENT = None
NOVA_MODEL = None
NOVA_ENDPOINT = None
NOVA_TOOLS_MAP: Dict[str, Callable] = {}
NOVA_TOOL_DEFINITIONS: List[ChatCompletionsToolDefinition] = []
NOVA_FALLBACK_ENABLED = False
NOVA_FALLBACK_MODEL = "gemma2:7b"
NOVA_FALLBACK_URL = "http://localhost:11434"

@dataclass
class ResponseWrapper:
    text: str
    action_taken: bool
    tools_called: List[str] = field(default_factory=list)
    route_type: str = "llm"
    route_confidence: float = 0.0
    latency_ms: int = 0

def function_to_schema(func: Callable) -> ChatCompletionsToolDefinition:
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or "No description provided."
    
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for param_name, param in sig.parameters.items():
        param_type = "string" 
        if param.annotation == int:
            param_type = "integer"
        elif param.annotation == float:
            param_type = "number"
        elif param.annotation == bool:
            param_type = "boolean"
            
        parameters["properties"][param_name] = {
            "type": param_type,
            "description": f"Parameter {param_name}" 
        }
        
        if param.default == inspect.Parameter.empty:
            parameters["required"].append(param_name)

    return ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name=func.__name__,
            description=doc,
            parameters=parameters
        )
    )

class AzureNovaSession:
    def __init__(self, client: ChatCompletionsClient, model_name: str, tools_map: Dict[str, Callable], tool_definitions: List, fallback_session=None):
        self.client = client
        self.model_name = model_name
        self.history = [SystemMessage(content=SYSTEM_INSTRUCTION)]
        self.tools_map = tools_map
        self.tool_definitions = tool_definitions
        self.fallback_session = fallback_session

    def reset_history(self):
        self.history = [SystemMessage(content=SYSTEM_INSTRUCTION)]

    def get_history_length(self) -> int:
        return len(self.history)

    def load_conversation(self, transcript: List[Dict[str, str]]) -> None:
        """Rehydrate context from persisted user/assistant turns."""
        for turn in transcript:
            user_text = (turn.get("user_text") or "").strip()
            assistant_text = (turn.get("assistant_text") or "").strip()
            if user_text:
                self.history.append(UserMessage(content=user_text))
            if assistant_text:
                self.history.append(AssistantMessage(content=assistant_text))

    def _execute_tool_calls(self, tool_calls, tools_called: List[str]) -> None:
        fn_calls = {}
        call_lookup = {}

        for tool_call in tool_calls:
            func_name = tool_call.function.name
            args_json = tool_call.function.arguments
            tools_called.append(func_name)
            call_lookup[func_name] = tool_call

            if func_name in self.tools_map:
                try:
                    args = json.loads(args_json)
                except Exception:
                    args = {}
                fn_calls[func_name] = (self.tools_map[func_name], args)

        if os.getenv("NOVA_ENABLE_PARALLEL_SKILLS", "true").lower() == "true" and len(fn_calls) > 1:
            results = execute_functions_parallel(fn_calls)
        else:
            results = {}
            for func_name, (fn, kwargs) in fn_calls.items():
                try:
                    results[func_name] = fn(**kwargs)
                except Exception as exc:
                    results[func_name] = f"Error executing {func_name}: {exc}"

        for tool_call in tool_calls:
            func_name = tool_call.function.name
            if func_name in results:
                content = str(results[func_name])
            elif func_name not in self.tools_map:
                content = f"Error: Function {func_name} not found."
            else:
                content = f"Error: Function {func_name} execution failed."
            self.history.append(ToolMessage(tool_call_id=tool_call.id, content=content))

    def send_message(self, text: str):
        started = time.perf_counter()
        self.history.append(UserMessage(content=text))
        
        max_turns = 5
        tool_used = False
        tools_called: List[str] = []
        
        for _ in range(max_turns):
            try:
                response = self.client.complete(
                    messages=self.history,
                    tools=self.tool_definitions if self.tool_definitions else None,
                    model=self.model_name
                )
            except Exception as exc:
                if self.fallback_session is not None:
                    logger.warning(f"Azure request failed, using fallback: {exc}")
                    fb = self.fallback_session.send_message(text)
                    fb.route_type = "fallback"
                    return fb
                raise
            
            choice = response.choices[0]
            
            if choice.message.tool_calls:
                tool_used = True
                self.history.append(AssistantMessage(tool_calls=choice.message.tool_calls))
                self._execute_tool_calls(choice.message.tool_calls, tools_called)
                
                continue
            
            else:
                final_text = choice.message.content
                self.history.append(AssistantMessage(content=final_text))
                
                return ResponseWrapper(
                    text=final_text,
                    action_taken=tool_used,
                    tools_called=tools_called,
                    route_type="azure",
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
                
        return ResponseWrapper(
            text="I'm sorry, I got stuck in a loop processing your request.",
            action_taken=True,
            tools_called=tools_called,
            route_type="azure",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def stream_message(self, text: str) -> Generator[str, None, ResponseWrapper]:
        if os.getenv("NOVA_ENABLE_STREAMING", "true").lower() != "true":
            wrapper = self.send_message(text)
            for ch in chunk_text(wrapper.text):
                yield ch
            return wrapper

        # Best effort streaming path. Falls back to chunking final text.
        try:
            history = self.history + [UserMessage(content=text)]
            response = self.client.complete(
                messages=history,
                model=self.model_name,
                tools=self.tool_definitions if self.tool_definitions else None,
                stream=True,
            )
            collected = []
            for chunk in response:
                token = None
                try:
                    token = chunk.choices[0].delta.content
                except Exception:
                    token = None
                if token:
                    collected.append(token)
                    yield token
            final = "".join(collected).strip()
            if not final:
                wrapper = self.send_message(text)
                for ch in chunk_text(wrapper.text):
                    yield ch
                return wrapper
            self.history.append(UserMessage(content=text))
            self.history.append(AssistantMessage(content=final))
            return ResponseWrapper(text=final, action_taken=False, route_type="azure-stream")
        except Exception:
            wrapper = self.send_message(text)
            for ch in chunk_text(wrapper.text):
                yield ch
            return wrapper


class OllamaSession:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.history: List[dict] = []

    def reset_history(self):
        self.history = []

    def get_history_length(self) -> int:
        return len(self.history)

    def load_conversation(self, transcript: List[Dict[str, str]]) -> None:
        for turn in transcript:
            user_text = (turn.get("user_text") or "").strip()
            assistant_text = (turn.get("assistant_text") or "").strip()
            if user_text:
                self.history.append({"role": "user", "content": user_text})
            if assistant_text:
                self.history.append({"role": "assistant", "content": assistant_text})

    def send_message(self, text: str) -> ResponseWrapper:
        started = time.perf_counter()
        self.history.append({"role": "user", "content": text})
        try:
            payload = {"model": self.model_name, "messages": self.history, "stream": False}
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            self.history.append({"role": "assistant", "content": content})
            return ResponseWrapper(
                text=content or "I am running in local fallback mode.",
                action_taken=False,
                route_type="fallback",
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        except Exception as exc:
            return ResponseWrapper(
                text=f"Fallback mode failed: {exc}",
                action_taken=False,
                route_type="fallback",
                latency_ms=int((time.perf_counter() - started) * 1000),
            )


def initialize_brain(tools_list: List[Callable]):
    global NOVA_CLIENT, NOVA_MODEL, NOVA_TOOLS_MAP, NOVA_TOOL_DEFINITIONS
    global NOVA_ENDPOINT, NOVA_FALLBACK_ENABLED, NOVA_FALLBACK_MODEL, NOVA_FALLBACK_URL
    endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
    key = os.getenv("AZURE_INFERENCE_CREDENTIAL")
    model_name = os.getenv("LLM_MODEL", "gpt-4o") 
    NOVA_FALLBACK_ENABLED = os.getenv("NOVA_ENABLE_LLM_FALLBACK", "true").lower() == "true"
    NOVA_FALLBACK_MODEL = os.getenv("NOVA_FALLBACK_MODEL", "gemma2:7b")
    NOVA_FALLBACK_URL = os.getenv("NOVA_FALLBACK_URL", "http://localhost:11434")

    tools_map = {func.__name__: func for func in tools_list}
    tool_definitions = [function_to_schema(func) for func in tools_list]
    NOVA_TOOLS_MAP = tools_map
    NOVA_TOOL_DEFINITIONS = tool_definitions

    fallback_session = OllamaSession(model_name=NOVA_FALLBACK_MODEL, base_url=NOVA_FALLBACK_URL) if NOVA_FALLBACK_ENABLED else None

    if not endpoint or not key:
        if NOVA_FALLBACK_ENABLED:
            logger.warning("Azure credentials missing, using fallback-only mode.")
            NOVA_CLIENT = None
            NOVA_MODEL = NOVA_FALLBACK_MODEL
            NOVA_ENDPOINT = None
            return fallback_session
        raise ValueError("CRITICAL: Missing AZURE_INFERENCE_ENDPOINT or AZURE_INFERENCE_CREDENTIAL in .env")

    full_endpoint = f"{endpoint.rstrip('/')}/deployments/{model_name}"

    print(f"Initializing Azure AI Foundry with model: {model_name}")

    client = ChatCompletionsClient(endpoint=full_endpoint, credential=AzureKeyCredential(key))
    
    NOVA_CLIENT = client
    NOVA_MODEL = model_name
    NOVA_ENDPOINT = full_endpoint

    return AzureNovaSession(client, model_name, tools_map, tool_definitions, fallback_session=fallback_session)


def create_session() -> AzureNovaSession:
    if NOVA_CLIENT is None:
        if NOVA_FALLBACK_ENABLED:
            return OllamaSession(model_name=NOVA_FALLBACK_MODEL, base_url=NOVA_FALLBACK_URL)
        raise RuntimeError("NOVA brain is not initialized.")
    fallback_session = OllamaSession(model_name=NOVA_FALLBACK_MODEL, base_url=NOVA_FALLBACK_URL) if NOVA_FALLBACK_ENABLED else None
    return AzureNovaSession(NOVA_CLIENT, NOVA_MODEL, NOVA_TOOLS_MAP, NOVA_TOOL_DEFINITIONS, fallback_session=fallback_session)