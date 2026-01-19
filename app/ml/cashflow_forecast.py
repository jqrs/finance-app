"""
Cashflow Forecaster

Predicts future account balances by:
1. Learning day-of-week spending patterns
2. Learning day-of-month patterns (salary, rent, etc.)
3. Incorporating known recurring expenses
4. Using exponential smoothing for the trend
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd


class CashflowForecaster:
    """Predict future account balances."""

    def __init__(self):
        self.daily_pattern = {}  # day_of_week -> avg daily flow
        self.monthly_pattern = {}  # day_of_month -> avg daily flow
        self.avg_daily_flow = 0.0
        self.std_daily_flow = 0.0
        self.is_trained = False

    def train(
        self,
        transactions: list[dict],
        recurring_expenses: Optional[list[dict]] = None,
    ) -> dict:
        """
        Train on historical transaction data.

        Args:
            transactions: List of dicts with date, amount
            recurring_expenses: Optional list of detected recurring expenses

        Returns:
            Training summary
        """
        if not transactions:
            return {"trained": False, "days": 0}

        self.recurring = recurring_expenses or []

        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"])

        # Aggregate to daily net flow
        daily = df.groupby("date")["amount"].sum().reset_index()
        daily.columns = ["date", "daily_flow"]

        # Fill missing dates with 0
        date_range = pd.date_range(daily["date"].min(), daily["date"].max())
        daily = daily.set_index("date").reindex(date_range, fill_value=0).reset_index()
        daily.columns = ["date", "daily_flow"]

        # Add features
        daily["day_of_week"] = daily["date"].dt.dayofweek
        daily["day_of_month"] = daily["date"].dt.day

        # Learn patterns
        self.daily_pattern = daily.groupby("day_of_week")["daily_flow"].mean().to_dict()
        self.monthly_pattern = daily.groupby("day_of_month")["daily_flow"].mean().to_dict()

        self.avg_daily_flow = float(daily["daily_flow"].mean())
        self.std_daily_flow = float(daily["daily_flow"].std())

        self.is_trained = True

        return {
            "trained": True,
            "days": len(daily),
            "avg_daily_flow": round(self.avg_daily_flow, 2),
        }

    def predict(
        self,
        current_balance: float,
        days_ahead: int = 30,
    ) -> list[dict]:
        """
        Predict daily balances for next N days.

        Args:
            current_balance: Starting balance
            days_ahead: Number of days to forecast

        Returns:
            List of daily predictions with confidence intervals
        """
        if not self.is_trained:
            return []

        predictions = []
        balance = current_balance
        today = pd.Timestamp.today()

        # Calculate overall average for adjustments
        dow_avg = np.mean(list(self.daily_pattern.values())) if self.daily_pattern else 0
        dom_avg = np.mean(list(self.monthly_pattern.values())) if self.monthly_pattern else 0

        for i in range(1, days_ahead + 1):
            future_date = today + pd.Timedelta(days=i)

            # Base prediction
            daily_flow = self.avg_daily_flow

            # Day-of-week adjustment
            dow = future_date.dayofweek
            dow_adj = self.daily_pattern.get(dow, 0) - dow_avg
            daily_flow += dow_adj * 0.5  # Partial weight

            # Day-of-month adjustment (for salary, rent patterns)
            dom = future_date.day
            dom_adj = self.monthly_pattern.get(dom, 0) - dom_avg
            daily_flow += dom_adj * 0.3  # Partial weight

            # Add known recurring expenses
            recurring_flow = self._get_recurring_flow(future_date)
            daily_flow += recurring_flow

            # Update balance
            balance += daily_flow

            # Uncertainty grows with time
            uncertainty = self.std_daily_flow * np.sqrt(i) * 0.5

            predictions.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "predicted_balance": round(balance, 2),
                "daily_flow": round(daily_flow, 2),
                "lower_bound": round(balance - 1.96 * uncertainty, 2),
                "upper_bound": round(balance + 1.96 * uncertainty, 2),
            })

        return predictions

    def _get_recurring_flow(self, date: pd.Timestamp) -> float:
        """Calculate expected recurring expense flow for a date."""
        total = 0.0

        for rec in self.recurring:
            if self._is_recurring_due(rec, date):
                total += rec.get("average_amount", 0)

        return total

    def _is_recurring_due(self, recurring: dict, date: pd.Timestamp) -> bool:
        """Check if a recurring expense is due on this date."""
        try:
            next_date = pd.Timestamp(recurring.get("next_expected_date"))
            freq = recurring.get("frequency_days", 30)

            days_diff = (date - next_date).days

            # Check if date falls on the recurring pattern
            if days_diff >= 0 and days_diff % freq < 3:  # 3-day window
                return True

            return False
        except (ValueError, TypeError):
            return False


def forecast_cashflow(
    transactions: list[dict],
    current_balance: float,
    recurring_expenses: Optional[list[dict]] = None,
    days_ahead: int = 30,
) -> dict:
    """
    Convenience function to forecast cashflow.

    Args:
        transactions: List of transaction dicts with date, amount
        current_balance: Current account balance
        recurring_expenses: Optional detected recurring expenses
        days_ahead: Number of days to forecast

    Returns:
        Dict with training info and predictions
    """
    forecaster = CashflowForecaster()
    training_result = forecaster.train(transactions, recurring_expenses)
    predictions = forecaster.predict(current_balance, days_ahead)

    return {
        "training": training_result,
        "predictions": predictions,
    }
