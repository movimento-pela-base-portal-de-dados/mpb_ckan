import json

import pytest

from ckan.tests import factories


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "abc datastore"),
    pytest.mark.usefixtures("with_plugins"),
    pytest.mark.usefixtures("clean_db"),
]


def _admin_headers():
    user = factories.SysadminWithToken()
    return {"Authorization": user["token"]}


def _post_json(app, path, payload, headers):
    return app.post(
        path,
        params=json.dumps(payload),
        content_type="application/json",
        headers=headers,
    )


def test_catalog_homepage_is_available(app):
    response = app.get("/")

    assert response.status_code == 200
    assert "html" in response.content_type


def test_catalog_can_create_search_and_show_dataset(app):
    headers = _admin_headers()
    payload = {
        "name": "abc-catalog-test-dataset",
        "title": "ABC catalog test dataset",
        "notes": "Synthetic fixture used by the repository test suite.",
        "tags": [{"name": "abc-test"}],
        "resources": [
            {
                "url": "https://example.org/abc-test.csv",
                "name": "Synthetic CSV resource",
                "format": "CSV",
            }
        ],
    }

    response = _post_json(
        app,
        "/api/3/action/package_create",
        payload,
        headers,
    )
    assert response.json["success"] is True
    dataset = response.json["result"]

    shown = app.get(
        "/api/3/action/package_show",
        params={"id": dataset["name"]},
    ).json
    assert shown["success"] is True
    assert shown["result"]["title"] == payload["title"]
    assert shown["result"]["tags"][0]["name"] == "abc-test"
    assert shown["result"]["resources"][0]["format"] == "CSV"

    searched = app.get(
        "/api/3/action/package_search",
        params={"q": payload["title"]},
    ).json
    assert searched["success"] is True
    assert any(item["name"] == dataset["name"] for item in searched["result"]["results"])


def test_datastore_resource_can_be_written_and_read(app):
    headers = _admin_headers()
    resource = factories.Resource(url="https://example.org/abc-test.csv")

    created = _post_json(
        app,
        "/api/3/action/datastore_create",
        {
            "resource": {
                "id": resource["id"],
                "package_id": resource["package_id"],
            },
            "fields": [
                {"id": "municipio", "type": "text"},
                {"id": "valor", "type": "numeric"},
            ],
            "records": [{"municipio": "Sao Paulo", "valor": 1}],
        },
        headers,
    ).json
    assert created["success"] is True

    result = app.get(
        "/api/3/action/datastore_search",
        params={"resource_id": resource["id"]},
    ).json
    assert result["success"] is True
    assert result["result"]["records"][0]["municipio"] == "Sao Paulo"
