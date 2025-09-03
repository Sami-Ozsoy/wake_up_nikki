from typing import TypedDict, Literal, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY

from utils.loaders import load_prompt
MAIN_PROMPT = load_prompt("prompts/main_prompt.txt")

# Basit LLM tabanlı niyet sınıflandırıcı promptu
_INTENT_SYSTEM = (
    "You are a classifier. Decide if the user's request is about Teltonika FMB devices, "
    "commands or parameters (including FMB120/FMB130/FM130). "
    "Check the dialogue in the conversation and determine whether the user's question is a general conversation or one about the FMB 130 device, depending on its subject. Remember, the user can ask multiple and consecutive questions about the FMB 130. "
)

@tool("search_fmb_docs")
def search_fmb_docs(query: str, k: int = 6) -> List[str]:
    """
    FMB belgelerinden ilgili pasajları döndürür.
    """
    from vector.vector_store import VectorStore
    vs = VectorStore(index_path="vector/index")
    results = vs.similarity_search_with_score(query, k=k)
    high_quality = [doc for (doc, score) in results if score > 0.7]
    if not high_quality:
        high_quality = [doc for (doc, _) in results]
    return [doc.page_content for doc in high_quality]

class GraphState(TypedDict):
    messages: List[dict]
    intent: Optional[Literal["fmb", "general", "unknown"]]
    context_docs: Optional[List[str]]
    history_text: Optional[str]

def classify_intent(user_msg: str, history_text: str) -> Literal["fmb", "general"]:
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    prompt = (
        f"{_INTENT_SYSTEM}\n\n"
        f"History:\n{history_text}\n\n"
        f"User:\n{user_msg}\n\n"
        "Answer:"
    )
    label = llm.invoke(prompt).content.strip().lower()
    return "fmb" if "fmb" in label or "teltonika" in label else "general"

def router_node(state: GraphState) -> GraphState:
    user_msg = state["messages"][-1]["content"]
    history_text = state.get("history_text") or ""
    state["intent"] = classify_intent(user_msg, history_text)
    return state

def fmb_agent_node(state: GraphState) -> GraphState:
    query = state["messages"][-1]["content"]
    docs = search_fmb_docs.invoke({"query": query, "k": 6})
    state["context_docs"] = docs
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

    docs_content = "\n\n".join(docs) if docs else ""
    history_text = state.get("history_text") or ""
    combined_context = f"{docs_content}\n\n{history_text}".strip()

    formatted_prompt = MAIN_PROMPT.format(context=combined_context, question=query)
    answer = llm.invoke(formatted_prompt).content
    state["messages"].append({"role": "assistant", "content": answer})
    return state

def general_agent_node(state: GraphState) -> GraphState:
    query = state["messages"][-1]["content"]
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)
    answer = llm.invoke(query).content
    state["messages"].append({"role": "assistant", "content": answer})
    return state

def build_graph():
    g = StateGraph(GraphState)
    g.add_node("router", router_node)
    g.add_node("fmb_agent", fmb_agent_node)
    g.add_node("general_agent", general_agent_node)
    g.set_entry_point("router")

    def route_decider(state: GraphState):
        return "to_fmb" if state["intent"] == "fmb" else "to_general"

    g.add_conditional_edges(
        "router",
        route_decider,
        {"to_fmb": "fmb_agent", "to_general": "general_agent"},
    )
    g.add_edge("fmb_agent", END)
    g.add_edge("general_agent", END)
    return g.compile()

graph = build_graph()

def invoke_graph(user_input: str, history_text: str) -> str:
    initial = {
        "messages": [{"role": "user", "content": user_input}],
        "intent": None,
        "context_docs": None,
        "history_text": history_text
    }
    result = graph.invoke(initial)
    return result["messages"][-1]["content"]