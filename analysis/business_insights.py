"""Dataset-driven insight and recommendation generation."""

import pandas as pd


def generate_insights(data: pd.DataFrame) -> list[dict[str, str]]:
    if data.empty:
        return [{"insight": "No rows match the active filters.", "recommendation": "Broaden the filters to review business performance."}]
    category_sales = data.groupby("Category")["Sales"].sum()
    region_profit = data.groupby("Region")["Profit"].sum()
    month_sales = data.groupby("Month")["Sales"].sum()
    product_profit = data.groupby(["Product Name", "Product ID"])["Profit"].sum().sort_values()
    customer_sales = data.groupby(["Customer Name", "Customer ID"])["Sales"].sum().sort_values(ascending=False)
    discount_bins = pd.cut(data["Discount"], bins=[-0.001, .05, .10, .20, .80], labels=["0-5%", "5-10%", "10-20%", "20%+"])
    discount_profitability = data.assign(Discount_Band=discount_bins).groupby("Discount_Band", observed=True).agg(
        Profit=("Profit", "sum"), Revenue=("Sales", "sum"))
    discount_margin = (discount_profitability["Profit"] / discount_profitability["Revenue"].replace(0, pd.NA)).reindex(
        ["0-5%", "5-10%", "10-20%", "20%+"])
    peak_month = month_sales.idxmax()
    top_category = category_sales.idxmax()
    top_region = region_profit.idxmax()
    worst_product = product_profit.index[0]
    best_customer = customer_sales.index[0]
    high_discount_margin = discount_margin.get("20%+")
    low_discount_margin = discount_margin.get("0-5%")
    overall_margin = data["Profit"].sum() / data["Sales"].sum() if data["Sales"].sum() else 0
    discount_comparison = (
        f"high-discount band margin is {high_discount_margin:.1%} versus {low_discount_margin:.1%} for low discounts"
        if pd.notna(high_discount_margin) and pd.notna(low_discount_margin)
        else "there is not enough data in both low- and high-discount bands for a comparison"
    )
    return [
        {"insight": f"{top_category} leads filtered revenue with {category_sales.max():,.0f} ({category_sales.max() / category_sales.sum():.1%} of sales).",
         "recommendation": "Protect availability of leading products while testing adjacent-category bundles to diversify revenue."},
        {"insight": f"{top_region} contributes the highest filtered profit at {region_profit.max():,.0f}.",
         "recommendation": "Review the region's product mix and fulfillment practices for approaches that can be replicated elsewhere."},
        {"insight": f"{worst_product[0]} ({worst_product[1]}) is the lowest-profit product at {product_profit.iloc[0]:,.0f}.",
         "recommendation": "Review its landed cost, discounting, and return rate before repricing or reducing promotion."},
        {"insight": f"{peak_month} is the strongest filtered month with revenue of {month_sales.max():,.0f}.",
         "recommendation": "Align inventory, staffing, and campaign timing to demand peaks and validate that the pattern repeats year over year."},
        {"insight": f"Weighted profit margin is {overall_margin:.1%} across filtered lines; {discount_comparison}.",
         "recommendation": "Use margin guardrails and evaluate discount performance on incremental profit, not order volume alone."},
        {"insight": f"{best_customer[0]} ({best_customer[1]}) is the highest-revenue customer at {customer_sales.iloc[0]:,.0f}.",
         "recommendation": "Use service recovery and relevant loyalty offers to retain top-value customers without blanket discounting."},
    ]
