"""Transaction scraper with proper visibility handling."""

import logging
import time
from typing import List, Set, Dict, Optional
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy

from .config import TransactionLocators
from .parser import TransactionParser, Transaction

logger = logging.getLogger(__name__)


class TransactionScraper:
    """Simplified transaction scraper with proper visibility filtering."""

    def __init__(self, driver: webdriver.Remote, locators: TransactionLocators):
        self.driver = driver
        self.locators = locators
        self.parser = TransactionParser()
        self.seen_references: Set[str] = set()
        self.last_processed_ref: Optional[str] = None

    def scrape_all_transactions(self) -> List[Transaction]:
        """
        Scrape all transactions by:
        1. Finding visible transaction elements
        2. Clicking each to get reference number
        3. Scrolling to the last visible element
        4. Repeat until no new transactions found
        """
        transactions: List[Transaction] = []
        no_new_count = 0
        max_no_new = 3

        logger.info("Starting transaction scraping...")

        while no_new_count < max_no_new:
            # Get visible transaction elements with retry
            visible_txns = []
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

            # Process all visible transactions
            new_count = 0
            for i in range(len(visible_txns)):
                # Re-fetch elements after each click to avoid stale references
                visible_txns = self._get_visible_transaction_elements()

                # Check if index is still valid
                if i >= len(visible_txns):
                    logger.warning(f"  [{i}] Index out of range after refetch, breaking")
                    break

                txn_elem = visible_txns[i]

                # Extract transaction details
                txn_data = self._extract_transaction_details(txn_elem, i)

                if txn_data and txn_data.get("ref_number"):
                    ref_num = txn_data["ref_number"]

                    # Check if this is the last element and matches previous batch
                    if i == len(visible_txns) - 1 and ref_num == self.last_processed_ref:
                        logger.info(f"  [{i}] Last transaction matches previous batch (ref: {ref_num}), stopping")
                        no_new_count = max_no_new  # Force exit
                        break

                    # Skip if already seen
                    if ref_num in self.seen_references:
                        logger.info(f"  [{i}] Duplicate ref: {ref_num}")
                    else:
                        # Add to seen set
                        self.seen_references.add(ref_num)

                        # Parse transaction
                        txn = self._parse_transaction(txn_data)
                        if txn and txn.is_spending():
                            transactions.append(txn)
                            new_count += 1
                            logger.info(f"  [{i}] New: {txn.description} {txn.amount} AED (ref: {ref_num})")

                    # Update last processed ref if this is the last element
                    if i == len(visible_txns) - 1:
                        self.last_processed_ref = ref_num

            logger.info(f"Batch: {new_count} new transactions (total: {len(transactions)})")

            # Check if we found new transactions
            if new_count == 0:
                no_new_count += 1
                logger.info(f"No new transactions. Attempt {no_new_count}/{max_no_new}")
            else:
                no_new_count = 0

            # Scroll to load more
            if no_new_count < max_no_new:
                self._scroll_to_last_visible()

        logger.info(f"Scraping completed. Found {len(transactions)} unique spending transactions")
        return transactions

    def _get_visible_transaction_elements(self) -> List:
        """
        Get only visible transaction elements that are actually on screen.

        Returns:
            List of WebElement objects that are visible and contain AED
        """
        try:
            # Find all static text elements
            all_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                '//XCUIElementTypeStaticText'
            )

            # Get window size to check if element is in viewport
            window_size = self.driver.get_window_size()
            screen_height = window_size['height']
            screen_width = window_size['width']

            visible_txns = []
            debug_counts = {
                "total": len(all_elements),
                "visible_attr": 0,
                "has_aed": 0,
                "valid_position": 0,
                "final": 0
            }

            for elem in all_elements:
                try:
                    # Check if element is marked as visible
                    is_visible = elem.get_attribute("visible") == "true"
                    if not is_visible:
                        continue
                    debug_counts["visible_attr"] += 1

                    # Check if element contains AED (transaction indicator)
                    text = elem.get_attribute("value") or elem.get_attribute("label") or ""
                    if "AED" not in text:
                        continue
                    debug_counts["has_aed"] += 1

                    # Check if element has valid position and size
                    loc = elem.location
                    size = elem.size
                    x, y = loc.get('x', 0), loc.get('y', 0)
                    h = size.get('height', 0)

                    # Skip elements with invalid dimensions
                    if y <= 0 or h <= 0:
                        continue

                    # Skip elements outside viewport
                    if x < 0 or x >= screen_width or y >= screen_height:
                        continue

                    debug_counts["valid_position"] += 1

                    # This is a valid visible transaction element
                    visible_txns.append(elem)
                    debug_counts["final"] += 1

                except Exception as e:
                    # Skip elements that throw errors
                    continue

            logger.debug(f"Element filtering: {debug_counts}")
            return visible_txns

        except Exception as e:
            logger.error(f"Error getting visible elements: {e}")
            return []

    def _extract_transaction_details(self, element, index: int) -> Optional[Dict]:
        """
        Click on transaction element and extract details from details page.

        Args:
            element: Transaction element to click
            index: Element index for logging

        Returns:
            Dictionary with transaction data or None if failed
        """
        try:
            # Get preview text from list view
            preview_text = element.get_attribute("value") or element.get_attribute("label") or ""
            logger.info(f"  [{index}] Clicking: {preview_text[:60]}")

            # Click the element
            element.click()
            time.sleep(0.3)  # Wait for details page to load

            # Extract data from details page
            txn_data = {"preview_text": preview_text}

            # Extract reference number (required)
            ref_num = self._extract_field_value("Reference number")
            if ref_num:
                txn_data["ref_number"] = ref_num
            else:
                logger.warning(f"  [{index}] No reference number found")

            # Extract other fields
            txn_data["date"] = self._extract_field_value("Date")
            txn_data["amount"] = self._extract_field_value("Amount")
            txn_data["merchant"] = self._extract_field_value("Merchant name")
            txn_data["category"] = self._extract_field_value("Category")

            # Go back to list view
            self._go_back()

            return txn_data

        except Exception as e:
            logger.error(f"  [{index}] Error extracting details: {e}")
            # Try to go back anyway
            try:
                self._go_back()
            except:
                pass
            return None

    def _extract_field_value(self, field_name: str) -> Optional[str]:
        """
        Extract value for a field from details page.

        Args:
            field_name: Name of the field (e.g., "Reference number")

        Returns:
            Field value or None if not found
        """
        try:
            elem = self.driver.find_element(
                AppiumBy.XPATH,
                f'//XCUIElementTypeStaticText[contains(@value, "{field_name}")]'
            )
            text = elem.get_attribute("value") or ""
            # Parse "Field name\nValue" format
            parts = text.split("\n")
            if len(parts) >= 2:
                return parts[1].strip()
        except:
            pass
        return None

    def _go_back(self):
        """Navigate back to list view."""
        back_button = self.driver.find_element(
            AppiumBy.XPATH,
            '//XCUIElementTypeButton[@name="Go back"]'
        )
        back_button.click()
        time.sleep(0.5)

    def _scroll_to_last_visible(self):
        """Scroll down to load more transactions."""
        try:
            # Get window size
            window_size = self.driver.get_window_size()
            screen_height = window_size['height']
            screen_width = window_size['width']

            # Smaller scroll to avoid scrolling too far
            # Don't rely on element coordinates to avoid stale reference issues
            start_x = screen_width // 2
            start_y = int(screen_height * 0.75)  # Start at 75% from top
            end_x = screen_width // 2
            end_y = int(screen_height * 0.4)  # End at 40% from top (less distance)

            logger.info(f"Scrolling from y={start_y} to y={end_y}")

            self.driver.swipe(start_x, start_y, end_x, end_y, duration=600)
            time.sleep(0.5)  # Let UI settle

        except Exception as e:
            logger.warning(f"Scroll failed: {e}")

    def _parse_transaction(self, txn_data: Dict) -> Optional[Transaction]:
        """
        Parse transaction data into Transaction object.

        Args:
            txn_data: Dictionary with transaction data

        Returns:
            Transaction object or None if parsing failed
        """
        try:
            # Parse from preview text which contains all info
            preview_text = txn_data.get("preview_text", "")
            if not preview_text:
                return None

            txn = self.parser.parse_transaction(preview_text)

            # Override date with actual date from details page
            if txn and txn_data.get("date"):
                txn.date = txn_data["date"]

            return txn

        except Exception as e:
            logger.error(f"Error parsing transaction: {e}")
            return None

    def reset(self):
        """Reset scraper state for a new session."""
        self.seen_references.clear()
        self.last_processed_ref = None
        logger.info("Scraper state reset")
