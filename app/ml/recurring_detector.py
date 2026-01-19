"""
Recurring Expense Detector

Detects subscriptions and recurring bills from transaction history by:
1. Grouping transactions by normalized merchant name
2. Analyzing amount consistency
3. Detecting periodicity in dates (weekly, monthly, yearly, etc.)
4. Scoring confidence based on pattern strength
"""

import re
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd


# Standard billing cycles in days
FREQUENCIES = {
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "quarterly": 91,
    "yearly": 365,
}


class RecurringExpenseDetector:
    """Detect recurring expenses from transaction history."""

    def __init__(self, min_occurrences: int = 3):
        """
        Args:
            min_occurrences: Minimum number of transactions to consider as recurring
        """
        self.min_occurrences = min_occurrences

    def detect(self, transactions: list[dict]) -> list[dict]:
        """
        Find recurring expenses in transaction data.

        Args:
            transactions: List of dicts with keys: date, amount, description

        Returns:
            List of detected recurring expenses with confidence scores
        """
        if not transactions:
            return []

        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"])

        # Normalize merchant names
        df["merchant_normalized"] = df["description"].apply(self._normalize_merchant)

        # Group by merchant
        recurring = []

        for merchant, group in df.groupby("merchant_normalized"):
            if len(group) < self.min_occurrences:
                continue

            result = self._analyze_merchant(merchant, group)
            if result and result["confidence"] > 0.5:
                recurring.append(result)

        # Sort by confidence
        recurring.sort(key=lambda x: x["confidence"], reverse=True)

        return recurring

    def _normalize_merchant(self, description: str) -> str:
        """
        Normalize merchant name for grouping.

        Handles variations like:
        - "NETFLIX.COM" -> "netflix"
        - "SPOTIFY USA" -> "spotify"
        - "Amazon Prime*1234" -> "amazon prime"
        """
        text = description.lower()

        # Remove common suffixes/prefixes and noise
        patterns_to_remove = [
            r"\*\d+",  # *1234
            r"#\d+",  # #1234
            r"\d{6,}",  # Long numbers (transaction IDs)
            r"\.com",
            r"\.net",
            r"\.org",
            r"\s+inc\.?$",
            r"\s+llc\.?$",
            r"\s+ltd\.?$",
            r"\s+usa$",
            r"\s+us$",
            r"^pos\s+",
            r"^ach\s+",
            r"^debit\s+",
            r"^purchase\s+",
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Keep only alphanumeric and spaces
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Collapse whitespace
        text = " ".join(text.split())

        return text.strip()[:50]  # Limit length

    def _analyze_merchant(self, merchant: str, group: pd.DataFrame) -> Optional[dict]:
        """Analyze a merchant's transactions for recurring patterns."""
        if merchant == "" or len(merchant) < 2:
            return None

        amounts = group["amount"].values
        dates = group["date"].sort_values()

        # Amount consistency (coefficient of variation)
        mean_amount = np.mean(amounts)
        if mean_amount == 0:
            return None

        amount_std = np.std(amounts)
        amount_cv = amount_std / abs(mean_amount)
        amount_consistent = amount_cv < 0.15  # Less than 15% variation

        # Detect periodicity in dates
        intervals = dates.diff().dt.days.dropna().values

        if len(intervals) < 2:
            return None

        freq_result = self._detect_frequency(intervals)

        if not freq_result:
            return None

        # Calculate confidence score
        confidence = self._calculate_confidence(
            amount_consistent=amount_consistent,
            amount_cv=amount_cv,
            interval_consistency=freq_result["consistency"],
            num_occurrences=len(group),
        )

        # Predict next occurrence
        last_date = dates.max()
        next_date = last_date + pd.Timedelta(days=freq_result["days"])

        return {
            "merchant": merchant.title(),
            "average_amount": round(float(np.mean(amounts)), 2),
            "frequency_days": freq_result["days"],
            "frequency_type": freq_result["type"],
            "confidence": round(confidence, 2),
            "next_expected_date": next_date.strftime("%Y-%m-%d"),
            "occurrences": len(group),
            "first_seen": dates.min().strftime("%Y-%m-%d"),
            "last_seen": dates.max().strftime("%Y-%m-%d"),
        }

    def _detect_frequency(self, intervals: np.ndarray) -> Optional[dict]:
        """Detect the frequency pattern from date intervals."""
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)

        # Find closest standard frequency
        best_match = None
        best_diff = float("inf")

        for freq_name, freq_days in FREQUENCIES.items():
            diff = abs(mean_interval - freq_days)
            # Must be within 20% of the standard frequency
            if diff < best_diff and diff < freq_days * 0.25:
                best_diff = diff
                best_match = freq_name

        if not best_match:
            return None

        # Calculate consistency (how regular the intervals are)
        consistency = 1 - (std_interval / mean_interval) if mean_interval > 0 else 0
        consistency = max(0, min(1, consistency))

        return {
            "type": best_match,
            "days": FREQUENCIES[best_match],
            "consistency": consistency,
        }

    def _calculate_confidence(
        self,
        amount_consistent: bool,
        amount_cv: float,
        interval_consistency: float,
        num_occurrences: int,
    ) -> float:
        """Calculate overall confidence score (0-1)."""
        score = 0.0

        # Amount consistency (0-0.3)
        if amount_consistent:
            score += 0.3
        else:
            score += max(0, 0.3 - amount_cv * 0.5)

        # Interval consistency (0-0.4)
        score += 0.4 * interval_consistency

        # Number of occurrences (0-0.3)
        # Max out at 6 occurrences
        occurrence_score = min(num_occurrences / 6, 1.0)
        score += 0.3 * occurrence_score

        return min(score, 1.0)


def detect_recurring_expenses(transactions: list[dict], min_occurrences: int = 3) -> list[dict]:
    """
    Convenience function to detect recurring expenses.

    Args:
        transactions: List of transaction dicts with date, amount, description
        min_occurrences: Minimum occurrences to consider recurring

    Returns:
        List of detected recurring expenses
    """
    detector = RecurringExpenseDetector(min_occurrences=min_occurrences)
    return detector.detect(transactions)
