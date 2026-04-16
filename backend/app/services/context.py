"""
Context extractor — token-aware conversation compression.

Counts the actual tokens in the message history. When the total exceeds
CONTEXT_TOKEN_LIMIT, older messages are summarised and replaced with a
dense context note. The most recent RECENT_TOKEN_BUDGET tokens are always
kept verbatim (recency is most important for coherence).

Token counting uses tiktoken cl100k_base — a good approximation for all
models on Azure AI Foundry regardless of the underlying architecture.
"""
from __future__ import annotations

import tiktoken

from app.services import foundry

# Compress when the non-system history exceeds this many tokens
CONTEXT_TOKEN_LIMIT = 8_000

# Always preserve this many tokens of recent history verbatim
RECENT_TOKEN_BUDGET = 2_000

# Model used to generate the summary (fast + cheap)
COMPRESSOR_MODEL = "gpt-5.4-mini"

# Overhead added by the chat format per message (role tag + separators)
_MSG_OVERHEAD = 4

_COMPRESSOR_SYSTEM = (
    "You are a conversation memory compressor. "
    "Given a conversation history, output a dense context summary preserving:\n"
    "- The user's goals, constraints, and open questions\n"
    "- Key decisions, conclusions, and agreed-upon facts\n"
    "- Any code, commands, file names, numbers, or technical specifics mentioned\n"
    "- The direction and tone of the conversation\n\n"
    "Be dense and specific. Strip pleasantries. Fragments OK. "
    "Target 150–250 words. Output plain prose only."
)

_enc = tiktoken.get_encoding("cl100k_base")


def _token_count(text: str) -> int:
    return len(_enc.encode(text))


def _msg_tokens(msg: dict) -> int:
    """Approximate token cost of a single message dict."""
    return _token_count(msg.get("content") or "") + _MSG_OVERHEAD


def _history_tokens(messages: list[dict]) -> int:
    return sum(_msg_tokens(m) for m in messages)


def _split_by_token_budget(
    non_system: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Walk backward through non_system messages, accumulating tokens until
    RECENT_TOKEN_BUDGET is reached. Everything before that split is 'to compress'.
    Returns (to_compress, recent).
    """
    recent: list[dict] = []
    budget = RECENT_TOKEN_BUDGET

    for msg in reversed(non_system):
        cost = _msg_tokens(msg)
        if budget <= 0:
            break
        recent.insert(0, msg)
        budget -= cost

    to_compress = non_system[: len(non_system) - len(recent)]
    return to_compress, recent


async def compress(
    messages: list[dict],
) -> tuple[list[dict], bool, dict]:
    """
    Compress a message list if its token count exceeds CONTEXT_TOKEN_LIMIT.

    Returns:
        (compressed_messages, was_compressed, token_stats)

    token_stats keys: original_tokens, compressed_tokens, saved_tokens
    """
    system_msgs = [m for m in messages if m["role"] == "system"]
    non_system = [m for m in messages if m["role"] != "system"]

    total_tokens = _history_tokens(non_system)

    if total_tokens <= CONTEXT_TOKEN_LIMIT:
        return messages, False, {"originalTokens": total_tokens, "compressedTokens": total_tokens, "savedTokens": 0}

    to_compress, recent = _split_by_token_budget(non_system)

    if not to_compress:
        # Everything fits in the recent budget already
        return messages, False, {"originalTokens": total_tokens, "compressedTokens": total_tokens, "savedTokens": 0}

    # Summarise the older turns
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in to_compress
    )
    summary = await foundry.complete(
        model=COMPRESSOR_MODEL,
        system_prompt=_COMPRESSOR_SYSTEM,
        user_message=f"Summarise this conversation history:\n\n{history_text}",
    )

    context_block = f"[Prior conversation summary]\n{summary}"

    # Merge summary into existing system message (or create one)
    if system_msgs:
        merged_system = {
            "role": "system",
            "content": f"{system_msgs[0]['content']}\n\n{context_block}",
        }
        leading = [merged_system] + system_msgs[1:]
    else:
        leading = [{"role": "system", "content": context_block}]

    compressed = leading + recent
    compressed_tokens = _history_tokens(compressed)

    token_stats = {
        "originalTokens": total_tokens,
        "compressedTokens": compressed_tokens,
        "savedTokens": total_tokens - compressed_tokens,
    }

    return compressed, True, token_stats


def stats(token_stats: dict) -> dict:
    """Build the WebSocket event payload for a compression event."""
    return {"type": "context_compressed", **token_stats}
