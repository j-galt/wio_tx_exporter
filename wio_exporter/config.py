"""Configuration for Appium connection and app interaction."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AppiumConfig:
    """Appium connection configuration."""

    platform_name: str = "iOS"
    device_name: str = "iPhone"
    udid: str = "00008140-000C19E40E33001C"
    automation_name: str = "XCUITest"
    include_safari_in_webviews: bool = True
    new_command_timeout: int = 3600
    connect_hardware_keyboard: bool = True
    appium_server_url: str = "http://localhost:4723"

    def to_capabilities(self) -> Dict[str, Any]:
        """Convert config to Appium desired capabilities format."""
        return {
            "platformName": self.platform_name,
            "appium:deviceName": self.device_name,
            "appium:udid": self.udid,
            "appium:automationName": self.automation_name,
            "appium:includeSafariInWebviews": self.include_safari_in_webviews,
            "appium:newCommandTimeout": self.new_command_timeout,
            "appium:connectHardwareKeyboard": self.connect_hardware_keyboard,
        }


@dataclass
class TransactionLocators:
    """XPath locators for transaction elements."""

    # Transaction cards are XCUIElementTypeStaticText containing merchant, category, and amount
    # Each transaction is a multi-line static text element
    # Check value, label, or name attributes for "AED" text
    transaction_xpath: str = '//XCUIElementTypeStaticText[contains(@value, "AED") or contains(@label, "AED") or contains(@name, "AED")]'

    # Scroll view container
    scroll_view_xpath: str = '//XCUIElementTypeScrollView'

    # Date headers (e.g., "SUN, 5 OCTOBER", "TUE, 30 SEPTEMBER")
    # Match any date header by looking for day names followed by comma
    date_header_xpath: str = '//XCUIElementTypeStaticText[contains(@value, "DAY,") or contains(@value, "MON,") or contains(@value, "TUE,") or contains(@value, "WED,") or contains(@value, "THU,") or contains(@value, "FRI,") or contains(@value, "SAT,") or contains(@value, "SUN,")]'


# Default configuration instance
default_config = AppiumConfig()
default_locators = TransactionLocators()
