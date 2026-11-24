"""Run data, database-query, and analysis smoke checks."""

import re
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from analysis.data_cleaning import build_database, clean_data, generate_raw_data
from analysis.eda import create_eda_charts
from analysis.customer_segmentation import add_customer_segments
from analysis.business_insights import generate_insights
from config import CLEAN_DATA_PATH, DATABASE_PATH, PROJECT_ROOT


def main() -> None:
    if not CLEAN_DATA_PATH.exists():
        raw = generate_raw_data()
        clean = clean_data(raw)
        clean.to_csv(CLEAN_DATA_PATH, index=False)
        build_database(clean)
    data = pd.read_csv(CLEAN_DATA_PATH, parse_dates=["Order Date", "Ship Date", "Delivery Date"])
    assert len(data) >= 5000, f"Expected >=5,000 cleaned rows; got {len(data)}"
    assert data["Order Date"].notna().all()
    assert (data["Sales"] >= 0).all()
    assert (data["Profit"] < 0).any(), "Synthetic dataset should contain negative-profit order lines"
    order_columns = ["Order Date", "Order Status", "Shipping Mode", "Payment Mode"]
    customer_columns = ["Customer Name", "Gender", "Age", "Region", "State", "City"]
    assert (data.groupby("Order ID")[order_columns].nunique() <= 1).all().all(), "Order attributes are inconsistent"
    assert (data.groupby("Customer ID")[customer_columns].nunique() <= 1).all().all(), "Customer attributes are inconsistent"
    delivered = data.dropna(subset=["Delivery Date"])
    transit_days = (delivered["Delivery Date"] - delivered["Ship Date"]).dt.days
    assert (transit_days == delivered["Actual Delivery Days"].astype(int)).all(), "Delivery transit time reconciliation failed"
    assert (delivered["Is Late Delivery"] == (transit_days > delivered["Expected Delivery Days"])).all(), "Late delivery flag reconciliation failed"
    expected_sales = data["Quantity"] * data["Unit Price"] * (1 - data["Discount"])
    assert ((data["Sales"] - expected_sales).abs() < .02).all(), "Sales reconciliation failed"
    expected_margin = data["Profit"] / data["Sales"].replace(0, pd.NA)
    assert (data["Profit Margin"] - expected_margin).abs().fillna(0).lt(.0001).all(), "Profit margin reconciliation failed"
    segmented, rfm = add_customer_segments(data)
    assert segmented["Customer Segment"].notna().all() and not rfm.empty
    assert len(generate_insights(segmented)) >= 5

    sql = (PROJECT_ROOT / "sql" / "analysis_queries.sql").read_text(encoding="utf-8")
    queries = re.findall(r"-- query: ([a-z0-9_]+)\s+(.*?);", sql, re.S)
    assert len(queries) == 18, f"Expected 18 named SQL queries; found {len(queries)}"
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        objects = dict(connection.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')"
        ).fetchall())
        assert objects.get("dim_customer") == "table"
        assert objects.get("dim_product") == "table"
        assert objects.get("dim_order") == "table"
        assert objects.get("fact_sales") == "table"
        assert objects.get("sales") == "view"
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()
        for name, query in queries:
            result = pd.read_sql_query(query, connection)
            if name == "loss_making_products":
                assert not result.empty, "Expected at least one loss-making product in generated data"
            if name == "shipping_performance":
                assert result["delivered_orders"].sum() > 0, "Expected delivered orders for shipping analysis"
            print(f"PASS SQL {name}")
    charts = create_eda_charts(data)
    assert len(charts) >= 8 and all(Path(path).exists() for path in charts)
    print(f"PASS data pipeline: {len(data):,} rows, {data['Order ID'].nunique():,} orders, {data['Customer ID'].nunique():,} customers")
    print(f"PASS RFM segmentation: {len(rfm):,} customers across {rfm['Customer Segment'].nunique()} segments")
    print(f"PASS EDA charts: {len(charts)}")


if __name__ == "__main__":
    main()
