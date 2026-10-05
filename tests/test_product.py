# Copyright 2026 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TypeAlias

import pytest
from pystac.validation import JsonSchemaSTACValidator

import pystac
from pystac.extensions.product import (
    ACQUISITION_TYPE_PROP,
    PRODUCT_EXTENSION_HOOKS,
    QUALITY_STATUS_PROP,
    SCHEMA_URI,
    STATUS_PROP,
    TIMELINESS_CATEGORY_PROP,
    TIMELINESS_PROP,
    TYPE_PROP,
    AcquisitionType,
    ProductExtension,
    ProductStatus,
    QualityStatus,
)

TemporalIntervals: TypeAlias = list[list[datetime | None]]


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def make_item() -> pystac.Item:
    return pystac.Item(
        id="i",
        geometry=None,
        bbox=None,
        datetime=_dt("2020-01-01T00:00:00Z"),
        properties={},
        start_datetime=None,
        end_datetime=None,
    )


def make_collection() -> pystac.Collection:
    temporal_intervals: TemporalIntervals = [[None, None]]
    return pystac.Collection(
        id="c",
        description="d",
        extent=pystac.Extent(
            pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            pystac.TemporalExtent(temporal_intervals),
        ),
        license="proprietary",
    )


def test_apply_requires_timeliness_when_setting_category() -> None:
    item = make_item()
    ext = ProductExtension.ext(item, add_if_missing=True)

    with pytest.raises(ValueError):
        ext.apply(timeliness_category="NRT")  # timeliness missing and not already set

    # If timeliness is already set, setting category is allowed
    ext.timeliness = "PT3H"
    ext.apply(timeliness_category="NRT")
    assert item.properties[TIMELINESS_CATEGORY_PROP] == "NRT"


def test_item_apply_roundtrip_and_acquisition_type_enum() -> None:
    item = make_item()
    ext = ProductExtension.ext(item, add_if_missing=True)

    ext.apply(
        product_type="SLC",
        timeliness="PT3H",
        timeliness_category="NRT",
        acquisition_type=AcquisitionType.NOMINAL,
        status=ProductStatus.ACQUIRED,
    )

    assert item.properties[TYPE_PROP] == "SLC"
    assert item.properties[TIMELINESS_PROP] == "PT3H"
    assert item.properties[TIMELINESS_CATEGORY_PROP] == "NRT"
    assert item.properties[ACQUISITION_TYPE_PROP] == "nominal"
    assert item.properties[STATUS_PROP] == "acquired"
    assert ext.acquisition_type == AcquisitionType.NOMINAL
    assert ext.status == ProductStatus.ACQUIRED

    # Unknown strings should roundtrip as raw strings
    ext.acquisition_type = "nonstandard"
    assert item.properties[ACQUISITION_TYPE_PROP] == "nonstandard"
    assert ext.acquisition_type == "nonstandard"


def test_collection_top_level_fields() -> None:
    col = make_collection()
    ext = ProductExtension.ext(col, add_if_missing=True)

    ext.product_type = "L1C"
    assert col.extra_fields[TYPE_PROP] == "L1C"


def test_summaries_wrapper_sets_lists() -> None:
    col = make_collection()
    sext = ProductExtension.summaries(col, add_if_missing=True)

    sext.product_type = ["L1C", "L2A"]
    sext.status = [ProductStatus.PLANNED, ProductStatus.ACQUIRED]
    assert col.summaries.lists[TYPE_PROP] == ["L1C", "L2A"]
    assert col.summaries.lists[STATUS_PROP] == [
        ProductStatus.PLANNED,
        ProductStatus.ACQUIRED,
    ]


def test_product_status_values_match_schema() -> None:
    assert {status.value for status in ProductStatus} == {
        "archived",
        "acquired",
        "cancelled",
        "failed",
        "planned",
        "potential",
        "rejected",
        "qualitydegraded",
        "accepted",
    }


def test_extension_hooks_are_declared() -> None:
    assert SCHEMA_URI == "https://stac-extensions.github.io/product/v1.1.0/schema.json"
    assert PRODUCT_EXTENSION_HOOKS.schema_uri == ProductExtension.get_schema_uri()
    assert "product" in PRODUCT_EXTENSION_HOOKS.prev_extension_ids
    assert (
        "https://stac-extensions.github.io/product/v1.0.0/schema.json"
        in PRODUCT_EXTENSION_HOOKS.prev_extension_ids
    )
    assert pystac.STACObjectType.COLLECTION in PRODUCT_EXTENSION_HOOKS.stac_object_types


@pytest.fixture
def product_validator() -> JsonSchemaSTACValidator:
    """Use the upstream schema snapshot without retrieving remote schemas."""
    validator = JsonSchemaSTACValidator()
    schema_path = Path(__file__).parent / "data" / "product-v1.1.0-schema.json"
    validator.schema_cache[SCHEMA_URI] = json.loads(schema_path.read_text())
    return validator


@pytest.mark.parametrize("status", list(ProductStatus))
@pytest.mark.parametrize("quality", [None, *QualityStatus])
def test_item_status_and_quality_roundtrip_against_schema(
    product_validator: JsonSchemaSTACValidator,
    status: ProductStatus,
    quality: QualityStatus | None,
) -> None:
    item = make_item()
    extension = ProductExtension.ext(item, add_if_missing=True)
    extension.apply(status=status, quality_status=quality)
    serialized = json.loads(json.dumps(item.to_dict()))
    assert serialized["properties"][STATUS_PROP] == status.value
    if quality is None:
        assert QUALITY_STATUS_PROP not in serialized["properties"]
    else:
        assert serialized["properties"][QUALITY_STATUS_PROP] == quality.value
    restored = ProductExtension.ext(pystac.Item.from_dict(serialized))
    assert restored.status is status
    assert restored.quality_status is quality
    assert (
        product_validator.validate_extension(
            serialized, pystac.STACObjectType.ITEM, pystac.get_stac_version(), SCHEMA_URI
        )
        == SCHEMA_URI
    )


def test_quality_status_removal_and_apply_defaults() -> None:
    item = make_item()
    extension = ProductExtension.ext(item, add_if_missing=True)
    extension.apply(status=ProductStatus.ACCEPTED, quality_status=QualityStatus.DEGRADED)
    extension.quality_status = None
    assert QUALITY_STATUS_PROP not in item.properties
    assert extension.status is ProductStatus.ACCEPTED
    extension.quality_status = QualityStatus.NOMINAL
    extension.status = None
    assert extension.quality_status is QualityStatus.NOMINAL
    extension.apply()
    assert QUALITY_STATUS_PROP not in item.properties


@pytest.mark.parametrize("field", [STATUS_PROP, QUALITY_STATUS_PROP])
def test_unknown_status_fails_read_and_schema_validation(
    product_validator: JsonSchemaSTACValidator, field: str
) -> None:
    item = make_item()
    extension = ProductExtension.ext(item, add_if_missing=True)
    item.properties[field] = "unknown"
    with pytest.raises(ValueError, match="unknown"):
        _ = extension.status if field == STATUS_PROP else extension.quality_status
    with pytest.raises(pystac.STACValidationError):
        product_validator.validate_extension(
            item.to_dict(), pystac.STACObjectType.ITEM, pystac.get_stac_version(), SCHEMA_URI
        )


def test_asset_quality_fallback_and_override() -> None:
    item = make_item()
    product = ProductExtension.ext(item, add_if_missing=True)
    product.apply(status=ProductStatus.ACCEPTED, quality_status=QualityStatus.NOMINAL)
    asset = pystac.Asset("https://example.com/data.tif")
    item.add_asset("data", asset)
    extension = ProductExtension.ext(asset)
    assert extension.quality_status is QualityStatus.NOMINAL
    extension.quality_status = QualityStatus.DEGRADED
    assert asset.extra_fields[QUALITY_STATUS_PROP] == "degraded"
    assert product.quality_status is QualityStatus.NOMINAL
    extension.quality_status = None
    assert QUALITY_STATUS_PROP not in asset.extra_fields
    assert extension.quality_status is QualityStatus.NOMINAL


def test_collection_quality_assets_and_summaries_validate(
    product_validator: JsonSchemaSTACValidator,
) -> None:
    collection = make_collection()
    extension = ProductExtension.ext(collection, add_if_missing=True)
    extension.apply(status=ProductStatus.ACCEPTED, quality_status=QualityStatus.NOMINAL)
    asset = pystac.Asset("https://example.com/data.tif")
    collection.add_asset("data", asset)
    asset_extension = ProductExtension.ext(asset)
    assert asset_extension.quality_status is None
    asset_extension.apply(status=ProductStatus.ACCEPTED, quality_status=QualityStatus.DEGRADED)
    collection.item_assets = {"data": pystac.ItemAssetDefinition({"roles": ["data"]})}
    definition = ProductExtension.ext(collection.item_assets["data"])
    definition.apply(status=ProductStatus.ACCEPTED, quality_status=QualityStatus.NOMINAL)
    summaries = ProductExtension.summaries(collection)
    summaries.status = [ProductStatus.ACCEPTED, ProductStatus.REJECTED]
    summaries.quality_status = [QualityStatus.NOMINAL, QualityStatus.DEGRADED]
    serialized = json.loads(json.dumps(collection.to_dict()))
    assert serialized[QUALITY_STATUS_PROP] == "nominal"
    assert serialized["assets"]["data"][QUALITY_STATUS_PROP] == "degraded"
    assert serialized["item_assets"]["data"][QUALITY_STATUS_PROP] == "nominal"
    assert serialized["summaries"][QUALITY_STATUS_PROP] == ["nominal", "degraded"]
    restored = pystac.Collection.from_dict(serialized)
    assert ProductExtension.ext(restored).quality_status is QualityStatus.NOMINAL
    assert ProductExtension.summaries(restored).quality_status == ["nominal", "degraded"]
    assert (
        product_validator.validate_extension(
            serialized, pystac.STACObjectType.COLLECTION, pystac.get_stac_version(), SCHEMA_URI
        )
        == SCHEMA_URI
    )
    summaries.quality_status = None
    assert summaries.quality_status is None
    assert QUALITY_STATUS_PROP not in collection.summaries.lists


@pytest.mark.parametrize("qualities", [["unknown"], ["nominal", "nominal"]])
def test_schema_rejects_invalid_quality_summaries(
    product_validator: JsonSchemaSTACValidator, qualities: list[str]
) -> None:
    collection = make_collection()
    ProductExtension.add_to(collection)
    collection.summaries.add(QUALITY_STATUS_PROP, qualities)
    with pytest.raises(pystac.STACValidationError):
        product_validator.validate_extension(
            collection.to_dict(),
            pystac.STACObjectType.COLLECTION,
            pystac.get_stac_version(),
            SCHEMA_URI,
        )
