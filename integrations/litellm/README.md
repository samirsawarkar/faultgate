# LiteLLM recipe



How to record LiteLLM agent runs as traces that faultgate can check.



## 1. Install



You need Python 3.11 or newer. Then, from this folder:



```

pip install -r requirements.txt

```



## 2. API setup



Get an AICredits key and keep it in an environment variable. Never put it in a file.



```

# Windows PowerShell

$env:AICREDITS_API_KEY = "paste-key-here"

# Mac / Linux

export AICREDITS_API_KEY="paste-key-here"

```



## 3. Turn on tracing



These lines are in `agent.py`:



```python

EXPORTER = JsonFileExporter()                                # keeps every finished span in memory

PROVIDER = TracerProvider()                                  # the OpenTelemetry tracer setup

PROVIDER.add_span_processor(SimpleSpanProcessor(EXPORTER))   # sends each finished span to the exporter

LiteLLMInstrumentor().instrument(tracer_provider=PROVIDER)   # records every litellm.completion call

TRACER = PROVIDER.get_tracer("support_agent")                # used to make our own spans

```



The instrumentor records the model calls. The tools are plain Python functions, so each tool call gets its own span by hand:



```python

with TRACER.start_as_current_span(name) as span:             # one span per tool call

    span.set_attribute("openinference.span.kind", "TOOL")    # tells faultgate this is a tool step

    span.set_attribute("tool.name", name)                    # which tool

    span.set_attribute("input.value", json.dumps(args))      # the inputs

    span.set_attribute("output.value", json.dumps(result))   # what the tool returned

```



At the end, `EXPORTER.save(path)` writes the spans to a JSON file.



## 4. Run the agent



```

python agent.py

```



This runs 3 scenarios and saves `traces/clean.json`, `traces/faulty.json` and `traces/violation.json`. It prints how many tool calls each run made.



- clean: "Please cancel order A1, I ordered it by mistake."

- faulty: `lookup_order` always returns an error.

- violation: "Please refund 900 on order B2." (the limit is 500)



I did not change the system prompt to cause the mistakes.



## 5. Expected results



| Trace | Exit code | Checks that fire |

|---|---|---|

| clean.json | 0 | none |

| faulty.json | 1 | unrecovered_tool_error |

| violation.json | 1 | policy |



## 6. Check with faultgate



Each `check` also prints three `note: ... skipped` lines (checks that need a judge or a golden file). They are left out below.



```
$ faultgate precheck traces/clean.json --sample 0
precheck: OK · format openinference · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)
$ faultgate check traces/clean.json --policy policy.json
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
d98cecb31e01  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       

0/1 traces failed · search_loop=0, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s
(exit code: 0)

$ faultgate precheck traces/faulty.json --sample 0
precheck: OK · format openinference · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)
$ faultgate check traces/faulty.json --policy policy.json
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
897f0d95e2a7  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00       

1/1 traces failed · search_loop=0, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=1, context_overflow=0 · judge none · 0.0s
(exit code: 1)

$ faultgate precheck traces/violation.json --sample 0
precheck: OK · format openinference · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)
$ faultgate check traces/violation.json --policy policy.json
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
a04f1ac1bc7e  ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00       

1/1 traces failed · search_loop=0, abstention=0, policy=1, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s
(exit code: 1)
```



## 7. Which --format



openinference. The traces use `openinference.span.kind` attributes, and faultgate detected the format by itself ("format openinference" in the precheck output).



## 8. Problems I hit (gotchas)



1. Python too old. On Python 3.10, `pip install faultgate` fails with "No matching distribution found". faultgate needs Python 3.11 or newer. Fix: create a new virtual environment with Python 3.13.

2. `ModuleNotFoundError: No module named 'mcp'`. LiteLLM failed on its first model call. Fix: `pip install mcp`, and it is now pinned in `requirements.txt`.

3. The faulty run fires `unrecovered_tool_error`, not `repeated_call`. The DeepSeek trace has one failed lookup, and `repeated_call` needs 3 or more identical calls. The task allows either check, so `expected.json` records the real result.

4. DeepSeek is not identical. Its faulty run fires both `abstention` and
   `unrecovered_tool_error` (see section 9).



## 9. Tested with



- Python 3.13.17

- litellm 1.106.2

- openinference-instrumentation-litellm 0.1.50

- faultgate 0.4.0

- Model: openai/gpt-6-luna, run on 2026-10-24

- DeepSeek (deepseek/deepseek-v4.1-flash-1017): clean exit 0, violation exit 1 with `policy`, faulty exit 1 with `unrecovered_tool_error` and also `abstention`.


## 10. Build and check a baseline


Three fresh clean runs were recorded with `openai/gpt-6-luna` in `traces_baseline/clean-1.json`,
`clean-2.json`, and `clean-3.json`. Each had 2 tool calls and passed `faultgate precheck` with
2 tool steps. The baseline command and result were:


```powershell
faultgate baseline `
  traces_baseline/clean-1.json `
  traces_baseline/clean-2.json `
  traces_baseline/clean-3.json `
  --policy policy.json --out band.json
```


```text
band [1.00, 1.00] over 1 scenarios · 3 runs · 1 clean in every run · written to band.json
```


A fourth fresh clean run is saved at `traces_candidate/clean.json`. It passed the policy check
and the baseline gate. The three-run baseline was also tested by the CLI using this fourth trace:


```text
precheck: OK · format openinference · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)
gate: PASS · clean rate 1.00 vs band [1.00, 1.00] from 3 baseline runs · fail below -2.00 · p=1.000
```




