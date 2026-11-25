"""Streamlit entry point for the E-Commerce Sales Analysis dashboard."""

import sqlite3
from contextlib import closing
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis.business_insights import generate_insights
from analysis.customer_segmentation import add_customer_segments
from config import DATABASE_PATH

NAVY = "#142B4A"
BLUE = "#4F46E5"
TEAL = "#0F9D8A"
PALETTE = [BLUE, TEAL, "#F59E0B", "#E85D75", "#8B5CF6", "#0EA5E9"]
VIBRANT_SCALE = [[0, "#E9E8FF"], [.45, "#8B83F6"], [1, "#4338CA"]]
MUTED = "#65758B"
FILTER_KEYS = ["filter_dates", "filter_category", "filter_subcategory", "filter_region",
               "filter_state", "filter_payment", "filter_segment", "filter_status"]

st.set_page_config(page_title="E-Commerce Sales Dashboard", page_icon="\U0001F4CA", layout="wide")
st.markdown(
    """<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root { --ink:#172b4d; --muted:#64748b; --line:#e5ebf3; --canvas:#f4f7fb; --accent:#4f46e5; }
    .stApp { background:var(--canvas); color:var(--ink); font-family:'DM Sans',sans-serif; }
    [data-testid="stAppViewContainer"] > .main { background:var(--canvas); }
    [data-testid="stMainBlockContainer"] { width:100%; max-width:none; margin:0 auto; padding:1.35rem 1.25rem 2.5rem; }
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap:1.05rem; }
    [data-testid="stHorizontalBlock"] { gap:1.1rem; align-items:stretch; }
    [data-testid="stSidebar"] { background:#fbfcfe; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] > div { padding-top:1.4rem; }
    [data-testid="stSidebar"] h2 { font:800 1.18rem 'Manrope',sans-serif; letter-spacing:-.035em; color:var(--ink); margin-bottom:.1rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] p { color:var(--muted); font-size:.9rem; line-height:1.6; }
    .filter-heading { display:flex; align-items:center; gap:.65rem; padding:.8rem .85rem; margin:.15rem 0 .8rem; border:1px solid #d8d5ff; border-radius:13px; background:linear-gradient(120deg,#eeedff,#f7f6ff); }
    .filter-heading .filter-mark { display:grid; place-items:center; width:30px; height:30px; border-radius:9px; background:#dedcff; color:#4338ca; font-size:16px; }
    .filter-heading .filter-title { color:#302b78; font:750 .96rem 'Manrope',sans-serif; }
    .source-count { margin:.8rem 0 .55rem; padding:.75rem .85rem; border:1px solid #cbdafd; border-radius:12px; background:linear-gradient(120deg,#edf3ff,#f7f9ff); }
    .source-count-label { display:block; color:#435a83; font-size:.72rem; font-weight:700; letter-spacing:.075em; text-transform:uppercase; }
    .source-count-value { display:block; margin-top:.12rem; color:#3730a3; font:800 1.28rem 'Manrope',sans-serif; letter-spacing:-.035em; }
    .filter-note { margin:.55rem 0 .35rem; padding:.75rem .85rem; border-left:3px solid #0f9d8a; border-radius:0 10px 10px 0; background:#e5f7f3; color:#24534f; font-size:.79rem; line-height:1.55; }
    .workspace-label { display:inline-flex; align-items:center; gap:.45rem; margin:.2rem 0 .15rem; padding:.42rem .65rem; border:1px solid #d4d0ff; border-radius:999px; background:linear-gradient(120deg,#f0efff,#eaf7ff); color:#4338ca; font-size:.76rem; font-weight:700; letter-spacing:.015em; }
    .workspace-label:before { content:''; width:7px; height:7px; border-radius:50%; background:#4f46e5; box-shadow:0 0 0 3px #dcd9ff; }
    [data-testid="stSidebar"] label p { color:#263b55!important; font-size:.83rem!important; font-weight:650!important; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div { background:#fff; }
    h1,h2,h3 { color:var(--ink); font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
    h1 { font-size:clamp(2rem,3vw,2.65rem)!important; line-height:1.15!important; font-weight:800!important; margin:.15rem 0 .25rem!important; }
    h2 { position:relative; font-size:1.35rem!important; line-height:1.3!important; font-weight:750!important; margin:1.25rem 0 .25rem!important; padding:0 0 .62rem!important; border-bottom:1px solid #e2e8f2; }
    h2:after { content:''; position:absolute; left:0; bottom:-1px; width:48px; height:3px; border-radius:5px; background:linear-gradient(90deg,#4f46e5,#0f9d8a); }
    h3 { font-size:1.12rem!important; font-weight:700!important; }
    [data-testid="stMetric"] { background:#fff; border:1px solid var(--line); padding:1.05rem 1.2rem; border-radius:16px; box-shadow:0 2px 8px rgba(24,44,75,.035); min-height:116px; }
    [data-testid="stMetricLabel"] { color:var(--muted); font-size:.82rem; font-weight:600; }
    [data-testid="stMetricValue"] { color:var(--ink); font:750 clamp(1.35rem,1.8vw,1.8rem) 'Manrope',sans-serif; letter-spacing:-.04em; }
    [data-testid="stMetricDelta"] { font-size:.76rem; font-weight:600; }
    [data-testid="stPlotlyChart"] { width:100%; background:#fff; border:1px solid var(--line); border-radius:16px; padding:.45rem .6rem .15rem; box-shadow:0 3px 12px rgba(24,44,75,.045); }
    [data-testid="stDataFrame"] { width:100%; border:1px solid var(--line); border-radius:14px; overflow:hidden; background:#fff; box-shadow:0 3px 12px rgba(24,44,75,.035); }
    [data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border-color:var(--line)!important; border-radius:16px!important; box-shadow:0 2px 10px rgba(24,44,75,.035); }
    div[data-baseweb="select"] > div,div[data-baseweb="input"] > div { border-radius:10px; border-color:#dbe3ed; }
    .stButton > button,.stDownloadButton > button { border-radius:10px; font-weight:650; transition:all .18s ease; }
    .stButton > button:hover,.stDownloadButton > button:hover { border-color:var(--accent); color:var(--accent); transform:translateY(-1px); }
    [data-testid="stSidebar"] hr { border-color:var(--line); margin:1.15rem 0; }
    @media(max-width:900px) { [data-testid="stMainBlockContainer"] { padding:1.2rem .8rem 2rem; } [data-testid="stHorizontalBlock"] { gap:.65rem; } }
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading sales dataset...")
def load_data() -> pd.DataFrame:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"SQLite database is missing: {DATABASE_PATH}. Run analysis/data_cleaning.py first.")
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        data = pd.read_sql_query(
            "SELECT * FROM sales",
            connection,
            parse_dates=["Order Date", "Ship Date", "Delivery Date"],
        )
    data["Is Late Delivery"] = data["Is Late Delivery"].astype(bool)
    data["Is Sales Outlier"] = data["Is Sales Outlier"].astype(bool)
    data, _ = add_customer_segments(data)
    return data


def _format_money(value: float) -> str:
    return f"${value:,.0f}"


def _chart(fig: Any, height: int = 360) -> None:
    fig.update_layout(
        height=height, margin=dict(l=12, r=12, t=48, b=12),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", color=NAVY, size=13),
        title_font=dict(family="Manrope, sans-serif", size=16, color=NAVY),
        legend_title_text="", hoverlabel=dict(bgcolor="#172b4d", font_color="white", font_size=13),
        colorway=PALETTE, title_x=.025,
    )
    fig.update_traces(marker_line_color="white", marker_line_width=1, selector={"type": "bar"})
    fig.update_traces(marker_line_color="white", marker_line_width=2, selector={"type": "pie"})
    fig.update_xaxes(showgrid=True, gridcolor="#edf1f8", zerolinecolor="#cfd8e8", title_font=dict(size=12, color="#52627a"), tickfont=dict(color="#52627a"))
    fig.update_yaxes(showgrid=False, zerolinecolor="#cfd8e8", title_font=dict(size=12, color="#52627a"), tickfont=dict(color="#52627a"))
    st.plotly_chart(fig, width="stretch")


def _filters(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    with st.sidebar:
        st.markdown("## E-Commerce Sales")
        st.markdown('<div class="workspace-label">Sales performance dashboard</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<div class="filter-heading"><span class="filter-mark">&#128269;</span><span class="filter-title">Global filters</span></div>', unsafe_allow_html=True)
        if st.button("Reset filters", width="stretch"):
            for key in FILTER_KEYS:
                st.session_state.pop(key, None)
            st.rerun()
        minimum, maximum = data["Order Date"].min().date(), data["Order Date"].max().date()
        dates = st.date_input("Order date range", (minimum, maximum), min_value=minimum, max_value=maximum, key="filter_dates")
        categories = st.multiselect("Category", sorted(data["Category"].unique()), key="filter_category")
        subcategories = st.multiselect("Sub-category", sorted(data["Sub-Category"].unique()), key="filter_subcategory")
        regions = st.multiselect("Region", sorted(data["Region"].unique()), key="filter_region")
        states = st.multiselect("State", sorted(data["State"].unique()), key="filter_state")
        payments = st.multiselect("Payment mode", sorted(data["Payment Mode"].unique()), key="filter_payment")
        segments = st.multiselect("Customer segment", sorted(data["Customer Segment"].dropna().unique()), key="filter_segment")
        statuses = st.multiselect("Order status", sorted(data["Order Status"].unique()), key="filter_status")
        st.markdown("---")
        st.markdown(
            f'<div class="source-count"><span class="source-count-label">Source order lines</span>'
            f'<span class="source-count-value">{len(data):,}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="filter-note">Sales and profit reflect all selected order statuses. '
            'No assumed refund amounts are applied.</div>',
            unsafe_allow_html=True,
        )

    dimension_filtered = data
    for column, choices in [
        ("Category", categories), ("Sub-Category", subcategories), ("Region", regions),
        ("State", states), ("Payment Mode", payments), ("Customer Segment", segments),
        ("Order Status", statuses),
    ]:
        if choices:
            dimension_filtered = dimension_filtered[dimension_filtered[column].isin(choices)]

    filtered = dimension_filtered
    comparison = dimension_filtered.iloc[0:0]
    if isinstance(dates, (tuple, list)) and len(dates) == 2:
        start, end = dates
        filtered = dimension_filtered[dimension_filtered["Order Date"].dt.date.between(start, end)]
        period_days = (end - start).days + 1
        previous_start = start - pd.Timedelta(days=period_days)
        previous_end = start - pd.Timedelta(days=1)
        comparison = dimension_filtered[
            dimension_filtered["Order Date"].dt.date.between(previous_start, previous_end)
        ]
    return filtered, comparison


def _kpis(data: pd.DataFrame, comparison: pd.DataFrame, include_margin: bool = True) -> None:
    sales = data["Sales"].sum()
    profit = data["Profit"].sum()
    order_count = data["Order ID"].nunique()
    customer_count = data["Customer ID"].nunique()
    previous_sales = comparison["Sales"].sum()
    previous_profit = comparison["Profit"].sum()
    previous_orders = comparison["Order ID"].nunique()
    previous_customers = comparison["Customer ID"].nunique()
    previous_aov = previous_sales / previous_orders if previous_orders else 0
    current_aov = sales / order_count if order_count else 0
    previous_margin = previous_profit / previous_sales if previous_sales else 0
    current_margin = profit / sales if sales else 0
    has_comparison = not comparison.empty

    def change(current: float, previous: float, prefix: str = "", suffix: str = "") -> str | None:
        if not has_comparison:
            return None
        difference = current - previous
        sign = "+" if difference >= 0 else "-"
        return f"{sign}{prefix}{abs(difference):,.0f}{suffix} vs prior period"

    metrics = [
        ("Total Revenue", _format_money(sales), change(sales, previous_sales, "$")),
        ("Total Profit", _format_money(profit), change(profit, previous_profit, "$")),
        ("Total Orders", f"{order_count:,}", change(order_count, previous_orders)),
        ("Total Customers", f"{customer_count:,}", change(customer_count, previous_customers)),
        ("Average Order Value", _format_money(current_aov), change(current_aov, previous_aov, "$")),
    ]
    if include_margin:
        metrics.append(("Profit Margin", f"{current_margin:.1%}", change(current_margin * 100, previous_margin * 100, suffix=" pp")))
    columns = st.columns(len(metrics))
    for column, (label, value, delta) in zip(columns, metrics):
        column.metric(label, value, delta=delta, delta_color="normal")


def _empty(data: pd.DataFrame) -> bool:
    if not data.empty:
        return False
    st.info("No records match the selected filters. Adjust the sidebar filters to continue.")
    return True


def _overview(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Executive Overview")
    st.caption("A high-level view of sales, profitability, and demand. Use the order-status filter to focus on specific lifecycle states.")
    if _empty(data):
        return
    _kpis(data, comparison)
    monthly = data.groupby("Month", as_index=False).agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"))
    left, right = st.columns([1.5, 1])
    with left:
        fig = px.line(monthly, x="Month", y=["Revenue", "Profit"], markers=True, color_discrete_sequence=[BLUE, TEAL], title="Monthly revenue and profit")
        _chart(fig)
    with right:
        category = data.groupby("Category", as_index=False)["Sales"].sum()
        _chart(px.pie(category, values="Sales", names="Category", hole=.56, title="Revenue mix by category", color_discrete_sequence=PALETTE))
    left, right = st.columns([1.2, 1])
    with left:
        region = data.groupby("Region", as_index=False).agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"))
        _chart(px.bar(region.sort_values("Revenue"), x="Revenue", y="Region", orientation="h", color="Profit", color_continuous_scale=VIBRANT_SCALE, title="Regional performance"))
    with right:
        yearly = data.groupby("Year", as_index=False)["Sales"].sum().sort_values("Year")
        yearly["YoY Growth"] = yearly["Sales"].pct_change() * 100
        st.subheader("Year-over-year revenue")
        display = yearly.copy()
        display["Revenue"] = display["Sales"].map(_format_money)
        display["Growth"] = display["YoY Growth"].map(lambda x: "—" if pd.isna(x) else f"{x:+.1f}%")
        st.dataframe(display[["Year", "Revenue", "Growth"]], hide_index=True, width="stretch")
        if yearly["YoY Growth"].notna().any():
            latest = yearly.dropna(subset=["YoY Growth"]).iloc[-1]
            st.metric(f"{int(latest['Year'])} revenue growth", f"{latest['YoY Growth']:+.1f}%")
    status = data.groupby("Order Status", as_index=False).agg(Orders=("Order ID", "nunique"), Revenue=("Sales", "sum"))
    _chart(px.bar(status.sort_values("Orders"), x="Orders", y="Order Status", orientation="h",
                  color="Revenue", color_continuous_scale=VIBRANT_SCALE, title="Order status mix"))


def _sales(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Sales Analysis")
    st.caption("Explore demand by time period, product hierarchy, and revenue contribution.")
    if _empty(data):
        return
    _kpis(data, comparison, include_margin=False)
    grain = st.radio("Trend granularity", ["Daily", "Monthly", "Quarterly", "Yearly"], horizontal=True)
    if grain == "Daily":
        trend = data.assign(Period=data["Order Date"].dt.date).groupby("Period", as_index=False)["Sales"].sum()
    elif grain == "Monthly":
        trend = data.groupby("Month", as_index=False)["Sales"].sum().rename(columns={"Month": "Period"})
    elif grain == "Quarterly":
        trend = data.assign(Period=data["Year"].astype(str) + " " + data["Quarter"]).groupby("Period", as_index=False)["Sales"].sum()
    else:
        trend = data.groupby("Year", as_index=False)["Sales"].sum()
        trend["Period"] = trend["Year"].astype(str)
    _chart(px.area(trend, x="Period", y="Sales", title=f"{grain} revenue trend", color_discrete_sequence=[BLUE]))
    left, right = st.columns(2)
    with left:
        cat = data.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
        _chart(px.bar(cat, x="Category", y="Sales", title="Revenue by category", color="Sales", color_continuous_scale=VIBRANT_SCALE))
    with right:
        sub = data.groupby("Sub-Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
        _chart(px.bar(sub.head(12).sort_values("Sales"), x="Sales", y="Sub-Category", orientation="h", title="Top sub-categories", color_discrete_sequence=[TEAL]))
    product = data.groupby(["Product Name", "Product ID"], as_index=False).agg(Revenue=("Sales", "sum"), Units=("Quantity", "sum"))
    st.subheader("Top and bottom products by revenue")
    st.dataframe(pd.concat([product.nlargest(10, "Revenue").assign(Rank_Group="Top"), product.nsmallest(10, "Revenue").assign(Rank_Group="Bottom")]).sort_values("Revenue", ascending=False), hide_index=True, width="stretch")
    payment = data.groupby("Payment Mode", as_index=False).agg(
        Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    _chart(px.bar(payment, x="Payment Mode", y=["Revenue", "Profit"], barmode="group",
                  title="Revenue and profit by payment mode", color_discrete_sequence=[BLUE, TEAL]))


def _profitability(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Profitability Analysis")
    if _empty(data):
        return
    _kpis(data, comparison)
    left, right = st.columns(2)
    with left:
        category = data.groupby("Category", as_index=False).agg(Profit=("Profit", "sum"), Revenue=("Sales", "sum"))
        category["Margin"] = category["Profit"] / category["Revenue"].replace(0, pd.NA)
        _chart(px.bar(category, x="Category", y="Profit", color="Margin", color_continuous_scale="RdYlGn", title="Profit and margin by category"))
    with right:
        _chart(px.scatter(data, x="Discount", y="Profit", color="Category", size="Sales", hover_data=["Product Name"], opacity=.62, title="Discount versus profit"))
    products = data.groupby(["Product ID", "Product Name"], as_index=False).agg(Profit=("Profit", "sum"), Revenue=("Sales", "sum"))
    loss = products[products["Profit"] < 0].sort_values("Profit")
    st.subheader("Loss-making products")
    st.dataframe(loss if not loss.empty else products.nsmallest(10, "Profit"), hide_index=True, width="stretch")
    st.caption("If no product is loss-making in this filter, the 10 lowest-profit products are shown instead.")


def _customers(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Customer Analysis")
    if _empty(data):
        return
    customer = data.groupby(["Customer ID", "Customer Name", "Customer Segment", "Gender", "Age"], as_index=False).agg(
        Revenue=("Sales", "sum"), Orders=("Order ID", "nunique"), Profit=("Profit", "sum"))
    repeat_rate = (customer["Orders"] > 1).mean() if len(customer) else 0
    new_customers = int(customer["Orders"].eq(1).sum())
    repeat_customers = int(customer["Orders"].gt(1).sum())
    columns = st.columns(6)
    columns[0].metric("Unique customers", f"{customer['Customer ID'].nunique():,}")
    columns[1].metric("New customers", f"{new_customers:,}")
    columns[2].metric("Repeat customers", f"{repeat_customers:,}")
    columns[3].metric("Repeat customer rate", f"{repeat_rate:.1%}")
    columns[4].metric("Average customer spend", _format_money(customer["Revenue"].mean() if len(customer) else 0))
    columns[5].metric("Revenue per order", _format_money(data["Sales"].sum() / max(data["Order ID"].nunique(), 1)))
    segment_col, age_col, gender_col = st.columns(3)
    with segment_col:
        segments = customer.groupby("Customer Segment", as_index=False).agg(Customers=("Customer ID", "nunique"), Revenue=("Revenue", "sum"))
        _chart(px.bar(segments, x="Customer Segment", y="Customers", color="Revenue", title="RFM customer segments", color_continuous_scale=VIBRANT_SCALE))
    with age_col:
        customer["Age Group"] = pd.cut(customer["Age"], [17, 24, 34, 44, 54, 64, 100], labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
        age = customer.groupby("Age Group", observed=True, as_index=False)["Revenue"].sum()
        _chart(px.bar(age, x="Age Group", y="Revenue", title="Revenue by customer age group", color_discrete_sequence=[TEAL]))
    with gender_col:
        gender = customer.groupby("Gender", as_index=False).agg(Customers=("Customer ID", "nunique"), Revenue=("Revenue", "sum"))
        _chart(px.bar(gender, x="Gender", y="Customers", color="Revenue", title="Customers by gender", color_continuous_scale=VIBRANT_SCALE))
    st.subheader("High-value customers")
    st.dataframe(customer.nlargest(20, "Revenue"), hide_index=True, width="stretch")


def _products(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Product Analysis")
    if _empty(data):
        return
    products = data.groupby(["Product ID", "Product Name", "Category", "Sub-Category"], as_index=False).agg(
        Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"), Orders=("Order ID", "nunique"))
    products["Revenue Share"] = products["Revenue"] / products["Revenue"].sum()
    _kpis(data, comparison, include_margin=False)
    left, right = st.columns(2)
    with left:
        _chart(px.bar(products.nlargest(10, "Quantity").sort_values("Quantity"), x="Quantity", y="Product Name", orientation="h", title="Best-selling products by units", color_discrete_sequence=[BLUE]))
    with right:
        _chart(px.bar(products.nlargest(10, "Profit").sort_values("Profit"), x="Profit", y="Product Name", orientation="h", title="Most profitable products", color_discrete_sequence=[TEAL]))
    st.subheader("Full product performance")
    st.dataframe(products.sort_values("Revenue", ascending=False), hide_index=True, width="stretch")


def _regional(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Regional Analysis")
    st.caption("Compare revenue, profit, and order activity across regions and states. Use the global filters to focus the view.")
    if _empty(data):
        return
    _kpis(data, comparison, include_margin=False)
    region = data.groupby("Region", as_index=False).agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    state = data.groupby("State", as_index=False).agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    left, right = st.columns(2)
    with left:
        _chart(px.bar(region.sort_values("Profit"), x="Profit", y="Region", orientation="h", color="Revenue", title="Profit by region", color_continuous_scale=VIBRANT_SCALE))
    with right:
        abbreviations = {
            "Alabama":"AL", "Alaska":"AK", "Arizona":"AZ", "Arkansas":"AR", "California":"CA",
            "Colorado":"CO", "Connecticut":"CT", "Delaware":"DE", "District of Columbia":"DC",
            "Florida":"FL", "Georgia":"GA", "Hawaii":"HI", "Idaho":"ID", "Illinois":"IL",
            "Indiana":"IN", "Iowa":"IA", "Kansas":"KS", "Kentucky":"KY", "Louisiana":"LA",
            "Maine":"ME", "Maryland":"MD", "Massachusetts":"MA", "Michigan":"MI", "Minnesota":"MN",
            "Mississippi":"MS", "Missouri":"MO", "Montana":"MT", "Nebraska":"NE", "Nevada":"NV",
            "New Hampshire":"NH", "New Jersey":"NJ", "New Mexico":"NM", "New York":"NY",
            "North Carolina":"NC", "North Dakota":"ND", "Ohio":"OH", "Oklahoma":"OK", "Oregon":"OR",
            "Pennsylvania":"PA", "Rhode Island":"RI", "South Carolina":"SC", "South Dakota":"SD",
            "Tennessee":"TN", "Texas":"TX", "Utah":"UT", "Vermont":"VT", "Virginia":"VA",
            "Washington":"WA", "West Virginia":"WV", "Wisconsin":"WI", "Wyoming":"WY",
        }
        state["Code"] = state["State"].map(abbreviations)
        state_map = px.choropleth(state.dropna(subset=["Code"]), locations="Code", locationmode="USA-states", color="Revenue", hover_name="State", hover_data=["Profit", "Orders"], scope="usa", color_continuous_scale=[[0, "#e8e7ff"], [.45, "#918bfa"], [1, "#4338ca"]], title="Revenue by state", labels={"Revenue": "Revenue ($)"})
        state_map.update_geos(bgcolor="white", lakecolor="#f4f7fb", showlakes=True, subunitcolor="#ffffff", showcountries=False)
        _chart(state_map, height=430)
    st.subheader("State & city performance")
    st.caption("Ranked by revenue. Select a region, state, or city above to narrow the table.")
    st.dataframe(data.groupby(["Region", "State", "City"], as_index=False).agg(Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique")).sort_values("Revenue", ascending=False), hide_index=True, width="stretch")


def _shipping(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Shipping & Fulfillment")
    st.caption("Delivery-speed and on-time performance are based on generated ship/delivery dates; non-delivered orders are excluded from transit-time metrics.")
    if _empty(data):
        return
    order_level = data.drop_duplicates("Order ID")
    delivered = order_level.dropna(subset=["Delivery Date"])
    delivered_count = len(delivered)
    on_time_rate = (1 - delivered["Is Late Delivery"].astype(bool).mean()) if delivered_count else 0
    average_days = delivered["Actual Delivery Days"].mean() if delivered_count else 0
    median_days = delivered["Actual Delivery Days"].median() if delivered_count else 0
    shipment_rate = order_level["Ship Date"].notna().mean() if len(order_level) else 0
    kpis = st.columns(4)
    kpis[0].metric("Delivered orders", f"{delivered_count:,}")
    kpis[1].metric("On-time delivery", f"{on_time_rate:.1%}" if delivered_count else "N/A")
    kpis[2].metric("Average transit time", f"{average_days:.1f} days" if delivered_count else "N/A")
    kpis[3].metric("Median transit time", f"{median_days:.0f} days" if delivered_count else "N/A")
    st.caption(f"Shipment rate across filtered orders: {shipment_rate:.1%}")
    if delivered.empty:
        st.info("No delivered orders match the active filters, so delivery-time metrics are unavailable.")
        return
    mode = delivered.groupby("Shipping Mode", as_index=False).agg(
        Delivered=("Order ID", "nunique"),
        Average_Days=("Actual Delivery Days", "mean"),
        On_Time_Rate=("Is Late Delivery", lambda late: 1 - late.astype(bool).mean()),
    )
    left, right = st.columns(2)
    with left:
        _chart(px.bar(mode.sort_values("Average_Days"), x="Average_Days", y="Shipping Mode", orientation="h",
                      color="On_Time_Rate", color_continuous_scale="RdYlGn", range_color=[0, 1],
                      title="Average transit time and on-time rate", labels={"Average_Days": "Average transit days", "On_Time_Rate": "On-time rate"}))
    with right:
        status = order_level.groupby("Order Status", as_index=False).agg(Orders=("Order ID", "nunique"))
        _chart(px.pie(status, values="Orders", names="Order Status", hole=.56, title="Order fulfillment status"))
    monthly = delivered.assign(Month=delivered["Order Date"].dt.to_period("M").astype(str)).groupby("Month", as_index=False).agg(
        Delivered=("Order ID", "nunique"),
        On_Time_Rate=("Is Late Delivery", lambda late: 1 - late.astype(bool).mean()),
    )
    _chart(px.line(monthly, x="Month", y="On_Time_Rate", markers=True, title="Monthly on-time delivery rate",
                   labels={"On_Time_Rate": "On-time delivery rate"}, color_discrete_sequence=[TEAL]))
    st.subheader("Shipping mode performance")
    display = mode.rename(columns={"Average_Days": "Average Transit Days", "On_Time_Rate": "On-time Rate"})
    display["Average Transit Days"] = display["Average Transit Days"].round(1)
    display["On-time Rate"] = display["On-time Rate"].map(lambda rate: f"{rate:.1%}")
    st.dataframe(display.sort_values("Delivered", ascending=False), hide_index=True, width="stretch")


def _insights(data: pd.DataFrame, comparison: pd.DataFrame) -> None:
    st.title("Business Insights")
    st.caption("Insights recalculate from the current filter selection; treat the generated synthetic data as a demonstration, not company results.")
    if _empty(data):
        return
    _kpis(data, comparison)
    for index, item in enumerate(generate_insights(data), start=1):
        with st.container(border=True):
            st.markdown(f"**{index}. {item['insight']}**")
            st.markdown(f"Recommendation: {item['recommendation']}")
    st.subheader("Discount and profitability")
    data = data.copy()
    data["Discount Band"] = pd.cut(data["Discount"], [-.001, .05, .10, .20, .8], labels=["0-5%", "5-10%", "10-20%", "20%+"])
    impact = data.groupby("Discount Band", observed=True, as_index=False).agg(
        Revenue=("Sales", "sum"), Profit=("Profit", "sum"), Lines=("Sales", "size"))
    impact["Margin"] = impact["Profit"] / impact["Revenue"].replace(0, pd.NA)
    _chart(px.bar(impact, x="Discount Band", y="Margin", color="Profit", title="Average line profit margin by discount band", color_continuous_scale="RdYlGn"))
    st.dataframe(impact, hide_index=True, width="stretch")


PAGE_RENDERERS = {
    "Executive Overview": _overview, "Sales Analysis": _sales, "Profitability Analysis": _profitability,
    "Customer Analysis": _customers, "Product Analysis": _products, "Regional Analysis": _regional,
    "Shipping & Fulfillment": _shipping, "Business Insights": _insights,
}


def run_page(page: str | None = None) -> None:
    try:
        source = load_data()
        filtered, comparison = _filters(source)
        selected = page or "Executive Overview"
        _download(filtered)
        PAGE_RENDERERS[selected](filtered, comparison)
    except (FileNotFoundError, pd.errors.EmptyDataError) as error:
        st.error(str(error))


def _download(data: pd.DataFrame) -> None:
    st.sidebar.download_button("Download filtered CSV", data.to_csv(index=False).encode("utf-8"), "ecommerce_filtered.csv", "text/csv", width="stretch")


if __name__ == "__main__":
    # Give the entry page a meaningful navigation label instead of the
    # default filename label (“app”) shown by Streamlit's automatic pages.
    navigation = st.navigation(
        [
            st.Page(lambda: run_page("Executive Overview"), title="E-Commerce Sales Dashboard", icon="📊", url_path="dashboard", default=True),
            st.Page(lambda: run_page("Sales Analysis"), title="Sales Analysis", icon="📈", url_path="sales-analysis"),
            st.Page(lambda: run_page("Profitability Analysis"), title="Profitability Analysis", icon="💰", url_path="profitability-analysis"),
            st.Page(lambda: run_page("Customer Analysis"), title="Customer Analysis", icon="👥", url_path="customer-analysis"),
            st.Page(lambda: run_page("Product Analysis"), title="Product Analysis", icon="📦", url_path="product-analysis"),
            st.Page(lambda: run_page("Regional Analysis"), title="Regional Analysis", icon="🌎", url_path="regional-analysis"),
            st.Page(lambda: run_page("Shipping & Fulfillment"), title="Shipping & Fulfillment", icon="🚚", url_path="shipping-fulfillment"),
            st.Page(lambda: run_page("Business Insights"), title="Business Insights", icon="💡", url_path="business-insights"),
        ],
        position="sidebar",
    )
    navigation.run()
