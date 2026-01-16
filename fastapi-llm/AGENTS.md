# AGENTS.md - FastAPI LLM Application

This file contains essential information for AI agents working on this FastAPI application codebase. It includes build/lint/test commands, code style guidelines, and development practices.

## Project Overview

This is a FastAPI-based web application using SQLModel for ORM operations. The application supports both SQLite (default) and MySQL databases, with JWT-based authentication and CORS middleware.

## Development Environment

- **Python Version**: >= 3.12
- **Package Manager**: uv
- **Framework**: FastAPI with SQLModel ORM
- **Database**: SQLite (default) or MySQL

## Build/Lint/Test Commands

### Package Management
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package-name>

# Update dependencies
uv lock --upgrade
```

### Development Server
```bash
# Start development server
uv run fastapi dev app/app.py

# Alternative with explicit PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/app
uv run fastapi dev app/app.py
```

### Testing
```bash
# No tests currently exist - run this to set up pytest first
uv add --dev pytest pytest-asyncio httpx

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_file.py

# Run single test function
uv run pytest tests/test_file.py::test_function_name

# Run tests with coverage
uv run pytest --cov=app --cov-report=html
```

### Code Quality
```bash
# Install linting/formatting tools
uv add --dev ruff black mypy

# Format code
uv run black app/

# Lint code
uv run ruff check app/

# Fix auto-fixable linting issues
uv run ruff check app/ --fix

# Type checking
uv run mypy app/
```

### Docker
```bash
# Build container
docker build -t fastapi-app .

# Run container
docker run -p 8000:80 fastapi-app
```

## Code Style Guidelines

### Import Organization
```python
# Standard library imports (alphabetical)
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Union

# Third-party imports (alphabetical)
from fastapi import Depends, HTTPException, status
from pwdlib import PasswordHash
import jwt

# Local imports (relative, alphabetical)
from common.constants import auth_strip_path_prefixes
from service.Global import Global
```

### Naming Conventions
- **Functions/Methods**: `snake_case` (e.g., `get_current_user_uid`, `verify_password`)
- **Variables**: `snake_case` (e.g., `access_token`, `user_data`)
- **Constants**: `UPPER_CASE` (e.g., `JWT_SECRET_KEY`, `DATABASE_URL`)
- **Classes**: `PascalCase` (though minimal classes in current codebase)
- **Modules**: `snake_case` or `PascalCase` depending on content

### Type Hints
Always use type hints for function parameters and return values:
```python
from typing import Union, Optional, List, Dict, Any

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> tuple[str, datetime]:
    # Function implementation
    pass

async def get_current_user_uid(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None) -> Optional[str]:
    # Function implementation
    pass
```

### Logging
Use structured logging throughout the application:
```python
import logging

logger = logging.getLogger(__name__)

# Info level for important operations
logger.info("User authentication successful: %s", user_id)

# Debug level for detailed information
logger.debug("SQL query executed: %s with params: %s", query, params)

# Error level with traceback for exceptions
logger.error("Database error: %s", traceback.format_exc())
```

### Error Handling
Use FastAPI's HTTPException for API errors:
```python
from fastapi import HTTPException, status

# Authentication errors
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Basic"},
)

# General server errors
raise HTTPException(status_code=500, detail=str(e))
```

### Database Operations
Use the provided `execute_sql` helper for raw SQL operations:
```python
from common.db import execute_sql

# SELECT operations
users = execute_sql("SELECT * FROM users WHERE active = ?", {"active": True}, session=session)

# INSERT operations
result = execute_sql("INSERT INTO users (username, password) VALUES (?, ?)",
                    {"username": "john", "password": "hashed_pass"}, session=session)
affected_rows, last_id = result

# UPDATE/DELETE operations
affected_rows, _ = execute_sql("UPDATE users SET last_login = ? WHERE id = ?",
                              {"last_login": datetime.now(), "id": user_id}, session=session)
```

### Dependency Injection
Use FastAPI's dependency injection system:
```python
from fastapi import Depends
from sqlmodel import Session
from common.db import get_session

@app.get("/users")
async def get_users(session: Session = Depends(get_session)):
    # Function implementation
    pass
```

### Configuration Management
Use the Global service for configuration:
```python
from service.Global import Global

# Get configuration values
jwt_secret = Global.get_options("JWT_SECRET_KEY")
is_production = not Global.is_local()

# Check environment
if Global.get_options("is_cf") is not None:
    # Cloudflare-specific logic
    pass
```

### Router Organization
Organize API endpoints in routers:
```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user_uid)],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_users():
    # Implementation
    pass

@router.post("/")
async def create_user(user: UserCreate):
    # Implementation
    pass
```

### Security Best Practices
- Never log sensitive information (passwords, tokens, secrets)
- Use environment variables for secrets
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper CORS settings for production

### File Structure
```
app/
├── app.py                 # Main FastAPI application
├── routers/               # API route handlers
│   ├── __init__.py
│   └── utils.py
├── common/                # Shared utilities and constants
│   ├── __init__.py
│   ├── db.py             # Database utilities
│   ├── helpers.py        # Authentication helpers
│   ├── constants.py      # Application constants
│   └── utils.py          # General utilities
└── service/               # Business logic services
    ├── __init__.py
    └── Global.py         # Global configuration service
```

### Async/Await Patterns
Use async functions for I/O operations:
```python
# Async endpoint
@app.get("/data")
async def get_data():
    # Async database operations, API calls, etc.
    pass

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup logic
    Global.init()
    yield
    # Shutdown logic
```

### Testing Patterns
When adding tests, follow these patterns:
```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.fixture
async def client():
    # Test client setup
    pass

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    # Test implementation
    pass
```

## Additional Guidelines

### Commit Messages
Follow conventional commit format:
```
feat: add user registration endpoint
fix: resolve SQL injection vulnerability in user lookup
docs: update API documentation for authentication
refactor: simplify database query logic
test: add unit tests for password hashing
```

### Environment Variables
Key environment variables used:
- `DATABASE_URL`: Database connection string
- `JWT_SECRET_KEY`: Secret key for JWT signing
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `SWAGGER_USERNAME`/`SWAGGER_PASSWORD`: Basic auth for docs
- `LOG_DIR`: Directory for log files
- `DB_DIR`: Directory for SQLite database

### Performance Considerations
- Use database sessions efficiently (don't keep them open unnecessarily)
- Implement proper indexing for frequently queried columns
- Use async operations for I/O bound tasks
- Consider pagination for large result sets
- Cache expensive operations when appropriate

### Security Checklist
- [ ] Input validation on all endpoints
- [ ] Authentication required for sensitive operations
- [ ] Passwords properly hashed using pwdlib
- [ ] JWT tokens have reasonable expiration
- [ ] CORS properly configured for production
- [ ] No sensitive data logged
- [ ] HTTPS enforced in production
- [ ] Database credentials secured</content>
<parameter name="filePath">/Users/data/cloudflare/workers-python/fastapi-llm/AGENTS.md