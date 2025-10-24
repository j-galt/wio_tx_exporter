
import logging
import time
from typing import List, Set, Dict, Optional
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy

from .parser import TransactionParser, Transaction

logger = logging.getLogger(__name__)


class TransactionScraper:
    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.parser = TransactionParser()

    def scrape_all_transactions(self) -> List[Transaction]:
        transactions: List[Transaction] = []
        no_new_count = 0
        max_no_new = 3
        processed_tx_ids: Set[str] = set()

        while no_new_count < max_no_new:
            visible_txns = []
            new_count = 0

            for retry in range(3):
                visible_txns = self._get_visible_transaction_elements()
                if visible_txns:
                    break
                if retry < 2:
                    logger.warning(f"No visible transactions found, retry {retry + 1}/3...")
                    time.sleep(0.5)

            logger.info(f"Found {len(visible_txns)} visible transactions")

            if not visible_txns:
                logger.warning("No visible transactions found after 3 retries, stopping")
                break

            visible_txns = [tx for tx in visible_txns if tx.get_attribute('UID') not in processed_tx_ids]

            for i, txn_elem in enumerate(visible_txns):
                txn_data = self._extract_transaction_details(txn_elem, i)

                txn = self._parse_transaction(txn_data)

                if txn and txn.is_spending():
                    transactions.append(txn)
                    new_count += 1
                    logger.info(f"[{i}] New: {txn.description} {txn.amount} AED")


            if new_count == 0:
                no_new_count += 1
                logger.info(f"No new transactions. Attempt {no_new_count}/{max_no_new}")
            else:
                no_new_count = 0

            processed_tx_ids.update([tx.get_attribute('UID') for tx in visible_txns])

            if no_new_count < max_no_new:
                self._scroll_to_last_visible()

        return transactions  

    def _get_visible_transaction_elements(self) -> List:
        try:
            all_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                '//XCUIElementTypeStaticText'
            )

            window_size = self.driver.get_window_size()
            screen_height = window_size['height']
            screen_width = window_size['width']

            visible_txns = []

            for elem in all_elements:
                try:
                    is_visible = elem.get_attribute("visible") == "true"
                    if not is_visible:
                        continue

                    text = elem.get_attribute("value") or elem.get_attribute("label") or ""
                    if "AED" not in text:
                        continue

                    loc = elem.location
                    size = elem.size
                    x, y = loc.get('x', 0), loc.get('y', 0)
                    h = size.get('height', 0)

                    if y <= 0 or h <= 0:
                        continue

                    if x < 0 or x >= screen_width or y >= screen_height:
                        continue

                    visible_txns.append(elem)

                except Exception as e:
                    continue

            return visible_txns

        except Exception as e:
            logger.error(f"Error getting visible elements: {e}")
            return []

    def _extract_transaction_details(self, element, index: int) -> Optional[Dict]:
        try:
            preview_text = element.get_attribute("value") or element.get_attribute("label") or ""
            txn_data = {"preview_text": preview_text}
            return txn_data
        except Exception as e:
            logger.error(f"  [{index}] Error extracting details: {e}")
            return None

    def _scroll_to_last_visible(self):
        try:
            visible_txns = self._get_visible_transaction_elements()

            logger.info(f"Visible transactions: {len(visible_txns)}")

            if len(visible_txns) < 2:
                logger.warning("Not enough visible transactions for element scroll, using swipe fallback")
                return

            last_txn = visible_txns[-1]
            first_txn = visible_txns[0]

            self.driver.scroll(last_txn, first_txn, duration=5000)
            
        except Exception as e:
            logger.warning(f"Element-based scroll failed: {e}, using swipe fallback")

    def _parse_transaction(self, txn_data: Dict) -> Optional[Transaction]:
        try:
            preview_text = txn_data.get("preview_text", "")
            if not preview_text:
                return None

            txn = self.parser.parse_transaction(preview_text)

            if txn and txn_data.get("date"):
                txn.date = txn_data["date"]

            return txn

        except Exception as e:
            logger.error(f"Error parsing transaction: {e}")
            return None
