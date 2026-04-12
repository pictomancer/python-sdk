"""Pictomancer.ai Python SDK."""

import httpx

DEFAULT_BASE_URL = "https://api.pictomancer.ai"


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

    def resize(self, source: str, *, scale: float | None = None, scale_x: float | None = None, scale_y: float | None = None, format: str | None = None, **kwargs) -> bytes:
        body = {"source": source}
        if scale is not None: body["scale"] = scale
        if scale_x is not None: body["scale_x"] = scale_x
        if scale_y is not None: body["scale_y"] = scale_y
        if format: body["format"] = format
        body.update(kwargs)
        resp = self._client.post("/v1/resize", json=body)
        resp.raise_for_status()
        return resp.content

    def compress(self, source: str, *, format: str | None = None, q: int | None = None, strip: bool | None = None, **kwargs) -> bytes:
        body = {"source": source}
        if format: body["format"] = format
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        body.update(kwargs)
        resp = self._client.post("/v1/compress", json=body)
        resp.raise_for_status()
        return resp.content

    def convert(self, source: str, format: str, *, q: int | None = None, strip: bool | None = None, lossless: bool | None = None, **kwargs) -> bytes:
        body = {"source": source, "format": format}
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        if lossless is not None: body["lossless"] = lossless
        body.update(kwargs)
        resp = self._client.post("/v1/convert", json=body)
        resp.raise_for_status()
        return resp.content

    def crop(self, source: str, x: int, y: int, width: int, height: int, *, format: str | None = None, **kwargs) -> bytes:
        body = {"source": source, "x": x, "y": y, "width": width, "height": height}
        if format: body["format"] = format
        body.update(kwargs)
        resp = self._client.post("/v1/crop", json=body)
        resp.raise_for_status()
        return resp.content

    def pipeline(self, source: str, operations: list[dict]) -> bytes:
        body = {"source": source, "operations": operations}
        resp = self._client.post("/v1/pipeline", json=body)
        resp.raise_for_status()
        return resp.content


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

    async def resize(self, source: str, *, scale: float | None = None, scale_x: float | None = None, scale_y: float | None = None, format: str | None = None, **kwargs) -> bytes:
        body = {"source": source}
        if scale is not None: body["scale"] = scale
        if scale_x is not None: body["scale_x"] = scale_x
        if scale_y is not None: body["scale_y"] = scale_y
        if format: body["format"] = format
        body.update(kwargs)
        resp = await self._client.post("/v1/resize", json=body)
        resp.raise_for_status()
        return resp.content

    async def compress(self, source: str, *, format: str | None = None, q: int | None = None, strip: bool | None = None, **kwargs) -> bytes:
        body = {"source": source}
        if format: body["format"] = format
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        body.update(kwargs)
        resp = await self._client.post("/v1/compress", json=body)
        resp.raise_for_status()
        return resp.content

    async def convert(self, source: str, format: str, *, q: int | None = None, strip: bool | None = None, lossless: bool | None = None, **kwargs) -> bytes:
        body = {"source": source, "format": format}
        if q is not None: body["q"] = q
        if strip is not None: body["strip"] = strip
        if lossless is not None: body["lossless"] = lossless
        body.update(kwargs)
        resp = await self._client.post("/v1/convert", json=body)
        resp.raise_for_status()
        return resp.content

    async def crop(self, source: str, x: int, y: int, width: int, height: int, *, format: str | None = None, **kwargs) -> bytes:
        body = {"source": source, "x": x, "y": y, "width": width, "height": height}
        if format: body["format"] = format
        body.update(kwargs)
        resp = await self._client.post("/v1/crop", json=body)
        resp.raise_for_status()
        return resp.content

    async def pipeline(self, source: str, operations: list[dict]) -> bytes:
        body = {"source": source, "operations": operations}
        resp = await self._client.post("/v1/pipeline", json=body)
        resp.raise_for_status()
        return resp.content
