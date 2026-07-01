# Implementation: Inline Content Output for Large Scraping Responses

## Feature

Two new opt-in parameters added to all Scrapling MCP scraping tools:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `return_inline` | `bool` | `false` | Returns extracted content directly in the tool response regardless of size. No file is written. |
| `write_raw_file` | `bool` | `false` | Writes extracted content as a plain file (`.md`, `.txt`, or `.html` matching the extraction type) instead of a JSON wrapper. Eliminates the need for intermediate JSON parsing. |

When both flags are `true`, `return_inline` takes precedence and a note is included in the response.

### Size Threshold

- **Default:** `INLINE_MAX_SIZE = 10240` bytes (10 KB)
- **Configurable:** Set via `SCRAPLING_INLINE_MAX_SIZE` environment variable
- **Behavior:** The size threshold applies to the default mode (no flags set). When content exceeds `INLINE_MAX_SIZE`, the response is automatically written to a temporary file. Setting `return_inline=true` bypasses this limit and always returns content inline regardless of size.

### File Extension Mapping

| Extraction Type | File Extension |
|----------------|---------------|
| `markdown` | `.md` |
| `text` | `.txt` |
| `html` | `.html` |

---

## Motivation

When MCP scraping tools return large responses, they write results to a JSON file on disk. This forces every consumer to perform an intermediate step:

1. Read the file path from the tool result
2. Parse the JSON wrapper to extract the actual content (`data.content[0]`)
3. Truncate to a readable length

This adds friction, extra tool calls, and cognitive overhead — especially during multi-source research sessions where 3+ URLs are scraped in parallel.

### Goals Achieved

- **Reduces tool calls per research session** by 1–3 (one JSON parse per scraped URL eliminated)
- **Removes dependency on external tools** (e.g., Node.js) for JSON parsing
- **Simplifies the scraping workflow** from a 2-step process to a 1-step process
- **Zero breaking changes** — both parameters are opt-in with safe defaults (`false`)

---

## What Was Added/Changed

### Core Library Changes

#### `scrapling/core/shell.py`

| Change | Description |
|--------|-------------|
| **Added `import os`** | Required for environment variable access |
| **Added `INLINE_MAX_SIZE` constant** | Module-level constant (default 10240 bytes), configurable via `SCRAPLING_INLINE_MAX_SIZE` env var |
| **Extended `_extract_content()` signature** | Added `return_inline: bool = False` and `write_raw_file: bool = False` parameters with docstrings |
| **Extended `write_content_to_file()` signature** | Added `write_raw_file: bool = False` parameter with docstring |

#### `scrapling/core/ai.py`

| Change | Description |
|--------|-------------|
| **Added imports** | `os` and `make_temp_file` for temporary file creation |
| **Added `INLINE_MAX_SIZE` import** | Imported from `scrapling.core.shell` |
| **Rewrote `_translate_response()`** | Now handles three modes: default (size-checked — inline if under `INLINE_MAX_SIZE`, auto-fallback to file if over), `return_inline` (always inline, no size limit), and `write_raw_file` (plain file write with path in response) |
| **Updated `get()`** | Added `return_inline` and `write_raw_file` params, forwarded to `bulk_get()` |
| **Updated `bulk_get()`** | Added params, forwarded to `_translate_response()` |
| **Updated `fetch()`** | Added params, forwarded to `bulk_fetch()` |
| **Updated `bulk_fetch()`** | Added params, forwarded to `_translate_response()` |
| **Updated `stealthy_fetch()`** | Added params, forwarded to `bulk_stealthy_fetch()` |
| **Updated `bulk_stealthy_fetch()`** | Added params, forwarded to `_translate_response()` |
| **Updated all docstrings** | Documented new parameters in every method |

#### `scrapling/core/_shell_signatures.py`

| Change | Description |
|--------|-------------|
| **`_REQUESTS_PARAMS`** | Added `"return_inline": Optional[bool]` and `"write_raw_file": Optional[bool]` |
| **`_FETCH_PARAMS`** | Added `"return_inline": Optional[bool]` and `"write_raw_file": Optional[bool]` |
| **`_STEALTHY_FETCH_PARAMS`** | Added `"return_inline": Optional[bool]` and `"write_raw_file": Optional[bool]` |

### Test Changes

#### `tests/core/test_shell_inline.py` (new file — 13 tests)

| Test Class | Tests |
|------------|-------|
| `TestInlineMaxSize` | Verifies `INLINE_MAX_SIZE` value and type |
| `TestExtractContentWithInline` | Tests `_extract_content()` with all flag combinations, all extraction types |
| `TestWriteContentToFile` | Tests file writing for `.md`, `.html`, `.txt`, invalid extensions, and `write_raw_file=True` |

#### `tests/ai/test_ai_inline.py` (new file — 15 tests)

| Test Class | Tests |
|------------|-------|
| `TestTranslateResponseInline` | Tests `_translate_response()` for default small content (inline), default large content (auto-fallback to file), inline small content, inline large content (no fallback), raw file writing, and both-flags precedence |
| `TestMCPServerMethodSignatures` | Verifies all 6 MCP methods accept new params with correct defaults (`False`) |
| `TestShellSignatures` | Verifies all 3 signature dicts include new params |

### Test Results

```
28 new tests: PASSED
762 existing tests: PASSED
4 pre-existing failures: UNRELATED (Windows path separators, robots.txt rate limit)
```

---

## Usage Examples

### Inline Return (Small Content)

```python
response = await server.fetch(
    url="https://example.com",
    return_inline=True,
)
# response.content[0] contains the raw markdown string
```

### Inline Return (Large Content — No Size Limit)

```python
response = await server.fetch(
    url="https://example.com/large-page",
    return_inline=True,
)
# response.content[0] contains the full raw content regardless of size
```

### Raw File Writing

```python
response = await server.fetch(
    url="https://example.com",
    write_raw_file=True,
)
# response.content[0] contains "Content written to: /tmp/scrapling_raw_markdown_XXXXX.md"
# File contains raw markdown — no JSON wrapper
```

### Configuring the Size Threshold

```bash
# PowerShell
$env:SCRAPLING_INLINE_MAX_SIZE = 20480
scrapling mcp

# Bash
export SCRAPLING_INLINE_MAX_SIZE=20480
scrapling mcp
```

---

## Backward Compatibility

- All new parameters default to `false`
- Default behavior (no flags set) now includes a size-based auto-fallback: content under `INLINE_MAX_SIZE` is returned inline as before, content over the threshold is written to a temporary file
- Existing callers see zero changes for small responses
- No API surface was removed or renamed
