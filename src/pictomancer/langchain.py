"""LangChain tool wrappers for Pictomancer.ai.

Install with ``pip install pictomancer[langchain]``.

Usage::

    from pictomancer.langchain import pictomancer_tools

    tools = pictomancer_tools()
    # pass *tools* to your LangChain agent / tool node
"""

from __future__ import annotations

import base64

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from pictomancer.client import Pictomancer


class _AnalyzeInput(BaseModel):
    source: str = Field(description="Public image URL or base64 data URI.")


class _ResizeInput(BaseModel):
    source: str = Field(description="Public image URL or base64 data URI.")
    scale: float = Field(description="Uniform scale factor (e.g. 0.5 = half size).")
    format: str = Field("png", description="Output format: jpeg, png, webp.")


class _CompressInput(BaseModel):
    source: str = Field(description="Public image URL or base64 data URI.")
    q: int = Field(75, ge=1, le=100, description="Quality 1-100.")
    format: str = Field("jpeg", description="Output format.")


class _ConvertInput(BaseModel):
    source: str = Field(description="Public image URL or base64 data URI.")
    format: str = Field(description="Target format: jpeg, png, webp, tiff, gif.")
    q: int | None = Field(None, ge=1, le=100, description="Quality 1-100.")


class _CropInput(BaseModel):
    source: str = Field(description="Public image URL or base64 data URI.")
    x: int = Field(description="Left edge in pixels.")
    y: int = Field(description="Top edge in pixels.")
    width: int = Field(description="Width in pixels.")
    height: int = Field(description="Height in pixels.")
    format: str = Field("png", description="Output format.")


def _b64_uri(data: bytes, fmt: str) -> str:
    return f"data:image/{fmt};base64,{base64.b64encode(data).decode()}"


def pictomancer_tools(
    *,
    base_url: str = "https://api.pictomancer.ai",
    wallet: str | None = None,
) -> list[StructuredTool]:
    """Return a list of LangChain tools backed by the Pictomancer.ai API."""

    async def _analyze(source: str) -> dict:
        async with Pictomancer(base_url=base_url, wallet=wallet) as p:
            result = await p.analyze(source)
        return result.model_dump()

    async def _resize(source: str, scale: float, format: str = "png") -> str:
        async with Pictomancer(base_url=base_url, wallet=wallet) as p:
            data = await p.resize(source, scale=scale, format=format)
        return _b64_uri(data, format)

    async def _compress(source: str, q: int = 75, format: str = "jpeg") -> str:
        async with Pictomancer(base_url=base_url, wallet=wallet) as p:
            data = await p.compress(source, q=q, format=format)
        return _b64_uri(data, format)

    async def _convert(source: str, format: str, q: int | None = None) -> str:
        async with Pictomancer(base_url=base_url, wallet=wallet) as p:
            data = await p.convert(source, format=format, q=q)
        return _b64_uri(data, format)

    async def _crop(
        source: str, x: int, y: int, width: int, height: int, format: str = "png",
    ) -> str:
        async with Pictomancer(base_url=base_url, wallet=wallet) as p:
            data = await p.crop(source, x=x, y=y, width=width, height=height, format=format)
        return _b64_uri(data, format)

    return [
        StructuredTool.from_function(
            coroutine=_analyze,
            name="pictomancer_analyze",
            description="Get image file size in bytes. Free, no payment required.",
            args_schema=_AnalyzeInput,
        ),
        StructuredTool.from_function(
            coroutine=_resize,
            name="pictomancer_resize",
            description="Resize an image by a scale factor. Returns base64 data URI. Costs $0.001/request.",
            args_schema=_ResizeInput,
        ),
        StructuredTool.from_function(
            coroutine=_compress,
            name="pictomancer_compress",
            description="Compress an image with quality control. Returns base64 data URI. Costs $0.001/request.",
            args_schema=_CompressInput,
        ),
        StructuredTool.from_function(
            coroutine=_convert,
            name="pictomancer_convert",
            description="Convert image format (jpeg/png/webp/tiff/gif). Returns base64 data URI. Costs $0.002/request.",
            args_schema=_ConvertInput,
        ),
        StructuredTool.from_function(
            coroutine=_crop,
            name="pictomancer_crop",
            description="Crop a rectangular region from an image. Returns base64 data URI. Costs $0.001/request.",
            args_schema=_CropInput,
        ),
    ]
