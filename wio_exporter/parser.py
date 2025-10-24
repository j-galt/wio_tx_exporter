import re
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class Transaction:

    date: str
    description: str
    amount: Decimal
    currency: str
    category: Optional[str] = None
    foreign_amount: Optional[str] = None

    def __hash__(self):
        return hash((self.date, self.description, str(self.amount), self.currency))

    def is_spending(self) -> bool:
        return self.amount < 0

class TransactionParser:

    def __init__(self, current_date_header: str = ""):
        self.current_date = current_date_header

    def parse_transaction(self, element_text: str) -> Optional[Transaction]:
        if not element_text or "AED" not in element_text:
            return None

        lines = [line.strip() for line in element_text.split("\n") if line.strip()]

        if len(lines) < 2:
            return None

        aed_amount = None
        foreign_amount = None
        description_lines = []
        category = None

        for i, line in enumerate(lines):
            if "AED" in line:
                aed_amount = self._extract_amount(line)
                if i + 1 < len(lines) and ("THB" in lines[i + 1] or "USD" in lines[i + 1]):
                    foreign_amount = lines[i + 1]
                description_lines = lines[:i]
                break

        if aed_amount is None:
            return None

        description = description_lines[0] if description_lines else "Unknown"

        if len(description_lines) > 1:
            potential_category = description_lines[1]
            if potential_category and not re.search(r'\d', potential_category):
                category = potential_category
                if len(description_lines) == 2:
                    pass
                else:
                    description = " ".join(description_lines[:-1]) if category else description

        return Transaction(
            date=self.current_date,
            description=description,
            amount=aed_amount,
            currency="AED",
            category=category,
            foreign_amount=foreign_amount,
        )

    @staticmethod
    def _extract_amount(amount_str: str) -> Optional[Decimal]:
        cleaned = amount_str.replace("AED", "").replace(",", "").strip()

        match = re.search(r'[+-]?\d+\.?\d*', cleaned)
        if match:
            try:
                return Decimal(match.group())
            except:
                return None

        return None
