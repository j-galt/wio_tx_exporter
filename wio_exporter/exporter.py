import csv
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from .parser import Transaction

logger = logging.getLogger(__name__)


class CSVExporter:

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export(self, transactions: List[Transaction], filename: str = None) -> Path:
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
