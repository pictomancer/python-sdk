"""Request/response models mirroring the Pictomancer.ai REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeResult(BaseModel):
    size_bytes: int = Field(description="File size of the fetched image in bytes.")


class ResizeParams(BaseModel):
    scale: float | None = Field(None, description="Uniform scale factor (e.g. 0.5 = half size).")
    scale_x: float | None = Field(None, description="Horizontal scale factor.")
    scale_y: float | None = Field(None, description="Vertical scale factor.")
    format: str | None = Field(None, description="Output format: jpeg, png, webp, tiff, gif.")


class CompressParams(BaseModel):
    q: int | None = Field(None, ge=1, le=100, description="Quality 1-100.")
    format: str | None = Field(None, description="Output format.")
    strip: bool | None = Field(None, description="Strip EXIF/ICC metadata.")


class ConvertParams(BaseModel):
    format: str = Field(description="Target format: jpeg, png, webp, tiff, gif.")
    q: int | None = Field(None, ge=1, le=100, description="Quality 1-100.")
    strip: bool | None = Field(None, description="Strip metadata.")
    lossless: bool | None = Field(None, description="Lossless encoding (webp only).")


class CropParams(BaseModel):
    x: int = Field(description="Left edge in pixels.")
    y: int = Field(description="Top edge in pixels.")
    width: int = Field(description="Width in pixels.")
    height: int = Field(description="Height in pixels.")
    format: str | None = Field(None, description="Output format.")


class PipelineOp(BaseModel):
    type: str = Field(description="Operation: resize, compress, convert, crop.")
    params: dict[str, str] = Field(default_factory=dict, description="Operation params as string k/v.")


class FormatOption(BaseModel):
    name: str
    kind: str
    description: str = ""
    default_str: str | None = None
    min: float | None = None
    max: float | None = None
    enum_values: list[str] | None = None


class FormatSpec(BaseModel):
    id: str = Field(description="Format identifier: jpeg, png, webp, tiff, gif.")
    suffix: str = Field(description="File extension including dot.")
    options: list[FormatOption] = Field(default_factory=list)
