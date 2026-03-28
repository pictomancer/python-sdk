"""Unit tests for the LangChain tool adapter."""

import json

import pytest
import respx

BASE = "https://api.pictomancer.ai"
SOURCE = "https://example.com/img.jpg"


@pytest.fixture
def tools():
    from pictomancer.langchain import pictomancer_tools
    return pictomancer_tools(base_url=BASE)


def _tool_by_name(tools: list, name: str):
    return next(t for t in tools if t.name == name)


class TestToolDiscovery:
    def test_returns_five_tools(self, tools):
        assert len(tools) == 5

    def test_tool_names(self, tools):
        names = {t.name for t in tools}
        assert names == {
            "pictomancer_analyze",
            "pictomancer_resize",
            "pictomancer_compress",
            "pictomancer_convert",
            "pictomancer_crop",
        }

    def test_all_tools_have_descriptions(self, tools):
        assert all(t.description for t in tools)


class TestAnalyzeTool:
    @respx.mock
    async def test_returns_dict_with_size(self, tools):
        respx.post(f"{BASE}/v1/analyze").respond(json={"size_bytes": 5000})
        tool = _tool_by_name(tools, "pictomancer_analyze")

        result = await tool.ainvoke({"source": SOURCE})

        assert result == {"size_bytes": 5000}


class TestResizeTool:
    @respx.mock
    async def test_returns_base64_data_uri(self, tools):
        respx.post(f"{BASE}/v1/resize").respond(content=b"\x89PNG")
        tool = _tool_by_name(tools, "pictomancer_resize")

        result = await tool.ainvoke({"source": SOURCE, "scale": 0.5, "format": "png"})

        assert result.startswith("data:image/png;base64,")

    @respx.mock
    async def test_sends_scale_to_api(self, tools):
        route = respx.post(f"{BASE}/v1/resize").respond(content=b"x")
        tool = _tool_by_name(tools, "pictomancer_resize")

        await tool.ainvoke({"source": SOURCE, "scale": 0.25, "format": "png"})

        payload = json.loads(route.calls[0].request.content)
        assert payload["scale"] == 0.25


class TestCompressTool:
    @respx.mock
    async def test_returns_base64_data_uri(self, tools):
        respx.post(f"{BASE}/v1/compress").respond(content=b"\xff\xd8")
        tool = _tool_by_name(tools, "pictomancer_compress")

        result = await tool.ainvoke({"source": SOURCE, "q": 60, "format": "jpeg"})

        assert result.startswith("data:image/jpeg;base64,")

    @respx.mock
    async def test_sends_quality_to_api(self, tools):
        route = respx.post(f"{BASE}/v1/compress").respond(content=b"x")
        tool = _tool_by_name(tools, "pictomancer_compress")

        await tool.ainvoke({"source": SOURCE, "q": 42, "format": "jpeg"})

        assert json.loads(route.calls[0].request.content)["q"] == 42


class TestConvertTool:
    @respx.mock
    async def test_returns_data_uri_with_target_format(self, tools):
        respx.post(f"{BASE}/v1/convert").respond(content=b"RIFF")
        tool = _tool_by_name(tools, "pictomancer_convert")

        result = await tool.ainvoke({"source": SOURCE, "format": "webp"})

        assert result.startswith("data:image/webp;base64,")


class TestCropTool:
    @respx.mock
    async def test_returns_base64_data_uri(self, tools):
        respx.post(f"{BASE}/v1/crop").respond(content=b"\x89PNG")
        tool = _tool_by_name(tools, "pictomancer_crop")

        result = await tool.ainvoke({
            "source": SOURCE, "x": 0, "y": 0, "width": 50, "height": 50, "format": "png",
        })

        assert result.startswith("data:image/png;base64,")

    @respx.mock
    async def test_sends_crop_rect_to_api(self, tools):
        route = respx.post(f"{BASE}/v1/crop").respond(content=b"x")
        tool = _tool_by_name(tools, "pictomancer_crop")

        await tool.ainvoke({
            "source": SOURCE, "x": 10, "y": 20, "width": 100, "height": 200, "format": "png",
        })

        payload = json.loads(route.calls[0].request.content)
        assert payload["x"] == 10
        assert payload["width"] == 100
