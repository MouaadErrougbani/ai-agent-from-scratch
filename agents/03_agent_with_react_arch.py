import os

from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv 
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from google import genai

load_dotenv()

class ChatGoogle:
    def __init__(
            self,
            model="gemini-3.8-flash",
            api_key=None,
    ):
        self.model = model 
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is missing from .env")

        self.client = genai.Client(api_key=self.api_key)
        self.tools = []

    def bind_tools(self, tools: Sequence[dict]) -> "ChatGoogle":
        self.tools = list(tools)
        return self

    def invoke(self, messages: Sequence[BaseMessage])->BaseMessage:
        interaction = self.client.interactions.create(
            model=self.model,
            input= messages,
            tools=self.tools or None
        )
        tool_calls = []
        for step in interaction.steps or []:
            if step.type == "function_call":
                tool_calls.append({
                    "name": step.name,
                    "args": step.arguments,
                    "id": step.id,
                    "type": "tool_call",
                })
        if tool_calls: 
            return AIMessage(
                content= interaction.output_text or "",
                tool_calls= tool_calls
            )
        return AIMessage(content=interaction.output_text or "")

class AgentState(TypedDict): 
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def add(a: int, b: int):
    """This is an addition function that adds 2 numbers together"""
    return a + b

tools = [add]

model = ChatGoogle(model="gemini-3.1-flash-lite")

model.bind_tools(tools=tools)

def model_call(state: AgentState) -> AgentState: 
    system_prompt = SystemMessage(content="You are my AI assistant, please answer my query to the best of your ability.")
    response = model.invoke([system_prompt] + [state["messages"]])
    return {"messages": [response]}

def should_continue(state: AgentState) -> AgentState:
    messages = state["messages"]
    last_message = messages[-1]

    if not last_message.tool_calls:
        return "end"
    return "continue"