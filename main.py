import logging
import sys
from appium import webdriver
from appium.options.ios import XCUITestOptions

from wio_exporter.config import default_config
from wio_exporter.scraper import TransactionScraper
from wio_exporter.exporter import CSVExporter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Wio Transaction Exporter")

    driver = None

    try:
        logger.info(f"Connecting to Appium server at {default_config.appium_server_url}")

        options = XCUITestOptions()
        caps = default_config.to_capabilities()

        options.platform_name = caps["platformName"]
        options.device_name = caps["appium:deviceName"]
        options.udid = caps["appium:udid"]
        options.automation_name = caps["appium:automationName"]
        options.new_command_timeout = caps["appium:newCommandTimeout"]

        options.set_capability("appium:includeSafariInWebviews", caps["appium:includeSafariInWebviews"])
        options.set_capability("appium:connectHardwareKeyboard", caps["appium:connectHardwareKeyboard"])

        driver = webdriver.Remote(
            default_config.appium_server_url,
            options=options
        )

        logger.info("Connected to device successfully")

        scraper = TransactionScraper(driver)

        logger.info("Starting transaction extraction...")
        transactions = scraper.scrape_all_transactions()

        if not transactions:
            logger.warning("No spending transactions found!")
            return

        exporter = CSVExporter()
        output_file = exporter.export(transactions)

        logger.info(f"✓ Successfully exported {len(transactions)} transactions to {output_file}")

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        sys.exit(1)

    finally:
        if driver:
            driver.quit()
            logger.info("Closed Appium session")


if __name__ == "__main__":
    main()
