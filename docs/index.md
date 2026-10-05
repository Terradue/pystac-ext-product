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

# Product PySTAC extension

`pystac-ext-product` reads and writes product packaging and distribution metadata through `pystac.extensions.product.ProductExtension`.

```bash
python -m pip install pystac-ext-product
```

The implementation declares [Product v1.1.0](https://stac-extensions.github.io/product/v1.1.0/schema.json). Its Python distribution version is independent of the specification version. All six Product fields are supported, including accepted lifecycle status and quality status. See the [version and migration notes](reference/fields.md#specification-compatibility).

- [Create a Product Item](tutorials/first-steps.md) and round-trip its metadata.
- [Work with Product metadata](how-to/use-extension.md) on Items, Collections, Assets, and item asset definitions.
- [Look up fields](reference/fields.md) and runtime behavior.
- [Browse the Python API](reference/api.md).
- [Understand storage and validation](explanation/architecture.md).
