PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS sales;
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_order;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;

CREATE TABLE dim_customer (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    age INTEGER NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE dim_product (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL
);

CREATE TABLE dim_order (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES dim_customer(customer_id),
    order_date TEXT NOT NULL,
    payment_mode TEXT NOT NULL,
    shipping_mode TEXT NOT NULL,
    order_status TEXT NOT NULL,
    ship_date TEXT,
    delivery_date TEXT,
    expected_delivery_days INTEGER NOT NULL CHECK (expected_delivery_days >= 0),
    actual_delivery_days INTEGER CHECK (actual_delivery_days IS NULL OR actual_delivery_days >= 0),
    is_late_delivery INTEGER NOT NULL CHECK (is_late_delivery IN (0, 1)),
    order_month INTEGER NOT NULL,
    month TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_of_week TEXT NOT NULL
);

CREATE TABLE fact_sales (
    sales_line_id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES dim_order(order_id),
    product_id TEXT NOT NULL REFERENCES dim_product(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    discount REAL NOT NULL CHECK (discount >= 0 AND discount <= 0.8),
    sales REAL NOT NULL CHECK (sales >= 0),
    profit REAL NOT NULL,
    profit_margin REAL NOT NULL,
    is_sales_outlier INTEGER NOT NULL
);

CREATE INDEX idx_dim_order_date ON dim_order(order_date);
CREATE INDEX idx_dim_order_customer ON dim_order(customer_id);
CREATE INDEX idx_dim_customer_region ON dim_customer(region);
CREATE INDEX idx_fact_sales_order ON fact_sales(order_id);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_id);

CREATE VIEW sales AS
SELECT
    o.order_id AS "Order ID",
    o.order_date AS "Order Date",
    c.customer_id AS "Customer ID",
    c.customer_name AS "Customer Name",
    c.gender AS "Gender",
    c.age AS "Age",
    p.product_id AS "Product ID",
    p.product_name AS "Product Name",
    p.category AS "Category",
    p.sub_category AS "Sub-Category",
    f.quantity AS "Quantity",
    f.unit_price AS "Unit Price",
    f.discount AS "Discount",
    f.sales AS "Sales",
    f.profit AS "Profit",
    o.payment_mode AS "Payment Mode",
    c.city AS "City",
    c.state AS "State",
    c.region AS "Region",
    o.shipping_mode AS "Shipping Mode",
    o.order_status AS "Order Status",
    o.ship_date AS "Ship Date",
    o.delivery_date AS "Delivery Date",
    o.expected_delivery_days AS "Expected Delivery Days",
    o.actual_delivery_days AS "Actual Delivery Days",
    o.is_late_delivery AS "Is Late Delivery",
    f.profit_margin AS "Profit Margin",
    o.order_month AS "Order Month",
    o.month AS "Month",
    o.year AS "Year",
    o.quarter AS "Quarter",
    o.day AS "Day",
    o.day_of_week AS "Day Of Week",
    f.is_sales_outlier AS "Is Sales Outlier"
FROM fact_sales f
JOIN dim_order o ON o.order_id = f.order_id
JOIN dim_customer c ON c.customer_id = o.customer_id
JOIN dim_product p ON p.product_id = f.product_id;
