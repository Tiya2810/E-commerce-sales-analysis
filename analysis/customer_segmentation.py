"""Customer-level RFM scoring and segment assignment."""

import pandas as pd


def build_rfm(data: pd.DataFrame) -> pd.DataFrame:
    """Return one row per customer with recency, frequency, monetary value, and segment."""
    frame = data.copy()
    frame["Order Date"] = pd.to_datetime(frame["Order Date"])
    snapshot = frame["Order Date"].max() + pd.Timedelta(days=1)
    rfm = frame.groupby("Customer ID", as_index=False).agg(
        Recency=("Order Date", lambda dates: (snapshot - dates.max()).days),
        Frequency=("Order ID", "nunique"),
        Monetary=("Sales", "sum"),
        Customer_Name=("Customer Name", "first"),
        Age=("Age", "first"),
        Gender=("Gender", "first"),
    )
    if len(rfm) > 1:
        rfm["R Score"] = pd.qcut(rfm["Recency"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
        rfm["F Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
        rfm["M Score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    else:
        rfm[["R Score", "F Score", "M Score"]] = 1
    rfm["Customer Segment"] = "Potential Loyalist"
    rfm.loc[(rfm["R Score"] >= 3) & (rfm["F Score"] >= 3) & (rfm["M Score"] >= 3), "Customer Segment"] = "Champions"
    rfm.loc[(rfm["R Score"] <= 2) & (rfm["F Score"] >= 3), "Customer Segment"] = "At Risk"
    rfm.loc[(rfm["F Score"] == 1) & (rfm["R Score"] >= 3), "Customer Segment"] = "New Customers"
    rfm.loc[(rfm["F Score"] <= 2) & (rfm["R Score"] <= 2), "Customer Segment"] = "Hibernating"
    rfm.loc[(rfm["M Score"] == 4) & (rfm["F Score"] <= 2), "Customer Segment"] = "Big Spenders"
    return rfm


def add_customer_segments(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rfm = build_rfm(data)
    return data.merge(rfm[["Customer ID", "Customer Segment"]], on="Customer ID", how="left"), rfm
