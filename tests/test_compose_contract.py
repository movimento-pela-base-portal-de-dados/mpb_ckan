#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env.example"

DATA_VOLUMES = {
    "db": ("pg_data", "/var/lib/postgresql/data"),
    "solr": ("solr_data", "/var/solr"),
}

APP_VOLUME = ("ckan_storage", "/var/lib/ckan")
EPHEMERAL_SERVICES = ("redis", "datapusher")
HTTP_HEALTHCHECKS = ("ckan", "ckan-dev", "datapusher", "solr")
CKAN_IMAGE_SOURCES = ("ckan/Dockerfile", "ckan/Dockerfile.dev", ".github/workflows/test.yml")
CKAN_IMAGE_TAG = re.compile(r"\bckan/ckan-(?:base|dev|solr|postgres-dev):(\d+\.\d+)")


class ContractError(AssertionError):
    pass


def compose_base() -> list[str]:
    docker = shutil.which("docker")
    if docker and subprocess.run(
        [docker, "compose", "version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0:
        return [docker, "compose"]
    standalone = shutil.which("docker-compose")
    if standalone and subprocess.run(
        [standalone, "version", "--short"],
        text=True,
        capture_output=True,
        check=False,
    ).stdout.startswith("2."):
        return [standalone]
    raise ContractError("Docker Compose V2 não encontrado (docker compose ou docker-compose).")


def render(filename: str) -> dict:
    command = compose_base() + [
        "--env-file",
        str(ENV_FILE),
        "-f",
        str(ROOT / filename),
        "config",
        "--format",
        "json",
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        hint = "\nExecute: cp .env.example .env" if not (ROOT / ".env").exists() else ""
        raise ContractError(f"Falha ao renderizar {filename}:\n{result.stderr}{hint}")
    return json.loads(result.stdout)


def duration_seconds(value: object) -> float:
    if isinstance(value, (int, float)):
        return value / 1_000_000_000 if value > 1_000_000 else float(value)
    text = str(value).strip()
    if text.endswith("ms"):
        return float(text[:-2]) / 1000
    if text.endswith("m") and text[:-1].replace(".", "", 1).isdigit():
        return float(text[:-1]) * 60
    total = 0.0
    number = ""
    for char in text:
        if char.isdigit() or char == ".":
            number += char
            continue
        if not number:
            raise ContractError(f"Duração inválida: {value!r}")
        amount = float(number)
        number = ""
        if char == "h":
            total += amount * 3600
        elif char == "m":
            total += amount * 60
        elif char == "s":
            total += amount
        else:
            raise ContractError(f"Duração inválida: {value!r}")
    if number:
        total += float(number)
    return total


def volume_mount(service: dict, source: str, target: str) -> None:
    mounts = service.get("volumes") or []
    for mount in mounts:
        if mount.get("type") == "volume" and mount.get("source") == source and mount.get("target") == target:
            return
    raise ContractError(f"Volume {source} -> {target} ausente. Montagens: {mounts}")


def require_healthy_dependency(service: dict, dependency: str) -> None:
    depends_on = service.get("depends_on") or {}
    relation = depends_on.get(dependency)
    if not isinstance(relation, dict) or relation.get("condition") != "service_healthy":
        raise ContractError(f"Dependência {dependency} sem condition service_healthy: {depends_on}")


def require_healthcheck(service_name: str, service: dict) -> None:
    healthcheck = service.get("healthcheck") or {}
    test = healthcheck.get("test")
    if not test or test == ["NONE"]:
        raise ContractError(f"{service_name} não tem healthcheck.")
    if test[0] != "CMD":
        raise ContractError(f"{service_name} deve usar healthcheck em formato CMD: {test}")
    command = " ".join(test)
    if service_name in HTTP_HEALTHCHECKS:
        if "127.0.0.1" not in command or "localhost" in command:
            raise ContractError(
                f"{service_name} deve sondar 127.0.0.1, sem localhost, para evitar falha de IPv6: {test}"
            )
    if service_name == "db" and "-h" not in test:
        raise ContractError(
            "db deve rodar pg_isready com -h 127.0.0.1: pelo socket ele responde durante o init."
        )
    if service_name == "solr" and "/solr/ckan/admin/ping" not in command:
        raise ContractError(f"solr deve sondar o core ckan em /solr/ckan/admin/ping: {test}")
    if "start_period" not in healthcheck:
        raise ContractError(f"{service_name} não define start_period.")
    if duration_seconds(healthcheck["start_period"]) <= 0:
        raise ContractError(f"{service_name} tem start_period vazio.")
    if int(healthcheck.get("retries") or 0) < 3:
        raise ContractError(f"{service_name} precisa de ao menos 3 retries.")


def assert_no_data_volume(service_name: str, service: dict) -> None:
    for mount in service.get("volumes") or []:
        if mount.get("type") == "volume":
            raise ContractError(f"{service_name} não deve persistir volume nomeado: {mount}")


def assert_internal(config: dict, network: str) -> None:
    networks = config.get("networks") or {}
    if network not in networks or not networks[network].get("internal"):
        raise ContractError(f"A rede {network} deve existir e ser internal.")


def assert_stack(filename: str, app_service: str) -> None:
    config = render(filename)
    services = config["services"]
    expected = {app_service, "datapusher", "db", "solr", "redis"}
    if filename == "docker-compose.yml":
        expected.add("nginx")
    missing = expected.difference(services)
    if missing:
        raise ContractError(f"{filename} sem serviços: {sorted(missing)}")

    for name in expected:
        if name == "nginx":
            continue
        require_healthcheck(name, services[name])

    app = services[app_service]
    for dependency in ("db", "solr", "redis"):
        require_healthy_dependency(app, dependency)
    for network in ("ckannet", "dbnet", "solrnet", "redisnet"):
        if network not in (app.get("networks") or {}):
            raise ContractError(f"{app_service} precisa alcançar a rede {network}.")
    volume_mount(app, *APP_VOLUME)
    volume_mount(services["db"], *DATA_VOLUMES["db"])
    volume_mount(services["solr"], *DATA_VOLUMES["solr"])
    for name in EPHEMERAL_SERVICES:
        assert_no_data_volume(name, services[name])

    for network in ("dbnet", "solrnet", "redisnet"):
        assert_internal(config, network)

    if services["db"].get("networks", {}).keys() != {"dbnet"}:
        raise ContractError("db deve permanecer somente na rede interna dbnet.")
    if services["solr"].get("networks", {}).keys() != {"solrnet"}:
        raise ContractError("solr deve permanecer somente na rede interna solrnet.")
    if services["redis"].get("networks", {}).keys() != {"redisnet"}:
        raise ContractError("redis deve permanecer somente na rede interna redisnet.")

    volumes = config.get("volumes") or {}
    for volume in ("ckan_storage", "pg_data", "solr_data"):
        if volume not in volumes:
            raise ContractError(f"{filename} não declara o volume {volume}.")

    if filename == "docker-compose.yml":
        require_healthy_dependency(services["nginx"], "ckan")
        callback = "http://ckan:5000"
    else:
        extensions = [
            mount for mount in app.get("volumes") or []
            if mount.get("type") == "bind" and mount.get("target") == "/srv/app/src_extensions"
        ]
        if not extensions:
            raise ContractError("ckan-dev deve montar ./src em /srv/app/src_extensions.")
        callback = "http://ckan-dev:5000"

    environment = app.get("environment") or {}
    actual = environment.get("CKAN__DATAPUSHER__CALLBACK_URL_BASE")
    if actual != callback:
        raise ContractError(
            f"{app_service} deve chamar o DataPusher de volta em {callback}, obtido {actual!r}."
        )


def env_example() -> dict[str, str]:
    values = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


def assert_ckan_versions() -> None:
    env = env_example()
    expected = ".".join(env.get("CKAN_VERSION", "").split(".")[:2])
    if not expected:
        raise ContractError("CKAN_VERSION ausente em .env.example.")
    solr = env.get("SOLR_IMAGE_VERSION", "")
    found = {f"SOLR_IMAGE_VERSION={solr}": solr.split("-")[0]}
    for source in CKAN_IMAGE_SOURCES:
        for match in CKAN_IMAGE_TAG.finditer((ROOT / source).read_text()):
            found[f"{source}: {match.group(0)}"] = match.group(1)
    divergent = sorted(origin for origin, version in found.items() if version != expected)
    if divergent:
        raise ContractError(f"Versões do CKAN divergem de CKAN_VERSION={expected}: {divergent}")


def main() -> int:
    try:
        assert_ckan_versions()
        assert_stack("docker-compose.yml", "ckan")
        assert_stack("docker-compose.dev.yml", "ckan-dev")
    except ContractError as exc:
        print(f"Contrato do Compose reprovado: {exc}", file=sys.stderr)
        return 1
    print("Contrato do Compose validado: versões do CKAN, dependências, healthchecks e volumes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
