# -*- coding: utf-8 -*-
"""Tests for return_inline and write_raw_file functionality in shell.py and ai.py"""

import os
import tempfile
import pytest

from scrapling.core.shell import Convertor, INLINE_MAX_SIZE
from scrapling.parser import Selector


class TestInlineMaxSize:
    """Test INLINE_MAX_SIZE constant"""

    def test_inline_max_size_value(self):
        """Test that INLINE_MAX_SIZE is set to 10KB"""
        assert INLINE_MAX_SIZE == 10240

    def test_inline_max_size_is_positive(self):
        """Test that INLINE_MAX_SIZE is a positive integer"""
        assert isinstance(INLINE_MAX_SIZE, int)
        assert INLINE_MAX_SIZE > 0


class TestExtractContentWithInline:
    """Test _extract_content with return_inline and write_raw_file parameters"""

    @pytest.fixture
    def sample_selector(self):
        """Create a simple Selector for testing"""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <p>This is a test paragraph.</p>
        </body>
        </html>
        """
        return Selector(html, url="http://example.com")

    def test_extract_content_default_behavior(self, sample_selector):
        """Test that default behavior (return_inline=False) works unchanged"""
        results = list(
            Convertor._extract_content(
                sample_selector,
                extraction_type="markdown",
                return_inline=False,
                write_raw_file=False,
            )
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_extract_content_with_return_inline_true(self, sample_selector):
        """Test that return_inline=True passes through without error"""
        results = list(
            Convertor._extract_content(
                sample_selector,
                extraction_type="markdown",
                return_inline=True,
                write_raw_file=False,
            )
        )
        assert isinstance(results, list)
        # The actual inline logic is in _translate_response, _extract_content just passes through

    def test_extract_content_with_write_raw_file_true(self, sample_selector):
        """Test that write_raw_file=True passes through without error"""
        results = list(
            Convertor._extract_content(
                sample_selector,
                extraction_type="html",
                return_inline=False,
                write_raw_file=True,
            )
        )
        assert isinstance(results, list)

    def test_extract_content_both_flags_true(self, sample_selector):
        """Test that both flags can be True (return_inline takes precedence in _translate_response)"""
        results = list(
            Convertor._extract_content(
                sample_selector,
                extraction_type="text",
                return_inline=True,
                write_raw_file=True,
            )
        )
        assert isinstance(results, list)

    def test_extract_content_html_extraction(self, sample_selector):
        """Test HTML extraction type"""
        results = list(
            Convertor._extract_content(
                sample_selector,
                extraction_type="html",
                return_inline=False,
                write_raw_file=False,
            )
        )
        assert "Hello World" in results[0]

    def test_extract_content_text_extraction(self, sample_selector):
        """Test text extraction type"""
        results = list(
            Convertor._extract_content(
                sample_selector,
                extraction_type="text",
                return_inline=False,
                write_raw_file=False,
            )
        )
        assert "Hello World" in results[0]


class TestWriteContentToFile:
    """Test write_content_to_file with write_raw_file parameter"""

    @pytest.fixture
    def sample_selector(self):
        """Create a simple Selector for testing"""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <p>This is a test paragraph.</p>
        </body>
        </html>
        """
        return Selector(html, url="http://example.com")

    def test_write_content_to_file_markdown(self, sample_selector):
        """Test writing content to a .md file"""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            filepath = f.name
        try:
            Convertor.write_content_to_file(
                sample_selector,
                filepath,
                write_raw_file=False,
            )
            assert os.path.exists(filepath)
            with open(filepath, "r") as f:
                content = f.read()
            assert "Hello World" in content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_write_content_to_file_html(self, sample_selector):
        """Test writing content to a .html file"""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            filepath = f.name
        try:
            Convertor.write_content_to_file(
                sample_selector,
                filepath,
                write_raw_file=False,
            )
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_write_content_to_file_txt(self, sample_selector):
        """Test writing content to a .txt file"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            filepath = f.name
        try:
            Convertor.write_content_to_file(
                sample_selector,
                filepath,
                write_raw_file=False,
            )
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_write_content_to_file_invalid_extension(self, sample_selector):
        """Test that invalid file extension raises ValueError"""
        with pytest.raises(ValueError, match="Unknown file type"):
            Convertor.write_content_to_file(
                sample_selector,
                "test.pdf",
                write_raw_file=False,
            )

    def test_write_content_to_file_with_write_raw_file_true(self, sample_selector):
        """Test that write_raw_file=True works without error"""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            filepath = f.name
        try:
            Convertor.write_content_to_file(
                sample_selector,
                filepath,
                write_raw_file=True,
            )
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
