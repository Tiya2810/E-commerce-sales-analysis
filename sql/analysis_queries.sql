-- SQLite analytical query library. Run each query independently.

-- query: total_revenue
SELECT ROUND(SUM(Sales), 2) AS total_revenue FROM sales;

-- query: total_profit
SELECT ROUND(SUM(Profit), 2) AS total_profit FROM sales;

-- query: total_orders
SELECT COUNT(DISTINCT "Order ID") AS total_orders FROM sales;

-- query: total_customers
SELECT COUNT(DISTINCT "Customer ID") AS total_customers FROM sales;

-- query: average_order_value
SELECT ROUND(SUM(Sales) / NULLIF(COUNT(DISTINCT "Order ID"), 0), 2) AS average_order_value FROM sales;

-- query: top_10_best_selling_products
SELECT "Product ID", "Product Name", SUM(Quantity) AS units_sold, ROUND(SUM(Sales), 2) AS revenue
FROM sales GROUP BY "Product ID", "Product Name" ORDER BY units_sold DESC, revenue DESC LIMIT 10;

-- query: top_10_most_profitable_products
SELECT "Product ID", "Product Name", ROUND(SUM(Profit), 2) AS profit
FROM sales GROUP BY "Product ID", "Product Name" ORDER BY profit DESC LIMIT 10;

-- query: category_sales_profit
SELECT Category, ROUND(SUM(Sales), 2) AS revenue, ROUND(SUM(Profit), 2) AS profit,
       ROUND(SUM(Profit) / NULLIF(SUM(Sales), 0), 4) AS profit_margin
FROM sales GROUP BY Category ORDER BY revenue DESC;

-- query: monthly_revenue
SELECT strftime('%Y-%m', "Order Date") AS month, ROUND(SUM(Sales), 2) AS revenue
FROM sales GROUP BY month ORDER BY month;

-- query: year_over_year_growth
WITH yearly AS (
    SELECT Year, SUM(Sales) AS revenue FROM sales GROUP BY Year
), growth AS (
    SELECT Year, revenue, LAG(revenue) OVER (ORDER BY Year) AS prior_year_revenue FROM yearly
)
SELECT Year, ROUND(revenue, 2) AS revenue, ROUND(prior_year_revenue, 2) AS prior_year_revenue,
       ROUND((revenue - prior_year_revenue) / NULLIF(prior_year_revenue, 0) * 100, 2) AS growth_pct
FROM growth ORDER BY Year;

-- query: region_performance
SELECT Region, ROUND(SUM(Sales), 2) AS revenue, ROUND(SUM(Profit), 2) AS profit,
       COUNT(DISTINCT "Order ID") AS orders
FROM sales GROUP BY Region ORDER BY revenue DESC;

-- query: customer_purchase_frequency
SELECT "Customer ID", "Customer Name", COUNT(DISTINCT "Order ID") AS order_count,
       ROUND(SUM(Sales), 2) AS customer_revenue
FROM sales GROUP BY "Customer ID", "Customer Name" ORDER BY order_count DESC, customer_revenue DESC;

-- query: repeat_customer_analysis
WITH customer_orders AS (
    SELECT "Customer ID", COUNT(DISTINCT "Order ID") AS order_count FROM sales GROUP BY "Customer ID"
)
SELECT CASE WHEN order_count > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type,
       COUNT(*) AS customers, SUM(order_count) AS orders
FROM customer_orders GROUP BY customer_type;

-- query: payment_mode_analysis
SELECT "Payment Mode", COUNT(DISTINCT "Order ID") AS orders, ROUND(SUM(Sales), 2) AS revenue,
       ROUND(SUM(Profit), 2) AS profit
FROM sales GROUP BY "Payment Mode" ORDER BY revenue DESC;

-- query: discount_profitability
SELECT CASE WHEN Discount = 0 THEN '0%' WHEN Discount <= .05 THEN '1-5%'
            WHEN Discount <= .10 THEN '6-10%' WHEN Discount <= .20 THEN '11-20%' ELSE 'Over 20%' END AS discount_band,
       COUNT(*) AS order_lines, ROUND(AVG(Profit), 2) AS average_profit,
       ROUND(SUM(Profit) / NULLIF(SUM(Sales), 0), 4) AS profit_margin
FROM sales GROUP BY discount_band ORDER BY MIN(Discount);

-- query: loss_making_products
SELECT "Product ID", "Product Name", ROUND(SUM(Sales), 2) AS revenue, ROUND(SUM(Profit), 2) AS profit
FROM sales GROUP BY "Product ID", "Product Name" HAVING SUM(Profit) < 0 ORDER BY profit;

-- query: high_value_customers
SELECT "Customer ID", "Customer Name", ROUND(SUM(Sales), 2) AS lifetime_revenue,
       COUNT(DISTINCT "Order ID") AS orders
FROM sales GROUP BY "Customer ID", "Customer Name" ORDER BY lifetime_revenue DESC LIMIT 20;

-- query: shipping_performance
WITH order_summary AS (
    SELECT "Order ID", "Shipping Mode", MAX("Delivery Date") AS "Delivery Date",
           MAX("Actual Delivery Days") AS "Actual Delivery Days",
           MAX("Is Late Delivery") AS "Is Late Delivery", SUM(Sales) AS revenue
    FROM sales GROUP BY "Order ID", "Shipping Mode"
)
SELECT "Shipping Mode", COUNT(*) AS orders,
       SUM(CASE WHEN "Delivery Date" IS NOT NULL THEN 1 ELSE 0 END) AS delivered_orders,
       ROUND(AVG("Actual Delivery Days"), 2) AS average_transit_days,
       ROUND(100.0 * AVG(CASE WHEN "Delivery Date" IS NOT NULL THEN 1.0 - "Is Late Delivery" END), 2) AS on_time_delivery_pct,
       ROUND(SUM(revenue), 2) AS revenue
FROM order_summary GROUP BY "Shipping Mode" ORDER BY delivered_orders DESC;
