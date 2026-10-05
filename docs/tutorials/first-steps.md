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

# Create a Product Item

[Install the package](../how-to/install.md), then run this complete example:

```python
from datetime import datetime, timezone

import pystac
from pystac.extensions.product import (
    AcquisitionType,
    ProductExtension,
    ProductStatus,
    QualityStatus,
)

item = pystac.Item(
    id="example-product",
    geometry=None,
    bbox=None,
    datetime=datetime(2026, 1, 1, tzinfo=timezone.utc),
    properties={},
)
product = ProductExtension.ext(item, add_if_missing=True)
product.apply(
    product_type="L1C",
    timeliness="PT3H",
    timeliness_category="NRT",
    acquisition_type=AcquisitionType.NOMINAL,
    status=ProductStatus.ACCEPTED,
    quality_status=QualityStatus.NOMINAL,
)

serialized = item.to_dict()
assert ProductExtension.get_schema_uri() in serialized["stac_extensions"]
assert serialized["properties"]["product:type"] == "L1C"
assert serialized["properties"]["product:timeliness"] == "PT3H"

restored_item = pystac.Item.from_dict(serialized)
restored = ProductExtension.ext(restored_item)
assert restored.product_type == "L1C"
assert restored.acquisition_type == AcquisitionType.NOMINAL
assert restored.timeliness_category == "NRT"
assert restored.status is ProductStatus.ACCEPTED
assert restored.quality_status is QualityStatus.NOMINAL
```

`add_if_missing=True` declares the extension on the Item. The wrapper writes directly to Item properties. `to_dict()` serializes without running JSON Schema validation.

A timeliness category needs a duration. `apply(timeliness_category="NRT")` raises `ValueError` unless a duration is supplied in the same call or already readable from the wrapper. See [update semantics](../reference/fields.md#updates-and-runtime-checks) before using `apply()` to update existing metadata.
