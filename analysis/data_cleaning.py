"""Synthetic data generation, cleaning, and SQLite loading."""

import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd

from config import CLEAN_DATA_PATH, DATABASE_PATH, RANDOM_SEED, RAW_DATA_PATH

CATEGORIES = {
    "Electronics": ["Audio", "Computing", "Accessories", "Cameras"],
    "Home & Kitchen": ["Kitchen", "Furniture", "Decor", "Appliances"],
    "Fashion": ["Clothing", "Footwear", "Bags", "Accessories"],
    "Beauty": ["Skincare", "Haircare", "Makeup", "Fragrance"],
    "Sports": ["Fitness", "Outdoor", "Team Sports", "Cycling"],
}
PRODUCTS = {
    "Electronics": ["Wireless Headphones", "Smart Speaker", "Laptop Stand", "4K Monitor", "Mirrorless Camera", "USB-C Hub", "Mechanical Keyboard", "Portable SSD", "Fitness Earbuds", "Webcam Pro"],
    "Home & Kitchen": ["Espresso Maker", "Air Fryer", "Ceramic Dinner Set", "Linen Duvet", "Floor Lamp", "Storage Organizer", "Chef Knife Set", "Robot Vacuum", "Throw Blanket", "Water Filter"],
    "Fashion": ["Classic Denim Jacket", "Running Sneakers", "Leather Crossbody", "Cotton Hoodie", "Everyday Backpack", "Wool Scarf", "Canvas Tote", "Trail Boots", "Linen Shirt", "Travel Wallet"],
    "Beauty": ["Vitamin C Serum", "Hydrating Cleanser", "Hair Repair Mask", "Matte Lip Color", "Botanical Shampoo", "Daily Sunscreen", "Eau de Parfum", "Retinol Night Cream", "Curl Defining Gel", "Makeup Brush Set"],
    "Sports": ["Yoga Mat Pro", "Adjustable Dumbbells", "Insulated Bottle", "Trail Running Pack", "Resistance Bands", "Cycling Helmet", "Foam Roller", "Camping Lantern", "Tennis Racket", "Hiking Poles"],
}
STATES = {
    "West": {"California": ["Los Angeles", "San Diego", "San Francisco"], "Washington": ["Seattle", "Spokane"], "Oregon": ["Portland", "Eugene"], "Arizona": ["Phoenix", "Tucson"]},
    "South": {"Texas": ["Houston", "Austin", "Dallas"], "Florida": ["Miami", "Orlando", "Tampa"], "Georgia": ["Atlanta", "Savannah"], "North Carolina": ["Charlotte", "Raleigh"]},
    "Midwest": {"Illinois": ["Chicago", "Springfield"], "Ohio": ["Columbus", "Cleveland"], "Michigan": ["Detroit", "Grand Rapids"], "Minnesota": ["Minneapolis", "St. Paul"]},
    "Northeast": {"New York": ["New York", "Buffalo"], "Massachusetts": ["Boston", "Worcester"], "Pennsylvania": ["Philadelphia", "Pittsburgh"], "New Jersey": ["Newark", "Jersey City"]},
}


def generate_raw_data(records: int = 6000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Create reproducible order-line data with realistic variation and known imperfections."""
    rng = np.random.default_rng(seed)
    customer_count = 1050
    customers = pd.DataFrame({
        "Customer ID": [f"C{n:05d}" for n in range(1, customer_count + 1)],
        "Customer Name": [f"{first} {last}" for first, last in zip(
            rng.choice(["Alex", "Jordan", "Taylor", "Morgan", "Riley", "Casey", "Avery", "Jamie", "Cameron", "Drew"], customer_count),
            rng.choice(["Chen", "Patel", "Garcia", "Johnson", "Kim", "Singh", "Brown", "Nguyen", "Davis", "Wilson"], customer_count))],
        "Gender": rng.choice(["Female", "Male", "Non-binary"], customer_count, p=[0.49, 0.47, 0.04]),
        "Age": rng.integers(18, 71, customer_count),
    })
    customer_locations = []
    for _ in range(customer_count):
        region = rng.choice(list(STATES))
        state = rng.choice(list(STATES[region]))
        customer_locations.append((region, state, rng.choice(STATES[region][state])))
    customers[["Region", "State", "City"]] = pd.DataFrame(customer_locations, index=customers.index)

    order_ids = rng.integers(10000, 10000 + max(4500, int(records * .72)), records)
    unique_order_ids = np.unique(order_ids)
    order_dates = pd.to_datetime(rng.choice(pd.date_range("2022-01-01", "2025-12-31", freq="D"), len(unique_order_ids)))
    order_date_map = dict(zip(unique_order_ids, order_dates))
    status_map = dict(zip(unique_order_ids, rng.choice(
        ["Delivered", "Shipped", "Processing", "Cancelled", "Returned"],
        len(unique_order_ids), p=[.78, .09, .06, .04, .03])))
    shipping_modes = ["Standard", "Express", "Same Day", "Economy"]
    shipping_mode_map = dict(zip(unique_order_ids, rng.choice(shipping_modes, len(unique_order_ids), p=[.52, .22, .10, .16])))
    payment_mode_map = dict(zip(unique_order_ids, rng.choice(
        ["Credit Card", "Debit Card", "Digital Wallet", "Cash on Delivery", "Bank Transfer"],
        len(unique_order_ids), p=[.34, .24, .24, .12, .06])))
    expected_days_by_mode = {"Standard": 5, "Express": 2, "Same Day": 1, "Economy": 8}
    delivery_details = {}
    for order_id in unique_order_ids:
        status = status_map[order_id]
        mode = shipping_mode_map[order_id]
        expected_days = expected_days_by_mode[mode]
        shipped = status in ("Delivered", "Shipped", "Returned")
        delivered = status in ("Delivered", "Returned")
        ship_date = pd.Timestamp(order_date_map[order_id]) + pd.Timedelta(days=1) if shipped else None
        actual_days = None
        delivery_date = None
        if delivered:
            delayed = rng.random() < .18
            actual_days = expected_days + int(rng.integers(1, 4)) if delayed else max(1, expected_days - int(rng.integers(0, 3)))
            delivery_date = ship_date + pd.Timedelta(days=actual_days)
        delivery_details[order_id] = (
            ship_date, delivery_date, expected_days, actual_days,
            bool(actual_days is not None and actual_days > expected_days),
        )
    customer_by_order = dict(zip(unique_order_ids, rng.integers(0, customer_count, len(unique_order_ids))))
    customer_idx = np.array([customer_by_order[order_id] for order_id in order_ids])
    seasonal_weights = np.array([0.75, .78, .85, .9, .92, .95, .98, 1.0, 1.04, 1.12, 1.28, 1.48])
    rows = []
    category_names = list(CATEGORIES)
    for row_index in range(records):
        category = rng.choice(category_names, p=[.27, .23, .22, .14, .14])
        product = rng.choice(PRODUCTS[category])
        subcategory = rng.choice(CATEGORIES[category])
        product_id = f"P{category_names.index(category) + 1}{PRODUCTS[category].index(product) + 1:03d}"
        unit_price = round(float(np.clip(rng.lognormal(3.35, .78), 8, 900)), 2)
        date = pd.Timestamp(order_date_map[order_ids[row_index]])
        discount = float(rng.choice([0, .05, .10, .15, .20, .25, .30], p=[.19, .14, .22, .19, .15, .08, .03]))
        month_factor = seasonal_weights[date.month - 1]
        category_idx = category_names.index(category)
        customer = customers.iloc[customer_idx[row_index]]
        region, state, city = customer["Region"], customer["State"], customer["City"]
        status = status_map[order_ids[row_index]]
        shipping_mode = shipping_mode_map[order_ids[row_index]]
        ship_date, delivery_date, expected_days, actual_days, is_late = delivery_details[order_ids[row_index]]
        quantity = int(np.clip(rng.poisson(1.7 * month_factor) + 1, 1, 8))
        sales = round(quantity * unit_price * (1 - discount), 2)
        low_margin_product = product in ("Robot Vacuum", "Trail Running Pack")
        margin_base = .035 if low_margin_product else rng.uniform(.10, .36) + (0.025 if category_idx == 0 else 0)
        discount_sensitivity = .9 if low_margin_product else .72
        profit = round(sales * (margin_base - discount * discount_sensitivity + rng.normal(0, .035)), 2)
        rows.append({
            "Order ID": f"O{order_ids[row_index]}", "Order Date": date.strftime("%Y-%m-%d"),
            "Customer ID": customer["Customer ID"],
            "Customer Name": customer["Customer Name"],
            "Gender": customer["Gender"],
            "Age": int(customer["Age"]),
            "Product ID": product_id, "Product Name": product, "Category": category,
            "Sub-Category": subcategory, "Quantity": quantity, "Unit Price": unit_price,
            "Discount": discount, "Sales": sales, "Profit": profit,
            "Payment Mode": payment_mode_map[order_ids[row_index]],
            "City": city, "State": state, "Region": region,
            "Shipping Mode": shipping_mode,
            "Order Status": status,
            "Ship Date": ship_date.strftime("%Y-%m-%d") if ship_date is not None else None,
            "Delivery Date": delivery_date.strftime("%Y-%m-%d") if delivery_date is not None else None,
            "Expected Delivery Days": expected_days,
            "Actual Delivery Days": actual_days,
            "Is Late Delivery": is_late,
        })
    raw = pd.DataFrame(rows)
    # Introduce limited, recoverable quality issues so the cleaning pipeline is observable.
    raw.loc[rng.choice(raw.index, 12, replace=False), "Customer Name"] = np.nan
    credit_card_rows = raw.index[raw["Payment Mode"].eq("Credit Card")]
    raw.loc[rng.choice(credit_card_rows, min(8, len(credit_card_rows)), replace=False), "Payment Mode"] = "credit card "
    raw = pd.concat([raw, raw.iloc[[3, 17, 44]]], ignore_index=True)
    return raw


def clean_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize source data, reconcile derived measures, and add analysis features."""
    data = raw.copy()
    data = data.drop_duplicates().reset_index(drop=True)
    for column in ("Order Date", "Ship Date", "Delivery Date"):
        data[column] = pd.to_datetime(data[column], errors="coerce")
    data = data.dropna(subset=["Order Date", "Order ID", "Customer ID", "Product ID"])
    for column in ("Quantity", "Unit Price", "Discount", "Profit", "Age", "Expected Delivery Days", "Actual Delivery Days"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["Quantity"] = data["Quantity"].fillna(1).clip(lower=1).round().astype(int)
    data["Unit Price"] = data["Unit Price"].fillna(data["Unit Price"].median()).clip(lower=0)
    data["Discount"] = data["Discount"].fillna(0).clip(0, 0.8)
    data["Sales"] = (data["Quantity"] * data["Unit Price"] * (1 - data["Discount"])).round(2)
    data["Profit"] = data["Profit"].fillna(data["Sales"] * .12).round(2)
    data["Age"] = data["Age"].fillna(data["Age"].median()).clip(18, 100).round().astype(int)
    data["Customer Name"] = data["Customer Name"].astype("string")
    data["Customer Name"] = data.groupby("Customer ID")["Customer Name"].transform(lambda names: names.ffill().bfill())
    data["Expected Delivery Days"] = data["Expected Delivery Days"].fillna(0).clip(lower=0).astype(int)
    data["Actual Delivery Days"] = data["Actual Delivery Days"].clip(lower=0).astype("Int64")
    data["Is Late Delivery"] = data["Is Late Delivery"].fillna(False).astype(bool)
    for column in ("Customer Name", "Gender", "Product Name", "Category", "Sub-Category",
                   "Payment Mode", "City", "State", "Region", "Shipping Mode", "Order Status"):
        data[column] = data[column].fillna("Unknown").astype(str).str.strip()
    for column in ("Gender", "Category", "Sub-Category", "Payment Mode", "Region",
                   "Shipping Mode", "Order Status", "State", "City"):
        data[column] = data[column].str.replace(r"\s+", " ", regex=True).str.title()
    data["Profit Margin"] = np.divide(data["Profit"], data["Sales"], out=np.zeros(len(data)), where=data["Sales"].to_numpy() != 0).round(4)
    data["Order Month"] = data["Order Date"].dt.month
    data["Month"] = data["Order Date"].dt.to_period("M").astype(str)
    data["Year"] = data["Order Date"].dt.year
    data["Quarter"] = "Q" + data["Order Date"].dt.quarter.astype(str)
    data["Day"] = data["Order Date"].dt.day
    data["Day Of Week"] = data["Order Date"].dt.day_name()
    q1, q3 = data["Sales"].quantile([.25, .75])
    upper_bound = q3 + 1.5 * (q3 - q1)
    data["Is Sales Outlier"] = data["Sales"] > upper_bound
    return data.sort_values(["Order Date", "Order ID"]).reset_index(drop=True)


def build_database(data: pd.DataFrame, path: Path = DATABASE_PATH) -> None:
    """Load a relational star schema and expose a sales view for analytical SQL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="ecommerce-", suffix=".db", dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    schema_path = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    try:
        with closing(sqlite3.connect(temporary_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(schema_path.read_text(encoding="utf-8"))
            customers = data[["Customer ID", "Customer Name", "Gender", "Age", "City", "State", "Region"]].drop_duplicates("Customer ID")
            customers = customers.rename(columns={
                "Customer ID": "customer_id", "Customer Name": "customer_name",
                "Gender": "gender", "Age": "age", "City": "city", "State": "state", "Region": "region",
            })
            products = data[["Product ID", "Product Name", "Category", "Sub-Category"]].drop_duplicates("Product ID")
            products = products.rename(columns={
                "Product ID": "product_id", "Product Name": "product_name",
                "Category": "category", "Sub-Category": "sub_category",
            })
            order_columns = [
                "Order ID", "Customer ID", "Order Date", "Payment Mode", "Shipping Mode", "Order Status",
                "Ship Date", "Delivery Date", "Expected Delivery Days", "Actual Delivery Days",
                "Is Late Delivery", "Order Month", "Month", "Year", "Quarter", "Day", "Day Of Week",
            ]
            orders = data[order_columns].drop_duplicates("Order ID").rename(columns={
                "Order ID": "order_id", "Customer ID": "customer_id", "Order Date": "order_date",
                "Payment Mode": "payment_mode", "Shipping Mode": "shipping_mode", "Order Status": "order_status",
                "Ship Date": "ship_date", "Delivery Date": "delivery_date",
                "Expected Delivery Days": "expected_delivery_days", "Actual Delivery Days": "actual_delivery_days",
                "Is Late Delivery": "is_late_delivery", "Order Month": "order_month", "Month": "month",
                "Year": "year", "Quarter": "quarter", "Day": "day", "Day Of Week": "day_of_week",
            })
            for column in ("order_date", "ship_date", "delivery_date"):
                orders[column] = pd.to_datetime(orders[column], errors="coerce").dt.strftime("%Y-%m-%d")
            orders["is_late_delivery"] = orders["is_late_delivery"].astype(int)
            lines = data[["Order ID", "Product ID", "Quantity", "Unit Price", "Discount", "Sales", "Profit", "Profit Margin", "Is Sales Outlier"]].copy()
            lines.insert(0, "sales_line_id", np.arange(1, len(lines) + 1))
            lines = lines.rename(columns={
                "Order ID": "order_id", "Product ID": "product_id", "Quantity": "quantity",
                "Unit Price": "unit_price", "Discount": "discount", "Sales": "sales",
                "Profit": "profit", "Profit Margin": "profit_margin", "Is Sales Outlier": "is_sales_outlier",
            })
            lines["is_sales_outlier"] = lines["is_sales_outlier"].astype(int)
            customers.to_sql("dim_customer", connection, if_exists="append", index=False)
            products.to_sql("dim_product", connection, if_exists="append", index=False)
            orders.to_sql("dim_order", connection, if_exists="append", index=False)
            lines.to_sql("fact_sales", connection, if_exists="append", index=False)
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise sqlite3.IntegrityError(f"Foreign key violations found: {violations[:5]}")
            connection.commit()
        temporary_path.replace(path)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise


def run_pipeline() -> pd.DataFrame:
    """Generate source data, clean it, and save both CSV and SQLite outputs."""
    raw = generate_raw_data()
    raw.to_csv(RAW_DATA_PATH, index=False)
    clean = clean_data(raw)
    clean.to_csv(CLEAN_DATA_PATH, index=False)
    build_database(clean)
    print(f"Generated {len(raw):,} raw rows; retained {len(clean):,} clean rows.")
    print(f"Database: {DATABASE_PATH}")
    return clean


if __name__ == "__main__":
    run_pipeline()
