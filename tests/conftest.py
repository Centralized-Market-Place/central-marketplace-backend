import pytest
import pytest_asyncio
import asyncio
import os
import redis.asyncio as redis
from typing import Generator, AsyncGenerator

@pytest_asyncio.fixture(scope="function")
async def event_loop() -> AsyncGenerator[asyncio.AbstractEventLoop, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    await loop.shutdown_asyncgens()
    loop.close()

@pytest.fixture(scope="session")
async def redis_client() -> Generator:
    """Create a Redis client for tests."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    client = redis.from_url(redis_url, decode_responses=True)
    yield client
    await client.close()

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "e2e: mark a test as an end-to-end test") 