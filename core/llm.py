import os
import inspect
import json
import logging
from typing import List, Callable, Dict, Any
from dataclasses import dataclass

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage, ToolMessage, ChatCompletionsToolDefinition, FunctionDefinition
from azure.core.credentials import AzureKeyCredential

SYSTEM_INSTRUCTION = """
You are N.O.V.A, an advanced AI system.
Your goal is to assist the user with their tasks efficiently and accurately.

GUIDELINES:
1.  **Brevity:** You are a voice assistant. Keep answers concise (1-2 sentences) unless asked for details.
2.  **Personality:** Professional, efficient, with a very slight dry wit.
3.  **Tools:** You have access to real-world tools. USE THEM. Do not say "I can't do that" if you have a tool for it.
4.  **Confirmation:** When performing an action (like turning on lights), confirm briefly (e.g., "Lights enabled.").
"""

logger = logging.getLogger("NOVA_BRAIN")

@dataclass
class ResponseWrapper:
    text: str
    action_taken: bool

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
    def __init__(self, client: ChatCompletionsClient, model_name: str, tools_map: Dict[str, Callable], tool_definitions: List):
        self.client = client
        self.model_name = model_name
        self.history = [SystemMessage(content=SYSTEM_INSTRUCTION)]
        self.tools_map = tools_map
        self.tool_definitions = tool_definitions

    def send_message(self, text: str):
        self.history.append(UserMessage(content=text))
        
        max_turns = 5
        tool_used = False
        
        for _ in range(max_turns):
            response = self.client.complete(
                messages=self.history,
                tools=self.tool_definitions if self.tool_definitions else None,
                model=self.model_name
            )
            
            choice = response.choices[0]
            
            if choice.message.tool_calls:
                tool_used = True
                self.history.append(AssistantMessage(tool_calls=choice.message.tool_calls))
                
                for tool_call in choice.message.tool_calls:
                    func_name = tool_call.function.name
                    args_json = tool_call.function.arguments
                    
                    if func_name in self.tools_map:
                        try:
                            args = json.loads(args_json)
                            logger.info(f"🛠️ Executing {func_name} with {args}")
                            
                            result = self.tools_map[func_name](**args)
                            
                        except Exception as e:
                            result = f"Error executing {func_name}: {str(e)}"
                    else:
                        result = f"Error: Function {func_name} not found."
                    
                    self.history.append(ToolMessage(tool_call_id=tool_call.id, content=str(result)))
                
                continue
            
            else:
                final_text = choice.message.content
                self.history.append(AssistantMessage(content=final_text))
                
                return ResponseWrapper(text=final_text, action_taken=tool_used)
                
        return ResponseWrapper(text="I'm sorry, I got stuck in a loop processing your request.", action_taken=True)


def initialize_brain(tools_list: List[Callable]):
    endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
    key = os.getenv("AZURE_INFERENCE_CREDENTIAL")
    model_name = os.getenv("LLM_MODEL", "gpt-4o") 

    if not endpoint or not key:
        raise ValueError("CRITICAL: Missing AZURE_INFERENCE_ENDPOINT or AZURE_INFERENCE_CREDENTIAL in .env")

    print(f"Initializing Azure AI Foundry with model: {model_name}")

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    tools_map = {func.__name__: func for func in tools_list}
    tool_definitions = [function_to_schema(func) for func in tools_list]

    return AzureNovaSession(client, model_name, tools_map, tool_definitions)