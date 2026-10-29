# Arize Phoenix recipe

How to capture a real support-agent run through Arize Phoenix and check the resulting
OpenInference trace with Faultgate. Phoenix receives the spans locally; the recipe also saves
an OTLP/JSON copy so checks can run offline.

## 1. Install

Use Python 3.11 or newer, create a virtual environment, and install the pinned requirements:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. API setup

Set the AICredits key in the current shell. Do not save it in a file:

```powershell
$env:AICREDITS_API_KEY = "your-key-here"
```

## 3. Start Phoenix

In a second terminal, from this recipe folder, start the local Phoenix server:

```powershell
$env:PHOENIX_WORKING_DIR = "$PWD\.phoenix-data"
phoenix serve
```

Phoenix listens on `http://localhost:6006`. The data directory is local and ignored by Git.

## 4. Turn on tracing

`agent.py` calls `phoenix.otel.register(project_name="faultgate-phoenix", auto_instrument=True)`
to export OpenAI model spans to the local collector. It records each fake tool call as an
OpenInference TOOL span and saves a local copy for Faultgate.

## 5. Run the agent

With Phoenix running, execute:

```powershell
python agent.py
```

The script records the `clean`, `faulty`, and `violation` scenarios in `traces/`. It accepts
`--scenario clean|faulty|violation|all`, `--runs N`, and `--output-dir DIR` for repeatable runs.
The tested local Phoenix project received all three traces under `faultgate-phoenix`.

Actual output from the run:

```text
$ python integrations/phoenix/agent.py --scenario all --output-dir integrations/phoenix/traces
clean: 2 tool calls, 6 spans saved to integrations\phoenix\traces\clean.json
faulty: 1 tool calls, 4 spans saved to integrations\phoenix\traces\faulty.json
violation: 2 tool calls, 6 spans saved to integrations\phoenix\traces\violation.json
```

## 6. Expected results

| Trace | Exit code | Checks that fire |
| --- | ---: | --- |
| `clean.json` | 0 | none |
| `faulty.json` | 1 | `abstention`, `unrecovered_tool_error` |
| `violation.json` | 1 | `policy` |

These results come from real runs using `openai/gpt-6-luna`. The faulty case can also fire
`abstention` because the model gives up after the lookup service error.

## 7. Check with Faultgate

Run the checks from this folder:

```powershell
faultgate precheck traces/clean.json --sample 0
faultgate check traces/clean.json --policy policy.json
faultgate check traces/faulty.json --policy policy.json
faultgate check traces/violation.json --policy policy.json
```

The saved traces are OpenInference JSON and can be checked without Phoenix or an API key.

Key lines from the actual checks:

```text
$ faultgate precheck integrations/phoenix/traces/clean.json --sample 0
precheck: OK · format openinference · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)

$ faultgate check integrations/phoenix/traces/clean.json --policy integrations/phoenix/policy.json
0/1 traces failed · search_loop=0, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s

$ faultgate check integrations/phoenix/traces/faulty.json --policy integrations/phoenix/policy.json
1/1 traces failed · search_loop=0, abstention=1, policy=0, repeated_call=0, unrecovered_tool_error=1, context_overflow=0 · judge none · 0.0s

$ faultgate check integrations/phoenix/traces/violation.json --policy integrations/phoenix/policy.json
1/1 traces failed · search_loop=0, abstention=0, policy=1, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s
```

## 8. Problems I hit (gotchas)

1. The Phoenix server must be running for the OpenTelemetry exporter to send spans to its local
   collector. The local exporter must be added with `replace_default_processor=False` so it does
   not replace Phoenix's network exporter. The recipe also saves a local trace copy so a later
   `faultgate check` does not need the server.
2. OpenInference's automatic OpenAI instrumentation records model calls; the recipe adds TOOL
   spans manually because the local Python functions are not framework tools.
3. The faulty run produces both `abstention` and `unrecovered_tool_error` with the tested model.

## 9. Tested with

- Python 3.13.17
- Arize Phoenix 20.26.0
- arize-phoenix-otel 0.17.2
- openinference-instrumentation-openai 0.1.66
- OpenAI SDK 3.37.0
- opentelemetry-sdk 1.45.1
- faultgate 0.4.0
- Model: `openai/gpt-6-luna`
- Date: 2026-10-26
