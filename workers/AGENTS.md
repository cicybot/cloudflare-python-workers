# AGENTS.md

This file provides guidance for agentic coding agents working in the workers-python repository. It includes build/lint/test commands, code style guidelines, and any specific rules.

## Overview
The workers-python project is a task processing system with an API server (FastAPI) that handles task submission, queuing (Redis), and storage (MySQL). Workers poll the API via HTTP to retrieve and update tasks, ensuring no direct database access by workers for better decoupling.

Task types use unified Redis queues named "tasks:{task_type}", where task_type is a string identifier (e.g., "test" for TTS tasks, "whisper" for Whisper transcription tasks).

## Build/Lint/Test Commands

### Environment Setup
- Install dependencies: `uv sync`
- Activate environment: `uv shell` or use `uv run` for commands

### Building
- No explicit build step; dependencies are installed via uv
- For production, ensure all deps are in pyproject.toml

### Linting and Formatting
- Install linting tools: `uv add --dev ruff`
- Lint code: `uv run ruff check .`
- Format code: `uv run ruff format .`
- Type checking: `uv add --dev mypy; uv run mypy .` (optional, no types enforced yet)

### Testing
- Run all tests: `uv run python test_worker.py` (note: tests are not in a framework, just functions)
- Run a single test: `uv run python -c "from test_worker import test_run_task; test_run_task()"`
- For test_get_queue_length: `uv run python -c "from test_worker import test_get_queue_length; test_get_queue_length()"`
- Database setup: Run `mysql -u root -p < db_setup.sql` to create tables (requires MySQL)
- Start API: `uv run python api.py` (requires Redis and MySQL for full functionality)
- Start worker: `python worker.py [worker_id]` (uses HTTP API only, no direct Redis/MySQL access)

### Running the Application
- API server: `uv run uvicorn api:app --reload --host 0.0.0.0 --port 8989`
- Worker (TTS): `uv run python worker.py [worker_id]` (worker_id optional, defaults to UUID)
- Worker (Whisper): `uv run python worker-whisper.py [worker_id]` (worker_id optional, defaults to UUID)
- Submit TTS task: `curl -X POST http://localhost:8989/api/tts/index-tts -H "Content-Type: application/json" -d '{"params": {"text": "hello"}}'`
- Submit Whisper audio from URL: `curl -X POST http://localhost:8989/api/whisper/audio/url -H "Content-Type: application/json" -d '{"url": "https://example.com/audio.mp3"}'`
- Submit Whisper video from URL: `curl -X POST http://localhost:8989/api/whisper/video/url -H "Content-Type: application/json" -d '{"url": "https://example.com/video.mp4"}'`
- Submit Whisper audio file: First upload file via `curl -X POST http://localhost:8989/api/upload -F "file=@audio.wav"`, then submit with rel_path from response.
- Get queue length: `curl http://localhost:8989/api/queue/length` (returns lengths for all types) or `curl "http://localhost:8989/api/queue/length?task_type=test"` or `curl "http://localhost:8989/api/queue/length?task_type=whisper"`

## Code Style Guidelines

### General Principles
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Keep functions small and focused
- Prefer readability over cleverness
- Use logging instead of print for production code
- Handle errors gracefully with try-except

### Imports
- Standard library imports first (e.g., import json, import logging)
- Third-party imports second (e.g., import redis, import mysql.connector)
- Local imports last (e.g., import config, import models)
- Group imports with blank lines between groups
- Use absolute imports

### Formatting
- Use 4 spaces for indentation
- Line length: 88 characters (Black/Ruff default)
- Use double quotes for strings, single for internal consistency if needed
- Trailing commas in multi-line structures

### Naming Conventions
- Functions and variables: snake_case (e.g., run_task, task_data)
- Classes: PascalCase (e.g., TaskModel) - none present
- Constants: UPPER_CASE (e.g., WORKER_ID)
- Modules: lowercase (e.g., models.py, api.py)

### Types
- Add type hints where possible (e.g., def run_task(task_data: dict) -> None)
- Use Union, Optional for complex types
- Not strictly enforced, but encouraged for clarity

### Error Handling
- Use try-except for external operations (Redis, MySQL, HTTP requests)
- Log exceptions with logging.error
- Raise custom exceptions for business logic errors
- Avoid bare except; catch specific exceptions

### Logging
- Use the logging module with appropriate levels (INFO, ERROR, DEBUG)
- Configure logging in main scripts
- Include relevant context in log messages
- Example: logging.info(f"Processing task: {task_data}")

### Database Interactions
- Use models.py for all DB operations
- Close connections properly
- Use parameterized queries to prevent SQL injection
- Handle connection errors

### API Design
- Use FastAPI for REST endpoints
- Validate input with Pydantic models
- Return consistent JSON responses
- Use HTTP status codes appropriately
- Document endpoints with descriptions

### Asynchronous Code
- Use async/await for I/O operations in API
- Worker is synchronous and uses HTTP polling for task retrieval

### Security
- Store secrets in config.py, not hardcoded
- Use environment variables for sensitive data if needed
- Validate inputs to prevent injection

### File Structure
- api.py: FastAPI application and endpoints
- worker.py: Worker logic for processing TTS tasks (HTTP-only, no direct DB/Redis)
- worker-whisper.py: Worker logic for processing Whisper transcription tasks (HTTP-only, no direct DB/Redis)
- utils_worker.py: Shared utilities for workers (registration, heartbeat, retry logic)
- models.py: Database models and operations
- config.py: Configuration settings
- test_worker.py: Test functions
- db_setup.sql: Database schema

### Best Practices
- Commit small, focused changes
- Write descriptive commit messages
- Test changes before committing
- Use branches for features
- Keep dependencies minimal

### No Specific Cursor or Copilot Rules Found
- No .cursor/rules or .cursorrules files
- No .github/copilot-instructions.md

This guide ensures consistent, maintainable code across the project.</content>
<parameter name="filePath">/Users/data/cloudflare/workers-python/workers/AGENTS.md