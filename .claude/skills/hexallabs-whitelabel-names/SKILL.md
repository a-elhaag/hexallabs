---
name: hexallabs-whitelabel-names
description: Never leak real model names in HexalLabs UI, API responses, logs visible to users, or error messages. Invoke when writing any user-facing string, API schema, or frontend component. Real names allowed ONLY on /about page.
---

# HexalLabs White-Label Names

## The 7 names

| White-label | Real model (NEVER expose except /about) | Role |
|---|---|---|
| **Apex** | Claude Opus 4.7 | Chairman / synth |
| **Swift** | GPT-4o-mini or gpt-4.1-mini | Fast organizer |
| **Prism** | o3-mini or gpt-5-mini | Reasoning |
| **Depth** | GPT-5 or o1 | Deep analysis |
| **Atlas** | DeepSeek-V3.1 or Llama-4 | Open-source |
| **Horizon** | GPT-4.1 | Long context |
| **Pulse** | Claude Sonnet 4.6 | Latest reasoning |

## Rules

1. **UI components**: show white-label only. Hex cells, confidence badges, peer-review lines, Apex synth banner → all use white-label.
2. **API responses**: `{ "model": "Apex" }` never `{ "model": "claude-opus-4-7" }`.
3. **SSE events**: `{ "hex": "Swift", "token": "..." }`.
4. **Error messages to user**: "Apex is unavailable" not "claude-opus-4-7 429".
5. **Server logs**: real names OK (internal debug). User-visible logs (e.g. exported session JSON): white-label only.
6. **Env vars**: `MODEL_APEX=claude-opus-4-7` — env maps white-label → real. Code only sees white-label.
7. **`/about` page**: only place real names + provider (Anthropic/Azure) appear.

## Pattern

```python
# Good
return {"model": whitelabel, "response": text}

# Bad
return {"model": self.deployment_name, "response": text}  # leaks "gpt-4.1"
```

## Why

Product positioning. White-label = Hexal brand. Real names = commodity. User buys Hexal council, not "7 APIs we stitched".
