"""
Store Administration, Stock Replenishment, Order Fulfillment, and Analytics module for ApexCommerce.
"""
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from data_manager import (
    load_items,
    save_items,
    load_categories,
    load_orders,
    save_orders,
    add_product,
    update_product,
    delete_product,
    update_stock,
    batch_restock,
    update_order_status,
)


def render_admin_dashboard():
    """Render the master administrative dashboard with tabs for KPIs, Stock, Orders, and Catalog."""
    items_df = load_items()
    cats_df = load_categories()
    orders_df = load_orders()

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
                    border-radius: 14px; padding: 1.5rem 1.8rem; color: white; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="background: #3B82F6; color: white; padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">
                        Executive Management Console
                    </span>
                    <h2 style="color: white; margin: 8px 0 4px 0; font-size: 1.8rem; font-weight: 800;">
                        Store Operations & Inventory Hub
                    </h2>
                    <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
                        Real-time telemetry, stock replenishment, product CRUD, and order fulfillment.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top KPI Metrics Cards
    render_kpi_cards(items_df, orders_df)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Administrative Navigation Tabs
    tab_analytics, tab_stock, tab_orders, tab_products, tab_cats = st.tabs([
        "📊 Analytics & Insights",
        "📦 Stock & Replenishment",
        "📑 Order Fulfillment",
        "✏️ Product Catalog (CRUD)",
        "🗂️ Categories",
    ])

    with tab_analytics:
        render_analytics_tab(items_df, orders_df)

    with tab_stock:
        render_stock_tab(items_df)

    with tab_orders:
        render_orders_tab(orders_df)

    with tab_products:
        render_product_crud_tab(items_df, cats_df)

    with tab_cats:
        render_categories_tab(items_df, cats_df)


def render_kpi_cards(items_df: pd.DataFrame, orders_df: pd.DataFrame):
    """Render top executive KPI summary cards."""
    # Calculations
    total_skus = len(items_df)
    total_units = int(items_df["stock"].sum()) if "stock" in items_df.columns else 0
    inv_value = float((items_df["price"] * items_df["stock"]).sum()) if "stock" in items_df.columns else 0.0
    low_stock_count = len(items_df[items_df["stock"] < 10]) if "stock" in items_df.columns else 0
    out_of_stock_count = len(items_df[items_df["stock"] <= 0]) if "stock" in items_df.columns else 0

    total_orders = len(orders_df)
    gross_revenue = float(orders_df["total_amount"].sum()) if not orders_df.empty and "total_amount" in orders_df.columns else 0.0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        st.metric(
            label="💵 Total Gross Revenue",
            value=f"${gross_revenue:,.2f}",
            delta=f"{total_orders} Orders",
        )

    with kpi2:
        st.metric(
            label="💎 Catalog Valuation",
            value=f"${inv_value:,.2f}",
            delta=f"{total_units:,} Units",
        )

    with kpi3:
        st.metric(
            label="📦 Active Products",
            value=f"{total_skus} SKUs",
            delta=f"{len(items_df[items_df['isBestSeller'] == True])} Best Sellers",
        )

    with kpi4:
        st.metric(
            label="⚠️ Low Stock Alerts",
            value=f"{low_stock_count} Items",
            delta=f"{out_of_stock_count} Out of stock",
            delta_color="inverse",
        )

    with kpi5:
        st.metric(
            label="🚚 Active Orders",
            value=f"{total_orders}",
            delta="Live sync",
        )


def render_analytics_tab(items_df: pd.DataFrame, orders_df: pd.DataFrame):
    """Render interactive Plotly analytics charts."""
    st.subheader("📈 Inventory & Sales Performance Insights")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Category valuation chart (vectorized aggregation)
        items_temp = items_df.copy()
        items_temp["item_val"] = items_temp["price"] * items_temp["stock"]
        cat_group = (
            items_temp.groupby("category_name")
            .agg(inventory_val=("item_val", "sum"), item_count=("title", "count"))
            .reset_index()
            .sort_values(by="inventory_val", ascending=False)
            .head(10)
        )

        fig_cat = px.bar(
            cat_group,
            x="inventory_val",
            y="category_name",
            orientation="h",
            title="Top 10 Categories by Inventory Valuation ($)",
            labels={"inventory_val": "Inventory Value ($)", "category_name": "Category"},
            color="inventory_val",
            color_continuous_scale="Purples",
        )
        fig_cat.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_chart2:
        # Stock health classification
        def stock_bracket(s):
            if s <= 0:
                return "Out of Stock (0)"
            elif s < 10:
                return "Low Stock (<10)"
            elif s < 25:
                return "Medium (10-24)"
            else:
                return "Optimal (25+)"

        items_df["health"] = items_df["stock"].apply(stock_bracket)
        health_counts = items_df["health"].value_counts().reset_index()
        health_counts.columns = ["Stock Level", "Count"]

        fig_donut = px.pie(
            health_counts,
            names="Stock Level",
            values="Count",
            title="Warehouse Stock Health Distribution",
            hole=0.45,
            color="Stock Level",
            color_discrete_map={
                "Out of Stock (0)": "#EF4444",
                "Low Stock (<10)": "#F59E0B",
                "Medium (10-24)": "#3B82F6",
                "Optimal (25+)": "#10B981",
            },
        )
        fig_donut.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_donut, use_container_width=True)

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        # Price distribution
        fig_hist = px.histogram(
            items_df[items_df["price"] < 100],
            x="price",
            nbins=25,
            title="Price Distribution for Retail SKUs (<$100)",
            labels={"price": "Price ($)"},
            color_discrete_sequence=["#6366F1"],
        )
        fig_hist.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_chart4:
        # Order status breakdown
        if not orders_df.empty and "status" in orders_df.columns:
            status_counts = orders_df["status"].value_counts().reset_index()
            status_counts.columns = ["Order Status", "Orders"]
            fig_orders = px.bar(
                status_counts,
                x="Order Status",
                y="Orders",
                title="Customer Order Fulfillment Pipeline",
                color="Order Status",
                color_discrete_map={
                    "Delivered": "#10B981",
                    "Shipped": "#8B5CF6",
                    "Processing": "#3B82F6",
                    "Pending": "#F59E0B",
                },
            )
            fig_orders.update_layout(margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_orders, use_container_width=True)
        else:
            st.info("No order history available to render order status breakdown.")


def render_stock_tab(items_df: pd.DataFrame):
    """Inventory workbench for restock actions and threshold monitoring."""
    st.subheader("📦 Inventory Workbench & Stock Replenishment")

    c1, c2 = st.columns([2, 1])
    with c1:
        stock_filter = st.radio(
            "Filter Stock Table:",
            options=["All Items", "⚠️ Low Stock (< 10 units)", "🔴 Out of Stock (0 units)"],
            horizontal=True,
        )
    with c2:
        # Bulk restock low items button
        low_items = items_df[items_df["stock"] < 10]["title"].tolist()
        if st.button(f"⚡ Batch Restock All Low-Stock Items ({len(low_items)}) to +25 Units", type="primary"):
            if low_items:
                batch_restock(low_items, 25)
                st.success(f"Successfully added 25 units to all {len(low_items)} low-stock items!")
                st.rerun()
            else:
                st.info("No low-stock items detected right now!")

    # Filtered dataframe
    if stock_filter == "⚠️ Low Stock (< 10 units)":
        display_df = items_df[items_df["stock"] < 10].copy()
    elif stock_filter == "🔴 Out of Stock (0 units)":
        display_df = items_df[items_df["stock"] <= 0].copy()
    else:
        display_df = items_df.copy()

    # Search within inventory table
    inv_search = st.text_input("Filter inventory by product name:", placeholder="Type to filter...")
    if inv_search.strip():
        display_df = display_df[display_df["title"].str.lower().str.contains(inv_search.strip().lower(), na=False)]

    st.dataframe(
        display_df[["title", "category_name", "price", "stock", "stars", "isBestSeller"]].rename(
            columns={
                "title": "Product Title",
                "category_name": "Category",
                "price": "Price ($)",
                "stock": "Units in Stock",
                "stars": "Rating",
                "isBestSeller": "Best Seller",
            }
        ),
        use_container_width=True,
        height=320,
    )

    # Restock single product tool
    st.markdown("---")
    st.markdown("#### 🎯 Quick Single Product Restock")
    r_col1, r_col2, r_col3 = st.columns([3, 1, 1])

    with r_col1:
        restock_title = st.selectbox("Select product to replenish:", options=items_df["title"].tolist())

    curr_val = items_df.loc[items_df["title"] == restock_title, "stock"].values[0] if restock_title else 0

    with r_col2:
        st.markdown(f"**Current Stock:** `{curr_val}` units")
        add_amt = st.number_input("Add Units", min_value=1, max_value=500, value=20, step=5)

    with r_col3:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Confirm Restock", use_container_width=True):
            update_stock(restock_title, curr_val + add_amt)
            st.success(f"Stock for '{restock_title[:30]}...' updated to {curr_val + add_amt} units!")
            st.rerun()


def render_orders_tab(orders_df: pd.DataFrame):
    """Order fulfillment pipeline with status updates."""
    st.subheader("📑 Customer Order Fulfillment Hub")

    if orders_df.empty:
        st.info("No orders placed yet.")
        return

    filter_status = st.selectbox(
        "Filter orders by status:",
        options=["All Statuses", "Pending", "Processing", "Shipped", "Delivered"],
    )

    filtered_orders = orders_df.copy()
    if filter_status != "All Statuses":
        filtered_orders = filtered_orders[filtered_orders["status"] == filter_status]

    st.markdown(f"Displaying **{len(filtered_orders)}** order(s)")

    for _, order in filtered_orders.iterrows():
        oid = order["order_id"]
        status = order.get("status", "Pending")

        # Color badges
        if status == "Delivered":
            badge_color = "#10B981"
        elif status == "Shipped":
            badge_color = "#8B5CF6"
        elif status == "Processing":
            badge_color = "#3B82F6"
        else:
            badge_color = "#F59E0B"

        with st.container(border=True):
            head_col, status_col = st.columns([3, 1])
            with head_col:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.1rem; font-weight: 700; color: #1E293B;">📦 {oid}</span>
                        <span style="color: #64748B; font-size: 0.85rem;">placed by <strong>{order.get('customer_name', order.get('username'))}</strong> on {order.get('order_date')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with status_col:
                st.markdown(
                    f"""
                    <div style="text-align: right;">
                        <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 999px; font-size: 0.8rem; font-weight: 700;">
                            {status}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(f"**Items:** {order.get('items_summary', 'N/A')}")
            st.markdown(f"**Shipping Address:** `{order.get('shipping_address', 'N/A')}` | **Payment:** `{order.get('payment_method', 'N/A')}`")

            amt_col, act_col = st.columns([2, 3])
            with amt_col:
                st.markdown(
                    f"**Total Paid:** `${float(order.get('total_amount', 0)):.2f}` "
                    f"<span style='color: #64748B; font-size: 0.85rem;'>(Subtotal: ${float(order.get('subtotal', 0)):.2f}, Discount: ${float(order.get('discount', 0)):.2f})</span>",
                    unsafe_allow_html=True,
                )

            with act_col:
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("Mark Processing", key=f"proc_{oid}", disabled=(status == "Processing"), use_container_width=True):
                        update_order_status(oid, "Processing")
                        st.rerun()
                with b2:
                    if st.button("Mark Shipped", key=f"ship_{oid}", disabled=(status == "Shipped"), use_container_width=True):
                        update_order_status(oid, "Shipped")
                        st.rerun()
                with b3:
                    if st.button("Mark Delivered", key=f"del_{oid}", disabled=(status == "Delivered"), use_container_width=True):
                        update_order_status(oid, "Delivered")
                        st.rerun()


def render_product_crud_tab(items_df: pd.DataFrame, cats_df: pd.DataFrame):
    """Product CRUD: Add, Edit, Delete products in catalog."""
    st.subheader("✏️ Product Catalog Management (Add, Edit, Delete)")

    crud_action = st.radio("Choose Action:", ["➕ Add New Product", "✏️ Edit Product", "❌ Delete Product"], horizontal=True)

    cat_map = dict(zip(cats_df["category_id"], cats_df["category_name"]))
    cat_names = [f"{cid} - {name}" for cid, name in cat_map.items()]

    if crud_action == "➕ Add New Product":
        with st.form("add_product_form", clear_on_submit=True):
            new_title = st.text_input("Product Title *")
            sel_cat_str = st.selectbox("Category *", options=cat_names)
            col_p, col_s, col_r, col_st = st.columns(4)
            with col_p:
                new_price = st.number_input("Price ($)", min_value=0.50, value=14.99, step=0.50)
            with col_s:
                new_stock = st.number_input("Initial Stock Units", min_value=0, value=30, step=5)
            with col_r:
                new_stars = st.slider("Rating (Stars)", 1.0, 5.0, 4.5, step=0.1)
            with col_st:
                new_reviews = st.number_input("Verified Reviews Count", min_value=0, value=50, step=10)

            new_bestseller = st.checkbox("Mark as Best Seller", value=False)
            submitted = st.form_submit_button("🚀 Add Product to Catalog")

            if submitted:
                if not new_title.strip():
                    st.error("Title cannot be blank.")
                elif new_title.strip() in items_df["title"].values:
                    st.error("A product with this title already exists.")
                else:
                    cid = int(sel_cat_str.split(" - ")[0])
                    add_product(new_title, cid, new_price, new_stars, new_reviews, new_bestseller, new_stock)
                    st.success(f"Product '{new_title}' added successfully!")
                    st.rerun()

    elif crud_action == "✏️ Edit Product":
        selected_prod = st.selectbox("Select product to edit:", options=items_df["title"].tolist())
        row = items_df[items_df["title"] == selected_prod].iloc[0]

        with st.form("edit_product_form"):
            edit_title = st.text_input("Title", value=row["title"])

            # Find matching category index
            cid = row["category_id"]
            matched_str = f"{cid} - {cat_map.get(cid, '')}"
            idx = cat_names.index(matched_str) if matched_str in cat_names else 0
            edit_cat_str = st.selectbox("Category", options=cat_names, index=idx)

            col_p, col_s, col_r = st.columns(3)
            with col_p:
                edit_price = st.number_input("Price ($)", min_value=0.50, value=float(row["price"]), step=0.50)
            with col_s:
                edit_stock = st.number_input("Stock", min_value=0, value=int(row["stock"]), step=5)
            with col_r:
                edit_stars = st.slider("Stars", 1.0, 5.0, float(row["stars"]), step=0.1)

            edit_bestseller = st.checkbox("Best Seller", value=bool(row.get("isBestSeller", False)))
            submitted = st.form_submit_button("💾 Save Product Updates")

            if submitted:
                new_cid = int(edit_cat_str.split(" - ")[0])
                update_product(selected_prod, edit_title, new_cid, edit_price, edit_stars, edit_stock, edit_bestseller)
                st.success("Product successfully updated!")
                st.rerun()

    elif crud_action == "❌ Delete Product":
        del_prod = st.selectbox("Select product to remove:", options=items_df["title"].tolist())
        st.warning(f"Are you sure you want to permanently remove **{del_prod}** from the catalog?")
        if st.button("⚠️ Confirm Delete Product", type="primary"):
            delete_product(del_prod)
            st.success(f"Product '{del_prod}' was removed from catalog.")
            st.rerun()


def render_categories_tab(items_df: pd.DataFrame, cats_df: pd.DataFrame):
    """View category counts and stats."""
    st.subheader("🗂️ Categories Overview")

    cat_stats = (
        items_df.groupby("category_id")
        .agg(
            Category=("category_name", "first"),
            Total_Items=("title", "count"),
            Avg_Price=("price", "mean"),
            Total_Stock=("stock", "sum"),
        )
        .reset_index()
    )
    cat_stats["Avg_Price"] = cat_stats["Avg_Price"].round(2)

    st.dataframe(
        cat_stats.rename(
            columns={
                "category_id": "ID",
                "Total_Items": "Total Products",
                "Avg_Price": "Avg Price ($)",
                "Total_Stock": "Total Stock Units",
            }
        ),
        use_container_width=True,
    )
