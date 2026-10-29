# Faultgate integration recipes

Each recipe records a real agent run as a local JSON trace, then checks that trace with `faultgate`.
Install the recipe's pinned requirements in its own environment before running its agent.

| Framework | Recipe | Trace format | Model tested |
| --- | --- | --- | --- |
| LiteLLM | [litellm/README.md](litellm/README.md) | OpenInference | `openai/gpt-6-luna`, DeepSeek |
| LangGraph | [langgraph/README.md](langgraph/README.md) | OpenInference | `openai/gpt-6-luna`, DeepSeek |
| OpenAI Agents SDK | [openai-agents/README.md](openai-agents/README.md) | OpenInference | `openai/gpt-6-luna`, DeepSeek |
| smolagents | [smolagents/README.md](smolagents/README.md) | OpenInference | `openai/gpt-6-luna`, DeepSeek |
| Arize Phoenix | [phoenix/README.md](phoenix/README.md) | OpenInference | `openai/gpt-6-luna` |

Every recipe includes `agent.py`, exact dependency pins, a policy, expected results, and clean,
faulty, and policy-violation traces. Read the recipe README for setup, tracing, commands, output,
known gotchas, and tested versions.

Run the saved-trace integration checks from the repository root:

```powershell
python -m pytest tests/test_integrations.py
```

The test reads saved traces only. It does not call a model or need a framework environment.
See [FINDINGS.md](FINDINGS.md) for the audit results and follow-up ideas.

The general GitHub Action implementation is at the repository root in `action.yml`. The
[LiteLLM Action example](litellm/faultgate-action.yml) shows how a project can run it on a pull
request. The [LiteLLM baseline example](litellm/README.md#10-build-and-check-a-baseline) records
three clean runs and checks a fourth run against the generated band.
