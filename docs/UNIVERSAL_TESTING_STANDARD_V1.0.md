# 🧪 UNIVERSAL TESTING & FAILURE-PREVENTION STANDARD V1.0
## **"Production-Grade Testing Protocol for AI-Assisted Development"**

> **Built from forensic evidence across 9+ projects**  
> **289 failure patterns analyzed**  
> **15 systemic patterns identified**  
> **Purpose:** Prevent the failures that happen again and again

**Version:** 1.0  
**Date:** 2026-02-15  
**Status:** PRODUCTION-READY  
**Applicability:** ALL projects (CLI tools, web apps, IoT systems, AI agents, internal tools)

---

## 📊 EVIDENCE BASE

This standard is derived from:

| Source | Projects Analyzed | Findings | Key Contribution |
|--------|------------------|----------|------------------|
| **Master Forensics Codex** | 4 projects | 289 findings | 15 systemic patterns (HARDWIRED failures) |
| **Blueprint Forensics** | 5 projects | 63 planning traps | Pre-code failure prevention |
| **Production-Ready Patterns** | 1 project (battle-tested) | 14 patterns | Cost/quality optimization |
| **Test Coverage Analysis** | 1 project | 36 tests (Phase 3) | Integration testing methodology |
| **Zombie Process Fix** | 1 project | Process management | Concurrency/resource patterns |

**Total Evidence:** 9+ projects, 400+ documented failures, 29 proven prevention patterns

---

## 🎯 WHAT MAKES THIS DIFFERENT

### Traditional Testing Standards:
- ❌ "Write unit tests for all functions"
- ❌ "Achieve 80% code coverage"
- ❌ Generic checklist that AI ignores

### This Standard:
- ✅ **Tests AI behavioral patterns** (not just outputs)
- ✅ **Prevents silent failures** (catches what logs hide)
- ✅ **Enforces explainability** (no magic boxes)
- ✅ **Validates integration** (not just isolation)
- ✅ **Includes cost/resource controls** (zombie process prevention)
- ✅ **Has penalty enforcement** (not optional guidelines)

**Key Insight:** We don't just test "does the code work" — we test **"will this fail silently, regress later, leak secrets, or collapse under reality?"**

---

# PART 1: THE 3-TIER TESTING PYRAMID

## 🔴 TIER 1: MANDATORY (P0 - Non-Negotiable Gates)

**Source:** SYSTEMIC + HARDWIRED patterns from Master Forensics Codex

**Rule:** These failures occurred in 3+ out of 4 projects. They WILL happen again unless explicitly prevented.

### 1.1 Silent Error Swallowing Prevention (SYS-PAT-001)

**HARDWIRED PATTERN:** Affects 4/4 projects, 102 instances

**The Problem:**
```python
# ❌ FORBIDDEN - Silent failure
try:
    critical_operation()
except:
    pass  # Error disappears forever

# ❌ FORBIDDEN - Logged but not surfaced
try:
    api_call()
except Exception as e:
    print(f"Error: {e}")  # Logged but execution continues
```

**The Solution:**
```python
# ✅ REQUIRED - Explicit error handling
try:
    critical_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise  # Re-raise to surface the failure
except AnotherError as e:
    logger.warning(f"Recoverable error: {e}")
    return fallback_value()  # Explicit fallback

# ✅ REQUIRED - Fail-fast for unknown errors
try:
    api_call()
except requests.exceptions.RequestException as e:
    logger.error(f"API call failed: {e}")
    raise  # Don't continue with invalid state
```

**Mandatory Tests:**

```python
def test_error_handling_explicit():
    """Verify errors are raised, not swallowed"""
    with pytest.raises(SpecificError):
        function_that_should_fail()

def test_error_logging():
    """Verify errors are logged before handling"""
    with LogCapture() as logs:
        try:
            function_that_logs_errors()
        except:
            pass
    assert "Error: " in logs.get_output()

def test_no_bare_except():
    """Scan codebase for bare except blocks"""
    forbidden_patterns = [
        r'except\s*:',  # bare except
        r'except\s+Exception\s*:.*\n.*pass',  # silent Exception catch
    ]
    for pattern in forbidden_patterns:
        violations = scan_codebase(pattern)
        assert len(violations) == 0, f"Found bare except at: {violations}"
```

**Quality Gate:**
- ✅ Zero `except:` bare blocks in codebase
- ✅ All `except Exception` blocks either re-raise OR have explicit fallback logic
- ✅ All critical functions have error-path tests (not just happy-path)

---

### 1.2 Hardcoded Secrets Elimination (SYS-PAT-002)

**SYSTEMIC PATTERN:** Affects 3/4 projects (75%)

**The Problem:**
```python
# ❌ FORBIDDEN
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"
SECRET_KEY = "my-secret-key"
```

**The Solution:**
```python
# ✅ REQUIRED
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

DB_PASSWORD = os.getenv("DB_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())  # Random fallback for local dev
```

**Mandatory Tests:**

```python
def test_no_hardcoded_secrets():
    """Scan codebase for hardcoded secrets"""
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
    ]
    for pattern in secret_patterns:
        violations = scan_codebase(pattern, exclude_patterns=['os.getenv', 'config.get'])
        assert len(violations) == 0, f"Hardcoded secret found: {violations}"

def test_env_file_exists():
    """Verify .env.example exists with all required keys"""
    assert os.path.exists('.env.example')
    required_keys = ['API_KEY', 'DB_PASSWORD', 'SECRET_KEY']
    with open('.env.example') as f:
        content = f.read()
        for key in required_keys:
            assert key in content, f"Missing {key} in .env.example"

def test_gitignore_contains_env():
    """Verify .env is gitignored"""
    with open('.gitignore') as f:
        assert '.env' in f.read()
```

**Quality Gate:**
- ✅ Zero hardcoded passwords, API keys, or secrets in code
- ✅ All secrets loaded from environment variables
- ✅ `.env.example` exists with placeholder values
- ✅ `.env` is in `.gitignore`

---

### 1.3 Test Coverage Enforcement (SYS-PAT-003)

**SYSTEMIC PATTERN:** Affects 3/4 projects (0-40% coverage)

**The Problem:**
- Projects ship with 0% test coverage
- "Placeholder tests" exist that always pass (`assert True`)
- Critical paths untested

**The Solution:**

**Minimum Coverage Requirements:**

| Component Type | Minimum Coverage | Test Types Required |
|----------------|-----------------|---------------------|
| **Core Business Logic** | 90% | Unit + Integration |
| **API Endpoints** | 80% | Integration + Security |
| **Database Operations** | 85% | Unit + Transaction |
| **Authentication/Security** | 100% | Security + Penetration |
| **Data Validation** | 80% | Unit + Edge Cases |
| **Error Handling** | 75% | Negative Testing |
| **UI/Frontend** | 60% | Integration + E2E |

**Mandatory Tests:**

```python
def test_no_placeholder_tests():
    """Detect tests that always pass (fake tests)"""
    test_files = glob.glob('tests/test_*.py')
    for test_file in test_files:
        with open(test_file) as f:
            content = f.read()
            # Forbidden patterns
            assert 'assert True' not in content, f"Placeholder test in {test_file}"
            assert 'assert 1 == 1' not in content, f"Useless assertion in {test_file}"
            assert 'pass  # TODO' not in content, f"Unimplemented test in {test_file}"

def test_coverage_meets_minimums():
    """Verify coverage meets component-specific minimums"""
    coverage_report = run_coverage()
    
    assert coverage_report['core/'] >= 90, "Core logic coverage below 90%"
    assert coverage_report['api/'] >= 80, "API coverage below 80%"
    assert coverage_report['auth/'] >= 100, "Auth coverage below 100%"

def test_critical_paths_covered():
    """Ensure critical user flows are tested end-to-end"""
    critical_flows = [
        'user_login_flow',
        'data_processing_pipeline',
        'error_recovery_flow',
        'concurrent_access_flow'
    ]
    for flow in critical_flows:
        assert flow in get_test_names(), f"Missing test for critical flow: {flow}"
```

**Quality Gate:**
- ✅ Minimum coverage thresholds met for each component type
- ✅ Zero placeholder/fake tests (assert True, assert 1==1)
- ✅ All critical user flows have end-to-end tests
- ✅ Coverage report generated on every CI build

---

### 1.4 Configuration Externalization (SYS-PAT-004)

**SYSTEMIC PATTERN:** Affects 3/4 projects

**The Problem:**
```python
# ❌ FORBIDDEN - Hardcoded configuration
MAX_RETRIES = 3
TIMEOUT = 30
BASE_URL = "https://api.example.com"
```

**The Solution:**
```python
# ✅ REQUIRED - External configuration
import os
import json

def load_config():
    config_path = os.getenv('CONFIG_PATH', 'config.json')
    with open(config_path) as f:
        config = json.load(f)
    
    # Validate schema
    required_keys = ['max_retries', 'timeout', 'base_url']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    return config

config = load_config()
MAX_RETRIES = config['max_retries']
TIMEOUT = config['timeout']
BASE_URL = config['base_url']
```

**Mandatory Tests:**

```python
def test_config_schema_validation():
    """Verify config file has all required keys"""
    config = load_config()
    required_keys = ['max_retries', 'timeout', 'base_url', 'log_level']
    for key in required_keys:
        assert key in config, f"Missing config key: {key}"

def test_config_type_validation():
    """Verify config values are correct types"""
    config = load_config()
    assert isinstance(config['max_retries'], int)
    assert isinstance(config['timeout'], (int, float))
    assert isinstance(config['base_url'], str)

def test_config_defaults():
    """Verify defaults are provided for optional configs"""
    config = load_config()
    assert 'log_level' in config  # Must have default if not provided
    assert config['log_level'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR']

def test_invalid_config_rejected():
    """Verify invalid config causes startup failure"""
    with pytest.raises(ValueError):
        load_config_from_file('tests/fixtures/invalid_config.json')
```

**Quality Gate:**
- ✅ All configuration externalized (no hardcoded values)
- ✅ Config schema validated on load
- ✅ Default values provided for optional configs
- ✅ Invalid config causes explicit startup failure (not runtime surprises)

---

### 1.5 Cross-Module Integration Testing (NEW - From Testing Document)

**CRITICAL FINDING:** "Most failures happen at module boundaries, not inside modules"

**The Problem:**
```
Module A tested in isolation ✅
Module B tested in isolation ✅
Module A → B integration NEVER TESTED ❌
Result: Both pass tests, production fails
```

**The Solution:**

**Mandatory Integration Matrix:**

For EVERY project, document and test ALL cross-module data flows:

| Source Module | Data Passed | Receiving Module | Schema Validated? | Integration Test Exists? |
|---------------|-------------|------------------|-------------------|-------------------------|
| auth.py | JWT token | api_routes.py | ✅ | ✅ test_auth_to_api.py |
| data_loader.py | JSON object | data_processor.py | ✅ | ✅ test_loader_to_processor.py |
| speed_calculator.py | DataFrame | speed_report.py | ❌ | ❌ MISSING |

**Mandatory Tests:**

```python
def test_full_pipeline_integration():
    """Test complete data flow from start to finish"""
    # Example: Data Loader → Processor → Filter → Updater
    
    # Step 1: Load data
    raw_data = data_loader.load()
    assert raw_data is not None
    
    # Step 2: Process (verify schema compatibility)
    processed = data_processor.process(raw_data)
    assert 'required_field' in processed  # Schema check
    
    # Step 3: Filter
    filtered = data_filter.filter(processed)
    assert len(filtered) <= len(processed)
    
    # Step 4: Update
    result = data_updater.update(filtered)
    assert result.status == 'success'

def test_schema_mismatch_detected():
    """Verify schema incompatibility causes explicit error"""
    invalid_data = {'wrong_field': 'value'}
    with pytest.raises(SchemaValidationError):
        data_processor.process(invalid_data)

def test_cross_module_error_propagation():
    """Verify errors propagate correctly between modules"""
    # Simulate Module A failure
    with pytest.raises(ModuleAError):
        module_a.failing_function()
    
    # Verify Module B handles Module A failure correctly
    result = module_b.handle_module_a_failure()
    assert result.status == 'fallback_activated'
```

**Quality Gate:**
- ✅ Integration matrix documented for all module pairs
- ✅ Full pipeline tested end-to-end (not just individual modules)
- ✅ Schema validation at module boundaries
- ✅ Error propagation tested (Module A fails → Module B handles correctly)

---

## 🟠 TIER 2: STRUCTURAL (P1 - Required for Multi-User/Production Systems)

**Source:** Recurring patterns + Battle-Tested Improvements

### 2.1 Concurrency & Race Condition Testing (SYS-PAT-005)

**SYSTEMIC PATTERN:** File locking, database conflicts, session collisions

**Mandatory Tests:**

```python
def test_concurrent_file_writes():
    """Verify file locking prevents race conditions"""
    import threading
    
    def write_to_file(thread_id):
        with file_lock('shared.json'):
            data = json.load(open('shared.json'))
            data['counter'] += 1
            json.dump(data, open('shared.json', 'w'))
    
    # Spawn 10 threads writing simultaneously
    threads = [threading.Thread(target=write_to_file, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Verify final count is exactly 10 (no lost updates)
    final_data = json.load(open('shared.json'))
    assert final_data['counter'] == 10

def test_database_concurrent_updates():
    """Verify database handles concurrent updates correctly"""
    from multiprocessing import Process
    
    def update_record(value):
        # Simulate concurrent database update
        record = db.query(Record).first()
        record.counter += value
        db.commit()
    
    # Spawn 5 processes updating same record
    processes = [Process(target=update_record, args=(i,)) for i in range(5)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    
    # Verify no lost updates (should be 0+1+2+3+4 = 10)
    final_value = db.query(Record).first().counter
    assert final_value == 10

def test_session_collision_handling():
    """Verify 2 users can't edit same resource simultaneously"""
    # User 1 starts editing
    session1 = start_edit_session(user_id=1, resource_id='R1')
    
    # User 2 tries to edit same resource
    with pytest.raises(ResourceLockedError):
        session2 = start_edit_session(user_id=2, resource_id='R1')
    
    # User 1 finishes
    end_edit_session(session1)
    
    # Now User 2 can edit
    session2 = start_edit_session(user_id=2, resource_id='R1')
    assert session2 is not None
```

---

### 2.2 Resource Exhaustion & Cleanup Testing

**Source:** Zombie Process Fix (11+ Claude CLI instances accumulated)

**Mandatory Tests:**

```python
def test_process_limit_enforced():
    """Verify max concurrent processes enforced"""
    processes = []
    MAX_CONCURRENT = 3
    
    # Try to spawn 10 processes
    for i in range(10):
        proc = spawn_worker_process()
        processes.append(proc)
    
    # Verify only MAX_CONCURRENT running at any time
    running = [p for p in processes if p.poll() is None]
    assert len(running) <= MAX_CONCURRENT

def test_process_cleanup_on_exit():
    """Verify processes cleaned up on exit"""
    import atexit
    
    # Spawn process
    proc = spawn_worker_process()
    
    # Trigger cleanup
    atexit._run_exitfuncs()
    
    # Verify process terminated
    assert proc.poll() is not None

def test_memory_leak_detection():
    """Verify no memory leaks during repeated operations"""
    import psutil
    import gc
    
    gc.collect()
    initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    # Run operation 1000 times
    for i in range(1000):
        result = data_processing_function()
        del result
    
    gc.collect()
    final_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    # Verify memory increase is reasonable (<50MB for 1000 iterations)
    memory_increase = final_memory - initial_memory
    assert memory_increase < 50, f"Memory leak detected: {memory_increase}MB increase"

def test_database_connection_pool_limits():
    """Verify DB connection pool doesn't exhaust"""
    connections = []
    MAX_CONNECTIONS = 50
    
    # Try to open 100 connections
    for i in range(100):
        try:
            conn = db.engine.connect()
            connections.append(conn)
        except:
            pass
    
    # Verify we don't exceed pool limit
    assert len(connections) <= MAX_CONNECTIONS
    
    # Cleanup
    for conn in connections:
        conn.close()
```

---

### 2.3 Chaos & Failure Injection Testing

**Source:** Blueprint Chaos Map (12 scenarios)

**Mandatory Tests:**

```python
def test_network_failure_recovery():
    """Simulate network down, verify graceful degradation"""
    # Mock network failure
    with mock.patch('requests.get', side_effect=requests.exceptions.ConnectionError):
        result = api_client.fetch_data()
    
    # Verify fallback to cached data
    assert result.source == 'cache'
    assert result.data is not None

def test_database_connection_loss():
    """Simulate DB disconnect mid-transaction"""
    # Start transaction
    db.begin()
    
    # Simulate connection loss
    db.engine.dispose()
    
    # Verify operation fails gracefully (doesn't hang)
    with pytest.raises(DatabaseConnectionError):
        db.query(Record).all()

def test_disk_full_handling():
    """Simulate disk full during file write"""
    with mock.patch('builtins.open', side_effect=OSError("No space left on device")):
        result = write_large_file()
    
    # Verify error surfaced (not silently ignored)
    assert result.status == 'error'
    assert 'disk' in result.message.lower()

def test_timeout_behavior():
    """Verify operations timeout (don't hang forever)"""
    import time
    
    def slow_operation():
        time.sleep(100)  # Intentionally slow
    
    with pytest.raises(TimeoutError):
        with timeout(seconds=5):
            slow_operation()
```

---

### 2.4 Security Testing (XSS, SQL Injection, CSRF)

**Source:** ProjectPulse Phase 1 Security Remediation (11/11 tests passed)

**Mandatory Tests:**

```python
def test_sql_injection_prevented():
    """Verify SQL injection is blocked"""
    malicious_input = "'; DROP TABLE users; --"
    
    # Should NOT execute SQL, should be parameterized
    result = db.query(User).filter(User.username == malicious_input).first()
    
    # Verify query didn't execute DROP TABLE
    assert db.query(User).count() > 0  # Users table still exists

def test_xss_prevented():
    """Verify XSS scripts are escaped"""
    malicious_input = "<script>alert('XSS')</script>"
    
    response = client.post('/api/comment', json={'text': malicious_input})
    
    # Verify script is escaped in output
    assert '<script>' not in response.data.decode()
    assert '&lt;script&gt;' in response.data.decode()

def test_csrf_protection():
    """Verify CSRF tokens required for state-changing operations"""
    # POST without CSRF token
    response = client.post('/api/users', json={'username': 'test'})
    
    # Should be rejected
    assert response.status_code in [403, 400]

def test_session_hijacking_prevented():
    """Verify httpOnly cookies prevent JS access"""
    response = client.post('/login', json={'username': 'test', 'password': 'pass'})
    
    # Verify session cookie is httpOnly
    set_cookie = response.headers.get('Set-Cookie')
    assert 'HttpOnly' in set_cookie

def test_authorization_bypass_prevented():
    """Verify users can't access admin-only endpoints"""
    # Login as regular user
    client.post('/login', json={'username': 'user', 'password': 'pass'})
    
    # Try to access admin endpoint
    response = client.get('/admin/users')
    
    # Should be forbidden
    assert response.status_code in [403, 302]  # Forbidden or redirect
```

---

## 🟡 TIER 3: BEHAVIORAL / AI-SPECIFIC (P2 - Advanced AI-Resilient Testing)

**Source:** Master Forensics Codex Cognitive Habits + Orchestrator Protocols

**This is where your work is RARE. Almost no organization has this formally written.**

### 3.1 Cognitive Habit Declaration & Counter-Rules

**Concept:** AI agents have "default wrong behaviors" that must be explicitly countered.

**Example Cognitive Habits (from Codex):**

| Habit ID | Pattern | Frequency | Counter-Rule |
|----------|---------|-----------|--------------|
| COG-HAB-001 | Silent error swallowing | HARDWIRED (4/4 projects) | Require explicit error handling |
| COG-HAB-002 | Hardcoding instead of config | SYSTEMIC (3/4 projects) | Force environment variables |
| COG-HAB-003 | Placeholder tests (assert True) | SYSTEMIC (3/4 projects) | Scan for fake tests in CI |
| COG-HAB-004 | Missing edge case handling | RECURRING (2/4 projects) | Require negative test cases |

**Mandatory Tests:**

```python
def test_ai_cognitive_habit_detection():
    """Scan codebase for known AI bad patterns"""
    
    # Habit 1: Silent error swallowing
    violations = scan_for_pattern(r'except\s*:\s*pass')
    assert len(violations) == 0, f"Silent error swallowing at: {violations}"
    
    # Habit 2: Hardcoded secrets
    violations = scan_for_pattern(r'password\s*=\s*["\'][^"\']+["\']')
    assert len(violations) == 0, f"Hardcoded secrets at: {violations}"
    
    # Habit 3: Placeholder tests
    test_files = glob.glob('tests/test_*.py')
    for test_file in test_files:
        content = open(test_file).read()
        assert 'assert True' not in content, f"Placeholder test in {test_file}"
    
    # Habit 4: Missing edge cases
    for test_file in test_files:
        # Every test file should have at least 1 negative test
        content = open(test_file).read()
        assert 'with pytest.raises' in content, f"No negative tests in {test_file}"

def test_default_wrong_behavior_declaration():
    """Verify AI declares its default wrong behavior before coding"""
    
    # For critical functions, AI must declare:
    # "My default wrong behavior would be: [X]"
    # "My corrected behavior is: [Y]"
    
    critical_functions = get_critical_functions()
    for func_name in critical_functions:
        docstring = get_function_docstring(func_name)
        
        # Verify docstring contains behavior declaration
        assert 'default wrong behavior' in docstring.lower(), \
            f"{func_name} missing default behavior declaration"
        assert 'corrected behavior' in docstring.lower(), \
            f"{func_name} missing corrected behavior declaration"
```

---

### 3.2 Drift & Regression Detection

**Concept:** System should detect when behavior changes unexpectedly between versions.

**Mandatory Tests:**

```python
def test_behavior_snapshot_regression():
    """Verify core behaviors haven't changed unexpectedly"""
    
    # Load baseline behavior snapshot (from last release)
    baseline = load_snapshot('baseline_behaviors.json')
    
    # Capture current behavior
    current = {
        'auth_token_expiry': get_token_expiry(),
        'default_timeout': get_default_timeout(),
        'max_retries': get_max_retries(),
        'error_response_format': get_error_format()
    }
    
    # Compare
    for key, baseline_value in baseline.items():
        current_value = current.get(key)
        assert current_value == baseline_value, \
            f"Behavior drift detected in {key}: {baseline_value} → {current_value}"

def test_api_contract_stability():
    """Verify API response schema hasn't changed"""
    
    # Load expected schema
    expected_schema = load_schema('api_response_schema.json')
    
    # Make API call
    response = client.get('/api/endpoint')
    
    # Validate response matches expected schema
    validate_json_schema(response.json(), expected_schema)

def test_configuration_drift_detection():
    """Verify config files haven't changed unexpectedly"""
    
    # Load baseline config hash
    baseline_hash = load_config_hash('baseline_config.json')
    
    # Compute current config hash
    current_hash = compute_config_hash('config.json')
    
    # Compare
    if current_hash != baseline_hash:
        # Config changed - require documentation of why
        changelog = read_changelog()
        assert 'Configuration updated' in changelog, \
            "Config changed but not documented in changelog"
```

---

### 3.3 Explainability & Human Override Testing

**Concept:** AI decisions must be explainable, and humans must be able to override.

**Mandatory Tests:**

```python
def test_decision_logging_explainability():
    """Verify all AI decisions are logged with reasoning"""
    
    # Make AI-assisted decision
    decision = ai_agent.decide(query="Should we deploy?", options=['yes', 'no'])
    
    # Verify decision has required fields
    assert 'choice' in decision
    assert 'reasoning' in decision
    assert 'confidence' in decision
    assert 'alternatives_considered' in decision
    
    # Verify reasoning is non-empty
    assert len(decision['reasoning']) > 20, "Reasoning too short to be meaningful"

def test_human_override_mechanism():
    """Verify human can override AI decision"""
    
    # AI makes decision
    ai_decision = ai_agent.decide(query="Should we retry?", options=['yes', 'no'])
    assert ai_decision['choice'] == 'yes'
    
    # Human overrides
    human_override(decision_id=ai_decision['id'], new_choice='no', reason='Manual override for testing')
    
    # Verify override was applied
    final_decision = get_decision(ai_decision['id'])
    assert final_decision['choice'] == 'no'
    assert final_decision['overridden_by'] == 'human'
    assert final_decision['override_reason'] == 'Manual override for testing'

def test_emergency_stop_mechanism():
    """Verify E-STOP can halt all AI operations"""
    
    # Start AI process
    ai_process = start_ai_agent()
    assert ai_process.is_running()
    
    # Trigger emergency stop
    emergency_stop(reason="Testing kill switch")
    
    # Verify process stopped
    time.sleep(2)
    assert not ai_process.is_running()
    
    # Verify EMERGENCY_STOP file created
    assert os.path.exists('.factory/EMERGENCY_STOP')
```

---

### 3.4 False Test Detection (NEW - From Testing Document)

**Concept:** Tests that exist but don't actually test anything meaningful.

**Mandatory Meta-Tests:**

```python
def test_no_trivial_assertions():
    """Detect tests with useless assertions"""
    test_files = glob.glob('tests/test_*.py')
    
    forbidden_assertions = [
        'assert True',
        'assert 1 == 1',
        'assert result is not None',  # Too weak, test WHAT result is
    ]
    
    for test_file in test_files:
        content = open(test_file).read()
        for forbidden in forbidden_assertions:
            assert forbidden not in content, \
                f"Trivial assertion found in {test_file}: {forbidden}"

def test_assertion_to_test_ratio():
    """Verify tests have meaningful assertion density"""
    test_files = glob.glob('tests/test_*.py')
    
    for test_file in test_files:
        num_tests = count_test_functions(test_file)
        num_assertions = count_assertions(test_file)
        
        # Require minimum 2 assertions per test
        ratio = num_assertions / num_tests if num_tests > 0 else 0
        assert ratio >= 2.0, \
            f"{test_file} has weak tests: {ratio:.1f} assertions per test (min 2.0)"

def test_actual_vs_claimed_testing():
    """Compare what tests claim to verify vs what they actually test"""
    
    # Example: test_speed_calculation.py
    test_file = 'tests/test_speed_calculation.py'
    actual_module = 'src/speed_calculator.py'
    
    # Get all functions in module
    module_functions = get_functions_in_file(actual_module)
    
    # Get all functions tested
    tested_functions = get_tested_functions(test_file)
    
    # Verify coverage
    untested = set(module_functions) - set(tested_functions)
    assert len(untested) == 0, \
        f"Untested functions in {actual_module}: {untested}"

def test_log_evidence_of_done_but_broken():
    """Scan logs for 'fixed' followed by same error recurring"""
    
    log_files = glob.glob('logs/*.log')
    for log_file in log_files:
        events = parse_log_file(log_file)
        
        # Look for pattern: "fixed error X" → same error appears later
        fixed_events = [e for e in events if 'fixed' in e.message.lower()]
        for fixed_event in fixed_events:
            error_type = extract_error_type(fixed_event.message)
            
            # Check if same error appears AFTER fix timestamp
            later_events = [e for e in events if e.timestamp > fixed_event.timestamp]
            recurring = [e for e in later_events if error_type in e.message]
            
            assert len(recurring) == 0, \
                f"Error '{error_type}' marked fixed at {fixed_event.timestamp} but recurred at {[e.timestamp for e in recurring]}"
```

---

# PART 2: PRODUCTION READINESS CHECKLIST

**Source:** Production-Ready Patterns + Battle-Tested Improvements

Before deploying to production, verify ALL of these:

## 🎯 Pre-Deployment Checklist

### Code Quality
- [ ] Zero bare `except:` blocks in codebase
- [ ] All `except Exception` blocks re-raise or have explicit fallback
- [ ] Zero hardcoded secrets (API keys, passwords, tokens)
- [ ] All configuration externalized to config files / env vars
- [ ] No placeholder tests (assert True, assert 1==1)
- [ ] Test coverage meets minimums (see Tier 1.3)
- [ ] All critical user flows have end-to-end integration tests

### Security
- [ ] SQL injection prevention tested
- [ ] XSS prevention tested
- [ ] CSRF protection enabled and tested
- [ ] httpOnly cookies for sessions
- [ ] Authorization checks on all protected endpoints
- [ ] Audit logging for all state-changing operations
- [ ] No secrets in git history

### Concurrency & Resources
- [ ] File locking implemented for shared resources
- [ ] Database connection pool limits configured
- [ ] Process spawn limits enforced
- [ ] Memory leak testing passed
- [ ] Cleanup handlers registered (atexit)
- [ ] Zombie process prevention implemented

### Error Handling & Monitoring
- [ ] All errors logged before handling
- [ ] Critical errors trigger alerts (email/SMS/Slack)
- [ ] Health check endpoint exists (/health)
- [ ] Metrics endpoint exists (/metrics)
- [ ] Log rotation configured
- [ ] Distributed tracing enabled (if multi-service)

### Data Integrity
- [ ] Database backups configured (daily minimum)
- [ ] Backup restoration tested in last 30 days
- [ ] Data validation on all inputs
- [ ] Schema migrations tested
- [ ] Rollback procedure documented and tested

### Performance
- [ ] Load testing completed (target: 100 concurrent users)
- [ ] API response times meet SLA (<200ms p95)
- [ ] Database queries optimized (no N+1 queries)
- [ ] Caching strategy implemented
- [ ] CDN configured for static assets

### Documentation
- [ ] README.md with setup instructions
- [ ] API documentation generated (OpenAPI/Swagger)
- [ ] Architecture diagram exists
- [ ] Deployment guide exists
- [ ] Runbook exists (incident response procedures)
- [ ] Configuration documentation complete

### Disaster Recovery
- [ ] E-STOP / emergency shutdown tested
- [ ] Rollback procedure tested
- [ ] RPO/RTO defined and achievable
- [ ] Multi-region failover (if required)
- [ ] Contact escalation list updated

---

# PART 3: TESTING WORKFLOW INTEGRATION

## 🔄 When to Run Which Tests

### On Every Commit (Pre-Commit Hook)
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Fast tests only (<30 seconds)
pytest tests/unit/ -v --tb=short
pytest tests/security/test_secrets_scan.py -v
pytest tests/quality/test_no_placeholder_tests.py -v

# Linting
flake8 src/ tests/
black --check src/ tests/

# If any fail, block commit
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit blocked."
    exit 1
fi
```

### On Every Pull Request (CI Pipeline)
```yaml
# .github/workflows/ci.yml
name: CI Tests

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run all tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml
          
      - name: Check coverage minimums
        run: |
          pytest tests/meta/test_coverage_minimums.py
          
      - name: Security tests
        run: |
          pytest tests/security/ -v
          
      - name: Integration tests
        run: |
          pytest tests/integration/ -v
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Nightly (Full Test Suite + Chaos)
```bash
#!/bin/bash
# Cron: 0 2 * * * (2 AM daily)

# Full test suite
pytest tests/ -v --cov=src --cov-report=html

# Chaos testing
pytest tests/chaos/ -v

# Load testing
locust -f tests/load/locustfile.py --headless -u 100 -r 10 --run-time 5m

# Generate report
pytest tests/ --html=reports/nightly_$(date +%Y%m%d).html
```

### Before Production Deploy (Manual Gate)
```bash
#!/bin/bash
# Must pass before deployment allowed

# Run production readiness checklist
python scripts/verify_production_readiness.py

# Run critical path tests
pytest tests/critical/ -v

# Smoke test in staging
pytest tests/smoke/ --base-url=https://staging.example.com

# Manual approval required
echo "Review test results and approve deployment? (yes/no)"
read approval
if [ "$approval" != "yes" ]; then
    exit 1
fi
```

---

# PART 4: COST & RESOURCE CONTROLS

**Source:** Production-Ready Patterns (Luxury Car → Race Car transformation)

## 💰 Budget Discipline

**Problem:** $50 budget spent $45 on overhead, $5 on actual work

**Solution:**

### Mandatory Resource Allocation

| Category | Minimum % | Maximum % | Purpose |
|----------|-----------|-----------|---------|
| Code Generation | 60% | 70% | Actual feature development |
| Testing | 15% | 20% | Quality assurance |
| Orchestration | 10% | 15% | Coordination overhead |
| Infrastructure | 5% | 10% | Monitoring, logging, etc. |

**Enforcement Tests:**

```python
def test_budget_allocation_compliance():
    """Verify budget spent according to allocation rules"""
    
    # Load spending data from last sprint
    spending = get_spending_data(sprint_id='current')
    
    total = spending['total']
    code_gen = spending['code_generation']
    testing = spending['testing']
    orchestration = spending['orchestration']
    infra = spending['infrastructure']
    
    # Verify minimums
    assert code_gen >= 0.60 * total, "Code generation below 60% minimum"
    assert testing >= 0.15 * total, "Testing below 15% minimum"
    
    # Verify maximums
    assert orchestration <= 0.15 * total, "Orchestration exceeds 15% maximum"
    assert infra <= 0.10 * total, "Infrastructure exceeds 10% maximum"

def test_no_idle_resource_waste():
    """Verify resources cleaned up when idle"""
    
    # Spawn worker
    worker_id = spawn_worker()
    
    # Wait for idle timeout (5 minutes)
    time.sleep(310)
    
    # Verify worker was automatically cleaned up
    assert not is_worker_running(worker_id), "Idle worker not cleaned up"

def test_exponential_backoff_polling():
    """Verify polling backs off when idle"""
    
    orchestrator = Orchestrator()
    
    # Initial poll interval
    assert orchestrator.poll_interval == 30  # 30 seconds
    
    # After 5 idle polls, should increase
    for _ in range(5):
        orchestrator.poll()
    
    assert orchestrator.poll_interval == 60  # Doubled
    
    # After 10 more, should increase again
    for _ in range(10):
        orchestrator.poll()
    
    assert orchestrator.poll_interval >= 120  # Further increase
```

---

# PART 5: AI AGENT TESTING PROTOCOLS

**Source:** Master Orchestrator Protocol + Orchestrator Playbook

## 🤖 Testing AI Agent Behavior

### 5.1 Deterministic Output Verification

**Mandatory Tests:**

```python
def test_ai_output_determinism():
    """Verify AI produces same output for same input (when using temperature=0)"""
    
    prompt = "Generate a function to calculate Fibonacci numbers"
    
    # Run 3 times
    outputs = [ai_agent.generate(prompt, temperature=0) for _ in range(3)]
    
    # All outputs should be identical
    assert outputs[0] == outputs[1] == outputs[2], \
        "AI output not deterministic at temperature=0"

def test_ai_respects_constraints():
    """Verify AI follows explicit constraints"""
    
    constraints = {
        'max_length': 100,
        'language': 'Python',
        'no_external_libraries': True
    }
    
    code = ai_agent.generate_code(prompt="Sort a list", constraints=constraints)
    
    # Verify constraints
    assert len(code) <= 100, "Code exceeds max length"
    assert 'import' not in code, "Code uses external libraries despite constraint"
    assert 'def ' in code, "Not valid Python function"
```

---

### 5.2 Blueprint Adherence Testing

**Mandatory Tests:**

```python
def test_ai_follows_blueprint():
    """Verify AI doesn't hallucinate features not in blueprint"""
    
    blueprint = load_blueprint()
    in_scope = blueprint['in_scope_features']
    out_of_scope = blueprint['out_of_scope_features']
    
    # AI generates implementation
    code = ai_agent.implement_from_blueprint(blueprint)
    
    # Verify in-scope features are implemented
    for feature in in_scope:
        assert feature_implemented_in_code(code, feature), \
            f"In-scope feature '{feature}' not implemented"
    
    # Verify out-of-scope features are NOT implemented
    for feature in out_of_scope:
        assert not feature_implemented_in_code(code, feature), \
            f"Out-of-scope feature '{feature}' was hallucinated"

def test_ai_gap_detection():
    """Verify AI flags blueprint gaps before coding"""
    
    incomplete_blueprint = {
        'features': ['user login'],
        # Missing: database choice, auth strategy, etc.
    }
    
    gaps = ai_agent.detect_blueprint_gaps(incomplete_blueprint)
    
    # Verify AI detected missing critical sections
    assert 'database_choice' in gaps, "AI didn't flag missing database choice"
    assert 'authentication_strategy' in gaps, "AI didn't flag missing auth strategy"
    assert len(gaps) >= 5, "AI should find minimum 5 gaps in incomplete blueprint"
```

---

### 5.3 Human-in-the-Loop Validation

**Mandatory Tests:**

```python
def test_tier3_operations_require_human_approval():
    """Verify destructive operations require human approval"""
    
    # Try destructive operation without approval
    with pytest.raises(HumanApprovalRequired):
        ai_agent.execute_command("DROP TABLE users")
    
    # Provide approval
    approval_token = human_approves(operation="DROP TABLE users", reason="Test cleanup")
    
    # Now it should work
    result = ai_agent.execute_command("DROP TABLE users", approval=approval_token)
    assert result.status == 'success'

def test_ai_requests_clarification_when_ambiguous():
    """Verify AI asks for clarification instead of guessing"""
    
    ambiguous_task = "Make the button blue"  # Which button?
    
    response = ai_agent.execute_task(ambiguous_task)
    
    # AI should request clarification
    assert response.status == 'clarification_needed'
    assert 'which button' in response.message.lower()
```

---

# PART 6: TESTING ANTI-PATTERNS TO AVOID

## ❌ What NOT To Do

### Anti-Pattern 1: Test-After-the-Fact
```python
# ❌ BAD - Writing tests after code is done
def implement_feature():
    # ... 200 lines of code ...
    pass

def test_feature():  # Written 3 days later
    assert True  # Placeholder
```

**✅ CORRECT - TDD Approach:**
```python
# Write test first
def test_user_can_login():
    response = client.post('/login', json={'username': 'test', 'password': 'pass'})
    assert response.status_code == 200
    assert 'token' in response.json()

# Then implement
def login():
    # ... implementation guided by test
    pass
```

---

### Anti-Pattern 2: Integration Tests Without Unit Tests
```python
# ❌ BAD - Only testing full stack, no unit tests
def test_entire_application():
    # Login
    response1 = client.post('/login', ...)
    # Create project
    response2 = client.post('/api/projects', ...)
    # Update project
    response3 = client.put('/api/projects/1', ...)
    # ... 50 more lines ...
```

**✅ CORRECT - Test Pyramid:**
```python
# Many unit tests (fast, isolated)
def test_hash_password():
    hashed = hash_password('mypassword')
    assert len(hashed) == 60  # bcrypt length
    assert hashed != 'mypassword'

def test_verify_password():
    hashed = hash_password('mypassword')
    assert verify_password('mypassword', hashed) == True
    assert verify_password('wrongpassword', hashed) == False

# Few integration tests (slower, end-to-end)
def test_login_flow():
    response = client.post('/login', json={'username': 'test', 'password': 'pass'})
    assert response.status_code == 200
```

---

### Anti-Pattern 3: Mocking Everything
```python
# ❌ BAD - Over-mocking makes test meaningless
def test_data_processing():
    with mock.patch('data_loader.load') as mock_load:
        with mock.patch('data_processor.process') as mock_process:
            with mock.patch('data_saver.save') as mock_save:
                mock_load.return_value = 'fake_data'
                mock_process.return_value = 'fake_result'
                mock_save.return_value = True
                
                result = full_pipeline()
                assert result == True  # What did we actually test?
```

**✅ CORRECT - Mock Only External Dependencies:**
```python
# Mock external API, test real internal logic
def test_data_processing():
    with mock.patch('requests.get') as mock_api:
        mock_api.return_value.json.return_value = {'data': [1, 2, 3]}
        
        # Real data loader, processor, saver
        result = full_pipeline()
        
        # Verify real business logic executed correctly
        assert result['processed_count'] == 3
        assert result['status'] == 'success'
```

---

### Anti-Pattern 4: Tests That Depend on Execution Order
```python
# ❌ BAD - test_b depends on test_a running first
def test_a_create_user():
    db.create_user('testuser')

def test_b_update_user():
    db.update_user('testuser', email='new@example.com')  # Breaks if test_a didn't run
```

**✅ CORRECT - Independent Tests:**
```python
@pytest.fixture
def test_user():
    user = db.create_user('testuser')
    yield user
    db.delete_user('testuser')

def test_create_user():
    user = db.create_user('newuser')
    assert user.username == 'newuser'
    db.delete_user('newuser')

def test_update_user(test_user):
    db.update_user(test_user.id, email='new@example.com')
    updated = db.get_user(test_user.id)
    assert updated.email == 'new@example.com'
```

---

# PART 7: QUALITY GATES & ENFORCEMENT

## 🚦 Automated Quality Gates

### Gate 1: Pre-Commit (Local)
```bash
# Block commit if any of these fail:
- pytest tests/unit/ (unit tests)
- pytest tests/security/test_secrets_scan.py (no hardcoded secrets)
- flake8 src/ (code quality)
- black --check src/ (formatting)
```

### Gate 2: Pre-Merge (CI)
```yaml
# Block PR merge if any of these fail:
- All tests pass (unit + integration + security)
- Coverage >= minimums (core 90%, API 80%, auth 100%)
- No placeholder tests detected
- No cognitive habit violations
- Security scan passes (OWASP ZAP)
```

### Gate 3: Pre-Deploy (Manual)
```bash
# Human must verify:
- Production readiness checklist complete (42 items)
- Load testing passed (100 concurrent users)
- Chaos testing passed (12 scenarios)
- Backup restoration tested in last 30 days
- Deployment runbook reviewed
```

---

# PART 8: CONTINUOUS IMPROVEMENT

## 📈 Testing Metrics to Track

### Weekly
- Test coverage % (by component)
- Test execution time (keep under 5 min for unit tests)
- Flaky test count (tests that fail randomly)
- False positive tests detected and removed

### Monthly
- Escaped defects (bugs found in production, not caught by tests)
- Test effectiveness (defects caught in testing vs production)
- Testing ROI (time saved by catching bugs early)
- Cognitive habit violation frequency

### Quarterly
- Full chaos testing suite
- Load testing with increasing user counts
- Security penetration testing
- Disaster recovery drill

---

# APPENDIX A: TESTING TOOLS RECOMMENDATIONS

## 🛠️ Recommended Tech Stack

### Python Projects
- **Unit Testing:** pytest
- **Coverage:** pytest-cov
- **Mocking:** pytest-mock, responses
- **Security:** bandit, safety
- **Code Quality:** flake8, black, mypy
- **Load Testing:** locust
- **Chaos:** chaostoolkit

### JavaScript/TypeScript Projects
- **Unit Testing:** Jest, Vitest
- **E2E Testing:** Playwright, Cypress
- **Coverage:** istanbul/nyc
- **Security:** npm audit, snyk
- **Code Quality:** ESLint, Prettier, TypeScript
- **Load Testing:** k6, Artillery

### Database Testing
- **Python:** pytest-postgresql, pytest-mysql
- **Migrations:** Alembic (Python), Flyway (Java)
- **Data Validation:** Great Expectations, Soda

### API Testing
- **Contract Testing:** Pact, Dredd
- **Security:** OWASP ZAP, Burp Suite
- **Performance:** JMeter, Gatling
- **Functional:** Postman, REST-assured

---

# APPENDIX B: GLOSSARY

| Term | Definition |
|------|------------|
| **SYSTEMIC Pattern** | Failure pattern appearing in 3+ out of 4 projects |
| **HARDWIRED Pattern** | Failure pattern appearing in ALL projects (AI default behavior) |
| **Cognitive Habit** | AI's tendency to make the same mistake repeatedly |
| **Silent Failure** | Error that occurs but doesn't surface (logged but execution continues) |
| **Placeholder Test** | Test that exists but doesn't verify meaningful behavior (assert True) |
| **Integration Gap** | Module A and B tested separately but A→B flow never tested |
| **False Test** | Test that appears to pass but doesn't actually validate correctness |
| **Tier 1-3 Decision** | Orchestrator decision classification (T1=auto, T2=flag, T3=block) |

---

# APPENDIX C: TESTING MATURITY MODEL

## Level 0: No Testing (❌ Production Risk)
- Zero automated tests
- Manual testing only
- No quality gates
- **Risk:** Silent failures, regression, security vulnerabilities

## Level 1: Basic Unit Tests (⚠️ Partial Coverage)
- Some unit tests exist
- Coverage 20-40%
- No integration tests
- **Risk:** Integration failures, false confidence

## Level 2: Comprehensive Testing (✅ Standard)
- Unit + integration tests
- Coverage 60-80%
- CI/CD with quality gates
- **Risk:** Edge cases, chaos scenarios untested

## Level 3: Production-Grade (✅ Recommended)
- Unit + integration + security + chaos
- Coverage 80-95%
- Automated quality gates
- Regular load testing
- **Risk:** Minimal, expected for production systems

## Level 4: AI-Resilient (🏆 Advanced)
- All Level 3 +
- Cognitive habit detection
- Behavioral drift monitoring
- Human-in-the-loop validation
- False test detection
- **Risk:** Extremely low, suitable for critical systems

---

# FINAL CHECKLIST: IS MY PROJECT PRODUCTION-READY?

## ✅ Tier 1 (Mandatory) - Must Have ALL
- [ ] Zero silent error swallowing (bare except blocks)
- [ ] Zero hardcoded secrets in codebase
- [ ] Test coverage meets minimums (core 90%, API 80%, auth 100%)
- [ ] All configuration externalized
- [ ] Cross-module integration tests exist for all data flows

## ✅ Tier 2 (Structural) - Must Have 80%+
- [ ] Concurrency/race condition testing
- [ ] Resource exhaustion testing
- [ ] Chaos/failure injection testing
- [ ] Security testing (XSS, SQL injection, CSRF)
- [ ] Performance/load testing

## ✅ Tier 3 (Behavioral) - Must Have 60%+
- [ ] Cognitive habit violation detection
- [ ] Behavioral drift monitoring
- [ ] Explainability/decision logging
- [ ] Human override mechanisms
- [ ] False test detection

## 🎯 Production Readiness Score

Calculate your score:

```
Score = (Tier 1 % × 0.5) + (Tier 2 % × 0.3) + (Tier 3 % × 0.2)

90-100%: PRODUCTION-GRADE ✅ Deploy confidently
80-89%:  STRONG ✅ Minor gaps, deploy with monitoring
70-79%:  ADEQUATE ⚠️ Fix Tier 1 gaps before production
60-69%:  WEAK ⚠️ Significant risk, delay deployment
<60%:    REJECTED ❌ Not ready for production
```

---

**END OF STANDARD**

**Version:** 1.0  
**Status:** PRODUCTION-READY  
**Last Updated:** 2026-02-15  
**Next Review:** After 3 production deployments using this standard  

**Usage:** Copy this standard to your project as `TESTING_STANDARD.md` and implement the 3-tier testing pyramid. Update your CI/CD to enforce quality gates. Review quarterly and update based on new failure patterns discovered.

**Feedback:** This is a living document. As you discover new failure patterns, add them to the appropriate tier and update the Forensic Codex.
