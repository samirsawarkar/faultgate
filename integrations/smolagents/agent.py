"""Support agent with 3 fake tools (smolagents recipe). Data lives in a dict."""
import json
import os

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from smolagents import OpenAIServerModel, ToolCallingAgent, tool

ORDERS = {
    "A1": {"order_id": "A1", "status": "pending", "customer_id": "C1", "price": 300},
    "B2": {"order_id": "B2", "status": "delivered", "customer_id": "C2", "price": 900},
}


def lookup_order(order_id):
    """Return the order details, or an error if the order does not exist."""
    return ORDERS.get(order_id, {"error": "order not found"})


def make_tools(lookup=lookup_order):
    """Build the 3 tools. `lookup` can be swapped to simulate a broken service."""

    @tool
    def lookup_order(order_id: str) -> str:
        """Look up an order.

        Args:
            order_id: The id of the order.
        """
        return json.dumps(lookup(order_id))

    @tool
    def cancel_order(order_id: str, reason: str) -> str:
        """Cancel an order.

        Args:
            order_id: The id of the order.
            reason: Why the order is cancelled.
        """
        return json.dumps({"order_id": order_id, "status": "cancelled"})

    @tool
    def issue_refund(order_id: str, amount: float) -> str:
        """Refund an order.

        Args:
            order_id: The id of the order.
            amount: The amount to refund.
        """
        return json.dumps({"order_id": order_id, "refunded": amount})

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
                    {"key": k, "value": _attr(v)} for k, v in s.attributes.items()
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
SmolagentsInstrumentor().instrument(tracer_provider=PROVIDER)


def run_agent(user_request, lookup=lookup_order, max_steps=8):
    """Run one request. Returns (final answer, number of tool calls made)."""
    model = OpenAIServerModel(
        model_id=MODEL, api_base=BASE_URL, api_key=os.environ["AICREDITS_API_KEY"]
    )
    agent = ToolCallingAgent(
        tools=make_tools(lookup),
        model=model,
        instructions=SYSTEM_PROMPT,
        max_steps=max_steps,
        verbosity_level=0,
    )
    answer = agent.run(user_request)
    calls = sum(
        1
        for step in agent.memory.steps
        for tc in (getattr(step, "tool_calls", None) or [])
    )
    return answer, calls


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