"""
Google Sheets service — generates overnight cart summary spreadsheet.

Phase 3 implementation. Currently a stub with the data contract defined.
After the overnight cart-building run, this service creates (or overwrites) a
Google Sheet with one row per cart item so the buyer can review in the morning.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.models.purchase_order import CartItem

if TYPE_CHECKING:
    from src.config import Settings

logger = logging.getLogger(__name__)

SHEET_COLUMNS = [
    "item_id",
    "description",
    "manufacturer_code",
    "current_inventory",
    "cost",
    "quantity_added",
    "supplier",
    "cart_name",
]


class GoogleSheetsService:
    """
    Writes cart summary data to a Google Sheet for morning review.

    Phase 3 stub — interface and data model are defined; write logic is deferred.

    Expected sheet layout (one row per CartItem):
    | item_id | description | manufacturer_code | current_inventory |
    | cost | quantity_added | supplier | cart_name |
    """

    def __init__(self, settings: "Settings"):
        self.settings = settings
        # Phase 3: initialize gspread client here
        # creds = service_account.Credentials.from_service_account_info(
        #     settings.get_sheets_credentials(),
        #     scopes=["https://www.googleapis.com/auth/spreadsheets"],
        # )
        # self.gc = gspread.authorize(creds)

    def write_cart_summary(
        self,
        cart_items: list[CartItem],
        spreadsheet_id: str,
        worksheet_name: str = "Cart Summary",
    ) -> str:
        """
        Write cart items to the specified Google Sheet.

        Args:
            cart_items: Items to write.
            spreadsheet_id: Target Google Sheet ID.
            worksheet_name: Target worksheet tab name.

        Returns:
            URL of the updated spreadsheet.

        Phase 3: implement using gspread.
        """
        logger.info(
            f"Phase 3 not yet implemented — would write {len(cart_items)} items "
            f"to sheet {spreadsheet_id} tab '{worksheet_name}'"
        )
        # Phase 3 implementation:
        # sheet = self.gc.open_by_key(spreadsheet_id)
        # try:
        #     ws = sheet.worksheet(worksheet_name)
        #     ws.clear()
        # except gspread.WorksheetNotFound:
        #     ws = sheet.add_worksheet(worksheet_name, rows=1000, cols=len(SHEET_COLUMNS))
        #
        # rows = [SHEET_COLUMNS] + [self._item_to_row(item) for item in cart_items]
        # ws.update(rows, value_input_option="USER_ENTERED")
        # return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        return ""

    def _item_to_row(self, item: CartItem) -> list:
        """Convert a CartItem to a spreadsheet row."""
        return [
            item.item_id,
            item.description,
            item.manufacturer_code or "",
            item.current_inventory,
            float(item.cost) if item.cost is not None else "",
            item.quantity_added,
            item.supplier,
            item.cart_name,
        ]
