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

# Work with Product metadata

## Update and remove fields

Starting with `item` from the [tutorial](../tutorials/first-steps.md):

```python
from pystac.extensions.product import ProductExtension, ProductStatus, QualityStatus

product = ProductExtension.ext(item)
product.product_type = "L2A"
product.timeliness = "PT36H"
product.timeliness_category = "STC"
assert product.product_type == "L2A"

product.timeliness_category = None
product.timeliness = None
assert product.timeliness_category is None
```

Individual setters preserve unrelated fields. Remove the category before removing its duration. `apply()` clears omitted product type, acquisition type, status, and quality status, but preserves timeliness and category when their arguments are `None`.

## Record quality independently of lifecycle

After a quality check, describe both usability and quality:

```python
product.status = ProductStatus.ACCEPTED
product.quality_status = QualityStatus.DEGRADED
assert product.status is ProductStatus.ACCEPTED
assert product.quality_status is QualityStatus.DEGRADED
```

For legacy `ProductStatus.QUALITY_DEGRADED`, choose a lifecycle status based on your application's knowledge, then set `QualityStatus.DEGRADED`. No automatic conversion is performed. Use `quality_status = None` when quality has not been checked.

## Add Item assets

```python
asset = pystac.Asset(href="https://example.com/product.tif", roles=["data"])
item.add_asset("data", asset)
asset_product = ProductExtension.ext(asset)
assert asset_product.product_type == "L2A"
asset_product.product_type = "L2A-COG"
assert asset.extra_fields["product:type"] == "L2A-COG"
assert product.product_type == "L2A"
asset_product.product_type = None
assert asset_product.product_type == "L2A"
```

Asset reads fall back to owning Item properties when no local value is present. Writes and removals affect only the Asset. Collection-owned Assets have no such fallback. Attach assets to their owner before requesting `add_if_missing=True`, which declares the extension on that owner.

## Describe a Collection

```python
collection = pystac.Collection(
    id="example-products",
    description="Example product collection",
    extent=pystac.Extent(
        pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
        pystac.TemporalExtent([[None, None]]),
    ),
    license="proprietary",
)
collection_product = ProductExtension.ext(collection, add_if_missing=True)
collection_product.product_type = "L2A"
assert collection.extra_fields["product:type"] == "L2A"

summaries = ProductExtension.summaries(collection)
summaries.product_type = ["L1C", "L2A"]
summaries.timeliness = ["PT3H", "PT36H"]
summaries.status = [ProductStatus.ACCEPTED, ProductStatus.REJECTED]
summaries.quality_status = [QualityStatus.NOMINAL, QualityStatus.DEGRADED]
assert summaries.product_type == ["L1C", "L2A"]
summaries.timeliness = None
assert "product:timeliness" not in collection.summaries.lists
```

Top-level fields and summaries are independent. Summaries retain complete lists and are not computed from Items. The summary helper has no `apply()` method.

## Describe item asset definitions

```python
collection.item_assets = {
    "data": pystac.ItemAssetDefinition(
        {"type": "image/tiff", "roles": ["data"]}
    ),
}
definition = collection.item_assets["data"]
definition_product = ProductExtension.ext(definition)
definition_product.product_type = "L2A-COG"
definition_product.quality_status = QualityStatus.NOMINAL
assert definition.properties["product:type"] == "L2A-COG"
```

Retrieve definitions through `collection.item_assets` so they have an owner. The wrapper writes to the definition's `properties` dictionary, with extension membership checked on the Collection.
