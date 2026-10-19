#!/bin/bash
set -e

ckan config-tool $CKAN_INI "scheming.dataset_schemas = ckanext.mpb:schemas/dataset.yaml"
ckan config-tool $CKAN_INI "scheming.presets = ckanext.scheming:presets.json"
ckan config-tool $CKAN_INI "search.facets = organization groups tags res_format license_id"
