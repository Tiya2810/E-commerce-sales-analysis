"""Focused regression tests for data integrity and analytical outputs."""

import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

import pandas as pd

from analysis.business_insights import generate_insights
from analysis.customer_segmentation import add_customer_segments
from analysis.data_cleaning import build_database, clean_data, generate_raw_data
from config import PROJECT_ROOT


class AnalyticsPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = generate_raw_data(records=600, seed=17)
        cls.data = clean_data(cls.raw)

    def test_cleaning_reconciles_sales_and_removes_duplicate_rows(self) -> None:
        self.assertEqual(len(self.data), len(self.raw.drop_duplicates()))
        expected_sales = self.data["Quantity"] * self.data["Unit Price"] * (1 - self.data["Discount"])
        self.assertTrue(((self.data["Sales"] - expected_sales).abs() < .02).all())
        self.assertTrue(self.data["Order Date"].notna().all())

    def test_order_and_customer_attributes_are_consistent(self) -> None:
        order_columns = ["Order Date", "Order Status", "Shipping Mode", "Payment Mode"]
        customer_columns = ["Customer Name", "Gender", "Age", "Region", "State", "City"]
        self.assertTrue((self.data.groupby("Order ID")[order_columns].nunique() <= 1).all().all())
        self.assertTrue((self.data.groupby("Customer ID")[customer_columns].nunique() <= 1).all().all())

    def test_delivery_dates_match_transit_metrics(self) -> None:
        delivered = self.data.dropna(subset=["Delivery Date"])
        self.assertGreater(len(delivered), 0)
        self.assertTrue((delivered["Delivery Date"] >= delivered["Ship Date"]).all())
        transit_days = (delivered["Delivery Date"] - delivered["Ship Date"]).dt.days
        self.assertTrue((transit_days == delivered["Actual Delivery Days"].astype(int)).all())
        self.assertTrue((delivered["Is Late Delivery"] == (transit_days > delivered["Expected Delivery Days"])).all())

    def test_rfm_and_business_insights_are_populated(self) -> None:
        segmented, rfm = add_customer_segments(self.data)
        self.assertTrue(segmented["Customer Segment"].notna().all())
        self.assertGreaterEqual(rfm["Customer Segment"].nunique(), 1)
        self.assertGreaterEqual(len(generate_insights(segmented)), 5)
        self.assertIn("No rows", generate_insights(segmented.iloc[0:0])[0]["insight"])

    def test_every_named_sql_query_executes(self) -> None:
        sql_path = PROJECT_ROOT / "sql" / "analysis_queries.sql"
        queries = re.findall(r"-- query: ([a-z0-9_]+)\s+(.*?);", sql_path.read_text(encoding="utf-8"), re.S)
        self.assertEqual(len(queries), 18)
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "test.db"
            build_database(self.data, database)
            with closing(sqlite3.connect(database)) as connection:
                for name, query in queries:
                    with self.subTest(query=name):
                        result = pd.read_sql_query(query, connection)
                        self.assertIsNotNone(result)
                shipping = pd.read_sql_query(dict(queries)["shipping_performance"], connection)
                self.assertGreater(int(shipping["delivered_orders"].sum()), 0)
                objects = dict(connection.execute(
                    "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')"
                ).fetchall())
                self.assertEqual(objects.get("dim_customer"), "table")
                self.assertEqual(objects.get("dim_product"), "table")
                self.assertEqual(objects.get("dim_order"), "table")
                self.assertEqual(objects.get("fact_sales"), "table")
                self.assertEqual(objects.get("sales"), "view")
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                count = connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
            build_database(self.data, database)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0], count)


if __name__ == "__main__":
    unittest.main()
