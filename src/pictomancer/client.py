"""Async client for the Pictomancer.ai image processing API."""

from __future__ import annotations

from typing import Sequence

import httpx

from pictomancer.models import (
    AnalyzeResult,
    CompressParams,
    ConvertParams,
    CropParams,
    FormatSpec,
    PipelineOp,
    ResizeParams,
)

_DEFAULT_BASE = "https://api.pictomancer.ai"
_DEFAULT_TIMEOUT = 30.0


class PictomancerError(Exception):
    """Raised when the API returns a non-2xx status."""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status}: {detail}")


class Pictomancer:
    """Thin async client for api.pictomancer.ai.

    Usage::

        async with Pictomancer() as p:
            info = await p.analyze("https://example.com/photo.jpg")
            data = await p.resize("https://example.com/photo.jpg", scale=0.5)
    """

    def __init__(
        self,
        *,
        base_url: str = _DEFAULT_BASE,
        timeout: float = _DEFAULT_TIMEOUT,
        wallet: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        headers: dict[str, str] = {}
        if wallet:
            headers["X-Agent-Wallet"] = wallet
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
        )

    async def __aenter__(self) -> Pictomancer:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _raise(self, resp: httpx.Response) -> None:
        if resp.is_success:
            return
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise PictomancerError(resp.status_code, str(detail))

    async def info(self) -> list[FormatSpec]:
        """Return supported output formats and their options."""
        resp = await self._client.get("/v1/info")
        self._raise(resp)
        return [FormatSpec.model_validate(f) for f in resp.json()["formats"]]

    async def analyze(self, source: str) -> AnalyzeResult:
        resp = await self._client.post("/v1/analyze", json={"source": source})
        self._raise(resp)
        return AnalyzeResult.model_validate(resp.json())

    async def resize(
        self,
        source: str,
        *,
        scale: float | None = None,
        scale_x: float | None = None,
        scale_y: float | None = None,
        format: str | None = None,
    ) -> bytes:
        params = ResizeParams(scale=scale, scale_x=scale_x, scale_y=scale_y, format=format)
        body = {"source": source, **params.model_dump(exclude_none=True)}
        resp = await self._client.post("/v1/resize", json=body)
        self._raise(resp)
        return resp.content

    async def compress(
        self,
        source: str,
        *,
        q: int | None = None,
        format: str | None = None,
        strip: bool | None = None,
    ) -> bytes:
        params = CompressParams(q=q, format=format, strip=strip)
        body = {"source": source, **params.model_dump(exclude_none=True)}
        resp = await self._client.post("/v1/compress", json=body)
        self._raise(resp)
        return resp.content

    async def convert(
        self,
        source: str,
        *,
        format: str,
        q: int | None = None,
        strip: bool | None = None,
        lossless: bool | None = None,
    ) -> bytes:
        params = ConvertParams(format=format, q=q, strip=strip, lossless=lossless)
        body = {"source": source, **params.model_dump(exclude_none=True)}
        resp = await self._client.post("/v1/convert", json=body)
        self._raise(resp)
        return resp.content

    async def crop(
        self,
        source: str,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
        format: str | None = None,
    ) -> bytes:
        params = CropParams(x=x, y=y, width=width, height=height, format=format)
        body = {"source": source, **params.model_dump(exclude_none=True)}
        resp = await self._client.post("/v1/crop", json=body)
        self._raise(resp)
        return resp.content

    async def pipeline(
        self,
        source: str,
        operations: Sequence[PipelineOp],
    ) -> bytes:
        body = {
            "source": source,
            "operations": [op.model_dump() for op in operations],
        }
        resp = await self._client.post("/v1/pipeline", json=body)
        self._raise(resp)
        return resp.content
