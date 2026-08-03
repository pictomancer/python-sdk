"""Pictomancer.ai Python SDK."""

import base64
from os import PathLike
from pathlib import Path

import httpx

DEFAULT_BASE_URL = "https://api.pictomancer.ai"


def source_from_bytes(data: bytes) -> str:
    """Base64 source for in-memory image bytes (the API accepts raw base64)."""
    return base64.b64encode(data).decode()


def source_from_path(path: str | PathLike) -> str:
    """Base64 source for a local image file."""
    return source_from_bytes(Path(path).read_bytes())


def Inline() -> dict:
    """Default delivery: the optimized bytes are returned in the response."""
    return {"mode": "inline"}


def PutUrl(url: str, *, headers: dict | None = None) -> dict:
    """Delivery to a customer-signed presigned PUT URL (S3/R2/GCS/Azure).

    The bytes are uploaded there and the op returns a JSON dict (etag, sha256,
    bytes_written, ...) instead of raw bytes. No cloud credentials reach us.
    """
    target: dict = {"mode": "put_url", "put_url": url}
    if headers:
        target["headers"] = headers
    return target


def Callback(url: str, *, headers: dict | None = None, secret: str | None = None) -> dict:
    """Delivery via POST to a customer callback endpoint (async/large jobs).

    The bytes are POSTed to `url` with an X-Pig-Sha256 integrity header; the op
    returns a JSON dict (status, sha256, bytes_sent, ...). Secure the endpoint
    with a token in the URL — no credentials are stored on our side.

    Pass `secret` to have the body signed with HMAC-SHA256: we send
    `X-Pig-Signature: sha256=<hex>`, which you recompute on your endpoint with
    the same secret (constant-time compare) to authenticate the callback. The
    secret is used per request and never stored.
    """
    target: dict = {"mode": "callback_url", "callback_url": url}
    if headers:
        target["headers"] = headers
    if secret:
        target["secret"] = secret
    return target


def _result(resp: httpx.Response):
    """Image bytes for inline delivery, parsed JSON for put_url/callback_url."""
    resp.raise_for_status()
    if resp.headers.get("content-type", "").startswith("application/json"):
        return resp.json()
    return resp.content


class Client:
    """Synchronous Pictomancer client."""

    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(base_url=base_url, headers=headers, timeout=timeout)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _post(self, path: str, body: dict, delivery: dict | None):
        if delivery is not None:
            body["delivery"] = delivery
        return _result(self._client.post(path, json=body))

    def info(self) -> dict:
        resp = self._client.get("/v1/info")
        resp.raise_for_status()
        return resp.json()

    def usage(self) -> dict:
        resp = self._client.get("/v1/usage")
        resp.raise_for_status()
        return resp.json()

    def analyze(self, source: str) -> dict:
        resp = self._client.post("/v1/analyze", json={"source": source})
        resp.raise_for_status()
        return resp.json()

    def resize(self, source: str, *, scale: float | None = None, scale_x: float | None = None, scale_y: float | None = None, format: str | None = None, width: int | None = None, height: int | None = None, gravity: str | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        """Fill mode: pass `width` + `height` (optionally `gravity`, default `attention`) instead of scale/scale_x/scale_y to resize and smart-crop to exact dimensions in one call. `gravity` is one of 'attention', 'entropy', 'centre'."""
        body: dict = {"source": source}
        if scale is not None: body["scale"] = scale
        if scale_x is not None: body["scale_x"] = scale_x
        if scale_y is not None: body["scale_y"] = scale_y
        if format: body["format"] = format
        if width is not None: body["width"] = width
        if height is not None: body["height"] = height
        if gravity: body["gravity"] = gravity
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return self._post("/v1/resize", body, delivery)

    def compress(self, source: str, *, format: str | None = None, q: int | None = None, strip: bool | None = None, quality_target: float | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        body: dict = {"source": source}
        if format: body["format"] = format
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        if quality_target is not None: body["quality_target"] = quality_target
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return self._post("/v1/compress", body, delivery)

    def convert(self, source: str, format: str, *, q: int | None = None, strip: bool | None = None, lossless: bool | None = None, effort: int | None = None, quality_target: float | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        body: dict = {"source": source, "format": format}
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        if lossless is not None: body["lossless"] = lossless
        if effort is not None: body["effort"] = effort
        if quality_target is not None: body["quality_target"] = quality_target
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return self._post("/v1/convert", body, delivery)

    def crop(self, source: str, x: int | None = None, y: int | None = None, width: int | None = None, height: int | None = None, *, format: str | None = None, gravity: str | None = None, trim: bool | None = None, threshold: float | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        """Three mutually exclusive modes: manual (x+y+width+height), smart (`gravity` one of 'attention', 'entropy', 'centre' + width+height), trim (`trim=True`, optional `threshold`, default 10.0 server-side). `autorot` is valid in all three."""
        body: dict = {"source": source}
        if x is not None: body["x"] = x
        if y is not None: body["y"] = y
        if width is not None: body["width"] = width
        if height is not None: body["height"] = height
        if format: body["format"] = format
        if gravity: body["gravity"] = gravity
        if trim is not None: body["trim"] = trim
        if threshold is not None: body["threshold"] = threshold
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return self._post("/v1/crop", body, delivery)

    def pipeline(self, source: str, operations: list[dict], *, delivery: dict | None = None) -> bytes | dict:
        body: dict = {"source": source, "operations": operations}
        return self._post("/v1/pipeline", body, delivery)


class AsyncClient:
    """Asynchronous Pictomancer client."""

    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout)

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _post(self, path: str, body: dict, delivery: dict | None):
        if delivery is not None:
            body["delivery"] = delivery
        return _result(await self._client.post(path, json=body))

    async def info(self) -> dict:
        resp = await self._client.get("/v1/info")
        resp.raise_for_status()
        return resp.json()

    async def usage(self) -> dict:
        resp = await self._client.get("/v1/usage")
        resp.raise_for_status()
        return resp.json()

    async def analyze(self, source: str) -> dict:
        resp = await self._client.post("/v1/analyze", json={"source": source})
        resp.raise_for_status()
        return resp.json()

    async def resize(self, source: str, *, scale: float | None = None, scale_x: float | None = None, scale_y: float | None = None, format: str | None = None, width: int | None = None, height: int | None = None, gravity: str | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        """Fill mode: pass `width` + `height` (optionally `gravity`, default `attention`) instead of scale/scale_x/scale_y to resize and smart-crop to exact dimensions in one call. `gravity` is one of 'attention', 'entropy', 'centre'."""
        body: dict = {"source": source}
        if scale is not None: body["scale"] = scale
        if scale_x is not None: body["scale_x"] = scale_x
        if scale_y is not None: body["scale_y"] = scale_y
        if format: body["format"] = format
        if width is not None: body["width"] = width
        if height is not None: body["height"] = height
        if gravity: body["gravity"] = gravity
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return await self._post("/v1/resize", body, delivery)

    async def compress(self, source: str, *, format: str | None = None, q: int | None = None, strip: bool | None = None, quality_target: float | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        body: dict = {"source": source}
        if format: body["format"] = format
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        if quality_target is not None: body["quality_target"] = quality_target
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return await self._post("/v1/compress", body, delivery)

    async def convert(self, source: str, format: str, *, q: int | None = None, strip: bool | None = None, lossless: bool | None = None, effort: int | None = None, quality_target: float | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        body: dict = {"source": source, "format": format}
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        if lossless is not None: body["lossless"] = lossless
        if effort is not None: body["effort"] = effort
        if quality_target is not None: body["quality_target"] = quality_target
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return await self._post("/v1/convert", body, delivery)

    async def crop(self, source: str, x: int | None = None, y: int | None = None, width: int | None = None, height: int | None = None, *, format: str | None = None, gravity: str | None = None, trim: bool | None = None, threshold: float | None = None, autorot: bool | None = None, delivery: dict | None = None, **kwargs) -> bytes | dict:
        """Three mutually exclusive modes: manual (x+y+width+height), smart (`gravity` one of 'attention', 'entropy', 'centre' + width+height), trim (`trim=True`, optional `threshold`, default 10.0 server-side). `autorot` is valid in all three."""
        body: dict = {"source": source}
        if x is not None: body["x"] = x
        if y is not None: body["y"] = y
        if width is not None: body["width"] = width
        if height is not None: body["height"] = height
        if format: body["format"] = format
        if gravity: body["gravity"] = gravity
        if trim is not None: body["trim"] = trim
        if threshold is not None: body["threshold"] = threshold
        if autorot is not None: body["autorot"] = autorot
        body.update(kwargs)
        return await self._post("/v1/crop", body, delivery)

    async def pipeline(self, source: str, operations: list[dict], *, delivery: dict | None = None) -> bytes | dict:
        body: dict = {"source": source, "operations": operations}
        return await self._post("/v1/pipeline", body, delivery)
