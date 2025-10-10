"""CSV export functionality for transactions."""

import csv
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from .parser import Transaction

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports transactions to CSV format."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize exporter.

        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export(self, transactions: List[Transaction], filename: str = None) -> Path:
        """
        Export transactions to CSV file.

        Args:
            transactions: List of Transaction objects to export
            filename: Optional custom filename. If not provided, uses timestamp.

        Returns:
            Path to the created CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wio_transactions_{timestamp}.csv"

        filepath = self.output_dir / filename

        logger.info(f"Exporting {len(transactions)} transactions to {filepath}")

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["date", "description", "amount", "currency", "category"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for txn in transactions:
                writer.writerow({
                    "date": txn.date,
                    "description": txn.description,
                    "amount": str(txn.amount),
                    "currency": txn.currency,
                    "category": txn.category or "",
                })

        logger.info(f"Export completed: {filepath}")
        return filepath
