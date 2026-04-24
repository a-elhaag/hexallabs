---
name: hexallabs-caching-rules
description: Prompt caching rules for HexalLabs. Invoke when writing any prompt template for Apex synthesis, peer review, Council fan-out, or Prompt Forge. Claude uses explicit cache_control; Azure OpenAI uses automatic prefix cache.
---

# HexalLabs Caching Rules

## Two cache systems

### Anthropic Claude (Apex, Pulse)

Explicit `cache_control: {type: "ephemeral"}` on message blocks.

```python
messages = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": APEX_SYNTH_SYSTEM, "cache_control": {"type": "ephemeral"}},
        ],
    },
    {"role": "user", "content": council_responses_and_query},
]
```

- Cache invariant prefix (system rubric, council rules)
- User content (query + council responses) goes last, uncached
- TTL ~5 min idle, 1 hr hard max
- Discount: up to 90% input tokens

### Azure OpenAI (Swift, Prism, Depth, Horizon)

Automatic prefix cache. Rules:
- First 1024 tokens must be identical across requests → cache hit
- After 1024, hits extend every 128 tokens
- Pass `prompt_cache_key=<session_or_user_id>` → sticky routing, higher hit rate
- Rate limit: ~15 req/min per prefix+key combo before cache dilutes

### DeepSeek/Llama (Atlas)

Provider-dependent. Do not rely on caching. Keep prompts lean.

## Cacheable templates (put FIRST in messages)

1. **Apex synthesis system prompt** — council rules, scoring rubric, output format
2. **Peer-review template** — rubric, anonymization instructions, confidence rescoring rules
3. **Prompt Forge system prompt** — rewrite instructions
4. **Primal Protocol rewrite prompt** — caveman rules

## Non-cacheable (put LAST)

- User query
- Anonymized council responses
- Per-session context
- Confidence scores from other models

## Prompt structure pattern

```
[CACHED SYSTEM: rubric + rules + format]   ← cache_control here
[CACHED FEW-SHOT: 1-2 example syntheses]   ← cache_control here
[USER: query + council responses]          ← no cache
```

Order matters. One byte drift in cached section = full miss.

## Monitoring

Log `cached_tokens` from response `usage.prompt_tokens_details.cached_tokens` (Azure OpenAI) and `usage.cache_read_input_tokens` (Anthropic). Alert if hit rate < 40% on Apex synth.
