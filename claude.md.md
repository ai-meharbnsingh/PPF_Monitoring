# UNIVERSAL DEVELOPMENT RULES
**A Comprehensive Benchmark for Any Software Project**

> **Purpose:** This document defines mandatory development standards applicable to web applications, IoT devices, mobile apps, enterprise systems, and any software project.
> 
> **Status:** Living Document - Update as project evolves
> 
> **Last Updated:** 2026-02-21

---

## 📋 TABLE OF CONTENTS

1. [Core Principles](#core-principles)
2. [File Organization & Structure](#file-organization--structure)
3. [Documentation Standards](#documentation-standards)
4. [Code Quality & Standards](#code-quality--standards)
5. [Configuration Management](#configuration-management)
6. [Database & Data Management](#database--data-management)
7. [Testing Requirements](#testing-requirements)
8. [Security & Privacy](#security--privacy)
9. [Version Control & Git](#version-control--git)
10. [Session & Progress Tracking](#session--progress-tracking)
11. [Error Handling & Logging](#error-handling--logging)
12. [Development Workflow](#development-workflow)
13. [Deployment & Production](#deployment--production)
14. [Platform-Specific Rules](#platform-specific-rules)

---

## 🎯 CORE PRINCIPLES

### Principle 1: Documentation First, Code Second
- ✅ **ALWAYS** update documentation BEFORE writing code
- ✅ **ALWAYS** update progress tracking AFTER completing tasks
- ✅ **NEVER** skip documentation updates
- ✅ **NEVER** proceed without updating status

### Principle 2: Track Everything
- ✅ Log all decisions to learnings database/journal
- ✅ Track all provider/API usage and costs
- ✅ Record all user preferences
- ✅ Maintain audit trail for all changes
- ✅ Document WHY decisions were made, not just WHAT

### Principle 3: Zero Clutter Policy
- ✅ Every file has a designated location
- ✅ No files at project root (except approved files)
- ✅ Clean separation of concerns
- ✅ Temporary files deleted after use

### Principle 4: Fail-Fast Over Fail-Silent
- ✅ Stop and report structural conflicts immediately
- ✅ Never hide errors with empty catch blocks
- ✅ Log all errors with context
- ✅ Explicit error messages over silent failures

### Principle 5: Configuration Over Code
- ✅ All configurable values in config files
- ✅ No hardcoded values in source code
- ✅ Feature flags for all new features (default: disabled)
- ✅ Environment-specific configurations

### Principle 6: 80% Done > 100% Planned
- ✅ Ship working MVP, iterate
- ✅ Working code beats perfect documentation
- ✅ But NEVER skip essential documentation
- ✅ Progressive refinement over perfection

---

## 📁 FILE ORGANIZATION & STRUCTURE

### Root Folder Rules

**Root folder MUST ONLY contain:**
- `README.md` - Project overview
- `requirements.txt` / `package.json` - Dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Git exclusions
- `CHANGELOG.md` - Project changelog
- Launch scripts (`start.bat`, `launch.sh`, etc.)
- **FOLDERS ONLY** (no other files)

**NEVER create at root:**
- ❌ Status files (`STATUS.md`, `TODO.md`)
- ❌ Test files (`test.py`, `debug.js`)
- ❌ Temporary files (`temp.txt`, `scratch.md`)
- ❌ Bug reports (`BUG_FIX.md`, `ISSUES.md`)

### Standard Directory Structure

```
project-name/
├── src/                          # Source code
│   ├── api/                      # API endpoints/routes
│   ├── services/                 # Business logic
│   ├── models/                   # Data models
│   ├── utils/                    # Utility functions
│   ├── config/                   # Configuration loaders
│   └── shared/                   # Shared/common code
├── tests/                        # All test files
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── e2e/                      # End-to-end tests
│   └── fixtures/                 # Test fixtures/mocks
├── docs/                         # Documentation
│   ├── architecture/             # Architecture diagrams, ADRs
│   ├── api/                      # API documentation
│   ├── guides/                   # User/developer guides
│   ├── specs/                    # Technical specifications
│   └── archive/                  # Outdated/superseded docs
├── config/                       # Configuration files
│   ├── dev/                      # Development configs
│   ├── staging/                  # Staging configs
│   ├── production/               # Production configs
│   └── settings.yaml             # Main configuration
├── database/                     # Database files (if applicable)
│   ├── migrations/               # Database migrations
│   ├── seeds/                    # Seed data
│   └── backups/                  # Auto-generated backups
├── scripts/                      # Utility scripts
│   ├── setup/                    # Setup/installation scripts
│   ├── deployment/               # Deployment scripts
│   └── maintenance/              # Maintenance tasks
├── logs/                         # Log files (gitignored)
├── data/                         # Runtime data (gitignored)
│   ├── uploads/                  # User uploads
│   ├── exports/                  # Generated exports
│   └── cache/                    # Cache files
├── public/                       # Static assets (web apps)
│   ├── images/
│   ├── css/
│   └── js/
└── tools/                        # Development tools
    ├── cli/                      # CLI utilities
    └── generators/               # Code generators
```

### Folder Creation Rules

When creating a new folder:
- **Python packages** → Create `__init__.py` inside
- **Data/log folders** → Create `.gitkeep` inside
- **Never** create folders named "New folder" or leave unnamed
- **Document** the folder's purpose in `PROJECT_STRUCTURE.md`

---

## 📚 DOCUMENTATION STANDARDS

### Mandatory Documentation Files

| File | Location | Purpose | When to Update |
|------|----------|---------|----------------|
| `README.md` | Root | Project overview, quick start | When setup changes |
| `CHANGELOG.md` | Root | All changes with dates | EVERY change |
| `PROJECT_STRUCTURE.md` | Root or `/docs/` | File organization guide | When structure changes |
| `ARCHITECTURE.md` | `/docs/architecture/` | System architecture | Major design changes |
| `API_DOCUMENTATION.md` | `/docs/api/` | API endpoints, usage | API changes |
| `DEPLOYMENT_GUIDE.md` | `/docs/guides/` | Deployment steps | Deployment process changes |
| `LEARNINGS.md` | `/docs/` | Lessons learned | After each phase/milestone |

### Documentation Principles

**DO:**
- ✅ Keep docs simple and accessible to non-technical stakeholders
- ✅ Use flowcharts, diagrams, and tables
- ✅ Explain WHAT and WHY, not HOW (code is the HOW)
- ✅ Update docs when user explicitly requests
- ✅ Show findings in chat first, ask before creating files
- ✅ Include examples and use cases
- ✅ Version your documentation

**DON'T:**
- ❌ Include code snippets in documentation (code becomes outdated)
- ❌ Create documentation files proactively without user request
- ❌ Duplicate information across multiple docs
- ❌ Leave outdated documentation (move to `/archive/`)
- ❌ Write vague descriptions ("fix stuff", "updates")

### CHANGELOG.md Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Added
- New feature description

### Changed
- Change description with reason

### Fixed
- Bug fix description

### Removed
- Removed feature with reason

## [YYYY-MM-DD] - Version X.Y.Z
### Added
- Feature 1: Description and reason
- Feature 2: Description and reason

### Changed
- Change 1: What changed and why

### Fixed
- Bug 1: What was broken and how it was fixed

### Security
- Security fix description
```

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Documentation files | `UPPERCASE_WITH_UNDERSCORES.md` | `DEPLOYMENT_GUIDE.md` |
| Code files | `snake_case.py` / `camelCase.js` | `user_service.py`, `userService.js` |
| Classes | `PascalCase` | `UserController` |
| Functions/methods | `snake_case` / `camelCase` | `get_user_by_id()`, `getUserById()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `API_TIMEOUT` |
| Test files | `test_<module>.<ext>` | `test_user_service.py` |
| Config files | `lowercase-with-dashes.yaml` | `app-config.yaml` |

---

## 💻 CODE QUALITY & STANDARDS

### General Code Standards

1. **Type Hints (Python) / TypeScript**
   - All public methods have type hints
   - All function parameters typed
   - Return types specified

2. **Docstrings / Comments**
   - All public functions have docstrings
   - Complex logic explained with inline comments
   - No obvious comments ("increment i by 1")

3. **Single Responsibility Principle**
   - One file = one responsibility
   - Functions do ONE thing well
   - Classes have single, clear purpose

4. **DRY (Don't Repeat Yourself)**
   - Extract repeated code into functions
   - Use configuration for repeated values
   - Share common utilities

5. **Meaningful Names**
   - Variables describe their content
   - Functions describe their action
   - No single-letter names except loop counters

### Code Review Checklist

Before committing code:
- [ ] All code compile-checked / linted
- [ ] No hardcoded values (check config files)
- [ ] Proper error handling (no bare except/catch)
- [ ] All new functions have tests
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No debug statements left in code
- [ ] No TODO comments in production code

### Module Documentation Template

```python
"""
Module Name: [Brief description]

Purpose:
    [Detailed explanation of module purpose]

Dependencies:
    External:
        - package_name >= version (purpose)
    Internal:
        - module.submodule (purpose)

Configuration:
    Required config keys:
        - config.section.key (purpose)

Breaking Changes:
    - vX.X.X (YYYY-MM-DD): Description of breaking change

Author: [Name/Team]
Created: YYYY-MM-DD
Last Updated: YYYY-MM-DD
"""
```

---

## ⚙️ CONFIGURATION MANAGEMENT

### Configuration Hierarchy

**Priority Order (highest to lowest):**
1. Environment variables (`.env`)
2. Runtime arguments
3. Configuration files (`config/*.yaml`)
4. Default values in code

### NO Hardcoded Values Rule

**NEVER hardcode:**
- ❌ API endpoints
- ❌ File paths
- ❌ Database connection strings
- ❌ Thresholds, limits, ratios
- ❌ Feature flags
- ❌ Port numbers
- ❌ Timeouts, retry counts
- ❌ Model parameters

**Examples:**

```python
# ❌ WRONG
if position_size > 10000:
    raise ValueError("Position too large")

db_path = "C:/Projects/data/db.sqlite"
api_url = "https://api.example.com/v1"

# ✅ CORRECT
if position_size > config['risk']['max_position_size']:
    raise ValueError("Position too large")

db_path = config['database']['path']
api_url = config['api']['base_url']
```

### Configuration File Structure

**`config/settings.yaml`:**
```yaml
# Application Settings
app:
  name: "Project Name"
  version: "1.0.0"
  environment: "development"  # development, staging, production
  debug: true

# Server Configuration
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  timeout: 30

# Database Configuration
database:
  type: "sqlite"  # sqlite, postgresql, mysql
  path: "data/app.db"
  backup_path: "data/backups"
  connection_pool_size: 10

# API Configuration
api:
  base_url: "https://api.example.com"
  timeout: 30
  retry_attempts: 3
  rate_limit: 100  # requests per minute

# Feature Flags
features:
  new_feature_name:
    enabled: false
    description: "Description of feature"
    rollout_percentage: 0  # 0-100

# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "logs/app.log"
  max_file_size_mb: 10
  backup_count: 5

# Security
security:
  secret_key_env_var: "APP_SECRET_KEY"
  token_expiry_hours: 24
  max_login_attempts: 5
```

### Environment Variables (.env)

**`.env.example`:**
```bash
# API Keys (NEVER commit actual values)
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# External Services
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password_here

# Feature Flags (optional overrides)
ENABLE_FEATURE_X=false

# Environment
ENVIRONMENT=development
DEBUG=true
```

**Rules:**
- ✅ Commit `.env.example` with placeholder values
- ❌ NEVER commit `.env` with actual values
- ✅ Document all environment variables in README
- ✅ Use descriptive variable names
- ✅ Group related variables together

---

## 🗄️ DATABASE & DATA MANAGEMENT

### Database Standards

1. **Schema Documentation**
   - Document all tables, columns, relationships
   - Include sample data examples
   - Document all indexes, constraints

2. **Migration Strategy**
   - All schema changes via migration files
   - Never modify production DB manually
   - Reversible migrations (up/down scripts)
   - Version-controlled migration files

3. **Backup Protocol**
   - Automated backups (daily minimum)
   - Backup before schema changes
   - Store backups in separate location
   - Test restore procedures regularly

4. **Data Integrity**
   - Foreign key constraints enabled
   - NOT NULL for required fields
   - Unique constraints where applicable
   - Check constraints for valid ranges

### Database Synchronization Rules

**MANDATORY:** When modifying database schema:

1. ✅ Modify production database
2. ✅ Update schema SQL file immediately
3. ✅ Update database documentation
4. ✅ Update CHANGELOG.md
5. ✅ Increment schema version
6. ✅ Test migration on staging first

**Never:**
- ❌ Modify production without updating SQL file
- ❌ Manual changes without migration script
- ❌ Delete data without backup

### Data Validation

**Use schema validation (Pydantic, Joi, etc.):**

```python
# Python with Pydantic
from pydantic import BaseModel, Field

class UserSchema(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)

# Validate before processing
def create_user(data: dict):
    try:
        validated_data = UserSchema(**data)
        # Process validated data
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        return None
```

---

## 🧪 TESTING REQUIREMENTS

### Test Coverage Standards

**Minimum Requirements:**
- **Unit Tests:** 80% code coverage
- **Integration Tests:** All critical paths
- **E2E Tests:** All user workflows

### Testing Hierarchy

```
┌─────────────────────────────────────┐
│         E2E Tests (Slow)            │  ← Test full user workflows
│  Test entire system end-to-end     │
├─────────────────────────────────────┤
│    Integration Tests (Medium)       │  ← Test module interactions
│  Test component interactions        │
├─────────────────────────────────────┤
│      Unit Tests (Fast)              │  ← Test individual functions
│  Test single functions/methods      │
└─────────────────────────────────────┘
```

### Testing Rules

**MANDATORY:**
1. Every new public method → at least one unit test
2. Critical path functions → comprehensive test suite
3. All tests must pass before commit
4. Tests use fixtures/mocks for external dependencies
5. Tests must be deterministic (no random failures)

**Test File Organization:**
```
tests/
├── unit/
│   ├── test_user_service.py
│   ├── test_auth_service.py
│   └── test_utils.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_database_operations.py
├── e2e/
│   ├── test_user_registration_flow.py
│   └── test_purchase_flow.py
├── fixtures/
│   ├── user_fixtures.py
│   └── database_fixtures.py
└── conftest.py  # Pytest configuration
```

### Test Naming Convention

```python
# Format: test_<function>_<scenario>_<expected_result>

def test_calculate_discount_with_valid_coupon_returns_discounted_price():
    pass

def test_calculate_discount_with_expired_coupon_raises_error():
    pass

def test_calculate_discount_with_invalid_coupon_returns_original_price():
    pass
```

### Before Deployment Testing Checklist

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Performance tests (if applicable)
- [ ] Security tests (penetration testing)
- [ ] Load tests (stress testing)
- [ ] Browser compatibility tests (web apps)
- [ ] Device compatibility tests (mobile apps)

---

## 🔒 SECURITY & PRIVACY

### Secrets Management

**NEVER store in code/config:**
- ❌ API keys
- ❌ Passwords
- ❌ Access tokens
- ❌ Private keys
- ❌ Database credentials
- ❌ Encryption keys

**ALWAYS use:**
- ✅ Environment variables (`.env`)
- ✅ Secure vaults (HashiCorp Vault, AWS Secrets Manager)
- ✅ OS keyring (for desktop apps)
- ✅ Encrypted configuration files

**Environment Variable Rules:**
```bash
# ✅ CORRECT naming
DATABASE_PASSWORD=secret123
API_KEY=abc123xyz

# ❌ WRONG - obvious dummy values
DATABASE_PASSWORD=your_password_here
API_KEY=placeholder
```

### Privacy Rules

**NEVER commit to version control:**
- ❌ `.env` files
- ❌ `*_PRIVATE.md` files
- ❌ Medical/health data
- ❌ Financial records
- ❌ Personal information (PII)
- ❌ Authentication tokens
- ❌ SSL certificates/private keys

**Required in `.gitignore`:**
```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Private files
*_PRIVATE.md
*.secret
credentials*

# Sensitive data directories
health_data/
medical_records/
financial_records/
user_data/

# Keys and certificates
*.pem
*.key
*.p12
*.pfx

# Database files
*.db
*.sqlite
*.sqlite3

# Logs (may contain sensitive info)
logs/
*.log
```

### Security Checklist

**Application Security:**
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection
- [ ] Authentication & authorization implemented
- [ ] Password hashing (bcrypt, argon2)
- [ ] Rate limiting on APIs
- [ ] HTTPS enforced in production
- [ ] Security headers configured

**Data Security:**
- [ ] Encryption at rest for sensitive data
- [ ] Encryption in transit (TLS/SSL)
- [ ] Regular security audits
- [ ] Dependency vulnerability scanning
- [ ] Access logs maintained
- [ ] Data backup encryption

---

## 📝 VERSION CONTROL & GIT

### Git Commit Standards

**Format:** `[MODULE] Action: Brief description`

**Module Tags:**
- `[FEATURE]` - New feature
- `[FIX]` - Bug fix
- `[REFACTOR]` - Code restructuring
- `[DOCS]` - Documentation only
- `[TEST]` - Test addition/modification
- `[STYLE]` - Code formatting
- `[PERF]` - Performance improvement
- `[SECURITY]` - Security fix
- `[CONFIG]` - Configuration change
- `[DATABASE]` - Database changes
- `[DEPS]` - Dependency updates

**Action Verbs:**
- `Add` - New functionality
- `Update` - Modify existing
- `Fix` - Bug fixes
- `Remove` - Delete code/features
- `Refactor` - Code restructure
- `Optimize` - Performance improvements

**Examples:**
```bash
✅ GOOD:
[FEATURE] Add: User authentication with JWT tokens
[FIX] Fix: Null pointer exception in payment processing
[REFACTOR] Refactor: Extract validation logic to separate module
[DOCS] Update: API documentation for new endpoints
[SECURITY] Fix: SQL injection vulnerability in search feature

❌ BAD:
"Fixed stuff"
"Updates"
"WIP"
"asdfasdf"
```

### Branching Strategy

**Git Flow:**
```
main (production)
  ↓
develop (integration)
  ↓
feature/feature-name (individual features)
hotfix/issue-name (emergency fixes)
release/version-number (release prep)
```

**Branch Naming:**
```bash
feature/user-authentication
feature/payment-integration
bugfix/login-error
hotfix/critical-security-patch
release/v1.2.0
```

### What to Commit

**✅ COMMIT:**
- Source code
- Configuration templates (`.env.example`)
- Documentation
- Tests
- Build scripts
- Schema files
- Migration files
- Requirements/dependencies

**❌ DON'T COMMIT:**
- `.env` files with secrets
- Database files
- Log files
- Cache files
- Build artifacts
- `node_modules/`, `venv/`, `__pycache__/`
- IDE-specific files (`.idea/`, `.vscode/`)
- OS-specific files (`.DS_Store`, `Thumbs.db`)

### Pre-Commit Checklist

Before `git commit`:
- [ ] All tests passing
- [ ] Code linted/formatted
- [ ] No debug statements
- [ ] No hardcoded values
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] No secrets in files
- [ ] `.gitignore` up to date

### Pre-Push Checklist

Before `git push`:
- [ ] All commits have meaningful messages
- [ ] No WIP commits
- [ ] Database schema synchronized
- [ ] No merge conflicts
- [ ] Branch up to date with base
- [ ] CI/CD pipeline will pass

---

## 📊 SESSION & PROGRESS TRACKING

### Session Logging System

**Purpose:** Track every development session for audit, learning, and continuity.

**Implementation:**

```python
# Create session at start of work
from session_logger import SessionLogger

session = SessionLogger.new_session(
    phase="Phase 2",
    description="Implementing user authentication"
)

# Log significant events
session.log("user", "Build login endpoint with JWT")
session.log("claude", "Created auth_service.py with JWT implementation")
session.log("user", "Add password reset functionality")
session.log("claude", "Added password reset with email verification")

# Close session with summary
session.close("Completed user authentication module with login, logout, and password reset")
```

**Session Database Schema:**
```sql
CREATE TABLE session_meta (
    session_id TEXT PRIMARY KEY,
    phase TEXT,
    description TEXT,
    started_at TIMESTAMP,
    last_updated TIMESTAMP,
    summary TEXT
);

CREATE TABLE session_messages (
    message_id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,  -- 'user' or 'assistant'
    content TEXT,
    summary TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session_meta(session_id)
);
```

### Progress Tracking Format

**Master Plan Format:**

```markdown
# PROJECT MASTER PLAN

## Overview
**Project:** [Name]
**Version:** [X.Y.Z]
**Started:** YYYY-MM-DD
**Current Phase:** [Phase Name]

## Phase Progress

### ✅ PHASE 1: Foundation (Week 1) - COMPLETE
**Status:** ✅ 100% Complete
**Completed:** 2026-02-15

Tasks:
- ✅ Project scaffolding
- ✅ Database setup
- ✅ Configuration system
- ✅ Logging framework

### 🟡 PHASE 2: Core Features (Week 2) - IN PROGRESS
**Status:** 🟡 60% Complete
**Started:** 2026-02-16
**Current Task:** User authentication

Tasks:
- ✅ User registration
- ✅ Login endpoint
- 🟡 Password reset (IN PROGRESS)
- ❌ Email verification (NOT STARTED)
- ❌ OAuth integration (NOT STARTED)

### ⚪ PHASE 3: Advanced Features (Week 3) - PENDING
**Status:** ⚪ Not Started

Tasks:
- ❌ Payment integration
- ❌ Notification system
- ❌ Analytics dashboard

## Legend
- ✅ = Complete
- 🟡 = In Progress
- ❌ = Not Started (planned)
- ⚪ = Pending (future phase)
```

### Learnings Database

**Track:**
- Decisions made and why
- Mistakes and how they were fixed
- Performance optimizations
- User preferences
- API usage and costs

**Schema:**
```sql
CREATE TABLE learnings (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP,
    event_type TEXT,  -- 'decision', 'error', 'optimization', 'preference'
    category TEXT,    -- 'architecture', 'performance', 'security', etc.
    description TEXT,
    outcome TEXT,     -- 'success', 'failure', 'partial'
    metadata JSON
);
```

---

## ⚠️ ERROR HANDLING & LOGGING

### Error Handling Standards

**NEVER use bare except/catch:**

```python
# ❌ WRONG
try:
    process_data()
except:
    pass  # Silent failure - BANNED

# ✅ CORRECT
try:
    process_data()
except ValueError as e:
    logger.error(f"Invalid data format: {e}", exc_info=True)
    return {"error": "Invalid data format"}
except ConnectionError as e:
    logger.error(f"Database connection failed: {e}", exc_info=True)
    return {"error": "Service temporarily unavailable"}
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    return {"error": "An unexpected error occurred"}
```

### Logging Standards

**Log Levels:**
- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages (recoverable issues)
- `ERROR` - Error messages (operation failed)
- `CRITICAL` - Critical errors (system failure)

**Logging Format:**
```python
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Log with context
logger.info(f"User {user_id} logged in from {ip_address}")
logger.warning(f"Rate limit exceeded for API key {api_key[:8]}...")
logger.error(f"Payment processing failed: {error_msg}", exc_info=True)
logger.critical(f"Database connection lost - system halted")
```

**What to Log:**
- ✅ User actions (login, logout, critical operations)
- ✅ System events (startup, shutdown, configuration changes)
- ✅ Errors and exceptions with stack traces
- ✅ Performance metrics (slow queries, API response times)
- ✅ Security events (failed login attempts, unauthorized access)

**What NOT to Log:**
- ❌ Passwords or credentials
- ❌ Full credit card numbers
- ❌ Personal information (PII)
- ❌ API keys or secrets
- ❌ Sensitive user data

### Log Rotation

```python
# Python logging configuration
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

---

## 🔄 DEVELOPMENT WORKFLOW

### Standard Development Cycle

```
┌──────────────────────────────────────────────────────┐
│ 1. READ & UNDERSTAND                                  │
│    - Read master plan                                 │
│    - Read current phase requirements                  │
│    - Check what's already built                       │
│    - Identify dependencies                            │
└─────────────────┬────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────────────┐
│ 2. UPDATE PLAN STATUS                                 │
│    - Mark task as "🟡 IN PROGRESS"                    │
│    - Update progress tracking                         │
│    - Create session log                               │
└─────────────────┬────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────────────┐
│ 3. IMPLEMENT                                          │
│    - Follow coding standards                          │
│    - Write tests alongside code                       │
│    - Log decisions to learnings DB                    │
│    - Test as you build                                │
└─────────────────┬────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────────────┐
│ 4. UPDATE DOCUMENTATION                               │
│    - Update CHANGELOG.md                              │
│    - Update API docs (if applicable)                  │
│    - Update README (if user-facing changes)           │
│    - Mark task as "✅ COMPLETE"                       │
└─────────────────┬────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────────────┐
│ 5. LOG LEARNINGS                                      │
│    - Log to learnings database                        │
│    - Record decisions made                            │
│    - Track API usage/costs                            │
│    - Document mistakes and fixes                      │
└─────────────────┬────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────────────┐
│ 6. VERIFY & COMMIT                                    │
│    - All tests passing                                │
│    - All documentation updated                        │
│    - No hardcoded values                              │
│    - Meaningful commit message                        │
└──────────────────────────────────────────────────────┘
```

### Task Breakdown Guidelines

**Break down tasks if:**
- Task estimated > 8 hours
- Task has multiple sub-components
- Task has complex dependencies
- Task affects multiple modules

**Each subtask should:**
- Be independently testable
- Have clear acceptance criteria
- Be completable in < 4 hours
- Have minimal dependencies

### Communication Protocol

**When starting a task:**
```
Starting: [Task Name]

Current Status:
- Reading: [relevant documentation]
- Understanding: [what needs to be built]
- Dependencies: [list any]
- Estimated Complexity: [low/medium/high]

Updating master plan status to IN PROGRESS...
```

**When completing a task:**
```
✅ [Task Name] Complete

What Was Built:
- [Component 1]: [description]
- [Component 2]: [description]

Files Created/Modified:
- [file 1]: [purpose]
- [file 2]: [purpose]

Documentation Updated:
✅ CHANGELOG.md
✅ Master plan
✅ API documentation

Testing:
✅ Unit tests: X passing
✅ Integration tests: Y passing

Ready for: [Next Task/Phase]
```

---

## 🚀 DEPLOYMENT & PRODUCTION

### Pre-Deployment Checklist

**Code Quality:**
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code reviewed by at least one other developer
- [ ] No debug statements in code
- [ ] No hardcoded values
- [ ] Error handling comprehensive

**Documentation:**
- [ ] CHANGELOG.md updated
- [ ] Deployment guide updated
- [ ] API documentation current
- [ ] README reflects current state

**Security:**
- [ ] No secrets in code/config
- [ ] Dependencies scanned for vulnerabilities
- [ ] Security headers configured
- [ ] SSL/TLS certificates valid

**Database:**
- [ ] Backup created
- [ ] Migration scripts tested
- [ ] Schema documentation updated
- [ ] Rollback procedure documented

**Configuration:**
- [ ] Environment variables configured
- [ ] Feature flags set correctly
- [ ] Resource limits configured
- [ ] Monitoring enabled

**Performance:**
- [ ] Load testing completed
- [ ] Performance benchmarks met
- [ ] Caching configured
- [ ] Database queries optimized

### Deployment Procedures

**Staging Deployment:**
1. Deploy to staging environment
2. Run smoke tests
3. Run full test suite
4. Verify all integrations
5. Performance testing
6. Security scanning
7. Stakeholder approval

**Production Deployment:**
1. Create production backup
2. Deploy during maintenance window
3. Run database migrations
4. Deploy application code
5. Verify deployment successful
6. Monitor error logs closely
7. Verify critical workflows
8. Announce deployment complete

### Rollback Procedures

**If deployment fails:**
1. Identify failure point
2. Stop deployment immediately
3. Restore database backup
4. Revert to previous version
5. Investigate root cause
6. Document incident
7. Plan remediation

---

## 💻 PLATFORM-SPECIFIC RULES

### Windows Development

**Subprocess Handling:**
```python
# ✅ CORRECT for Windows
subprocess.run(cmd, shell=True, ...)

# ❌ WRONG
subprocess.run(cmd, shell=False, ...)  # Fails on Windows
```

**Path Handling:**
```python
# ✅ CORRECT
from pathlib import Path
project_root = Path(__file__).parent.parent

# ❌ WRONG
project_root = "../.."  # Breaks on Windows
```

**Console Output:**
```python
# ✅ CORRECT for Windows console
print("[OK] Success")
print("[X] Error")

# ❌ WRONG (causes UnicodeEncodeError)
print("✅ Success")
print("❌ Error")
```

### IoT Device Specific

**Resource Constraints:**
- Minimize memory usage
- Optimize battery consumption
- Handle network interruptions
- Implement retry logic with exponential backoff

**Logging for IoT:**
- Log levels configurable remotely
- Log rotation to prevent storage overflow
- Critical logs sent to remote server
- Local logs compressed

**Update Mechanism:**
- Over-the-air (OTA) updates
- Fallback to previous version if update fails
- Checksum verification before applying
- Staged rollout to subset of devices

---

## 🚫 FORBIDDEN ACTIONS

### NEVER DO:

1. ❌ Skip documentation updates
2. ❌ Commit without testing
3. ❌ Hardcode configuration values
4. ❌ Use bare except/catch blocks
5. ❌ Store secrets in code
6. ❌ Modify production database manually
7. ❌ Deploy without backup
8. ❌ Skip code reviews
9. ❌ Leave TODO comments in production
10. ❌ Commit sensitive data
11. ❌ Create files at root (except approved)
12. ❌ Bypass the testing phase
13. ❌ Ignore error logs
14. ❌ Delete backups
15. ❌ Modify live data without audit trail

---

## ✅ REQUIRED ACTIONS

### ALWAYS DO:

1. ✅ Update documentation BEFORE code
2. ✅ Update CHANGELOG.md with EVERY change
3. ✅ Log all decisions to learnings DB
4. ✅ Write tests for new code
5. ✅ Use configuration files for all settings
6. ✅ Handle errors explicitly
7. ✅ Review code before committing
8. ✅ Create database backups
9. ✅ Validate user inputs
10. ✅ Monitor production errors
11. ✅ Keep dependencies updated
12. ✅ Follow naming conventions
13. ✅ Ask for clarification when unsure
14. ✅ Test in staging before production
15. ✅ Document breaking changes

---

## 📋 QUICK REFERENCE CHECKLIST

**Before Starting Any Task:**
- [ ] Read master plan
- [ ] Check current phase status
- [ ] Create/resume session log
- [ ] Identify dependencies
- [ ] Update task status to "IN PROGRESS"

**During Development:**
- [ ] Follow coding standards
- [ ] Write tests alongside code
- [ ] Use configuration files
- [ ] Handle errors explicitly
- [ ] Log significant decisions

**After Completing Task:**
- [ ] All tests passing
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Session logged
- [ ] Task marked complete
- [ ] Meaningful commit message

**Before Git Push:**
- [ ] All commits have good messages
- [ ] No secrets in files
- [ ] No debug statements
- [ ] Tests passing
- [ ] Documentation synchronized

**Before Deployment:**
- [ ] Staging tested
- [ ] Backup created
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Security verified

---

## 📖 APPENDIX

### Document Maintenance

**This document should be updated when:**
- New development patterns emerge
- Mistakes are identified and prevented
- Tools or frameworks change
- Team grows or structure changes
- Deployment processes evolve

**Review schedule:**
- After each major phase completion
- When onboarding new team members
- Quarterly review of all rules
- When critical incidents occur

### Getting Started Template

When starting a new project:

1. Copy this document as `.claude/RULES.md` or `docs/DEVELOPMENT_RULES.md`
2. Customize sections for your project
3. Remove sections that don't apply
4. Add project-specific rules
5. Update team members
6. Schedule first review

---

**Remember:** These rules exist to prevent mistakes, maintain quality, and ensure consistency. They are guidelines born from real project experience. Adapt them to your needs, but respect their intent.

**Last Updated:** 2026-02-21
**Version:** 1.0
**Maintainer:** Development Team
