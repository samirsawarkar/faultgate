# Changelog

## 0.4.1 — 2026-10-26

- Update package metadata and bundled README with the FAULTLINE product page and current source repository. Runtime behavior is unchanged.

## 0.4.0 — 2026-10-14

Closes the six policy gaps an outside client found in 0.3.1 (17 retail probes: 6 caught, 6 missed) and adds an outcome input.

- `requires[].success`: the earlier call counts only if it succeeded (no structural error, no tool span error). Gap: a failed identity lookup followed by a mutation.
- `requires[].result`: typed predicates (`equals`, `in`, `not_in`, `exists`) on a dotted path into the earlier call's parsed JSON result; a non-JSON result or a missing path fails closed. Gaps: an error message containing "pending"; a delivered order whose note says "previously pending". `result_contains` is unchanged.
- `requires[].latest` and `requires[].invalidated_by`: only the most recent matching lookup counts (per `same_arg` value), and a successful call to a listed tool on the same record voids earlier lookups. Gap: lookup "pending", cancel, then modify on the stale lookup.
- `required_args`: listed arguments must be present and not empty. Gap: a cancellation without a reason.
- `confirmation`: listed mutations need an earlier successful confirm-tool call for the same record, or `faultgate.confirmed = true` on the mutation span. Gap: a mutation without confirmation.
- `require_complete`: no final answer, an error termination, a root span error or a root span with no end time is a policy violation.
- `--outcomes outcomes.json` on `check` and `baseline`, and an `outcomes` Action input: `{scenario key: true | false}` from your own evaluator. The `outcome` check fires on `false`, joins the clean rate (bands and gates unchanged), skips scenarios without an outcome and reports how many. Terminal, JSON (`outcome`) and Markdown show outcome rate and structural clean rate separately.
- `precheck --policy`: lists the policy's keys and warns when `result` / `latest` rules meet traces with no JSON tool results.
- `examples/policy_retail.json` uses the new keys; the 0.3.1 file is `examples/policy_retail_v031.json`. On 180 real tau2 retail runs: 0 fires on 120 baseline and same-model runs (unchanged), 10/30 weaker-model runs (was 5), 23/30 sabotaged runs (was 1).
- `tests/fixtures/retail_gaps.json`: one run per gap and 7 valid look-alikes; all 6 gaps fire with the new keys and none with the 0.3.1 policy; no look-alike fires.

**Back-compat.** Every new key and flag is opt-in. A policy, band or command line from 0.3.1 gives the same result: on the shipped examples, the `make demo-real` sample and the format examples, with no policy and with each shipped 0.3.1 policy, the JSON reports of 0.3.1 and 0.4.0 are byte-identical (40 runs), and the examples/gate verdicts are unchanged. Without `--outcomes`, reports have no `outcome` check.

**Not covered.** Free-text confirmation (faultgate does not read the dialogue); relational checks such as payment-method or order ownership, item availability and price arithmetic; one tool call per turn. Run-ending root errors are caught by `require_complete`, not by `unrecovered_tool_error`.

## 0.3.1 — 2026-10-13

Fixes from the first outside test (tau2-bench retail, 180 real runs, 2026-10-13).

- Redaction: a card number written next to another number (`4111 1111 1111 1111 123-45-6789`) joined its digit run, failed the Luhn check as a whole and was written unmasked to the JSON report, the Markdown summary and `failing_traces.json`. Cards are now found as Luhn-valid windows of whole digit groups, SSNs are masked first, and a card at the end of a sentence (`...1111.`) is masked too (it was also missed).
- Tool spans named `execute_tool` / `execute_tool <tool>` without `gen_ai.operation.name` are read as tool calls. Before, every structural check saw zero steps on such exports while `precheck` passed them clean.
- `precheck` reports the tool steps it read and warns on tool spans recognised by name only, spans with tool attributes that are not read as steps, and mixed native / OpenInference exports.
- Auto-detect: an OTLP export with native `execute_tool` spans and OpenInference LLM spans was read as OpenInference and counted every tool call twice (once from the span, once from the LLM message). The tool spans are now the steps, as with `--format otlp`; the native root keeps its own agent name.
- An output file that cannot be written exits 2 instead of crashing with exit 1 (which CI reads as a gate FAIL); parent directories of `--json`, `--markdown` and `baseline --out` are created.
- GitHub Action: `version: 0.3.0` was passed to pip as a package name. A bare version, `v`-prefixed version or specifier now installs that faultgate version; any other value goes to pip unchanged.
- `abstention` no longer fires on a bare `cannot` / `unable to`: the inability has to be about finding the information. On the 180 retail runs it fired on 21 final answers that were policy reminders, authentication refusals or explanations of what a tool cannot do; now 1. FAULTLINE P4 calibration unchanged (1/1, 0 FP on 200).
- Policy, order-level rules: `requires[].after` takes a list of alternatives, `requires[].same_arg` binds the prerequisite to the same argument value (the order looked up is the order changed), `max_calls_per_arg` caps successful calls per argument value (one exchange per order), `values` allowlists an argument. `examples/policy_retail.json` uses them: 0 fires on 120 baseline and same-model retail runs, 5/30 on a weaker model.

## 0.3.0 — 2026-10-12

- Policy business rules in `policy.json`: `limits` (numeric min/max on a tool argument, dotted paths, `"$1,200.50"` parsed), `identity` (argument must equal the root span's `enduser.id` or another `session_attr`), `requires` (tool order prerequisites, optionally on the earlier result). Each fails closed when it cannot be checked. Malformed keys exit 2.
- Hard block: with `--band`, any `policy` violation makes the gate FAIL regardless of clean rate; the gate result lists `policy_violations`.
- `examples/policy_support.json`: a customer-support policy using every key.
- New default rule `context_overflow`: the run hit the context window or output token limit (`gen_ai.response.finish_reasons` `length` / `max_tokens`, or a provider context-limit error in a span status message, `error.type`, tool result or `faultgate.termination`). 0 detections on the 125 shipped real traces and the 30-trace `make demo-real` sample. Spans now keep `status.message` and `endTimeUnixNano`. The default report gains a column.
- Trace formats: `--format auto|otlp|openinference|langfuse|langsmith|braintrust` on `check` and `baseline` (detected by default). Each vendor export is mapped onto the GenAI span model, carrying tool calls, errors, finish reasons, token usage, user id and scenario. Examples in `examples/formats/`.
- `faultgate precheck`: validates an export (format, roots, duplicate span ids, dangling parents, timestamps, unnamed tool calls, missing content) on the first 5 traces (`--sample`); exit 2 on errors.
- `Trace.usage`: token totals across spans.
- Redaction (`--redact builtin|presidio|off`, default `builtin`): PII and secrets are masked in the trace sent to an API judge and in every verdict reason (terminal, JSON report, CI). Rules still read raw values. `builtin` is stdlib regex (emails, Luhn-checked cards, SSNs, phones, IPs, API keys, bearer tokens, JWTs); `presidio` uses the new `[pii]` extra. Reports gain `redaction`.
- PR comment and audit files: `--markdown PATH` writes the verdict, gate numbers, fired checks, policy hard block, failing traces (step and reason), latency / token / cost change against the baseline, and a repro command; `--audit DIR` writes `verdict.json` (inputs with SHA-256), `failing_traces.json` and `repro.sh`. Neither copies trace payloads. Bands record mean `tokens`, `latency_ms`, `cost_usd` per run under `usage`, and the gate reports the change. `examples/gate/band.json` regenerated (same clean rates and verdicts, now with `usage`).
- GitHub Action: job summary, one upserted PR comment (`comment`, needs `pull-requests: write`), `faultgate-audit` artifact, `verdict` output, `format` / `redact` inputs; fails closed if the gate never ran.
- Gate statistics: **WARN is replaced by INCONCLUSIVE.** Between the PASS and FAIL thresholds the gate now runs a one-sided test against the baseline mean (binomial noise of both sides plus measured run-to-run variance); a significant drop (α 0.05) is FAIL, otherwise INCONCLUSIVE with `required_n` / `additional_n` for power 0.80. The gate result gains `stats` (`p_value`, `drop`, `baseline_mean`, `required_n`, `additional_n`). Bands from fewer than 3 baseline runs warn. Existing band.json files keep working. If you parse `verdict == "WARN"`, switch to `"INCONCLUSIVE"`.

## 0.2.0 — 2026-09-29

- Chat-only trace support: tool calls embedded inside message parts (paired with tool responses by ID), in addition to `execute_tool` spans.
- New rule checks: `repeated_call` (same tool + normalized arguments issued >= 3 times with identical result, κ 0.95 vs a blind second rater (Claude Opus 5.5) on 97 real runs) and `unrecovered_tool_error` (structural tool error with no later success, or a span error (error.type or status code 2) with no later successful tool call; recall 0.57, κ 0.54), calibrated against FAULTLINE P18 on Exgentic real benchmark traces.
- `scripts/fetch_real_traces.py` and `make demo-real`: sample real traces across 6 benchmarks from `Exgentic/agent-llm-traces-v2` and evaluate with default rule checks.
- `demo-real` works from an empty cache via `snapshot_download`, carries span status codes into OTLP, and adds `demo` optional dependency group.
- Hybrid traces preserve message-embedded tool calls deduplicated against `execute_tool` span IDs.
- Tool and span error signals preserved (Span `status_code` parsed from OTLP status, `is_error`/error status flagged on message tool call responses).
- Hybrid trace steps ordered chronologically by span start time, preserving originating `span_id`.
- Span error recovery ported from FAULTLINE P18: middle span errors unrecovered unless a later span runs a non-error tool call.
- Pinned Exgentic dataset revision in `scripts/fetch_real_traces.py` and handled expected trace-failure exit code in `make demo-real`.

## 0.1.0 — 2026-09-22

- `faultgate check <traces.json>`: run checks over an OTLP/JSON GenAI-semconv trace export; exit 1 if any fires.
- Rule checks (no model): `search_loop` (κ 0.98 on 200 human-labelled runs, 1.00 on the P5 split), `abstention` (1/1, 0 FP).
- `policy` rule + `--policy policy.json` (allowlist, denied argument patterns, max argument size, call budget) — FAULTLINE P16 after the fact; P9's four structural attack shapes covered by tests; 0 FP on 290 real traces.
- Golden checks + `--golden golden.json` (keyed by scenario or prompt): `wrong_answer` (4/4 vs human verdict, 0 FP), `truncation` (1/1, 0 FP).
- Composite GitHub Action (`uses: Faultline-lab/faultgate@<ref>`), self-tested in CI against the shipped examples.
- `laya` is an extra (`faultgate[laya]`); the base install is pydantic only.
- Judge checks (opt-in `--judge`): `wrong_direction`. Judges: `laya` (local, pinned `1c5edc17`, budgeted render), `litellm:<model>` (`[api]` extra).
- `faultgate baseline` + `check --band`: tolerance band from ≥ 2 baseline runs (FAULTLINE P11 rule), PASS/WARN/FAIL, named regressions.
- `scripts/calibrate.py`: score any check/judge against FAULTLINE P4 human labels.
- Examples: five real runs (`examples/traces.json`); two `glm-5.3-flash` baselines and `gpt-5.6-luna` / `qwen3.7-flash` candidates on P11's 30 golden scenarios (`examples/gate/`).
