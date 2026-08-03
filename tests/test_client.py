import base64
import json

import httpx
import pytest
import respx

from pictomancer import (
    AsyncClient,
    Callback,
    Client,
    Inline,
    PutUrl,
    source_from_bytes,
    source_from_path,
)

BASE = "https://api.pictomancer.ai"
PNG = b"\x89PNG\r\n\x1a\n"
PUT_URL = "https://bucket.s3.amazonaws.com/key?X-Amz-Signature=abc"
CALLBACK_URL = "https://hooks.example.com/pig?token=abc"


class TestDeliveryHelpers:
    def test_inline(self):
        assert Inline() == {"mode": "inline"}

    def test_put_url_without_headers(self):
        assert PutUrl(PUT_URL) == {"mode": "put_url", "put_url": PUT_URL}

    def test_put_url_with_headers(self):
        out = PutUrl(PUT_URL, headers={"Content-Type": "image/webp"})

        assert out == {
            "mode": "put_url",
            "put_url": PUT_URL,
            "headers": {"Content-Type": "image/webp"},
        }

    def test_callback(self):
        assert Callback(CALLBACK_URL) == {"mode": "callback_url", "callback_url": CALLBACK_URL}

    def test_callback_with_secret(self):
        out = Callback(CALLBACK_URL, secret="s3cr3t")

        assert out == {
            "mode": "callback_url",
            "callback_url": CALLBACK_URL,
            "secret": "s3cr3t",
        }


class TestInlineReturnsBytes:
    @respx.mock
    def test_resize_inline_returns_bytes(self):
        respx.post(f"{BASE}/v1/resize").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/png"}, content=PNG)
        )

        with Client(api_key="k") as c:
            out = c.resize("data:image/png;base64,xxx", scale=0.5)

        assert out == PNG

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_resize_inline_returns_bytes(self):
        respx.post(f"{BASE}/v1/resize").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/png"}, content=PNG)
        )

        async with AsyncClient(api_key="k") as c:
            out = await c.resize("data:image/png;base64,xxx", scale=0.5)

        assert out == PNG


class TestPutUrlReturnsJson:
    @respx.mock
    def test_resize_put_url_returns_dict_and_sends_delivery(self):
        route = respx.post(f"{BASE}/v1/resize").mock(
            return_value=httpx.Response(
                200,
                json={"etag": "abc", "sha256": "0" * 64, "bytes_written": 10},
            )
        )

        with Client(api_key="k") as c:
            out = c.resize("data:image/png;base64,xxx", scale=0.5, delivery=PutUrl(PUT_URL))

        assert out == {"etag": "abc", "sha256": "0" * 64, "bytes_written": 10}
        sent = route.calls[0].request
        assert b'"put_url"' in sent.content
        assert b'"delivery"' in sent.content

    @respx.mock
    def test_compress_callback_returns_dict(self):
        respx.post(f"{BASE}/v1/compress").mock(
            return_value=httpx.Response(200, json={"status": 202, "sha256": "f" * 64})
        )

        with Client(api_key="k") as c:
            out = c.compress("data:image/png;base64,xxx", delivery=Callback(CALLBACK_URL))

        assert out["status"] == 202


class TestConvertParams:
    @respx.mock
    def test_convert_avif_sends_effort(self):
        route = respx.post(f"{BASE}/v1/convert").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/avif"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.convert("data:image/png;base64,xxx", "avif", q=50, effort=2)

        sent = route.calls[0].request
        assert b'"format": "avif"' in sent.content or b'"format":"avif"' in sent.content
        assert b'"effort"' in sent.content


class TestQualityTargetParams:
    @respx.mock
    def test_compress_sends_quality_target(self):
        route = respx.post(f"{BASE}/v1/compress").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.compress("data:image/png;base64,xxx", format="webp", quality_target=0.95)

        sent = json.loads(route.calls[0].request.content)
        assert sent["quality_target"] == 0.95

    @respx.mock
    def test_convert_sends_quality_target(self):
        route = respx.post(f"{BASE}/v1/convert").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/avif"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.convert("data:image/png;base64,xxx", "avif", quality_target=0.9)

        sent = json.loads(route.calls[0].request.content)
        assert sent["quality_target"] == 0.9

    @respx.mock
    def test_compress_omits_quality_target_by_default(self):
        route = respx.post(f"{BASE}/v1/compress").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.compress("data:image/png;base64,xxx", format="webp", q=80)

        sent = json.loads(route.calls[0].request.content)
        assert "quality_target" not in sent

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_convert_sends_quality_target(self):
        route = respx.post(f"{BASE}/v1/convert").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        async with AsyncClient(api_key="k") as c:
            await c.convert("data:image/png;base64,xxx", "webp", quality_target=0.95)

        sent = json.loads(route.calls[0].request.content)
        assert sent["quality_target"] == 0.95


class TestGeometryParams:
    @respx.mock
    def test_crop_smart_sends_gravity_without_xy(self):
        route = respx.post(f"{BASE}/v1/crop").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.crop("data:image/png;base64,xxx", gravity="attention", width=200, height=200)

        sent = json.loads(route.calls[0].request.content)
        assert sent["gravity"] == "attention"
        assert sent["width"] == 200
        assert sent["height"] == 200
        assert "x" not in sent
        assert "y" not in sent

    @respx.mock
    def test_crop_trim_sends_threshold(self):
        route = respx.post(f"{BASE}/v1/crop").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.crop("data:image/png;base64,xxx", trim=True, threshold=5.0)

        sent = json.loads(route.calls[0].request.content)
        assert sent["trim"] is True
        assert sent["threshold"] == 5.0
        assert "width" not in sent
        assert "gravity" not in sent

    @respx.mock
    def test_crop_manual_positional_regression(self):
        route = respx.post(f"{BASE}/v1/crop").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.crop("data:image/png;base64,xxx", 0, 0, 100, 100, format="webp")

        sent = json.loads(route.calls[0].request.content)
        assert sent["x"] == 0
        assert sent["y"] == 0
        assert sent["width"] == 100
        assert sent["height"] == 100
        assert sent["format"] == "webp"
        assert "gravity" not in sent
        assert "trim" not in sent

    @respx.mock
    def test_crop_omits_geometry_params_by_default(self):
        route = respx.post(f"{BASE}/v1/crop").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.crop("data:image/png;base64,xxx", 0, 0, 100, 100)

        sent = json.loads(route.calls[0].request.content)
        assert "gravity" not in sent
        assert "trim" not in sent
        assert "threshold" not in sent
        assert "autorot" not in sent

    @respx.mock
    def test_crop_sends_autorot(self):
        route = respx.post(f"{BASE}/v1/crop").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.crop("data:image/png;base64,xxx", 0, 0, 100, 100, autorot=True)

        sent = json.loads(route.calls[0].request.content)
        assert sent["autorot"] is True

    @respx.mock
    def test_resize_fill_sends_width_height_gravity(self):
        route = respx.post(f"{BASE}/v1/resize").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.resize("data:image/png;base64,xxx", width=200, height=150, gravity="entropy")

        sent = json.loads(route.calls[0].request.content)
        assert sent["width"] == 200
        assert sent["height"] == 150
        assert sent["gravity"] == "entropy"
        assert "scale" not in sent

    @respx.mock
    def test_resize_omits_fill_params_by_default(self):
        route = respx.post(f"{BASE}/v1/resize").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.resize("data:image/png;base64,xxx", scale=0.5)

        sent = json.loads(route.calls[0].request.content)
        assert "width" not in sent
        assert "height" not in sent
        assert "gravity" not in sent
        assert "autorot" not in sent

    @respx.mock
    def test_resize_sends_autorot(self):
        route = respx.post(f"{BASE}/v1/resize").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.resize("data:image/png;base64,xxx", scale=0.5, autorot=True)

        sent = json.loads(route.calls[0].request.content)
        assert sent["autorot"] is True

    @respx.mock
    def test_compress_sends_autorot(self):
        route = respx.post(f"{BASE}/v1/compress").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.compress("data:image/png;base64,xxx", format="webp", autorot=True)

        sent = json.loads(route.calls[0].request.content)
        assert sent["autorot"] is True

    @respx.mock
    def test_compress_omits_autorot_by_default(self):
        route = respx.post(f"{BASE}/v1/compress").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.compress("data:image/png;base64,xxx", format="webp")

        sent = json.loads(route.calls[0].request.content)
        assert "autorot" not in sent

    @respx.mock
    def test_convert_sends_autorot(self):
        route = respx.post(f"{BASE}/v1/convert").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/avif"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.convert("data:image/png;base64,xxx", "avif", autorot=True)

        sent = json.loads(route.calls[0].request.content)
        assert sent["autorot"] is True

    @respx.mock
    def test_convert_omits_autorot_by_default(self):
        route = respx.post(f"{BASE}/v1/convert").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/avif"}, content=PNG)
        )

        with Client(api_key="k") as c:
            c.convert("data:image/png;base64,xxx", "avif")

        sent = json.loads(route.calls[0].request.content)
        assert "autorot" not in sent

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_crop_smart_sends_gravity_without_xy(self):
        route = respx.post(f"{BASE}/v1/crop").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        async with AsyncClient(api_key="k") as c:
            await c.crop("data:image/png;base64,xxx", gravity="attention", width=200, height=200)

        sent = json.loads(route.calls[0].request.content)
        assert sent["gravity"] == "attention"
        assert "x" not in sent
        assert "y" not in sent

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_resize_fill_sends_width_height_gravity(self):
        route = respx.post(f"{BASE}/v1/resize").mock(
            return_value=httpx.Response(200, headers={"content-type": "image/webp"}, content=PNG)
        )

        async with AsyncClient(api_key="k") as c:
            await c.resize("data:image/png;base64,xxx", width=200, height=150, gravity="entropy")

        sent = json.loads(route.calls[0].request.content)
        assert sent["width"] == 200
        assert sent["height"] == 150
        assert sent["gravity"] == "entropy"
        assert "scale" not in sent


class TestErrorPropagation:
    @respx.mock
    def test_4xx_raises(self):
        respx.post(f"{BASE}/v1/resize").mock(return_value=httpx.Response(402))

        with Client(api_key="k") as c:
            with pytest.raises(httpx.HTTPStatusError):
                c.resize("data:image/png;base64,xxx", scale=0.5)


class TestSourceHelpers:
    def test_source_from_bytes_returns_base64(self):
        out = source_from_bytes(PNG)

        assert out == base64.b64encode(PNG).decode()

    def test_source_from_path_reads_and_encodes(self, tmp_path):
        path = tmp_path / "image.png"
        path.write_bytes(PNG)

        out = source_from_path(path)

        assert out == base64.b64encode(PNG).decode()

    def test_source_from_path_accepts_str(self, tmp_path):
        path = tmp_path / "image.png"
        path.write_bytes(PNG)

        out = source_from_path(str(path))

        assert out == base64.b64encode(PNG).decode()
