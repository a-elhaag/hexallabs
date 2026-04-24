"""Workflow mode executor — node-based pipeline streaming.

Nodes execute in topological order. Output of upstream nodes becomes input
to downstream nodes. Model nodes stream SSE events per node.

Node format:
    {
        "id": "node_1",           # unique string ID
        "type": "model",          # "model" | "passthrough" | "prompt_template"
        "model": "Swift",         # whitelabel (only for type=model)
        "inputs": ["node_0"],     # list of upstream node IDs
        "config": {}              # optional extra config
    }

Nodes with no inputs receive the user's original query.

SSE events emitted:
    session        {session_id, mode="workflow"}
    hex_start      {hex: node_model}          — type=model only
    token          {hex, delta}               — type=model only
    hex_done       {hex, tokens, cached_tokens} — type=model only
    error          {hex, code, message}       — on node failure
    done           {session_id, duration_ms}
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from typing import Literal

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.quota import QuotaService
from app.db.models import Message as MessageRow
from app.db.models import Query as QueryRow
from app.db.models.user_quota import UserQuota
from app.llm.base import Message as LLMMessage
from app.llm.factory import get_client
from app.sse.events import SseEvent, format_event
from app.tools.scout import scout_force

ScoutMode = Literal["off", "auto", "force"]

logger = logging.getLogger(__name__)

_JOIN_SEP = "\n\n---\n\n"


# ---------------------------------------------------------------------------
# Topological sort
# ---------------------------------------------------------------------------


def _topo_sort(nodes: list[dict[str, object]]) -> list[dict[str, object]] | None:
    """Return nodes in topological execution order, or None if a cycle exists.

    Kahn's algorithm: nodes with no remaining in-edges are processed first.
    """
    node_ids = {n["id"] for n in nodes}
    id_to_node: dict[str, dict[str, object]] = {n["id"]: n for n in nodes}

    # Build in-degree map and adjacency list (upstream → downstream)
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    dependents: dict[str, list[str]] = defaultdict(list)

    for node in nodes:
        node_inputs: list[str] = list(node.get("inputs") or [])  # type: ignore[arg-type]
        for upstream_id in node_inputs:
            if upstream_id in node_ids:
                in_degree[node["id"]] += 1
                dependents[upstream_id].append(str(node["id"]))

    queue: deque[str] = deque(nid for nid, deg in in_degree.items() if deg == 0)
    ordered: list[dict[str, object]] = []

    while queue:
        nid = queue.popleft()
        ordered.append(id_to_node[nid])
        for dep_id in dependents[nid]:
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                queue.append(dep_id)

    if len(ordered) != len(nodes):
        return None  # cycle detected

    return ordered


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def _workflow_stream(
    db: AsyncSession,
    query_row: QueryRow,
    prompt: str,
    nodes: list[dict[str, object]],
    *,
    scout: ScoutMode = "off",
    quota: UserQuota | None = None,
) -> AsyncIterator[bytes]:
    """Execute a workflow pipeline and stream SSE events.

    Args:
        db: Async SQLAlchemy session.
        query_row: Persisted QueryRow for this request.
        prompt: Original user query (fed to root nodes).
        nodes: List of node dicts in any order; will be topologically sorted.
        scout: Web search injection mode ("off", "force", "auto").
    """
    start_ns = time.monotonic_ns()
    session_id = str(query_row.session_id)

    yield format_event(SseEvent("session", {"session_id": session_id, "mode": "workflow"}))

    # Scout pre-injection (force/auto both do pre-execution in workflow)
    scout_context_text: str | None = None
    if scout in ("force", "auto"):
        from app.config import get_settings
        settings = get_settings()
        try:
            context_text, pre_result = await scout_force(prompt, settings)
        except ValueError:
            query_row.status = "error"
            yield format_event(SseEvent("error", {"hex": "workflow", "code": "MissingConfig", "message": "TAVILY_API_KEY not set"}))
            duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
            return
        except Exception as exc:
            query_row.status = "error"
            yield format_event(SseEvent("error", {"hex": "workflow", "code": type(exc).__name__, "message": str(exc)[:500]}))
            duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
            return
        force_id = f"force_{uuid.uuid4().hex[:8]}"
        yield format_event(SseEvent("tool_call", {"hex": "workflow", "id": force_id, "name": "web_search", "input": {"query": prompt}, "forced": True}))
        yield format_event(SseEvent("tool_result", {"hex": "workflow", "id": force_id, "name": "web_search", "summary": pre_result.summary, "urls": pre_result.urls, "result_count": pre_result.result_count}))
        scout_context_text = context_text

    if not nodes:
        query_row.status = "done"
        query_row.completed_at = func.now()
        duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
        return

    # Topological sort
    ordered = _topo_sort(nodes)
    if ordered is None:
        query_row.status = "error"
        query_row.error = "workflow graph contains a cycle"
        yield format_event(SseEvent(
            "error",
            {"hex": "workflow", "code": "CycleDetected", "message": "workflow graph contains a cycle"},
        ))
        duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
        yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
        return

    # Execute nodes in topological order
    node_outputs: dict[str, str] = {}  # node_id → output text

    for node in ordered:
        node_id: str = str(node["id"])
        node_type: str = str(node.get("type", "model"))
        node_inputs_ids: list[str] = list(node.get("inputs") or [])  # type: ignore[arg-type]

        # Compute input for this node
        if not node_inputs_ids:
            node_input = prompt
        else:
            upstream_texts: list[str] = []
            for uid in node_inputs_ids:
                if uid in node_outputs:
                    upstream_texts.append(node_outputs[uid])
            node_input = _JOIN_SEP.join(upstream_texts) if upstream_texts else prompt

        if node_type == "model":
            # Collect output via side-channel list passed into generator
            collected_output: list[str] = []

            # We need to collect the output text while streaming SSE bytes.
            # Re-implement the model node inline to share the collected list.
            whitelabel: str = str(node.get("model", ""))

            try:
                client = get_client(whitelabel)
            except KeyError as exc:
                yield format_event(SseEvent(
                    "error",
                    {"hex": node_id, "code": "UnknownModel", "message": str(exc)[:500]},
                ))
                node_outputs[node_id] = ""
                continue

            yield format_event(SseEvent("hex_start", {"hex": whitelabel}))

            messages: list[LLMMessage] = []
            if scout_context_text:
                messages.append(LLMMessage(role="system", content=scout_context_text, cache=True))
            messages.append(LLMMessage(role="user", content=node_input))

            total_tokens: int | None = None
            cached_tokens: int | None = None
            node_failed = False

            try:
                async for chunk in client.stream(messages):
                    if chunk.delta:
                        collected_output.append(chunk.delta)
                        yield format_event(SseEvent("token", {"hex": whitelabel, "delta": chunk.delta}))
                    if chunk.total_tokens is not None:
                        total_tokens = chunk.total_tokens
                    if chunk.cached_tokens is not None:
                        cached_tokens = chunk.cached_tokens
            except Exception as exc:
                logger.exception(
                    "workflow: model node %r (%s) stream failed", node_id, whitelabel
                )
                yield format_event(SseEvent(
                    "error",
                    {"hex": whitelabel, "code": type(exc).__name__, "message": str(exc)[:500]},
                ))
                node_outputs[node_id] = "".join(collected_output)
                node_failed = True

            if not node_failed:
                full_text = "".join(collected_output)
                node_outputs[node_id] = full_text

                db.add(MessageRow(
                    query_id=query_row.id,
                    role="model",
                    model=whitelabel,
                    content=full_text,
                    tokens_out=total_tokens,
                    stage="workflow",
                ))

                yield format_event(SseEvent("hex_done", {
                    "hex": whitelabel,
                    "tokens": total_tokens or 0,
                    "cached_tokens": cached_tokens or 0,
                }))
                if quota is not None and total_tokens:
                    await QuotaService.deduct(db, quota, total_tokens, whitelabel)

        elif node_type == "passthrough":
            # Pass input through unchanged, no SSE events
            node_outputs[node_id] = node_input

        elif node_type == "prompt_template":
            # Apply f-string template with {input} placeholder
            config: dict[str, object] = dict(node.get("config") or {})  # type: ignore[arg-type]
            template: str = str(config.get("template", "{input}"))
            try:
                result_text = template.format(input=node_input)
            except (KeyError, ValueError) as exc:
                yield format_event(SseEvent(
                    "error",
                    {
                        "hex": node_id,
                        "code": "TemplateError",
                        "message": f"prompt_template formatting failed: {exc!s}",
                    },
                ))
                node_outputs[node_id] = node_input
                continue
            node_outputs[node_id] = result_text

        else:
            # Unknown node type — skip and emit error, continue pipeline
            yield format_event(SseEvent(
                "error",
                {
                    "hex": node_id,
                    "code": "UnknownNodeType",
                    "message": f"unknown node type {node_type!r}; skipping",
                },
            ))
            node_outputs[node_id] = node_input

    query_row.status = "done"
    query_row.completed_at = func.now()

    duration_ms = (time.monotonic_ns() - start_ns) // 1_000_000
    yield format_event(SseEvent("done", {"session_id": session_id, "duration_ms": duration_ms}))
