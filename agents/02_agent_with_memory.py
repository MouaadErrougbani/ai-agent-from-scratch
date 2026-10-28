# Agent with file memory

import os 
from typing import TypedDict, List, Union
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START

from google import genai

load_dotenv()

class AgentState(TypedDict): 
    messages: List[Union[HumanMessage, AIMessage]]


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

    def invoke(self, messages: list) -> AIMessage:
        history = "\n".join(
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}:"
            f"{msg.content}"
            for msg in messages
        )
        interaction = self.client.interactions.create(
            model=self.model,
            input=history,
        )
        return AIMessage(content=interaction.output_text)



llm = ChatGoogle(model="gemini-3.1-flash-lite")

def process(state: AgentState) -> AgentState:
    """This node will solve the request you input"""
    response = llm.invoke(messages=state['messages'])
    state['messages'].append(response)
    return state


graph = StateGraph(AgentState)
graph.add_node('process', process)
graph.add_edge(START, "process")
graph.add_edge("process", END)

agent = graph.compile()

state = AgentState({"messages": []})

while True: 
    user_input = input("\nYou: ")
    if user_input.strip().lower() == "exit":
        break
    state["messages"].append(HumanMessage(content=user_input))
    state = agent.invoke(state)

    print('\nAI: ', state["messages"][-1].content)

with open("logging.md", "w") as file: 
    file.write("Your Conversation log: \n---\n")
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            file.write(f"User: {message.content}\n")
        elif isinstance(message, AIMessage):
            file.write(f"Assistant: {message.content}\n")
    file.write("---")

print("Conversation saved to logging.txt")