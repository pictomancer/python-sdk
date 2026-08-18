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

## Sources

Every operation takes a `source`: an image URL, a base64 string, or a `data:` URI. For local files or in-memory bytes use the helpers:

```python
from pictomancer import Client, source_from_bytes, source_from_path

with Client() as client:
    out = client.compress(source_from_path("photo.jpg"), q=80)

    with open("photo.jpg", "rb") as f:
        out = client.compress(source_from_bytes(f.read()), q=80)
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

## Geometry ops: smart crop, trim, fill, autorot

`crop` has three mutually exclusive modes:

```python
with Client(api_key="your-api-key") as client:
    # Manual: exact rectangle.
    out = client.crop("https://example.com/image.jpg", 0, 0, 100, 100)

    # Smart: gravity picks the window. One of 'attention', 'entropy', 'centre'.
    out = client.crop("https://example.com/image.jpg", gravity="attention", width=200, height=200)

    # Trim: removes a uniform background border. threshold defaults to 10.0 server-side.
    out = client.crop("https://example.com/image.jpg", trim=True, threshold=5.0)
```

`resize` gains a fill mode: pass `width` + `height` (instead of `scale`/`scale_x`/`scale_y`) to
resize and smart-crop to exact dimensions in one call; `gravity` defaults to `attention`.

```python
out = client.resize("https://example.com/image.jpg", width=200, height=150, gravity="entropy")
```

All four ops (`resize`, `compress`, `convert`, `crop`) accept `autorot=True` to apply EXIF
orientation before processing.

When a crop actually trims, the response carries `X-Pictomancer-Trim-Left/-Top/-Width/-Height`
headers (inspect them with your own httpx client or event hooks).

## Enhance: denoise, auto-contrast, sharpen

All four ops (`resize`, `compress`, `convert`, `crop`) also accept `denoise`, `equalize` and
`sharpen`. Opt-in, base price - no surcharge.

```python
with Client(api_key="your-api-key") as client:
    out = client.convert("https://example.com/image.jpg", "webp", denoise=2, equalize=True)
    out = client.resize("https://example.com/image.jpg", scale=0.5, sharpen=True)
```

- `denoise` (int, 1-3) - median filter before the operation, window 3x3 to 7x7.
- `equalize` (bool) - auto-contrast, histogram equalisation of the value channel only; hue and
  saturation are preserved.
- `sharpen` (bool) - unsharp-mask sharpen after the operation (libvips defaults).

Applied in a fixed order: `autorot -> denoise -> equalize -> operation -> sharpen`. A `compress`
with any of these that comes out larger is still billed, unlike a plain compress with no gain.

## Quality target (SSIM)

Instead of guessing a `q` value, ask for the smallest file that still scores at
least a given SSIM. Pass `quality_target` (float, 0 < v <= 1) to `compress` or
`convert`; the server binary-searches the encoder quality for you.

```python
with Client(api_key="your-api-key") as client:
    out = client.compress("https://example.com/image.jpg", format="webp", quality_target=0.95)
    out = client.convert("https://example.com/image.jpg", "avif", quality_target=0.9)
```

Constraints (validated server-side, violations return 422):

- Mutually exclusive with `q`, and with `lossless=True` on `convert`.
- Only for `jpeg`, `webp` and `avif` outputs; `compress` requires an explicit `format`.
- Not supported inside `pipeline` operations.
- Carries a flat surcharge for the extra encodes.

The search outcome is reported in response headers (the SDK returns the body
only; inspect them with your own httpx client or event hooks if you need them):

- `X-Pictomancer-Quality-Target` - the target you asked for.
- `X-Pictomancer-Quality-Achieved` - SSIM of the returned encode, e.g. `0.9530`.
- `X-Pictomancer-Quality-Q-Final` - encoder quality the search settled on.
- `X-Pictomancer-Quality-Encodes` - encode cycles spent.

Headers are absent when no search ran. `X-Pig-Billed` is `0` when the input came
back untouched (already within target at its current size).

## AI-generated images: one call to web-ready

Image generators (gpt-image, DALL-E, Flux, Midjourney, Stable Diffusion) return 2-8 MB
PNGs. optimize_generated returns the same picture as web-ready webp (default), avif,
jpeg or png: metadata stripped, transparency kept, optional max_dimension cap (never
upscales), optional q or quality_target. Same price as convert; a result that is not
smaller is returned free.

```python
with Client(api_key="your-api-key") as client:
    out = client.optimize_generated("https://example.com/gen.png", format="avif", max_dimension=1600)
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
