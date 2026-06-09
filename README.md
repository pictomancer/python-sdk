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

## Delivery: write the result somewhere else

By default an operation returns the optimized `bytes`. Pass a `delivery` target to
have Pictomancer write the result directly to your storage or endpoint instead —
the operation then returns a `dict` (etag, sha256, bytes written, ...). No cloud
credentials ever reach Pictomancer.

```python
from pictomancer import Client, PutUrl, Callback

with Client(api_key="your-api-key") as client:
    # Upload to a customer-signed presigned PUT URL (S3/R2/GCS/Azure).
    res = client.resize(
        "https://example.com/image.jpg",
        scale=0.5,
        delivery=PutUrl("https://bucket.s3.amazonaws.com/key?X-Amz-Signature=..."),
    )
    print(res["sha256"], res["bytes_written"])

    # Or POST the bytes to your own callback endpoint (async/large jobs).
    res = client.compress(
        "https://example.com/image.jpg",
        delivery=Callback("https://hooks.example.com/pig?token=secret"),
    )
    print(res["status"], res["sha256"])
```

`PutUrl` and `Callback` accept optional `headers=` (whitelisted storage headers,
e.g. `Content-Type`, `Cache-Control`, `x-amz-*`). The returned `sha256` is the
digest of exactly the bytes delivered, so you can verify the stored object.

### Authenticating a callback

Pass `secret=` to `Callback` to have the POST body signed. We send
`X-Pig-Signature: sha256=<hex>` (HMAC-SHA256 of the body, GitHub-webhook style).
The secret is used per request and never stored. Verify it on your endpoint:

```python
res = client.resize(
    "https://example.com/image.jpg",
    scale=0.5,
    delivery=Callback("https://hooks.example.com/pig", secret="shared-secret"),
)

# On your endpoint (any framework), recompute and constant-time compare:
import hashlib, hmac
expected = "sha256=" + hmac.new(b"shared-secret", request_body, hashlib.sha256).hexdigest()
assert hmac.compare_digest(expected, request.headers["X-Pig-Signature"])
```

Errors use httpx behavior: non-2xx responses raise `httpx.HTTPStatusError` after `raise_for_status()`.

## API documentation

Interactive docs: [https://api.pictomancer.ai/docs](https://api.pictomancer.ai/docs)

OpenAPI: [https://api.pictomancer.ai/openapi.json](https://api.pictomancer.ai/openapi.json)
