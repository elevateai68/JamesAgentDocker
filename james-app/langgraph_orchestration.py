from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import re
import json

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_agent: str
    needs_external_data: bool
    needs_domain_expert: bool
    final_response: str
    user_context: str

# ✅ UPDATED: Use Docker service name for internal Ollama connection
james_model = ChatOllama(model="qwen2.5:7b", temperature=0.7, base_url="http://ollama:11434")
scout_model = ChatOllama(model="llama3.2:3b", temperature=0.3, base_url="http://ollama:11434")
trained_model = ChatOllama(model="qwen2.5:7b", temperature=0.8, base_url="http://ollama:11434")

def james_coordinator(state: AgentState) -> AgentState:
    user_message = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
    if not user_message:
        return state

    james_system = f"""You are James, a sophisticated AI coordinator with a subtle James Bond-inspired personality. 
You coordinate between specialists:
- Scout: external data (web, news, APIs)
- Trained: domain expert
Handle yourself if possible.

Routing:
- ROUTE_TO_SCOUT for current/live data
- ROUTE_TO_TRAINED for expert knowledge
- Otherwise, respond directly

Context: {state.get("user_context", "")}
User: {user_message}
"""
    response = james_model.invoke([SystemMessage(content=james_system), HumanMessage(content=user_message)])
    response_content = response.content

    if "ROUTE_TO_SCOUT" in response_content:
        state["needs_external_data"] = True
        state["current_agent"] = "scout"
        scout_request = response_content.replace("ROUTE_TO_SCOUT", "").strip()
        state["messages"].append(AIMessage(content=f"James routing to Scout: {scout_request}"))
    elif "ROUTE_TO_TRAINED" in response_content:
        state["needs_domain_expert"] = True  
        state["current_agent"] = "trained"
        trained_request = response_content.replace("ROUTE_TO_TRAINED", "").strip()
        state["messages"].append(AIMessage(content=f"James routing to Trained: {trained_request}"))
    else:
        state["final_response"] = response_content
        state["current_agent"] = "james_final"
    return state

def scout_agent(state: AgentState) -> AgentState:
    routing_message = next((m.content.replace("James routing to Scout:", "").strip() for m in reversed(state["messages"]) if isinstance(m, AIMessage) and "James routing to Scout:" in m.content), "")
    if not routing_message:
        return state
    scout_system = f"""You are Scout, focused on external data (web/API/etc).
Respond with:
1. How you'd retrieve the data
2. What source you'd use
3. Simulated response

Request: {routing_message}
"""
    response = scout_model.invoke([SystemMessage(content=scout_system), HumanMessage(content=routing_message)])
    state["messages"].append(AIMessage(content=f"Scout report: {response.content}"))
    state["current_agent"] = "james_final"
    state["needs_external_data"] = False
    return state

def trained_agent(state: AgentState) -> AgentState:
    routing_message = next((m.content.replace("James routing to Trained:", "").strip() for m in reversed(state["messages"]) if isinstance(m, AIMessage) and "James routing to Trained:" in m.content), "")
    if not routing_message:
        return state
    trained_system = f"""You are Trained, a domain expert. Provide professional advice or insight.

Request: {routing_message}
"""
    response = trained_model.invoke([SystemMessage(content=trained_system), HumanMessage(content=routing_message)])
    state["messages"].append(AIMessage(content=f"Expert analysis: {response.content}"))
    state["current_agent"] = "james_final"
    state["needs_domain_expert"] = False
    return state

def james_final_response(state: AgentState) -> AgentState:
    if state.get("final_response"):
        return state

    history = "\n".join(f"{'User' if isinstance(m, HumanMessage) else 'System'}: {m.content}" for m in state["messages"])
    user_message = next((m.content for m in state["messages"] if isinstance(m, HumanMessage)), "")

    james_final_system = f"""You are James. Review the full conversation and specialist input. Respond as a coordinated, charming assistant.

Conversation:
{history}
"""
    response = james_model.invoke([SystemMessage(content=james_final_system), HumanMessage(content=user_message)])
    state["final_response"] = response.content
    return state

def route_decision(state: AgentState) -> Literal["scout", "trained", "james_final"]:
    return state.get("current_agent", "james_final")

def create_james_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("james_coordinator", james_coordinator)
    workflow.add_node("scout", scout_agent)
    workflow.add_node("trained", trained_agent)
    workflow.add_node("james_final", james_final_response)

    workflow.add_edge(START, "james_coordinator")
    workflow.add_conditional_edges("james_coordinator", route_decision, {
        "scout": "scout",
        "trained": "trained",
        "james_final": "james_final"
    })
    workflow.add_edge("scout", "james_final")
    workflow.add_edge("trained", "james_final")
    workflow.add_edge("james_final", END)

    return workflow.compile()
