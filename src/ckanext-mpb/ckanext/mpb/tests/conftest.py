from pathlib import Path

import pytest

import ckan.plugins.toolkit as toolkit


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
ENV_EXAMPLE = REPOSITORY_ROOT / ".env.example"


@pytest.fixture
def env_example():
    values = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


@pytest.fixture
def auth_config(env_example):
    return {
        key.lower().replace("__", "."): toolkit.asbool(value)
        for key, value in env_example.items()
        if key.startswith("CKAN__AUTH__")
    }


@pytest.fixture
def portal_auth(ckan_config, monkeypatch, auth_config):
    for key, value in auth_config.items():
        monkeypatch.setitem(ckan_config, key, value)
