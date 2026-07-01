# Feature: Inline Content Output for Large Scraping Responses

## Overview
Add `returnInline` and `writeRawFile` parameters to scraping tools (`mcp_scrapling_get`, `mcp_scrapling_fetch`, `mcp_scrapling_stealthy_fetch`, and their bulk variants) so that:
1. **`returnInline: true`** returns extracted content directly in the tool response instead of writing to a JSON file.
2. **`writeRawFile: true`** writes extracted content as a plain text/markdown/HTML file (matching the extraction type) instead of a JSON wrapper, eliminating the need for intermediate JSON parsing.

Both parameters are opt-in with safe defaults (`false`) to ensure zero breaking changes.

## Project Context
- **Architecture:** Python package (`scrapling/`) with MCP server integration via `core/ai.py`. Content extraction flows through `core/shell.py` (`_extract_content` -> `_save_content_to_file`). Bulk operations use `asyncio.gather` in `core/ai.py`.
- **Test Framework:** `pytest` (configured in `pytest.ini` with `asyncio_mode = auto`). Tests use `pytest-asyncio` for async fixtures and tests. Conventions include `@pytest.fixture`, `@pytest.mark.asyncio`, and direct assertion style.
- **Relevant Existing Code:**
  - `scrapling/core/shell.py` — `_extract_content()` and `_save_content_to_file()` (lines 1008–1130)
  - `scrapling/core/ai.py` — MCP tool registration, `fetch_url()`, `fetch_urls()`, `stealthy_fetch_url()`, `stealthy_fetch_urls()`, `get_url()`, `get_urls()`
  - `tests/core/test_shell.py` — Existing tests for `_extract_content` and `_save_content_to_file`
  - `tests/ai/test_ai_mcp.py` — Existing MCP server tests

## Phase 1: Core Logic — Inline Return & Raw File Writing

### Description
Extend `_extract_content` in `core/shell.py` to accept `return_inline` and `write_raw_file` flags, and modify the content saving logic to support both modes.

### Affected Files
- `scrapling/core/shell.py` — Modify `_extract_content()` and `_save_content_to_file()`
- `scrapling/core/_shell_signatures.py` — Update shell signature to include new parameters

### TODO
- [ ] Add `return_inline: bool = False` and `write_raw_file: bool = False` parameters to `_extract_content()` method signature
- [ ] Modify `_save_content_to_file()` to accept a `write_raw_file: bool = False` parameter
- [ ] When `write_raw_file=True`, determine file extension from `extraction_type` (`.md` for markdown, `.txt` for text, `.html` for html) and write raw content directly without JSON wrapper
- [ ] When `return_inline=True`, skip file writing entirely and return the extracted content string directly in the response dictionary
- [ ] Add a size threshold constant (e.g., `INLINE_MAX_SIZE = 10240` bytes) — when `return_inline=True` but content exceeds threshold, auto-fallback to file output with a warning message
- [ ] Update the return value structure of `_extract_content()` to include a `content` key with the raw string when `return_inline=True`
- [ ] Preserve all existing behavior when both flags are `False` (default) — JSON file + schema file written as before
- [ ] Update `_shell_signatures.py` to reflect the new parameters in the shell signature metadata

## Phase 2: MCP Tool Integration

### Description
Wire the new parameters through the MCP tool layer so that `mcp_scrapling_get`, `mcp_scrapling_fetch`, `mcp_scrapling_stealthy_fetch` (and bulk variants) accept and forward the flags.

### Affected Files
- `scrapling/core/ai.py` — Modify `fetch_url()`, `fetch_urls()`, `stealthy_fetch_url()`, `stealthy_fetch_urls()`, `get_url()`, `get_urls()`
- `scrapling/core/shell.py` — Ensure `_execute_single()` passes through the new parameters if applicable

### TODO
- [ ] Add `return_inline` and `write_raw_file` to the JSON Schema definitions for all affected MCP tools in `core/ai.py`
- [ ] Update `fetch_url()` to read the new params from `tool_params` and pass them to `_extract_content()`
- [ ] Update `fetch_urls()` (bulk) to handle per-URL `return_inline` / `write_raw_file` overrides
- [ ] Update `stealthy_fetch_url()` and `stealthy_fetch_urls()` similarly
- [ ] Update `get_url()` and `get_urls()` similarly
- [ ] In the response assembly logic, when `return_inline=True`, return the content string directly instead of the file-path message
- [ ] When `write_raw_file=True`, return the `.md`/`.txt`/`.html` file path in the response message
- [ ] Ensure bulk operations aggregate results correctly when some URLs use inline and others use file output
- [ ] Add parameter validation: if both `return_inline` and `write_raw_file` are `True`, prefer `return_inline` (with a note in response)

## Phase 3: Unit Tests

### Description
Add comprehensive unit tests for the new functionality and verify existing behavior is unchanged.

### Affected Files
- `tests/core/test_shell.py` — Add tests for inline return and raw file writing
- `tests/ai/test_ai_mcp.py` — Add tests for MCP tool parameter forwarding

### TODO
- [ ] Add test `_test_extract_content_returns_inline` — Verify that `_extract_content(url, return_inline=True)` returns a dict with `content` key containing the raw string and no file is written
- [ ] Add test `_test_extract_content_write_raw_file_markdown` — Verify that `_extract_content(url, write_raw_file=True, extraction_type='markdown')` writes a `.md` file with raw markdown content (no JSON wrapper)
- [ ] Add test `_test_extract_content_write_raw_file_text` — Verify `.txt` extension for text extraction
- [ ] Add test `_test_extract_content_write_raw_file_html` — Verify `.html` extension for HTML extraction
- [ ] Add test `_test_extract_content_inline_size_fallback` — Verify that content exceeding `INLINE_MAX_SIZE` auto-falls back to file output even when `return_inline=True`
- [ ] Add test `_test_extract_content_default_behavior_unchanged` — Verify that with no flags set, behavior is identical to before (JSON file + schema file)
- [ ] Add test `_test_extract_content_both_flags_prefer_inline` — Verify that when both flags are `True`, inline takes precedence
- [ ] Add test `_test_fetch_url_return_inline` in `test_ai_mcp.py` — Verify MCP `fetch_url` correctly forwards `return_inline=True`
- [ ] Add test `_test_fetch_url_write_raw_file` in `test_ai_mcp.py` — Verify MCP `fetch_url` correctly forwards `write_raw_file=True`
- [ ] Add test `_test_bulk_fetch_mixed_modes` in `test_ai_mcp.py` — Verify bulk fetch handles a mix of inline and file-based URLs
- [ ] Run existing tests to confirm no regressions (`pytest tests/`)

## Phase 4: Documentation & Type Hints

### Description
Update type hints, docstrings, and any relevant documentation.

### Affected Files
- `scrapling/core/shell.py` — Update docstrings for `_extract_content` and `_save_content_to_file`
- `scrapling/core/ai.py` — Update docstrings for fetch functions
- `docs/api-reference/fetchers.md` (if applicable) — Document the new parameters

### TODO
- [ ] Add type hints for `return_inline: bool = False` and `write_raw_file: bool = False` in all modified function signatures
- [ ] Update docstrings to describe the new parameters, their defaults, and the auto-fallback behavior
- [ ] Add a constant `INLINE_MAX_SIZE = 10240` at module level in `shell.py` with a docstring
- [ ] Document the file extension mapping (markdown -> `.md`, text -> `.txt`, html -> `.html`)
- [ ] Update any public API reference docs to mention the new parameters

## Testing Strategy
- **Framework:** pytest + pytest-asyncio (configured in `pytest.ini`, `asyncio_mode = auto`)
- **Test Patterns:** Follow existing conventions — `@pytest.fixture` for setup, `@pytest.mark.asyncio` for async tests, direct assertions, `tempfile` for file system tests
- **Coverage Goals:**
  - Inline return path (content in response, no file written)
  - Raw file writing path (correct extension, no JSON wrapper)
  - Size threshold auto-fallback
  - Default behavior preservation (regression)
  - Both-flags conflict resolution
  - MCP parameter forwarding (single and bulk)
- **Tests to Create:**
  - `tests/core/test_shell.py` — 6 new tests covering inline return, raw file writing (3 extraction types), size fallback, default behavior, and both-flags interaction
  - `tests/ai/test_ai_mcp.py` — 3 new tests covering MCP forwarding for single URL, single URL raw file, and bulk mixed modes
