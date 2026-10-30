#!/bin/bash
set -e

ckan config-tool $CKAN_INI "scheming.dataset_schemas = ckanext.mpb:schemas/pesquisa.yaml"
ckan config-tool $CKAN_INI "ckan.default.package_type = pesquisa"
ckan config-tool $CKAN_INI "scheming.presets = ckanext.scheming:presets.json"
