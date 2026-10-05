<!--
Copyright 2026 Terradue

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Scope, architecture, and validation

## Package structure and storage

The distribution is `pystac-ext-product`; the import path is `pystac.extensions.product`. The wheel excludes the shared `pystac.extensions` initializer owned by PySTAC.

`ProductExtension.ext()` selects a wrapper that mutates the existing PySTAC object:

| Object | Storage | Extension declaration |
| --- | --- | --- |
| Item | `properties` | Item `stac_extensions` |
| Collection | `extra_fields` | Collection `stac_extensions` |
| Asset | `extra_fields` | Owner `stac_extensions` |
| ItemAssetDefinition | `properties` | Owner Collection `stac_extensions` |

Asset wrappers additionally read owning Item properties as a fallback. They do not fall back to Collection fields. Item asset definitions have no fallback. Removing an Asset override can reveal the Item value again.

`ProductExtension.summaries()` accesses Collection summary lists independently of top-level fields. It does not aggregate Items or truncate lists to one entry. Catalogs and Links are not supported by `ext()`.

## Validation boundaries

The wrapper stores product metadata; it does not deliver products or calculate their timeliness. Its main dependency check requires timeliness when setting a category. See the [field reference](../reference/fields.md) for precise setter and `apply()` behavior.

Neither `apply()` nor `to_dict()` performs JSON Schema validation. For full validation, install `python -m pip install "pystac[validation]"` and call `item.validate()` or `collection.validate()`. Schema retrieval can require network access unless your application configures a local validator.

The wrapper declares Product v1.1.0. Schema validation checks enum values and unique summary entries in addition to field constraints. An inherited Item duration may satisfy an Asset wrapper's category check, while schema validation still requires a duration in the Asset's own fields.

## Migration hooks

`PRODUCT_EXTENSION_HOOKS` exposes the schema identifier, the previous v1.0.0 identifier, the legacy identifier `product`, and supported Item/Collection object types. The module does not automatically register this object with PySTAC. During PySTAC migration, the hook replaces recognized previous identifiers with v1.1.0. Registering the hook alone does not force migration of a document already using the current STAC core version. Field contents are preserved, including deprecated `qualitydegraded`; choose any replacement lifecycle status explicitly.
