"""Support agent that exports OpenInference spans through local Arize Phoenix."""
import argparse
import json
import os
from pathlib import Path

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

os.environ.setdefault("PHOENIX_WORKING_DIR", str(Path(__file__).resolve().parent / ".phoenix-data"))
from phoenix.otel import register

ORDERS = {
    "A1": {"order_id": "A1", "status": "pending", "customer_id": "C1", "price": 300},
    "B2": {"order_id": "B2", "status": "delivered", "customer_id": "C2", "price": 900},
}
BASE_URL = "https://aicredits.in/v1"
MODEL = os.environ.get("MODEL", "openai/gpt-6-luna")
SYSTEM_PROMPT = (
    "You are a customer support agent. Use the tools. "
    "Always look up an order before you cancel or refund it. "
    "If a lookup returns an error, do not cancel or refund the order."
)
TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "lookup_order", "description": "Look up an order.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}},
    {"type": "function", "function": {"name": "cancel_order", "description": "Cancel an order.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}, "reason": {"type": "string"}},
                     "required": ["order_id", "reason"]}}},
    {"type": "function", "function": {"name": "issue_refund", "description": "Refund an order.",
     "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}},
                     "required": ["order_id", "amount"]}}},
]


def lookup_order(order_id):
    """Return one order as a JSON object or a not-found error."""
    return ORDERS.get(order_id, {"error": "order not found"})


class JsonFileExporter(SpanExporter):
    """Keep finished spans in memory and save them as OpenInference OTLP/JSON."""

    def __init__(self):
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def save(self, path):
        def value(v):
            if isinstance(v, bool):
                return {"boolValue": v}
            if isinstance(v, int):
                return {"intValue": str(v)}
            if isinstance(v, float):
                return {"doubleValue": v}
            return {"stringValue": str(v)}

        items = []
        for span in self.spans:
            ctx = span.get_span_context()
            item = {
                "traceId": format(ctx.trace_id, "032x"),
                "spanId": format(ctx.span_id, "016x"),
                "name": span.name,
                "startTimeUnixNano": str(span.start_time),
                "endTimeUnixNano": str(span.end_time),
                "attributes": [{"key": key, "value": value(v)} for key, v in span.attributes.items()],
            }
            if span.parent is not None:
                item["parentSpanId"] = format(span.parent.span_id, "016x")
            items.append(item)
        payload = {"resourceSpans": [{"scopeSpans": [{"spans": items}]}]}
        Path(path).write_text(json.dumps(payload, indent=1), encoding="utf-8")


# Register with a local Phoenix collector and keep a local copy for Faultgate.
PROVIDER = register(
    project_name="faultgate-phoenix",
    endpoint=os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://127.0.0.1:6006/v1/traces"),
    protocol="http/protobuf",
    auto_instrument=True,
)
EXPORTER = JsonFileExporter()
PROVIDER.add_span_processor(SimpleSpanProcessor(EXPORTER), replace_default_processor=False)
TRACER = trace.get_tracer(__name__)
CLIENT = OpenAI(base_url=BASE_URL, api_key=os.environ["AICREDITS_API_KEY"])


def run_tool(name, args, lookup):
    """Run and record one of the three local fake tools."""
    with TRACER.start_as_current_span(name) as span:
        span.set_attribute("openinference.span.kind", "TOOL")
        span.set_attribute("tool.name", name)
        span.set_attribute("tool.parameters", json.dumps(args))
        if name == "lookup_order":
            result = lookup(args["order_id"])
        elif name == "cancel_order":
            result = {"order_id": args["order_id"], "status": "cancelled"}
        elif name == "issue_refund":
            result = {"order_id": args["order_id"], "refunded": args["amount"]}
        else:
            result = {"error": "unknown tool"}
        span.set_attribute("output.value", json.dumps(result))
        return result


def run_agent(user_request, scenario, lookup=lookup_order, max_steps=8):
    """Run one request. Returns (final answer, number of tool calls made)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_request}]
    calls = 0
    with TRACER.start_as_current_span("support_agent") as root:
        root.set_attribute("openinference.span.kind", "AGENT")
        root.set_attribute("metadata", json.dumps({"scenario": scenario}))
        root.set_attribute("input.value", user_request)
        for _ in range(max_steps):
            response = CLIENT.chat.completions.create(model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
            reply = response.choices[0].message
            messages.append(reply.model_dump(exclude_none=True))
            if not reply.tool_calls:
                answer = reply.content or ""
                root.set_attribute("output.value", answer)
                return answer, calls
            for call in reply.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = run_tool(call.function.name, args, lookup)
                calls += 1
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
    return "The request could not be completed.", calls


SCENARIOS = {
    "clean": ("Please cancel order A1, I ordered it by mistake.", lookup_order),
    "faulty": ("Please cancel order A1, I ordered it by mistake.",
               lambda order_id: {"error": "lookup service unavailable"}),
    "violation": ("Please refund 900 on order B2.", lookup_order),
}


def save_run(name, output):
    request, lookup = SCENARIOS[name]
    EXPORTER.spans.clear()
    answer, calls = run_agent(request, name, lookup=lookup)
    PROVIDER.force_flush()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    EXPORTER.save(output)
    print(f"{name}: {calls} tool calls, {len(EXPORTER.spans)} spans saved to {output}")


def main():
    parser = argparse.ArgumentParser(description="Run the support agent and save local Phoenix traces.")
    parser.add_argument("--scenario", choices=(*SCENARIOS, "all"), default="all")
    parser.add_argument("--runs", type=int, default=1, help="repeat the selected scenario")
    parser.add_argument("--output-dir", default=os.environ.get("TRACES_DIR", "traces"))
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    for name in names:
        for index in range(1, args.runs + 1):
            filename = f"{name}.json" if args.runs == 1 else f"{name}-{index}.json"
            save_run(name, Path(args.output_dir) / filename)
    PROVIDER.force_flush()


if __name__ == "__main__":
    main()
