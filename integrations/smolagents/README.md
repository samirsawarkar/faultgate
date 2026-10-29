# smolagents recipe



## 1. What this is



How to record smolagents agent runs as traces that faultgate can check.



## 2. Install



```

pip install -r requirements.txt

```



## 3. API setup



The agent reads your key from the environment variable `AICREDITS_API_KEY`. Never write the real key in a file.



Windows PowerShell:



```

$env:AICREDITS_API_KEY = "your-key-here"

```



macOS / Linux:



```

export AICREDITS_API_KEY="your-key-here"

```



## 4. Turn on tracing



These lines are in `agent.py`:



```python

EXPORTER = JsonFileExporter()  # keeps every finished span in memory

PROVIDER = TracerProvider()  # the OpenTelemetry tracer

PROVIDER.add_span_processor(SimpleSpanProcessor(EXPORTER))  # send each span to our exporter

SmolagentsInstrumentor().instrument(tracer_provider=PROVIDER)  # records the agent run

```



`JsonFileExporter` saves the spans as one OTLP/JSON file.



The agent is a `ToolCallingAgent` that talks to the model through `OpenAIServerModel` pointed at the provider URL, so the recipe works with any OpenAI-style server.



## 5. Run the agent



```

python agent.py

```



It runs 3 scenarios and writes `traces/clean.json`, `traces/faulty.json` and `traces/violation.json`.



## 6. Check with faultgate



Run these from this folder. The output below is real and unchanged.



```text

$ faultgate precheck traces/clean.json --sample 0

precheck: OK · format openinference · checked 1 of 1 traces · 3 tool steps read · 0 error(s), 0 warning(s)

$ faultgate check traces/clean.json --policy policy.json

note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ

note: wrong_answer skipped — it needs --golden golden.json (expected answers)

note: truncation skipped — it needs --golden golden.json (expected answers)

trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow

------------------------------------------------------------------------------------------------------------------------------

5a7e3ad12f82  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       ok   1.00       



0/1 traces failed · search_loop=0, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s



$ faultgate precheck traces/faulty.json --sample 0

precheck: OK · format openinference · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)

$ faultgate check traces/faulty.json --policy policy.json

note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ

note: wrong_answer skipped — it needs --golden golden.json (expected answers)

note: truncation skipped — it needs --golden golden.json (expected answers)

trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow

------------------------------------------------------------------------------------------------------------------------------

c129f523ae01  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00       ok   1.00       



1/1 traces failed · search_loop=0, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=1, context_overflow=0 · judge none · 0.0s



$ faultgate precheck traces/violation.json --sample 0

precheck: OK · format openinference · checked 1 of 1 traces · 3 tool steps read · 0 error(s), 0 warning(s)

$ faultgate check traces/violation.json --policy policy.json

note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ

note: wrong_answer skipped — it needs --golden golden.json (expected answers)

note: truncation skipped — it needs --golden golden.json (expected answers)

trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow

------------------------------------------------------------------------------------------------------------------------------

a4dd85900eae  ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00       ok   1.00       



1/1 traces failed · search_loop=0, abstention=0, policy=1, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s

```



What each trace shows:



- `clean`: nothing fires (exit code 0).

- `faulty`: `unrecovered_tool_error` fires (exit code 1). The order lookup is broken on purpose, and the agent does not recover.

- `violation`: `policy` fires (exit code 1). The agent refunds 900 on order B2, and the policy does not allow that.



## 7. Which --format to use



Use `openinference`. The OpenInference smolagents instrumentation writes OpenInference attributes, and faultgate detects the format by itself (`precheck` prints `format openinference`). You can also pass `--format openinference` to be explicit.



## 8. Problems I hit (gotchas)



1. **The instrumentation records tool calls by itself.** Unlike the LiteLLM recipe, no hand-made tool spans are needed. Each tool call becomes a TOOL span named after the tool.

2. **`final_answer` is recorded as a tool call.** smolagents agents finish by calling a built-in tool named `final_answer`, and it shows up as a tool step in the trace. The first check failed `policy` on the clean run with "tool 'final_answer' not in allowlist" (step 3). Fix: this recipe's `policy.json` adds `final_answer` to the `allow` list. The other recipes do not need that.

3. **Tools need a docstring with an `Args:` section.** The `@tool` decorator of smolagents refuses a tool whose docstring does not describe every argument.

4. **The faulty run fires `unrecovered_tool_error`, not `repeated_call`.** `repeated_call` needs 3 or more tool calls. The faulty run makes only 1 real tool call, plus `final_answer`.

5. **Python version.** Faultgate needs Python 3.11 or newer.



## 9. Tested with



- Python 3.13.17

- smolagents 1.26.0

- openai 3.37.0

- openinference-instrumentation-smolagents 0.1.43

- opentelemetry-sdk 1.45.1

- faultgate 0.4.0

- Model: `openai/gpt-6-luna`

- Date: 2026-10-25


## 10. DeepSeek run


Run the same scenarios with DeepSeek and save their traces separately:


```powershell
$env:MODEL = "deepseek/deepseek-v4.1-flash-1017"
$env:TRACES_DIR = "traces_deepseek"
python agent.py
```


These are real runs. `faultgate precheck --sample 0` read 3 / 2 / 3 tool steps from
`clean.json`, `faulty.json`, and `violation.json`. The agent's printed calls also match at
3 / 2 / 3. `faultgate check` returned exit codes 0 / 1 / 1; the faulty trace fired
`unrecovered_tool_error`, and the violation trace fired `policy`.

