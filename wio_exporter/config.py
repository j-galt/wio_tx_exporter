import os
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


@dataclass
class AppiumConfig:
    """Appium connection configuration."""

    platform_name: str = "iOS"
    device_name: str = os.getenv("DEVICE_NAME", "iPhone")
    udid: str = os.getenv("DEVICE_UDID", "YOUR_DEVICE_UDID_HERE")
    automation_name: str = "XCUITest"
    include_safari_in_webviews: bool = True
    new_command_timeout: int = 3600
    connect_hardware_keyboard: bool = True
    appium_server_url: str = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")

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

default_config = AppiumConfig()
