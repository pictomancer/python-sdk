"""Unit tests for the Pictomancer client — no network calls."""

import json

import httpx
import pytest
import respx

from pictomancer import AnalyzeResult, FormatSpec, Pictomancer, PictomancerError, PipelineOp

BASE = "https://api.pictomancer.ai"
SOURCE = "https://example.com/img.jpg"

FORMAT_INFO_RESPONSE = {
    "formats": [
        {"id": "jpeg", "suffix": ".jpg", "options": [
            {"name": "q", "kind": "int", "min": 1, "max": 100, "default_str": "85",
             "description": "Quality"},
        ]},
        {"id": "webp", "suffix": ".webp", "options": []},
    ],
}


# ── Helpers ──────────────────────────────────────────────────────────


def sent_json(route: respx.Route) -> dict:
    """Extract the JSON payload sent in the first call to a mocked route."""
    return json.loads(route.calls[0].request.content)


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
async def client():
    async with Pictomancer() as c:
        yield c


@pytest.fixture
async def wallet_client():
    async with Pictomancer(wallet="0xABC") as c:
        yield c


# ── info ─────────────────────────────────────────────────────────────


class TestInfo:
    @respx.mock
    async def test_returns_format_specs(self, client: Pictomancer):
        respx.get(f"{BASE}/v1/info").respond(json=FORMAT_INFO_RESPONSE)

        result = await client.info()

        assert len(result) == 2

    @respx.mock
    async def test_parses_format_ids(self, client: Pictomancer):
        respx.get(f"{BASE}/v1/info").respond(json=FORMAT_INFO_RESPONSE)

        result = await client.info()

        assert all(isinstance(f, FormatSpec) for f in result)
        assert result[0].id == "jpeg"
        assert result[1].id == "webp"

    @respx.mock
    async def test_parses_format_options(self, client: Pictomancer):
        respx.get(f"{BASE}/v1/info").respond(json=FORMAT_INFO_RESPONSE)

        result = await client.info()

        assert len(result[0].options) == 1
        assert result[0].options[0].name == "q"


# ── analyze ──────────────────────────────────────────────────────────


class TestAnalyze:
    @respx.mock
    async def test_returns_analyze_result_type(self, client: Pictomancer):
        respx.post(f"{BASE}/v1/analyze").respond(json={"size_bytes": 42_000})

        result = await client.analyze(SOURCE)

        assert isinstance(result, AnalyzeResult)

    @respx.mock
    async def test_returns_correct_size(self, client: Pictomancer):
        respx.post(f"{BASE}/v1/analyze").respond(json={"size_bytes": 42_000})

        result = await client.analyze(SOURCE)

        assert result.size_bytes == 42_000


# ── resize ───────────────────────────────────────────────────────────


class TestResize:
    @respx.mock
    async def test_returns_image_bytes(self, client: Pictomancer):
        respx.post(f"{BASE}/v1/resize").respond(content=b"\x89PNG")

        data = await client.resize(SOURCE, scale=0.5)

        assert data == b"\x89PNG"

    @respx.mock
    async def test_sends_scale_param(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/resize").respond(content=b"x")

        await client.resize(SOURCE, scale=0.5)

        assert sent_json(route)["scale"] == 0.5

    @respx.mock
    async def test_excludes_none_params(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/resize").respond(content=b"x")

        await client.resize(SOURCE, scale=0.5)

        payload = sent_json(route)
        assert "scale_x" not in payload
        assert "scale_y" not in payload
        assert "format" not in payload


# ── compress ─────────────────────────────────────────────────────────


class TestCompress:
    @respx.mock
    async def test_sends_quality(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/compress").respond(content=b"\xff\xd8")

        await client.compress(SOURCE, q=60)

        assert sent_json(route)["q"] == 60

    @respx.mock
    async def test_sends_strip(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/compress").respond(content=b"\xff\xd8")

        await client.compress(SOURCE, strip=True)

        assert sent_json(route)["strip"] is True

    @respx.mock
    async def test_excludes_none_params(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/compress").respond(content=b"\xff\xd8")

        await client.compress(SOURCE, q=60, strip=True)

        assert "format" not in sent_json(route)


# ── convert ──────────────────────────────────────────────────────────


class TestConvert:
    @respx.mock
    async def test_sends_format(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/convert").respond(content=b"RIFF")

        await client.convert(SOURCE, format="webp")

        assert sent_json(route)["format"] == "webp"

    @respx.mock
    async def test_sends_quality(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/convert").respond(content=b"RIFF")

        await client.convert(SOURCE, format="webp", q=85)

        assert sent_json(route)["q"] == 85

    @respx.mock
    async def test_excludes_none_params(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/convert").respond(content=b"RIFF")

        await client.convert(SOURCE, format="webp")

        payload = sent_json(route)
        assert "q" not in payload
        assert "strip" not in payload
        assert "lossless" not in payload


# ── crop ─────────────────────────────────────────────────────────────


class TestCrop:
    @respx.mock
    async def test_sends_rect_params(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/crop").respond(content=b"\x89PNG")

        await client.crop(SOURCE, x=10, y=20, width=100, height=200)

        payload = sent_json(route)
        assert payload["x"] == 10
        assert payload["y"] == 20
        assert payload["width"] == 100
        assert payload["height"] == 200

    @respx.mock
    async def test_excludes_format_when_none(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/crop").respond(content=b"\x89PNG")

        await client.crop(SOURCE, x=0, y=0, width=50, height=50)

        assert "format" not in sent_json(route)


# ── pipeline ─────────────────────────────────────────────────────────


class TestPipeline:
    @respx.mock
    async def test_sends_operation_count(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/pipeline").respond(content=b"ok")
        ops = [
            PipelineOp(type="resize", params={"scale": "0.5"}),
            PipelineOp(type="convert", params={"format": "webp"}),
        ]

        await client.pipeline(SOURCE, ops)

        assert len(sent_json(route)["operations"]) == 2

    @respx.mock
    async def test_sends_operation_types(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/pipeline").respond(content=b"ok")
        ops = [
            PipelineOp(type="resize", params={"scale": "0.5"}),
            PipelineOp(type="convert", params={"format": "webp"}),
        ]

        await client.pipeline(SOURCE, ops)

        types = [o["type"] for o in sent_json(route)["operations"]]
        assert types == ["resize", "convert"]


# ── error handling ───────────────────────────────────────────────────


class TestErrorHandling:
    @respx.mock
    async def test_raises_on_4xx_with_json_detail(self, client: Pictomancer):
        respx.post(f"{BASE}/v1/analyze").respond(
            status_code=422, json={"detail": "source is required"},
        )

        with pytest.raises(PictomancerError) as exc_info:
            await client.analyze("")

        assert exc_info.value.status == 422

    @respx.mock
    async def test_error_contains_detail_message(self, client: Pictomancer):
        respx.post(f"{BASE}/v1/analyze").respond(
            status_code=422, json={"detail": "source is required"},
        )

        with pytest.raises(PictomancerError) as exc_info:
            await client.analyze("")

        assert "source is required" in exc_info.value.detail

    @respx.mock
    async def test_raises_on_non_json_error_body(self, client: Pictomancer):
        respx.post(f"{BASE}/v1/analyze").respond(
            status_code=500, content=b"Internal Server Error",
        )

        with pytest.raises(PictomancerError) as exc_info:
            await client.analyze(SOURCE)

        assert exc_info.value.status == 500
        assert "Internal Server Error" in exc_info.value.detail


# ── wallet header ────────────────────────────────────────────────────


class TestWalletHeader:
    @respx.mock
    async def test_sends_wallet_header(self, wallet_client: Pictomancer):
        route = respx.post(f"{BASE}/v1/analyze").respond(json={"size_bytes": 1})

        await wallet_client.analyze(SOURCE)

        assert route.calls[0].request.headers["x-agent-wallet"] == "0xABC"

    @respx.mock
    async def test_omits_wallet_header_when_not_set(self, client: Pictomancer):
        route = respx.post(f"{BASE}/v1/analyze").respond(json={"size_bytes": 1})

        await client.analyze(SOURCE)

        assert "x-agent-wallet" not in route.calls[0].request.headers


# ── http_client injection ────────────────────────────────────────────


class TestClientInjection:
    @respx.mock
    async def test_uses_injected_client(self):
        route = respx.post(f"{BASE}/v1/analyze").respond(json={"size_bytes": 99})
        custom = httpx.AsyncClient(base_url=BASE)

        try:
            p = Pictomancer(http_client=custom)
            result = await p.analyze(SOURCE)

            assert result.size_bytes == 99
        finally:
            await custom.aclose()

    @respx.mock
    async def test_does_not_close_injected_client(self):
        route = respx.post(f"{BASE}/v1/analyze").respond(json={"size_bytes": 1})
        custom = httpx.AsyncClient(base_url=BASE)

        try:
            async with Pictomancer(http_client=custom) as p:
                await p.analyze(SOURCE)
            # After context exit, injected client should still be open
            assert not custom.is_closed
        finally:
            await custom.aclose()
