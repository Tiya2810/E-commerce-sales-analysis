"""Reproducible EDA chart generation."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from analysis.customer_segmentation import add_customer_segments
from config import CHARTS_DIR, CLEAN_DATA_PATH

sns.set_theme(style="whitegrid", palette="deep")


def create_eda_charts(data: pd.DataFrame) -> list[str]:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    charts = [
        ("sales_distribution.png", lambda ax: sns.histplot(data=data, x="Sales", bins=40, ax=ax), "Sales distribution"),
        ("profit_distribution.png", lambda ax: sns.histplot(data=data, x="Profit", bins=40, ax=ax), "Profit distribution"),
        ("category_sales.png", lambda ax: sns.barplot(data=data.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False), x="Sales", y="Category", ax=ax), "Revenue by category"),
        ("subcategory_sales.png", lambda ax: sns.barplot(data=data.groupby("Sub-Category", as_index=False)["Sales"].sum().nlargest(15, "Sales"), x="Sales", y="Sub-Category", ax=ax), "Top sub-categories by revenue"),
        ("regional_sales.png", lambda ax: sns.barplot(data=data.groupby("Region", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False), x="Sales", y="Region", ax=ax), "Revenue by region"),
        ("customer_gender.png", lambda ax: sns.barplot(data=data.groupby("Gender", as_index=False)["Customer ID"].nunique().sort_values("Customer ID", ascending=False), x="Customer ID", y="Gender", ax=ax), "Customers by gender"),
        ("discount_vs_profit.png", lambda ax: sns.scatterplot(data=data.sample(min(2500, len(data)), random_state=42), x="Discount", y="Profit Margin", hue="Category", alpha=.55, ax=ax), "Discount and profit margin"),
        ("correlation_heatmap.png", lambda ax: sns.heatmap(data[["Quantity", "Unit Price", "Discount", "Sales", "Profit", "Profit Margin", "Age"]].corr(), annot=True, cmap="Blues", fmt=".2f", ax=ax), "Numeric feature correlation"),
    ]
    for filename, draw, title in charts:
        fig, ax = plt.subplots(figsize=(10, 5))
        draw(ax)
        ax.set_title(title, fontsize=14, weight="bold")
        fig.tight_layout()
        destination = CHARTS_DIR / filename
        fig.savefig(destination, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(destination))
    monthly = data.groupby("Month", as_index=False)["Sales"].sum()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=monthly, x="Month", y="Sales", marker="o", ax=ax)
    ax.set_title("Monthly revenue trend", fontsize=14, weight="bold")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout()
    destination = CHARTS_DIR / "monthly_revenue.png"
    fig.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(destination))

    yearly = data.groupby("Year", as_index=False).agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"))
    fig, ax = plt.subplots(figsize=(10, 5))
    yearly.set_index("Year")[["Revenue", "Profit"]].plot(kind="bar", ax=ax, color=["#3678B7", "#35A7A0"])
    ax.set_title("Yearly revenue and profit", fontsize=14, weight="bold")
    ax.set_ylabel("USD")
    ax.set_xlabel("Year")
    fig.tight_layout()
    destination = CHARTS_DIR / "yearly_revenue_profit.png"
    fig.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(destination))

    if "Customer Segment" not in data:
        data, _ = add_customer_segments(data)
    segment = data.groupby("Customer Segment", as_index=False).agg(
        Customers=("Customer ID", "nunique"), Revenue=("Sales", "sum"))
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=segment.sort_values("Revenue", ascending=False), x="Revenue", y="Customer Segment", ax=ax)
    ax.set_title("RFM customer segment revenue", fontsize=14, weight="bold")
    fig.tight_layout()
    destination = CHARTS_DIR / "customer_segments.png"
    fig.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(str(destination))

    if {"Delivery Date", "Actual Delivery Days", "Is Late Delivery"}.issubset(data.columns):
        delivered = data.drop_duplicates("Order ID").dropna(subset=["Delivery Date"])
        if not delivered.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.boxplot(data=delivered, x="Shipping Mode", y="Actual Delivery Days", hue="Is Late Delivery", ax=ax)
            ax.set_title("Delivery transit time by shipping mode", fontsize=14, weight="bold")
            ax.set_ylabel("Transit days")
            fig.tight_layout()
            destination = CHARTS_DIR / "shipping_transit_time.png"
            fig.savefig(destination, dpi=150, bbox_inches="tight")
            plt.close(fig)
            paths.append(str(destination))
    return paths


if __name__ == "__main__":
    dataset = pd.read_csv(CLEAN_DATA_PATH, parse_dates=["Order Date"])
    for chart in create_eda_charts(dataset):
        print(chart)
