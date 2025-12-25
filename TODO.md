# SDK Remaining Tasks

## ✅ Completed (Phase 1-3)
- [x] Create shared serialization utilities
- [x] Create BaseAPIClient class
- [x] Refactor all clients to use base class
- [x] Standardize error handling
- [x] Fix bare exception clauses

---

## 🔴 High Priority - Do Next

### 1. **Remove/Implement Unimplemented Methods**
**Location:** `sdk/neurocluster/api/agents.py:576-624`

**Issue:** Two methods raise `Exception("TODO: unimplemented")`:
- `get_pipedream_tools()` 
- `update_pipedream_tools()`

**Action:** Either:
- Remove them if not needed
- Implement them properly
- Mark as deprecated with proper deprecation warnings

**Impact:** These will break user code if called. Need to decide on API.

---

### 2. **Test the Refactored Code**
**Action:** Run the example to verify nothing broke:
```bash
cd sdk
PYTHONPATH=$(pwd) uv run example/example.py
```

**Why:** We changed core infrastructure. Need to verify backward compatibility.

---

### 3. **Add Basic Unit Tests**
**Priority:** Medium-High

**What to test:**
- `serialization.py`: `to_dict`, `from_dict`, `handle_api_response`
- `base_client.py`: Client initialization, headers, context manager
- Error handling paths (404, 403, 500, etc.)

**Where:** Create `sdk/tests/` directory with:
- `test_serialization.py`
- `test_base_client.py`
- `test_error_handling.py`

---

## 🟡 Medium Priority

### 4. **Remove Example Code from Source Files**
**Location:** `sdk/neurocluster/api/agents.py:732-783`

**Issue:** 50+ lines of commented example code in source file

**Action:** Move to:
- `sdk/examples/agents_example.py` OR
- Update `sdk/README.md` with examples

---

### 5. **Improve Type Safety**
**Issue:** Still using `Any` in many places:
- `Message.content: Any` (threads.py:94)
- `metadata: Any` in multiple places
- `tool_calls: Optional[Any]` (models.py:16)

**Action:** Create TypedDict or proper types for:
- Message content structures
- Metadata structures
- Tool call structures

**Benefit:** Better IDE support, catch errors at type-check time

---

### 6. **Extract Magic Strings to Constants**
**Location:** Throughout codebase

**Examples:**
- `"X-API-Key"` appears in multiple places
- `"application/json"` repeated
- Message type strings

**Action:** Create `sdk/neurocluster/api/constants.py`:
```python
class APIHeaders:
    API_KEY = "X-API-Key"
    CONTENT_TYPE = "Content-Type"
    ACCEPT = "Accept"

class ContentTypes:
    JSON = "application/json"
```

---

### 7. **Add HTTP Connection Pooling**
**Location:** `base_client.py`

**Action:** Configure httpx with connection limits:
```python
limits = httpx.Limits(
    max_keepalive_connections=20,
    max_connections=100,
    keepalive_expiry=30.0
)
self.client = httpx.AsyncClient(
    headers=headers,
    timeout=timeout,
    base_url=self.base_url,
    limits=limits
)
```

**Benefit:** Better performance for multiple requests

---

## 🟢 Low Priority - Nice to Have

### 8. **Refactor Complex Stream Parsing**
**Location:** `sdk/neurocluster/utils.py:148-330`

**Issue:** Single 180-line function with complex state machine

**Action:** Break into `StreamParser` class:
```python
class StreamParser:
    def __init__(self):
        self.state = "text"
        self.chunks = []
        ...
    
    async def parse(self, stream):
        ...
```

---

### 9. **Standardize Naming Conventions**
**Issues:**
- `AgentPressTools` vs `AgentPress_ToolConfig` (inconsistent underscore)
- Some methods use `snake_case`, some don't

**Action:** Review and standardize (but be careful - might break API)

---

### 10. **Improve Documentation**
**Action:** 
- Add comprehensive docstrings to all public methods
- Add type hints where missing
- Document error conditions
- Add usage examples

---

### 11. **Handle Thread Deletion Properly**
**Location:** `sdk/neurocluster/thread.py:52-53`

**Issue:** `delete()` calls `delete_thread()` which raises `NotImplementedError`

**Action:** Either implement or document clearly that it's not supported

---

### 12. **Consider Pydantic Migration (Future)**
**Idea:** Replace manual `from_dict`/`to_dict` with Pydantic models

**Benefit:** 
- Automatic validation
- Better type safety
- Less custom serialization code

**Cost:** Breaking change, would require v2.0

---

## 📋 Quick Wins (Can Do Now)

1. **Remove commented example code** (5 min)
2. **Add connection pooling** (10 min)
3. **Extract magic strings** (15 min)
4. **Run example to verify** (5 min)

---

## 🎯 Recommended Order

1. **Test the refactored code** (verify it works)
2. **Remove/fix unimplemented methods** (fix broken API)
3. **Add basic tests** (prevent regressions)
4. **Quick wins** (extract constants, remove dead code)
5. **Improve type safety** (gradual improvement)
6. **Refactor complex code** (when time permits)

---

## 📊 Estimated Time

- **High Priority:** 4-6 hours
- **Medium Priority:** 8-12 hours  
- **Low Priority:** 12-16 hours
- **Total:** ~24-34 hours of work

---

## 🚀 Next Immediate Steps

1. Run `example/example.py` to verify everything works
2. Decide on `get_pipedream_tools` / `update_pipedream_tools` - remove or implement?
3. Create basic test structure
4. Extract magic strings to constants

