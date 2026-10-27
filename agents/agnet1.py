
from typing import TypedDict
import os

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
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

    def invoke(self, message: str) -> dict:
        interaction = self.client.interactions.create(
            model=self.model,
            input=message,
        )
        return {"content": interaction.output_text}


class AgentState(TypedDict):
    message: str


llm = ChatGoogle(model="gemini-3.1-flash-lite")


def process(state: AgentState) -> AgentState:
    response = llm.invoke(state["message"])

    print(f"\nAI: {response['content']}")

    return state


graph = StateGraph(AgentState)

graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)

agent = graph.compile()


while True:
    user_input = input("\nYou: ")

    if user_input.strip().lower() == "exit":
        break

    agent.invoke({"message": user_input})
