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

# Product fields

The current wrapper exposes these properties on Items, Collections, Assets, and item asset definitions:

| STAC field | Python property | Python value |
| --- | --- | --- |
| `product:type` | `product_type` | `str` |
| `product:timeliness` | `timeliness` | ISO 8601 duration string, such as `PT3H` |
| `product:timeliness_category` | `timeliness_category` | Provider category string, such as `NRT` |
| `product:acquisition_type` | `acquisition_type` | `AcquisitionType` or `str` |
| `product:status` | `status` | `ProductStatus` |
| `product:quality_status` | `quality_status` | `QualityStatus` |

All getters can return `None`; setters accept `None` to remove the local field. Item Asset reads may still return an inherited Item value after removal.

`AcquisitionType` defines `NOMINAL`, `CALIBRATION`, and `OTHER`, serialized as lowercase strings. Its getter preserves unknown strings.

`ProductStatus` defines `ARCHIVED`, `ACQUIRED`, `CANCELLED`, `FAILED`, `PLANNED`, `POTENTIAL`, `REJECTED`, `QUALITY_DEGRADED`, and `ACCEPTED`. Their serialized values are lowercase, with `QUALITY_DEGRADED` serialized as `qualitydegraded`. The status setter expects an enum; the getter raises `ValueError` for an unknown stored status.

## Updates and runtime checks

`apply()` accepts keyword-only arguments matching the properties above. Its defaults have different effects:

| Argument omitted or `None` | Effect |
| --- | --- |
| `product_type`, `acquisition_type`, `status`, `quality_status` | Remove the local field. |
| `timeliness`, `timeliness_category` | Preserve the existing field. |

Setting a non-null category requires a readable timeliness value. `apply()` checks this dependency before making assignments. Individual category assignment checks it too. However, removing timeliness does not check whether a category remains, so remove the category first.

`QualityStatus` defines `NOMINAL` and `DEGRADED`, serialized as `nominal` and `degraded`. Its setter expects an enum, and its getter raises `ValueError` for unknown stored values. Quality and lifecycle status are independent; an accepted product can have degraded quality. Leave quality status unset until a quality check has taken place.

The wrapper does not validate duration syntax, nonempty strings, or acquisition enum membership on assignment. Type annotations are not runtime validation. Reading existing fields does not rerun setter checks. Updates are not transactional if a later assignment fails.

## Collection summaries

`ProductExtension.summaries(collection)` exposes all six properties as lists: `list[str]` for the first four, `list[ProductStatus]` for status, and `list[QualityStatus]` for quality status. Getters return the stored list or `None`; they do not convert each entry to an enum. Setters replace the whole list, and `None` removes the summary. The helper neither aggregates Items nor enforces the timeliness dependency.

## Specification compatibility

The implementation declares [Product v1.1.0](https://stac-extensions.github.io/product/v1.1.0/schema.json) and supports all fields in the [upstream specification](https://github.com/stac-extensions/product), including `ProductStatus.ACCEPTED` and `quality_status` on objects and summaries.

`ProductStatus.QUALITY_DEGRADED` remains readable and writable for compatibility, but is deprecated by the specification. For new metadata, set a lifecycle status separately from `QualityStatus.DEGRADED`. The wrapper does not automatically infer a lifecycle status from a legacy quality value.

For an existing v1.0.0 document, review its metadata, remove the old schema identifier from `stac_extensions`, then call `ProductExtension.ext(document, add_if_missing=True)` to add v1.1.0. Registering `PRODUCT_EXTENSION_HOOKS` with PySTAC enables recognition of the previous identifier during STAC migration; it does not rewrite field values. See [migration behavior](../explanation/architecture.md#migration-hooks).

Product status describes the product itself. Order extension status describes a request or processing transaction; a completed order does not imply an accepted product.
