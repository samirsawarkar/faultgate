"""Support agent with 3 fake tools (LangGraph recipe). Data lives in a dict."""
import json
import os

from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

ORDERS = {
    "A1": {"order_id": "A1", "status": "pending", "customer_id": "C1", "price": 300},
    "B2": {"order_id": "B2", "status": "delivered", "customer_id": "C2", "price": 900},
}


def lookup_order(order_id):
    """Return the order details, or an error if the order does not exist."""
    return ORDERS.get(order_id, {"error": "order not found"})


def make_tools(lookup=lookup_order):
    """Build the 3 tools. `lookup` can be swapped to simulate a broken service."""

    def lookup_order(order_id: str) -> dict:
        """Look up an order."""
        return lookup(order_id)

    def cancel_order(order_id: str, reason: str) -> dict:
        """Cancel an order."""
        return {"order_id": order_id, "status": "cancelled"}

    def issue_refund(order_id: str, amount: float) -> dict:
        """Refund an order."""
        return {"order_id": order_id, "refunded": amount}

    return [lookup_order, cancel_order, issue_refund]


def _attr(value):
    """Turn a Python value into an OTLP/JSON attribute value."""
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    return {"stringValue": str(value)}


SINGLE_ARG = {"lookup_order": "order_id"}  # tools with one argument are recorded as a bare value


def _clean_tool_io(name, attrs):
    """Make TOOL spans readable by faultgate: JSON arguments in, plain JSON result out."""
    attrs = dict(attrs)
    if attrs.get("openinference.span.kind") != "TOOL":
        return attrs
    raw_in = str(attrs.get("input.value", ""))
    if not raw_in.startswith("{") and name in SINGLE_ARG:
        attrs["input.value"] = json.dumps({SINGLE_ARG[name]: raw_in})
    try:  # LangGraph wraps the result in a tool message; keep only its content
        attrs["output.value"] = json.loads(attrs["output.value"])["data"]["content"]
    except (KeyError, ValueError, TypeError):
        pass
    return attrs


class JsonFileExporter(SpanExporter):
    """Collect finished spans, then save them as one OTLP/JSON file."""

    def __init__(self):
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def save(self, path):
        out = []
        for s in self.spans:
            ctx = s.get_span_context()
            item = {
                "traceId": format(ctx.trace_id, "032x"),
                "spanId": format(ctx.span_id, "016x"),
                "name": s.name,
                "startTimeUnixNano": str(s.start_time),
                "endTimeUnixNano": str(s.end_time),
                "attributes": [
                    {"key": k, "value": _attr(v)}
                    for k, v in _clean_tool_io(s.name, s.attributes).items()
                ],
            }
            if s.parent is not None:
                item["parentSpanId"] = format(s.parent.span_id, "016x")
            out.append(item)
        with open(path, "w") as f:
            json.dump({"resourceSpans": [{"scopeSpans": [{"spans": out}]}]}, f, indent=1)

BASE_URL = "https://aicredits.in/v1"
MODEL = os.environ.get("MODEL", "openai/gpt-6-luna")
SYSTEM_PROMPT = (
    "You are a customer support agent. Use the tools. "
    "Always look up an order before you cancel or refund it."
)

# Turn on tracing: save every span in memory.
EXPORTER = JsonFileExporter()
PROVIDER = TracerProvider()
PROVIDER.add_span_processor(SimpleSpanProcessor(EXPORTER))
LangChainInstrumentor().instrument(tracer_provider=PROVIDER)


def run_agent(user_request, lookup=lookup_order, max_steps=8):
    """Run one request. Returns (final answer, number of tool calls made)."""
    tools = make_tools(lookup)
    llm = ChatOpenAI(
        model=MODEL, base_url=BASE_URL, api_key=os.environ["AICREDITS_API_KEY"]
    ).bind_tools(tools)

    def call_model(state):
        return {"messages": [llm.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    app = graph.compile()

    result = app.invoke(
        {"messages": [("system", SYSTEM_PROMPT), ("user", user_request)]},
        config={"recursion_limit": max_steps * 2 + 1},
    )
    messages = result["messages"]
    calls = sum(isinstance(m, ToolMessage) for m in messages)
    return messages[-1].content, calls


SCENARIOS = {
    "clean": ("Please cancel order A1, I ordered it by mistake.", lookup_order),
    "faulty": ("Please cancel order A1, I ordered it by mistake.",
               lambda order_id: {"error": "lookup service unavailable"}),
    "violation": ("Please refund 900 on order B2.", lookup_order),
}


def main():
    """Run the 3 scenarios and save one trace file for each."""
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, os.environ.get("TRACES_DIR", "traces"))
    os.makedirs(out_dir, exist_ok=True)
    for name, (request, lookup) in SCENARIOS.items():
        EXPORTER.spans.clear()  # start each trace file empty
        answer, calls = run_agent(request, lookup=lookup)
        EXPORTER.save(os.path.join(out_dir, name + ".json"))
        print(f"{name}: {calls} tool calls, {len(EXPORTER.spans)} spans saved")


if __name__ == "__main__":
    main()