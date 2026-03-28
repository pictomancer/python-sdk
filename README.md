<p align="center">
  <img src="https://pictomancer.ai/icon.svg" width="80" height="80" alt="Pictomancer.ai">
</p>

<h1 align="center">pictomancer</h1>

<p align="center">
  <strong>Image processing for AI agents.</strong><br>
  Resize, compress, convert, crop & pipeline — sub-50 ms, pay-per-request.
</p>

<p align="center">
  <a href="https://pypi.org/project/pictomancer/"><img src="https://img.shields.io/pypi/v/pictomancer?color=a855f7&style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/pictomancer/"><img src="https://img.shields.io/pypi/pyversions/pictomancer?style=flat-square" alt="Python"></a>
  <a href="https://api.pictomancer.ai/docs"><img src="https://img.shields.io/badge/docs-api-a855f7?style=flat-square" alt="API Docs"></a>
  <a href="https://x402.org"><img src="https://img.shields.io/badge/payments-x402_USDC-3b82f6?style=flat-square" alt="x402"></a>
</p>

---

Thin async Python client for [Pictomancer.ai](https://pictomancer.ai) — the
image processing API built for autonomous agents. No API keys, no accounts.
First 50 requests free, then micropayments via
[x402](https://x402.org) (USDC on Base L2).

## Install

```bash
pip install pictomancer
```

With [LangChain](https://python.langchain.com/) support:

```bash
pip install pictomancer[langchain]
```

## Quick start

```python
import asyncio
from pictomancer import Pictomancer

async def main():
    async with Pictomancer() as p:
        # Free — get image metadata
        info = await p.analyze("https://example.com/photo.jpg")
        print(f"{info.size_bytes:,} bytes")

        # Resize to 50%
        data = await p.resize("https://example.com/photo.jpg", scale=0.5)

        # Compress to q=70 WebP
        data = await p.compress("https://example.com/photo.jpg", q=70, format="webp")

        # Convert PNG → WebP
        data = await p.convert("https://example.com/photo.png", format="webp")

        # Crop a region
        data = await p.crop("https://example.com/photo.jpg",
                            x=0, y=0, width=800, height=600)

asyncio.run(main())
```

## Pipeline

Chain up to 10 operations in a single request:

```python
from pictomancer import Pictomancer, PipelineOp

async with Pictomancer() as p:
    data = await p.pipeline("https://example.com/photo.jpg", [
        PipelineOp(type="resize",   params={"scale": "0.5"}),
        PipelineOp(type="compress", params={"q": "70"}),
        PipelineOp(type="convert",  params={"format": "webp"}),
    ])
```

## Supported formats

Query at runtime with `await p.info()`, or see the full list:

| Format | Extensions | Key options |
|--------|-----------|-------------|
| JPEG | `.jpg` | `q` (1–100), `strip`, `interlace` |
| PNG | `.png` | `compression` (0–9), `palette`, `strip` |
| WebP | `.webp` | `q` (1–100), `lossless`, `strip` |
| TIFF | `.tiff` | `compression` (deflate, lzw, zstd…), `q` |
| GIF | `.gif` | `dither` (0–1), `effort`, `bitdepth` |

## LangChain

```python
from pictomancer.langchain import pictomancer_tools

tools = pictomancer_tools()

# 5 tools: analyze, resize, compress, convert, crop
# Pass to any LangChain agent, LangGraph tool node, or chain
```

Each tool includes pricing in its description so cost-aware agents can make
informed decisions.

## x402 payments

The first **50 requests per agent** are free. After that, agents pay
automatically via [x402](https://x402.org) — USDC on Base L2.

Pass a wallet address for identity tracking:

```python
async with Pictomancer(wallet="0xYourAgentWallet") as p:
    data = await p.resize("https://example.com/photo.jpg", scale=0.5)
```

## Pricing

| Operation | Base cost | What it does |
|-----------|-----------|--------------|
| `analyze` | Free | Image metadata (size in bytes) |
| `resize` | $0.001 | Scale by factor |
| `compress` | $0.001 | Re-encode with quality control |
| `convert` | $0.002 | Format conversion |
| `crop` | $0.001 | Extract rectangular region |
| `pipeline` | Per-op | Chain operations, volume discount at 3+ |

**Size multipliers:** &lt;1 MB → 1×, 1–5 MB → 1.5×, 5–10 MB → 2×, 10–50 MB → 3×.

## MCP

You can also connect directly to the hosted MCP server — no SDK needed:

```json
{
  "mcpServers": {
    "pictomancer": {
      "url": "https://api.pictomancer.ai/mcp"
    }
  }
}
```

Works with Claude Desktop, Cursor, Windsurf, and any MCP-compatible client.

## Links

- [API Documentation](https://api.pictomancer.ai/docs)
- [OpenAPI Spec](https://api.pictomancer.ai/openapi.json)
- [Website](https://pictomancer.ai)
- [MCP Registry](https://registry.modelcontextprotocol.io) — `ai.pictomancer/image-processing`

## License

MIT
