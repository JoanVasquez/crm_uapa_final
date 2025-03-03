# app/tests/conftest.py
import os

from dotenv import load_dotenv


def pytest_configure():
    """Pytest hook that runs before any tests; load .env.test from container."""
    # Because the Dockerfile places .env.test at /, the path is '/.env.test'
    env_file_path = "/.env.test"
    if not os.path.exists(env_file_path):
        print(f"WARNING: {env_file_path} not found in container!")
    else:
        print(f"INFO: Loading env vars from {env_file_path}")
    load_dotenv(dotenv_path=env_file_path, override=True)
