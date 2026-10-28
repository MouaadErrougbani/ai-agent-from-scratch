import os
from typing import Sequence

from dotenv import load_dotenv
from google import genai
from langchain_core.messages import BaseMessage, AIMessage

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

    def invoke(self, messages: Sequence[BaseMessage]) -> BaseMessage:
        interaction = self.client.interactions.create(
            model=self.model,
            input=messages,
            tools=self.tools or None,
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
                content=interaction.output_text or "",
                tool_calls=tool_calls,
            )

        return AIMessage(content=interaction.output_text or "")