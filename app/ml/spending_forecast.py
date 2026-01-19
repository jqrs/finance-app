"""
Spending Forecaster

Predicts future spending by category using:
- Exponential Smoothing for categories with 12+ months of data
- Ridge Regression with seasonal features for less data
- Simple average for minimal data
"""

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


class SpendingForecaster:
    """Predict future spending by category."""

    def __init__(self):
        self.models = {}  # category_id -> model info
        self.is_trained = False

    def train(self, transactions: list[dict]) -> dict:
        """
        Train models on historical transaction data.

        Args:
            transactions: List of dicts with date, amount, category_id

        Returns:
            Training summary with categories trained
        """
        if not transactions:
            return {"trained": 0, "categories": []}

        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"])
        df["year_month"] = df["date"].dt.to_period("M")

        # Only consider expenses (negative amounts)
        df = df[df["amount"] < 0].copy()
        df["amount"] = df["amount"].abs()

        # Aggregate by category and month
        monthly = (
            df.groupby(["category_id", "year_month"])
            .agg({"amount": "sum", "date": "count"})
            .reset_index()
        )
        monthly.columns = ["category_id", "year_month", "total_amount", "txn_count"]

        trained_categories = []

        for category_id in monthly["category_id"].unique():
            if pd.isna(category_id):
                continue

            cat_data = monthly[monthly["category_id"] == category_id].copy()
            cat_data = cat_data.sort_values("year_month")

            self._train_category(int(category_id), cat_data)
            trained_categories.append(int(category_id))

        self.is_trained = True

        return {
            "trained": len(trained_categories),
            "categories": trained_categories,
        }

    def _train_category(self, category_id: int, data: pd.DataFrame):
        """Train model for a single category."""
        if len(data) < 2:
            # Not enough data - use simple average
            self.models[category_id] = {
                "type": "average",
                "value": float(data["total_amount"].mean()),
                "std": float(data["total_amount"].std()) if len(data) > 1 else 0,
            }
            return

        # Add time features
        data = data.copy()
        data["month"] = data["year_month"].dt.month
        data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12)
        data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12)

        if len(data) >= 12:
            # Try exponential smoothing approach via rolling stats
            # Use Ridge with lag features for simplicity
            data["lag_1"] = data["total_amount"].shift(1)
            data["lag_2"] = data["total_amount"].shift(2)
            data["rolling_mean_3"] = data["total_amount"].rolling(3, min_periods=1).mean()
            data = data.dropna()

            if len(data) >= 6:
                X = data[["month_sin", "month_cos", "lag_1", "rolling_mean_3"]].values
                y = data["total_amount"].values

                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)

                model = Ridge(alpha=1.0)
                model.fit(X_scaled, y)

                self.models[category_id] = {
                    "type": "ridge_seasonal",
                    "model": model,
                    "scaler": scaler,
                    "last_values": list(data["total_amount"].tail(3).values),
                    "std": float(np.std(y)),
                }
                return

        # Fall back to simpler Ridge with just seasonal features
        X = data[["month_sin", "month_cos"]].values
        y = data["total_amount"].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = Ridge(alpha=1.0)
        model.fit(X_scaled, y)

        self.models[category_id] = {
            "type": "ridge_simple",
            "model": model,
            "scaler": scaler,
            "std": float(np.std(y)),
            "mean": float(np.mean(y)),
        }

    def predict(self, category_id: int, months_ahead: int = 3) -> list[dict]:
        """
        Predict spending for next N months.

        Args:
            category_id: Category to predict
            months_ahead: Number of months to forecast

        Returns:
            List of predictions with confidence intervals
        """
        if category_id not in self.models:
            return []

        model_info = self.models[category_id]
        predictions = []
        today = pd.Timestamp.today()

        for i in range(1, months_ahead + 1):
            future_date = today + pd.DateOffset(months=i)
            month = future_date.month

            if model_info["type"] == "average":
                pred = model_info["value"]
                std = model_info["std"] if model_info["std"] > 0 else pred * 0.2

            elif model_info["type"] == "ridge_seasonal":
                month_sin = np.sin(2 * np.pi * month / 12)
                month_cos = np.cos(2 * np.pi * month / 12)

                # Use last known values for lag features
                last_vals = model_info["last_values"]
                lag_1 = last_vals[-1] if last_vals else model_info.get("mean", 0)
                rolling_mean = np.mean(last_vals) if last_vals else lag_1

                X = np.array([[month_sin, month_cos, lag_1, rolling_mean]])
                X_scaled = model_info["scaler"].transform(X)
                pred = float(model_info["model"].predict(X_scaled)[0])
                std = model_info["std"]

            else:  # ridge_simple
                month_sin = np.sin(2 * np.pi * month / 12)
                month_cos = np.cos(2 * np.pi * month / 12)

                X = np.array([[month_sin, month_cos]])
                X_scaled = model_info["scaler"].transform(X)
                pred = float(model_info["model"].predict(X_scaled)[0])
                std = model_info["std"]

            # Ensure non-negative predictions
            pred = max(0, pred)
            lower = max(0, pred - 1.96 * std)
            upper = pred + 1.96 * std

            predictions.append({
                "month": future_date.strftime("%Y-%m"),
                "predicted_amount": round(pred, 2),
                "lower_bound": round(lower, 2),
                "upper_bound": round(upper, 2),
            })

        return predictions

    def predict_all(self, months_ahead: int = 3) -> dict[int, list[dict]]:
        """Predict spending for all trained categories."""
        results = {}
        for category_id in self.models:
            results[category_id] = self.predict(category_id, months_ahead)
        return results


def forecast_spending(
    transactions: list[dict],
    category_id: Optional[int] = None,
    months_ahead: int = 3,
) -> dict:
    """
    Convenience function to forecast spending.

    Args:
        transactions: List of transaction dicts with date, amount, category_id
        category_id: Specific category to forecast, or None for all
        months_ahead: Number of months to forecast

    Returns:
        Dict with predictions by category
    """
    forecaster = SpendingForecaster()
    training_result = forecaster.train(transactions)

    if category_id is not None:
        predictions = {category_id: forecaster.predict(category_id, months_ahead)}
    else:
        predictions = forecaster.predict_all(months_ahead)

    return {
        "training": training_result,
        "predictions": predictions,
    }
