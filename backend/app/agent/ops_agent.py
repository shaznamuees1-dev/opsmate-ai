"""
OpsMate AI - LangGraph Assistant with Groq Integration

Implements a deterministic tool-calling agent using LangGraph and Groq.
Tools:
1. `list_incidents`: filter and retrieve incidents by priority, status, or service.
2. `calculate_sla_risk`: calculate SLA metrics deterministically using Python logic.
"""

import os
import re
from typing import List, Dict, Any, Optional, Sequence, TypedDict, Annotated
import operator

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

from app.models.incident import ChatResponse
from app.services.incident_service import get_incidents_with_sla, get_incident_by_id


# --- Deterministic Core Tools ---

@tool
def list_incidents(
    priority: Optional[str] = None,
    status: Optional[str] = None,
    service: Optional[str] = None,
) -> str:
    """
    List and filter IT incidents.
    Args:
        priority: Filter by priority ('P1', 'P2', 'P3', 'P4').
        status: Filter by status ('Open', 'In Progress', 'Resolved').
        service: Filter by service name (e.g. 'Database', 'Payment Gateway').
    Returns:
        Formatted summary of matching incidents with deterministic SLA status.
    """
    incidents = get_incidents_with_sla(priority=priority, status=status, service=service)
    if not incidents:
        filters = []
        if priority:
            filters.append(f"priority={priority}")
        if status:
            filters.append(f"status={status}")
        if service:
            filters.append(f"service={service}")
        filter_str = f" with {', '.join(filters)}" if filters else ""
        return f"No incidents found{filter_str}."

    lines = [f"Found {len(incidents)} incident(s):"]
    for inc in incidents:
        lines.append(
            f"- [{inc.id}] {inc.title} | Priority: {inc.priority.value} | Status: {inc.status.value} "
            f"| Service: {inc.service} | SLA: {inc.sla.sla_status.value} (Remaining: {inc.sla.remaining_minutes}m, Target: {inc.sla.sla_target_minutes}m) "
            f"| Assigned: {inc.assigned_to}"
        )
    return "\n".join(lines)


@tool
def calculate_sla_risk(incident_id: Optional[str] = None) -> str:
    """
    Calculate SLA risk deterministically using Python logic.
    Args:
        incident_id: Specific incident ID (e.g. 'INC-1001') or None to evaluate all active incidents.
    Returns:
        Exact SLA calculations: elapsed time, remaining time, percentage consumed, and SLA status.
    """
    if incident_id and incident_id.strip() and incident_id.strip().lower() != "all":
        inc = get_incident_by_id(incident_id.strip())
        if not inc:
            return f"Incident '{incident_id}' not found in the incident dataset."

        sla = inc.sla
        return (
            f"Deterministic SLA Assessment for [{inc.id}] {inc.title}:\n"
            f"- SLA Target: {sla.sla_target_minutes} minutes\n"
            f"- Elapsed Time: {sla.elapsed_minutes} minutes\n"
            f"- Remaining Time: {sla.remaining_minutes} minutes\n"
            f"- Consumed: {sla.percentage_consumed}%\n"
            f"- SLA Status: {sla.sla_status.value}\n"
            f"- Breached: {sla.breached}\n"
            f"- Evaluation Notes: {sla.calculation_notes}"
        )

    # If no ID or "all", calculate SLA for all active incidents ranked by urgency (lowest remaining time first)
    active_incidents = [inc for inc in get_incidents_with_sla() if inc.status.value != "Resolved"]
    if not active_incidents:
        return "No active incidents found to evaluate."

    # Sort: Breached and closest to breach first (ascending remaining_minutes)
    ranked = sorted(active_incidents, key=lambda x: x.sla.remaining_minutes)

    lines = ["Deterministic SLA Risk Ranking (Most Urgent First):"]
    for inc in ranked:
        sla = inc.sla
        lines.append(
            f"- [{inc.id}] {inc.title} ({inc.priority.value}) -> SLA: {sla.sla_status.value} "
            f"| Remaining: {sla.remaining_minutes}m | Consumed: {sla.percentage_consumed}% of {sla.sla_target_minutes}m target"
        )
    return "\n".join(lines)


TOOLS = [list_incidents, calculate_sla_risk]
TOOL_MAP = {t.name: t for t in TOOLS}


SYSTEM_PROMPT = """You are OpsMate AI, an intelligent IT Service Management (ITSM) assistant.
Your job is to assist incident managers and engineers by answering questions about active IT incidents, SLA risks, and operational urgency.

CRITICAL RULES:
1. Ground your answers strictly in the data returned by the provided tools (`list_incidents` and `calculate_sla_risk`).
2. NEVER invent, hallucinate, or estimate incident numbers or SLA timings.
3. SLA calculations (elapsed time, remaining time, breach status) are computed deterministically by the Python tools; always quote them accurately.
4. Keep your answers concise, professional, structured (with bullet points where appropriate), and easy to scan for an operations team.
5. If the user asks about P1 incidents, SLA breaches, at-risk incidents, or urgent summaries, call the appropriate tool(s) to fetch the real data before answering.
"""


# --- LangGraph Agent State Definition ---

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    tools_used: Annotated[List[str], operator.add]


def _build_agent_graph(llm_with_tools):
    """Construct a LangGraph StateGraph connecting the model and tool execution."""

    def call_model(state: AgentState) -> Dict[str, Any]:
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)

        new_tools = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name and name not in new_tools:
                    new_tools.append(name)

        return {"messages": [response], "tools_used": new_tools}

    def run_tools(state: AgentState) -> Dict[str, Any]:
        last_message = state["messages"][-1]
        tool_messages: List[ToolMessage] = []

        if hasattr(last_message, "tool_calls"):
            for tc in last_message.tool_calls:
                tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
                tool_args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                call_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", "")

                tool_func = TOOL_MAP.get(tool_name)
                if tool_func:
                    try:
                        content = tool_func.invoke(tool_args)
                    except Exception as e:
                        content = f"Error running tool '{tool_name}': {str(e)}"
                else:
                    content = f"Tool '{tool_name}' is not recognized."

                tool_messages.append(ToolMessage(content=str(content), tool_call_id=call_id))

        return {"messages": tool_messages}

    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", run_tools)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    return workflow.compile()


def sanitize_error(error_message: str) -> str:
    """Remove any potential API keys or secret tokens from error strings."""
    # Mask any gsk_ (Groq) or other token patterns
    sanitized = re.sub(r'gsk_[a-zA-Z0-9_-]{20,}', '[REDACTED_API_KEY]', error_message)
    sanitized = re.sub(r'Bearer\s+[a-zA-Z0-9_\-\.]{20,}', 'Bearer [REDACTED]', sanitized)
    return sanitized


def run_ops_assistant(user_message: str) -> ChatResponse:
    """
    Execute the OpsMate AI assistant on a user query.
    Handles credential verification, Groq model invocation via LangGraph,
    and returns the assistant's answer alongside the invoked tools.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    # Graceful degradation if API key is missing or dummy
    if not api_key or api_key == "your_groq_api_key_here" or api_key.startswith("your_"):
        return ChatResponse(
            response=(
                "Groq API key is not configured. "
                "Please configure GROQ_API_KEY in backend/.env to activate live AI answers. "
                "The incident dashboard, search filters, and deterministic SLA calculations remain fully operational."
            ),
            tools_used=[],
            status="fallback"
        )

    model_name = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()

    try:
        from langchain_groq import ChatGroq

        def _get_working_llm(chosen_model: str):
            return ChatGroq(
                groq_api_key=api_key,
                model_name=chosen_model,
                temperature=0.1,
                max_tokens=512,
            )

        active_model = model_name
        try:
            llm = _get_working_llm(active_model)
            llm_with_tools = llm.bind_tools(TOOLS)
            graph = _build_agent_graph(llm_with_tools)

            initial_state: AgentState = {
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_message),
                ],
                "tools_used": [],
            }
            final_state = graph.invoke(initial_state, {"recursion_limit": 10})
        except Exception as model_err:
            # If the requested model is not found on this account, dynamically detect available chat models
            err_str = str(model_err).lower()
            if "model_not_found" in err_str or "does not exist" in err_str:
                from groq import Groq
                client = Groq(api_key=api_key)
                account_models = [m.id for m in client.models.list().data]
                candidates = ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
                fallback_model = None
                for cand in candidates:
                    if cand in account_models and cand != active_model:
                        fallback_model = cand
                        break
                
                if not fallback_model and account_models:
                    fallback_model = account_models[0]

                if fallback_model:
                    llm = _get_working_llm(fallback_model)
                    llm_with_tools = llm.bind_tools(TOOLS)
                    graph = _build_agent_graph(llm_with_tools)
                    initial_state = {
                        "messages": [
                            SystemMessage(content=SYSTEM_PROMPT),
                            HumanMessage(content=user_message),
                        ],
                        "tools_used": [],
                    }
                    final_state = graph.invoke(initial_state, {"recursion_limit": 10})
                else:
                    raise model_err
            else:
                raise model_err

        # Find final assistant message
        final_response = "I was unable to generate a response."
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                final_response = str(msg.content)
                break

        # Deduplicate tools_used while maintaining order
        raw_tools = final_state.get("tools_used", [])
        unique_tools = []
        for t in raw_tools:
            if t not in unique_tools:
                unique_tools.append(t)

        return ChatResponse(
            response=final_response,
            tools_used=unique_tools,
            status="success"
        )

    except Exception as e:
        safe_msg = sanitize_error(str(e))
        return ChatResponse(
            response=(
                f"OpsMate AI encountered a temporary issue connecting to the Groq AI service: {safe_msg}. "
                "The incident dashboard and SLA calculations continue to work normally."
            ),
            tools_used=[],
            status="error"
        )
