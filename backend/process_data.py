#!/usr/bin/env python
"""
process_data.py – generate a static JSON payload for the churn dashboard.

It:
1. Loads WA_Fn-UseC_-Telco-Customer-Churn.csv (project‑root folder).
2. Cleans the data.
3. Computes KPIs, chart‑ready aggregations and a 100‑row preview.
4. Writes everything to ../frontend/data.json.
"""

import json
import os

import pandas as pd


def load_dataset() -> pd.DataFrame:
    """Read the CSV that lives next to the two top‑level folders."""
    csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "WA_Fn-UseC_-Telco-Customer-Churn.csv")
    )
    df = pd.read_csv(csv_path)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace, fix dtypes and map categorical values."""
    # Strip whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda s: s.str.strip())

    # TotalCharges → numeric, drop rows where conversion failed
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).reset_index(drop=True)

    # Map churn to binary
    df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

    # Map SeniorCitizen from 0/1 to Yes/No (as asked)
    df["SeniorCitizen"] = df["SeniorCitizen"].map({1: "Yes", 0: "No"})

    return df


def kpis(df: pd.DataFrame) -> dict:
    total_customers = len(df)
    churn_rate_pct = round(df["Churn"].mean() * 100, 2)
    total_monthly_revenue = round(df["MonthlyCharges"].sum(), 2)
    revenue_at_risk = round(df.loc[df["Churn"] == 1, "MonthlyCharges"].sum(), 2)
    avg_monthly_charge = round(df["MonthlyCharges"].mean(), 2)
    avg_tenure = round(df["tenure"].mean(), 2)

    return {
        "total_customers": total_customers,
        "churn_rate_pct": churn_rate_pct,
        "total_monthly_revenue": total_monthly_revenue,
        "revenue_at_risk": revenue_at_risk,
        "avg_monthly_charge": avg_monthly_charge,
        "avg_tenure": avg_tenure,
    }


def churn_distribution(df: pd.DataFrame) -> dict:
    counts = df["Churn"].value_counts().sort_index()
    labels = ["No", "Yes"]
    values = [int(counts.get(0, 0)), int(counts.get(1, 0))]
    return {"labels": labels, "values": values}


def churn_by_category(df: pd.DataFrame, column: str) -> dict:
    grp = df.groupby(column)["Churn"].mean().reset_index()
    grp["churn_pct"] = (grp["Churn"] * 100).round(2)
    return {"labels": grp[column].tolist(), "values": grp["churn_pct"].tolist()}


def churn_by_tenure_group(df: pd.DataFrame) -> dict:
    bins = [0, 12, 24, 48, 72]
    labels = ["0‑12", "13‑24", "25‑48", "49‑72"]
    df["tenure_group"] = pd.cut(df["tenure"], bins=bins, labels=labels, right=True, include_lowest=True)
    grp = df.groupby("tenure_group")["Churn"].mean().reset_index()
    grp["churn_pct"] = (grp["Churn"] * 100).round(2)
    return {"labels": grp["tenure_group"].astype(str).tolist(), "values": grp["churn_pct"].tolist()}


def preview_customers(df: pd.DataFrame, n: int = 100) -> list:
    preview_df = df.head(n).copy()
    return preview_df.to_dict(orient="records")


def main() -> None:
    df = load_dataset()
    df = clean_data(df)

    payload = {
        "kpis": kpis(df),
        "charts": {
            "churn_distribution": churn_distribution(df),
            "churn_by_contract": churn_by_category(df, "Contract"),
            "churn_by_internet": churn_by_category(df, "InternetService"),
            "churn_by_payment": churn_by_category(df, "PaymentMethod"),
            "churn_by_tenure": churn_by_tenure_group(df),
        },
        "customers": preview_customers(df, 100),
    }

    out_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "frontend", "data.json")
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Data written to {out_path}")


if __name__ == "__main__":
    main()
