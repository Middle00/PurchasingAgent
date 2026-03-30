import base64
import json
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # GCP
    gcp_project_id: str = "potomax-brands"
    bigquery_sa_key: str = ""  # Base64-encoded service account JSON

    # BigQuery tables
    bq_items_table: str = "scalelean_production.stg_uc_items"
    bq_reorder_table: str = "dbt_clickthrunetwork.rtp_inventory_recomendations"
    bq_feed_table: str = "scalelean_production.algolia__potomacbeads_feed_items_unified"

    # ClickUp
    clickup_api_token: str = ""
    clickup_list_id: str = ""  # List ID for reorder approval tasks

    # Google Sheets
    google_sheets_sa_key: str = ""  # Base64-encoded, defaults to bigquery_sa_key if empty

    # Reorder thresholds
    default_days_supply_threshold: int = 30  # Flag items with < 30 days supply
    phantom_buffer: int = 3  # Units withheld from marketplace inventory reporting

    # Paths
    moq_corrections_path: str = "data/moq_corrections.json"

    def get_bigquery_credentials(self) -> dict:
        """Decode and parse the BigQuery service account key."""
        if not self.bigquery_sa_key:
            raise ValueError("BIGQUERY_SA_KEY environment variable is not set")
        decoded = base64.b64decode(self.bigquery_sa_key).decode("utf-8")
        return json.loads(decoded)

    def get_sheets_credentials(self) -> dict:
        """Decode and parse the Google Sheets service account key."""
        key = self.google_sheets_sa_key or self.bigquery_sa_key
        if not key:
            raise ValueError("No Google Sheets credentials configured")
        decoded = base64.b64decode(key).decode("utf-8")
        return json.loads(decoded)


@lru_cache
def get_settings() -> Settings:
    return Settings()
