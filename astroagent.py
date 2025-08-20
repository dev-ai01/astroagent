from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from tools import get_chart_positions, fetch_horoscope, generate_final_prediction

class AgentState(TypedDict):
    name: str
    birth_date: str
    birth_time: str
    city_name: str
    moon_sign: Optional[str]
    ascendant: Optional[str]
    asc_data: Optional[str]
    moon_data: Optional[str]
    prediction: Optional[str]

# Node 1: Calculate Asc + Moon
def astro_node(state: AgentState):
    result = get_chart_positions(
        state["birth_date"], state["birth_time"], state["city_name"]
    )
    state["ascendant"] = result["Ascendant"]["sign"]
    state["moon_sign"] = result["Moon"]["sign"]
    return state

# Node 2: Web Search
def search_node(state: AgentState):
    state["asc_data"] = fetch_horoscope(state["ascendant"], "ascendant")
    state["moon_data"] = fetch_horoscope(state["moon_sign"], "moon")
    return state

# Node 3: LLM Summarizer
def llm_node(state: AgentState):
    state["prediction"] = generate_final_prediction(
        state["name"], state["ascendant"], state["moon_sign"],
        state["asc_data"], state["moon_data"]
    )
    return state

# Build graph
graph = StateGraph(AgentState)
graph.add_node("astro", astro_node)
graph.add_node("search", search_node)
graph.add_node("llm", llm_node)

graph.set_entry_point("astro")
graph.add_edge("astro", "search")
graph.add_edge("search", "llm")
graph.add_edge("llm", END)

astro_agent = graph.compile()

