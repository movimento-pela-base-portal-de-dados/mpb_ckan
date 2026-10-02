#!/bin/bash
set -e

# Ensure ckanext-scheming is installed in the current environment
# (needed because volumes might shadow the build-time installation)
# echo "Ensuring ckanext-scheming is installed..."
# pip3 install -e "git+https://github.com/ckan/ckanext-scheming.git#egg=ckanext-scheming"

ckan config-tool $CKAN_INI "scheming.dataset_schemas = ckanext.scheming:ckan_dataset_schema.yaml"
ckan config-tool $CKAN_INI "scheming.presets = ckanext.scheming:presets.json"
ckan config-tool $CKAN_INI "search.facets = organization groups tags res_format license_id"