from pathlib import Path

import pytest
import yaml

from ckan.tests.helpers import call_action


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
SCHEMA_OPTION = "ckanext.mpb:schemas/dataset.yaml"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "dataset.yaml"
SCHEMING_SETUP = REPOSITORY_ROOT / "ckan" / "docker-entrypoint.d" / "03_setup_scheming.sh"


def _schema():
    with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        return yaml.safe_load(schema_file)


def test_dataset_schema_has_expected_identity():
    schema = _schema()

    assert schema["scheming_version"] == 2
    assert schema["dataset_type"] == "dataset"
    assert schema["dataset_fields"]
    assert schema["resource_fields"]


def test_dataset_schema_contains_catalog_metadata_contract():
    schema = _schema()
    dataset_fields = {field["field_name"]: field for field in schema["dataset_fields"]}
    resource_fields = {field["field_name"]: field for field in schema["resource_fields"]}

    assert dataset_fields["title"]["preset"] == "title"
    assert dataset_fields["name"]["preset"] == "dataset_slug"
    assert dataset_fields["tag_string"]["required"] is True
    assert dataset_fields["owner_org"]["preset"] == "dataset_organization"
    assert resource_fields["url"]["preset"] == "resource_url_upload"
    assert "format" in resource_fields


def test_container_setup_uses_extension_schema():
    assert f'"scheming.dataset_schemas = {SCHEMA_OPTION}"' in SCHEMING_SETUP.read_text()


@pytest.mark.ckan_config("ckan.plugins", "mpb scheming_datasets")
@pytest.mark.ckan_config("scheming.dataset_schemas", SCHEMA_OPTION)
@pytest.mark.usefixtures("with_plugins")
def test_scheming_loads_extension_schema():
    schema = call_action("scheming_dataset_schema_show", type="dataset")

    assert [field["field_name"] for field in schema["dataset_fields"]] == [
        field["field_name"] for field in _schema()["dataset_fields"]
    ]

