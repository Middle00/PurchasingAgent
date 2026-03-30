"""BigQuery service — read-only access to inventory and product data."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from google.cloud import bigquery
from google.oauth2 import service_account

from src.models.product import Product, SupplierCodes

if TYPE_CHECKING:
    from src.config import Settings

logger = logging.getLogger(__name__)


class BigQueryService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: bigquery.Client | None = None

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            creds_dict = self.settings.get_bigquery_credentials()
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/bigquery.readonly"],
            )
            self._client = bigquery.Client(
                project=self.settings.gcp_project_id,
                credentials=credentials,
            )
        return self._client

    def get_items_below_threshold(self) -> list[Product]:
        """
        Query rtp_inventory_recomendations for items below their days-supply threshold.
        Joins to stg_uc_items for product master data including supplier codes.
        """
        query = f"""
        SELECT
            rec.item_id          AS sku,
            rec.item_name        AS name,
            rec.category,
            rec.days_supply,
            rec.daily_burn_rate,
            rec.current_stock,
            rec.reorder_point,
            item.manufacturer,
            item.manufacturer_code,
            item.sell_uom,
            item.buy_uom,
            item.uom_conversion_factor,
            item.moq,
            item.moq_increment,
            item.lead_time_days,
            item.unit_cost,
            -- Supplier-specific codes from product attributes JSON
            JSON_VALUE(item.attributes, '$.supplier_codes.beadsmith')  AS code_beadsmith,
            JSON_VALUE(item.attributes, '$.supplier_codes.starman')    AS code_starman,
            JSON_VALUE(item.attributes, '$.supplier_codes.allbeads')   AS code_allbeads,
            JSON_VALUE(item.attributes, '$.supplier_codes.rutkovsky')  AS code_rutkovsky,
            JSON_VALUE(item.attributes, '$.supplier_codes.gnb')        AS code_gnb
        FROM
            `{self.settings.bq_reorder_table}` AS rec
        LEFT JOIN
            `{self.settings.bq_items_table}` AS item
            ON rec.item_id = item.item_id
        WHERE
            rec.days_supply < {self.settings.default_days_supply_threshold}
            AND rec.is_active = TRUE
        ORDER BY
            rec.days_supply ASC
        """
        logger.info("Querying BigQuery for items below threshold")
        rows = list(self.client.query(query).result())
        return [self._row_to_product(row) for row in rows]

    def get_product_by_sku(self, sku: str) -> Product | None:
        """Fetch a single product record by SKU."""
        query = f"""
        SELECT
            item.item_id         AS sku,
            item.item_name       AS name,
            item.category,
            item.manufacturer,
            item.manufacturer_code,
            item.sell_uom,
            item.buy_uom,
            item.uom_conversion_factor,
            item.moq,
            item.moq_increment,
            item.lead_time_days,
            item.unit_cost,
            0                    AS current_stock,
            0                    AS reorder_point,
            NULL                 AS days_supply,
            NULL                 AS daily_burn_rate,
            JSON_VALUE(item.attributes, '$.supplier_codes.beadsmith')  AS code_beadsmith,
            JSON_VALUE(item.attributes, '$.supplier_codes.starman')    AS code_starman,
            JSON_VALUE(item.attributes, '$.supplier_codes.allbeads')   AS code_allbeads,
            JSON_VALUE(item.attributes, '$.supplier_codes.rutkovsky')  AS code_rutkovsky,
            JSON_VALUE(item.attributes, '$.supplier_codes.gnb')        AS code_gnb
        FROM
            `{self.settings.bq_items_table}` AS item
        WHERE
            item.item_id = @sku
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("sku", "STRING", sku)]
        )
        rows = list(self.client.query(query, job_config=job_config).result())
        if not rows:
            return None
        return self._row_to_product(rows[0])

    def _row_to_product(self, row) -> Product:
        """Convert a BigQuery row to a Product model."""
        supplier_codes = SupplierCodes(
            beadsmith=row.get("code_beadsmith"),
            starman=row.get("code_starman"),
            allbeads=row.get("code_allbeads"),
            rutkovsky=row.get("code_rutkovsky"),
            gnb=row.get("code_gnb"),
        )
        return Product(
            sku=str(row["sku"]),
            name=str(row["name"]),
            category=row.get("category") or "",
            manufacturer=row.get("manufacturer"),
            manufacturer_code=row.get("manufacturer_code"),
            supplier_codes=supplier_codes,
            sell_uom=row.get("sell_uom") or "EA",
            buy_uom=row.get("buy_uom") or "EA",
            uom_conversion_factor=row.get("uom_conversion_factor"),
            moq=int(row.get("moq") or 1),
            moq_increment=int(row.get("moq_increment") or row.get("moq") or 1),
            lead_time_days=int(row.get("lead_time_days") or 14),
            unit_cost=row.get("unit_cost"),
            current_stock=int(row.get("current_stock") or 0),
            reorder_point=int(row.get("reorder_point") or 0),
            days_supply=row.get("days_supply"),
            daily_burn_rate=row.get("daily_burn_rate"),
        )
