# Integration findings

## Summary

Counts below are from actual saved runs. “Calls / steps” lists agent tool calls and the tool steps
read by `faultgate precheck --sample 0`, respectively, in clean / faulty / violation order. The
smolagents count includes its built-in `final_answer` tool, which is recorded as a TOOL span too.
Each recorded call count matches the trace step count. Setup duration was not measured; difficulty
is a rough rating from 1 (easy) to 5 (hard).

| Framework | Model | Tool calls (clean / faulty / violation) | Tool steps read (clean / faulty / violation) | Checks fired (clean / faulty / violation) | Setup | Difficulty |
| --- | --- | --- | --- | --- | --- | ---: |
| LiteLLM | Luna | 2/2/2 | 2/2/2 | none / unrecovered_tool_error / policy | Not timed | 2 |
| LiteLLM | DeepSeek | 2/1/2 | 2/1/2 | none / abstention + unrecovered_tool_error / policy | Not timed | 2 |
| LangGraph | Luna | 2/2/2 | 2/2/2 | none / unrecovered_tool_error / policy | Not timed | 3 |
| LangGraph | DeepSeek | 2/1/2 | 2/1/2 | none / unrecovered_tool_error / policy | Not timed | 3 |
| OpenAI Agents SDK | Luna | 2/1/2 | 2/1/2 | none / unrecovered_tool_error / policy | Not timed | 3 |
| OpenAI Agents SDK | DeepSeek | 2/2/2 | 2/2/2 | none / unrecovered_tool_error / policy | Not timed | 3 |
| smolagents | Luna | 3/2/3 | 3/2/3 | none / unrecovered_tool_error / policy | Not timed | 4 |
| smolagents | DeepSeek | 3/2/3 | 3/2/3 | none / unrecovered_tool_error / policy | Not timed | 4 |
| Arize Phoenix | Luna | 2/1/2 | 2/1/2 | none / abstention + unrecovered_tool_error / policy | Not timed | Not assessed |

The three new DeepSeek trace sets are saved under each recipe's `traces_deepseek/` directory.
The Phoenix OpenInference recipe and its real traces are in `phoenix/`. The saved-trace
integration tests cover the original four recipes; the full suite result of 313 passing tests and
fresh dependency installs was reported in the handoff. This work also ran `tests/test_integrations.py`
before adding Phoenix and DeepSeek evidence; it passed all 12 original cases.

## Baseline example

The LiteLLM README now shows three fresh clean Luna runs used to build a band, followed by a
fourth real clean run checked against that band. The band covered one scenario and three runs;
each baseline run was clean. The candidate precheck read two tool steps and the band gate passed:

```text
band [1.00, 1.00] over 1 scenarios · 3 runs · 1 clean in every run
gate: PASS · clean rate 1.00 vs band [1.00, 1.00] from 3 baseline runs · fail below -2.00 · p=1.000
```

This same-recipe baseline succeeds. A separate cross-framework case below still reproduces a
Faultgate scenario-matching bug.

## Reproducible Faultgate issue

The three real clean traces from LiteLLM, LangGraph, and OpenAI Agents SDK use the same user
request, but `faultgate baseline` reports that the runs share no scenarios. Their OpenInference
root spans encode the prompt in different `input.value` JSON wrappers. The fallback scenario key
hashes the wrapper instead of extracting the same prompt.

Reproduce from the repository root:

```powershell
faultgate baseline `
  integrations/litellm/traces/clean.json `
  integrations/langgraph/traces/clean.json `
  integrations/openai-agents/traces/clean.json `
  --policy integrations/litellm/policy.json
```

Observed result:

```text
faultgate: baseline runs share no scenarios (keys come from faultgate.scenario, gen_ai.agent.id or the prompt)
```

The matching code path is `Trace.prompt` and the OpenInference root mapping in
`src/faultgate/trace.py` and `src/faultgate/formats.py`. A search found no duplicate issue; this
reproduction was filed as [Faultgate issue #18](https://github.com/Faultline-lab/faultgate/issues/18).
It is a report only; the bug has not been fixed in this integration work.

## Three ideas for new users

1. Have `precheck` show the scenario key it selected, so a baseline mismatch names the key used
   by each input trace.
2. Include one baseline example with several repeated runs of the same recipe and prompt,
   followed by a separate candidate run and the real CLI output. The LiteLLM recipe now does this.
3. Add a short CI example beside each recipe so new users can copy a working Action configuration
   without searching the repository root.

## Status against Week 3 deliverables

- Four original recipes include exact dependency pins, policies, expected results, three real
  traces, and nine-section READMEs. Each now has real Luna and DeepSeek results documented.
- A fifth Arize Phoenix recipe includes pinned dependencies, an OpenInference exporter, three real
  traces, and a nine-section README.
- The integration index and LiteLLM GitHub Action example are complete.
- `integrations/smolagents/agent.py` now counts `final_answer` in its printed tool-call total, so
  its output matches the three tool steps that Faultgate reads.
- No files under `src/faultgate/` were changed.
- The baseline-matching bug is reported in issue #18. PR checks #15–#17 are still pending approval,
  according to the handoff status.
