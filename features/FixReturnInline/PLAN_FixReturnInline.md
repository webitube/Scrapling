# Plan: Fix `return_inline` behavior for `bulk_get`

## Goal
Modify the `bulk_get` tool (and other bulk tools) so that when `return_inline=true`, it returns the raw content directly without the JSON envelope (ResponseModel), bypassing the `INLINE_MAX_SIZE` limit.

## Current Behavior
- `bulk_get` returns a `List[ResponseModel]`.
- `_translate_response` handles the logic for `return_inline` and `write_raw_file`, but it always returns a `ResponseModel`.
- The MCP server wraps the return value of `bulk_get` in a JSON envelope because it returns a list of models.

## Proposed Changes

### Phase 1: Refactor Response Translation
The goal of this phase is to decouple raw content extraction from the `ResponseModel` wrapping to allow bulk tools to return raw strings.

- [ ] **Step 1.1: Create `_get_raw_content` helper**
    - Implement a new helper function `_get_raw_content(page, extraction_type, css_selector, main_content_only)` in `scrapling/core/ai.py`.
    - This function should handle the `Convertor._extract_content` call and return the joined `raw_content` string.
- [ ] **Step 1.2: Refactor `_translate_response`**
    - Update `_translate_response` to call `_get_raw_content` to obtain the raw text.
    - Keep the existing logic for `return_inline`, `write_raw_file`, and `INLINE_MAX_SIZE` within `_translate_response` to maintain backward compatibility for single-page tools.

### Phase 2: Update Bulk Tools
Modify the bulk tools to conditionally return raw content when `return_inline=true`.

- [ ] **Step 2.1: Update `bulk_get`**
    - Modify `bulk_get` in `scrapling/core/ai.py`.
    - If `return_inline=true`, use `_get_raw_content` for each response and return the results as a joined string (or a format that avoids the JSON envelope).
    - If `return_inline=false`, continue returning `List[ResponseModel]` via `_translate_response`.
- [ ] **Step 2.2: Update `bulk_fetch`**
    - Apply the same logic as Step 2.1 to `bulk_fetch`.
- [ ] **Step 2.3: Update `bulk_stealthy_fetch`**
    - Apply the same logic as Step 2.1 to `bulk_stealthy_fetch`.
- [ ] **Step 2.4: Update Type Hints**
    - Update the return type hints for `bulk_get`, `bulk_fetch`, and `bulk_stealthy_fetch` to reflect that they can now return either `List[ResponseModel]` or `str`.

### Phase 3: Testing and Validation
Ensure the changes work as expected and do not break existing functionality.

- [ ] **Step 3.1: Update Unit Tests**
    - Update `tests/ai/test_ai_inline.py` and `tests/ai/test_ai_mcp.py` to include test cases for `return_inline=true` in bulk tools.
    - Verify that the output is a raw string without the JSON envelope.
    - Verify that `INLINE_MAX_SIZE` is ignored when `return_inline=true`.
- [ ] **Step 3.2: Regression Testing**
    - Verify `return_inline=false` still obeys `INLINE_MAX_SIZE`.
    - Verify `write_raw_file=true` still works correctly when `return_inline=false`.
    - Verify single-page tools (`get`, `fetch`, `stealthy_fetch`) still behave as expected.


## Verification
- Test `bulk_get` with `return_inline=false` $\rightarrow$ verify JSON envelope and `INLINE_MAX_SIZE` limit.
- Test `bulk_get` with `return_inline=true` $\rightarrow$ verify raw content is returned without envelope and `INLINE_MAX_SIZE` is ignored.
- Verify `write_raw_file=true` still works as expected when `return_inline=false`.
