"""Tests for Prompt Lens — post-run per-model interpretation analysis.

Covers:
  - analyze_responses returns a LensResult per input
  - LensResult has non-empty interpretation and divergence_score 1-10
  - Parallel execution: N inputs → N separate Spark calls
  - DIVERGENCE:N parsing (happy path, missing sentinel → default 5, clamp)
  - Per-model failure is skipped, not raised
  - Council stream emits lens events after synth_done, before done
  - lens events use white-label names in `hex` field (hexal-whitelabel-names)
  - PromptLensEntry rows persisted to DB per lens result
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest

from app.lens.analyzer import LensInput, LensResult, analyze_responses
from app.llm.base import Message, StreamChunk

from .conftest import FakeClient, FakeSession, parse_sse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _CountingClient:
    """Fake Spark client that records how many times stream() was called."""

    def __init__(self, response_text: str, whitelabel: str = "Spark") -> None:
        self.whitelabel = whitelabel
        self._response_text = response_text
        self.call_count = 0

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        self.call_count += 1
        yield StreamChunk(delta=self._response_text)
        yield StreamChunk(delta="", total_tokens=10, cached_tokens=3)


class _ErrorClient:
    """Fake Spark client that always raises on stream()."""

    whitelabel = "Spark"

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        raise RuntimeError("Spark unavailable")
        yield  # make this an async generator


# ---------------------------------------------------------------------------
# Unit tests for analyze_responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_responses_returns_result_per_input() -> None:
    """analyze_responses returns one LensResult per LensInput."""
    spark = _CountingClient("It focused on the technical side.\nDIVERGENCE:4")
    inputs = [
        LensInput(whitelabel="Swift", text="some swift response", confidence=8),
        LensInput(whitelabel="Prism", text="some prism response", confidence=7),
    ]
    results = await analyze_responses(spark, "what is async?", inputs)

    assert len(results) == 2
    assert {r.whitelabel for r in results} == {"Swift", "Prism"}


@pytest.mark.asyncio
async def test_analyze_responses_nonempty_interpretation() -> None:
    """Each LensResult has a non-empty interpretation string."""
    spark = _CountingClient("The model prioritized conciseness.\nDIVERGENCE:3")
    inputs = [LensInput(whitelabel="Depth", text="depth response text", confidence=9)]
    results = await analyze_responses(spark, "explain entropy", inputs)

    assert len(results) == 1
    assert results[0].interpretation != ""
    assert len(results[0].interpretation) > 5


@pytest.mark.asyncio
async def test_analyze_responses_divergence_score_in_range() -> None:
    """divergence_score is clamped to 1-10."""
    spark = _CountingClient("Reframed the question broadly.\nDIVERGENCE:7")
    inputs = [LensInput(whitelabel="Atlas", text="atlas text", confidence=6)]
    results = await analyze_responses(spark, "explain recursion", inputs)

    assert 1 <= results[0].divergence_score <= 10
    assert results[0].divergence_score == 7


@pytest.mark.asyncio
async def test_analyze_responses_divergence_parsed_correctly() -> None:
    """DIVERGENCE:N sentinel is parsed from response text."""
    spark = _CountingClient(
        "The model took a practical coding angle, with examples.\nDIVERGENCE:6"
    )
    inputs = [LensInput(whitelabel="Horizon", text="horizon text", confidence=5)]
    results = await analyze_responses(spark, "how to sort a list?", inputs)

    assert results[0].divergence_score == 6


@pytest.mark.asyncio
async def test_analyze_responses_divergence_default_when_missing() -> None:
    """If Spark omits DIVERGENCE:N, divergence_score defaults to 5."""
    spark = _CountingClient("The model gave a broad overview without rating.")
    inputs = [LensInput(whitelabel="Swift", text="swift text", confidence=7)]
    results = await analyze_responses(spark, "what is machine learning?", inputs)

    assert results[0].divergence_score == 5


@pytest.mark.asyncio
async def test_analyze_responses_divergence_clamped_above_10() -> None:
    """DIVERGENCE score above 10 is clamped to 10."""
    spark = _CountingClient("Creative reframing happened here.\nDIVERGENCE:15")
    inputs = [LensInput(whitelabel="Prism", text="prism text", confidence=8)]
    results = await analyze_responses(spark, "explain creativity", inputs)

    assert results[0].divergence_score == 10


@pytest.mark.asyncio
async def test_analyze_responses_divergence_clamped_below_1() -> None:
    """DIVERGENCE score of 0 or below is clamped to 1."""
    spark = _CountingClient("Very literal interpretation.\nDIVERGENCE:0")
    inputs = [LensInput(whitelabel="Depth", text="depth text", confidence=9)]
    results = await analyze_responses(spark, "what is 2+2?", inputs)

    assert results[0].divergence_score == 1


@pytest.mark.asyncio
async def test_analyze_responses_parallel_calls() -> None:
    """Each LensInput triggers a separate Spark stream() call (parallelized)."""
    spark = _CountingClient("Focused on the core concept.\nDIVERGENCE:5")
    inputs = [
        LensInput(whitelabel="Swift", text="swift text", confidence=8),
        LensInput(whitelabel="Prism", text="prism text", confidence=7),
        LensInput(whitelabel="Depth", text="depth text", confidence=9),
    ]
    results = await analyze_responses(spark, "explain Python", inputs)

    # One call per input
    assert spark.call_count == 3
    assert len(results) == 3


@pytest.mark.asyncio
async def test_analyze_responses_per_model_failure_skipped() -> None:
    """If Spark raises for one model, that model is skipped (not raised)."""
    spark = _ErrorClient()
    inputs = [
        LensInput(whitelabel="Swift", text="swift text", confidence=8),
        LensInput(whitelabel="Prism", text="prism text", confidence=7),
    ]
    # Should not raise; failing models are omitted from results
    results = await analyze_responses(spark, "question", inputs)
    assert results == []


@pytest.mark.asyncio
async def test_analyze_responses_partial_failure_skipped() -> None:
    """When some calls succeed and others fail, only successes are returned."""

    class _PartialClient:
        """Fails on first call, succeeds on subsequent calls."""

        whitelabel = "Spark"
        _call_count = 0

        async def stream(
            self,
            messages: list[Message],
            cache_key: str | None = None,
            tools: list[dict[str, Any]] | None = None,
        ) -> AsyncIterator[StreamChunk]:
            self.__class__._call_count += 1
            # Fail on calls for "Swift" model (first item)
            if self.__class__._call_count == 1:
                raise RuntimeError("transient failure")
            yield StreamChunk(delta="Good interpretation.\nDIVERGENCE:5")
            yield StreamChunk(delta="", total_tokens=8, cached_tokens=2)

    _PartialClient._call_count = 0
    spark = _PartialClient()
    inputs = [
        LensInput(whitelabel="Swift", text="swift text", confidence=8),  # will fail
        LensInput(whitelabel="Prism", text="prism text", confidence=7),   # will succeed
    ]
    results = await analyze_responses(spark, "question", inputs)

    # Only 1 result (the successful one)
    assert len(results) == 1
    assert results[0].whitelabel == "Prism"


@pytest.mark.asyncio
async def test_analyze_responses_interpretation_excludes_divergence_line() -> None:
    """Interpretation text does not include the DIVERGENCE:N line itself."""
    spark = _CountingClient(
        "The model approached this from a first-principles angle.\nDIVERGENCE:8"
    )
    inputs = [LensInput(whitelabel="Apex", text="some text", confidence=10)]
    results = await analyze_responses(spark, "explain thermodynamics", inputs)

    assert "DIVERGENCE" not in results[0].interpretation
    assert "8" not in results[0].interpretation or "first-principles" in results[0].interpretation


# ---------------------------------------------------------------------------
# Council stream integration tests: lens events
# ---------------------------------------------------------------------------


def _make_spark_client(response_text: str) -> FakeClient:
    """Return a FakeClient that emits the given text (stands in for Spark)."""
    return FakeClient([response_text], whitelabel="Spark")


def _setup_council_with_lens(
    monkeypatch: pytest.MonkeyPatch,
    council_clients: dict[str, FakeClient],
    apex_client: object,
    spark_client: object,
    fake_session: FakeSession | None = None,
) -> object:
    """Wire app with fake clients including Spark for lens phase."""
    import uuid as _uuid

    from fastapi.testclient import TestClient

    from app.api import query as query_module
    from app.auth.middleware import get_current_user
    from app.auth.models import AuthUser
    from app.db.session import get_session
    from app.main import app

    user = AuthUser(id=_uuid.uuid4(), email="user@example.com")
    session = fake_session or FakeSession()

    def _get_client(wl: str) -> object:
        if wl == "Apex":
            return apex_client
        if wl == "Spark":
            return spark_client
        if wl in council_clients:
            return council_clients[wl]
        raise KeyError(f"Unknown white-label {wl!r}")

    async def _fake_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = _fake_session
    # Patch get_client in both the query API module AND council/stream module
    # (council/stream imports get_client directly at module level)
    monkeypatch.setattr(query_module, "get_client", _get_client)
    import app.council.stream as council_stream_module
    monkeypatch.setattr(council_stream_module, "get_client", _get_client)
    return TestClient(app)


class _SimpleApexClient:
    """Minimal Apex fake for lens integration tests."""

    whitelabel = "Apex"

    async def stream(
        self,
        messages: list[Message],
        cache_key: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta="Synthesis result.")
        yield StreamChunk(delta="", total_tokens=15, cached_tokens=0)


def test_council_stream_emits_lens_events_after_synth_done(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """lens events are emitted after synth_done and before done."""
    from fastapi.testclient import TestClient

    from app.main import app

    clients = {
        "Swift": FakeClient(["swift answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("Took a concise, direct angle.\nDIVERGENCE:3")

    tc = _setup_council_with_lens(monkeypatch, clients, apex, spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "what is async?", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]

    assert "lens" in names
    synth_done_idx = names.index("synth_done")
    done_idx = names.index("done")
    lens_indices = [i for i, n in enumerate(names) if n == "lens"]

    # All lens events come after synth_done
    assert all(i > synth_done_idx for i in lens_indices)
    # All lens events come before done
    assert all(i < done_idx for i in lens_indices)


def test_council_stream_lens_events_use_whitelabel_hex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """lens events use white-label names in the `hex` field (hexal-whitelabel-names)."""
    from app.main import app

    clients = {
        "Swift": FakeClient(["swift answer [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism answer [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("Focused on practical examples.\nDIVERGENCE:5")

    tc = _setup_council_with_lens(monkeypatch, clients, apex, spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "explain caching", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    lens_events = [(e, d) for e, d in events if e == "lens"]

    assert len(lens_events) == 2
    hex_names = {d["hex"] for _, d in lens_events}
    # Must use white-label names — not real model names
    assert hex_names == {"Swift", "Prism"}


def test_council_stream_lens_one_per_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exactly one lens event per council model."""
    from app.main import app

    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Depth": FakeClient(["depth [[CONF:9]]"], whitelabel="Depth"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("Comprehensive coverage.\nDIVERGENCE:4")

    tc = _setup_council_with_lens(monkeypatch, clients, apex, spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={
                    "mode": "council",
                    "query": "what is a neural network?",
                    "models": ["Swift", "Depth", "Prism"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    lens_events = [(e, d) for e, d in events if e == "lens"]

    assert len(lens_events) == 3
    hex_names = {d["hex"] for _, d in lens_events}
    assert hex_names == {"Swift", "Depth", "Prism"}


def test_council_stream_lens_has_interpretation_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """lens event payload contains a non-empty interpretation string."""
    from app.main import app

    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("The model prioritized accuracy over brevity.\nDIVERGENCE:2")

    tc = _setup_council_with_lens(monkeypatch, clients, apex, spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "what is entropy?", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    lens_events = [(e, d) for e, d in events if e == "lens"]

    for _, d in lens_events:
        assert "interpretation" in d
        assert isinstance(d["interpretation"], str)
        assert len(d["interpretation"]) > 0


def test_council_stream_done_still_emitted_when_lens_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """done is emitted even when the Spark/lens phase raises an exception."""
    from app.main import app

    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()

    # Spark client that raises on every call
    error_spark = _ErrorClient()

    tc = _setup_council_with_lens(monkeypatch, clients, apex, error_spark)
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "question", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    events = parse_sse(r.text)
    names = [e for e, _ in events]
    # done must always be emitted
    assert "done" in names
    assert names[-1] == "done"


def test_council_stream_lens_persists_db_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PromptLensEntry rows are added to the DB session for each lens result."""
    from app.db.models import PromptLensEntry as PromptLensEntryModel
    from app.main import app

    fake_session = FakeSession()
    clients = {
        "Swift": FakeClient(["swift [[CONF:8]]"], whitelabel="Swift"),
        "Prism": FakeClient(["prism [[CONF:7]]"], whitelabel="Prism"),
    }
    apex = _SimpleApexClient()
    spark = _make_spark_client("Analytical angle.\nDIVERGENCE:6")

    tc = _setup_council_with_lens(
        monkeypatch, clients, apex, spark, fake_session=fake_session
    )
    try:
        with tc:
            r = tc.post(
                "/api/query",
                json={"mode": "council", "query": "what is REST?", "models": ["Swift", "Prism"]},
            )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    lens_rows = [
        o for o in fake_session.added if isinstance(o, PromptLensEntryModel)
    ]
    assert len(lens_rows) == 2
    persisted_models = {row.model for row in lens_rows}
    assert persisted_models == {"Swift", "Prism"}
    for row in lens_rows:
        assert row.interpretation
        assert row.divergence_score is not None
        assert 1 <= row.divergence_score <= 10
