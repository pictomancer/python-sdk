# pictomancer

Python SDK for [Pictomancer.ai](https://pictomancer.ai) — a thin [httpx](https://www.python-httpx.org/) wrapper around the REST API at `https://api.pictomancer.ai`.

## Install

```bash
pip install .
```

From PyPI (when published):

```bash
pip install pictomancer
```

## Configuration

- **`api_key`** — optional Bearer token (`Authorization: Bearer …`).
- **`base_url`** — defaults to `https://api.pictomancer.ai`.
- **`timeout`** — request timeout in seconds (default `30.0`).

JSON helpers return `dict`; image operations return `bytes` (response body).

## Synchronous client

```python
from pictomancer import Client

with Client(api_key="your-api-key") as client:
    info = client.info()
    usage = client.usage()

    meta = client.analyze("https://example.com/image.jpg")

    out = client.resize("https://example.com/image.jpg", scale=0.5, format="webp")
    out = client.compress("https://example.com/image.jpg", q=85, format="jpeg")
    out = client.convert("https://example.com/image.jpg", "png", q=90)
    out = client.crop("https://example.com/image.jpg", 0, 0, 100, 100, format="webp")
    out = client.pipeline(
        "https://example.com/image.jpg",
        [
            {"type": "resize", "params": {"scale": "0.5"}},
            {"type": "convert", "params": {"format": "webp"}},
        ],
    )

    with open("out.webp", "wb") as f:
        f.write(out)
```

## Async client

```python
import asyncio
from pictomancer import AsyncClient


async def main():
    async with AsyncClient(api_key="your-api-key") as client:
        info = await client.info()
        usage = await client.usage()
        meta = await client.analyze("https://example.com/image.jpg")
        out = await client.resize("https://example.com/image.jpg", scale=0.5, format="webp")
        return info, usage, meta, out


asyncio.run(main())
```

Errors use httpx behavior: non-2xx responses raise `httpx.HTTPStatusError` after `raise_for_status()`.

## API documentation

Interactive docs: [https://api.pictomancer.ai/docs](https://api.pictomancer.ai/docs)

OpenAPI: [https://api.pictomancer.ai/openapi.json](https://api.pictomancer.ai/openapi.json)
