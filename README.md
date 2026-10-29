# faultgate

**A local-first release gate for AI agents.** Hand it the traces your agent recorded, it checks every run for known failure modes, measures your run-to-run noise, and exits non-zero only when a candidate is a real regression. Free, offline, no model required for the default checks.

**Product and examples:** [FAULTLINE faultgate](https://www.faultline-labs.com/products/faultgate/) · **Documentation:** [faultgate docs](https://www.faultline-labs.com/docs/) · **PyPI:** [`faultgate`](https://pypi.org/project/faultgate/). Use faultgate to test recorded agent runs against business rules and measured baseline variation before a CI release.

**Why measure a baseline first?** [Regression or noise? A release gate that measures first](https://www.faultline-labs.com/blog/faultgate-regression-or-noise/) explains run-to-run variation and the current PASS, FAIL, and INCONCLUSIVE verdicts.

```
$ faultgate check examples/traces.json
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
fc2cdab304bd  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
6d1f9d67a2d4  ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
8bf3879339eb  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
3a9e507a0f6d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
2ab3b6c1e891  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00

2/5 traces failed · search_loop=1, abstention=1, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s
$ echo $?
1
```

Real output, unedited, on five real agent runs (`openai/gpt-5.6-luna` on a multi-hop retrieval task, recorded by [FAULTLINE](https://github.com/samirsawarkar/faultline-ai-reliability)). Trace 1 looped for 12 steps and never answered; trace 2 said it couldn't find the answer; 3–5 answered.

## Install

```bash
pip install faultgate
```

Requires Python 3.11 or newer. One dependency (pydantic). The built-in checks are code — nothing to download. Judges are extras:

```bash
pip install 'faultgate[laya]'   # local judge: downloads Laya once (~800 MB, Apache-2.0, pinned revision), offline after
pip install 'faultgate[api]'    # any API model through litellm
pip install 'faultgate[pii]'    # Microsoft Presidio for --redact presidio (names, locations; MIT)
```

Read [How much to trust a verdict](#how-much-to-trust-a-verdict) before you enable a judge.

## Usage

```bash
faultgate check traces.json                          # built-in rule checks
faultgate check traces.json --json report.json       # full per-trace verdicts
faultgate check traces.json --golden golden.json     # expected answers: correctness + truncation
faultgate check traces.json --policy policy.json     # what the agent was allowed to do
faultgate check traces.json --outcomes outcomes.json # your own evaluator's pass / fail per scenario
faultgate check traces.json --judge laya             # also run judge checks, locally
faultgate check traces.json --judge litellm:openai/gpt-5.6-luna   # any API model
faultgate check traces.json --markdown pr.md --audit audit/   # PR comment + audit files
faultgate precheck traces.json                       # validate an export before gating
faultgate precheck traces.json --policy policy.json  # ...and check the traces carry what the policy reads
faultgate checks                                     # list checks and their kind
faultgate judges                                     # list judge specs

faultgate baseline run1.json run2.json run3.json --out band.json   # measure your noise (3+ runs)
faultgate check candidate.json --band band.json          # regression, or just noise?
```

Exit codes: `0` clean · `1` at least one check fired (or, with `--band`, gate FAIL) · `2` bad input, or an output file (`--json`, `--markdown`, `--audit`, `--out`) that cannot be written. Missing parent directories of output files are created.

### Input format

An [OTLP/JSON](https://opentelemetry.io/docs/specs/otlp/#json-protobuf-encoding) export using the [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/). One trace is one agent run:

| Span | Attributes read |
|---|---|
| root `invoke_agent` | `gen_ai.operation.name` = `invoke_agent`, `gen_ai.agent.name`, `gen_ai.input.messages` (the user prompt), `gen_ai.output.messages` (the final answer), optional `faultgate.termination` (why the run stopped, e.g. `step cap`) |
| child `execute_tool` | `gen_ai.operation.name` = `execute_tool`, `gen_ai.tool.name`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result` |

Set `gen_ai.operation.name`. A span without it is still read as a tool call when its name is `execute_tool` or `execute_tool <tool>` (the semconv span name), and `precheck` warns that it was recognised by name only.

Legacy `gen_ai.prompt` / `gen_ai.completion` are accepted as fallback. If your exporter records structure but not content, `faultgate` warns you. [`examples/traces.json`](https://github.com/Faultline-lab/faultgate/blob/main/examples/traces.json) is a complete reference file.

### Other trace formats

`faultgate` also reads the exports of the common agent-observability tools and maps them onto the same attributes, so every check, policy and judge works unchanged. The format is detected; force it with `--format`.

| `--format` | Export | Steps come from |
|---|---|---|
| `otlp` | OTLP/JSON, GenAI semantic conventions | `execute_tool` spans and tool calls inside chat messages |
| `openinference` | OTLP with `openinference.span.kind` (Arize Phoenix) | `TOOL` spans: `tool.name`, `tool.parameters` or `input.value`, `output.value` |
| `langfuse` | trace objects with `observations` (e.g. `GET /api/public/traces/{id}`) | `TOOL` observations; `level: ERROR` + `statusMessage` become span errors |
| `langsmith` | a list of runs | `run_type: tool` runs; `error` becomes a tool error |
| `braintrust` | a list of logged spans | `span_attributes.type: tool` spans |

Token usage, finish reasons (`context_overflow`), errors (`unrecovered_tool_error`), the user id (`enduser.id`, for `identity` policies) and `metadata.scenario` (scenario key for bands) are carried over where the format records them. [`examples/formats/`](examples/formats/) holds the same refund run in each format; `tests/test_formats.py` checks that all four normalise to identical steps.

### Precheck

Validate an export before you gate on it:

```
$ faultgate precheck examples/formats/langfuse.json
precheck: OK · format langfuse · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)
```

It reports the detected format and how many tool steps the checks will read, then per trace: duplicate span ids, missing or backwards timestamps, tool calls without a name (errors, exit 2), and missing roots, spans whose parent is not in the export, runs with no prompt, answer or content, tool spans recognised only by their span name, spans that carry tool attributes but are not read as steps, and exports that mix native `execute_tool` spans with OpenInference LLM spans (warnings, exit 0). Compare the tool-step count with what your agent actually ran: a structurally valid export whose tools are not read passes every check by default. It inspects the first 5 traces by default (`--sample N`, `0` for all). On the 30 real benchmark traces from `make demo-real` it passes with warnings: those exports omit the root span.

With `--policy policy.json` it also prints the keys the policy uses and warns when a `requires` rule reads tool results as JSON (`result`, `latest`) but no tool result in the checked traces is JSON, so those prerequisites could never be met:

```
$ faultgate precheck traces.json --policy examples/policy_retail.json
policy keys: allow, max_calls_per_arg, required_args, requires (after, invalidated_by, latest, result, same_arg, success, tool), values
```

A malformed policy exits 2, as it does for `check`.

## Measured on real agent traces

faultgate reads chat-only OpenTelemetry GenAI traces where tool calls live inside messages (as exported by many agent harnesses), in addition to `execute_tool` spans.

Run `make demo-real` (first run downloads ~220 MB, ~1 min) to fetch and evaluate 30 real traces (5 per benchmark from `Exgentic/agent-llm-traces-v2`: AppWorld, BrowseComp-Plus, SWE-bench, tau2 airline, tau2 retail, and tau2 telecom):

```
$ faultgate check .demo/real_traces.json
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
8a224e8eacdd  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
3cf53cafee61  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
0ff67ea879fc  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00
0f2709401932  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
a182fd9c1858  ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00
9bf471687b5f  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
16b13ee29724  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
9dc71e9167b0  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00
3524b4b6ef7e  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00
9ca4051344ef  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00
56e646e603b2  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
f406d07bd94c  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
012e74b002d9  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
f0cd792c3105  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
7c69e4d47302  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
fadbf538c24a  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
8e611f21829d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00
70722761fb7a  FAIL 1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00
4ab9ef2c7e60  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
910a177350e2  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
a585b61b1598  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
3d7d24721847  ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00
4422dd26b177  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
bff8bb4c1b2e  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
e42782af7315  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
53fdb0601422  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
1dff5fc97b54  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
88733a4ec841  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
dc97bf8af1d8  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00
192bf8092eb8  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00

9/30 traces failed · search_loop=2, abstention=0, policy=0, repeated_call=2, unrecovered_tool_error=6, context_overflow=0 · judge none · 2.1s
```

Two new checks with measured trust, ported from [FAULTLINE P18](https://github.com/samirsawarkar/faultline-ai-reliability) (`projects/p18_trace_triage`):

| Check | Kind | Measured trust | Source |
|---|---|---|---|
| `repeated_call` | rule | κ 0.95 vs a blind second rater (Claude Opus 5.5) on 97 real runs | FAULTLINE P18 |
| `unrecovered_tool_error` | rule | Caught 13 of 23 unrecovered errors confirmed by the blind second rater (Claude Opus 5.5) (recall 0.57, κ 0.54); misses plain-text errors and run-ending API failures (faultgate has no check for those yet; read flagged traces manually) | FAULTLINE P18 |

Span error = error.type or OTLP status code 2; P18 measured error.type only.

These are public benchmark traces, not production traffic; the P18 sample was stratified half passed / half failed, so rates are not production failure rates; dataset licence is unstated, so faultgate does not ship or redistribute the traces - the demo downloads them from Hugging Face.

## Checks

| Check | Kind | Fires when |
|---|---|---|
| `search_loop` | rule | The run ended with no answer at its step budget and most tool calls returned nothing. |
| `abstention` | rule | The final answer explicitly says the information could not be found: an inability to *find* (`couldn't find / locate / retrieve / determine`), `no matching documents`, `information not available`, `don't know`. A bare `cannot` / `unable to` does not count: a support agent that "cannot modify the order again" or is "unable to verify" an unauthenticated caller has not abstained. |
| `policy` | rule | A tool call broke the policy: unlisted tool, denied argument pattern, oversized argument, call budget, argument limit, identity mismatch, or missing prerequisite. |
| `repeated_call` | rule | The same tool was called with identical arguments and returned identical results >= 3 times. |
| `unrecovered_tool_error` | rule | A tool call produced a structural error with no later successful call of the same tool, or a span errored (error.type or status code 2) and no later span made a successful tool call. |
| `context_overflow` | rule | The run hit the model's context window or output token limit: a span's `gen_ai.response.finish_reasons` says `length` / `max_tokens`, or a provider error naming the context limit (`context_length_exceeded`, "maximum context length", "prompt is too long") in a span status, `error.type`, tool result or `faultgate.termination`. |
| `wrong_answer` | golden | Answered, and the expected answer is not in the final answer. |
| `truncation` | golden | The answer has the head of the expected token but not the whole token (`Onyx` for `Onyx-4413`). |
| `wrong_direction` | judge | On a multi-hop task, the agent walked the dependency chain backwards. |

A **rule** is plain code over the trace structure: instant, deterministic, no model. A **golden** check is a rule that also needs the expected answer (`--golden golden.json`, keyed by scenario or by prompt text). A **judge** check is a yes/no question a model answers from the rendered trace; it only runs when you pass `--judge`. All three kinds are calibrated the same way, below.

### Policy: what was the agent allowed to do?

```json
{"allow": ["search", "lookup", "calc"], "max_calls": 10, "max_arg_chars": 200}
```

`faultgate check traces.json --policy policy.json` then flags every step that called a tool outside `allow`, passed an argument matching a denied pattern (path traversal, `file://`, `/etc/passwd`, `~/.ssh` out of the box), exceeded `max_arg_chars`, or pushed the run past `max_calls` — with the step number in the reason. It is FAULTLINE P16's runtime policy applied after the fact: the four structural injection categories from P9 (`tool_exfil_path`, `unlisted_tool`, `query_dump`, `budget_loop`) are each caught by a test in `tests/test_policy.py`. Without a policy file only the denied-pattern rule is active, and it fires on 0 of the 290 real traces shipped here.

Three more keys check business rules on what the agent actually did, not just which tools it touched:

```json
{
 "limits":   [{"tool": "issue_refund", "arg": "amount", "min": 0, "max": 500}],
 "identity": {"arg": "customer_id", "session_attr": "enduser.id", "tools": ["issue_refund", "modify_billing_record"]},
 "requires": [{"tool": "modify_billing_record", "after": "verify_customer_identity", "result_contains": "VERIFIED"}]
}
```

- `limits`: a numeric floor or ceiling on one argument of one tool. `arg` is a dotted path into the JSON arguments (`refund.amount`). Strings like `"$1,200.50"` are read as numbers. An argument that is present but not a number, or arguments that are not a JSON object, count as a violation; an absent argument (or no arguments at all) does not. Arguments encoded as JSON twice are decoded. `min`/`max` must be finite numbers.
- `identity`: the argument must equal the authenticated principal, read from the root span attribute `session_attr` (default `enduser.id`). Only calls that carry the argument are checked, optionally only for `tools`. If the root span has no such attribute, the call cannot be verified and counts as a violation. So do unreadable (non-JSON-object) arguments on a listed tool, or on any tool when no `tools` list is given and the argument's name appears in the text.
- `requires`: `tool` may only run after an earlier call to `after`, and, if `result_contains` is set, one whose result contains that text.

Order-level rules bind a call to the record it acts on:

```json
{
 "requires": [{"tool": "get_user_details", "after": ["find_user_id_by_email", "find_user_id_by_name_zip"]},
              {"tool": "cancel_pending_order", "after": "get_order_details", "result_contains": "pending", "same_arg": "order_id"}],
 "max_calls_per_arg": [{"tools": ["exchange_delivered_order_items", "modify_pending_order_items"], "arg": "order_id", "max": 1}],
 "values": [{"tool": "cancel_pending_order", "arg": "reason", "allowed": ["no longer needed", "ordered by mistake"]}]
}
```

- `requires[].after` may be a list: any one of them satisfies the prerequisite (two ways to authenticate).
- `requires[].same_arg`: the earlier call must carry the same value of that argument. Reading the status of order A no longer licenses cancelling order B. A call without a readable `same_arg` is a violation.
- `max_calls_per_arg`: at most `max` successful calls to `tools` per value of `arg`, e.g. one item change per order. A call whose result is an error is not counted: an agent that fixes a bad item id and retries changed the order once. A call without a readable `arg` is a violation.
- `values`: the argument, when present, must be one of `allowed` (compared as text, trimmed).

#### Stateful rules (0.4)

Order and substring are not enough to prove a prerequisite: a failed lookup, an error message that mentions "pending", or a lookup made before the order was cancelled all satisfied a 0.3.1 `requires`. Each key below is opt-in; a policy without them evaluates exactly as in 0.3.1.

**`success`**: the earlier call counts only if it succeeded (no structural error in its result, no error on its tool span).

```json
{"requires": [{"tool": "cancel_pending_order", "after": ["find_user_id_by_email", "find_user_id_by_name_zip"], "success": true}]}
```

**`result`**: typed predicates on the earlier call's result, parsed as JSON. Each has a dotted `path` (a number indexes a list: `items.0.status`) and one of `equals`, `in`, `not_in`, `exists`. Comparison keeps JSON types apart (`true` is not `1`). A result that is not JSON, or has no such path, does not meet the condition. `result_contains` keeps its substring meaning.

```json
{"requires": [{"tool": "cancel_pending_order", "after": "get_order_details", "same_arg": "order_id",
               "result": [{"path": "status", "equals": "pending"}]}]}
```

**`latest`** and **`invalidated_by`**: current state. With `latest`, only the most recent matching `after` call (per `same_arg` value) counts: a later lookup that says `cancelled` overrides an earlier `pending`. `invalidated_by` lists tools whose successful call, on the same `same_arg` value, voids every earlier lookup: after a cancel, a modify needs a fresh lookup.

```json
{"requires": [{"tool": "modify_pending_order_items", "after": "get_order_details", "same_arg": "order_id", "latest": true,
               "result": [{"path": "status", "equals": "pending"}],
               "invalidated_by": ["cancel_pending_order", "modify_pending_order_items"]}]}
```

The reason says which call fell short: `step 6: modify_pending_order_items before get_order_details with status == 'pending' for the same order_id '#W1' (get_order_details at step 2 voided by cancel_pending_order at step 4)`.

**`required_args`**: arguments that must be present and not empty (`""`, `null`, `[]`, `{}`). `values` only checks an argument that is there.

```json
{"required_args": [{"tool": "cancel_pending_order", "args": ["order_id", "reason"]}]}
```

**`confirmation`**: each listed mutation needs an earlier successful call to the `by` tool for the same `same_arg` value (optional), or the attribute `faultgate.confirmed = true` on the mutation's own span. Record confirmation as a tool call or a span attribute in your agent. faultgate does not read the conversation to find a "yes": free-text confirmation is out of scope.

```json
{"confirmation": {"tools": ["cancel_pending_order", "modify_pending_order_items"], "by": "confirm_action", "same_arg": "order_id"}}
```

**`require_complete`**: an incomplete run is a violation: no final answer, an error termination (`faultgate.termination` naming an error, exception, abort, failure, timeout, crash, `too_many_errors` or a step cap), an error on the root span, or a root span with no end time. A run that stopped half-way cannot prove it followed the rules.

```json
{"require_complete": true}
```

[`examples/policy_retail.json`](examples/policy_retail.json) applies these to the tau2-bench retail domain: successful authentication before any account or order change, the latest successful lookup of the same order with the right status, invalidated by status-changing mutations, required arguments, one item change per order and the two allowed cancellation reasons. It has no `confirmation` (tau2 records confirmation only in the dialogue) and no `require_complete` (decide for your recorder). The 0.3.1 version is [`examples/policy_retail_v031.json`](examples/policy_retail_v031.json).

On 180 real tau2 retail runs from an outside test (three `gpt-6-luna` baselines, a same-model candidate, a weaker model and a sabotaged prompt), the 0.4 policy fires on 0 of the 120 baseline and same-model runs, 10 of 30 weaker-model runs and 23 of 30 sabotaged runs; the 0.3.1 policy fires on 0, 5 and 1. The added weaker-model fires include order changes with no identity lookup at all, which the client's hand audit had marked as missed violations.

Still not expressible: free-text confirmation, one tool call per turn, joins against earlier results (the payment method belongs to the customer, the item is available, the price difference is right), and anything semantic. A clean `policy` result is not a compliance certificate.

Reasons name the step and the values: `step 4: modify_billing_record.customer_id 'C-999' != session enduser.id 'C-123'`. [`examples/policy_support.json`](examples/policy_support.json) is a complete customer-support policy. A malformed policy file exits 2.

**A policy violation is a hard block.** With `--band`, a run whose clean rate sits inside the measured band still FAILs if the `policy` check fired on any trace; the gate prints `policy violation in N trace(s) (hard block)` and lists them under `policy_violations` in the JSON report. Noise explains a flaky answer, not a refund over the limit.

Semantic injections — the agent *obeying* text it read in a document — are a judge question, not a rule, and are not in this release.

## Data stays local: redaction

`faultgate` reads your traces in memory and writes no trace payloads anywhere. Rules, policy, bands and the local Laya judge never send anything off the machine. Two things can travel: the trace an **API judge** (`litellm:`) reads, and the **reasons** that end up in your terminal, `--json` report, CI logs and PR comments. By default both are masked:

| `--redact` | Masks | Needs |
|---|---|---|
| `builtin` (default) | emails, credit cards (Luhn-checked), US SSNs, phone numbers, IPv4/IPv6, API keys, bearer tokens, JWTs | nothing (stdlib regex) |
| `presidio` | the above plus Presidio's recognisers: person names, locations, more | `pip install 'faultgate[pii]'` and a spaCy model |
| `off` | nothing | |

Rules always see the raw values (an `identity` policy has to compare the real customer id); only what leaves is masked: `step 2: update_profile.email '<EMAIL>' != session enduser.id '<EMAIL>'`. The report's `redaction` field records which mode ran. On the 30 real benchmark traces from `make demo-real` the built-in masker finds 81 emails, 39 phone numbers and 69 JWT access tokens, all real-looking customer data or credentials; it changes none of the text in the shipped FAULTLINE traces.

## Regression or noise? Tolerance bands

Agents are not deterministic. FAULTLINE P11 ran the same model on the same 30 inputs five times and got pass rates from 0.60 to 0.87. A fixed threshold turns that into a coin-flip gate. `faultgate` measures your spread instead:

```
$ faultgate baseline examples/gate/baseline_glm_run1.json examples/gate/baseline_glm_run2.json --out band.json
note: 2 baseline runs measure noise poorly; use 3 or more
examples/gate/baseline_glm_run1.json: 30 traces · clean rate 0.93 · 0.0s
examples/gate/baseline_glm_run2.json: 30 traces · clean rate 0.93 · 0.0s
band [0.93, 0.93] over 30 scenarios × 2 runs · 26 clean in every run · written to band.json

$ faultgate check examples/gate/candidate_gpt.json --band band.json
18/30 traces failed · search_loop=18, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s
gate: FAIL · clean rate 0.40 vs band [0.93, 0.93] from 2 baseline runs · fail below 0.83 · p=0.000
regressions (clean in every baseline, not now): r-0208, r-0214, r-0216, r-0224, r-0226, r-0232, r-0258, ...

$ faultgate check examples/gate/candidate_qwen.json --band band.json
gate: FAIL · clean rate 0.70 vs band [0.93, 0.93] from 2 baseline runs · fail below 0.83 · p=0.005

$ faultgate check examples/gate/baseline_glm_run2.json --band band.json
gate: PASS · clean rate 0.93 vs band [0.93, 0.93] from 2 baseline runs · fail below 0.83 · p=0.500
```

Real runs (table rows and most stderr notes omitted): two `z-ai/glm-5.3-flash` baselines and `openai/gpt-5.6-luna` / `qwen/qwen3.7-flash` candidates on the same 30 multi-hop scenarios. The verdicts match FAULTLINE P11's live drill (R4 FAIL / R1 FAIL / R2 PASS), which cost $1.84 and an API judge; this took 0.0 s and no model.

| Verdict | Rule (n = scenarios in the band) | Exit |
|---|---|---|
| **PASS** | clean rate ≥ min observed − 1/n | 0 |
| **FAIL** | clean rate < min observed − 3/n, or below PASS and the drop is significant (one-sided, α = 0.05) | 1 |
| **INCONCLUSIVE** | in between and not significant: the gate says how many scenarios it would need (power 0.80) | 0 |

In between the two thresholds, the gate tests whether the candidate's clean rate is below the baseline mean. The variance is the binomial noise of both sides plus the run-to-run variance the baseline measured, so a noisy baseline needs a bigger drop to fail. When it cannot tell, it says so and sizes the fix:

```
gate: INCONCLUSIVE · clean rate 0.93 vs band [1.00, 1.00] from 2 baseline runs · fail below 0.90 · p=0.072
inconclusive: a drop of 0.07 needs 89 scenarios to tell from noise (alpha 0.05, power 0.80) · run 59 more
```

(Two failures injected into a run of a baseline that was clean on all 30 scenarios; `tests/test_band.py`.) `required_n` is the standard two-proportion sample size for the observed drop. The gate result in the JSON report carries the same numbers under `stats`. Build the band from 3 or more baseline runs; with 2, the run-to-run variance is a guess and the gate warns.

It also lists **regressions**: scenarios clean in *every* baseline run and not clean now — the ones to read first. Scenarios are matched across runs by `faultgate.scenario`, else `gen_ai.agent.id`, else a hash of the prompt.

With expected answers the gate grades correctness too, and the numbers land on P11's exactly:

```
$ faultgate baseline examples/gate/baseline_glm_run*.json --golden examples/gate/golden.json --out band.json
examples/gate/baseline_glm_run1.json: 30 traces · clean rate 0.80 · 0.0s      # P11: 24/30 grounded
examples/gate/baseline_glm_run2.json: 30 traces · clean rate 0.87 · 0.0s      # P11: 26/30 grounded
band [0.80, 0.87] over 30 scenarios × 2 runs · 21 clean in every run

$ faultgate check examples/gate/candidate_gpt.json --golden examples/gate/golden.json --band band.json
21/30 traces failed · search_loop=18, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0, wrong_answer=3, truncation=3 · judge none · 0.0s
gate: FAIL · clean rate 0.30 vs band [0.80, 0.87] from 2 baseline runs · fail below 0.70 · p=0.000

$ faultgate check examples/gate/candidate_qwen.json --golden examples/gate/golden.json --band band.json
18/30 traces failed · search_loop=9, abstention=0, policy=0, repeated_call=1, unrecovered_tool_error=0, context_overflow=0, wrong_answer=9, truncation=8 · judge none · 0.0s
gate: FAIL · clean rate 0.40 vs band [0.80, 0.87] from 2 baseline runs · fail below 0.70 · p=0.000
```

(Qwen returns the head of the answer token without its suffix in 8 of 30 runs. Nobody had noticed.)

## Task outcomes

A clean trace is not a solved task. Retail baselines that faultgate rated structurally clean earned the benchmark reward in 25, 23 and 22 of 30 runs. If you have your own evaluator, hand its verdict in:

```json
{"retail-0": true, "retail-1": false, "retail-2": true}
```

```bash
faultgate check candidate.json --outcomes outcomes.json --band band.json
faultgate baseline run1.json run2.json run3.json --outcomes outcomes.json --out band.json
```

Keys are scenario keys (`faultgate.scenario`, `gen_ai.agent.id`, a prompt hash) or the prompt text, as for `--golden`. The `outcome` check fires when a scenario's outcome is `false`. It joins the clean rate like any other check, so a band built with outcomes gates on them. Scenarios missing from the file are not judged, and the output says how many. The terminal, the JSON report (`outcome`) and the Markdown summary keep the two rates apart:

```
outcome: 23/28 true (0.82) · 2 scenario(s) without an outcome, not judged · structural clean rate 0.93
```

Without `--outcomes` there is no `outcome` check and the report is exactly as before. Build the band and check the candidate with the same flags: a band built without outcomes warns when the check sets differ.

## In CI

```yaml
- uses: Faultline-lab/faultgate@main
  with:
    traces: traces/candidate.json      # exported by your agent's OTel pipeline
    band: traces/band.json             # from `faultgate baseline`, committed
    golden: traces/golden.json         # optional
    policy: traces/policy.json         # optional
```

Exit 1 on gate FAIL, so the job fails; PASS and INCONCLUSIVE pass (INCONCLUSIVE prints how many more scenarios to run). Every run also:

- writes the Markdown summary to the **job summary**, and on pull requests posts **one PR comment** (updated in place on later pushes, found by its `<!-- faultgate -->` marker): the verdict, gate numbers and p-value, fired checks, the policy hard block with each broken rule, failing traces with the step and reason, the latency / token / cost change against the baseline, and the exact command to reproduce it locally. Give the job `permissions: pull-requests: write`, or set `comment: "false"`;
- uploads an **audit artifact** (`faultgate-audit`): `verdict.json` (verdict, exit code, faultgate version, UTC time, every input file with its SHA-256, gate numbers), `failing_traces.json` (each failing trace and every reason) and `repro.sh`. No prompts, answers or tool payloads are copied into it, and reasons are masked by `redact`;
- exposes the verdict as the step output `verdict`.

Other inputs: `format`, `redact`, `checks`, `judge`, `report`, `audit`, `outcomes`, `version`. `version` takes a version (`0.3.0`), a specifier (`>=0.3`), a full requirement (`faultgate==0.3.0`) or any pip spec (a path, `git+https://...`); the default is the latest release. The same files come from the CLI with `--markdown summary.md --audit audit/`. The action installs nothing heavier than pydantic; our own CI runs it against this repo's examples and asserts that the GPT candidate fails and the GLM baseline passes, with matching verdict outputs and audit files.

## How much to trust a verdict

This is the part every evaluation tool skips. Every check and judge here is scored against **human failure-mode labels** on 200 real agent runs (FAULTLINE P4), reported on all 200 and on P5's frozen test split (n = 60). Regenerate with `scripts/calibrate.py`.

| Check | Kind | Positives | TPR | TNR | κ (n=200) | κ (P5 test, n=60) |
|---|---|---|---|---|---|---|
| `search_loop` | rule | 36 | 1.00 | 0.99 | **0.98** | **1.00** |
| `abstention` | rule | 1 | 1.00 | 1.00 | 1.00 | — (0 positives) |
| `policy` | rule | synthetic | 4/4 P9 categories; 6/6 retail gap fixtures | 0 FP on 290 real traces; 0 of 7 valid retail look-alikes; 0 of 120 retail baseline / same-model runs | — | — |
| `context_overflow` | rule | synthetic | finish-reason and provider-error forms in `tests/test_checks.py` | 0 FP on the 125 shipped real traces | — | — |
| `wrong_answer` | golden | 4 | 1.00 | 1.00 | 1.00 | 1.00 |
| `truncation` | golden | 1 | 1.00 | 1.00 | 1.00 | — (0 positives) |
| `wrong_direction` | Laya judge | 1 | 1.00 | 0.61 | 0.02 | 0.00 |

For comparison, the same `search_loop` question put to judges instead of a rule: Laya κ 0.09, GLM-5.3 (API) κ −0.03. **Where a failure is structural, code beats every model we measured**, which is why the default checks are rules.

Read the table honestly:
- `search_loop` is solid on this task family. The human coder saw the same structural signals, so κ measures agreement with that coding, not ground truth from nowhere.
- `abstention` and `truncation` have one positive each to learn from. `abstention` is a phrase list; a paraphrase it doesn't know is a miss. It was tuned on question-answering runs and then narrowed after an outside test on tau2 retail support runs, where "cannot" and "unable to" fired on 21 of 180 final answers that were policy reminders, authentication refusals and explanations of what a tool cannot do. It now fires on 1 of those 180 ("couldn't locate the ... payment method"); the P4 numbers above are unchanged.
- `wrong_answer` agrees with the human verdict on all 21 answered runs. It is substring containment, case-insensitive: right for short factual answers, wrong for free-text ones — say what "expected" means for your task before you trust it.
- `policy` has no human-labelled positives: FAULTLINE's agent rejects hostile calls before they become steps, so its traces never contain an executed attack. Recall is by construction on the P9 attack shapes; the number that matters is zero false positives on real runs.
- The 0.4 policy keys were built against six gaps an outside client found in 0.3.1 (a failed prerequisite, an error message matching a substring, stale state, an incidental substring, a missing argument, no confirmation). [`tests/fixtures/retail_gaps.json`](tests/fixtures/retail_gaps.json) holds one run per gap and 7 valid look-alikes: 6 of 6 gaps fire with the 0.4 keys and 0 of 6 with the 0.3.1 policy; 0 of 7 look-alikes fire. These are hand-written fixtures by the maintainer, not an independent test set: they show each key works, not how often real agents commit each gap.
- `wrong_direction` is the only check that needs reading, and the only local judge we have is noise on it (fires on 39% of clean runs). It ships because the contract is the product: the day a local model scores κ ≥ 0.7 on it, that's a one-line adapter, and this harness is what proves it.
- Laya's context is 512 tokens. `faultgate` compacts the trace to fit (answer and termination first, middle steps elided) and counts every call that still overflows; the count is printed.

Full confusion matrices and Wilson CIs for the original P5 judges: [FAULTLINE `projects/p05_judge/DECISIONS.md`](https://github.com/samirsawarkar/faultline-ai-reliability/blob/main/projects/p05_judge/DECISIONS.md).

## Swap the judge

```python
class Judge(Protocol):
    name: str
    budget: int | None          # max characters of trace it can read
    def ask(self, state: str, question: str) -> Verdict: ...   # Verdict(detected, confidence, reason)
```

`laya` and `litellm:<model>` ship in the box. Add a judge, run `scripts/calibrate.py --judge yours`, and publish the row.

## What it doesn't do yet

- **Premature stop** (answered with an intermediate entity of the chain). Needs the traversal chain, not just the final answer.
- **Semantic injection checks** (the agent obeyed text it read). P9 has the taxonomy; needs a judge that scores.
- **Running your agent.** `faultgate` reads traces; it never executes anything.
- **Free-text confirmation.** `confirmation` needs a confirm tool call or a span attribute; faultgate does not read the dialogue.
- **Relational policy checks.** Ownership (the order or payment method belongs to this customer), item availability and price arithmetic need joins against earlier results; `policy` has no keys for them yet.

## Built on FAULTLINE

[FAULTLINE](https://github.com/samirsawarkar/faultline-ai-reliability) is the research workbench behind this tool: 30 days of simulator, 16 measured projects, two papers. `faultgate` is the part you install. Every number in this README links back to the run that produced it.

MIT © 2026 Samir Sawarkar
