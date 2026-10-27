
import os
from typing import TypedDict
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from google import genai

load_dotenv()


class AgentState(TypedDict):
    messages: list[HumanMessage | AIMessage]


class ChatGoogle:
    def __init__(
        self,
        model="gemini-3.1-flash-lite",
        api_key=None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is missing from .env")

        self.client = genai.Client(api_key=self.api_key)

    def invoke(self, messages: list) -> dict:
        history = "\n".join(
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: "
            f"{msg.content}"
            for msg in messages
        )

        interaction = self.client.interactions.create(
            model=self.model,
            input=history,
        )

        return {"content": interaction.output_text}


llm = ChatGoogle()


def process(state: AgentState) -> AgentState:
    """Process the conversation and append the AI response."""

    response = llm.invoke(state["messages"])

    state["messages"].append(
        AIMessage(content=response["content"])
    )

    return state


graph_builder = StateGraph(AgentState)
graph_builder.add_node("process", process)
graph_builder.add_edge(START, "process")
graph_builder.add_edge("process", END)

agent = graph_builder.compile()


while True:
    user_input = input("\nYou: ")

    if user_input.strip().lower() == "exit":
        break

    result = agent.invoke({
        "messages": [HumanMessage(content=user_input)]
    })

    print("\nAI:", result["messages"][-1].content)
