import httpx
import pytest
import respx

from pictomancer import AsyncClient, Callback, Client, Inline, PutUrl

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


class TestErrorPropagation:
    @respx.mock
    def test_4xx_raises(self):
        respx.post(f"{BASE}/v1/resize").mock(return_value=httpx.Response(402))

        with Client(api_key="k") as c:
            with pytest.raises(httpx.HTTPStatusError):
                c.resize("data:image/png;base64,xxx", scale=0.5)
