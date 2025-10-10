# Wio Transaction Exporter

Python application to export transaction history from the Wio banking app (iOS) to CSV using Appium automation.

## Features

- ✓ Automated transaction extraction from iOS app
- ✓ Scrolling with duplicate detection
- ✓ Filters only spending transactions (negative amounts)
- ✓ CSV export with date, description, amount, currency, and category
- ✓ Modular, clean code structure

## Prerequisites

- Python 3.9+
- Appium Server running (default: `http://localhost:4723`)
- iOS device connected with Wio app installed
- Device configured in Appium Inspector

## Installation

1. Install dependencies using Poetry:
```bash
poetry install
```

Or using pip:
```bash
pip install appium-python-client pandas
```

2. Update device configuration in `wio_exporter/config.py` if needed (UDID, device name, etc.)

## Usage

1. Start Appium server
2. Open Wio app on your iPhone
3. Navigate to the Activities (transaction history) screen
4. Run the exporter:

```bash
poetry run python main.py
```

Or if using venv:
```bash
python main.py
```

5. Find your exported CSV in the `output/` directory

## Project Structure

```
wio_tx_exporter/
├── wio_exporter/
│   ├── __init__.py
│   ├── config.py          # Appium capabilities and element locators
│   ├── parser.py          # Transaction data parser
│   ├── scraper.py         # Scroll handler with duplicate detection
│   └── exporter.py        # CSV export functionality
├── main.py                # Main entry point
├── pyproject.toml         # Poetry dependencies
├── PLAN.md               # Implementation plan
└── README.md             # This file
```

## Output Format

CSV file with columns:
- `date` - Transaction date (e.g., "SUN, 5 OCTOBER")
- `description` - Merchant/transaction description
- `amount` - Amount in decimal format (negative for spendings)
- `currency` - Currency code (AED)
- `category` - Transaction category (e.g., Restaurant, Shopping)

## Logs

Application logs are written to:
- Console (stdout)
- `wio_exporter.log` file

## Future Enhancements

- [ ] Login automation
- [ ] Date range filters configuration
- [ ] Support for custom date filters from app UI
- [ ] Configuration file for runtime settings

## Troubleshooting

**Connection issues:**
- Ensure Appium server is running on port 4723
- Verify device UDID matches configuration
- Check that WebDriverAgent is properly installed on device

**No transactions found:**
- Verify you're on the Activities screen before running
- Check element locators in `config.py` match your app version
- Enable DEBUG logging to see detailed extraction info

**Duplicate transactions:**
- Scraper automatically deduplicates based on date, description, and amount
- Check logs for "Already seen" messages
