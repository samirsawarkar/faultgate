"""Support agent with 3 fake tools (LiteLLM recipe). Data lives in a dict."""

ORDERS = {
    "A1": {"order_id": "A1", "status": "pending", "customer_id": "C1", "price": 300},
    "B2": {"order_id": "B2", "status": "delivered", "customer_id": "C2", "price": 900},
}


def lookup_order(order_id):
    """Return the order details, or an error if the order does not exist."""
    return ORDERS.get(order_id, {"error": "order not found"})


def cancel_order(order_id, reason):
    """Pretend to cancel an order."""
    return {"order_id": order_id, "status": "cancelled"}


def issue_refund(order_id, amount):
    """Pretend to refund an amount."""
    return {"order_id": order_id, "refunded": amount}


TOOLS = {
    "lookup_order": lookup_order,
    "cancel_order": cancel_order,
    "issue_refund": issue_refund,
}

import json

from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


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

import os

import litellm
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

BASE_URL = "https://aicredits.in/v1"
MODEL = os.environ.get("MODEL", "openai/gpt-6-luna")  # LiteLLM sees "openai/" + MODEL (an OpenAI-style server)
SYSTEM_PROMPT = (
    "You are a customer support agent. Use the tools. "
    "Always look up an order before you cancel or refund it."
)

# Turn on tracing: save every span (model calls + tool calls) in memory.
EXPORTER = JsonFileExporter()
PROVIDER = TracerProvider()
PROVIDER.add_span_processor(SimpleSpanProcessor(EXPORTER))
LiteLLMInstrumentor().instrument(tracer_provider=PROVIDER)  # records model calls
TRACER = PROVIDER.get_tracer("support_agent")


def _schema(name, desc, props):
    params = {"type": "object", "properties": props, "required": list(props)}
    return {"type": "function", "function": {"name": name, "description": desc, "parameters": params}}


_S = {"type": "string"}
TOOL_SCHEMAS = [
    _schema("lookup_order", "Look up an order.", {"order_id": _S}),
    _schema("cancel_order", "Cancel an order.", {"order_id": _S, "reason": _S}),
    _schema("issue_refund", "Refund an order.", {"order_id": _S, "amount": {"type": "number"}}),
]


def run_tool(name, args, tools):
    """Run one tool and record it as a TOOL span (what faultgate reads)."""
    with TRACER.start_as_current_span(name) as span:
        span.set_attribute("openinference.span.kind", "TOOL")
        span.set_attribute("tool.name", name)
        span.set_attribute("input.value", json.dumps(args))
        try:
            result = tools[name](**args) if name in tools else {"error": "unknown tool"}
        except TypeError:
            result = {"error": "bad arguments"}
        span.set_attribute("output.value", json.dumps(result))
    return result


def run_agent(user_request, system_prompt=SYSTEM_PROMPT, tools=TOOLS, max_steps=8):
    """Run one request. Returns (final answer, number of tool calls made)."""
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}]
    answer, calls = "", 0
    with TRACER.start_as_current_span("support_agent") as root:
        root.set_attribute("openinference.span.kind", "AGENT")
        root.set_attribute("input.value", user_request)
        for _ in range(max_steps):
            reply = litellm.completion(
                model="openai/" + MODEL, api_base=BASE_URL,
                api_key=os.environ["AICREDITS_API_KEY"],
                messages=messages, tools=TOOL_SCHEMAS,
            ).choices[0].message
            messages.append(reply)
            if not reply.tool_calls:
                answer = reply.content or ""
                break
            for call in reply.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = run_tool(call.function.name, args, tools)
                calls += 1
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})
        root.set_attribute("output.value", answer)
    return answer, calls

SCENARIOS = {
    "clean": ("Please cancel order A1, I ordered it by mistake.", TOOLS),
    "faulty": ("Please cancel order A1, I ordered it by mistake.",
               {**TOOLS, "lookup_order": lambda order_id: {"error": "lookup service unavailable"}}),
    "violation": ("Please refund 900 on order B2.", TOOLS),
}


def main():
    """Run the 3 scenarios and save one trace file for each."""
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.environ.get("TRACES_DIR", "traces"))
    os.makedirs(out_dir, exist_ok=True)
    for name, (request, tools) in SCENARIOS.items():
        EXPORTER.spans.clear()  # start each trace file empty
        answer, calls = run_agent(request, tools=tools)
        EXPORTER.save(os.path.join(out_dir, name + ".json"))
        print(f"{name}: {calls} tool calls, {len(EXPORTER.spans)} spans saved")


if __name__ == "__main__":
    main()
