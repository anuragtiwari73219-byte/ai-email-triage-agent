from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
import os

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

class AgentState(TypedDict):
    email_subject: str
    decision: str
    reasoning: str
    verified: bool
    retry_count: int

def decide_node(state: AgentState) -> AgentState:
    print(f"[decide_node] Deciding for: {state['email_subject']} (attempt {state['retry_count'] + 1})")
    response = llm.invoke(
        f"Email subject: '{state['email_subject']}'. "
        f"Should this be 'draft_reply', 'flag_urgent', or 'archive_silently'? "
        f"Reply in format: ACTION: <action> | REASON: <one sentence reason>"
    )
    text = response.content.strip()
    action = "archive_silently"
    reason = text
    if "ACTION:" in text and "REASON:" in text:
        action_part = text.split("ACTION:")[1].split("|")[0].strip()
        reason_part = text.split("REASON:")[1].strip()
        action = action_part
        reason = reason_part
    return {**state, "decision": action, "reasoning": reason, "retry_count": state["retry_count"] + 1}

def verify_node(state: AgentState) -> AgentState:
    print(f"[verify_node] Checking: decision='{state['decision']}' reasoning='{state['reasoning']}'")
    verified = True
    print(f"[verify_node] verified={verified}")
    return {**state, "verified": verified}

def route_after_verify(state: AgentState) -> str:
    if state["verified"] or state["retry_count"] >= 2:
        return "end"
    return "retry"

graph = StateGraph(AgentState)
graph.add_node("decide", decide_node)
graph.add_node("verify", verify_node)
graph.set_entry_point("decide")
graph.add_edge("decide", "verify")
graph.add_conditional_edges("verify", route_after_verify, {"end": END, "retry": "decide"})

app = graph.compile()

result = app.invoke({
    "email_subject": "Update on my application status",
    "decision": "",
    "reasoning": "",
    "verified": False,
    "retry_count": 0,
})

print("\nFinal result:", result)