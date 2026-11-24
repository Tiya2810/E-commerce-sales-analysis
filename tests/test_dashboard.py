"""Streamlit AppTest smoke tests for navigation and shared filters."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DashboardSmokeTests(unittest.TestCase):
    def test_all_dashboard_pages_render(self) -> None:
        page_paths = [PROJECT_ROOT / "app.py", *sorted((PROJECT_ROOT / "pages").glob("*.py"))]
        for path in page_paths:
            with self.subTest(page=path.name):
                app = AppTest.from_file(str(path), default_timeout=60).run()
                self.assertFalse(app.exception, f"{path.name}: {app.exception}")

    def test_shared_filters_period_comparison_and_reset(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=60).run()
        app.date_input(key="filter_dates").set_value(("2024-01-01", "2024-12-31"))
        app.multiselect(key="filter_status").set_value(["Delivered"])
        app.multiselect(key="filter_category").set_value(["Electronics"])
        app.run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(any("vs prior period" in str(metric.delta) for metric in app.metric))

        app.button[0].click().run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.multiselect(key="filter_status").value, [])
        self.assertEqual(app.multiselect(key="filter_category").value, [])

    def test_shipping_page_handles_no_deliveries_in_filter(self) -> None:
        page = PROJECT_ROOT / "pages" / "7_Shipping_Fulfillment.py"
        app = AppTest.from_file(str(page), default_timeout=60).run()
        app.multiselect(key="filter_status").set_value(["Cancelled"]).run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(any("No delivered orders" in item.value for item in app.info))


if __name__ == "__main__":
    unittest.main()
