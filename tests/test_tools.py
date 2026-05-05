"""Tests for pypi-mcp tools."""

import pytest
from pypi_mcp.tools.discovery import check_package_exists, get_package_info_tool, search_packages
from pypi_mcp.tools.versions import compare_versions, get_latest_version


@pytest.mark.asyncio
async def test_get_package_info(respx_mock, sample_package_info):
    """Test get_package_info tool."""
    respx_mock.get("https://pypi.org/pypi/requests/json").mock(
        return_value=__import__("httpx").Response(200, json=sample_package_info)
    )
    result = await get_package_info_tool("requests")
    assert "package" in result
    assert result["package"]["name"] == "requests"


@pytest.mark.asyncio
async def test_check_package_exists_not_found(respx_mock):
    """Test check_package_exists for non-existent package."""
    respx_mock.get("https://pypi.org/pypi/nonexistent-package/json").mock(
        return_value=__import__("httpx").Response(404)
    )
    result = await check_package_exists("nonexistent-package")
    assert result["exists"] is False


@pytest.mark.asyncio
async def test_compare_versions():
    """Test version comparison."""
    result = await compare_versions("requests", "2.30.0", "2.31.0")
    assert result["newer"] == "2.31.0"
    assert result["older"] == "2.30.0"

    result = await compare_versions("requests", "2.31.0", "2.31.0")
    assert result["is_equal"] is True


@pytest.mark.asyncio
async def test_search_packages(respx_mock):
    """Test search packages."""
    respx_mock.get("https://pypi.org/simple/").mock(
        return_value=__import__("httpx").Response(
            200, text='<a href="/simple/requests/">requests</a>'
        )
    )
    result = await search_packages("requests", limit=5)
    assert "results" in result
