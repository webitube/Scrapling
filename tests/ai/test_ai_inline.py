# -*- coding: utf-8 -*-
"""Tests for return_inline and write_raw_file functionality in MCP server (ai.py)"""

import os
import tempfile
import pytest
import pytest_httpbin
from unittest.mock import AsyncMock, patch, MagicMock

from scrapling.core.ai import (
    ScraplingMCPServer,
    ResponseModel,
    _translate_response,
    INLINE_MAX_SIZE,
)
from scrapling.core.shell import Convertor


class TestTranslateResponseInline:
    """Test _translate_response with return_inline parameter"""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page response"""
        mock = MagicMock()
        mock.status = 200
        mock.url = "http://example.com"
        return mock

    def test_translate_response_default_small_content(self, mock_page):
        """Test default behavior with small content returns inline"""
        with patch.object(Convertor, '_extract_content') as mock_extract:
            mock_extract.return_value = iter(["# Hello World", ""])
            result = _translate_response(
                mock_page,
                extraction_type="markdown",
                css_selector=None,
                main_content_only=True,
                return_inline=False,
                write_raw_file=False,
            )
            assert isinstance(result, ResponseModel)
            assert result.status == 200
            assert result.url == "http://example.com"

    def test_translate_response_default_large_content_fallback(self, mock_page):
        """Test default behavior with large content falls back to file"""
        large_content = "# Large Content\n" + "x" * (INLINE_MAX_SIZE + 1000)
        with patch.object(Convertor, '_extract_content') as mock_extract:
            mock_extract.return_value = iter([large_content, ""])
            result = _translate_response(
                mock_page,
                extraction_type="markdown",
                css_selector=None,
                main_content_only=True,
                return_inline=False,
                write_raw_file=False,
            )
            assert isinstance(result, ResponseModel)
            assert "exceeds inline size limit" in result.content[0].lower()
            assert "written to:" in result.content[0].lower()

    def test_translate_response_return_inline_small_content(self, mock_page):
        """Test return_inline returns content directly regardless of size"""
        small_content = "# Small Content\nThis is small content."
        with patch.object(Convertor, '_extract_content') as mock_extract:
            mock_extract.return_value = iter([small_content, ""])
            result = _translate_response(
                mock_page,
                extraction_type="markdown",
                css_selector=None,
                main_content_only=True,
                return_inline=True,
                write_raw_file=False,
            )
            assert isinstance(result, ResponseModel)
            assert len(result.content) == 1
            assert small_content in result.content[0]

    def test_translate_response_return_inline_large_content_no_fallback(self, mock_page):
        """Test return_inline returns content directly even when it exceeds INLINE_MAX_SIZE"""
        large_content = "# Large Content\n" + "x" * (INLINE_MAX_SIZE + 1000)
        with patch.object(Convertor, '_extract_content') as mock_extract:
            mock_extract.return_value = iter([large_content, ""])
            result = _translate_response(
                mock_page,
                extraction_type="markdown",
                css_selector=None,
                main_content_only=True,
                return_inline=True,
                write_raw_file=False,
            )
            assert isinstance(result, ResponseModel)
            assert len(result.content) == 1
            assert large_content in result.content[0]
            # No fallback to file — return_inline always returns inline

    def test_translate_response_write_raw_file(self, mock_page):
        """Test write_raw_file creates a file"""
        with patch.object(Convertor, '_extract_content') as mock_extract:
            mock_extract.return_value = iter(["# Content for file", ""])
            result = _translate_response(
                mock_page,
                extraction_type="markdown",
                css_selector=None,
                main_content_only=True,
                return_inline=False,
                write_raw_file=True,
            )
            assert isinstance(result, ResponseModel)
            assert "written to:" in result.content[0].lower()

    def test_translate_response_both_flags_return_inline_precedence(self, mock_page):
        """Test that return_inline takes precedence when both flags are True"""
        small_content = "# Content with precedence test"
        with patch.object(Convertor, '_extract_content') as mock_extract:
            mock_extract.return_value = iter([small_content, ""])
            result = _translate_response(
                mock_page,
                extraction_type="markdown",
                css_selector=None,
                main_content_only=True,
                return_inline=True,
                write_raw_file=True,
            )
            assert isinstance(result, ResponseModel)
            # Should contain the precedence note
            assert "precedence" in result.content[0].lower()


class TestMCPServerMethodSignatures:
    """Test that MCP server methods accept the new parameters"""

    @pytest.fixture
    def server(self):
        return ScraplingMCPServer()

    def test_get_method_has_return_inline_param(self, server):
        """Test that get method accepts return_inline parameter"""
        import inspect
        sig = inspect.signature(server.get)
        params = list(sig.parameters.keys())
        assert "return_inline" in params
        assert "write_raw_file" in params

    def test_bulk_get_method_has_return_inline_param(self, server):
        """Test that bulk_get method accepts return_inline parameter"""
        import inspect
        sig = inspect.signature(server.bulk_get)
        params = list(sig.parameters.keys())
        assert "return_inline" in params
        assert "write_raw_file" in params

    def test_fetch_method_has_return_inline_param(self, server):
        """Test that fetch method accepts return_inline parameter"""
        import inspect
        sig = inspect.signature(server.fetch)
        params = list(sig.parameters.keys())
        assert "return_inline" in params
        assert "write_raw_file" in params

    def test_bulk_fetch_method_has_return_inline_param(self, server):
        """Test that bulk_fetch method accepts return_inline parameter"""
        import inspect
        sig = inspect.signature(server.bulk_fetch)
        params = list(sig.parameters.keys())
        assert "return_inline" in params
        assert "write_raw_file" in params

    def test_stealthy_fetch_method_has_return_inline_param(self, server):
        """Test that stealthy_fetch method accepts return_inline parameter"""
        import inspect
        sig = inspect.signature(server.stealthy_fetch)
        params = list(sig.parameters.keys())
        assert "return_inline" in params
        assert "write_raw_file" in params

    def test_bulk_stealthy_fetch_method_has_return_inline_param(self, server):
        """Test that bulk_stealthy_fetch method accepts return_inline parameter"""
        import inspect
        sig = inspect.signature(server.bulk_stealthy_fetch)
        params = list(sig.parameters.keys())
        assert "return_inline" in params
        assert "write_raw_file" in params

    def test_default_values_are_false(self, server):
        """Test that default values for new parameters are False"""
        import inspect
        for method_name in ["get", "bulk_get", "fetch", "bulk_fetch", "stealthy_fetch", "bulk_stealthy_fetch"]:
            method = getattr(server, method_name)
            sig = inspect.signature(method)
            assert sig.parameters["return_inline"].default is False
            assert sig.parameters["write_raw_file"].default is False


class TestShellSignatures:
    """Test that _shell_signatures.py includes the new parameters"""

    def test_request_params_has_new_params(self):
        """Test that _REQUESTS_PARAMS includes return_inline and write_raw_file"""
        from scrapling.core._shell_signatures import _REQUESTS_PARAMS
        assert "return_inline" in _REQUESTS_PARAMS
        assert "write_raw_file" in _REQUESTS_PARAMS

    def test_fetch_params_has_new_params(self):
        """Test that _FETCH_PARAMS includes return_inline and write_raw_file"""
        from scrapling.core._shell_signatures import _FETCH_PARAMS
        assert "return_inline" in _FETCH_PARAMS
        assert "write_raw_file" in _FETCH_PARAMS

    def test_stealthy_fetch_params_has_new_params(self):
        """Test that _STEALTHY_FETCH_PARAMS includes return_inline and write_raw_file"""
        from scrapling.core._shell_signatures import _STEALTHY_FETCH_PARAMS
        assert "return_inline" in _STEALTHY_FETCH_PARAMS
        assert "write_raw_file" in _STEALTHY_FETCH_PARAMS


class TestBulkToolsReturnInline:
    """Test bulk tools return raw string when return_inline=True"""

    @pytest.fixture
    def server(self):
        return ScraplingMCPServer()

    @pytest.fixture
    def mock_page(self):
        """Create a mock page response"""
        mock = MagicMock()
        mock.status = 200
        mock.url = "http://example.com"
        return mock

    def _make_async_context_manager(self, mock_obj):
        """Helper to create a proper async context manager mock"""
        mock_obj.__aenter__ = AsyncMock(return_value=mock_obj)
        mock_obj.__aexit__ = AsyncMock(return_value=False)
        return mock_obj

    @pytest.mark.asyncio
    async def test_bulk_get_return_inline_returns_string(self, server, mock_page):
        """Test bulk_get with return_inline=True returns a raw string, not List[ResponseModel]"""
        with patch('scrapling.core.ai.FetcherSession') as mock_session_cls:
            mock_session = self._make_async_context_manager(MagicMock())
            mock_session.get = AsyncMock(return_value=mock_page)
            mock_session_cls.return_value = mock_session

            with patch.object(Convertor, '_extract_content') as mock_extract:
                mock_extract.return_value = iter(["# Page 1", ""])
                result = await server.bulk_get(
                    urls=["http://example.com"],
                    return_inline=True,
                )
                assert isinstance(result, str)
                assert "# Page 1" in result

    @pytest.mark.asyncio
    async def test_bulk_get_return_inline_false_returns_list(self, server, mock_page):
        """Test bulk_get with return_inline=False returns List[ResponseModel]"""
        with patch('scrapling.core.ai.FetcherSession') as mock_session_cls:
            mock_session = self._make_async_context_manager(MagicMock())
            mock_session.get = AsyncMock(return_value=mock_page)
            mock_session_cls.return_value = mock_session

            with patch.object(Convertor, '_extract_content') as mock_extract:
                mock_extract.return_value = iter(["# Content", ""])
                results = await server.bulk_get(
                    urls=["http://example.com"],
                    return_inline=False,
                )
                assert isinstance(results, list)
                assert all(isinstance(r, ResponseModel) for r in results)

    @pytest.mark.asyncio
    async def test_bulk_get_return_inline_ignores_inline_max_size(self, server, mock_page):
        """Test bulk_get with return_inline=True bypasses INLINE_MAX_SIZE limit"""
        with patch('scrapling.core.ai.FetcherSession') as mock_session_cls:
            mock_session = self._make_async_context_manager(MagicMock())
            mock_session.get = AsyncMock(return_value=mock_page)
            mock_session_cls.return_value = mock_session

            large_content = "# Large\n" + "x" * (INLINE_MAX_SIZE + 5000)
            with patch.object(Convertor, '_extract_content') as mock_extract:
                mock_extract.return_value = iter([large_content, ""])
                result = await server.bulk_get(
                    urls=["http://example.com"],
                    return_inline=True,
                )
                # Should return string with full content, not fallback to file
                assert isinstance(result, str)
                assert large_content in result

    @pytest.mark.asyncio
    async def test_bulk_fetch_return_inline_returns_string(self, server, mock_page):
        """Test bulk_fetch with return_inline=True returns a raw string"""
        with patch('scrapling.core.ai.AsyncDynamicSession') as mock_session_cls:
            mock_session = self._make_async_context_manager(MagicMock())
            mock_session.fetch = AsyncMock(return_value=mock_page)
            mock_session_cls.return_value = mock_session

            with patch.object(Convertor, '_extract_content') as mock_extract:
                mock_extract.return_value = iter(["# Fetched Content", ""])
                result = await server.bulk_fetch(
                    urls=["http://example.com"],
                    return_inline=True,
                )
                assert isinstance(result, str)
                assert "# Fetched Content" in result

    @pytest.mark.asyncio
    async def test_bulk_stealthy_fetch_return_inline_returns_string(self, server, mock_page):
        """Test bulk_stealthy_fetch with return_inline=True returns a raw string"""
        with patch('scrapling.core.ai.AsyncStealthySession') as mock_session_cls:
            mock_session = self._make_async_context_manager(MagicMock())
            mock_session.fetch = AsyncMock(return_value=mock_page)
            mock_session_cls.return_value = mock_session

            with patch.object(Convertor, '_extract_content') as mock_extract:
                mock_extract.return_value = iter(["# Stealthy Content", ""])
                result = await server.bulk_stealthy_fetch(
                    urls=["http://example.com"],
                    return_inline=True,
                )
                assert isinstance(result, str)
                assert "# Stealthy Content" in result

    @pytest.mark.asyncio
    async def test_bulk_get_multiple_urls_joined_with_newline(self, server, mock_page):
        """Test bulk_get with multiple URLs joins content with newlines"""
        with patch('scrapling.core.ai.FetcherSession') as mock_session_cls:
            mock_session = self._make_async_context_manager(MagicMock())

            mock_page1 = MagicMock()
            mock_page1.status = 200
            mock_page1.url = "http://example.com"

            mock_page2 = MagicMock()
            mock_page2.status = 200
            mock_page2.url = "http://example.org"

            async def mock_get(*args, **kwargs):
                url = args[0]
                if "example.com" in url:
                    return mock_page1
                return mock_page2

            mock_session.get = mock_get
            mock_session_cls.return_value = mock_session

            with patch('scrapling.core.ai._get_raw_content') as mock_get_raw:
                def get_raw_side_effect(page, *args, **kwargs):
                    if page.url == "http://example.com":
                        return "# First Page"
                    return "# Second Page"

                mock_get_raw.side_effect = get_raw_side_effect
                result = await server.bulk_get(
                    urls=["http://example.com", "http://example.org"],
                    return_inline=True,
                )
                assert isinstance(result, str)
                assert "# First Page" in result
                assert "# Second Page" in result
                assert "\n" in result
